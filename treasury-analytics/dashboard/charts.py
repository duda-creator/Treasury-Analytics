import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


COLORS = {
    "bg": "#0f1117",
    "surface": "#1a1d27",
    "border": "#2a2d3e",
    "text": "#e2e8f0",
    "text_muted": "#64748b",
    "blue": "#3b82f6",
    "teal": "#14b8a6",
    "amber": "#f59e0b",
    "red": "#ef4444",
    "green": "#22c55e",
    "purple": "#8b5cf6",
    "chart_bg": "rgba(0,0,0,0)",
}

ENTITY_COLORS = {
    "E001": "#3b82f6",
    "E002": "#14b8a6",
    "E003": "#8b5cf6",
    "E004": "#f59e0b",
    "E005": "#22c55e",
    "EGROUP": "#e2e8f0",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["chart_bg"],
    plot_bgcolor=COLORS["chart_bg"],
    font=dict(family="Inter, system-ui, sans-serif", color=COLORS["text"], size=12),
    margin=dict(l=48, r=24, t=36, b=36),
    legend=dict(
        bgcolor="rgba(26,29,39,0.8)",
        bordercolor=COLORS["border"],
        borderwidth=1,
        font=dict(size=11),
    ),
    xaxis=dict(
        gridcolor=COLORS["border"],
        linecolor=COLORS["border"],
        zerolinecolor=COLORS["border"],
    ),
    yaxis=dict(
        gridcolor=COLORS["border"],
        linecolor=COLORS["border"],
        zerolinecolor=COLORS["border"],
    ),
)


def fig_lcr_timeseries(df: pd.DataFrame, scenario: str) -> go.Figure:
    fig = go.Figure()
    for entity_id, grp in df.groupby("entity_id"):
        name = grp["entity_name"].iloc[0].replace("SCB ", "").replace(" Branch", "")
        fig.add_trace(
            go.Scatter(
                x=grp["date"],
                y=grp["lcr_ratio_pct"],
                name=name,
                mode="lines",
                line=dict(color=ENTITY_COLORS.get(entity_id, "#888"), width=1.8),
                hovertemplate="%{y:.1f}%<extra>" + name + "</extra>",
            )
        )

    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color=COLORS["red"],
        line_width=1,
        annotation_text="Regulatory min 100%",
        annotation_font_color=COLORS["red"],
        annotation_font_size=10,
    )
    fig.update_layout(
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k != "yaxis"},
        title=dict(text=f"LCR - {scenario} scenario", font_size=13),
        yaxis_title="LCR (%)",
        xaxis_title=None,
        yaxis=dict(**PLOTLY_LAYOUT["yaxis"], range=[70, 175]),
    )
    return fig


def fig_lcr_bar(df: pd.DataFrame, scenario: str) -> go.Figure:
    colors = [COLORS["red"] if v < 110 else COLORS["teal"] for v in df["lcr_ratio_pct"]]
    short_names = df["entity_name"].str.replace("SCB ", "").str.replace(" Branch", "")
    fig = go.Figure(
        [
            go.Bar(
                x=short_names,
                y=df["lcr_ratio_pct"],
                marker_color=colors,
                text=df["lcr_ratio_pct"].map(lambda v: f"{v:.1f}%"),
                textposition="outside",
                textfont_size=11,
                hovertemplate="<b>%{x}</b><br>LCR: %{y:.1f}%<extra></extra>",
            )
        ]
    )
    fig.add_hline(y=100, line_dash="dash", line_color=COLORS["red"], line_width=1)
    fig.add_hline(
        y=110,
        line_dash="dot",
        line_color=COLORS["amber"],
        line_width=1,
        annotation_text="Internal target 110%",
        annotation_font_size=10,
        annotation_font_color=COLORS["amber"],
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text=f"LCR by entity - latest ({scenario})", font_size=13),
        yaxis_title="LCR (%)",
        yaxis_range=[0, 185],
        showlegend=False,
    )
    return fig


