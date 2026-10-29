async function askQuestion(
    question
){

    const settings = JSON.parse(localStorage.getItem("ragSettings") || "{}");
    const response =
        await fetch(
            "/chat",
            {
                method:"POST",

                headers:{
                    "Content-Type":
                        "application/json"
                },

                body:JSON.stringify(
                    {
                        question,
                        mode: settings.searchMode || "hybrid",
                        active_document: localStorage.getItem("activeDocument"),
                        session_id: localStorage.getItem("sessionId") || "default",
                        top_k: Number(settings.topK ?? 5),
                        model: settings.model || "qwen3:8b"
                    }
                )
            }
        );

    const responseText = await response.text();
    let result;

    try {
        result = responseText ? JSON.parse(responseText) : {};
    } catch {
        result = { detail: responseText || "The server returned an unreadable response." };
    }

    if (!response.ok) {
        throw new Error(result.detail || `Chat request failed (${response.status}).`);
    }

    return result;

}

async function setActiveDocument(filename){
    const response = await fetch("/set-active-document", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename })
    });

    const result = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(result.detail || "Could not select document");
    }
    return result;
}

async function getDocuments(){

    const response =
        await fetch(
            "/documents"
        );

    return await response.json();

}

async function deleteDocument(
    filename
){

    await fetch(
        `/documents/${filename}`,
        {
            method:"DELETE"
        }
    );

}

window.askQuestion =
    askQuestion;

window.getDocuments =
    getDocuments;

window.deleteDocument =
    deleteDocument;

window.setActiveDocument = setActiveDocument;
window.getDocumentChunks = async function(filename) {
    const response = await fetch(`/document/${encodeURIComponent(filename)}`);
    if (!response.ok) throw new Error("Could not load source chunks");
    return (await response.json()).chunks || [];
};
