from backend.bm25_store import load_bm25


def get_chunk(chunk_id):

    _, chunks = load_bm25(
        "backend/bm25_index.pkl"
    )

    for chunk in chunks:

        if (
            chunk["chunk_id"]
            ==
            chunk_id
        ):
            return chunk

    return None