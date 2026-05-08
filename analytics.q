/ analytics.q — named query functions for the RDB
/ Load in a q session connected to the RDB:
/   h: hopen 5011
/   h "\l q/analytics.q"
/ Or run standalone queries directly (see README)

/ ── VWAP ─────────────────────────────────────────────────────────────────────
/ Volume-weighted average price per symbol
/ Maps each trade's price weighted by its size
vwap: {
  select vwap: wavg[size; price] by sym from trade
 }

/ VWAP for a single symbol
vwapSym: {[s]
  select vwap: wavg[size; price] from trade where sym = s
 }

/ ── MOVING AVERAGE ───────────────────────────────────────────────────────────
/ N-period moving average of price for a given symbol
mavgN: {[s; n]
  select time, sym, price, ma: n mavg price
    from trade
   where sym = s
 }

/ ── VOLATILITY ───────────────────────────────────────────────────────────────
/ Standard deviation of price per symbol (proxy for volatility)
vol: {
  select volatility: dev price by sym from trade
 }

/ ── SPREAD ───────────────────────────────────────────────────────────────────
/ Average bid-ask spread per symbol from quote table
spread: {
  select avgSpread: avg ask - bid by sym from quote
 }

/ ── ASOF JOIN ────────────────────────────────────────────────────────────────
/ Map each trade to the most recent quote at time of execution
/ aj[] is kdb+'s asof join — critical for trade cost analysis
tradesWithQuotes: {
  aj[`sym`time; trade; quote]
 }

/ ── OHLC ─────────────────────────────────────────────────────────────────────
/ Open/High/Low/Close per symbol for current session
ohlc: {
  select
    open:  first price,
    high:  max   price,
    low:   min   price,
    close: last  price,
    volume: sum  size,
    trades: count i
  by sym from trade
 }

/ ── TRADE IMBALANCE ──────────────────────────────────────────────────────────
/ Buy vs sell volume imbalance — positive = more buying pressure
imbalance: {
  select
    buyVol:  sum size where side = `buy,
    sellVol: sum size where side = `sell,
    netFlow: (sum size where side=`buy) - sum size where side=`sell
  by sym from trade
 }

/ ── LARGE TRADES ─────────────────────────────────────────────────────────────
/ Filter trades above a size threshold (default 2000)
largeTrades: {[threshold]
  select from trade where size > threshold
 }

-1 "analytics.q loaded — functions: vwap, vwapSym, mavgN, vol, spread, tradesWithQuotes, ohlc, imbalance, largeTrades";
