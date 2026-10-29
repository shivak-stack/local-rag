from pathlib import Path
from backend.healthcare_guard import is_healthcare_file


def list_documents():

    uploads = Path(
        "backend/uploads"
    )

    documents = []
    for file in uploads.iterdir():
        if file.is_file() and is_healthcare_file(file.name):
            documents.append(file.name)
    return documents
