#!/usr/bin/env python3
"""
Berean — check the derived chapter map against what scholarship already knows.

library/versification.json is derived from the texts rather than copied from a
reference table. That is only worth doing if the result can be checked, so this
checks it: the Psalms offset, the relocated oracles in Jeremiah, and Esdras B —
which is Ezra and Nehemiah as one book — are all documented independently of
Berean, and the derivation has to reproduce them.

    python3 scripts/check_versification.py
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "library", "versification.json"), encoding="utf-8"))

# (book code, chapter in the Greek, where it should land in a Hebrew-numbered Bible)
EXPECT = [
    # The Psalms run one lower from Psalm 10 on, because the Greek joins 9 and 10.
    ("PSA", 10, 11), ("PSA", 22, 23), ("PSA", 50, 51), ("PSA", 90, 91), ("PSA", 145, 146),
    # …and rejoin at the end.
    ("PSA", 148, 148), ("PSA", 150, 150),
    # Jeremiah's oracles against the nations sit in the middle of the Greek book.
    ("JER", 32, 25),        # the cup of wrath
    ("JER", 26, 46), ("JER", 27, 50), ("JER", 28, 51), ("JER", 29, 47),
    ("JER", 30, 49), ("JER", 31, 48),
    # Esdras B is Ezra and Nehemiah together.
    ("EZR", 11, "NEH 1"), ("EZR", 23, "NEH 13"),
    # Hebrew Joel has four chapters where English has three.
    ("JOL", 3, 2), ("JOL", 4, 3),
    # 3 Kingdoms swaps Naboth's vineyard with the Aramean wars.
    ("1KI", 20, 21), ("1KI", 21, 20),
]


def main():
    books = {b["code"]: b for b in DATA["books"]}
    bad = 0
    for code, greek, want in EXPECT:
        entry = books.get(code)
        got = (entry or {}).get("map", {}).get(str(greek))
        if got is None and want == greek:
            print(f"ok    {code} {greek:<3} unchanged, as expected")
            continue
        ok = got == want
        bad += 0 if ok else 1
        print(f"{'ok   ' if ok else 'FAIL '} {code} {greek:<3} → {str(got):<8} (expected {want})")

    total = sum(b["differing"] for b in DATA["books"])
    print(f"\n{total} chapters numbered differently across {len(DATA['books'])} books; "
          f"{len(EXPECT)} documented correspondences checked")
    print("FAILED" if bad else "the derived map matches the documented one")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
