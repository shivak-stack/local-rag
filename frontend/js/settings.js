const settingsBtn = document.getElementById("settingsBtn");
const drawer = document.getElementById("settingsDrawer");
const settingsCloseBtn = document.getElementById("settingsCloseBtn");
const settingFields = ["searchMode", "topK", "modelSelection"];
const DEFAULT_SETTINGS = { searchMode: "hybrid", topK: 5, model: "qwen3:8b" };

function loadSettings() {
    try {
        return { ...DEFAULT_SETTINGS, ...JSON.parse(localStorage.getItem("ragSettings") || "{}") };
    } catch {
        return { ...DEFAULT_SETTINGS };
    }
}

function saveSettings() {
    const searchMode = document.getElementById("searchMode").value;
    const topKInput = document.getElementById("topK");
    const topK = Math.max(1, Math.min(20, Math.trunc(Number(topKInput.value) || DEFAULT_SETTINGS.topK)));
    topKInput.value = topK;
    const settings = {
        searchMode: ["semantic", "bm25", "hybrid"].includes(searchMode) ? searchMode : DEFAULT_SETTINGS.searchMode,
        topK,
        model: document.getElementById("modelSelection").value || DEFAULT_SETTINGS.model
    };
    localStorage.setItem("ragSettings", JSON.stringify(settings));
}

function applySettings() {
    const saved = loadSettings();
    const mode = document.getElementById("searchMode");
    const topK = document.getElementById("topK");
    const model = document.getElementById("modelSelection");
    mode.value = ["semantic", "bm25", "hybrid"].includes(saved.searchMode) ? saved.searchMode : DEFAULT_SETTINGS.searchMode;
    topK.value = Math.max(1, Math.min(20, Math.trunc(Number(saved.topK) || DEFAULT_SETTINGS.topK)));
    model.value = Array.from(model.options).some(option => option.value === saved.model) ? saved.model : DEFAULT_SETTINGS.model;

    if (!localStorage.getItem("sessionId")) {
        localStorage.setItem("sessionId", crypto.randomUUID ? crypto.randomUUID() : `session-${Date.now()}`);
    }
    saveSettings();
}

function setSettingsOpen(open) {
    drawer?.classList.toggle("open", open);
    settingsBtn?.setAttribute("aria-expanded", String(open));
}

settingsBtn?.setAttribute("aria-controls", "settingsDrawer");
settingsBtn?.setAttribute("aria-expanded", "false");
settingsBtn?.addEventListener("click", () => setSettingsOpen(!drawer?.classList.contains("open")));
settingsCloseBtn?.addEventListener("click", () => setSettingsOpen(false));
document.addEventListener("keydown", event => {
    if (event.key === "Escape" && drawer?.classList.contains("open")) setSettingsOpen(false);
});
document.addEventListener("click", event => {
    if (drawer?.classList.contains("open") && !drawer.contains(event.target) && !settingsBtn?.contains(event.target)) {
        setSettingsOpen(false);
    }
});
for (const id of settingFields) {
    document.getElementById(id)?.addEventListener("change", saveSettings);
}

const exportBtn = document.getElementById("exportBtn");
const exportMenu = document.getElementById("exportMenu");
exportBtn?.addEventListener("click", () => {
    const isOpen = !exportMenu.hidden;
    exportMenu.hidden = isOpen;
    exportBtn.setAttribute("aria-expanded", String(!isOpen));
});
exportMenu?.addEventListener("click", event => {
    const button = event.target.closest("[data-export-format]");
    if (!button) return;
    exportChat(button.dataset.exportFormat);
    exportMenu.hidden = true;
    exportBtn.setAttribute("aria-expanded", "false");
});
document.addEventListener("click", event => {
    if (exportMenu && !exportMenu.hidden && !exportMenu.contains(event.target) && !exportBtn.contains(event.target)) {
        exportMenu.hidden = true;
        exportBtn.setAttribute("aria-expanded", "false");
    }
});

