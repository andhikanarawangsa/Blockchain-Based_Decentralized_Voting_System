# server.py
from flask import Flask, request, jsonify
from blockchain import Blockchain, Block
from datetime import datetime
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import hashlib, os
import requests

app = Flask(__name__)
blockchain = Blockchain()
peers = set()
my_url = None
pending_votes = []
VOTES_PER_BLOCK = 2
DIFFICULTY = 4

CHAIN_DIR = "chain"
os.makedirs(CHAIN_DIR, exist_ok=True)

CHAIN_FILE = None  # placeholder doang

def resolve_conflicts():
    global blockchain

    longest_chain = None
    max_length = len(blockchain.chain)

    for peer in peers:
        try:
            response = requests.get(f"{peer}/chain")
            if response.status_code == 200:
                data = response.json()
                length = len(data["chain"])
                chain = data["chain"]

                temp = Blockchain()
                temp.from_dict(chain)

                if length > max_length and temp.is_valid(DIFFICULTY):
                    max_length = length
                    longest_chain = temp

        except Exception as e:
            print(f"[SYNC ERROR] {peer}: {e}")

    if longest_chain:
        blockchain = longest_chain
        blockchain.save_to_file(CHAIN_FILE)
        print("[SYNC] Chain updated from peer")
        return True

    return False

def load_chain_from_file():
    global blockchain

    if os.path.exists(CHAIN_FILE):
        try:
            temp_blockchain = Blockchain()
            temp_blockchain.load_from_file(CHAIN_FILE)

            print(f"[DEBUG] Loaded {len(temp_blockchain.chain)} blocks")

            if temp_blockchain.is_valid(DIFFICULTY):
                blockchain = temp_blockchain
                print(f"[INFO] Blockchain loaded from {CHAIN_FILE}")
            else:
                print("[WARNING] Invalid chain → reset")
                blockchain = Blockchain()

        except Exception as e:
            print(f"[ERROR] Load failed: {e}")
            blockchain = Blockchain()
    else:
        print("[INFO] No existing chain → starting fresh")
        
def broadcast_block(block):
    for peer in peers:
        try:
            requests.post(
                f"{peer}/receive_block",
                json={"block": block.to_dict()},
                timeout=2
            )
        except Exception as e:
            print(f"[BROADCAST ERROR] {peer}: {e}")

# store public keys: voter_hash -> public key object
public_keys = {}

CHAIN_DIR = "chain"
os.makedirs(CHAIN_DIR, exist_ok=True)

# -------------------- Routes --------------------
@app.route("/add_peer", methods=["POST"])
def add_peer():
    data = request.get_json()
    node = data.get("node")

    if not node:
        return jsonify({"error": "No node provided"}), 400

    if node not in peers and node != my_url:
        peers.add(node)

        # 🔥 ambil peers dari node itu
        try:
            response = requests.get(f"{node}/get_peers", timeout=5)
            if response.status_code == 200:
                new_peers = response.json().get("peers", [])
                for p in new_peers:
                    if p != my_url:
                        peers.add(p)
        except Exception as e:
            print(f"[PEER FETCH ERROR] {e}")

        # 🔥 broadcast diri ke semua peers
        for peer in peers:
            if peer == my_url:
                continue
            try:
                requests.post(
                    f"{peer}/add_peer",
                    json={"node": my_url},  # 🔥 FIX
                    timeout=5
                )
            except Exception as e:
                print(f"[BROADCAST ERROR] {peer}: {e}")

    return jsonify({
        "message": "Peer added",
        "peers": list(peers)
    })

@app.route("/get_peers", methods=["GET"])
def get_peers():
    return jsonify({
        "peers": list(peers)
    })

@app.route("/sync", methods=["GET"])
def sync():
    replaced = resolve_conflicts()
    return jsonify({
        "replaced": replaced,
        "length": len(blockchain.chain)
    })
    
