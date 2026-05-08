/ rdb.q — Real-Time Database (RDB)
/ Usage: q q/rdb.q -p 5011
/
/ The RDB holds today's data entirely in memory.
/ It subscribes to the TP on startup and receives every tick via upd[].
/ At end of day it writes its tables to the HDB on disk.

\l q/schema.q

/ tickerplant handle — connect on startup
TP: hopen `::5010

/ subscribe to both trade and quote tables
.u.upd: {[t;x] insert[t;x] }

/ send subscription request to TP for each table
{
  r: TP (`.u.sub; x; `);
  / r is (tablename; schema) — initialize local table
  @[`.;  r 0; :; r 1]
 } each `trade`quote;

-1 "RDB subscribed to TP. Listening on port ", string system "p";

/ end-of-day write to HDB
/ called by the TP at day rollover
.u.end: {[d]
  -1 "EOD: writing to HDB for date ", string d;
  / write each table as a partitioned splayed table
  {
    t: value x;
    / create date partition directory
    path: `:hdb/, string[d], "/", string[x], "/";
    / sort by time within each sym partition before saving
    t: `sym`time xasc t;
    (hsym `$string[path]) set t;
    -1 "  wrote ", string[count t], " rows for ", string x;
   } each `trade`quote;
  / clear in-memory tables for new day
  trade:: 0#trade;
  quote:: 0#quote;
  -1 "EOD complete.";
 }
