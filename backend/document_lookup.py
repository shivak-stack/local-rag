import pickle


def get_document_chunks(
    document_name
):

    with open(
        "backend/bm25_index.pkl",
        "rb"
    ) as f:

        data = pickle.load(f)

    docs = data["documents"]

    results = []

    for chunk in docs:

        if (
            chunk["document"]
            ==
            document_name
        ):

            results.append(
                chunk
            )

    return results
