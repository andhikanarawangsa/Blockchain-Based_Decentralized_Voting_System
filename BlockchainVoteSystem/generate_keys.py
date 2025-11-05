# generate_keys.py
import os
import sys
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

KEY_DIR = "keys"

def ensure_key_dir():
    os.makedirs(KEY_DIR, exist_ok=True)

def generate_keys(voter_id):
    ensure_key_dir()
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    priv_file = os.path.join(KEY_DIR, f"{voter_id}_private.pem")
    pub_file = os.path.join(KEY_DIR, f"{voter_id}_public.pem")

    with open(priv_file, "wb") as f:
        f.write(private_keys_bytes(private_key))

    with open(pub_file, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    print("Keys generated:")
    print(" Private:", priv_file)
    print(" Public :", pub_file)
    print("NOTE: Keep the private file safe and never upload it anywhere.")

def private_keys_bytes(private_key):
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_keys.py <voter_id>")
    else:
        generate_keys(sys.argv[1])
