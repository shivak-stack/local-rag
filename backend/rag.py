from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import CHUNK_SIZE
from backend.config import CHUNK_OVERLAP


def chunk_document(pages, chunk_size=None, chunk_overlap=None):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or CHUNK_SIZE,
        chunk_overlap=chunk_overlap if chunk_overlap is not None else CHUNK_OVERLAP
    )

    chunks = []

    chunk_id = 0

    for page in pages:

        split_chunks = splitter.split_text(
            page["text"]
        )

        for chunk in split_chunks:

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "page": page["page"],
                    "text": chunk
                }
            )

            chunk_id += 1

    return chunks
