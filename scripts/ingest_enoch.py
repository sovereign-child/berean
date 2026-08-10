#!/usr/bin/env python3
"""
Berean wider-canon ingest — 1 Enoch (R.H. Charles, 1917).

Kicks off Phase 3 (the wider canon / "lost books"). Ingests the public-domain
R.H. Charles translation of 1 Enoch from Project Gutenberg (#77935) into the same
corpus schema as the Bible versions, but CLEARLY LABELED by tradition and canon
status — it is non-canonical in most traditions, canonical in the Ethiopian
Orthodox Tewahedo Church, and famously quoted in Jude 14-15.

Nothing is fabricated: the text is the actual Charles translation; editorial marks
(〚 〛 ⌜ ⌝ = =) used by Charles for restorations/uncertainty are simplified for
reading. Reproducible, stdlib only. Run from repo root:

    python3 scripts/ingest_enoch.py

Output: library/corpus/ENOCH.json  +  an entry in library/manifest.json.
"""
import json
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "library")
URL = "https://www.gutenberg.org/cache/epub/77935/pg77935.txt"
START = "I. 1. The words of the blessing of Enoch"
END = "END OF THE PROJECT GUTENBERG"
ROMAN = re.compile(r"^([IVXLCDM]+)\.\s")
VERSE = re.compile(r"(?:^|\s)(\d{1,3})\.\s+")


def roman_to_int(s):
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total, prev = 0, 0
    for ch in reversed(s):
        v = vals.get(ch, 0)
        total += -v if v < prev else v
        prev = max(prev, v)
    return total


def clean(t):
    t = t.replace("〚", "").replace("〛", "").replace("⌜", "").replace("⌝", "")
    t = t.replace("=", "").replace("†", "")
    return re.sub(r"\s+", " ", t).strip()


def main():
    print("fetching 1 Enoch (Charles, PD) from Project Gutenberg…")
    req = urllib.request.Request(URL, headers={"User-Agent": "berean-research/0.1"})
    text = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")
    lines = text.splitlines()

    # isolate the translated body
    s = next(i for i, ln in enumerate(lines) if ln.startswith(START))
    e = next(i for i, ln in enumerate(lines) if END in ln)
    body = lines[s:e]

    # group into chapters by line-initial Roman numeral
    chapters = []          # list of (chapter_number, joined_text)
    cur_num, cur_lines = None, []
    for ln in body:
        m = ROMAN.match(ln)
        if m and roman_to_int(m.group(1)) > 0:
            if cur_num is not None:
                chapters.append((cur_num, " ".join(cur_lines)))
            cur_num = roman_to_int(m.group(1))
            cur_lines = [ln[m.end():]]          # drop the "VI. " chapter marker
        elif cur_num is not None:
            cur_lines.append(ln)
    if cur_num is not None:
        chapters.append((cur_num, " ".join(cur_lines)))

    # split each chapter's text into verses on inline "N." markers
    max_ch = max(n for n, _ in chapters)
    out_chapters = [[] for _ in range(max_ch)]
    for num, raw in chapters:
        parts = VERSE.split(raw)          # [pre, n, text, n, text, ...]
        verses = {}
        if parts[0].strip():
            verses[1] = clean(parts[0])
        for i in range(1, len(parts) - 1, 2):
            vnum = int(parts[i]); vtext = clean(parts[i + 1])
            if vtext:
                verses[vnum] = vtext
        hi = max(verses) if verses else 0
        out_chapters[num - 1] = [verses.get(v, "") for v in range(1, hi + 1)]

    data = {
        "version": "ENOCH",
        "name": "1 Enoch (R.H. Charles)",
        "language": "en",
        "license": "Public Domain",
        "source": "https://www.gutenberg.org/ebooks/77935",
        "attribution": "The Book of Enoch, translated by R. H. Charles (SPCK, 1917) — Public Domain, via Project Gutenberg #77935.",
        "tradition": "Pseudepigrapha",
        "canon_status": "Non-canonical in Jewish, Catholic, Orthodox and Protestant canons; canonical in the Ethiopian Orthodox Tewahedo Church; quoted in Jude 14-15.",
        "books": [{"name": "1 Enoch", "chapters": out_chapters}],
    }
    path = os.path.join(LIB, "corpus", "ENOCH.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    nch = len(out_chapters)
    nv = sum(len(c) for c in out_chapters)
    print(f"wrote {path}: {nch} chapters, {nv} verses, {os.path.getsize(path)//1024} KB")

    # register in the manifest (append; keep Bible versions first / default)
    mpath = os.path.join(LIB, "manifest.json")
    with open(mpath, encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest["versions"] = [v for v in manifest["versions"] if v.get("id") != "ENOCH"]
    manifest["versions"].append({
        "version": "ENOCH", "name": data["name"], "language": "en",
        "license": data["license"], "source": data["source"],
        "attribution": data["attribution"], "tradition": "Pseudepigrapha",
        "canon_status": data["canon_status"], "canonical": False, "id": "ENOCH",
    })
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print("updated library/manifest.json")


if __name__ == "__main__":
    main()
