import requests, json, hashlib, sys, os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

BASE_URL = "http://127.0.0.1:5000"
KEY_DIR = "keys"
CHAIN_DIR = "chain"
os.makedirs(CHAIN_DIR, exist_ok=True)

# --- Existing functions ---
def cmd_genkeys(voter_id):
    try:
        from generate_keys import generate_keys
        generate_keys(voter_id)
    except Exception:
        print("generate_keys.py not found or error importing it.")

def register(voter_id, public_pem_path=None):
    if not public_pem_path:
        public_pem_path = os.path.join(KEY_DIR, f"{voter_id}_public.pem")
    with open(public_pem_path, "r") as f:
        pem = f.read()
    r = requests.post(BASE_URL + "/register", json={"voter_id": voter_id, "public_key": pem})
    return r.json()  # <-- return data instead of print

def vote(voter_id, candidate):
    priv_path = os.path.join(KEY_DIR, f"{voter_id}_private.pem")
    with open(priv_path, "rb") as f:
        priv = serialization.load_pem_private_key(f.read(), password=None)

    voter_hash = hashlib.sha256(voter_id.encode()).hexdigest()
    message = f"{voter_hash}:{candidate}".encode()
    signature = priv.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    r = requests.post(BASE_URL + "/vote", json={"voter_hash": voter_hash, "candidate": candidate, "signature": signature.hex()})
    return r.json()

def force_commit():
    r = requests.post(BASE_URL + "/force_commit")
    return r.json()

# --- Update: return dict instead of print ---
def show_chain():
    r = requests.get(BASE_URL + "/chain")
    try:
        return r.json()
    except:
        return None

def show_results():
    r = requests.get(BASE_URL + "/results")
    try:
        return r.json()
    except:
        return None

# --- New functions ---
def reset_blockchain():
    r = requests.post(BASE_URL + "/reset")
    return r.json() if r.status_code==200 else {"error": r.status_code}

def validate_chain():
    r = requests.get(BASE_URL + "/validate")
    return r.json() if r.status_code==200 else {"error": r.status_code}

def export_chain():
    r = requests.get(BASE_URL + "/chain")
    if r.status_code != 200:
        return {"error": r.status_code}
    data = r.json()
    filename = os.path.join(CHAIN_DIR, f"chain_export.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return {"status": "success", "file": filename}

def import_chain(filename):
    filepath = os.path.join(CHAIN_DIR, filename)
    if not os.path.exists(filepath):
        return {"error": f"File {filepath} does not exist."}
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    payload = {"chain": data["chain"]}  # ✅ hanya kirim chain
    
    r = requests.post(BASE_URL + "/import", json=payload)
    return r.json() if r.status_code==200 else {"error": r.status_code}


# --- CLI help ---
def help_text():
    print("Usage:")
    print(" python client.py genkeys <voter_id>")
    print(" python client.py register <voter_id>")
    print(" python client.py vote <voter_id> <candidate>")
    print(" python client.py force_commit")
    print(" python client.py chain")
    print(" python client.py results")
    print(" python client.py reset")
    print(" python client.py validate")
    print(" python client.py export")
    print(" python client.py import <filename>")

# --- CLI ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        help_text(); sys.exit(0)
    cmd = sys.argv[1].lower()
    if cmd == "genkeys" and len(sys.argv)==3:
        cmd_genkeys(sys.argv[2])
    elif cmd == "register" and len(sys.argv)==3:
        print(json.dumps(register(sys.argv[2]), indent=2))
    elif cmd == "vote" and len(sys.argv)==4:
        print(json.dumps(vote(sys.argv[2], sys.argv[3]), indent=2))
    elif cmd == "force_commit":
        print(json.dumps(force_commit(), indent=2))
    elif cmd == "chain":
        print(json.dumps(show_chain(), indent=2))
    elif cmd == "results":
        print(json.dumps(show_results(), indent=2))
    elif cmd == "reset":
        print(json.dumps(reset_blockchain(), indent=2))
    elif cmd == "validate":
        print(json.dumps(validate_chain(), indent=2))
    elif cmd == "export":
        print(json.dumps(export_chain(), indent=2))
    elif cmd == "import" and len(sys.argv)==3:
        print(json.dumps(import_chain(sys.argv[2]), indent=2))
    else:
        help_text()
