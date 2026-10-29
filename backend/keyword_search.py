from backend.bm25_store import load_bm25
from backend.schemas import RetrievalResult


def keyword_search(
    query,
    k=5,
    document=None
):

    bm25, docs = load_bm25(
        "backend/bm25_index.pkl"
    )

    if not docs:
        return []

    if bm25 is None:
        return []

    scores = bm25.get_scores(
        query.lower().split()
    )

    scored_docs = [
        (score, doc)
        for score, doc in zip(scores, docs)
        if document is None or doc.get("document") == document
    ]

    ranked = sorted(
        scored_docs,
        reverse=True,
        key=lambda x: x[0]
    )

    max_score = max(scores) if len(scores) else 1

    results = []

    for score, doc in ranked[:k]:

        confidence = (
            score / max_score
            if max_score > 0
            else 0
        )

        results.append(

            RetrievalResult(

                document=
                    doc["document"],

                page=
                    doc["page"],

                chunk_id=
                    doc["chunk_id"],

                text=
                    doc["text"],

                score=
                    confidence
            )
        )

    return results
