"""
Treasury Analytics — Mock Data Generator
=========================================
Generates realistic (but entirely synthetic) treasury data for:
  - LCR (Liquidity Coverage Ratio) by legal entity
  - FTP (Funds Transfer Pricing) adjustments by product / business unit
  - Balance sheet positions by entity / currency / product

Design principles:
  1. Domain-credible ranges — ratios cluster where they would in real life
  2. Internal consistency — entity-level figures roll up to group correctly
  3. Time-series coherence — metrics drift realistically, not randomly
  4. Regulatory realism — stress scenarios degrade LCR below base
  5. Reproducible — fixed random seed for stable demo data
"""

import random
import math
import csv
import json
import os
from datetime import date, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Dict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration & seed
# ---------------------------------------------------------------------------

random.seed(42)

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "data" / "generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Reference data — dimensions
# ---------------------------------------------------------------------------

ENTITIES = [
    {"entity_id": "E001", "entity_name": "SCB Singapore Branch",    "region": "APAC",  "currency": "SGD", "weight": 0.30},
    {"entity_id": "E002", "entity_name": "SCB Hong Kong Branch",    "region": "APAC",  "currency": "HKD", "weight": 0.20},
    {"entity_id": "E003", "entity_name": "SCB London Branch",       "region": "EMEA",  "currency": "GBP", "weight": 0.18},
    {"entity_id": "E004", "entity_name": "SCB Frankfurt Branch",    "region": "EMEA",  "currency": "EUR", "weight": 0.12},
    {"entity_id": "E005", "entity_name": "SCB New York Branch",     "region": "AMER",  "currency": "USD", "weight": 0.20},
]

# Regulatory LCR minimum = 100%. Entities should sit 110-145% in base,
# degrade to 90-115% under stress — some may breach in stress (realistic).
ENTITY_LCR_PROFILE = {
    "E001": {"base_mean": 128, "base_std": 6,  "stress_haircut": 22},
    "E002": {"base_mean": 135, "base_std": 8,  "stress_haircut": 28},
    "E003": {"base_mean": 118, "base_std": 5,  "stress_haircut": 20},
    "E004": {"base_mean": 142, "base_std": 9,  "stress_haircut": 35},
    "E005": {"base_mean": 122, "base_std": 7,  "stress_haircut": 25},
}

PRODUCTS = [
    {"product_id": "P001", "product_name": "Corporate Loans",      "asset_class": "Lending",    "ftp_base_bps": 85},
    {"product_id": "P002", "product_name": "Trade Finance",        "asset_class": "Lending",    "ftp_base_bps": 72},
    {"product_id": "P003", "product_name": "FICC — Rates",         "asset_class": "Markets",    "ftp_base_bps": 18},
    {"product_id": "P004", "product_name": "FICC — Credit",        "asset_class": "Markets",    "ftp_base_bps": 25},
    {"product_id": "P005", "product_name": "Transaction Banking",  "asset_class": "Deposits",   "ftp_base_bps": -45},
    {"product_id": "P006", "product_name": "Retail Deposits",      "asset_class": "Deposits",   "ftp_base_bps": -38},
    {"product_id": "P007", "product_name": "Interbank Lending",    "asset_class": "Treasury",   "ftp_base_bps": 12},
    {"product_id": "P008", "product_name": "Securities Portfolio", "asset_class": "Treasury",   "ftp_base_bps": 30},
]

BUSINESS_UNITS = [
    {"bu_id": "BU01", "bu_name": "Corporate & Institutional Banking", "region": "APAC"},
    {"bu_id": "BU02", "bu_name": "Financial Markets",                  "region": "APAC"},
    {"bu_id": "BU03", "bu_name": "Transaction Banking",                "region": "EMEA"},
    {"bu_id": "BU04", "bu_name": "Treasury",                          "region": "GROUP"},
]

CURRENCIES = ["USD", "SGD", "HKD", "GBP", "EUR", "JPY", "AUD", "CNH"]

# Maturity buckets for liquidity gap / NSFR
MATURITY_BUCKETS = [
    "Overnight", "2-7 days", "8-30 days", "1-3 months",
    "3-6 months", "6-12 months", "1-2 years", "2-5 years", ">5 years"
]

HQLA_CATEGORIES = ["Level 1", "Level 2A", "Level 2B"]

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))

