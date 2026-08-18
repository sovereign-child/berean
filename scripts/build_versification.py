#!/usr/bin/env python3
"""
Berean — where two Bibles disagree about the numbers.

Brenton's Septuagint follows the Greek chapter numbering, which is not the one a
Hebrew-based Old Testament uses. Psalm 23 is Psalm 22 there; Jeremiah's oracles
are in a different order entirely, so its chapter 25 and ours are not the same
chapter. Put the two side by side without saying so and the reader is shown two
different passages presented as the same verse.

Rather than assert a mapping from a reference book, this derives one from the
texts: each chapter of the Greek version is matched against the chapter of the
Hebrew-based version it most shares distinctive wording with. Both are English
translations of the same underlying material, so real correspondences stand out
sharply from coincidence — and the result can be checked, which an asserted
table cannot be. scripts/check_versification.py verifies it against the mapping
scholarship already knows.

Output: library/versification.json — only the books where the numbering actually
differs, so the reader can say so exactly where it matters.

Run from the repo root, after ingesting:
    python3 scripts/build_versification.py
"""

import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import berean_lib as lib   # noqa: E402

OUT = os.path.join(lib.LIB, "versification.json")
GREEK, HEBREW = "LXX", "BSB"
N = 4
MIN_SCORE = 3.0          # a differing number, within the same book
MIN_CROSS = 6.0          # a different BOOK is a structural claim, and needs more
WORD = re.compile(r"[a-z]+")


def grams(text):
    ws = WORD.findall(text.lower())
    return {tuple(ws[i:i + N]) for i in range(len(ws) - N + 1)}


def chapter_grams(chapters):
    return [grams(" ".join(ch)) for ch in chapters]


OT_ONLY = {b["code"] for b in lib.registry()["books"] if b["section"] == "ot"}


def hebrew_index(hebrew):
    """One index over the whole Hebrew-based Old Testament, because the Greek does
    not always keep the same books: its Esdras B is our Ezra AND Nehemiah, so the
    chapter a Greek chapter answers to is not always in the book of the same name."""
    postings = collections.Counter()
    index = collections.defaultdict(list)
    for code, book in hebrew.items():
        if code not in OT_ONLY:
            continue          # Romans quotes the Psalms; that is not a numbering difference
        for ci, chapter in enumerate(book["chapters"]):
            for g in grams(" ".join(chapter)):
                postings[g] += 1
                index[g].append((code, ci + 1))
    return postings, index


def align(greek_chapters, postings, index, code):
    """For each Greek chapter, the Hebrew chapter sharing the most distinctive
    four-word sequences. Sequences common to many chapters identify nothing, so
    they are weighted down the same way the quotation finder weights them."""
    out = []
    for gi, chapter in enumerate(greek_chapters):
        tally = collections.Counter()
        for g in grams(" ".join(chapter)):
            n = postings.get(g, 0)
            if not n or n > 8:            # in too many chapters to identify one
                continue
            for ref in index[g]:
                tally[ref] += 1.0 / n
        if not tally:
            out.append((gi + 1, None, None, 0.0))
            continue
        (bc, ch), score = tally.most_common(1)[0]
        # Claim a different number only when the evidence clearly beats the chapter
        # of the same number. Parallel passages (Samuel and Chronicles telling one
        # story) otherwise masquerade as renumbering.
        same = tally.get((code, gi + 1), 0.0)
        floor = max(MIN_CROSS if bc != code else MIN_SCORE, same * 1.5 + 0.5)
        if score < floor:
            bc, ch, score = code, gi + 1, same
        out.append((gi + 1, bc, ch, round(score, 1)))
    return out


def build():
    greek = lib.books_by_code(GREEK)
    hebrew = lib.books_by_code(HEBREW)
    postings, index = hebrew_index(hebrew)

    books = []
    for code in sorted(greek, key=lib.order_of):
        if code not in hebrew:
            continue                       # a book the Hebrew canon does not carry
        pairs = align(greek[code]["chapters"], postings, index, code)
        differs = [(g, bc, h, s) for g, bc, h, s in pairs
                   if h is not None and s >= MIN_SCORE and (bc != code or g != h)]
        if not differs:
            continue
        matched = [p for p in pairs if p[2] is not None and p[3] >= MIN_SCORE]
        # Chapters this method could not place. Usually that means the chapter is
        # short and has too few distinctive phrases to match on — NOT that it has
        # no counterpart. The one that genuinely has none is noted below by name.
        unplaced = [g for g, _, _, sc in pairs if sc < MIN_SCORE]
        entry = {
            "code": code,
            "book": lib.name_for(code),
            "chapters": len(pairs),
            "differing": len(differs),
            "matched": len(matched),
            # greek chapter → where it is in a Hebrew-numbered Bible
            "map": {str(g): (h if bc == code else f"{bc} {h}") for g, bc, h, _ in differs},
            "weakest": min((s for _, _, _, s in differs), default=0.0),
        }
        if unplaced:
            entry["unplaced"] = unplaced
        if code == "PSA":
            entry["note"] = ("The Greek numbers most of the Psalms one lower than a Hebrew "
                             "Bible does, because it joins Psalms 9 and 10 into one. Psalm 151 "
                             "is supernumerary — it is in the Greek and not in the Hebrew at "
                             "all, which is a fact about the canon rather than the numbering.")
        elsewhere = sorted({bc for _, bc, _, _ in differs if bc != code}, key=lib.order_of)
        if elsewhere:
            entry["alsoIn"] = elsewhere
        books.append(entry)

    data = {
        "note": ("Where the Greek Old Testament and a Hebrew-based one number things "
                 "differently. Derived by matching the chapters' own wording — not asserted "
                 "from a reference table — so it can be checked, and it is: see "
                 "scripts/check_versification.py. Only differing chapters are listed; anything "
                 "absent is numbered the same in both. `unplaced` lists chapters this method "
                 "could not confidently place, which usually means the chapter is short rather "
                 "than that it has no counterpart."),
        "schemes": {
            "masoretic": "The numbering of a Hebrew-based Old Testament (BSB, KJV, WEB here).",
            "septuagint": "The numbering of the Greek Old Testament (Brenton here).",
        },
        "from": GREEK, "to": HEBREW,
        "method": {"ngram": N, "minScore": MIN_SCORE, "maxChapterPostings": 8},
        "books": books,
    }
    lib.write_json(OUT, data, indent=1)
    total = sum(b["differing"] for b in books)
    print(f"wrote library/versification.json — {total} chapters numbered differently "
          f"across {len(books)} books")
    for b in books:
        extra = f"  → also {', '.join(b['alsoIn'])}" if b.get("alsoIn") else ""
        print(f"  {b['book']:<14} {b['differing']:>3} of {b['chapters']} chapters differ "
              f"(weakest match {b['weakest']}){extra}")


if __name__ == "__main__":
    build()
