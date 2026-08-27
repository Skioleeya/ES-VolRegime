# ES Contract Roll Policy

The system determines the ES lead contract from the IBKR futures chain and
`config/session.toml`. It makes no runtime request to CME and does not maintain
a CME date table.

For the default policy, each March, June, September, and December contract rolls
at the 18:00 ET session start on the Sunday before the Monday preceding that
month's third Friday. The computation uses the contract month, not IBKR's real
expiration date. This keeps the roll date stable when a holiday moves the
contract's actual expiration, such as June 2026.

The selector sorts the IBKR chain by contract month. Before the configured
cutover it selects the nearest quarterly contract; at and after it selects the
next available quarterly contract and locks that `conId` for the research
session. An empty chain, malformed contract month, non-quarterly month, or a
missing next contract fails explicitly. There is no date-table, expiry-minus-N,
or volume-based fallback.

An exchange exceptional-rule change cannot be discovered without an external
source. Operations must treat an explicit selector failure or contract-chain
anomaly as an alert requiring review.
