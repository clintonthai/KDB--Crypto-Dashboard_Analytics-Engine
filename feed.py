"""
feed.py — Simulated crypto price feed
Connects to the kdb+ Tickerplant on port 5010 and streams
randomized trade and quote ticks for BTC, ETH, SOL, BNB.

Usage:
    python python/feed.py

Requirements:
    pip install qpython   # kdb+ IPC library for Python
"""

import time
import random
import datetime
from qpython import qconnection
from qpython.qtype import QSymbol

# ── Config ────────────────────────────────────────────────────────────────────

TP_HOST = "localhost"
TP_PORT = 5010
TICK_INTERVAL = 0.5   # seconds between ticks

# Base prices — randomness walks around these
BASE_PRICES = {
    "BTCUSD": 67800.0,
    "ETHUSD":  3420.0,
    "SOLUSD":   148.0,
    "BNBUSD":   412.0,
}

# Max % move per tick
VOLATILITY = 0.0008

# ── Helpers ───────────────────────────────────────────────────────────────────

prices = dict(BASE_PRICES)

def next_price(sym):
    """Random walk around the base price."""
    move = prices[sym] * VOLATILITY * (random.random() - 0.499)
    prices[sym] = max(prices[sym] + move, BASE_PRICES[sym] * 0.90)
    return round(prices[sym], 2)

def make_trade_tick(sym):
    """Return a trade row as a list matching the kdb+ trade schema."""
    price = next_price(sym)
    size  = random.randint(100, 5000)
    side  = random.choice(["buy", "sell"])
    now   = datetime.datetime.now().time()
    return [now, QSymbol(sym), price, size, QSymbol(side)]

def make_quote_tick(sym):
    """Return a quote row — bid slightly below, ask slightly above mid."""
    mid    = prices[sym]
    spread = mid * 0.0002
    bid    = round(mid - spread / 2, 2)
    ask    = round(mid + spread / 2, 2)
    bsize  = random.randint(500, 10000)
    asize  = random.randint(500, 10000)
    now    = datetime.datetime.now().time()
    return [now, QSymbol(sym), bid, ask, bsize, asize]

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Connecting to Tickerplant at {TP_HOST}:{TP_PORT}...")
    q = qconnection.QConnection(host=TP_HOST, port=TP_PORT)
    q.open()
    print("Connected. Streaming ticks...")

    syms = list(BASE_PRICES.keys())
    tick_count = 0

    try:
        while True:
            sym = random.choice(syms)

            # Send trade tick to TP via upd[]
            trade_row = make_trade_tick(sym)
            q.sendSync("upd", "trade", trade_row)

            # Send quote tick every 3 trades
            if tick_count % 3 == 0:
                quote_row = make_quote_tick(sym)
                q.sendSync("upd", "quote", quote_row)

            tick_count += 1
            if tick_count % 100 == 0:
                print(f"  {tick_count} ticks sent — latest: {sym} @ {prices[sym]:.2f}")

            time.sleep(TICK_INTERVAL)

    except KeyboardInterrupt:
        print(f"\nFeed stopped. Total ticks sent: {tick_count}")
    finally:
        q.close()

if __name__ == "__main__":
    main()
