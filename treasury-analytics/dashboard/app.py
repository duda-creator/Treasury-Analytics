import dash

from callbacks import register_callbacks
from layout import build_layout


app = dash.Dash(
    __name__,
    title="Treasury Analytics",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True,
)

app.layout = build_layout()
register_callbacks(app)


if __name__ == "__main__":
    print("\nTreasury Analytics Dashboard")
    print("Open http://localhost:8050 in your browser\n")
    app.run(debug=True, port=8050)