def noise(scale: float = 1.0) -> float:
    """Gaussian noise centred on zero."""
    return random.gauss(0, scale)

def brownian_walk(start: float, steps: int, drift: float, vol: float,
                  lo: float = None, hi: float = None) -> List[float]:
    """
    Simulates a mean-reverting random walk (Ornstein-Uhlenbeck-like).
    Keeps values within realistic bounds without hard clipping artefacts.
    """
    values = [start]
    mean_reversion = 0.08
    for _ in range(steps - 1):
        prev = values[-1]
        # Pull toward long-run mean (start) plus small drift
        rev = mean_reversion * (start + drift * len(values) - prev)
        shock = random.gauss(0, vol)
        new_val = prev + rev + shock
        if lo is not None and hi is not None:
            new_val = clamp(new_val, lo, hi)
        values.append(new_val)
    return values

def date_range(start: date, end: date) -> List[date]:
    dates = []
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=1)
    # Keep only weekdays (Mon-Fri) — treasury reports daily on business days
    return [d for d in dates if d.weekday() < 5]

# ---------------------------------------------------------------------------
# 1. Dimension tables (write once, reference everywhere)
# ---------------------------------------------------------------------------

def write_dim_entity():
    rows = []
    for e in ENTITIES:
        rows.append({
            **e,
            "is_group": False,
            "regulatory_lcr_minimum": 100.0,
            "regulatory_nsfr_minimum": 100.0,
        })
    # Add a synthetic Group consolidation row
    rows.append({
        "entity_id": "EGROUP",
        "entity_name": "SCB Group (Consolidated)",
        "region": "GROUP",
        "currency": "USD",
        "weight": 1.0,
        "is_group": True,
        "regulatory_lcr_minimum": 100.0,
        "regulatory_nsfr_minimum": 100.0,
    })
    _write_csv("dim_entity.csv", rows)
    print(f"  dim_entity.csv — {len(rows)} rows")

def write_dim_product():
    _write_csv("dim_product.csv", PRODUCTS)
    print(f"  dim_product.csv — {len(PRODUCTS)} rows")

def write_dim_date(dates: List[date]):
    rows = []
    for d in dates:
        is_month_end = (d + timedelta(days=1)).month != d.month
        is_quarter_end = is_month_end and d.month in (3, 6, 9, 12)
        rows.append({
            "date_id": d.strftime("%Y%m%d"),
            "date": d.isoformat(),
            "year": d.year,
            "month": d.month,
            "quarter": (d.month - 1) // 3 + 1,
            "week": d.isocalendar()[1],
            "day_of_week": d.strftime("%A"),
            "is_month_end": is_month_end,
            "is_quarter_end": is_quarter_end,
            "reporting_period": d.strftime("%Y-%m"),
        })
    _write_csv("dim_date.csv", rows)
    print(f"  dim_date.csv — {len(rows)} rows")

def write_dim_maturity():
    rows = [{"bucket_id": f"MB{i+1:02d}", "bucket_name": b, "sort_order": i+1}
            for i, b in enumerate(MATURITY_BUCKETS)]
    _write_csv("dim_maturity_bucket.csv", rows)

def write_dim_currency():
    rows = [{"currency_code": c} for c in CURRENCIES]
    _write_csv("dim_currency.csv", rows)

# ---------------------------------------------------------------------------
# 2. Fact: LCR daily by entity
# ---------------------------------------------------------------------------

