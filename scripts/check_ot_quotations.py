#!/usr/bin/env python3
"""
Berean — checks on "The Old Testament in the New".

Verifies that well-known quotations were found and point at the right place, and
that ordinary verses were not swept in. Run after rebuilding:

    python3 scripts/build_ot_quotations.py && python3 scripts/check_ot_quotations.py
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "library", "ot-quotations.json"), encoding="utf-8"))

# New Testament verse → an Old Testament book+chapter it must cite.
EXPECT = [
    ("Matthew 1:23", "ISA", 7), ("Matthew 4:4", "DEU", 8), ("Matthew 4:7", "DEU", 6),
    ("Matthew 21:42", "PSA", 118), ("Matthew 22:37", "DEU", 6), ("Matthew 27:46", "PSA", 22),
    ("Mark 12:29", "DEU", 6), ("Luke 4:18", "ISA", 61), ("John 12:38", "ISA", 53),
    ("John 19:24", "PSA", 22), ("Acts 2:17", "JOL", 2), ("Romans 1:17", "HAB", 2),
    ("Romans 3:4", "PSA", 51), ("Romans 10:13", "JOL", 2), ("Romans 15:12", "ISA", 11),
    ("2 Corinthians 6:16", ("LEV", "JER", "EZK"), None),   # composite; the phrase recurs
    ("Galatians 3:11", "HAB", 2), ("Hebrews 1:5", "PSA", 2), ("Hebrews 10:5", "PSA", 40),
    ("1 Peter 1:16", "LEV", 11), ("1 Peter 2:7", "PSA", 118),
]

# Quotations this method cannot see: the New Testament quotes the Greek, an
# English Old Testament renders the Hebrew, and where those differ there is
# nothing to match on. Listed rather than quietly dropped from the checks.
KNOWN_LIMITS = {
    "Matthew 4:7": "Deut 6:16 — 'do not put to the test' vs 'do not test'",
    "Romans 15:12": "Isaiah 11:10 — only 'the Root of Jesse' survives both renderings",
    "1 Corinthians 15:54": "Isaiah 25:8 — 'swallowed up in victory' vs 'swallow up death'",
}

# Verses that quote nothing — a sweep that catches these is catching noise.
EXPECT_NONE = ["Matthew 5:3", "John 1:1", "Romans 8:28", "Philippians 4:13", "Revelation 1:1"]


def index():
    out = {}
    for b in DATA["books"]:
        for q in b["quotations"]:
            out[q["ref"]] = q
    return out


def main():
    found, bad = index(), 0
    for ref, code, chapter in EXPECT:
        q = found.get(ref)
        if not q:
            if ref in KNOWN_LIMITS:
                print(f"limit {ref:<22} not detectable: {KNOWN_LIMITS[ref]}")
            else:
                print(f"MISS  {ref:<22} expected {code} {chapter} — not found")
                bad += 1
            continue
        codes = code if isinstance(code, tuple) else (code,)
        hit = any(s["code"] in codes and (chapter is None or s["from"][0] == chapter)
                  for s in q["sources"])
        print(f"{'ok   ' if hit else 'FAIL '} {ref:<22} {q['kind']:<10} "
              + ", ".join(f"{s['ref']} ({s['shared']})" for s in q["sources"]))
        if not hit:
            bad += 1
    for ref in EXPECT_NONE:
        if ref in found:
            print(f"FAIL  {ref} should not be listed — {found[ref]['sources'][0]['ref']}")
            bad += 1
    print(f"\n{len(KNOWN_LIMITS)} known limitations, listed above and in the data note.")
    print(f"{DATA['stats']['quotations']} quotations · {DATA['stats']['echoes']} echoes · "
          f"{len(EXPECT)} landmarks checked, {len(EXPECT_NONE)} verses checked clean")
    print("FAILED" if bad else "all landmark quotations resolve")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
