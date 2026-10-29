from pathlib import Path
from rank_bm25 import BM25Okapi

from backend.bm25_store import save_bm25
from backend.document_processor import SUPPORTED_EXTENSIONS
from backend.healthcare_guard import is_healthcare_file
from backend.storage import get_vectorstore


def rebuild_bm25():

    all_chunks = []
    vectorstore = get_vectorstore()

    # Migrate legacy vectors only when their source PDF passes the same gate.
    for source_file in Path("backend/uploads").iterdir():
        if not source_file.is_file() or source_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        indexed_pdf = vectorstore.get(where={"document": source_file.name}, include=["metadatas"])
        if not indexed_pdf.get("ids"):
            continue
        allowed = is_healthcare_file(source_file.name)
        if not allowed:
            vectorstore.delete(where={"document": source_file.name})
            continue
        updated_metadata = []
        for metadata in indexed_pdf.get("metadatas", []):
            updated_metadata.append({**metadata, "healthcare": True})
        vectorstore._collection.update(ids=indexed_pdf["ids"], metadatas=updated_metadata)

    indexed = vectorstore.get(where={"healthcare": True}, include=["documents", "metadatas"])
    for text, metadata in zip(indexed.get("documents", []), indexed.get("metadatas", [])):
        all_chunks.append({
            "text": text,
            "document": metadata.get("document", "Unknown"),
            "page": metadata.get("page", 0),
            "chunk_id": metadata.get("chunk_id", 0),
        })

    tokenized = [

        chunk["text"].lower().split()

        for chunk in all_chunks
    ]

    bm25 = BM25Okapi(tokenized) if tokenized else None

    save_bm25(
        bm25,
        all_chunks,
        "backend/bm25_index.pkl"
    )

    return len(all_chunks)
