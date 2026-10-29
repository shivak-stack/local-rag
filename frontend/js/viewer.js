pdfjsLib.GlobalWorkerOptions.workerSrc =
    "/static/vendor/pdf.worker.min.js";

let pdfDocument = null;
let renderedPdfName = null;

async function loadDocumentViewer()
{
    const documentName =
        localStorage.getItem(
            "activeDocument"
        );

    if (!documentName)
    {
        return;
    }

    const documentNameLabel = document.getElementById("activeDocumentName");
    if (documentNameLabel) documentNameLabel.textContent = documentName;

    const container =
        document.getElementById(
            "pdfContainer"
        );

    if (!container)
    {
        return;
    }

    container.innerHTML =
        "<p>Loading document...</p>";

    try
    {
        if (!/\.pdf$/i.test(documentName)) {
            const chunks = await getDocumentChunks(documentName);
            container.innerHTML = "";

            if (!chunks.length) {
                container.innerHTML = "<p>No extracted text is available for this document.</p>";
                return;
            }

            for (const chunk of chunks) {
                const card = document.createElement("article");
                card.className = "viewer-chunk";
                card.id = `viewer-chunk-${chunk.page}-${chunk.chunk_id}`;
                card.innerHTML = `<div class="chunk-meta"></div><div class="chunk-text"></div>`;
                card.querySelector(".chunk-meta").textContent =
                    `Section ${chunk.page} · Chunk ${chunk.chunk_id}`;
                card.querySelector(".chunk-text").textContent = chunk.text || "";
                container.appendChild(card);
            }
            return;
        }

        const pdfUrl =
            `/pdfs/${encodeURIComponent(documentName)}`;

        pdfDocument =
            await pdfjsLib
                .getDocument(
                    pdfUrl
                )
                .promise;
        renderedPdfName = documentName;

        container.innerHTML = "";

        for (
            let pageNum = 1;
            pageNum <= pdfDocument.numPages;
            pageNum++
        )
        {
            const page =
                await pdfDocument.getPage(
                    pageNum
                );

            const viewport =
                page.getViewport(
                    {
                        scale: 1.3
                    }
                );

            const wrapper =
                document.createElement(
                    "div"
                );

            wrapper.className =
                "pdf-page-wrapper";
            wrapper.style.position = "relative";

            wrapper.id =
                `wrapper-${pageNum}`;

            const canvas =
                document.createElement(
                    "canvas"
                );

            canvas.id =
                `page-${pageNum}`;

            canvas.dataset.page =
                pageNum;

            canvas.className =
                "pdf-page";

            const ctx =
                canvas.getContext(
                    "2d"
                );

            canvas.width =
                viewport.width;

            canvas.height =
                viewport.height;

            wrapper.appendChild(
                canvas
            );

            container.appendChild(
                wrapper
            );

            await page.render(
                {
                    canvasContext: ctx,
                    viewport
                }
            ).promise;

            await renderPdfTextLayer(page, viewport, wrapper);
        }
    }
    catch (error)
    {
        renderedPdfName = null;
        console.error(
            error
        );

        container.innerHTML =
            `
            <p>
                Failed to load document
            </p>
            `;
    }
}

async function renderPdfTextLayer(page, viewport, wrapper) {
    const textContent = await page.getTextContent();
    const canvas = wrapper.querySelector("canvas");
    const displayScale = canvas?.clientWidth ? canvas.clientWidth / viewport.width : 1;
    const layer = document.createElement("div");
    layer.className = "pdf-text-layer";
    layer.dataset.page = page.pageNumber;
    const textItems = [];

    for (const item of textContent.items) {
        if (!item.str) continue;
        const transform = pdfjsLib.Util.transform(viewport.transform, item.transform);
        const fontHeight = Math.hypot(transform[2], transform[3]);
        const span = document.createElement("span");
        span.className = "pdf-text-item";
        span.textContent = item.str;
        span.style.left = `${transform[4] * displayScale}px`;
        span.style.top = `${(transform[5] - fontHeight) * displayScale}px`;
        span.style.fontSize = `${fontHeight * displayScale}px`;
        span.style.width = `${Math.max(item.width * viewport.scale * displayScale, fontHeight * displayScale * .25)}px`;
        span.style.height = `${fontHeight * 1.2 * displayScale}px`;
        const angle = Math.atan2(transform[1], transform[0]);
        if (angle) span.style.transform = `rotate(${angle}rad)`;
        textItems.push(span);
        layer.appendChild(span);
    }
    wrapper.appendChild(layer);
    layer._textItems = textItems;
}

