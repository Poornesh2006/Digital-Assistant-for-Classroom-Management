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
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
