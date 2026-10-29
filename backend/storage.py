from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from backend.config import EMBED_MODEL
from backend.config import VECTOR_DB_PATH


def get_vectorstore():

    embeddings = OllamaEmbeddings(
        model=EMBED_MODEL
    )

    return Chroma(
        persist_directory=VECTOR_DB_PATH,
        embedding_function=embeddings
    )
