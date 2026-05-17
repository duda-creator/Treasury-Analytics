import plotly.graph_objects as go
from dash import Input, Output

from charts import (
    fig_ftp_by_product,
    fig_ftp_waterfall,
    fig_lcr_bar,
    fig_lcr_timeseries,
    fig_liquidity_gap,
)
from data import (
    get_ftp_attribution_waterfall,
    get_ftp_waterfall,
    get_lcr_latest_bar,
    get_lcr_timeseries,
    get_liquidity_gap,
)
from layout import tab_ftp, tab_gap, tab_lcr


def register_callbacks(app):
    @app.callback(Output("tab-content", "children"), Input("tabs", "value"))
    def render_tab(tab):
        return {"lcr": tab_lcr, "ftp": tab_ftp, "gap": tab_gap}.get(tab, tab_lcr)

    @app.callback(
        Output("lcr-timeseries", "figure"),
        Output("lcr-bar", "figure"),
        Output("kpi-group-lcr", "children"),
        Output("kpi-below-110", "children"),
        Output("kpi-min-headroom", "children"),
        Output("kpi-total-hqla", "children"),
        Input("lcr-entities", "value"),
        Input("lcr-scenario", "value"),
    )
    def update_lcr(entity_ids, scenario):
        if not entity_ids:
            empty = go.Figure()
            return empty, empty, "-", "-", "-", "-"

        ts_df = get_lcr_timeseries(entity_ids, scenario)
        bar_df = get_lcr_latest_bar(scenario)

        grp = get_lcr_timeseries(["EGROUP"], scenario)
        grp_latest = grp.sort_values("date").iloc[-1] if not grp.empty else None
        group_lcr_str = f"{grp_latest['lcr_ratio_pct']:.1f}" if grp_latest is not None else "-"
        below_110 = int((bar_df["lcr_ratio_pct"] < 110).sum())
        min_hw = int(bar_df["headroom_bps"].min()) if not bar_df.empty else 0
        total_hqla = bar_df["hqla_total_usd_bn"].sum() if not bar_df.empty else 0

        return (
            fig_lcr_timeseries(ts_df, scenario),
            fig_lcr_bar(bar_df, scenario),
            group_lcr_str,
            str(below_110),
            f"{min_hw:,}",
            f"{total_hqla:.1f}",
        )

    @app.callback(
        Output("ftp-waterfall", "figure"),
        Output("ftp-by-product", "figure"),
        Input("ftp-entity", "value"),
        Input("ftp-period", "value"),
    )
    def update_ftp(entity_id, period):
        if not entity_id or not period:
            return go.Figure(), go.Figure()

        wf_df = get_ftp_attribution_waterfall(entity_id, period)
        prd_df = get_ftp_waterfall(entity_id, period)
        return fig_ftp_waterfall(wf_df), fig_ftp_by_product(prd_df)

    @app.callback(
        Output("gap-chart", "figure"),
        Input("gap-entity", "value"),
        Input("gap-period", "value"),
    )
    def update_gap(entity_id, period):
        if not entity_id or not period:
            return go.Figure()

        df = get_liquidity_gap(entity_id, period)
        return fig_liquidity_gap(df)
