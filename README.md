# Decentralized Blockchain Voting System
This project is a **decentralized voting system built on blockchain technology** that ensures vote integrity, transparency, and tamper resistance using cryptographic signatures and Proof-of-Work consensus.
The system is designed as a **multi-node peer-to-peer network**, where each node maintains a replicated blockchain and participates in consensus without a central authority.

---

## Key Features
### Blockchain Core
- Proof-of-Work consensus mechanism
- Longest-chain conflict resolution
- Persistent chain storage per node
- Block validation & integrity checks

### Voting System
- RSA-based digital signatures
- Voter registration via public key binding
- Double-voting prevention
- Pending vote pooling before block mining

### Peer-to-Peer Network
- Automatic node discovery (seed-based bootstrap)
- Peer synchronization across nodes
- Broadcast-based block propagation

### Client Interface
- CLI client for scripting/testing
- GUI client (Tkinter) for interactive voting
- Automatic node detection and failover handling

### Dashboard
- Real-time node status monitoring
- Live vote results visualization
- Peer network overview
- Blockchain state inspection

---

## Technologies Used
- Python 3
- Flask + Flask-CORS
- Cryptography (RSA, PSS signatures)
- Requests (P2P communication)
- Tkinter (GUI client)
- HTML / CSS / JavaScript (Dashboard frontend)

---

## Documents
- [Architecture, Flow, and Security](./Docs/Architecture.md)
- [Setup Guide](./Docs/Setup.md)
- [Research & Future Work](./Docs/Research.md)

---

## ⚠️ Disclaimer
This project is built for educational and research purposes only.  
It is not intended for production election systems without further security hardening and formal verification.
