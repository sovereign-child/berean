#!/usr/bin/env python3
"""
Berean wider-canon ingest — Brenton's Septuagint in English (1851).

The Greek Old Testament, readable. Berean's threads already argue that the New
Testament usually quotes the Greek and that its wording sometimes differs from
the Hebrew our Old Testaments translate; hosting Brenton turns that argument
into something a reader can simply open and compare.

Sir Lancelot Brenton's translation was published in 1851 and is public domain;
eBible.org publishes it verse-per-line.

IT DOES NOT SHARE OUR CHAPTER NUMBERS, and that is not a defect — it is the
point. Brenton follows the Greek:

    Psalm 23 in a Hebrew-numbered Bible is Psalm 22 here
    Jeremiah 25:15, the cup of wrath, is Jeremiah 32:15 here

So this records `versification: "septuagint"`, and scripts/build_versification.py
derives the chapter map from the texts themselves rather than asserting one. The
reader warns wherever the two schemes disagree instead of quietly showing two
different passages side by side and calling them the same verse.

Reproducible, stdlib only. Run from the repo root:
    python3 scripts/ingest_brenton.py && python3 scripts/shard_corpus.py

Output: library/corpus/LXX.json  +  an entry in library/manifest.json.
"""

import io
import json
import os
import re
import sys
import urllib.request
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import berean_lib as lib   # noqa: E402

URL = "https://ebible.org/Scriptures/eng-Brenton_vpl.zip"
MEMBER = "eng-Brenton_vpl.txt"
VPL = re.compile(r"^(\S+)\s+(\d+):(\d+)\s+(.*)$")
PROTESTANT_OT_NT = {b["code"] for b in lib.registry()["books"] if b["section"] in ("ot", "nt")}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "berean-ingest/0.1"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main():
    print(f"fetching Brenton's Septuagint (PD, 1851) from {URL} …")
    with zipfile.ZipFile(io.BytesIO(fetch(URL))) as z:
        text = z.read(MEMBER).decode("utf-8-sig")

    order, nested = [], {}
    for line in text.splitlines():
        m = VPL.match(line)
        if not m:
            continue
        src, c, v, verse = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4).strip()
        code = lib.code_for(src)
        if not code:
            raise SystemExit(f"Brenton: no code for {src!r} — add it to build_books.py")
        if code not in nested:
            order.append(code)
            nested[code] = {}
        nested[code].setdefault(c, {})[v] = verse

    books = []
    for code in order:
        chapters_map = nested[code]
        chapters = []
        for c in range(1, max(chapters_map) + 1):
            verses = chapters_map.get(c, {})
            chapters.append([verses.get(v, "") for v in range(1, max(verses) + 1)] if verses else [])
        books.append({"name": lib.name_for(code), "chapters": chapters})

    extra = [b["name"] for b in books if lib.code_for(b["name"]) not in PROTESTANT_OT_NT]
    data = {
        "version": "LXX",
        "name": "Brenton's Septuagint (1851)",
        "language": "en",
        "license": "Public Domain",
        "source": URL,
        "attribution": ("The Septuagint version of the Old Testament, translated by Sir Lancelot "
                        "C. L. Brenton (London, 1851) — public domain, via eBible.org."),
        "tradition": "Greek Old Testament (Septuagint)",
        "versification": "septuagint",
        "canon_status": ("The Greek Old Testament: the translation Jewish scholars made in the "
                         "third to second centuries BC, and the one the New Testament writers "
                         "usually quote. It carries the deuterocanonical books, and it has no "
                         "separate Hebrew Esther or Daniel — only the Greek forms. Its chapter "
                         "and verse numbers follow the Greek, not the Hebrew; see "
                         "library/versification.json. About 1% of verse slots are empty — "
                         "places where the Greek has no counterpart to a verse the Hebrew "
                         "has, most of them in Jeremiah, which is markedly shorter in Greek. "
                         "Those slots are kept rather than renumbered away, and the reader "
                         "says so where it meets one."),
        "canonical": True,
        "deuterocanonical": [lib.code_for(n) for n in extra],
        "books": books,
    }
    path = os.path.join(lib.CORPUS, "LXX.json")
    lib.write_json(path, data)
    nv = sum(len(ch) for b in books for ch in b["chapters"])
    print(f"wrote library/corpus/LXX.json: {len(books)} books, {nv} verses, "
          f"{os.path.getsize(path) // 1024} KB")
    print(f"  beyond the Protestant canon ({len(extra)}): {', '.join(extra)}")

    mpath = os.path.join(lib.LIB, "manifest.json")
    with open(mpath, encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest["versions"] = [x for x in manifest["versions"] if x.get("id") != "LXX"]
    entry = {k: data[k] for k in ("version", "name", "language", "license", "source",
                                  "attribution", "tradition", "versification", "canon_status",
                                  "canonical")}
    entry["id"] = "LXX"
    entry["deuterocanonical"] = data["deuterocanonical"]
    # keep it with the Bibles, ahead of the texts outside the canon
    at = len([x for x in manifest["versions"] if x.get("canonical", True)])
    manifest["versions"].insert(at, entry)
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("updated library/manifest.json — run scripts/shard_corpus.py, "
          "then scripts/build_versification.py")


if __name__ == "__main__":
    main()
