# ==========================================
# Decentralized Voting Blockchain (Core Blockchain Implementation)
# Author : Andhika Narawangsa Susilo
# https://github.com/andhikanarawangsa
# ==========================================

# Description : Used by server node for decentralized voting system
# Contains: Block structure (with Proof-of-Work), Blockchain chain management, Validation logic, Serialization (save/load/import)

# -------------------- IMPORTS --------------------
import hashlib
import json
from time import time

# -------------------- BLOCK CLASS --------------------
class Block:
    # Initialize
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data  # list of votes
        self.previous_hash = previous_hash
        self.nonce = 0  # PoW
        self.hash = self.hash_block()

    # Hashing
    def hash_block(self):
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }
        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    # Mining (PoW)
    def mine_block(self, difficulty=4):
        """Proof of Work: cari hash yang diawali dengan '0'*difficulty"""
        prefix = "0" * difficulty
        while not self.hash.startswith(prefix):
            self.nonce += 1
            self.hash = self.hash_block()
        print(f"Block mined: {self.hash} (nonce={self.nonce})")

    # Serialization
    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

# -------------------- BLOCKCHAIN CLASS --------------------
class Blockchain:
    # Initialize
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        self.chain = []
        genesis_block = Block(0, time(), "Genesis Block", "0")
        # Bisa juga ditambang, tapi biasanya genesis langsung valid
        self.chain.append(genesis_block)

    def get_last_block(self):
        return self.chain[-1]

    # Validation
    def is_valid(self, difficulty=4):
        prefix = "0" * difficulty
        for i in range(1, len(self.chain)):
            prev = self.chain[i-1]
            curr = self.chain[i]

            if curr.previous_hash != prev.hash: # hash linkage
                print(f"[INVALID] Block {i}: previous_hash mismatch")
                return False

            if curr.hash != curr.hash_block(): # hash correctness
                print(f"[INVALID] Block {i}: hash mismatch")
                return False

            if not curr.hash.startswith(prefix): # Proof-of-Work validity
                print(f"[INVALID] Block {i}: PoW invalid")
                return False

        return True

    # Conversion
    def to_dict(self):
        return [b.to_dict() for b in self.chain]

    def from_dict(self, chain_json):
        self.chain = []

        for block_data in chain_json:
            block = Block(
                index=block_data["index"],
                timestamp=block_data["timestamp"],
                data=block_data["data"],
                previous_hash=block_data["previous_hash"]
            )
            block.nonce = block_data.get("nonce", 0)
            block.hash = block_data.get("hash", block.hash)
            self.chain.append(block)


    # File Storage 
    def save_to_file(self, filename="chain_dump.json"): # Save to JSON
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)
        return filename

    def load_from_file(self, filename="chain_dump.json"): # Load from JSON
        with open(filename, "r", encoding="utf-8") as f:
            arr = json.load(f)
        self.chain = []
        for item in arr:
            blk = Block(
                index=item["index"],
                timestamp=item["timestamp"],
                data=item["data"],
                previous_hash=item["previous_hash"]
            )
            blk.nonce = item.get("nonce", 0)
            blk.hash = item.get("hash", blk.hash)
            self.chain.append(blk)
        return True