function conversationEntries() {
    return Array.from(document.querySelectorAll("#chatMessages .message"))
        .filter(message => message.classList.contains("user") || message.classList.contains("assistant"))
        .map(message => ({
            role: message.classList.contains("user") ? "You" : "Assistant",
            timestamp: message.dataset.timestamp,
            text: (message.dataset.exportText || message.innerText || "").trim()
        }))
        .filter(entry => entry.text && entry.text !== "Thinking...");
}

function formatTimestamp(timestamp) {
    if (!timestamp) return "";
    const date = new Date(timestamp);
    return Number.isNaN(date.getTime()) ? "" : date.toLocaleString();
}

function exportChat(format) {
    const entries = conversationEntries();
    if (!entries.length) {
        window.showToast?.("There are no messages to export yet.", "error");
        return;
    }
    const transcript = entries.map(entry => {
        const timestamp = formatTimestamp(entry.timestamp);
        const heading = `${entry.role}${timestamp ? ` (${timestamp})` : ""}`;
        return format === "md" ? `## ${heading}\n\n${entry.text}` : `${heading}\n${entry.text}`;
    }).join("\n\n---\n\n");

    if (format === "pdf") {
        downloadBlob(createTranscriptPdf(`# Healthcare Chat Session\n\n${transcript}`), "healthcare-chat.pdf");
        return;
    }
    const content = format === "md" ? `# Healthcare Chat Session\n\n${transcript}` : `Conversation history\n\n${transcript}`;
    downloadBlob(new Blob([content], { type: format === "md" ? "text/markdown;charset=utf-8" : "text/plain;charset=utf-8" }), `healthcare-chat.${format}`);
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function createTranscriptPdf(text) {
    const safeText = text.normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
        .replace(/[\u2013\u2014]/g, "-").replace(/[\u201c\u201d]/g, '"').replace(/[\u2018\u2019]/g, "'")
        .replace(/[^\x20-\x7e\n]/g, "?");
    const lines = [];
    for (const sourceLine of safeText.split("\n")) {
        if (!sourceLine) { lines.push(""); continue; }
        let line = "";
        for (const word of sourceLine.split(/\s+/)) {
            if (line && `${line} ${word}`.length > 88) { lines.push(line); line = word; }
            else line = line ? `${line} ${word}` : word;
        }
        lines.push(line);
    }
    const pages = [];
    for (let index = 0; index < lines.length; index += 47) pages.push(lines.slice(index, index + 47));
    const objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        `<< /Type /Pages /Kids [${pages.map((_, index) => `${4 + index * 2} 0 R`).join(" ")}] /Count ${pages.length} >>`,
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    ];
    const escape = line => line.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
    pages.forEach((pageLines, index) => {
        const pageId = 4 + index * 2;
        const contentId = pageId + 1;
        const commands = ["BT"];
        pageLines.forEach((line, lineIndex) => {
            const heading = line.startsWith("# ") ? 18 : line.startsWith("## ") ? 12 : 10;
            const content = line.replace(/^#{1,2}\s+/, "");
            commands.push(`/F1 ${heading} Tf`);
            commands.push(`1 0 0 1 48 ${750 - lineIndex * 15} Tm`);
            commands.push(`(${escape(content)}) Tj`);
        });
        commands.push("ET");
        const stream = commands.join("\n");
        objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents ${contentId} 0 R >>`);
        objects.push(`<< /Length ${new TextEncoder().encode(stream).length} >>\nstream\n${stream}\nendstream`);
    });

    let pdf = "%PDF-1.4\n% Transcript\n";
    const offsets = [0];
    objects.forEach((object, index) => {
        offsets.push(new TextEncoder().encode(pdf).length);
        pdf += `${index + 1} 0 obj\n${object}\nendobj\n`;
    });
    const xrefOffset = new TextEncoder().encode(pdf).length;
    pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
    offsets.slice(1).forEach(offset => { pdf += `${String(offset).padStart(10, "0")} 00000 n \n`; });
    pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;
    return new Blob([pdf], { type: "application/pdf" });
}

applySettings();

window.addEventListener("DOMContentLoaded", () => {
    const uploadScreen = document.getElementById("uploadScreen");
    const workspace = document.getElementById("workspace");
    if (uploadScreen) uploadScreen.hidden = false;
    if (workspace) workspace.hidden = true;
});
