from backend.storage import get_vectorstore
from backend.schemas import RetrievalResult


def semantic_search(
    query,
    k=5,
    document=None
):

    vectorstore = get_vectorstore()

    search_args = {"query": query, "k": k}
    search_args["filter"] = {"$and": [{"healthcare": True}, {"document": document}]} if document else {"healthcare": True}
    results = vectorstore.similarity_search_with_score(**search_args)

    formatted = []

    for doc, score in results:

        confidence = max(
            0,
            min(
                1,
                1 / (1 + score)
            )
        )

        formatted.append(

            RetrievalResult(

                document=
                    doc.metadata.get(
                        "document",
                        "Unknown"
                    ),

                page=
                    doc.metadata.get(
                        "page",
                        0
                    ),

                chunk_id=
                    doc.metadata.get(
                        "chunk_id",
                        0
                    ),

                text=
                    doc.page_content,

                score=
                    confidence
            )
        )

    return formatted
