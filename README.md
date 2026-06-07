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

## GitHub Pages

This repository now includes a static landing page at `index.html` that links to the two dashboard pages:

- `Treasury_ALCO_Dashboard.html`
- `Treasury_Command_Center.html`

To publish it with GitHub Pages:

1. Push the repository to GitHub.
2. In the repository, open `Settings` > `Pages`.
3. Set the source to deploy from the branch root, or keep the default branch root if your repo uses direct Pages publishing.
4. Wait for GitHub Pages to build, then open the Pages URL GitHub provides.

The `.nojekyll` file at the repository root prevents GitHub Pages from applying Jekyll processing to the static files.
