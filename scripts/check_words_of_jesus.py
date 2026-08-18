#!/usr/bin/env python3
"""
Berean — checks on the compiled "Words of Jesus".

Two things are verified: that every passage's offsets still slice real text out
of the BSB, and that a list of well-known passages came out with the voice a
reader would expect. Run after rebuilding:

    python3 scripts/build_words_of_jesus.py && python3 scripts/check_words_of_jesus.py
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BSB = json.load(open(os.path.join(ROOT, "library", "corpus", "BSB.json"), encoding="utf-8"))
WOJ = json.load(open(os.path.join(ROOT, "library", "words-of-jesus.json"), encoding="utf-8"))
BOOKS = {b["name"]: b for b in BSB["books"]}

# (book, chapter, verse, expected voice or None) — landmarks a reader would check.
EXPECT = [
    ("Matthew", 5, 3, "jesus"),        # Sermon on the Mount
    ("Matthew", 6, 9, "jesus"),        # the Lord's Prayer, mid-discourse
    ("Matthew", 3, 17, "father"),      # the baptism
    ("Matthew", 17, 5, "father"),      # the transfiguration
    ("Matthew", 4, 3, None),           # the tempter
    ("Matthew", 4, 4, "jesus"),        # Jesus answering him
    ("Matthew", 28, 19, "jesus"),      # the Great Commission
    ("Mark", 1, 15, "jesus"),
    ("Luke", 15, 2, None),             # the Pharisees grumbling
    ("Luke", 15, 11, "jesus"),         # the prodigal son
    ("Luke", 23, 34, "jesus"),         # "Father, forgive them"
    ("John", 3, 16, "jesus"),          # inside the quote opened at 3:10
    ("John", 11, 25, "jesus"),
    ("John", 12, 28, "father"),        # the voice from heaven
    ("John", 14, 6, "jesus"),
    ("John", 19, 30, "jesus"),         # "It is finished"
    ("Acts", 1, 8, "jesus"),
    ("Acts", 9, 5, "jesus"),           # curated — named inside the speech
    ("1 Corinthians", 11, 24, "jesus"),  # curated — the words at the Supper
    ("Revelation", 1, 17, "jesus"),
    ("Revelation", 3, 20, "jesus"),
    ("Revelation", 21, 5, "father"),   # the One seated on the throne
    ("Revelation", 22, 13, "jesus"),
]


def slice_part(book, part):
    (c1, v1, o1), (c2, v2, o2) = part["from"], part["to"]
    chapters = BOOKS[book]["chapters"]
    out = []
    for c in range(c1, c2 + 1):
        lo = v1 if c == c1 else 1
        hi = v2 if c == c2 else len(chapters[c - 1])
        for v in range(lo, hi + 1):
            t = chapters[c - 1][v - 1]
            a = o1 if (c, v) == (c1, v1) else 0
            b = o2 if (c, v) == (c2, v2) else len(t)
            out.append(t[a:b])
    return " ".join(x for x in out if x.strip())


def voice_at(book, c, v):
    """All voices carried at this verse — two passages legitimately overlap on a
    verse where one speaker stops and the next begins (John 12:28)."""
    found = []
    for entry in WOJ["books"]:
        if entry["book"] != book:
            continue
        for p in entry["passages"]:
            if tuple(p["from"]) <= (c, v) <= tuple(p["to"]):
                found.append(p)
    return found


def main():
    bad = 0

    # 1. every offset still slices real text
    empty = 0
    for entry in WOJ["books"]:
        for p in entry["passages"]:
            for part in p["parts"]:
                if not slice_part(entry["book"], part).strip():
                    empty += 1
    if empty:
        print(f"FAIL  {empty} passages slice to empty text")
        bad += 1
    else:
        print("ok    every passage slices real text out of the BSB")

    # 2. landmark passages carry the expected voice
    for book, c, v, want in EXPECT:
        found = voice_at(book, c, v)
        voices = [p["voice"] for p in found]
        ok = (want in voices) if want else not voices
        bad += 0 if ok else 1
        refs = ", ".join(f"{p['voice']}:{p['ref']}" for p in found) or "—"
        print(f"{'ok   ' if ok else 'FAIL '} {book} {c}:{v:<3} expected {str(want):<7} {refs}")

    print()
    print(f"{WOJ['stats']['passages']} passages of Jesus · {WOJ['stats']['verses']} verses · "
          f"{WOJ['stats']['fatherPassages']} of the Father · "
          f"{WOJ['stats']['unattributed']} quotations left unattributed")
    for entry in WOJ["books"]:
        jesus = sum(1 for p in entry["passages"] if p["voice"] == "jesus")
        print(f"  {entry['book']:<15} {jesus} passages")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
