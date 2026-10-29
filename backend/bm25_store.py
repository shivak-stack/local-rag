import joblib


def save_bm25(
    bm25,
    documents,
    path
):

    joblib.dump(
        {
            "bm25": bm25,
            "documents": documents
        },
        path
    )


def load_bm25(path):

    data = joblib.load(path)

    return (
        data["bm25"],
        data["documents"]
    )
