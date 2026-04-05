document.addEventListener("DOMContentLoaded", () => {

    const btn = document.getElementById("stream-btn");
    const container = document.getElementById("stream-container");

    const CONFIG = window.STREAM_CONFIG;

    const serversUI = {};

    function createServerBlock(server) {
        const block = document.createElement("div");
        block.className = "card mb-4";

        block.innerHTML = `
            <div class="card-body">

                <h5>Server: ${server}</h5>

                <div class="file-counter small text-muted mb-2"></div>

                <div class="file-bars mb-3"></div>

                <div class="progress mb-2">
                    <div class="progress-bar bg-success total-bar" style="width:0%">0%</div>
                </div>

                <div class="server-log small text-muted"></div>

            </div>
        `;

        container.appendChild(block);

        serversUI[server] = {
            block,
            bars: [],   // ← vacío al inicio
            totalBar: block.querySelector(".total-bar"),
            log: block.querySelector(".server-log"),
            counter: block.querySelector(".file-counter"),
            totalFiles: 0,
            completedFiles: 0
        };
    }


    function assignBar(serverUI, file) {

        // looking for an open bar
        for (let slot of serverUI.bars) {
            if (!slot.file) {
                slot.file = file;
                return slot;
            }
        }

        // If sequential always uses the first
        if (!CONFIG.bulk) {
            const slot = serverUI.bars[0];
            slot.file = file;
            return slot;
        }

        return null;
    }

    function findBar(serverUI, file) {

        return serverUI.bars.find(b => b.file === file);
    }

    function pushLog(log, html) {
        const div = document.createElement("div");
        div.innerHTML = html;
        log.appendChild(div);
    }

    function addLogMessage(html, es) {
        const log = document.getElementById("stream-log");

        if (log.children.length >= CONFIG.max_reconnect) {
            log.replaceChildren();
            pushLog(log, `<span class="text-danger">Server or App disconnected</span>`);
            log.scrollTop = log.scrollHeight;
            es?.close?.();
            return;
        }

        pushLog(log, html);
        log.scrollTop = log.scrollHeight;
    }



    btn.onclick = async () => {

        container.innerHTML = "";
        Object.keys(serversUI).forEach(k => delete serversUI[k]);

        const r = await fetch("/stream/start", { method: "POST" });
        const j = await r.json();

        const es = new EventSource(`/stream/events/${j.job_id}`);

        const log = document.getElementById("stream-log");

        es.addEventListener("Batch", e => {
            const data = JSON.parse(e.data);
            const server = data.server;

            if (!serversUI[server]) createServerBlock(server);

            const serverUI = serversUI[server];
            serverUI.totalFiles = data.total;

            if (serverUI.bars.length > 0) return;

            const barsContainer = serverUI.block.querySelector(".file-bars");

            const barCount = (data.total === 1) ? 1 :
                            (CONFIG.bulk ? CONFIG.max_simultaneous : 1);

            for (let i = 0; i < barCount; i++) {
                const wrapper = document.createElement("div");
                wrapper.innerHTML = `
                    <div class="small file-name"></div>
                    <div class="progress mb-2">
                        <div class="progress-bar bg-primary" style="width:0%">0%</div>
                    </div>
                `;
                barsContainer.appendChild(wrapper);

                serverUI.bars.push({
                    wrapper,
                    name: wrapper.querySelector(".file-name"),
                    bar: wrapper.querySelector(".progress-bar"),
                    file: null,
                    size: 0
                });
            }
        });

        es.addEventListener("File", e => {

            const data = JSON.parse(e.data);
            const server = data.server;

            if (!serversUI[server]) createServerBlock(server);

            const serverUI = serversUI[server];

            const slot = assignBar(serverUI, data.file);

            if (!slot) return;

            slot.file = data.file;
            slot.size = data.size;

            const totalMB = (data.size / 1024 / 1024).toFixed(1);

            slot.name.innerText = `${data.file} (Downloaded 0 MB de ${totalMB} MB)`;

            slot.bar.style.width = "0%";
            slot.bar.innerText = "0%";

        });

        es.addEventListener("Progress", e => {

            const data = JSON.parse(e.data);

            const serverUI = serversUI[data.server];

            if (!serverUI) return;

            const slot = findBar(serverUI, data.file);

            if (!slot) return;

            slot.bar.style.width = data.percent + "%";
            slot.bar.innerText = data.percent + "%";

            if (slot.size) {

                const downloaded = slot.size * data.percent / 100;

                const downloadedMB = (downloaded / 1024 / 1024).toFixed(1);
                const totalMB = (slot.size / 1024 / 1024).toFixed(1);

                slot.name.innerText =
                    `${data.file} (Downloaded ${downloadedMB} MB de ${totalMB} MB)`;
            }
        });

        es.addEventListener("FileDone", e => {

            const data = JSON.parse(e.data);
            const serverUI = serversUI[data.server];

            if (!serverUI) return;

            const slot = findBar(serverUI, data.file);

            if (slot) slot.file = null;

            serverUI.completedFiles++;

            const percent = Math.floor(
                serverUI.completedFiles / serverUI.totalFiles * 100
            );

            serverUI.totalBar.style.width = percent + "%";
            serverUI.totalBar.innerText = percent + "%";

            serverUI.counter.innerText =
                `File ${serverUI.completedFiles} / ${serverUI.totalFiles}`;

        });

        es.addEventListener("debug", e => {

            const data = JSON.parse(e.data);
            const server = data.server;

            if (!serversUI[server]) createServerBlock(server);

            const log = serversUI[server].log;

            log.innerHTML += `<div>${data.msg}</div>`;
            log.scrollTop = log.scrollHeight;

        });

        es.addEventListener("done", () => {

            Object.values(serversUI).forEach(serverUI => {

                serverUI.totalBar.style.width = "100%";
                serverUI.totalBar.innerText = "100%";

            });

            es.close();

        });

        // Connection error capture
        es.onerror = (e) => {
            if (es.readyState === EventSource.CLOSED) {
                addLogMessage(`<span class="text-danger">Server or App disconnected</span>`, es);
            } else {
                addLogMessage(`<span class="text-warning">Connection interrupted, attempting to reconnect...</span>`, es);
            }
        };
    };

});
