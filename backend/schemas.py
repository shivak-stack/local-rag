from dataclasses import dataclass


@dataclass
class RetrievalResult:

    document: str

    page: int

    chunk_id: int

    text: str

    score: float
