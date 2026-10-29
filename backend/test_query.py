from backend.query_engine import ask

result = ask(
    "What is the purpose of this dashboard?"
)

print()
print("="*80)
print("ANSWER")
print("="*80)

print(
    result["answer"]
)

print()

print("="*80)
print("SOURCES")
print("="*80)

for source in result["sources"]:

    print()

    print(
        source["document"]
    )

    print(
        source["page"]
    )

    print(
        source["chunk_id"]
    )
