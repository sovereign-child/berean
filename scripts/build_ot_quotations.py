#!/usr/bin/env python3
"""
Berean — the Old Testament in the New.

When the New Testament quotes the Old, most Bibles leave you to notice it. This
finds those places and records them, so a reader in Matthew 1 can see that the
verse in front of them is Isaiah 7:14, and open it.

Nothing is licensed and nothing is hand-listed: both testaments are already here
in one public-domain translation, so a quotation can be found by looking for it.
Each New Testament verse is compared against an index of every four-word
sequence in the Old Testament; a verse that shares several of them with an Old
Testament verse is quoting it, or reaching for it.

Two signals, kept apart in the output rather than blurred:

  quotation — the writer says so ("as it is written", "spoken through the
              prophet"), or the wording overlaps heavily
  echo      — the wording overlaps, with no citation formula: the New Testament
              writers thought in Scripture, and much of this is allusion rather
              than citation. Labeled as such, never claimed as a quotation.

Where the source runs across two verses (Matthew 21:42 quotes Psalm 118:22-23)
the range is kept whole. Where a verse quotes two places at once (Hebrews 1:5
puts Psalm 2:7 beside 2 Samuel 7:14) both are listed, because both are there.

Output: library/ot-quotations.json — references and scores, never a copy of the
text. Run from the repo root:

    python3 scripts/build_ot_quotations.py
"""

import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import berean_lib as lib   # noqa: E402

OUT = os.path.join(lib.LIB, "ot-quotations.json")
VERSION = "BSB"
N = 4                       # length of the word sequences compared
# A four-word sequence is worth what it can identify. "the angel of the LORD"
# appears in hundreds of verses and identifies nothing; "lord will be saved"
# appears in a handful and identifies a passage. Weighted, rather than a hard
# cutoff, which would have thrown away Romans 10:13 — Joel 2:32 word for word,
# built almost entirely out of common phrases.
def weight(postings):
    if postings <= 5:
        return 1.0
    if postings <= 15:
        return 0.5
    if postings <= 40:
        return 0.2
    return 0.0

MIN_SHARED = 3.0            # below this weighted total, an overlap is coincidence
MIN_WITH_FORMULA = 2.0      # a writer saying "as it is written" is evidence of its own
ECHO_SHARED = 5.0           # without a citation formula, this much overlap to count
MAX_SOURCES = 3

# The New Testament's own ways of saying "this is Scripture".
FORMULA = re.compile(
    r"(is written|the Scriptures?\b|as the prophet|through the prophet|spoken (?:of )?through"
    r"|to fulfill what|was fulfilled|says the Lord|the Law says|in the Law"
    r"|(?:Isaiah|Moses|David|Jeremiah|Ezekiel|Daniel|Hosea|Joel|Habakkuk|Malachi|the prophet"
    r"|Scripture|God|he|He|it) (?:say|says|said|writes|declares|testifies|cried out)"
    r"|again[, ]|once more|for this reason it says)", re.I)

WORD = re.compile(r"[a-z]+")


def words(text):
    return WORD.findall(text.lower())


def grams(ws):
    return {tuple(ws[i:i + N]) for i in range(len(ws) - N + 1)}


def build_ot_index(by_code, ot_codes):
    """Every four-word sequence in the Old Testament, minus the stock phrases.

    "the right hand of", "the angel of the LORD", "the lord your god" occur in
    hundreds of verses; matching on them finds a formula of Hebrew narrative, not
    a quotation. Only sequences rare enough to identify a passage are kept."""
    idx = collections.defaultdict(set)
    for code in ot_codes:
        for ci, chapter in enumerate(by_code[code]["chapters"]):
            for vi, text in enumerate(chapter):
                for g in grams(words(text)):
                    idx[g].add((code, ci + 1, vi + 1))
    weights = {g: weight(len(refs)) for g, refs in idx.items()}
    dropped = sum(1 for w in weights.values() if not w)
    print(f"  Old Testament index: {len(idx)} {N}-word sequences "
          f"({dropped} too common to identify anything)")
    return idx, weights


def merge_runs(refs):
    """Consecutive verses of one book are one citation: Psalm 118:22-23."""
    out = []
    for code, c, v, score in sorted(refs, key=lambda r: (lib.order_of(r[0]), r[1], r[2])):
        if out and out[-1][0] == code and out[-1][1] == c and v - out[-1][3] <= 1:
            out[-1][3] = max(out[-1][3], v)
            out[-1][4] = max(out[-1][4], score)
        else:
            out.append([code, c, v, v, score])
    return out


