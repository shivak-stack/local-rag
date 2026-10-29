import pickle


def get_chunk(
    document,
    chunk_id
):

    with open(
        "backend/bm25_index.pkl",
        "rb"
    ) as f:

        data = pickle.load(f)

    docs = data["documents"]

    for chunk in docs:

        if (
            chunk["document"] == document
            and
            chunk["chunk_id"] == chunk_id
        ):

            return chunk

    return None
