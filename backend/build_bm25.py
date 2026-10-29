from backend.indexing import rebuild_bm25


def build_bm25():
    count = rebuild_bm25()
    print(f"Indexed {count} healthcare chunks")


if __name__ == "__main__":

    build_bm25()
