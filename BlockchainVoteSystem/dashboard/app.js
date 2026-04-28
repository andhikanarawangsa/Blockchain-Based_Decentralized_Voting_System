/*
==========================================
Blockchain Voting Dashboard (FIXED FINAL)
==========================================
*/

const NODE_SEEDS = [
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002"
];

let nodes = [];
let lastAliveNodes = [];

// -------------------- DISCOVERY --------------------
async function discoverNodes() {
    try {
        let bootstrap = null;

        for (const node of NODE_SEEDS) {
            try {
                const res = await fetch(`${node}/status`);
                if (res.ok) {
                    bootstrap = node;
                    break;
                }
            } catch {}
        }

        if (!bootstrap) {
            nodes = [];
            return;
        }

        const res = await fetch(`${bootstrap}/network`);
        const data = await res.json();

        const discovered = new Set();

        discovered.add(data.self);

        (data.peers || []).forEach(p => discovered.add(p));

        nodes = [...discovered];

    } catch (e) {
        console.error("Discovery failed:", e);
        nodes = [];
    }
}

// -------------------- FETCH NODE --------------------
async function fetchNode(node) {
    try {
        const res = await fetch(`${node}/status`, { cache: "no-store" });
        if (!res.ok) throw new Error();

        const data = await res.json();

        return {
            node,
            ok: true,
            ...data
        };

    } catch {
        return {
            node,
            ok: false
        };
    }
}

// -------------------- CARD --------------------
function renderCard(data) {
    const card = document.createElement("div");
    card.className = "node-card";

    if (!data.ok) {
        card.innerHTML = `
            <div class="node-title">${data.node}</div>
            <span class="badge offline">OFFLINE</span>
        `;
        return card;
    }

    card.innerHTML = `
        <div class="node-title">${data.node}</div>

        <div class="metrics">
            <p>Pending Votes : <b>${data.pending_votes}</b></p>
            <p>Status : <span class="badge ok">LIVE</span></p>
        </div>
    `;

    return card;
}

// -------------------- GLOBAL RESULTS --------------------
async function fetchGlobalResults() {
    if (!lastAliveNodes.length) return { results: {} };

    const node = lastAliveNodes[0];

    try {
        const res = await fetch(`${node}/results`, { cache: "no-store" });
        if (!res.ok) throw new Error();

        return await res.json();

    } catch {
        return { results: {} };
    }
}

// -------------------- UPDATE --------------------
async function updateDashboard() {

    await discoverNodes();

    const container = document.getElementById("nodes");
    container.innerHTML = "";

    let alive = 0;

    const results = await Promise.all(nodes.map(fetchNode));

    // filter alive nodes
    const aliveNodes = results.filter(n => n.ok);
    lastAliveNodes = aliveNodes.map(n => n.node);

    aliveNodes.forEach(data => {
        container.appendChild(renderCard(data));
        alive++;
    });

    document.getElementById("aliveNodes").innerText = alive;

    // ---------------- RESULTS ----------------
    const global = await fetchGlobalResults();
    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = "";

    const votes = global.results || {};

    const totalVotes = Object.values(votes).reduce((a, b) => a + b, 0) || 1;

    Object.entries(votes)
        .sort((a, b) => b[1] - a[1])
        .forEach(([candidate, count]) => {

            const percent = (count / totalVotes) * 100;

            const el = document.createElement("div");
            el.className = "vote-bar";

            el.innerHTML = `
                <span class="label">${candidate}</span>

                <div class="bar">
                    <div class="fill" style="width:${percent}%"></div>
                </div>

                <span class="value">${percent.toFixed(0)}%</span>
            `;

            resultsDiv.appendChild(el);
        });
}

// ---------------- LOOP ----------------
setInterval(updateDashboard, 2000);
updateDashboard();