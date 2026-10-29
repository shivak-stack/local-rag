from backend.retriever import semantic_search
from backend.keyword_search import keyword_search


def hybrid_search(
    query,
    k=5,
    document=None
):

    semantic = semantic_search(
        query,
        k,
        document
    )

    keyword = keyword_search(
        query,
        k,
        document
    )

    scores = {}

    docs = {}

    for rank, doc in enumerate(
        semantic
    ):

        cid = (doc.document, doc.chunk_id)

        scores[cid] = (
            scores.get(cid, 0)
            + 1/(60+rank)
        )

        docs[cid] = doc

    for rank, doc in enumerate(
        keyword
    ):

        cid = (doc.document, doc.chunk_id)

        scores[cid] = (
            scores.get(cid, 0)
            + 1/(60+rank)
        )

        docs[cid] = doc

    ranked = sorted(
        scores.items(),
        key=lambda x:x[1],
        reverse=True
    )

    final_results = []

    for cid, score in ranked[:k]:

        item = docs[cid]

        item.score = min(
            1,
            score * 100
        )

        final_results.append(
            item
        )

    return final_results
