/ tick.q — Tickerplant (TP)
/ Usage: q q/tick.q sym . -p 5010
/
/ The tickerplant is the entry point for all market data.
/ It receives raw ticks, timestamps them, and publishes to subscribers (RDB).

\l q/schema.q

/ subscriber list — processes that have called .u.sub[]
.u.w: ()! ()

/ publish tick to all subscribers
/ t = table name (symbol), x = row data (list)
.u.pub: {[t;x]
  / iterate over subscribers and send the update
  {[t;x;w] neg[w] `.u.upd, (t; x) } [t; x] each .u.w[t]
 }

/ subscribe handler — called by RDB on startup
/ t = table name, s = symbols requested
.u.sub: {[t;s]
  / register the calling handle under the table name
  .u.w[t]: distinct .u.w[t], neg .z.w;
  / return current schema so subscriber can init its table
  (t; value t)
 }

/ tick insert and publish — called by the Python feed
/ t = table name, x = (time; sym; price; size; side)
upd: {[t;x]
  / stamp with current time if time is null
  x[0]: $[null x[0]; .z.t; x[0]];
  / insert into local TP table
  insert[t; x];
  / publish to all subscribers
  .u.pub[t; x]
 }

/ end-of-day — save TP log and reset
.u.end: {
  system "mv ", (string .z.d), "/tick.log ", (string .z.d-1), ".log 2>/dev/null";
 }

-1 "Tickerplant started on port ", string system "p";
-1 "Waiting for feed connections...";
