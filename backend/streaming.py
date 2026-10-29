from langchain_ollama import ChatOllama

from backend.config import OLLAMA_MODEL
from backend.query_engine import build_rag_prompt
from backend.healthcare_guard import (
    HEALTHCARE_NOTICE,
    is_healthcare_file,
    is_healthcare_query,
    is_healthcare_followup,
    is_document_overview_query,
)
from backend.session_store import session_store
from backend.active_document import get_active_document


def stream_answer(
    question,
    temperature,
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
    history = session_store.get_history(scoped_session_id)
    contextual_healthcare = is_healthcare_followup(question, history)
    selected_document_is_allowed = bool(active_document) and is_healthcare_file(active_document)
    if (
        (active_document and not selected_document_is_allowed)
        or (
            not is_healthcare_query(question)
            and not contextual_healthcare
            and not (selected_document_is_allowed and is_document_overview_query(question))
        )
    ):
        yield HEALTHCARE_NOTICE
        return

    prompt = build_rag_prompt(
        question=question,
        mode=mode,
        session_id=session_id,
        active_document=active_document
    )

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        temperature=temperature
    )

    for chunk in llm.stream(
        prompt
    ):

        yield chunk.content
