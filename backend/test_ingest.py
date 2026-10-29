from pathlib import Path

from backend.ingest import ingest_document


uploads_dir = Path("backend/uploads")

pdf_files = list(
    uploads_dir.glob("*.pdf")
)

if not pdf_files:
    raise FileNotFoundError(
        "No PDF files found in backend/uploads"
    )

pdf_path = pdf_files[0]

print(f"Indexing: {pdf_path.name}")

count = ingest_document(
    str(pdf_path)
)

print(f"Indexed {count} chunks")
