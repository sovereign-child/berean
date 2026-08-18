#!/usr/bin/env python3
"""
Berean — re-key the cross-references to book codes and shard them by book.

The openbible.info data addresses books by their position in the Protestant 66,
which has two costs: a cross-reference cannot point at Tobit or 1 Enoch even in
principle, and the reader downloaded all 3.7 MB of it to look up one verse.

    library/crossrefs.json        the source-shaped file, kept as the archive
    library/crossrefs/index.json  attribution + which books have references
    library/crossrefs/JHN.json    { "JHN.3.16": ["1JN.4.9", …] }

Run from the repo root, after ingest_crossrefs.py:
    python3 scripts/shard_crossrefs.py
"""

import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import berean_lib as lib   # noqa: E402

# The source's book order: the Protestant 66, by index.
CANON66 = [b["code"] for b in lib.registry()["books"] if b["section"] in ("ot", "nt")]
OUT = os.path.join(lib.LIB, "crossrefs")


def recode(token):
    """'42.1.1-3' → 'MRK.1.1-3'  (book index, chapter, verse[, end verse])"""
    main, _, end = token.partition("-")
    parts = main.split(".")
    if len(parts) != 3:
        return None
    bi, ch, v = parts
    if not (bi.isdigit() and ch.isdigit() and v.isdigit()):
        return None
    i = int(bi)
    if i >= len(CANON66):
        return None
    return f"{CANON66[i]}.{int(ch)}.{int(v)}" + (f"-{end}" if end else "")


def main():
    with open(os.path.join(lib.LIB, "crossrefs.json"), encoding="utf-8") as fh:
        data = json.load(fh)

    by_book, links, dropped = {}, 0, 0
    for key, targets in data["refs"].items():
        src = recode(key)
        if not src:
            dropped += 1
            continue
        out = [t for t in (recode(x) for x in targets) if t]
        dropped += len(targets) - len(out)
        if not out:
            continue
        by_book.setdefault(src.split(".")[0], {})[src] = out
        links += len(out)

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for code, refs in by_book.items():
        lib.write_json(os.path.join(OUT, f"{code}.json"), refs)
    lib.write_json(os.path.join(OUT, "index.json"), {
        "attribution": data["attribution"], "source": data["source"], "license": data["license"],
        "note": ("Keyed CODE.CHAPTER.VERSE, one file per source book. The underlying data "
                 "covers the Protestant 66; books outside it have no cross-references yet, "
                 "and the reader says so rather than showing an empty list."),
        "books": sorted(by_book, key=lib.order_of),
        "verses": sum(len(v) for v in by_book.values()),
        "links": links,
    })
    sizes = sorted(((os.path.getsize(os.path.join(OUT, f)), f) for f in os.listdir(OUT)),
                   reverse=True)[:1]
    print(f"wrote library/crossrefs/ — {len(by_book)} books, "
          f"{sum(len(v) for v in by_book.values())} verses, {links} links"
          + (f", {dropped} unresolvable dropped" if dropped else "")
          + f" · largest {sizes[0][1]} {sizes[0][0] // 1024} KB")


if __name__ == "__main__":
    main()
