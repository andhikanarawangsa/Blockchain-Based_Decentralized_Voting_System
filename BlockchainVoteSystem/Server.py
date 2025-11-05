from flask import Flask, request, jsonify
from blockchain import Blockchain
import hashlib
import os
from datetime import datetime
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

app = Flask(__name__)

# store multiple blockchains per region
blockchains = {}  # { region_name: Blockchain() }

# store public keys in-memory: { voter_hash: public_key_object }
public_keys = {}

CHAIN_DIR = "chain"
os.makedirs(CHAIN_DIR, exist_ok=True)

def get_blockchain(region):
    if region not in blockchains:
        blockchains[region] = Blockchain()
    return blockchains[region]

@app.route("/register", methods=["POST"])
def register():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    data = request.get_json(silent=True) or {}
    voter_id = data.get("voter_id")
    public_key_pem = data.get("public_key")

    if not voter_id or not public_key_pem:
        return jsonify({"error": "Missing voter_id or public_key"}), 400

    voter_hash = hashlib.sha256(str(voter_id).encode()).hexdigest()
    try:
        public_key_obj = serialization.load_pem_public_key(public_key_pem.encode())
    except Exception as e:
        return jsonify({"error": "Invalid public key PEM", "detail": str(e)}), 400

    public_keys[voter_hash] = public_key_obj
    return jsonify({"message": "Registered", "voter_hash": voter_hash}), 201

@app.route("/vote", methods=["POST"])
def vote_endpoint():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    data = request.get_json(silent=True) or {}
    voter_hash = data.get("voter_hash")
    candidate = data.get("candidate")
    signature_hex = data.get("signature")
    region = data.get("region", "default")  # default region jika tidak ada

    if not voter_hash or not candidate or not signature_hex:
        return jsonify({"error": "Missing voter_hash/candidate/signature"}), 400

    if voter_hash not in public_keys:
        return jsonify({"error": "Voter not registered"}), 403

    public_key = public_keys[voter_hash]
    try:
        signature = bytes.fromhex(signature_hex)
    except Exception as e:
        return jsonify({"error": "Invalid signature hex", "detail": str(e)}), 400

    message = f"{voter_hash}:{candidate}".encode()
    try:
        public_key.verify(
            signature,
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
    except Exception as e:
        return jsonify({"error": "Invalid signature verification", "detail": str(e)}), 403

    blockchain = get_blockchain(region)

    # double-vote prevention per region
    for b in blockchain.chain:
        if isinstance(b.data, dict) and b.data.get("voter") == voter_hash:
            return jsonify({"error": f"Voter has already voted in region {region}"}), 403

    new_block = blockchain.add_vote(voter_hash, candidate)
    return jsonify({"message": "Vote recorded securely", "block": new_block.to_dict(), "region": region}), 201

@app.route("/chain", methods=["GET"])
def chain():
    region = request.args.get("region", "default")
    blockchain = get_blockchain(region)
    return jsonify({"region": region, "chain": blockchain.to_dict()}), 200

@app.route("/validate", methods=["GET"])
def validate():
    region = request.args.get("region", "default")
    blockchain = get_blockchain(region)
    try:
        valid = blockchain.is_valid()
        return jsonify({"region": region, "valid": valid}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/export", methods=["GET"])
def export_chain():
    region = request.args.get("region", "default")
    blockchain = get_blockchain(region)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(CHAIN_DIR, f"chain_{region}_{ts}.json")
    try:
        blockchain.save_to_file(filename)
        return jsonify({"message": "Exported", "file": os.path.basename(filename), "region": region}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/import", methods=["POST"])
def import_chain():
    data = request.get_json(silent=True) or {}
    fname = data.get("filename", None)
    region = data.get("region", "default")
    if not fname:
        return jsonify({"error": "Provide filename (relative to chain/ folder)"}), 400

    filename = os.path.join(CHAIN_DIR, os.path.basename(fname))
    if not os.path.exists(filename):
        return jsonify({"error": f"File not found: {filename}"}), 400
    try:
        blockchain = get_blockchain(region)
        blockchain.load_from_file(filename)
        return jsonify({"message": "Imported", "file": os.path.basename(filename), "region": region}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset", methods=["POST"])
def reset_chain():
    region = request.args.get("region", "default")
    blockchains[region] = Blockchain()
    return jsonify({"message": f"Blockchain for region {region} reset successfully"}), 200

@app.route("/results", methods=["GET"])
def results():
    region = request.args.get("region", "default")
    blockchain = get_blockchain(region)
    counts = {}
    for b in blockchain.chain[1:]:
        if isinstance(b.data, dict):
            cand = b.data.get("candidate")
            if cand:
                counts[cand] = counts.get(cand, 0) + 1
    return jsonify({"region": region, "results": counts}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
