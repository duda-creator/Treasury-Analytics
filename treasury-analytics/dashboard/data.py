import os
from pathlib import Path

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "warehouse" / "treasury.duckdb"


def _resolve_db_path() -> str:
    raw_path = os.getenv("DB_PATH")
    if not raw_path:
        return str(DEFAULT_DB_PATH)

    path = Path(raw_path)
    if path.is_absolute():
        return str(path)

    return str((PROJECT_ROOT / path).resolve())


def get_con():
    return duckdb.connect(_resolve_db_path(), read_only=True)


def q(sql: str, **params) -> pd.DataFrame:
    with get_con() as con:
        return con.execute(sql, list(params.values())).df()


def get_entities() -> pd.DataFrame:
    return q("SELECT entity_id, entity_name FROM dim_entity ORDER BY entity_id")


def get_lcr_timeseries(entity_ids: list, scenario: str) -> pd.DataFrame:
    ids = ", ".join(f"'{e}'" for e in entity_ids)
    return q(
        f"""
        SELECT d.date, l.entity_id, e.entity_name,
               l.lcr_ratio_pct, l.lcr_surplus_usd_bn, l.headroom_bps
        FROM fact_lcr_daily l
        JOIN dim_date d     ON d.date_id = l.date_id
        JOIN dim_entity e   ON e.entity_id = l.entity_id
        WHERE l.entity_id IN ({ids})
          AND l.scenario = '{scenario}'
        ORDER BY d.date, l.entity_id
    """
    )


def get_lcr_latest_bar(scenario: str) -> pd.DataFrame:
    return q(
        f"""
        WITH latest AS (
            SELECT MAX(date_id) AS max_date FROM fact_lcr_daily
        )
        SELECT e.entity_name, l.entity_id, l.lcr_ratio_pct,
               l.hqla_total_usd_bn, l.net_cash_outflows_usd_bn,
               l.lcr_surplus_usd_bn, l.headroom_bps
        FROM fact_lcr_daily l
        JOIN dim_entity e ON e.entity_id = l.entity_id
        JOIN latest      ON l.date_id = latest.max_date
        WHERE l.scenario = '{scenario}'
          AND l.entity_id != 'EGROUP'
        ORDER BY l.lcr_ratio_pct DESC
    """
    )


def get_ftp_waterfall(entity_id: str, period: str) -> pd.DataFrame:
    return q(
        f"""
        SELECT p.product_name, p.asset_class,
               AVG(f.base_ftp_bps)           AS base_ftp_bps,
               AVG(f.liquidity_premium_bps)  AS lp_bps,
               AVG(f.cost_of_funds_bps)      AS cof_bps,
               AVG(f.cost_of_liquidity_bps)  AS col_bps,
               AVG(f.total_ftp_bps)          AS total_ftp_bps,
               SUM(f.ftp_pnl_usd_k)          AS total_pnl_usd_k
        FROM fact_ftp_daily f
        JOIN dim_product p ON p.product_id = f.product_id
        JOIN dim_date d    ON d.date_id = f.date_id
        WHERE f.entity_id = '{entity_id}'
          AND d.reporting_period = '{period}'
        GROUP BY p.product_name, p.asset_class
        ORDER BY total_pnl_usd_k DESC
    """
    )


def get_ftp_attribution_waterfall(entity_id: str, period: str) -> pd.DataFrame:
    return q(
        f"""
        SELECT
            SUM(f.notional_balance_usd_mm * f.base_ftp_bps / 10000)          AS base_ftp_mm,
            SUM(f.notional_balance_usd_mm * f.liquidity_premium_bps / 10000) AS lp_mm,
            SUM(f.notional_balance_usd_mm * f.cost_of_funds_bps / 10000)     AS cof_mm,
            SUM(f.notional_balance_usd_mm * f.cost_of_liquidity_bps / 10000) AS col_mm,
            SUM(f.ftp_pnl_usd_k) / 1000                                      AS total_pnl_mm
        FROM fact_ftp_daily f
        JOIN dim_date d ON d.date_id = f.date_id
        WHERE f.entity_id = '{entity_id}'
          AND d.reporting_period = '{period}'
    """
    )


def get_liquidity_gap(entity_id: str, period: str) -> pd.DataFrame:
    return q(
        f"""
        SELECT g.bucket_name, mb.sort_order,
               AVG(g.inflows_usd_mm)  AS inflows,
               AVG(g.outflows_usd_mm) AS outflows,
               AVG(g.gap_usd_mm)      AS gap,
               AVG(g.cumulative_gap_usd_mm) AS cum_gap
        FROM fact_liquidity_gap_monthly g
        JOIN dim_maturity_bucket mb ON mb.bucket_id = g.bucket_id
        JOIN dim_date d             ON d.date_id = g.date_id
        WHERE g.entity_id = '{entity_id}'
          AND d.reporting_period = '{period}'
          AND g.scenario = 'Base'
        GROUP BY g.bucket_name, mb.sort_order
        ORDER BY mb.sort_order
    """
    )


def get_reporting_periods() -> list:
    df = q("SELECT DISTINCT reporting_period FROM dim_date ORDER BY reporting_period")
    return df["reporting_period"].tolist()
