/ schema.q — table definitions for the crypto tickerplant
/ loaded by both the TP and RDB on startup

/ trade table — one row per executed trade tick
trade:([]
  time:  `time$();
  sym:   `symbol$();
  price: `float$();
  size:  `long$();
  side:  `symbol$()
 )

/ quote table — one row per bid/ask update
quote:([]
  time:  `time$();
  sym:   `symbol$();
  bid:   `float$();
  ask:   `float$();
  bsize: `long$();
  asize: `long$()
 )

/ supported symbols
SYMS: `BTCUSD`ETHUSD`SOLUSD`BNBUSD
