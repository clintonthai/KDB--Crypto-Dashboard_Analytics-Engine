"""
dashboard.py — Real-time analytics dashboard
Queries the kdb+ RDB every 2 seconds and displays:
  - Live price cards per symbol
  - VWAP vs last price chart
  - Trade volume bar chart
  - Raw tick feed table

Usage:
    python python/dashboard.py
    open http://localhost:8050

Requirements:
    pip install dash dash-bootstrap-components pandas qpython plotly
"""

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, dash_table, Input, Output
from qpython import qconnection

# ── Config ────────────────────────────────────────────────────────────────────

RDB_HOST = "localhost"
RDB_PORT = 5011
REFRESH_MS = 2000
SYMS = ["BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD"]

# ── kdb+ query helper ─────────────────────────────────────────────────────────

def query_rdb(q_str):
    """Open a fresh connection, run a q query, return result as DataFrame."""
    try:
        q = qconnection.QConnection(host=RDB_HOST, port=RDB_PORT, pandas=True)
        q.open()
        result = q(q_str)
        q.close()
        return result
    except Exception as e:
        print(f"RDB query failed: {e}")
        return pd.DataFrame()

# ── App layout ────────────────────────────────────────────────────────────────

app = Dash(__name__)

app.layout = html.Div([
    html.H2("kdb+ Crypto Ticker — Live Dashboard", style={"fontFamily": "Arial", "padding": "1rem"}),

    # Price cards
    html.Div(id="price-cards", style={"display": "flex", "gap": "12px", "padding": "0 1rem 1rem"}),

    # Charts row
    html.Div([
        dcc.Graph(id="vwap-chart", style={"flex": 1}),
        dcc.Graph(id="volume-chart", style={"flex": 1}),
    ], style={"display": "flex", "gap": "12px", "padding": "0 1rem"}),

    # Tick table
    html.H4("Recent Trades", style={"fontFamily": "Arial", "padding": "1rem 1rem 0"}),
    html.Div(id="tick-table", style={"padding": "0 1rem 1rem"}),

    # Refresh interval
    dcc.Interval(id="interval", interval=REFRESH_MS, n_intervals=0),
])

# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("price-cards", "children"),
    Output("vwap-chart", "figure"),
    Output("volume-chart", "figure"),
    Output("tick-table", "children"),
    Input("interval", "n_intervals"),
)
def refresh(_):
    # ── Price cards ──
    last_df = query_rdb("select last price by sym from trade")
    vwap_df = query_rdb("select vwap: wavg[size;price] by sym from trade")

    cards = []
    for sym in SYMS:
        try:
            price = float(last_df.loc[sym, "price"]) if sym in last_df.index else 0.0
            vwap  = float(vwap_df.loc[sym, "vwap"])  if sym in vwap_df.index  else 0.0
            diff_pct = ((price - vwap) / vwap * 100) if vwap else 0.0
            color = "#2e7d32" if diff_pct >= 0 else "#c0392b"
            cards.append(html.Div([
                html.Div(sym, style={"fontSize": "12px", "color": "#777"}),
                html.Div(f"${price:,.2f}", style={"fontSize": "22px", "fontWeight": "500"}),
                html.Div(f"VWAP {vwap:,.2f}  ({diff_pct:+.2f}%)", style={"fontSize": "12px", "color": color}),
            ], style={"background": "#f5f5f5", "borderRadius": "8px", "padding": "12px 16px", "minWidth": "140px"}))
        except Exception:
            pass

    # ── VWAP chart ──
    vwap_fig = go.Figure()
    if not vwap_df.empty and not last_df.empty:
        common = [s for s in SYMS if s in vwap_df.index and s in last_df.index]
        vwap_fig.add_bar(x=common, y=[float(vwap_df.loc[s,"vwap"]) for s in common], name="VWAP", marker_color="#0057A8")
        vwap_fig.add_bar(x=common, y=[float(last_df.loc[s,"price"]) for s in common], name="Last", marker_color="#43A047")
    vwap_fig.update_layout(title="VWAP vs Last Price", barmode="group", font={"family":"Arial"}, margin={"t":40,"b":30})

    # ── Volume chart ──
    vol_df = query_rdb("select volume: sum size by sym from trade")
    vol_fig = go.Figure()
    if not vol_df.empty:
        syms_v = [s for s in SYMS if s in vol_df.index]
        vol_fig.add_bar(x=syms_v, y=[int(vol_df.loc[s,"volume"]) for s in syms_v], marker_color="#7B1FA2")
    vol_fig.update_layout(title="Total Volume by Symbol", font={"family":"Arial"}, margin={"t":40,"b":30})

    # ── Recent trades table ──
    recent_df = query_rdb("select[-20] time, sym, price, size, side from trade")
    if not recent_df.empty:
        recent_df["time"]  = recent_df["time"].astype(str).str[:12]
        recent_df["price"] = recent_df["price"].apply(lambda x: f"{x:,.2f}")
        recent_df["size"]  = recent_df["size"].apply(lambda x: f"{x:,}")
        table = dash_table.DataTable(
            data=recent_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in recent_df.columns],
            style_cell={"fontFamily": "Arial", "fontSize": "13px"},
            style_header={"fontWeight": "500", "backgroundColor": "#f0f0f0"},
        )
    else:
        table = html.P("No data yet — make sure the feed is running.", style={"color":"#999"})

    return cards, vwap_fig, vol_fig, table


if __name__ == "__main__":
    print("Starting dashboard at http://localhost:8050")
    print("Make sure the RDB is running on port 5011")
    app.run(debug=True)
