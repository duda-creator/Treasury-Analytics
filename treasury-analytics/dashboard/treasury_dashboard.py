"""Compatibility entrypoint.

Use app.py as the primary module.
"""

from app import app


if __name__ == "__main__":
    print("\nTreasury Analytics Dashboard")
    print("Open http://localhost:8050 in your browser\n")
    app.run(debug=True, port=8050)
