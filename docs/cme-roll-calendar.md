# CME Equity Roll Calendar

`config/cme_equity_roll_dates.csv` is the authoritative runtime source for ES
lead-month changes. Each row must come from CME Group's published Equity Index
Roll Dates page and include the publication URL and verification date.

The selector does not derive dates from a third-Friday formula. If IBKR returns
a contract whose `realExpirationDate` is not in this table when it becomes the
next required lead contract, collection fails explicitly. Update and review the
CSV from the CME source before that session starts.
