# Treasury Analytics — Prototype

End-to-end treasury analytics data product: synthetic data warehouse,
SSAS semantic layer, Dash web dashboard, and Jupyter notebooks.

## Quick Start

Start from the extracted repository root. That folder should contain
`requirements.txt` and the `treasury-analytics/` directory.

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate the synthetic source data

```bash
python treasury-analytics/warehouse/treasury_mock_data.py
```

This creates CSV files under `treasury-analytics/data/generated/`.

### 4. Build the DuckDB warehouse

```bash
python treasury-analytics/warehouse/build_warehouse.py
```

This creates the local DuckDB database under `treasury-analytics/warehouse/`.

### 5. Start the dashboard

```bash
python treasury-analytics/dashboard/app.py
```

Open the app at:

```text
http://localhost:8050
```

### Notes

- No local `.env` file is required for the default setup.
- If `python` does not point to Python 3 on your machine, use `python3` instead.
- Run data generation before the warehouse build, because the database loader expects the generated CSV files to exist first.
