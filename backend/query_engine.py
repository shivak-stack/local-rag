from langchain_ollama import ChatOllama

from backend.config import OLLAMA_MODEL
from backend.hybrid import hybrid_search
from backend.keyword_search import keyword_search
from backend.retriever import semantic_search

from backend.session_store import session_store
from backend.followups import generate_followups
from backend.active_document import get_active_document
from backend.healthcare_guard import (
    HEALTHCARE_NOTICE,
    is_healthcare_file,
    is_healthcare_query,
    is_healthcare_followup,
    is_document_overview_query,
)


SYSTEM_PROMPT = """
You are a document QA assistant.

Answer ONLY using the provided context.

Write a clear, concise, well-structured response. Start with a direct answer. Use short headings when the answer has distinct parts, bullet points for lists, and bold for key terms. Keep paragraphs short. Do not repeat the question.

If the answer cannot be found:

Information not found in the document.

Do not use outside knowledge.
"""


def retrieve(
    query,
    mode="hybrid",
    k=5,
    document=None
):

    document = document or get_active_document()

    if mode == "semantic":

        return semantic_search(
            query,
            k,
            document
        )

    elif mode in ("keyword", "bm25"):

        return keyword_search(
            query,
            k,
            document
        )

    return hybrid_search(
        query,
        k,
        document
    )

def build_rag_prompt(
    question,
    mode="hybrid",
    session_id="default",
    active_document=None
):

    active_document = active_document or get_active_document()
    scoped_session_id = (
        f"{session_id}::{active_document}"
        if active_document
        else session_id
    )

    history = session_store.get_history(
        scoped_session_id
    )

    history_text = ""

    for message in history[-6:]:

        history_text += (
            f"{message['role']}: "
            f"{message['content']}\n"
        )

    results = retrieve(
        question,
        mode,
        document=active_document
    )

    context_parts = []

    for item in results:

        context_parts.append(
            item.text
        )

    context = "\n\n".join(
        context_parts
    )

    prompt = f"""
{SYSTEM_PROMPT}

Conversation History:

{history_text}

Context:

{context}

Question:

{question}
"""

    return prompt
    
def ask(
    question,
    mode="hybrid",
    temperature=0.2,
    session_id="default",
    active_document=None,
    top_k=5,
    model=None
):

    import time

    start_time = time.time()

    active_document = active_document or get_active_document()
    scoped_session_id = (
        f"{session_id}::{active_document}"
        if active_document
        else session_id
    )

    # Enforce the domain boundary before touching retrieval or Ollama.
    history_for_guard = session_store.get_history(scoped_session_id)
    contextual_healthcare = is_healthcare_followup(question, history_for_guard)
    selected_document_is_allowed = bool(active_document) and is_healthcare_file(active_document)
    if (
        (active_document and not selected_document_is_allowed)
        or (
            not is_healthcare_query(question)
            and not contextual_healthcare
            and not (selected_document_is_allowed and is_document_overview_query(question))
        )
    ):
        return {
            "answer": HEALTHCARE_NOTICE, "sources": [], "followups": [],
            "context_length": 0, "retrieved_chunks": 0,
            "average_confidence": 0, "response_time": round(time.time() - start_time, 2),
            "restricted": True,
        }

    # -------------------------
    # Conversation History
    # -------------------------

    history = session_store.get_history(
        scoped_session_id
    )

    history_text = ""

    for message in history[-6:]:

        history_text += (
            f"{message['role']}: "
            f"{message['content']}\n"
        )

    # -------------------------
    # Retrieval
    # -------------------------

    results = retrieve(
        question,
        mode,
        k=max(1, min(int(top_k), 20)),
        document=active_document
    )

    context_parts = []

    sources = []

    confidences = []

    for item in results:

        context_parts.append(
            item.text
        )

        confidences.append(
            item.score
        )

        sources.append(
            {
                "document":
                    item.document,

                "page":
                    item.page,

                "chunk_id":
                    item.chunk_id,

                "score":
                    round(
                        item.score * 100,
                        1
                    ),

                "preview":
                    (
                        item.text[:180]
                        + "..."
                    )
                    if len(item.text) > 180
                    else item.text,

                "text":
                    item.text
            }
        )

    context = "\n\n".join(
        context_parts
    )

    # -------------------------
    # Prompt
    # -------------------------

    prompt = f"""
{SYSTEM_PROMPT}

Conversation History:

{history_text}

Context:

{context}

Question:

{question}
"""

    llm = ChatOllama(
        model=model or OLLAMA_MODEL,
        temperature=temperature
    )

    response = llm.invoke(
        prompt
    )

    answer = response.content

    # -------------------------
    # Save Session Memory
    # -------------------------

    session_store.add_message(
        scoped_session_id,
        "user",
        question
    )

    session_store.add_message(
        scoped_session_id,
        "assistant",
        answer
    )

    # -------------------------
    # Follow-up Suggestions
    # -------------------------

    try:

        followups = generate_followups(
            answer
        )

    except Exception:

        followups = []

    # -------------------------
    # Analytics
    # -------------------------

    elapsed = round(
        time.time() - start_time,
        2
    )

    average_confidence = (
        round(
            (
                sum(confidences)
                / len(confidences)
            ) * 100,
            1
        )
        if confidences
        else 0
    )

    return {

        "answer":
            answer,

        "sources":
            sources,

        "followups":
            followups,

        "context_length":
            len(context),

        "retrieved_chunks":
            len(results),

        "average_confidence":
            average_confidence,

        "response_time":
            elapsed
    }
