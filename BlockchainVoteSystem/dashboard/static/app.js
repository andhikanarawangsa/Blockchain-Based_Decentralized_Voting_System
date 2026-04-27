async function loadData() {
    const res = await fetch("/api/status");
    const data = await res.json();

    const container = document.getElementById("container");
    container.innerHTML = "";

    data.forEach(node => {
        const div = document.createElement("div");
        div.className = "card";

        if (node.error) {
            div.innerHTML = `<h3>${node.node}</h3><p class="bad">OFFLINE</p>`;
        } else {
            div.innerHTML = `
                <h3>${node.node}</h3>
                <p>Chain Length: ${node.chain_length}</p>
                <p>Pending Votes: ${node.pending}</p>
                <p>Status: ${node.valid ? "OK" : "INVALID"}</p>
                <p>Results: ${JSON.stringify(node.results)}</p>
            `;
        }

        container.appendChild(div);
    });
}

setInterval(loadData, 2000);
loadData();