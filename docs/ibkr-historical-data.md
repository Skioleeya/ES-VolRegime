# IBKR Historical Data Technical Notes

## Scope

This project uses the Linux IB Gateway TWS API on `127.0.0.1:4002` and
`EClient.reqHistoricalData`. The Client Portal Web API is a different product
and its limits must not be applied to this adapter.

## Request Limits

IBKR does not guarantee a fixed download throughput. Historical data is served
from HMDS and may be delayed or paced. The official small-bar pacing rules are:

- Do not repeat an identical request within 15 seconds.
- Do not submit six or more requests for the same contract, exchange, and tick
  type within two seconds.
- Do not exceed 60 historical requests in any ten-minute window.
- A `BID_ASK` request counts twice.

These rules are documented for bars of 30 seconds or less. The downloader will
still apply conservative pacing to all historical requests. The general TWS
API message rate is based on market-data lines; the default reference is 50
requests per second, but this is not a historical-data throughput promise.

Errors must be surfaced, especially error 162 (pacing), 200 (ambiguous or
missing contract), 166 (expired contract), and 2188 (recent historical data
requires the appropriate market-data subscription).

## Duration and Bar Size

`5 mins` is an officially supported bar size. Valid duration units are `S`,
`D`, `W`, `M`, and `Y`. The current official maximum-duration table lists the
following maximums for 5-minute bars: `86400 S`, `365 D`, `52 W`, `12 M`, and
`68 Y`. These are parameter limits, not guarantees that an ES contract has
that much available history.

The downloader should use bounded chunks and wait for `historicalDataEnd`
before submitting the next chunk. It must not assume that a larger legal
duration is faster or returns a complete dataset.

## Time Semantics

Requests may use `YYYYMMDD HH:mm:ss TMZ`, for example:

```text
20260827 16:00:00 America/New_York
```

UTC request syntax is also supported:

```text
20260827-20:00:00
```

If no timezone is supplied, IBKR interprets the value in the TWS or Gateway
operator timezone. Returned dates depend on `formatDate`: `1` is a timezone
string, `2` is Unix epoch seconds, and `3` is a shortened date/time form. The
project uses `formatDate=2`, converts immediately to timezone-aware UTC, and
derives `America/New_York` values only for session labeling. A bar timestamp is
the beginning of that bar.

## ES-Specific Rules

Use a fully qualified expiring futures contract, including its contract month,
and persist the returned `conId`, `localSymbol`, `tradingClass`, `timeZoneId`,
`tradingHours`, and `liquidHours`. Use `TRADES` and `useRTH=0` so Overnight,
Pre-market, and Cash Session observations remain available. Continuous futures
are not the storage identity for this research dataset; roll decisions belong
to a separate policy module.

Historical bars are IBKR's filtered/aggregated product. Volume must therefore
be labeled as IBKR historical volume and not treated as an unfiltered exchange
feed.

## Completed Bars

With `keepUpToDate=True`, IBKR may emit repeated updates for the same timestamp
every few seconds until a bar closes. The research pipeline accepts only
completed bars. Historical backfill uses `keepUpToDate=False`; live updates
will be a later, separate adapter.

## Official References

- [Requesting Historical Bars](https://www.interactivebrokers.com/docs/tws-api/doc/market-data-historical/historical-bars/requesting-historical-bars)
- [Historical Bar Sizes](https://www.interactivebrokers.com/docs/tws-api/doc/market-data-historical/historical-bars/historical-bar-sizes)
- [Max Duration Per Bar Size](https://www.interactivebrokers.com/docs/tws-api/doc/market-data-historical/historical-bars/max-duration-per-bar-size)
- [Pacing Violations](https://www.interactivebrokers.com/docs/tws-api/doc/market-data-historical/historical-data-limitations/pacing-violations-for-small-bars-30-secs-or-less)
- [Format Date Received](https://www.interactivebrokers.com/docs/tws-api/doc/market-data-historical/historical-bars/format-date-received)
- [Receiving Historical Bars](https://www.interactivebrokers.com/docs/tws-api/doc/market-data-historical/historical-bars/receiving-historical-bars)
- [Contract Details](https://www.interactivebrokers.com/docs/tws-api/doc/contracts-financial-instruments/contract-details/introduction)
- [Error Codes](https://www.interactivebrokers.com/docs/tws-api/doc/error-handling/error-codes)

