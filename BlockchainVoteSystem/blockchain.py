# blockchain.py
import hashlib
import json
from time import time

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.hash_block()

    def hash_block(self):
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }
        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        self.chain = []
        self.chain.append(Block(0, time(), "Genesis Block", "0"))

    def get_last_block(self):
        return self.chain[-1]

    def add_vote(self, voter_hash, candidate_name):
        data = {
            "voter": voter_hash,
            "candidate": candidate_name
        }
        previous_block = self.get_last_block()
        new_block = Block(
            index=len(self.chain),
            timestamp=time(),
            data=data,
            previous_hash=previous_block.hash
        )
        self.chain.append(new_block)
        return new_block

    def is_valid(self):
        for i in range(1, len(self.chain)):
            prev = self.chain[i-1]
            curr = self.chain[i]
            if curr.previous_hash != prev.hash:
                return False
            if curr.hash != curr.hash_block():
                return False
        return True

    def to_dict(self):
        return [b.to_dict() for b in self.chain]

    def save_to_file(self, filename="chain_dump.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4)
        return filename

    def load_from_file(self, filename="chain_dump.json"):
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
            blk.hash = item.get("hash", blk.hash)
            self.chain.append(blk)
        return True
