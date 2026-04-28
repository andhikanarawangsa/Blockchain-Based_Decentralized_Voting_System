# ==========================================
# Decentralized Voting Blockchain (Client Node using GUI)
# Author : Andhika Narawangsa Susilo
# https://github.com/andhikanarawangsa
# ==========================================

# Description:
# GUI-based client for interacting with a decentralized voting blockchain, supporting key generation, registration, and cryptographically signed voting.
# Handles automatic node discovery and provides an interactive interface for blockchain communication and result viewing.

# -------------------- IMPORTS --------------------
import tkinter as tk
from tkinter import messagebox
import requests
import hashlib
import json
import os
import subprocess

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# -------------------- CONFIG --------------------
SEED_NODES = [
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002"
]

BASE_URL = None
KEY_DIR = "keys"

os.makedirs(KEY_DIR, exist_ok=True)

# -------------------- THEME --------------------
BG = "#0d0d0d"
CARD = "#1a1a1a"
BORDER = "#2a2a2a"
TEXT = "#e6e6e6"
MUTED = "#a0a0a0"
GREEN = "#16a34a"
BLUE = "#0077ff"

# -------------------- NODE DISCOVERY --------------------
def discover_node():
    global BASE_URL

    for node in SEED_NODES:
        try:
            r = requests.get(node + "/ping", timeout=1)
            if r.status_code == 200:
                BASE_URL = node
                print("[CONNECTED]", BASE_URL)
                return
        except:
            continue

    BASE_URL = None

def is_alive():
    return BASE_URL is not None

# -------------------- REQUEST WRAPPER --------------------
def post(path, data=None):
    try:
        r = requests.post(BASE_URL + path, json=data, timeout=3)
        return r.json()
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None

def get(path):
    try:
        r = requests.get(BASE_URL + path, timeout=3)
        return r.json()
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None

# -------------------- CORE ACTIONS --------------------
def generate_keys():
    voter_id = entry_voter.get()

    if not voter_id:
        messagebox.showerror("Error", "Voter ID required")
        return

    try:
        subprocess.run(["python", "generate_keys.py", voter_id], check=True)
        messagebox.showinfo("Success", f"Keys generated for {voter_id}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def register():
    if not is_alive():
        return

    voter_id = entry_voter.get()

    try:
        with open(f"{KEY_DIR}/{voter_id}_public.pem", "r") as f:
            pub = f.read()
    except:
        messagebox.showerror("Error", "Public key not found")
        return

    res = post("/register", {
        "voter_id": voter_id,
        "public_key": pub
    })

    if res:
        messagebox.showinfo("Register", json.dumps(res, indent=2))


def vote():
    if not is_alive():
        return

    voter_id = entry_voter.get()
    candidate = entry_candidate.get()

    priv_path = f"{KEY_DIR}/{voter_id}_private.pem"

    try:
        with open(priv_path, "rb") as f:
            priv = serialization.load_pem_private_key(f.read(), password=None)
    except:
        messagebox.showerror("Error", "Private key not found")
        return

    voter_hash = hashlib.sha256(voter_id.encode()).hexdigest()
    msg = f"{voter_hash}:{candidate}".encode()

    signature = priv.sign(
        msg,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )

    res = post("/vote", {
        "voter_hash": voter_hash,
        "candidate": candidate,
        "signature": signature.hex()
    })

    if res:
        messagebox.showinfo("Vote", json.dumps(res, indent=2))


def force_commit():
    if not is_alive():
        return

    res = post("/force_commit")
    if res:
        messagebox.showinfo("Commit", json.dumps(res, indent=2))


def show_results():
    if not is_alive():
        return

    res = get("/results")
    if res:
        messagebox.showinfo("Results", json.dumps(res, indent=2))


def show_chain():
    if not is_alive():
        return

    res = get("/chain")
    if res:
        messagebox.showinfo("Chain", json.dumps(res, indent=2))

# -------------------- STARTUP CHECK --------------------
discover_node()

if not is_alive():
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "System Offline",
        "No active blockchain node found.\nGUI cannot start."
    )
    exit()

# -------------------- UI --------------------
root = tk.Tk()
root.title("Blockchain Voting Client")
root.geometry("520x620")
root.configure(bg=BG)

# HEADER
tk.Label(
    root,
    text="Blockchain Voting Client",
    bg=BG,
    fg=TEXT,
    font=("Arial", 18, "bold")
).pack(pady=10)

# CARD
card = tk.Frame(root, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
card.pack(padx=20, pady=10, fill="both")

# INPUTS
tk.Label(card, text="Voter ID", bg=CARD, fg=TEXT).pack(pady=(10, 0))
entry_voter = tk.Entry(card, bg="#111", fg=TEXT, insertbackground=TEXT)
entry_voter.pack(pady=5, ipadx=10, ipady=5)

tk.Label(card, text="Candidate", bg=CARD, fg=TEXT).pack(pady=(10, 0))
entry_candidate = tk.Entry(card, bg="#111", fg=TEXT, insertbackground=TEXT)
entry_candidate.pack(pady=5, ipadx=10, ipady=5)

# BUTTON FACTORY
def btn(text, cmd, color):
    return tk.Button(
        card,
        text=text,
        command=cmd,
        bg=color,
        fg="white",
        relief="flat",
        padx=10,
        pady=6
    )

# BUTTONS
btn("Generate Keys", generate_keys, "#555").pack(pady=5, fill="x", padx=20)
btn("Register", register, GREEN).pack(pady=5, fill="x", padx=20)
btn("Vote", vote, BLUE).pack(pady=5, fill="x", padx=20)
btn("Force Commit", force_commit, "#444").pack(pady=5, fill="x", padx=20)

# EXTRA
tk.Button(root, text="Results", command=show_results, bg=CARD, fg=TEXT, relief="flat").pack(pady=5, fill="x", padx=20)
tk.Button(root, text="Chain", command=show_chain, bg=CARD, fg=TEXT, relief="flat").pack(pady=5, fill="x", padx=20)

# STATUS
tk.Label(
    root,
    text=f"Connected Node: {BASE_URL}",
    bg=BG,
    fg=MUTED
).pack(pady=10)

root.mainloop()