@app.route("/receive_block", methods=["POST"])
def receive_block():
    global blockchain

    data = request.get_json()
    block_data = data.get("block")

    if not block_data:
        return jsonify({"error": "No block data"}), 400

    # ambil block terakhir
    last_block = blockchain.get_last_block()

    # validasi basic
    if block_data["previous_hash"] != last_block.hash:
        print("[WARNING] Chain mismatch → syncing...")
        resolve_conflicts()
        return jsonify({"error": "Invalid previous hash, triggered sync"}), 400

    # rebuild block
    new_block = Block(
        index=block_data["index"],
        timestamp=block_data["timestamp"],
        data=block_data["data"],
        previous_hash=block_data["previous_hash"]
    )
    new_block.nonce = block_data["nonce"]
    new_block.hash = block_data["hash"]

    # cek hash valid
    if new_block.hash != new_block.hash_block():
        return jsonify({"error": "Invalid hash"}), 400

    if not new_block.hash.startswith("0" * DIFFICULTY):
        return jsonify({"error": "Invalid PoW"}), 400

    # append
    blockchain.chain.append(new_block)
    blockchain.save_to_file(CHAIN_FILE)

    print("[RECEIVE] Block added from peer")

    return jsonify({"status": "Block accepted"}), 200

##---------------------

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
    resolve_conflicts()
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
        # Auto Save
        blockchain.save_to_file(CHAIN_FILE)
        broadcast_block(new_block)

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
    # Auto Save
    blockchain.save_to_file(CHAIN_FILE)
    broadcast_block(new_block)
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
    blockchain.save_to_file(CHAIN_FILE)
    return jsonify({"status": "success", "message": "Blockchain and results reset."})

@app.route("/import", methods=["POST"])
def import_chain():
    global blockchain, pending_votes

    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json(silent=True) or {}
    new_chain_json = data.get("chain")

    if not new_chain_json:
        return jsonify({"error": "No chain data provided"}), 400

    try:
        # 🔹 build temporary blockchain
        temp_blockchain = Blockchain()
        temp_blockchain.from_dict(new_chain_json)

        # 🔹 VALIDASI CHAIN
        if not temp_blockchain.is_valid(DIFFICULTY):
            return jsonify({
                "status": "failed",
                "error": "Blockchain validation failed",
                "reason": "Hash mismatch / PoW invalid / chain tampered"
            }), 400

        # 🔹 kalau valid → replace
        blockchain = temp_blockchain
        blockchain.save_to_file(CHAIN_FILE)
        pending_votes.clear()

        return jsonify({
            "status": "success",
            "message": "Blockchain imported and validated",
            "blocks": len(blockchain.chain)
        }), 200

    except Exception as e:
        return jsonify({"error": "Import failed", "detail": str(e)}), 500


# -------------------- Run Server --------------------
if __name__ == "__main__":
    import sys

    port = 5000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    print(f"[START] Node running on port {port}")

    # 🔥 tentuin identity node
    my_url = f"http://127.0.0.1:{port}"

    # 🔥 bootstrap node (node pertama di network)
    BOOTSTRAP_NODE = "http://127.0.0.1:5000"

    # 🔥 set file chain
    CHAIN_FILE = os.path.join(CHAIN_DIR, f"chain_{port}.json")

    load_chain_from_file()

    # 🔥 connect ke network (kalau bukan bootstrap)
    if my_url != BOOTSTRAP_NODE:
        try:
            # register ke bootstrap
            requests.post(
                f"{BOOTSTRAP_NODE}/add_peer",
                json={"node": my_url},
                timeout=5
            )

            # 🔥 AMBIL SEMUA PEERS DARI BOOTSTRAP
            response = requests.get(f"{BOOTSTRAP_NODE}/get_peers", timeout=5)
            if response.status_code == 200:
                new_peers = response.json().get("peers", [])
                for p in new_peers:
                    if p != my_url:
                        peers.add(p)

            # jangan lupa bootstrap juga masuk peers
            peers.add(BOOTSTRAP_NODE)

            print(f"[BOOTSTRAP] Connected. Peers: {peers}")

        except Exception as e:
            print(f"[BOOTSTRAP] Failed: {e}")

    # 🔥 initial sync
    print("[SYNC] Initial sync with peers...")
    resolve_conflicts()

    app.run(host="0.0.0.0", port=port, debug=False)