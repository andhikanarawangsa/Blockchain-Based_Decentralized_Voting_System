# server.py
from flask import Flask, request, jsonify
from blockchain import Blockchain, Block
import hashlib, os
from datetime import datetime
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

app = Flask(__name__)
blockchain = Blockchain()
pending_votes = []
VOTES_PER_BLOCK = 2  # jumlah vote per blok
DIFFICULTY = 4        # jumlah leading zeros untuk PoW

# store public keys: voter_hash -> public key object
public_keys = {}

CHAIN_DIR = "chain"
os.makedirs(CHAIN_DIR, exist_ok=True)

# -------------------- Routes --------------------

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
    global pending_votes
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    data = request.get_json(silent=True) or {}
    voter_hash = data.get("voter_hash")
    candidate = data.get("candidate")
    signature_hex = data.get("signature")

    if not voter_hash or not candidate or not signature_hex:
        return jsonify({"error": "Missing voter_hash/candidate/signature"}), 400
    if voter_hash not in public_keys:
        return jsonify({"error": "Voter not registered"}), 403

    # verifikasi signature
    try:
        signature = bytes.fromhex(signature_hex)
        message = f"{voter_hash}:{candidate}".encode()
        public_keys[voter_hash].verify(
            signature,
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
    except Exception as e:
        return jsonify({"error": "Invalid signature", "detail": str(e)}), 403

    # double vote check
    for b in blockchain.chain:
        if isinstance(b.data, list):
            for v in b.data:
                if v.get("voter") == voter_hash:
                    return jsonify({"error": "Voter has already voted"}), 403
    for v in pending_votes:
        if v["voter"] == voter_hash:
            return jsonify({"error": "Voter has already voted (pending)"}), 403

    # simpan ke pending pool
    pending_votes.append({"voter": voter_hash, "candidate": candidate})

    # cek apakah cukup buat blok baru
    if len(pending_votes) >= VOTES_PER_BLOCK:
        votes_to_add = pending_votes[:VOTES_PER_BLOCK]
        pending_votes[:VOTES_PER_BLOCK] = []

        previous_block = blockchain.get_last_block()
        new_block = Block(
            index=len(blockchain.chain),
            timestamp=datetime.now().timestamp(),
            data=votes_to_add,
            previous_hash=previous_block.hash
        )
        # mine block dulu (PoW)
        new_block.mine_block(DIFFICULTY)
        blockchain.chain.append(new_block)

        return jsonify({
            "message": "Vote recorded in new block (mined with PoW)",
            "block": new_block.to_dict()
        }), 201
    else:
        return jsonify({
            "message": f"Vote recorded in pending pool ({len(pending_votes)}/{VOTES_PER_BLOCK})",
            "pending_votes": pending_votes
        }), 201

@app.route("/force_commit", methods=["POST"])
def force_commit():
    global pending_votes
    if not pending_votes:
        return jsonify({"error": "No pending votes to commit"}), 400

    previous_block = blockchain.get_last_block()
    new_block = Block(
        index=len(blockchain.chain),
        timestamp=datetime.now().timestamp(),
        data=pending_votes.copy(),
        previous_hash=previous_block.hash
    )
    # mine block dulu (PoW)
    new_block.mine_block(DIFFICULTY)
    blockchain.chain.append(new_block)
    pending_votes = []

    return jsonify({
        "message": f"Pending votes forced into new block ({len(new_block.data)} votes, mined with PoW)",
        "block": new_block.to_dict()
    }), 201

@app.route("/chain", methods=["GET"])
def chain():
    return jsonify({
        "chain": blockchain.to_dict(),
        "pending_votes": pending_votes
    }), 200

@app.route("/results", methods=["GET"])
def results():
    counts = {}
    for b in blockchain.chain[1:]:
        if isinstance(b.data, list):
            for vote in b.data:
                cand = vote.get("candidate")
                if cand:
                    counts[cand] = counts.get(cand, 0) + 1
    return jsonify({"results": counts, "pending_votes": pending_votes}), 200

@app.route("/validate", methods=["GET"])
def validate():
    try:
        valid = blockchain.is_valid(DIFFICULTY)
        return jsonify({"valid": valid}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset", methods=["POST"])
def reset_blockchain():
    global blockchain, pending_votes
    blockchain = Blockchain()
    pending_votes = []
    return jsonify({"status": "success", "message": "Blockchain and results reset."})

@app.route("/import", methods=["POST"])
def import_chain():
    global blockchain, pending_votes

    data = request.get_json()
    blockchain.from_dict(data["chain"])   # <-- ini bagian penting
    
    pending_votes.clear()                 # reset pending
    return jsonify({"status": "success", "message": "Blockchain imported"})

    # Rebuild chain from JSON
    for blk in new_chain_json:
        new_block = Block(
            index=blk["index"],
            data=blk["data"],
            previous_hash=blk["previous_hash"],
            nonce=blk.get("nonce", 0)
        )
        new_chain.append(new_block)

    # Replace blockchain chain
    blockchain.chain = new_chain

    # Recompute hash to ensure integrity
    for i in range(len(blockchain.chain)):
        blockchain.chain[i].hash = blockchain.chain[i].compute_hash()
        if i > 0:
            blockchain.chain[i].previous_hash = blockchain.chain[i-1].hash

    # Rebuild voted_list to prevent double-vote
    blockchain.voted_list.clear()
    for blk in blockchain.chain:
        if isinstance(blk.data, list):
            for vote in blk.data:
                blockchain.voted_list.add(vote.get("voter"))

    # Clear pending votes (just like your original code)
    pending_votes.clear()

    return jsonify({"status": "success", "message": "Blockchain imported successfully", "blocks": len(blockchain.chain)})


# -------------------- Run Server --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
