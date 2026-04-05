// static/ui/custom.js
window.StreamUI_Custom = {
    createServerBlock: function(server) {
        const container = document.getElementById("stream-container");
        const block = document.createElement("div");
        block.className = "custom-server-block p-4 rounded-md shadow-md mb-4 bg-gray-800 text-white";

        block.innerHTML = `
            <h5 class="font-semibold mb-2">Server: ${server}</h5>
            <div class="file-counter text-sm text-gray-400 mb-2"></div>
            <div class="file-bars mb-3"></div>
            <div class="total-progress-container w-full h-4 bg-gray-700 rounded mb-2">
                <div class="total-bar h-4 bg-indigo-500 w-0 rounded"></div>
            </div>
            <div class="server-log text-sm text-gray-400"></div>
        `;

        container.appendChild(block);

        return {
            block,
            bars: [],
            totalBar: block.querySelector(".total-bar"),
            log: block.querySelector(".server-log"),
            counter: block.querySelector(".file-counter"),
            totalFiles: 0,
            completedFiles: 0
        };
    },

    assignBar: function(serverUI, file) {
        for (let slot of serverUI.bars) {
            if (!slot.file) {
                slot.file = file;
                return slot;
            }
        }
        if (!window.STREAM_CONFIG.bulk) {
            const slot = serverUI.bars[0];
            slot.file = file;
            return slot;
        }
        return null;
    },

    findBar: function(serverUI, file) {
        return serverUI.bars.find(b => b.file === file);
    }
};
