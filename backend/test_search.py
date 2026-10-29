from backend.hybrid import hybrid_search

results = hybrid_search(
    "hospital admissions"
)

for r in results:

    print()
    print("="*50)

    if isinstance(
        r,
        dict
    ):
        print(
            r["text"][:400]
        )
    else:
        print(
            r.page_content[:400]
        )
