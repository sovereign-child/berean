#!/usr/bin/env python3
"""
Berean — the book registry.

One table that every dataset keys on. Before this, texts were addressed by their
display name ("Song of Solomon") and cross-references by their position in the
Protestant 66 — which meant a cross-reference could not point at Tobit at all,
and renaming a book would silently orphan a reader's saved highlights.

Codes are USFM where USFM has one, so Berean's data can be read by, and built
from, the rest of the open-scripture world. The Ethiopian books USFM does not
cover are marked `berean_ext` rather than quietly invented.

Writes library/books.json, and verifies that every book in every hosted corpus
resolves to a code. Run from the repo root:

    python3 scripts/build_books.py
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "library")

# code, display name, section, aliases seen in sources or citations
BOOKS = [
    ("GEN", "Genesis", "ot", []),
    ("EXO", "Exodus", "ot", []),
    ("LEV", "Leviticus", "ot", []),
    ("NUM", "Numbers", "ot", []),
    ("DEU", "Deuteronomy", "ot", []),
    ("JOS", "Joshua", "ot", []),
    ("JDG", "Judges", "ot", []),
    ("RUT", "Ruth", "ot", []),
    ("1SA", "1 Samuel", "ot", []),
    ("2SA", "2 Samuel", "ot", []),
    ("1KI", "1 Kings", "ot", []),
    ("2KI", "2 Kings", "ot", []),
    ("1CH", "1 Chronicles", "ot", []),
    ("2CH", "2 Chronicles", "ot", []),
    ("EZR", "Ezra", "ot", []),
    ("NEH", "Nehemiah", "ot", []),
    ("EST", "Esther", "ot", []),
    ("JOB", "Job", "ot", []),
    ("PSA", "Psalms", "ot", ["Psalm"]),
    ("PRO", "Proverbs", "ot", []),
    ("ECC", "Ecclesiastes", "ot", []),
    ("SNG", "Song of Solomon", "ot", ["Song of Songs", "Canticles", "SOL"]),
    ("ISA", "Isaiah", "ot", []),
    ("JER", "Jeremiah", "ot", []),
    ("LAM", "Lamentations", "ot", []),
    ("EZK", "Ezekiel", "ot", ["EZE"]),
    ("DAN", "Daniel", "ot", []),
    ("HOS", "Hosea", "ot", []),
    ("JOL", "Joel", "ot", ["JOE"]),
    ("AMO", "Amos", "ot", []),
    ("OBA", "Obadiah", "ot", []),
    ("JON", "Jonah", "ot", []),
    ("MIC", "Micah", "ot", []),
    ("NAM", "Nahum", "ot", ["NAH"]),
    ("HAB", "Habakkuk", "ot", []),
    ("ZEP", "Zephaniah", "ot", []),
    ("HAG", "Haggai", "ot", []),
    ("ZEC", "Zechariah", "ot", []),
    ("MAL", "Malachi", "ot", []),
    # disputed between traditions — see library/canons.json
    ("TOB", "Tobit", "dc", []),
    ("JDT", "Judith", "dc", []),
    ("ESG", "Esther (Greek)", "dc", ["Greek Esther", "Additions to Esther"]),
    ("WIS", "Wisdom of Solomon", "dc", ["Wisdom"]),
    ("SIR", "Sirach", "dc", ["Ecclesiasticus"]),
    ("BAR", "Baruch", "dc", []),
    ("1MA", "1 Maccabees", "dc", []),
    ("2MA", "2 Maccabees", "dc", []),
    ("1ES", "1 Esdras", "dc", []),
    ("MAN", "Prayer of Manasseh", "dc", ["PRM"]),
    ("PS2", "Psalm 151", "dc", ["PSX"]),
    ("3MA", "3 Maccabees", "dc", []),
    ("2ES", "2 Esdras", "dc", ["4 Ezra", "4ES"]),
    ("4MA", "4 Maccabees", "dc", []),
    ("DAG", "Daniel (Greek)", "dc", ["Greek Daniel", "DNG", "Additions to Daniel"]),
    ("MAT", "Matthew", "nt", []),
    ("MRK", "Mark", "nt", ["MAR"]),
    ("LUK", "Luke", "nt", []),
    ("JHN", "John", "nt", ["JOH"]),
    ("ACT", "Acts", "nt", []),
    ("ROM", "Romans", "nt", []),
    ("1CO", "1 Corinthians", "nt", []),
    ("2CO", "2 Corinthians", "nt", []),
    ("GAL", "Galatians", "nt", []),
    ("EPH", "Ephesians", "nt", []),
    ("PHP", "Philippians", "nt", ["PHI"]),
    ("COL", "Colossians", "nt", []),
    ("1TH", "1 Thessalonians", "nt", []),
    ("2TH", "2 Thessalonians", "nt", []),
    ("1TI", "1 Timothy", "nt", []),
    ("2TI", "2 Timothy", "nt", []),
    ("TIT", "Titus", "nt", []),
    ("PHM", "Philemon", "nt", []),
    ("HEB", "Hebrews", "nt", []),
    ("JAS", "James", "nt", ["JAM"]),
    ("1PE", "1 Peter", "nt", []),
    ("2PE", "2 Peter", "nt", []),
    ("1JN", "1 John", "nt", ["1JO"]),
    ("2JN", "2 John", "nt", ["2JO"]),
    ("3JN", "3 John", "nt", ["3JO"]),
    ("JUD", "Jude", "nt", []),
    ("REV", "Revelation", "nt", []),
    # outside every biblical canon but the Ethiopian one
    ("ENO", "1 Enoch", "ext", ["Enoch", "1Enoch"]),
    ("JUB", "Jubilees", "ext", ["Book of Jubilees"]),
]

# Codes USFM does not define; kept explicit so nobody mistakes them for standard.
BEREAN_EXT = {"ENO", "JUB"}

SECTIONS = {"ot": "Old Testament", "dc": "Disputed between traditions",
            "nt": "New Testament", "ext": "Outside the biblical canon"}


def build():
    by_code, by_name, seen = {}, {}, set()
    books = []
    for i, (code, name, section, aliases) in enumerate(BOOKS):
        if code in seen:
            raise SystemExit(f"duplicate code {code}")
        seen.add(code)
        entry = {"code": code, "name": name, "section": section, "order": i}
        if aliases:
            entry["aliases"] = aliases
        if code in BEREAN_EXT:
            entry["standard"] = "berean_ext"
        books.append(entry)
        by_code[code] = name
        for key in [name, code] + aliases:
            by_name[key.lower()] = code

    # every book Berean actually hosts must resolve
    unmapped = []
    corpus_dir = os.path.join(LIB, "corpus")
    for fn in sorted(os.listdir(corpus_dir)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(corpus_dir, fn), encoding="utf-8") as fh:
            d = json.load(fh)
        for b in d.get("books", []):
            if b["name"].lower() not in by_name:
                unmapped.append((fn, b["name"]))
    if unmapped:
        raise SystemExit("books with no code — add them to BOOKS:\n  "
                         + "\n  ".join(f"{f}: {n}" for f, n in unmapped))

    data = {
        "note": ("The single registry every Berean dataset keys on. Codes are USFM where "
                 "USFM defines one, so this data can be read by other open-scripture tools; "
                 "books USFM does not cover are marked standard: berean_ext. A verse address "
                 "is CODE.CHAPTER.VERSE — for example JHN.3.16 or TOB.3.16."),
        "sections": SECTIONS,
        "books": books,
        "resolve": {k: v for k, v in sorted(by_name.items())},
    }
    path = os.path.join(LIB, "books.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    counts = {s: sum(1 for b in books if b["section"] == s) for s in SECTIONS}
    print(f"wrote library/books.json — {len(books)} books "
          + ", ".join(f"{counts[s]} {s}" for s in SECTIONS)
          + f"; {len(by_name)} names resolve")


if __name__ == "__main__":
    build()