window.addEventListener(
    "load",
    loadDocumentViewer
);

async function jumpToPage(
    pageNumber
)
{
    const page =
        document.getElementById(
            `page-${pageNumber}`
        );

    if (!page)
    {
        return;
    }

    page.scrollIntoView(
        {
            behavior: "smooth",
            block: "center"
        }
    );

    page.classList.add(
        "page-highlight"
    );

    setTimeout(
        () =>
        {
            page.classList.remove(
                "page-highlight"
            );
        },
        3000
    );
}

function normalizeCitationText(value) {
    return (value || "").toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, "");
}

function highlightPdfChunk(pageNumber, text) {
    const layer = document.querySelector(`.pdf-text-layer[data-page="${Number(pageNumber)}"]`);
    if (!layer) return;
    const spans = layer._textItems || [];
    spans.forEach(span => span.classList.remove("citation-text-highlight"));

    const target = normalizeCitationText(text);
    if (!target) return;
    let pageText = "";
    const charToSpan = [];
    for (const span of spans) {
        for (const char of normalizeCitationText(span.textContent)) {
            pageText += char;
            charToSpan.push(span);
        }
    }

    let start = pageText.indexOf(target);
    let end = start < 0 ? -1 : start + target.length;
    if (start < 0) {
        // Text extraction can differ slightly between PDF.js and the indexer;
        // fall back to a distinctive phrase from the chunk.
        const terms = (text || "").match(/[\p{L}\p{N}]{6,}/gu) || [];
        for (const term of terms.sort((a, b) => b.length - a.length)) {
            const phrase = normalizeCitationText(term);
            start = pageText.indexOf(phrase);
            if (start >= 0) { end = start + phrase.length; break; }
        }
    }
    if (start < 0) return;
    for (const span of new Set(charToSpan.slice(start, end))) span.classList.add("citation-text-highlight");
}

window.jumpToCitation = async function(source) {
    if (typeof source === "number") return jumpToPage(source);
    const current = localStorage.getItem("activeDocument");
    if (current !== source.document) {
        await setActiveDocument(source.document);
        localStorage.setItem("activeDocument", source.document);
        await loadDocumentViewer();
    }
    const chunks = await getDocumentChunks(source.document);
    const chunk = chunks.find(item => Number(item.chunk_id) === Number(source.chunk_id));
    if (!chunk) return;

    if (/\.pdf$/i.test(source.document)) {
        if (renderedPdfName !== source.document) await loadDocumentViewer();
        await jumpToPage(source.page);
        highlightPdfChunk(source.page, chunk.text || source.text || source.preview || "");
        setTimeout(() => {
            document.querySelectorAll(".pdf-text-item.citation-text-highlight")
                .forEach(span => span.classList.remove("citation-text-highlight"));
        }, 4000);
    } else {
        const card = document.getElementById(`viewer-chunk-${chunk.page}-${chunk.chunk_id}`);
        if (!card) return;
        card.classList.remove("citation-highlight");
        void card.offsetWidth;
        card.classList.add("citation-highlight");
        card.scrollIntoView({ behavior: "smooth", block: "center" });
        setTimeout(() => card.classList.remove("citation-highlight"), 4000);
    }
};

window.reloadPdfViewer =
function()
{
    loadDocumentViewer();
};
