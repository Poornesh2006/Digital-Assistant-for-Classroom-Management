import os

from classroom_app import create_app

users = {
    "Poornesh": "Poornesh2006",
    "Mythish": "Mythish123",
    "Shiyam": "Shiyam2006",
    "Rithish": "Rithish2006",
    "Jaiakash": "Jaiakash2006",
    "Nithish": "Nithish2006",
    "Sakthi": "Sakthi2005",
    "Unknown": "Unknown123",
}

app = create_app()
app.config["LOGIN_USERS"] = users


if __name__ == "__main__":
    print(f"Starting Flask app from: {os.path.abspath(__file__)}")
    print("Available routes:")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        print(f"  {rule.rule} -> {rule.endpoint}")

    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
