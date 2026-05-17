from dash import dcc, html

from charts import COLORS
from data import get_entities, get_reporting_periods


entities_df = get_entities()
periods = get_reporting_periods()
entity_opts = [
    {"label": r["entity_name"].replace("SCB ", ""), "value": r["entity_id"]}
    for _, r in entities_df.iterrows()
]
entity_opts_no_group = [e for e in entity_opts if e["value"] != "EGROUP"]
period_opts = [{"label": p, "value": p} for p in periods]

DROPDOWN_STYLE = dict(
    backgroundColor=COLORS["surface"],
    color=COLORS["text"],
    border=f"1px solid {COLORS['border']}",
    borderRadius="6px",
)


def control_row(*children):
    return html.Div(
        children,
        style=dict(
            display="flex",
            alignItems="center",
            gap="16px",
            padding="12px 20px",
            borderBottom=f"1px solid {COLORS['border']}",
            backgroundColor=COLORS["surface"],
        ),
    )


def label(text):
    return html.Span(
        text,
        style=dict(
            fontSize="12px",
            color=COLORS["text_muted"],
            whiteSpace="nowrap",
            fontWeight="500",
        ),
    )


def metric_card(title, value_id, unit=""):
    return html.Div(
        [
            html.Div(
                title,
                style=dict(fontSize="11px", color=COLORS["text_muted"], marginBottom="4px"),
            ),
            html.Div(
                [
                    html.Span(id=value_id, style=dict(fontSize="22px", fontWeight="500")),
                    html.Span(
                        unit,
                        style=dict(fontSize="13px", color=COLORS["text_muted"], marginLeft="4px"),
                    ),
                ]
            ),
        ],
        style=dict(
            background=COLORS["surface"],
            border=f"1px solid {COLORS['border']}",
            borderRadius="8px",
            padding="14px 18px",
            minWidth="140px",
        ),
    )


tab_lcr = html.Div(
    [
        control_row(
            label("Entities"),
            dcc.Dropdown(
                id="lcr-entities",
                options=entity_opts_no_group,
                value=["E001", "E002", "E003", "E004", "E005"],
                multi=True,
                style=dict(minWidth="360px", **DROPDOWN_STYLE),
            ),
            label("Scenario"),
            dcc.Dropdown(
                id="lcr-scenario",
                options=[
                    {"label": "Base", "value": "Base"},
                    {"label": "Stressed", "value": "Stressed"},
                ],
                value="Base",
                clearable=False,
                style=dict(minWidth="130px", **DROPDOWN_STYLE),
            ),
        ),
        html.Div(
            [
                metric_card("Group LCR (latest)", "kpi-group-lcr", "%"),
                metric_card("Entities below 110%", "kpi-below-110", ""),
                metric_card("Min headroom", "kpi-min-headroom", "bps"),
                metric_card("Total HQLA", "kpi-total-hqla", "USD bn"),
            ],
            style=dict(
                display="flex",
                gap="12px",
                padding="16px 20px",
                borderBottom=f"1px solid {COLORS['border']}",
            ),
        ),
        html.Div(
            [
                dcc.Graph(id="lcr-timeseries", config=dict(displayModeBar=False), style=dict(flex="1")),
                dcc.Graph(id="lcr-bar", config=dict(displayModeBar=False), style=dict(flex="1")),
            ],
            style=dict(display="flex", gap="0", padding="20px", paddingBottom="0"),
        ),
    ]
)


tab_ftp = html.Div(
    [
        control_row(
            label("Entity"),
            dcc.Dropdown(
                id="ftp-entity",
                options=entity_opts_no_group,
                value="E001",
                clearable=False,
                style=dict(minWidth="260px", **DROPDOWN_STYLE),
            ),
            label("Period"),
            dcc.Dropdown(
                id="ftp-period",
                options=period_opts,
                value=periods[-1] if periods else None,
                clearable=False,
                style=dict(minWidth="130px", **DROPDOWN_STYLE),
            ),
        ),
        html.Div(
            [
                dcc.Graph(id="ftp-waterfall", config=dict(displayModeBar=False), style=dict(flex="1")),
                dcc.Graph(id="ftp-by-product", config=dict(displayModeBar=False), style=dict(flex="1")),
            ],
            style=dict(display="flex", gap="0", padding="20px"),
        ),
    ]
)


tab_gap = html.Div(
    [
        control_row(
            label("Entity"),
            dcc.Dropdown(
                id="gap-entity",
                options=entity_opts_no_group,
                value="E001",
                clearable=False,
                style=dict(minWidth="260px", **DROPDOWN_STYLE),
            ),
            label("Period"),
            dcc.Dropdown(
                id="gap-period",
                options=period_opts,
                value=periods[-1] if periods else None,
                clearable=False,
                style=dict(minWidth="130px", **DROPDOWN_STYLE),
            ),
        ),
        html.Div(dcc.Graph(id="gap-chart", config=dict(displayModeBar=False)), style=dict(padding="20px")),
    ]
)


def build_layout():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                "Treasury Analytics",
                                style=dict(fontSize="16px", fontWeight="500", color=COLORS["text"]),
                            ),
                            html.Span(
                                "  |  Demo prototype - synthetic data",
                                style=dict(fontSize="12px", color=COLORS["text_muted"]),
                            ),
                        ]
                    ),
                ],
                style=dict(
                    padding="14px 20px",
                    borderBottom=f"1px solid {COLORS['border']}",
                    backgroundColor=COLORS["surface"],
                    display="flex",
                    alignItems="center",
                ),
            ),
            dcc.Tabs(
                id="tabs",
                value="lcr",
                children=[
                    dcc.Tab(
                        label="LCR Monitor",
                        value="lcr",
                        style=dict(
                            color=COLORS["text_muted"],
                            backgroundColor=COLORS["bg"],
                            border=f"1px solid {COLORS['border']}",
                            padding="10px 20px",
                        ),
                        selected_style=dict(
                            color=COLORS["text"],
                            backgroundColor=COLORS["surface"],
                            border=f"1px solid {COLORS['border']}",
                            borderBottom=f"2px solid {COLORS['blue']}",
                            padding="10px 20px",
                        ),
                    ),
                    dcc.Tab(
                        label="FTP Attribution",
                        value="ftp",
                        style=dict(
                            color=COLORS["text_muted"],
                            backgroundColor=COLORS["bg"],
                            border=f"1px solid {COLORS['border']}",
                            padding="10px 20px",
                        ),
                        selected_style=dict(
                            color=COLORS["text"],
                            backgroundColor=COLORS["surface"],
                            border=f"1px solid {COLORS['border']}",
                            borderBottom=f"2px solid {COLORS['blue']}",
                            padding="10px 20px",
                        ),
                    ),
                    dcc.Tab(
                        label="Liquidity Gap",
                        value="gap",
                        style=dict(
                            color=COLORS["text_muted"],
                            backgroundColor=COLORS["bg"],
                            border=f"1px solid {COLORS['border']}",
                            padding="10px 20px",
                        ),
                        selected_style=dict(
                            color=COLORS["text"],
                            backgroundColor=COLORS["surface"],
                            border=f"1px solid {COLORS['border']}",
                            borderBottom=f"2px solid {COLORS['blue']}",
                            padding="10px 20px",
                        ),
                    ),
                ],
                style=dict(backgroundColor=COLORS["bg"]),
            ),
            html.Div(id="tab-content"),
        ],
        style=dict(
            fontFamily="Inter, system-ui, sans-serif",
            backgroundColor=COLORS["bg"],
            minHeight="100vh",
            color=COLORS["text"],
        ),
    )
