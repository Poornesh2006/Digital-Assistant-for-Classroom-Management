import os

from classroom_app import create_app

app = create_app()


if __name__ == "__main__":
    print(f"Starting Flask app from: {os.path.abspath(__file__)}")
    print("Available routes:")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        print(f"  {rule.rule} -> {rule.endpoint}")

    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