def generate_lcr_fact(dates: List[date]) -> List[dict]:
    """
    LCR = HQLA / Net Cash Outflows (30-day stress).
    Regulatory minimum = 100%. Real banks run 110-145% base.
    Stressed LCR degrades by entity-specific haircut.
    HQLA and NCO are back-calculated from ratio to keep internal consistency.
    """
    rows = []
    # Generate a time series per entity
    entity_series = {}
    for e in ENTITIES:
        profile = ENTITY_LCR_PROFILE[e["entity_id"]]
        # Slow-moving base LCR series (weekly vol ~2 bps is realistic)
        series = brownian_walk(
            start=profile["base_mean"],
            steps=len(dates),
            drift=-0.005,  # slight downward drift over the year (tighter markets)
            vol=1.8,
            lo=95.0,
            hi=180.0,
        )
        entity_series[e["entity_id"]] = series

    for i, d in enumerate(dates):
        group_hqla = 0
        group_nco = 0

        for e in ENTITIES:
            profile = ENTITY_LCR_PROFILE[e["entity_id"]]
            base_lcr = entity_series[e["entity_id"]][i]

            # Stressed LCR: apply haircut plus a small idiosyncratic shock
            stress_haircut = profile["stress_haircut"] + noise(3)
            stressed_lcr = clamp(base_lcr - stress_haircut, 75.0, 165.0)

            # Back-calculate HQLA and NCO from base LCR
            # Scale by entity weight (in USD billions, notional)
            entity_scale = e["weight"] * 80 + noise(2)  # ~80 USD bn total HQLA
            hqla_total = entity_scale * (1 + noise(0.02))
            nco = hqla_total / (base_lcr / 100)

            # Split HQLA into Level 1 / 2A / 2B (Level 1 dominates)
            l1 = hqla_total * random.uniform(0.72, 0.82)
            l2a = hqla_total * random.uniform(0.12, 0.20)
            l2b = hqla_total - l1 - l2a

            group_hqla += hqla_total
            group_nco += nco

            rows.append({
                "date_id": d.strftime("%Y%m%d"),
                "entity_id": e["entity_id"],
                "scenario": "Base",
                "lcr_ratio_pct": round(base_lcr, 2),
                "hqla_total_usd_bn": round(hqla_total, 3),
                "hqla_level1_usd_bn": round(l1, 3),
                "hqla_level2a_usd_bn": round(l2a, 3),
                "hqla_level2b_usd_bn": round(l2b, 3),
                "net_cash_outflows_usd_bn": round(nco, 3),
                "lcr_surplus_usd_bn": round(hqla_total - nco, 3),
                "regulatory_minimum_pct": 100.0,
                "headroom_bps": round((base_lcr - 100) * 100, 0),
            })

            rows.append({
                "date_id": d.strftime("%Y%m%d"),
                "entity_id": e["entity_id"],
                "scenario": "Stressed",
                "lcr_ratio_pct": round(stressed_lcr, 2),
                "hqla_total_usd_bn": round(hqla_total * 0.92, 3),   # haircut on HQLA
                "hqla_level1_usd_bn": round(l1 * 0.95, 3),
                "hqla_level2a_usd_bn": round(l2a * 0.85, 3),
                "hqla_level2b_usd_bn": round(l2b * 0.50, 3),        # L2B hit hardest
                "net_cash_outflows_usd_bn": round(nco * 1.15, 3),   # outflows increase
                "lcr_surplus_usd_bn": round(hqla_total * 0.92 - nco * 1.15, 3),
                "regulatory_minimum_pct": 100.0,
                "headroom_bps": round((stressed_lcr - 100) * 100, 0),
            })

        # Group consolidated row
        group_base = group_hqla / group_nco * 100
        rows.append({
            "date_id": d.strftime("%Y%m%d"),
            "entity_id": "EGROUP",
            "scenario": "Base",
            "lcr_ratio_pct": round(group_base, 2),
            "hqla_total_usd_bn": round(group_hqla, 3),
            "hqla_level1_usd_bn": round(group_hqla * 0.77, 3),
            "hqla_level2a_usd_bn": round(group_hqla * 0.16, 3),
            "hqla_level2b_usd_bn": round(group_hqla * 0.07, 3),
            "net_cash_outflows_usd_bn": round(group_nco, 3),
            "lcr_surplus_usd_bn": round(group_hqla - group_nco, 3),
            "regulatory_minimum_pct": 100.0,
            "headroom_bps": round((group_base - 100) * 100, 0),
        })

    print(f"  fact_lcr_daily.csv — {len(rows)} rows")
    return rows

# ---------------------------------------------------------------------------
# 3. Fact: FTP adjustments daily by product / entity / business unit
# ---------------------------------------------------------------------------

