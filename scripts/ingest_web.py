#!/usr/bin/env python3
"""
Berean wider-canon ingest — the World English Bible with the Deuterocanon.

Phase 3. This is the text that answers "what does a Catholic Bible have that mine
doesn't" with the actual books rather than a table: the WEB is a modern-English
translation released into the PUBLIC DOMAIN, and eBible.org publishes an edition
carrying all 81 books — the Protestant 66, the Catholic deuterocanon, and the
books read in the Orthodox churches.

Nothing here decides whose canon is right. The books are ingested in their
traditional order (the deuterocanon between Malachi and Matthew) and every book
outside the Protestant 66 is recorded in `deuterocanonical`, so the reader can
label what a given tradition includes. Per-tradition status lives in
library/canons.json.

Reproducible, stdlib only. Run from the repo root:
    python3 scripts/ingest_web.py

Output: library/corpus/WEB.json  +  an entry in library/manifest.json.
"""

import io
import json
import os
import re
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "library")
URL = "https://ebible.org/Scriptures/eng-web_vpl.zip"
MEMBER = "eng-web_vpl.txt"
VPL = re.compile(r"^(\S+)\s+(\d+):(\d+)\s+(.*)$")

# eBible book codes → the names Berean displays. Order is the file's own, which is
# the traditional one: Old Testament, deuterocanon, New Testament.
NAMES = {
    "GEN": "Genesis", "EXO": "Exodus", "LEV": "Leviticus", "NUM": "Numbers",
    "DEU": "Deuteronomy", "JOS": "Joshua", "JDG": "Judges", "RUT": "Ruth",
    "1SA": "1 Samuel", "2SA": "2 Samuel", "1KI": "1 Kings", "2KI": "2 Kings",
    "1CH": "1 Chronicles", "2CH": "2 Chronicles", "EZR": "Ezra", "NEH": "Nehemiah",
    "EST": "Esther", "JOB": "Job", "PSA": "Psalms", "PRO": "Proverbs",
    "ECC": "Ecclesiastes", "SOL": "Song of Solomon", "ISA": "Isaiah",
    "JER": "Jeremiah", "LAM": "Lamentations", "EZE": "Ezekiel", "DAN": "Daniel",
    "HOS": "Hosea", "JOE": "Joel", "AMO": "Amos", "OBA": "Obadiah", "JON": "Jonah",
    "MIC": "Micah", "NAH": "Nahum", "HAB": "Habakkuk", "ZEP": "Zephaniah",
    "HAG": "Haggai", "ZEC": "Zechariah", "MAL": "Malachi",
    # the books at issue
    "TOB": "Tobit", "JDT": "Judith", "ESG": "Esther (Greek)",
    "WIS": "Wisdom of Solomon", "SIR": "Sirach", "BAR": "Baruch",
    "1MA": "1 Maccabees", "2MA": "2 Maccabees", "1ES": "1 Esdras",
    "PRM": "Prayer of Manasseh", "PSX": "Psalm 151", "3MA": "3 Maccabees",
    "4ES": "2 Esdras", "4MA": "4 Maccabees", "DNG": "Daniel (Greek)",
    # New Testament
    "MAT": "Matthew", "MAR": "Mark", "LUK": "Luke", "JOH": "John", "ACT": "Acts",
    "ROM": "Romans", "1CO": "1 Corinthians", "2CO": "2 Corinthians",
    "GAL": "Galatians", "EPH": "Ephesians", "PHI": "Philippians",
    "COL": "Colossians", "1TH": "1 Thessalonians", "2TH": "2 Thessalonians",
    "1TI": "1 Timothy", "2TI": "2 Timothy", "TIT": "Titus", "PHM": "Philemon",
    "HEB": "Hebrews", "JAM": "James", "1PE": "1 Peter", "2PE": "2 Peter",
    "1JO": "1 John", "2JO": "2 John", "3JO": "3 John", "JUD": "Jude",
    "REV": "Revelation",
}

# The Protestant 66 — everything else this file carries is disputed between
# traditions, and is listed as such rather than silently mixed in.
PROTESTANT = {
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges",
    "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles",
    "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations",
    "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
    "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew",
    "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians",
    "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians",
    "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
    "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude",
    "Revelation",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "berean-ingest/0.1"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def parse(text):
    """The verse-per-line edition: 'GEN 1:1 In the beginning…', in book order."""
    order, nested = [], {}
    for line in text.splitlines():
        m = VPL.match(line)
        if not m:
            continue
        code, c, v, verse = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4).strip()
        if code not in NAMES:
            raise SystemExit(f"WEB: unknown book code {code!r} — add it to NAMES")
        if code not in nested:
            order.append(code)
            nested[code] = {}
        nested[code].setdefault(c, {})[v] = verse
    return order, nested


def to_books(order, nested):
    books = []
    for code in order:
        chapters_map = nested[code]
        chapters = []
        for c in range(1, max(chapters_map) + 1):
            verses = chapters_map.get(c, {})
            chapters.append([verses.get(v, "") for v in range(1, max(verses) + 1)] if verses else [])
        books.append({"name": NAMES[code], "chapters": chapters})
    return books


def merge_manifest(entry):
    """Add or replace one version, leaving every other key — other versions,
    compilations — exactly as it was."""
    path = os.path.join(LIB, "manifest.json")
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    versions = [v for v in manifest.get("versions", []) if v.get("id") != entry["id"]]
    # keep the Bible versions ahead of the wider-canon texts
    insert = len([v for v in versions if v.get("canonical", True)])
    versions.insert(insert, entry)
    manifest["versions"] = versions
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def main():
    print(f"fetching the World English Bible with Deuterocanon (PD) from {URL} …")
    blob = fetch(URL)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        text = z.read(MEMBER).decode("utf-8-sig")
    order, nested = parse(text)
    books = to_books(order, nested)
    if len(books) != 81:
        raise SystemExit(f"WEB: expected 81 books, got {len(books)}")

    extra = [b["name"] for b in books if b["name"] not in PROTESTANT]
    data = {
        "version": "WEB",
        "name": "World English Bible (with Deuterocanon)",
        "language": "en",
        "license": "Public Domain",
        "source": URL,
        "attribution": ("World English Bible (WEB), public domain — eBible.org. "
                        "“World English Bible” is a trademark of eBible.org."),
        "tradition": "Catholic / Orthodox (81 books, incl. the deuterocanon)",
        "canon_status": ("Carries the Protestant 66 plus the books disputed between "
                         "traditions: the Catholic deuterocanon (73-book canon) and the "
                         "books read in the Orthodox churches. See library/canons.json "
                         "for which tradition receives which book."),
        "canonical": True,
        "deuterocanonical": extra,
        "books": books,
    }
    path = os.path.join(LIB, "corpus", "WEB.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    nv = sum(len(ch) for b in books for ch in b["chapters"])
    print(f"wrote {os.path.relpath(path, ROOT)}: {len(books)} books, {nv} verses, "
          f"{os.path.getsize(path) // 1024} KB")
    print(f"  beyond the Protestant 66 ({len(extra)}): {', '.join(extra)}")

    merge_manifest({k: data[k] for k in ("version", "name", "language", "license", "source",
                                         "attribution", "tradition", "canon_status", "canonical")}
                   | {"id": "WEB", "deuterocanonical": extra})
    print("updated library/manifest.json")


if __name__ == "__main__":
    main()
