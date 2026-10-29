from pathlib import Path

from fastapi import FastAPI
from fastapi import UploadFile
from fastapi import File

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse

from backend.ingest import ingest_document
from backend.indexing import rebuild_bm25

from backend.models import ChatRequest
from backend.query_engine import ask

from backend.documents import list_documents
from backend.streaming import stream_answer

from fastapi import HTTPException
from backend.lookup import get_chunk

from backend.document_lookup import get_document_chunks

from backend.chunk_lookup import get_chunk

from fastapi.staticfiles import StaticFiles

from backend.active_document import (
    set_active_document,
    get_active_document
)

app = FastAPI(
    title="Local RAG"
)


app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static"
)

app.mount(
    "/pdfs",
    StaticFiles(
        directory="backend/uploads"
    ),
    name="pdfs"
)

@app.get("/")
def home():

    return FileResponse(
        "frontend/index.html"
    )


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


@app.get("/documents")
def documents():

    return {
        "documents":
            list_documents()
    }


@app.get(
    "/document/{document_name}"
)
def document_content(
    document_name: str
):

    return {

        "document":
            document_name,

        "chunks":
            get_document_chunks(
                document_name
            )

    }

from pathlib import Path

@app.delete("/documents/{filename}")
def delete_document(
    filename: str
):

    file_path = Path(
        "backend/uploads"
    ) / filename

    if file_path.exists():

        file_path.unlink()

        rebuild_bm25()

        return {
            "success": True
        }

    return {
        "success": False
    }

@app.get(
    "/chunk/{document}/{chunk_id}"
)
def chunk_lookup(
    document: str,
    chunk_id: int
):

    result = get_chunk(
        document,
        chunk_id
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Chunk not found"
        )

    return result

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    upload_dir = Path(
        "backend/uploads"
    )

    upload_dir.mkdir(
        exist_ok=True
    )

    save_path = (
        upload_dir
        / file.filename
    )

    content = await file.read()

    save_path.write_bytes(
        content
    )

    chunk_count = ingest_document(
        str(save_path)
    )

    rebuild_bm25()

    return {
        "file":
            file.filename,

        "chunks":
            chunk_count
    }

@app.post(
    "/set-active-document"
)
def set_document(
    data: dict
):

    filename = data.get(
        "filename"
    )

    set_active_document(
        filename
    )

    return {
        "success": True,
        "active_document":
            filename
    }

@app.get(
    "/active-document"
)
def active_document():
    return {
        "active_document":
            get_active_document()
    } 

@app.post("/chat")
def chat(
    request: ChatRequest
):

    return ask(
        question=request.question,
        mode=request.mode,
        temperature=request.temperature,
        session_id=request.session_id
    )


@app.post("/stream-chat")
def stream_chat(
    request: ChatRequest
):

    return StreamingResponse(

        stream_answer(
            question=request.question,
            temperature=request.temperature,
            mode=request.mode,
            session_id=request.session_id
        ),

        media_type="text/plain"
    )

@app.get(
    "/chunk/{chunk_id}"
)
def chunk(
    chunk_id:int
):

    data = get_chunk(
        chunk_id
    )

    if not data:

        return {
            "error":
            "not found"
        }

    return data