def generate_ftp_fact(dates: List[date]) -> List[dict]:
    """
    FTP = funding cost/benefit attributed to each product.
    Components: Base FTP (risk-free curve), Liquidity Premium (LP),
    Cost of Funds (CoF), Cost of Liquidity (CoL).
    Sign convention: positive = cost to business (asset), negative = benefit (liability/deposit).
    """
    rows = []

    # Monthly volume index — slight growth trend
    def volume_index(d: date) -> float:
        months_elapsed = (d.year - dates[0].year) * 12 + (d.month - dates[0].month)
        return 1.0 + months_elapsed * 0.003 + noise(0.005)

    for d in dates:
        vol_idx = volume_index(d)
        for e in ENTITIES:
            for p in PRODUCTS:
                # Notional balance — varies by entity size and product
                base_balance = (
                    e["weight"] * 12_000          # USD millions
                    * (1 + noise(0.04))
                    * vol_idx
                )

                # FTP rate components (basis points, slowly time-varying)
                base_ftp = p["ftp_base_bps"] + noise(1.5)
                lp = abs(base_ftp) * 0.18 + noise(0.8)   # LP is ~18% of base
                cof = abs(base_ftp) * 0.12 + noise(0.5)  # CoF is ~12% of base
                col = abs(base_ftp) * 0.08 + noise(0.4)  # CoL is ~8% of base

                total_ftp_bps = base_ftp + lp + cof + col
                # FTP P&L = balance * rate / 365 / 10000
                ftp_pnl = base_balance * total_ftp_bps / 365 / 10_000

                # Assign a business unit (products map naturally)
                if p["asset_class"] == "Markets":
                    bu_id = "BU02"
                elif p["asset_class"] == "Deposits":
                    bu_id = "BU03"
                elif p["product_id"] in ("P007", "P008"):
                    bu_id = "BU04"
                else:
                    bu_id = "BU01"

                rows.append({
                    "date_id": d.strftime("%Y%m%d"),
                    "entity_id": e["entity_id"],
                    "product_id": p["product_id"],
                    "bu_id": bu_id,
                    "currency": e["currency"],
                    "notional_balance_usd_mm": round(base_balance, 2),
                    "base_ftp_bps": round(base_ftp, 2),
                    "liquidity_premium_bps": round(lp, 2),
                    "cost_of_funds_bps": round(cof, 2),
                    "cost_of_liquidity_bps": round(col, 2),
                    "total_ftp_bps": round(total_ftp_bps, 2),
                    "ftp_pnl_usd_k": round(ftp_pnl * 1000, 2),
                })

    print(f"  fact_ftp_daily.csv — {len(rows)} rows")
    return rows

# ---------------------------------------------------------------------------
# 4. Fact: Balance sheet positions monthly
# ---------------------------------------------------------------------------

def generate_balance_sheet_fact(dates: List[date]) -> List[dict]:
    """
    Monthly snapshot of asset / liability positions.
    Assets and liabilities balance at entity level.
    Funded vs Non-Funded split mirrors real treasury distinctions.
    """
    rows = []
    month_end_dates = [d for d in dates if (d + timedelta(days=1)).month != d.month]

    asset_products = [p for p in PRODUCTS if p["asset_class"] in ("Lending", "Markets", "Treasury")]
    liab_products = [p for p in PRODUCTS if p["asset_class"] == "Deposits"]

    for d in month_end_dates:
        for e in ENTITIES:
            entity_total_assets = e["weight"] * 220_000 * (1 + noise(0.02))  # USD mm
            remaining_assets = entity_total_assets

            for p in asset_products:
                allocation = entity_total_assets * random.uniform(0.12, 0.28)
                allocation = min(allocation, remaining_assets)
                remaining_assets -= allocation
                is_funded = p["asset_class"] == "Lending"

                for ccy in [e["currency"], "USD"]:
                    ccy_split = 0.65 if ccy == e["currency"] else 0.35
                    rows.append({
                        "date_id": d.strftime("%Y%m%d"),
                        "entity_id": e["entity_id"],
                        "product_id": p["product_id"],
                        "currency": ccy,
                        "position_type": "Asset",
                        "is_funded": is_funded,
                        "is_group": False,
                        "balance_usd_mm": round(allocation * ccy_split, 2),
                    })

            # Liabilities mirror assets (balance sheet must balance)
            total_liab = entity_total_assets
            for p in liab_products:
                liab_amount = total_liab * random.uniform(0.35, 0.55)
                for ccy in [e["currency"], "USD"]:
                    ccy_split = 0.60 if ccy == e["currency"] else 0.40
                    rows.append({
                        "date_id": d.strftime("%Y%m%d"),
                        "entity_id": e["entity_id"],
                        "product_id": p["product_id"],
                        "currency": ccy,
                        "position_type": "Liability",
                        "is_funded": True,
                        "is_group": False,
                        "balance_usd_mm": round(liab_amount * ccy_split, 2),
                    })

    print(f"  fact_balance_sheet_monthly.csv — {len(rows)} rows")
    return rows

