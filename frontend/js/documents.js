console.log(
    "documents.js loaded"
);

const documentsBtn =
    document.getElementById(
        "documentsBtn"
    );

console.log(
    "documentsBtn:",
    documentsBtn
);

const documentsPanel = document.getElementById("documentsPanel");
documentsPanel.hidden = true;
documentsBtn.setAttribute("aria-expanded", "false");
documentsBtn.setAttribute("aria-controls", "documentsPanel");

documentsBtn.addEventListener(
    "click",
    async () => {

        const opening = documentsPanel.hidden;
        documentsPanel.hidden = !opening;
        documentsBtn.setAttribute("aria-expanded", String(opening));
        if (opening) await loadDocuments();

    }
);

async function loadDocuments(){

    try{

        const result =
            await getDocuments();

        const panel =
            document.getElementById(
                "documentsPanel"
            );

        panel.innerHTML = "";

        if(
            !result.documents ||
            result.documents.length === 0
        ){

            panel.innerHTML =
                "<p>No documents found</p>";

            return;

        }

        result.documents.forEach(
            doc => {

                const row =
                    document.createElement(
                        "div"
                    );

                row.className =
                    "document-row";

                row.innerHTML =
                `
                <span>${doc}</span>

                <button
                    class="delete-btn"
                    onclick="event.stopPropagation(); removeDocument('${doc}')"
                >
                    🗑
                </button>
                `;

                row.onclick =
                    async () => {

                        try {
                        await setActiveDocument(doc);

                        const previousDocument = localStorage.getItem("activeDocument");
                        if (previousDocument && previousDocument !== doc) {
                            window.clearChatForDocument?.();
                        }

                        localStorage.setItem(
                            "activeDocument",
                            doc
                        );

                        showWorkspace();
                        loadDocumentViewer();

                        } catch(error) {
                            console.error(error);
                            window.showToast?.(error.message, "error");
                        }

                    };

                panel.appendChild(
                    row
                );

            }
        );

    }
    catch(error){

        console.error(
            error
        );

    }

}

async function removeDocument(
    filename
){

    try{

        await deleteDocument(
            filename
        );
        window.showToast?.("Document deleted.", "success");

        const activeDocument =
            localStorage.getItem(
                "activeDocument"
            );

        if(
            activeDocument ===
            filename
        ){

            await setActiveDocument(null);

            localStorage.removeItem(
                "activeDocument"
            );

        }

        await loadDocuments();

    }
    catch(error){

        console.error(
            error
        );

    }

}

window.removeDocument =
    removeDocument;
