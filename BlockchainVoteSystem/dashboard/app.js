/*
==========================================
Blockchain Voting Dashboard (FINAL CLEAN v2)
==========================================
*/

const BOOTSTRAP_NODE = "http://127.0.0.1:5000";
let nodes = [];

// -------------------- DISCOVERY --------------------
async function discoverNodes() {
    try {
        const res = await fetch(`${BOOTSTRAP_NODE}/network`);
        const data = await res.json();

        const discovered = new Set();
        discovered.add(data.self);

        (data.peers || []).forEach(p => discovered.add(p));

        nodes = Array.from(discovered);

    } catch (e) {
        console.error("Discovery failed:", e);
        nodes = [BOOTSTRAP_NODE];
    }
}

// -------------------- FETCH NODE --------------------
async function fetchNode(node) {
    try {
        const res = await fetch(`${node}/status`);
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
            <p>Peers : <b>${data.peers?.length || 0}</b></p>
            <p>Status : <span class="badge ok">LIVE</span></p>
        </div>
    `;

    return card;
}

// -------------------- GLOBAL RESULTS --------------------
async function fetchGlobalResults() {
    if (!nodes.length) return { results: {} };

    try {
        const res = await fetch(`${nodes[0]}/results`);
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

    results.forEach(data => {
        container.appendChild(renderCard(data));
        if (data.ok) alive++;
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