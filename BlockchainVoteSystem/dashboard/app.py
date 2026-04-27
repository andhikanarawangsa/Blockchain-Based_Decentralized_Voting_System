from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

NODES = [
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5001"
]


def fetch_node_data(node):
    try:
        chain = requests.get(f"{node}/chain", timeout=2).json()
        results = requests.get(f"{node}/results", timeout=2).json()
        validate = requests.get(f"{node}/validate", timeout=2).json()

        return {
            "node": node,
            "chain_length": len(chain["chain"]),
            "pending": len(chain["pending_votes"]),
            "results": results.get("results", {}),
            "valid": validate.get("valid", False)
        }
    except:
        return {
            "node": node,
            "error": "offline"
        }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/status")
def status():
    return jsonify([fetch_node_data(n) for n in NODES])


if __name__ == "__main__":
    app.run(port=7000, debug=True)