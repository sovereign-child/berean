#!/usr/bin/env python3
"""
Berean cross-reference ingest.

Fetches the OpenBible.info cross-reference dataset (CC BY) — derived from the
Treasury of Scripture Knowledge and community-voted — and normalizes it into
library/crossrefs.json for the reader's "related verses" feature.

Reproducible, stdlib only. Run from repo root:  python3 scripts/ingest_crossrefs.py

Output (compact, book indices 0..65 in canonical order):
    {"attribution": "...CC BY", "source": "...", "refs": {
        "<bi>.<ch>.<v>": ["<bi>.<ch>.<v>", "<bi>.<ch>.<v>-<endV>", ...],  # ranked, top 25
    }}
"""
import io
import json
import os
import urllib.request
import zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://a.openbible.info/data/cross-references.zip"
CAP = 25  # top-N related verses per source verse

# OSIS book codes in canonical Protestant order (index matches library/corpus book order).
OSIS = ["Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "Ruth", "1Sam", "2Sam",
        "1Kgs", "2Kgs", "1Chr", "2Chr", "Ezra", "Neh", "Esth", "Job", "Ps", "Prov",
        "Eccl", "Song", "Isa", "Jer", "Lam", "Ezek", "Dan", "Hos", "Joel", "Amos",
        "Obad", "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal", "Matt",
        "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal", "Eph", "Phil",
        "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm", "Heb", "Jas",
        "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev"]
IDX = {c: i for i, c in enumerate(OSIS)}


def parse_ref(ref: str):
    """'Rom.1.19' -> (idx, chapter, verse) or None."""
    parts = ref.split(".")
    if len(parts) != 3 or parts[0] not in IDX:
        return None
    try:
        return IDX[parts[0]], int(parts[1]), int(parts[2])
    except ValueError:
        return None


def main():
    print("fetching cross-references…")
    raw = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "berean/0.1"}), timeout=180).read()
    zf = zipfile.ZipFile(io.BytesIO(raw))
    lines = zf.read("cross_references.txt").decode("utf-8", "replace").splitlines()

    scored = defaultdict(dict)  # fromkey -> {toval: votes}
    for line in lines[1:]:  # skip header
        cols = line.split("\t")
        if len(cols) < 3:
            continue
        frm, to, votes = cols[0], cols[1], cols[2]
        try:
            votes = int(votes)
        except ValueError:
            continue
        if votes <= 0:
            continue
        f = parse_ref(frm)
        if not f:
            continue
        ends = to.split("-")
        s = parse_ref(ends[0])
        if not s:
            continue
        bi, ch, v = s
        toval = f"{bi}.{ch}.{v}"
        if len(ends) == 2:
            e = parse_ref(ends[1])
            if e and e[0] == bi and e[1] == ch and e[2] > v:
                toval = f"{bi}.{ch}.{v}-{e[2]}"
        fromkey = f"{f[0]}.{f[1]}.{f[2]}"
        d = scored[fromkey]
        if votes > d.get(toval, -1):
            d[toval] = votes

    refs = {}
    for fromkey, d in scored.items():
        ranked = sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:CAP]
        refs[fromkey] = [tv for tv, _ in ranked]

    out = {
        "attribution": "Cross-references from www.openbible.info (CC BY), derived from the Treasury of Scripture Knowledge + community votes.",
        "source": URL,
        "license": "CC BY 4.0",
        "refs": refs,
    }
    path = os.path.join(ROOT, "library", "crossrefs.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    total = sum(len(v) for v in refs.values())
    print(f"wrote {path}: {len(refs)} source verses, {total} links, {os.path.getsize(path)//1024} KB")


if __name__ == "__main__":
    main()
