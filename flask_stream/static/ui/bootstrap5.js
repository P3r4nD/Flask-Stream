window.StreamUI_Bootstrap = {

    createServerBlock(container, server) {

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
                <div class="provider-log small text-info"></div>

            </div>
        `;

        container.appendChild(block);

        return block;
    },

    createFileBar(barsContainer) {

        const wrapper = document.createElement("div");

        wrapper.innerHTML = `
            <div class="small file-name"></div>
            <div class="progress mb-2">
                <div class="progress-bar bg-primary" style="width:0%">0%</div>
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