# ---------------------------------------------------------------------------
# 5. Fact: Liquidity gap (maturity ladder) — monthly snapshot
# ---------------------------------------------------------------------------

def generate_liquidity_gap_fact(dates: List[date]) -> List[dict]:
    """
    Maturity mismatch: cash inflows vs outflows per bucket.
    The gap (inflows - outflows) should be negative in short buckets (funding risk)
    and positive in longer buckets — the classic liquidity gap profile of a bank.
    """
    rows = []
    month_end_dates = [d for d in dates if (d + timedelta(days=1)).month != d.month]

    # Realistic bucket profiles: short-term outflows > inflows (funding gap),
    # long-term inflows > outflows (loan maturities)
    BUCKET_PROFILES = {
        "Overnight":   {"inflow_factor": 0.60, "outflow_factor": 1.00},
        "2-7 days":    {"inflow_factor": 0.70, "outflow_factor": 0.95},
        "8-30 days":   {"inflow_factor": 0.80, "outflow_factor": 0.88},
        "1-3 months":  {"inflow_factor": 0.90, "outflow_factor": 0.85},
        "3-6 months":  {"inflow_factor": 1.00, "outflow_factor": 0.75},
        "6-12 months": {"inflow_factor": 1.10, "outflow_factor": 0.65},
        "1-2 years":   {"inflow_factor": 1.20, "outflow_factor": 0.50},
        "2-5 years":   {"inflow_factor": 1.35, "outflow_factor": 0.40},
        ">5 years":    {"inflow_factor": 1.50, "outflow_factor": 0.30},
    }

    for d in month_end_dates:
        for e in ENTITIES:
            base_flow = e["weight"] * 8_000  # USD mm per bucket

            cumulative_gap = 0
            for i, (bucket, profile) in enumerate(BUCKET_PROFILES.items()):
                inflows = base_flow * profile["inflow_factor"] * (1 + noise(0.05))
                outflows = base_flow * profile["outflow_factor"] * (1 + noise(0.05))
                gap = inflows - outflows
                cumulative_gap += gap

                rows.append({
                    "date_id": d.strftime("%Y%m%d"),
                    "entity_id": e["entity_id"],
                    "bucket_id": f"MB{i+1:02d}",
                    "bucket_name": bucket,
                    "inflows_usd_mm": round(inflows, 2),
                    "outflows_usd_mm": round(outflows, 2),
                    "gap_usd_mm": round(gap, 2),
                    "cumulative_gap_usd_mm": round(cumulative_gap, 2),
                    "scenario": "Base",
                })

    print(f"  fact_liquidity_gap_monthly.csv — {len(rows)} rows")
    return rows

# ---------------------------------------------------------------------------
# Utility: CSV writer
# ---------------------------------------------------------------------------

def _write_csv(filename: str, rows: List[dict]):
    if not rows:
        return
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\nTreasury Mock Data Generator")
    print("=" * 40)

    # Generate 12 months of daily business-day data
    start = date(2024, 1, 2)
    end = date(2024, 12, 31)
    dates = date_range(start, end)
    print(f"Date range: {start} → {end}  ({len(dates)} business days)\n")

    print("Writing dimension tables...")
    write_dim_entity()
    write_dim_product()
    write_dim_date(dates)
    write_dim_maturity()
    write_dim_currency()

    print("\nGenerating fact tables...")
    lcr_rows    = generate_lcr_fact(dates)
    ftp_rows    = generate_ftp_fact(dates)
    bs_rows     = generate_balance_sheet_fact(dates)
    gap_rows    = generate_liquidity_gap_fact(dates)

    print("\nWriting fact tables...")
    _write_csv("fact_lcr_daily.csv", lcr_rows)
    _write_csv("fact_ftp_daily.csv", ftp_rows)
    _write_csv("fact_balance_sheet_monthly.csv", bs_rows)
    _write_csv("fact_liquidity_gap_monthly.csv", gap_rows)

    # Summary
    total_rows = sum(len(r) for r in [lcr_rows, ftp_rows, bs_rows, gap_rows])
    print(f"\nDone. {total_rows:,} total fact rows written to ./{OUTPUT_DIR}/")
    print("\nFiles generated:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f"  {f:<45} {size/1024:>7.1f} KB")

if __name__ == "__main__":
    main()
