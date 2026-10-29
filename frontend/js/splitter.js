window.addEventListener("load", () => {
    const splitter = document.getElementById("splitter");
    const viewerPanel = document.getElementById("viewerPanel");
    const workspace = document.getElementById("workspace");
    if (!splitter || !viewerPanel || !workspace) return;

    let dragging = false;
    const narrowLayout = () => window.matchMedia("(max-width: 720px)").matches;

    function applySavedSize() {
        if (narrowLayout()) {
            const height = localStorage.getItem("viewerHeight");
            if (height) {
                viewerPanel.style.flex = "none";
                viewerPanel.style.height = `${height}px`;
            } else {
                viewerPanel.style.flex = "0 0 43%";
                viewerPanel.style.height = "";
            }
            viewerPanel.style.width = "100%";
        } else {
            viewerPanel.style.height = "";
            const width = localStorage.getItem("viewerWidth");
            if (width) {
                viewerPanel.style.flex = "none";
                viewerPanel.style.width = `${width}px`;
            } else {
                viewerPanel.style.flex = "0 0 52%";
                viewerPanel.style.width = "";
            }
        }
    }

    splitter.addEventListener("pointerdown", event => {
        dragging = true;
        splitter.setPointerCapture?.(event.pointerId);
        document.body.style.cursor = narrowLayout() ? "row-resize" : "col-resize";
        event.preventDefault();
    });

    document.addEventListener("pointerup", () => {
        dragging = false;
        document.body.style.cursor = "";
    });

    document.addEventListener("pointermove", event => {
        if (!dragging) return;
        const rect = workspace.getBoundingClientRect();
        viewerPanel.style.flex = "none";

        if (narrowLayout()) {
            const maxHeight = Math.max(110, rect.height - 160);
            const height = Math.max(110, Math.min(event.clientY - rect.top, maxHeight));
            viewerPanel.style.width = "100%";
            viewerPanel.style.height = `${height}px`;
            localStorage.setItem("viewerHeight", String(height));
        } else {
            const maxWidth = Math.max(250, rect.width - 300);
            const width = Math.max(250, Math.min(event.clientX - rect.left, maxWidth));
            viewerPanel.style.height = "";
            viewerPanel.style.width = `${width}px`;
            localStorage.setItem("viewerWidth", String(width));
        }
    });

    applySavedSize();
    window.addEventListener("resize", applySavedSize);
});
