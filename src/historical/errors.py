"""Explicit failures raised by the historical-data boundary."""


class HistoricalError(RuntimeError):
    """Base class for historical-data failures."""


class HistoricalTimeout(HistoricalError):
    """The expected callback did not arrive before the deadline."""


class HistoricalBrokerError(HistoricalError):
    """IBKR returned an error for the active historical request."""


class HistoricalEmpty(HistoricalError):
    """IBKR completed the request without returning bars."""

