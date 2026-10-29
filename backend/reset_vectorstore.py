import shutil
from pathlib import Path

vectorstore = Path(
    "backend/vectorstore"
)

if vectorstore.exists():

    shutil.rmtree(vectorstore)

    print(
        "Vectorstore cleared."
    )

else:

    print(
        "Vectorstore does not exist."
    )
