from langchain_ollama import ChatOllama

from backend.config import OLLAMA_MODEL
from backend.healthcare_guard import is_healthcare_query


def generate_followups(answer):

    llm = ChatOllama(
        model=OLLAMA_MODEL,
        temperature=0.3
    )

    prompt = f"""
Generate exactly 3 short follow-up questions based on this answer and the healthcare document context.

Every question must be directly about healthcare, medicine, patients, conditions,
diagnosis, treatment, prevention, clinical findings, or healthcare data. Do not
ask about careers, education, programming, general knowledge, or unrelated topics.
Each question must be answerable from healthcare-related document context. Return
only questions, one per line.

Answer:

{answer}

Return one question per line.
"""

    result = llm.invoke(prompt)

    lines = []
    seen = set()

    for line in result.content.split("\n"):

        cleaned = line.strip()

        if cleaned:

            cleaned = cleaned.lstrip("-")

            cleaned = cleaned.strip()

            cleaned = cleaned.lstrip("0123456789. )-").strip()
            if cleaned and is_healthcare_query(cleaned) and cleaned.lower() not in seen:
                lines.append(cleaned)
                seen.add(cleaned.lower())

    fallbacks = [
        "What symptoms or clinical findings are described?",
        "What diagnosis or health condition is discussed?",
        "What treatment or follow-up care is mentioned?",
    ]
    for question in fallbacks:
        if len(lines) >= 3:
            break
        if question.lower() not in seen:
            lines.append(question)
            seen.add(question.lower())

    return lines[:3]
