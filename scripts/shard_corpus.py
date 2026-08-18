#!/usr/bin/env python3
"""
Berean — shard each corpus into one file per book.

The reader used to download an entire Bible (about 1.2 MB gzipped) before it
could show a single verse. The commentary layer had already solved this by
sharding per chapter; this brings the corpus in line, keyed by book code.

    library/corpus/BSB.json          the whole version — kept, and used for search,
                                     offline download, and the build scripts
    library/corpus/BSB/index.json    version metadata + verse counts per chapter,
                                     which is all the reader needs to draw its menus
    library/corpus/BSB/JHN.json      one book

The index carries the verse counts so the chapter menu can be built without
fetching a book. Run from the repo root, after any ingest:

    python3 scripts/shard_corpus.py
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import berean_lib as lib   # noqa: E402


def shard(version):
    bundle = lib.load_bundle(version)
    out_dir = os.path.join(lib.CORPUS, version)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)

    index_books = []
    for b in bundle["books"]:
        code = lib.code_for(b["name"])
        if not code:
            raise SystemExit(f"{version}: no code for {b['name']!r} — add it to build_books.py")
        lib.write_json(os.path.join(out_dir, f"{code}.json"),
                       {"code": code, "name": b["name"], "chapters": b["chapters"]})
        index_books.append({"code": code, "name": b["name"],
                            "chapters": [len(ch) for ch in b["chapters"]]})

    meta = {k: v for k, v in bundle.items() if k != "books"}
    meta["books"] = index_books
    meta["bundle"] = f"{version}.json"
    if "deuterocanonical" in meta:                    # store codes, not display names
        meta["deuterocanonical"] = [lib.code_for(n) for n in meta["deuterocanonical"]]
    lib.write_json(os.path.join(out_dir, "index.json"), meta)

    idx = os.path.getsize(os.path.join(out_dir, "index.json"))
    biggest = max((os.path.getsize(os.path.join(out_dir, f)), f)
                  for f in os.listdir(out_dir) if f != "index.json")
    print(f"  {version}: {len(index_books)} books · index {idx // 1024} KB · "
          f"largest book {biggest[1]} {biggest[0] // 1024} KB")


def main():
    print("sharding corpora by book code…")
    for v in lib.versions():
        if os.path.exists(os.path.join(lib.CORPUS, f"{v['id']}.json")):
            shard(v["id"])


if __name__ == "__main__":
    main()
