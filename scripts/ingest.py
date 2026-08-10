#!/usr/bin/env python3
"""
Berean corpus ingest — Phase 1.

Fetches OPEN (public-domain / CC0) Bible texts from their sources and normalizes
them into Berean's corpus schema under ../library/. Only open texts are ingested
here; copyrighted translations are accessed via licensed APIs at runtime, never
hosted (see docs/03-texts-and-licensing.md).

Reproducible: uses only the Python standard library. Run from the repo root:
    python3 scripts/ingest.py

Normalized per-version file (library/corpus/<ID>.json):
    {"version","name","language","license","source","attribution",
     "books":[{"name":"Genesis","chapters":[["v1 text","v2 text",...], ...]}, ...]}
"""

import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(ROOT, "library", "corpus")

# Canonical Protestant 66-book order + full names. (The wider canon —
# deuterocanon/apocrypha/pseudepigrapha — arrives in Phase 3, labeled by tradition.)
BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges",
    "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles",
    "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations",
    "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
    "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew",
    "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians",
    "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians",
    "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
    "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation",
]
BOOK_INDEX = {name: i for i, name in enumerate(BOOKS)}

# Map source book-name spellings to our canonical names.
ALIASES = {
    "Psalm": "Psalms",
    "Song of Songs": "Song of Solomon",
    "Canticles": "Song of Solomon",
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "berean-ingest/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def canonical(name: str) -> str:
    name = name.strip()
    return ALIASES.get(name, name)


def nested_to_books(nested: dict) -> list:
    """nested[book][chapter][verse] = text  ->  ordered books/chapters arrays."""
    books = []
    for bname in BOOKS:
        if bname not in nested:
            continue
        chapters_map = nested[bname]
        max_ch = max(chapters_map)
        chapters = []
        for c in range(1, max_ch + 1):
            verses_map = chapters_map.get(c, {})
            if verses_map:
                max_v = max(verses_map)
                chapters.append([verses_map.get(v, "") for v in range(1, max_v + 1)])
            else:
                chapters.append([])
        books.append({"name": bname, "chapters": chapters})
    return books


def ingest_bsb() -> dict:
    """Berean Standard Bible — CC0, tab-separated 'Book C:V<TAB>text', one verse/row."""
    text = fetch("https://bereanbible.com/bsb.txt").decode("utf-8-sig")
    nested: dict = {}
    unmapped = set()
    for line in text.splitlines():
        if "\t" not in line:
            continue
        ref, verse_text = line.split("\t", 1)
        ref, verse_text = ref.strip(), verse_text.strip()
        if ":" not in ref or " " not in ref:
            continue  # header rows ("Verse")
        book_part, cv = ref.rsplit(" ", 1)
        if ":" not in cv:
            continue
        cs, vs = cv.split(":", 1)
        if not (cs.isdigit() and vs.isdigit()):
            continue
        bname = canonical(book_part)
        if bname not in BOOK_INDEX:
            unmapped.add(book_part)
            continue
        nested.setdefault(bname, {}).setdefault(int(cs), {})[int(vs)] = verse_text
    if unmapped:
        raise SystemExit(f"BSB: unmapped book names {sorted(unmapped)} — add to ALIASES")
    return {
        "version": "BSB", "name": "Berean Standard Bible", "language": "en",
        "license": "CC0-1.0",
        "source": "https://bereanbible.com/bsb.txt",
        "attribution": "Berean Standard Bible (BSB), dedicated to the public domain (CC0) — BereanBible.com",
        "tradition": "Protestant (66)",
        "books": nested_to_books(nested),
    }


def ingest_kjv() -> dict:
    """King James Version — public domain. Source array is in canonical order;
    map by index to our canonical names. Strip the source's {italic} markers."""
    data = json.loads(fetch(
        "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_kjv.json"
    ).decode("utf-8-sig"))
    if len(data) != 66:
        raise SystemExit(f"KJV: expected 66 books, got {len(data)}")
    books = []
    for i, book_obj in enumerate(data):
        chapters = [
            [v.replace("{", "").replace("}", "").strip() for v in chapter]
            for chapter in book_obj["chapters"]
        ]
        books.append({"name": BOOKS[i], "chapters": chapters})
    return {
        "version": "KJV", "name": "King James Version", "language": "en",
        "license": "Public Domain",
        "source": "https://raw.githubusercontent.com/thiagobodruk/bible (en_kjv.json)",
        "attribution": "King James Version (1769), public domain",
        "tradition": "Protestant (66)",
        "books": books,
    }


def stats(v: dict) -> str:
    nb = len(v["books"])
    nv = sum(len(ch) for b in v["books"] for ch in b["chapters"])
    return f"{v['version']}: {nb} books, {nv} verses"


def main():
    os.makedirs(CORPUS_DIR, exist_ok=True)
    versions = [ingest_bsb(), ingest_kjv()]
    for v in versions:
        with open(os.path.join(CORPUS_DIR, f"{v['version']}.json"), "w", encoding="utf-8") as f:
            json.dump(v, f, ensure_ascii=False, separators=(",", ":"))
        print(stats(v))
    manifest = {
        "note": ("Only public-domain / openly-licensed texts are hosted here; "
                 "copyrighted translations are accessed via licensed APIs at runtime, "
                 "never hosted. See docs/03-texts-and-licensing.md."),
        "versions": [
            {k: v[k] for k in ("version", "name", "language", "license", "source",
                               "attribution", "tradition")}
            for v in versions
        ],
    }
    # manifest lists versions by their file id
    for m, v in zip(manifest["versions"], versions):
        m["id"] = v["version"]
    with open(os.path.join(ROOT, "library", "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"wrote manifest with {len(versions)} versions")


if __name__ == "__main__":
    main()
