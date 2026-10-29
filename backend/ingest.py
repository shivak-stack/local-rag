from pathlib import Path

from langchain_core.documents import Document

from backend.document_processor import extract_document_text
from backend.healthcare_guard import is_healthcare_document
from backend.rag import chunk_document
from backend.storage import get_vectorstore


def ingest_document(pdf_path, chunk_size=None, chunk_overlap=None, document_name=None):

    pdf_name = document_name or Path(pdf_path).name

    pages = extract_document_text(
        pdf_path
    )

    if not is_healthcare_document(pages, pdf_name):
        raise ValueError("outside_healthcare_domain")

    chunks = chunk_document(pages, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    vectorstore = get_vectorstore()

    docs = []

    for chunk in chunks:

        docs.append(
            Document(
                page_content=chunk["text"],
                metadata={
                    "document": pdf_name,
                    "chunk_id": chunk["chunk_id"],
                    "page": chunk["page"],
                    "healthcare": True
                }
            )
        )

    vectorstore.add_documents(
        docs
    )

    return len(chunks)
