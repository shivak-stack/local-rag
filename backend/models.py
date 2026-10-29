from pydantic import BaseModel


class ChatRequest(BaseModel):

    question: str

    mode: str = "hybrid"

    temperature: float = 0.2

    session_id: str = "default"

    active_document: str | None = None
    top_k: int = 5
    model: str | None = None
    chunk_size: int = 1000
    chunk_overlap: int = 200
