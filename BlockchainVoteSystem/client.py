import requests, json, hashlib, sys, os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

BASE_URL = "http://127.0.0.1:5000"
KEY_DIR = "keys"
CHAIN_DIR = "chain"

# --- Helper: run generate_keys if asked ---
def cmd_genkeys(voter_id):
    try:
        from generate_keys import generate_keys
    except Exception:
        print("generate_keys.py not found or error importing it.")
        return
    generate_keys(voter_id)

# --- Register voter ---
def register(voter_id, public_pem_path=None):
    if not public_pem_path:
        public_pem_path = os.path.join(KEY_DIR, f"{voter_id}_public.pem")
    try:
        with open(public_pem_path, "r", encoding="utf-8") as f:
            pem = f.read()
    except FileNotFoundError:
        print("Public key file not found:", public_pem_path); return
    payload = {"voter_id": voter_id, "public_key": pem}
    r = requests.post(BASE_URL + "/register", json=payload)
    try:
        print(r.status_code, json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.status_code, r.text)

# --- Vote ---
def sign_and_vote(voter_id, candidate, region="default"):
    priv_path = os.path.join(KEY_DIR, f"{voter_id}_private.pem")
    try:
        with open(priv_path, "rb") as f:
            priv = serialization.load_pem_private_key(f.read(), password=None)
    except FileNotFoundError:
        print("Private key not found:", priv_path); return
    except Exception as e:
        print("Failed load private key:", e); return

    voter_hash = hashlib.sha256(voter_id.encode()).hexdigest()
    message = f"{voter_hash}:{candidate}".encode()
    try:
        signature = priv.sign(
            message,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
    except Exception as e:
        print("Signing failed:", e); return

    payload = {
        "voter_hash": voter_hash,
        "candidate": candidate,
        "signature": signature.hex(),
        "region": region
    }
    r = requests.post(BASE_URL + "/vote", json=payload)
    try:
        print(r.status_code, json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.status_code, r.text)

# --- Show blockchain ---
def show_chain(region="default"):
    r = requests.get(BASE_URL + "/chain", params={"region": region})
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.text)

# --- Validate chain ---
def validate(region="default"):
    r = requests.get(BASE_URL + "/validate", params={"region": region})
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)

# --- Export chain ---
def export_chain(region="default"):
    r = requests.get(BASE_URL + "/export", params={"region": region})
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.text)

# --- Import chain ---
def import_chain(filename, region="default"):
    r = requests.post(BASE_URL + "/import", json={"filename": filename, "region": region})
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.text)

# --- Reset chain ---
def reset_chain(region="default"):
    r = requests.post(BASE_URL + "/reset", params={"region": region})
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.text)

# --- Show voting results ---
def show_results(region="default"):
    r = requests.get(BASE_URL + "/results", params={"region": region})
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(r.text)

# --- Help text ---
def help_text():
    print("Usage:")
    print("  python client.py genkeys <voter_id>                       # create keys under keys/")
    print("  python client.py register <voter_id> [pub.pem]            # upload public key to server")
    print("  python client.py vote <voter_id> <candidate> [region]     # sign and submit vote")
    print("  python client.py chain [region]                            # show blockchain")
    print("  python client.py validate [region]                         # validate blockchain")
    print("  python client.py export [region]                           # export blockchain")
    print("  python client.py import <filename> [region]               # import blockchain")
    print("  python client.py reset [region]                             # reset blockchain")
    print("  python client.py results [region]                           # show voting results")

# --- Main CLI ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        help_text(); sys.exit(0)
    cmd = sys.argv[1].lower()

    if cmd == "genkeys" and len(sys.argv) == 3:
        cmd_genkeys(sys.argv[2])
    elif cmd == "register" and len(sys.argv) in (3,4):
        register(sys.argv[2], sys.argv[3] if len(sys.argv)==4 else None)
    elif cmd == "vote" and len(sys.argv) in (4,5):
        region = sys.argv[4] if len(sys.argv)==5 else "default"
        sign_and_vote(sys.argv[2], sys.argv[3], region)
    elif cmd == "chain":
        region = sys.argv[2] if len(sys.argv)==3 else "default"
        show_chain(region)
    elif cmd == "validate":
        region = sys.argv[2] if len(sys.argv)==3 else "default"
        validate(region)
    elif cmd == "export":
        region = sys.argv[2] if len(sys.argv)==3 else "default"
        export_chain(region)
    elif cmd == "import" and len(sys.argv) in (3,4):
        region = sys.argv[3] if len(sys.argv)==4 else "default"
        import_chain(sys.argv[2], region)
    elif cmd == "reset":
        region = sys.argv[2] if len(sys.argv)==3 else "default"
        reset_chain(region)
    elif cmd == "results":
        region = sys.argv[2] if len(sys.argv)==3 else "default"
        show_results(region)
    else:
        help_text()
