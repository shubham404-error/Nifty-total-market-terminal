import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import io

def market_chart(
    frame: pd.DataFrame,
    symbol: str,
    overlays: list[str],
    rsi_col: str = "RSI14",
    days: int = 180,
    cross_columns: list[str] | None = None,
    rsi_lines: list[tuple[float, str]] | None = None,
):
    """Price, volume and RSI chart. Missing optional columns are handled safely."""
    chart = frame.sort_values("Date").tail(days).copy()
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.025,
        row_heights=[0.66, 0.14, 0.20],
    )
    fig.add_trace(go.Candlestick(
        x=chart["Date"], open=chart["Open"], high=chart["High"],
        low=chart["Low"], close=chart["Close"], name=symbol,
        increasing_line_color="#26c281", increasing_fillcolor="#26c281",
        decreasing_line_color="#ef6461", decreasing_fillcolor="#ef6461",
    ), row=1, col=1)

    colors = {"EMA9":"#6ea8fe", "EMA21":"#f0a51a", "SMA20":"#b084f5",
              "SMA50":"#14b8a6", "SMA200":"#ef4444", "EMA255":"#f59e0b"}
    for col in overlays:
        if col in chart.columns:
            fig.add_trace(go.Scatter(
                x=chart["Date"], y=chart[col], mode="lines", name=col,
                line={"width":1.8, "color":colors.get(col,"#cbd5e1")},
            ), row=1, col=1)

    for cross_col in cross_columns or []:
        if cross_col not in chart.columns:
            continue
        marks=chart.loc[chart[cross_col].fillna(False)]
        if marks.empty:
            continue
        label={"Cross9_21":"9/21 Bullish Cross", "Cross20_50":"20/50 Bullish Cross", "Cross50_200":"Golden Cross"}.get(cross_col,"Bullish Cross")
        fig.add_trace(go.Scatter(
            x=marks["Date"], y=marks["Close"], mode="markers", name=label,
            marker={"symbol":"triangle-up","size":9,"color":"#26c281","line":{"color":"#080a0d","width":1}},
        ), row=1, col=1)

    if "Volume" in chart.columns:
        fig.add_trace(go.Bar(x=chart["Date"], y=chart["Volume"], name="Volume", marker_color="#64748b"), row=2, col=1)
    if "VolumeSMA20" in chart.columns:
        fig.add_trace(go.Scatter(x=chart["Date"], y=chart["VolumeSMA20"], mode="lines", name="20D Avg Vol", line={"width":1.3,"color":"#f0a51a"}), row=2, col=1)

    if rsi_col in chart.columns:
        fig.add_trace(go.Scatter(x=chart["Date"], y=chart[rsi_col], mode="lines", name=rsi_col, line={"width":1.7,"color":"#8ab4ff"}), row=3, col=1)
        for level,label in (rsi_lines or [(30,"RSI 30"),(70,"RSI 70")]):
            fig.add_hline(y=level,row=3,col=1,line_dash="dot",line_color="#46515f",line_width=1,
                          annotation_text=label,annotation_position="top left",annotation_font={"size":9,"color":"#7f8b99"})

    fig.update_layout(height=690, margin={"l":8,"r":8,"t":40,"b":10}, paper_bgcolor="#080a0d",
        plot_bgcolor="#080a0d", font={"family":"Helvetica, Arial, sans-serif","color":"#e9eef3"},
        legend={"orientation":"h","y":1.03,"x":0,"font":{"size":10}}, hovermode="x unified",
        xaxis_rangeslider_visible=False, xaxis2_rangeslider_visible=False, xaxis3_rangeslider_visible=False)
    for row in (1,2,3):
        fig.update_yaxes(gridcolor="#1d232b",linecolor="#252c35",showline=False,zeroline=False,row=row,col=1)
    fig.update_yaxes(range=[0,100], title_text="RSI", title_font={"size":10,"color":"#8c98a6"}, row=3,col=1)
    return fig


def _ai_chart_png(frame, symbol):
    if frame is None or frame.empty:
        return None

    plot = frame.tail(180).copy()
    x = pd.to_datetime(plot["Date"], errors="coerce") if "Date" in plot.columns else plot.index

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 6.5),
        gridspec_kw={"height_ratios": [3, 1]},
        sharex=True,
    )

    if "Close" in plot.columns:
        ax1.plot(x, pd.to_numeric(plot["Close"], errors="coerce"), label="Close", linewidth=1.6)

    for col in ["EMA9", "EMA21", "SMA20", "SMA50", "SMA200", "EMA255"]:
        if col in plot.columns:
            ax1.plot(x, pd.to_numeric(plot[col], errors="coerce"), label=col, linewidth=1.0)

    ax1.set_title(f"{symbol} . Existing terminal indicator history")
    ax1.legend(loc="upper left", ncol=3, fontsize=8)
    ax1.grid(alpha=0.2)

    if "RSI14" in plot.columns:
        ax2.plot(x, pd.to_numeric(plot["RSI14"], errors="coerce"), label="RSI14", linewidth=1.2)
        for level in [30, 50, 70]:
            ax2.axhline(level, linewidth=0.8, linestyle="--", alpha=0.6)
        ax2.set_ylim(0, 100)
        ax2.grid(alpha=0.2)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