def build():
    by_code = lib.books_by_code(VERSION)
    reg = lib.registry()["books"]
    ot_codes = [b["code"] for b in reg if b["section"] == "ot" and b["code"] in by_code]
    nt_codes = [b["code"] for b in reg if b["section"] == "nt" and b["code"] in by_code]
    idx, weights = build_ot_index(by_code, ot_codes)

    books_out = []
    counts = collections.Counter()
    for code in nt_codes:
        chapters = by_code[code]["chapters"]
        found = []
        for ci, chapter in enumerate(chapters):
            for vi, text in enumerate(chapter):
                gs = grams(words(text))
                if len(gs) < N:
                    continue
                tally = collections.Counter()
                for g in gs:
                    w = weights.get(g, 0.0)
                    if not w:
                        continue
                    for ref in idx[g]:
                        tally[ref] += w
                if not tally:
                    continue
                best = max(tally.values())
                if best < MIN_SHARED:
                    continue
                # The citation formula often sits a verse or two above the words it
                # introduces ("this is what was spoken by the prophet Joel:"), and a
                # long quotation runs on past it — so a verse continuing the previous
                # verse's citation is a quotation too.
                # The formula may introduce the verse from just above it, but no
                # further: two verses of reach let "to fulfill what the prophet
                # said" in Matthew 1:22 label the genealogy either side of it.
                here = FORMULA.search(text)
                formula = here or (FORMULA.search(chapter[vi - 1]) if vi else None)
                prev = found[-1] if found else None
                continues = bool(prev and prev["at"] == [ci + 1, vi]
                                 and {s["code"] for s in prev["sources"]} & {r[0] for r in tally})
                floor = MIN_WITH_FORMULA if here else (MIN_SHARED if not (formula or continues)
                                                       else MIN_SHARED)
                if best < floor:
                    continue
                kind = ("quotation" if (formula or continues)
                        else ("echo" if best >= ECHO_SHARED else None))
                if not kind:
                    continue
                # take the strongest sources, THEN put them in canonical order — the
                # other way round drops Psalm 2:7 from Hebrews 1:5, which quotes it
                # alongside 2 Samuel 7:14.
                keep = sorted([(c, ch, v, s) for (c, ch, v), s in tally.items()
                               if s >= max(floor, best * 0.5)],
                              key=lambda r: -r[3])[:MAX_SOURCES]
                sources = merge_runs(keep)
                found.append({
                    "ref": f"{lib.name_for(code)} {ci + 1}:{vi + 1}",
                    "at": [ci + 1, vi + 1],
                    "kind": kind,
                    "formula": formula.group(0).lower() if formula else None,
                    "sources": [{
                        "code": c, "from": [ch, v1], "to": [ch, v2],
                        "ref": f"{lib.name_for(c)} {ch}:{v1}" + (f"–{v2}" if v2 > v1 else ""),
                        "shared": round(s, 1),
                    } for c, ch, v1, v2, s in sources],
                })
                counts[kind] += 1
        if found:
            books_out.append({"code": code, "book": lib.name_for(code), "quotations": found})

    sources_used = {s["code"] for b in books_out for q in b["quotations"] for s in q["sources"]}
    data = {
        "id": "OTQ",
        "title": "The Old Testament in the New",
        "version": VERSION,
        "license": "CC0-1.0",
        "attribution": lib.load_bundle(VERSION)["attribution"],
        "note": ("Found by comparing every New Testament verse against an index of every "
                 f"{N}-word sequence in the Old Testament, in one public-domain translation "
                 "that carries both. A “quotation” is one the writer marks as Scripture or "
                 "whose wording overlaps heavily; an “echo” is wording that overlaps with no "
                 "citation formula — the New Testament writers thought in Scripture, and much "
                 "of that is allusion rather than citation. The distinction is kept in the data "
                 "rather than flattened. Where a verse draws on two places at once, both are "
                 "listed; where the source runs across verses, the range is kept whole. "
                 "The known blind spot: the New Testament usually quotes the Greek Septuagint, "
                 "while an English Old Testament translates the Hebrew — so where the two "
                 "traditions word a verse differently there is nothing for this to match on, "
                 "and the quotation is missed rather than guessed at."),
        "method": {"ngram": N, "minShared": MIN_SHARED, "echoShared": ECHO_SHARED},
        "stats": {"quotations": counts["quotation"], "echoes": counts["echo"],
                  "ntBooks": len(books_out), "otBooksCited": len(sources_used)},
        "books": books_out,
    }
    lib.write_json(OUT, data)
    print(f"wrote library/ot-quotations.json — {counts['quotation']} quotations, "
          f"{counts['echo']} echoes, across {len(books_out)} New Testament books, "
          f"citing {len(sources_used)} Old Testament books "
          f"({os.path.getsize(OUT) // 1024} KB)")


if __name__ == "__main__":
    build()
