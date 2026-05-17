# Treasury Analytics — Prototype

End-to-end treasury analytics data product: synthetic data warehouse,
SSAS semantic layer, Dash web dashboard, and Jupyter notebooks.

## Quick start
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
python warehouse/treasury_mock_data.py
python warehouse/build_warehouse.py
python dashboard/app.py
# → http://localhost:8050