def fig_ftp_waterfall(df_components: pd.DataFrame) -> go.Figure:
    if df_components.empty:
        return go.Figure()

    row = df_components.iloc[0]
    base = float(row["base_ftp_mm"])
    lp = float(row["lp_mm"])
    cof = float(row["cof_mm"])
    col = float(row["col_mm"])
    total = base + lp + cof + col

    labels = ["Base FTP", "Liquidity premium", "Cost of funds", "Cost of liquidity", "Net FTP"]
    values = [base, lp, cof, col, total]
    measure = ["relative", "relative", "relative", "relative", "total"]

    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=measure,
            x=labels,
            y=values,
            text=[f"{v:+.1f}" for v in values],
            textposition="outside",
            textfont_size=11,
            connector=dict(line=dict(color=COLORS["border"], width=1, dash="dot")),
            increasing=dict(marker_color=COLORS["teal"]),
            decreasing=dict(marker_color=COLORS["red"]),
            totals=dict(marker_color=COLORS["blue"]),
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="FTP component attribution (USD mm)", font_size=13),
        yaxis_title="USD mm",
        showlegend=False,
    )
    return fig


def fig_ftp_by_product(df: pd.DataFrame) -> go.Figure:
    df_sorted = df.sort_values("total_pnl_usd_k")
    colors = [COLORS["red"] if v < 0 else COLORS["teal"] for v in df_sorted["total_pnl_usd_k"]]
    fig = go.Figure(
        [
            go.Bar(
                x=df_sorted["total_pnl_usd_k"] / 1000,
                y=df_sorted["product_name"],
                orientation="h",
                marker_color=colors,
                text=df_sorted["total_pnl_usd_k"].map(lambda v: f"{v/1000:+.1f}M"),
                textposition="outside",
                textfont_size=10,
                hovertemplate="<b>%{y}</b><br>FTP P&L: USD %{x:.1f}M<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        **{k: v for k, v in PLOTLY_LAYOUT.items() if k != "yaxis"},
        title=dict(text="FTP P&L by product (USD mm)", font_size=13),
        xaxis_title="USD mm",
        showlegend=False,
        yaxis=dict(**PLOTLY_LAYOUT["yaxis"], automargin=True),
    )
    return fig


def fig_liquidity_gap(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.65, 0.35],
        vertical_spacing=0.06,
    )

    fig.add_trace(
        go.Bar(
            x=df["bucket_name"],
            y=df["inflows"],
            name="Inflows",
            marker_color=COLORS["teal"],
            opacity=0.85,
            hovertemplate="%{y:,.0f} USD mm<extra>Inflows</extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=df["bucket_name"],
            y=-df["outflows"],
            name="Outflows",
            marker_color=COLORS["red"],
            opacity=0.85,
            hovertemplate="%{y:,.0f} USD mm<extra>Outflows</extra>",
        ),
        row=1,
        col=1,
    )

    gap_colors = [COLORS["red"] if v < 0 else COLORS["teal"] for v in df["cum_gap"]]
    fig.add_trace(
        go.Bar(
            x=df["bucket_name"],
            y=df["cum_gap"],
            name="Cumulative gap",
            marker_color=gap_colors,
            hovertemplate="%{y:,.0f} USD mm<extra>Cumulative gap</extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_hline(y=0, row=2, col=1, line_color=COLORS["border"], line_width=1)

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Liquidity gap - maturity ladder (USD mm)", font_size=13),
        barmode="overlay",
    )
    fig.update_yaxes(
        title_text="USD mm",
        row=1,
        col=1,
        gridcolor=COLORS["border"],
        zerolinecolor=COLORS["border"],
    )
    fig.update_yaxes(
        title_text="Cum. gap",
        row=2,
        col=1,
        gridcolor=COLORS["border"],
        zerolinecolor=COLORS["border"],
    )
    return fig
