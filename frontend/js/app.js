window.showToast = function(message, kind = "info") {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.className = `visible ${kind}`;
    clearTimeout(window.toastTimer);
    window.toastTimer = setTimeout(() => { toast.className = ""; }, 2800);
};

window.addEventListener(
    "DOMContentLoaded",
    () => {
        localStorage.removeItem("activeDocument");
        setActiveDocument(null).catch(console.error);
        const uploadScreen = document.getElementById("uploadScreen");
        const workspace = document.getElementById("workspace");
        if (uploadScreen) uploadScreen.hidden = false;
        if (workspace) workspace.hidden = true;
    }
);

function resetWorkspace(){

    localStorage.removeItem(
        "activeDocument"
    );

    location.reload();

}
