const sendBtn =
document.getElementById(
    "sendBtn"
);

const inputBox =
document.getElementById(
    "questionInput"
);

const chatMessages =
document.getElementById(
    "chatMessages"
);

const followupsContainer =
document.getElementById(
    "followups"
);

sendBtn.addEventListener(
    "click",
    sendQuestion
);

inputBox.addEventListener(
    "keypress",
    (e)=>{

        if(
            e.key==="Enter"
        ){
            sendQuestion();
        }

    }
);

async function sendQuestion(){

    const question =
        inputBox.value.trim();

    if(!question){
        return;
    }

    sendBtn.disabled = true;

    addMessage(
        question,
        "user"
    );

    inputBox.value="";

    const loading =
        addMessage(
            "Thinking...",
            "assistant"
        );

    try{

        const result =
            await askQuestion(
                question
            );

        loading.remove();

        renderAssistantResponse(
            result
        );

    }
    catch(err){

        loading.innerText =
            `Query failed: ${err.message}`;
        loading.dataset.exportText = loading.innerText;

        console.error(
            err
        );

    }
    finally {
        sendBtn.disabled = false;
    }

}

function addMessage(
    text,
    type
){

    const div =
        document.createElement(
            "div"
        );

    div.className =
        `message ${type}`;

    div.dataset.timestamp = new Date().toISOString();
    div.dataset.exportText = text;

    div.innerText =
        text;

    chatMessages.appendChild(
        div
    );

    chatMessages.scrollTop =
        chatMessages.scrollHeight;

    return div;

}

function renderAssistantResponse(
    result
){

    const wrapper =
        document.createElement(
            "div"
        );

    wrapper.className =
        "message assistant";
    wrapper.dataset.timestamp = new Date().toISOString();
    wrapper.dataset.exportText = result.answer || "";

    const answer = document.createElement("div");
    answer.className = "answer";
    answer.innerHTML = formatAnswer(result.answer || "");
    wrapper.appendChild(answer);

    if(
        result.sources &&
        result.sources.length
    ){

        const sourceContainer =
            document.createElement(
                "div"
            );

        sourceContainer.className =
            "source-container";

        result.sources.forEach(
            source => {

                const chip =
                    document.createElement(
                        "button"
                    );

                chip.className =
                    "citation-btn";

                chip.innerText =
                    `${source.document} · Page ${source.page} · Chunk ${source.chunk_id}`;

                chip.title =
                    source.preview ||
                    "";

                chip.onclick =
                    () => {

                        jumpToCitation(source);

                    };

                sourceContainer.appendChild(
                    chip
                );

            }
        );

        wrapper.appendChild(
            sourceContainer
        );

    }

    chatMessages.appendChild(
        wrapper
    );

    chatMessages.scrollTop =
        chatMessages.scrollHeight;

    updateAnalytics(
        result
    );

    renderFollowups(
        result.followups || []
    );

}

function renderFollowups(
    followups
){

    if(
        !followupsContainer
    ){
        return;
    }

    followupsContainer.replaceChildren();

    if (!followups.length) {
        followupsContainer.hidden = true;
        return;
    }

    followupsContainer.hidden = false;
    const header = document.createElement("div");
    header.className = "followups-header";
    const label = document.createElement("span");
    label.innerText = "Suggested follow-ups";
    header.appendChild(label);

    const dismissAll = document.createElement("button");
    dismissAll.type = "button";
    dismissAll.className = "dismiss-followups";
    dismissAll.innerText = "Dismiss all";
    dismissAll.onclick = () => renderFollowups([]);
    header.appendChild(dismissAll);
    followupsContainer.appendChild(header);

    const list = document.createElement("div");
    list.className = "followups-list";
    followups.forEach(question => {
        const item = document.createElement("div");
        item.className = "followup-item";
        const askButton = document.createElement("button");
        askButton.type = "button";
        askButton.className = "followup-chip";
        askButton.innerText = question;
        askButton.onclick = () => {
            inputBox.value = question;
            renderFollowups([]);
            sendQuestion();
        };

        const dismissButton = document.createElement("button");
        dismissButton.type = "button";
        dismissButton.className = "dismiss-followup";
        dismissButton.setAttribute("aria-label", "Dismiss suggestion");
        dismissButton.title = "Dismiss suggestion";
        dismissButton.innerText = "x";
        dismissButton.onclick = () => {
            const remaining = Array.from(list.querySelectorAll(".followup-chip"))
                .filter(button => button !== askButton)
                .map(button => button.innerText);
            renderFollowups(remaining);
        };
        item.append(askButton, dismissButton);
        list.appendChild(item);
    });
    followupsContainer.appendChild(list);

}

window.clearChatForDocument = function() {
    chatMessages.replaceChildren();
    renderFollowups([]);
    document.getElementById("contextLength").innerText = "Context: 0";
    document.getElementById("retrievedChunks").innerText = "Chunks: 0";
    document.getElementById("responseTime").innerText = "Time: 0s";
};

function formatAnswer(markdown) {
    const escapeHtml = value => value.replace(/[&<>"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);

    const inline = value => escapeHtml(value)
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/__(.+?)__/g, "<strong>$1</strong>")
        .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
        .replace(/(^|[^_])_([^_]+)_/g, "$1<em>$2</em>");

    const output = [];
    const lines = markdown.replace(/\r/g, "").split("\n");
    let paragraph = [];
    let listType = null;

    const flushParagraph = () => {
        if (paragraph.length) {
            output.push(`<p>${inline(paragraph.join(" "))}</p>`);
            paragraph = [];
        }
    };
    const closeList = () => {
        if (listType) {
            output.push(`</${listType}>`);
            listType = null;
        }
    };

    for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line) {
            flushParagraph();
            closeList();
            continue;
        }

        const heading = line.match(/^(#{1,3})\s+(.+)$/);
        const bullet = line.match(/^[-*+]\s+(.+)$/);
        const numbered = line.match(/^\d+[.)]\s+(.+)$/);
        if (heading) {
            flushParagraph();
            closeList();
            const level = heading[1].length;
            output.push(`<h${level}>${inline(heading[2])}</h${level}>`);
        } else if (bullet || numbered) {
            flushParagraph();
            const nextType = bullet ? "ul" : "ol";
            if (listType !== nextType) {
                closeList();
                output.push(`<${nextType}>`);
                listType = nextType;
            }
            output.push(`<li>${inline((bullet || numbered)[1])}</li>`);
        } else {
            closeList();
            paragraph.push(line);
        }
    }

    flushParagraph();
    closeList();
    return output.join("");
}

function updateAnalytics(
    result
){

    document.getElementById(
        "contextLength"
    ).innerText =
        `Context: ${result.context_length}`;

    document.getElementById(
        "retrievedChunks"
    ).innerText =
        `Chunks: ${result.retrieved_chunks}`;

    document.getElementById(
        "responseTime"
    ).innerText =
        `Time: ${result.response_time}s`;

}
