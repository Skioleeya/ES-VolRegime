"""SQLite persistence for normalized historical bars."""

from pathlib import Path
import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from .models import HistoricalBar, QualifiedContract
from .coverage import expected_bar_starts, missing_bar_starts, is_trading_session


class HistoricalRepository:
    """Persist normalized bars with a deterministic primary key."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def close(self) -> None:
        self._connection.close()

    def save_bars(self, bars: tuple[HistoricalBar, ...]) -> int:
        rows = [self._row(bar) for bar in bars]
        with self._connection:
            self._connection.executemany(
                """
                INSERT INTO historical_bars (
                    con_id, local_symbol, contract_month, bar_start_utc,
                    bar_start_et, open, high, low, close, volume, wap,
                    bar_count, what_to_show, use_rth, source, is_complete
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(con_id, bar_start_utc) DO UPDATE SET
                    local_symbol=excluded.local_symbol,
                    contract_month=excluded.contract_month,
                    bar_start_et=excluded.bar_start_et,
                    open=excluded.open, high=excluded.high, low=excluded.low,
                    close=excluded.close, volume=excluded.volume, wap=excluded.wap,
                    bar_count=excluded.bar_count, source=excluded.source,
                    is_complete=excluded.is_complete
                """,
                rows,
            )
        return len(rows)

    def count(self) -> int:
        return self._connection.execute("SELECT COUNT(*) FROM historical_bars").fetchone()[0]

    def load_bars(self, contract: QualifiedContract) -> tuple[HistoricalBar, ...]:
        """Load completed bars for one explicitly identified contract."""
        rows = self._connection.execute(
            """
            SELECT bar_start_utc, open, high, low, close, volume, wap, bar_count,
                   source, is_complete
            FROM historical_bars
            WHERE con_id = ? AND local_symbol = ? AND contract_month = ?
            ORDER BY bar_start_utc
            """,
            (contract.con_id, contract.local_symbol, contract.contract_month),
        ).fetchall()
        return tuple(
            HistoricalBar(
                contract=contract,
                bar_start_utc=datetime.fromisoformat(row[0]).astimezone(timezone.utc),
                bar_start_et=datetime.fromisoformat(row[0]).astimezone(timezone.utc).astimezone(ZoneInfo(contract.time_zone)),
                open=Decimal(row[1]), high=Decimal(row[2]), low=Decimal(row[3]),
                close=Decimal(row[4]), volume=Decimal(row[5]), wap=Decimal(row[6]),
                bar_count=row[7], source=row[8], is_complete=bool(row[9]),
            )
            for row in rows
        )

    def record_request(
        self,
        request_id: int,
        con_id: int,
        requested_start_utc: datetime,
        requested_end_utc: datetime,
        bars: tuple[HistoricalBar, ...],
        duplicate_count: int,
        status: str,
        error_code: int | None = None,
        error_message: str | None = None,
    ) -> None:
        """Store one request audit record independently from bar upserts."""
        returned = sorted(bar.bar_start_utc for bar in bars)
        values = (
            request_id,
            con_id,
            requested_start_utc.isoformat(),
            requested_end_utc.isoformat(),
            returned[0].isoformat() if returned else None,
            returned[-1].isoformat() if returned else None,
            len(bars),
            duplicate_count,
            status,
            error_code,
            error_message,
            datetime.now(timezone.utc).isoformat(),
        )
        with self._connection:
            self._connection.execute(
                """
                INSERT OR REPLACE INTO historical_requests (
                    request_id, con_id, requested_start_utc, requested_end_utc,
                    returned_start_utc, returned_end_utc, returned_bars,
                    duplicate_bars, status, error_code, error_message,
                    created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )

    def request_count(self) -> int:
        return self._connection.execute("SELECT COUNT(*) FROM historical_requests").fetchone()[0]

    def save_coverage(self, contract: QualifiedContract, session_date: str, expected_bars: int, actual_bars: int, missing_bars: int, status: str) -> None:
        """Upsert one auditable research-session coverage result."""
        self._ensure_coverage_schema()
        with self._connection:
            self._connection.execute(
                """INSERT INTO session_coverage VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(con_id, local_symbol, contract_month, session_date) DO UPDATE SET expected_bars=excluded.expected_bars,
                actual_bars=excluded.actual_bars, missing_bars=excluded.missing_bars,
                status=excluded.status, updated_at_utc=excluded.updated_at_utc""",
                (contract.con_id, contract.local_symbol, contract.contract_month, session_date,
                 expected_bars, actual_bars, missing_bars, status, datetime.now(timezone.utc).isoformat()),
            )

    def refresh_coverage(self, session_date: date, contract: QualifiedContract) -> tuple[int, int]:
        """Recompute and persist coverage for one CME session and contract."""
        if not is_trading_session(session_date):
            raise ValueError(f"{session_date} is not a CME Equity session")
        expected = expected_bar_starts(session_date)
        start, end = expected[0], expected[-1] + (expected[1] - expected[0])
        rows = self._connection.execute(
            "SELECT bar_start_utc FROM historical_bars WHERE con_id=? AND local_symbol=? AND contract_month=? AND bar_start_utc>=? AND bar_start_utc<? AND is_complete=1",
            (contract.con_id, contract.local_symbol, contract.contract_month, start.isoformat(), end.isoformat()),
        ).fetchall()
        actual = tuple(datetime.fromisoformat(row[0]).astimezone(timezone.utc) for row in rows)
        missing = missing_bar_starts(session_date, actual)
        status = "COMPLETE" if not missing else "DEGRADED"
        self.save_coverage(contract, session_date.isoformat(), len(expected), len(actual), len(missing), status)
        return len(actual), len(missing)

    def _ensure_coverage_schema(self) -> None:
        columns = self._connection.execute("PRAGMA table_info(session_coverage)").fetchall()
        if columns and "con_id" not in {column[1] for column in columns}:
            raise ValueError("legacy session_coverage schema lacks contract identity; create a new database or migrate explicitly")
        self._connection.execute(
            """CREATE TABLE IF NOT EXISTS session_coverage (
                con_id INTEGER NOT NULL, local_symbol TEXT NOT NULL, contract_month TEXT NOT NULL,
                session_date TEXT NOT NULL, expected_bars INTEGER NOT NULL, actual_bars INTEGER NOT NULL,
                missing_bars INTEGER NOT NULL, status TEXT NOT NULL, updated_at_utc TEXT NOT NULL,
                PRIMARY KEY (con_id, local_symbol, contract_month, session_date)
            )"""
        )

    def save_contract_selection(self, session_date: str, contract: QualifiedContract, selected_at_utc: datetime) -> None:
        """Record the actual contract locked for a research session."""
        with self._connection:
            self._connection.execute(
                """CREATE TABLE IF NOT EXISTS contract_selections (
                    session_date TEXT PRIMARY KEY, con_id INTEGER NOT NULL, local_symbol TEXT NOT NULL,
                    contract_month TEXT NOT NULL, selected_at_utc TEXT NOT NULL
                )"""
            )
            self._connection.execute(
                """INSERT INTO contract_selections VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_date) DO UPDATE SET con_id=excluded.con_id,
                local_symbol=excluded.local_symbol, contract_month=excluded.contract_month,
                selected_at_utc=excluded.selected_at_utc""",
                (session_date, contract.con_id, contract.local_symbol, contract.contract_month, selected_at_utc.isoformat()),
            )

    def load_contract_selection(self, session_date: str) -> QualifiedContract | None:
        """Return the contract previously locked for a session, if any."""
        exists = self._connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='contract_selections'"
        ).fetchone()
        if exists is None:
            return None
        row = self._connection.execute(
            "SELECT con_id, local_symbol, contract_month FROM contract_selections WHERE session_date=?", (session_date,)
        ).fetchone()
        if row is None:
            return None
        return QualifiedContract(row[0], row[1], row[2])
    def _create_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS historical_bars (
                con_id INTEGER NOT NULL,
                local_symbol TEXT NOT NULL,
                contract_month TEXT NOT NULL,
                bar_start_utc TEXT NOT NULL,
                bar_start_et TEXT NOT NULL,
                open TEXT NOT NULL, high TEXT NOT NULL, low TEXT NOT NULL,
                close TEXT NOT NULL, volume TEXT NOT NULL, wap TEXT NOT NULL,
                bar_count INTEGER NOT NULL, what_to_show TEXT NOT NULL,
                use_rth INTEGER NOT NULL, source TEXT NOT NULL,
                is_complete INTEGER NOT NULL,
                PRIMARY KEY (con_id, bar_start_utc)
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS historical_requests (
                request_id INTEGER PRIMARY KEY,
                con_id INTEGER NOT NULL,
                requested_start_utc TEXT NOT NULL,
                requested_end_utc TEXT NOT NULL,
                returned_start_utc TEXT,
                returned_end_utc TEXT,
                returned_bars INTEGER NOT NULL,
                duplicate_bars INTEGER NOT NULL,
                status TEXT NOT NULL,
                error_code INTEGER,
                error_message TEXT,
                created_at_utc TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    @staticmethod
    def _row(bar: HistoricalBar) -> tuple[object, ...]:
        return (
            bar.contract.con_id,
            bar.contract.local_symbol,
            bar.contract.contract_month,
            bar.bar_start_utc.isoformat(),
            bar.bar_start_et.isoformat(),
            str(bar.open), str(bar.high), str(bar.low), str(bar.close),
            str(bar.volume), str(bar.wap), bar.bar_count,
            "TRADES", 0, bar.source, int(bar.is_complete),
        )
