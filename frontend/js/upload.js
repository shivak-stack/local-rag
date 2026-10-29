const fileInput =
document.getElementById(
    "fileInput"
);

const browseBtn =
document.getElementById(
    "browseBtn"
);

const uploadBtn =
document.getElementById(
    "uploadBtn"
);

const dropZone =
document.getElementById(
    "dropZone"
);

const uploadStatus = document.getElementById("uploadStatus");

const uploadScreen =
document.getElementById(
    "uploadScreen"
);

const workspace =
document.getElementById(
    "workspace"
);

browseBtn.addEventListener(
    "click",
    () => fileInput.click()
);

if(uploadBtn){

    uploadBtn.addEventListener(
        "click",
        async () => {

            localStorage.removeItem(
                "activeDocument"
            );

            await setActiveDocument(null).catch(console.error);
            if (uploadScreen) uploadScreen.hidden = false;
            if (workspace) workspace.hidden = true;

            fileInput.click();

        }
    );

}

fileInput.addEventListener(
    "change",
    async (e) => {

        if(
            !e.target.files.length
        ){
            return;
        }

        await uploadFile(
            e.target.files[0]
        );

    }
);

dropZone.addEventListener(
    "dragover",
    (e)=>{

        e.preventDefault();

    }
);

dropZone.addEventListener(
    "drop",
    async (e)=>{

        e.preventDefault();

        const file =
            e.dataTransfer.files[0];

        if(file){

            await uploadFile(
                file
            );

        }

    }
);

async function uploadFile(
    file
){

    try{

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );

        if (uploadStatus) {
            uploadStatus.textContent = "Processing document...";
            uploadStatus.hidden = false;
        }

        const response =
            await fetch(
                "/upload",
                {
                    method:"POST",
                    body:formData
                }
            );

        if(
            !response.ok
        ){

            const detail = await response.json().catch(() => ({}));
            throw new Error(detail.detail || "Upload failed");

        }

        const result =
            await response.json();

        window.showToast?.("Healthcare document indexed successfully.", "success");
        if (uploadStatus) uploadStatus.hidden = true;

        console.log(
            result
        );

        localStorage.setItem(
            "activeDocument",
            result.file
        );

        await setActiveDocument(result.file);
        window.clearChatForDocument?.();

        showWorkspace();

        if(
            typeof loadDocumentViewer
            === "function"
        ){

            await loadDocumentViewer();

        }

    }
    catch(error){

        window.showToast?.(error.message, "error");

        console.error(
            error
        );

        if (uploadStatus) {
            uploadStatus.textContent = error.message;
            uploadStatus.hidden = false;
        }

    } finally {
        fileInput.value = "";
    }

}

function showWorkspace(){
    if (!uploadScreen || !workspace) {
        throw new Error("The upload or workspace view is missing from the page.");
    }
    uploadScreen.hidden = true;
    workspace.hidden = false;
}
