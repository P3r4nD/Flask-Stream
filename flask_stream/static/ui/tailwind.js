window.StreamUI_Tailwind = {

    createServerBlock(container, server) {

        const block = document.createElement("div");

        block.className = "border rounded p-4 mb-4";

        block.innerHTML = `
            <h5 class="font-semibold mb-2">Server: ${server}</h5>

            <div class="file-counter text-sm text-gray-500 mb-2"></div>

            <div class="file-bars mb-3"></div>

            <div class="bg-slate-800 rounded h-4 w-full mb-2">
                <div class="total-bar bg-emerald-400 h-4 rounded text-xs text-slate-900 text-center" style="width:0%">
                    0%
                </div>
            </div>

            <div class="server-log text-sm text-gray-500"></div>
            <div class="provider-log small text-info"></div>
        `;

        container.appendChild(block);

        return block;
    },

    createFileBar(barsContainer) {

        const wrapper = document.createElement("div");

        wrapper.innerHTML = `
            <div class="text-xs mb-1 file-name"></div>

            <div class="bg-slate-800 rounded h-4 w-full mb-2">
                <div class="progress-bar bg-sky-400 h-4 rounded text-xs text-slate-900 text-center" style="width:0%">
                    0%
                </div>
            </div>
        `;

        barsContainer.appendChild(wrapper);

        return {
            wrapper,
            name: wrapper.querySelector(".file-name"),
            bar: wrapper.querySelector(".progress-bar"),
            file: null,
            size: 0
        };
    },

    updateFileBar(slot, percent) {

        slot.bar.style.width = percent + "%";
        slot.bar.innerText = percent + "%";
    },

    updateFileLabel(slot, text) {

        slot.name.innerText = text;
    }

}
