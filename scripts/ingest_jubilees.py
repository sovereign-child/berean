#!/usr/bin/env python3
"""
Berean wider-canon ingest — Jubilees (R.H. Charles, 1917).

The last book Berean's canon table named but could not open. Jubilees is
canonical in the Ethiopian Orthodox Tewahedo Church, was found in more than a
dozen copies at Qumran, and retells Genesis and Exodus on a calendar of jubilees
— including the version of Genesis 6 that the Watchers tradition runs through.

The roadmap carried it as blocked for want of "a clean PD machine-readable
source": the scans of Charles are OCR, and the readable web copies are wrapped
in someone's site. Sefaria publishes the Charles 1917 translation through an
open API with chapter and verse structure intact, marked Public Domain — so the
text arrives already divided the way Berean stores it, with nothing to OCR and
nothing to scrape.

The script refuses to write anything if the version it is handed is not the one
named below, or is not marked public domain. A text this project hosts has to be
one it can account for.

Reproducible, stdlib only. Run from the repo root:
    python3 scripts/ingest_jubilees.py

Output: library/corpus/JUBILEES.json  +  an entry in library/manifest.json.
(Then run scripts/shard_corpus.py so the reader can fetch it a book at a time.)
"""

import json
import os
import re
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "library")

WANT_VERSION = "The Book of Jubilees, trans. R. H. Charles. London [1917]"
WANT_LICENSE = "Public Domain"
API = "https://www.sefaria.org/api/v3/texts/Book_of_Jubilees"
CHAPTERS = 50


def fetch():
    url = API + "?" + urllib.parse.urlencode({"version": f"english|{WANT_VERSION}"})
    req = urllib.request.Request(url, headers={"User-Agent": "berean-ingest/0.1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def clean(text):
    text = re.sub(r"<br\s*/?>", " ", str(text))
    text = re.sub(r"<[^>]+>", "", text)          # no markup reaches the corpus
    return re.sub(r"\s+", " ", text).strip()


def main():
    print(f"fetching Jubilees (Charles 1917, PD) from {API} …")
    data = fetch()
    versions = data.get("versions") or []
    if not versions:
        raise SystemExit("Jubilees: the API returned no version — refusing to write anything")
    v = versions[0]
    if v.get("versionTitle") != WANT_VERSION:
        raise SystemExit(f"Jubilees: expected {WANT_VERSION!r}, got {v.get('versionTitle')!r}")
    if v.get("license") != WANT_LICENSE:
        raise SystemExit(f"Jubilees: version is licensed {v.get('license')!r}, not "
                         f"{WANT_LICENSE!r} — Berean hosts only open texts")

    chapters = [[clean(verse) for verse in chapter if clean(verse)] for chapter in v["text"]]
    chapters = [c for c in chapters if c]
    if len(chapters) != CHAPTERS:
        raise SystemExit(f"Jubilees: expected {CHAPTERS} chapters, got {len(chapters)}")

    out = {
        "version": "JUBILEES",
        "name": "Jubilees (R.H. Charles)",
        "language": "en",
        "license": "Public Domain",
        "source": f"{API} — version: {WANT_VERSION}",
        "attribution": ("The Book of Jubilees, translated by R. H. Charles (London, 1917) — "
                        "Public Domain, via Sefaria (sefaria.org)."),
        "tradition": "Pseudepigrapha",
        "canon_status": ("Canonical in the Ethiopian Orthodox Tewahedo Church; not received as "
                         "Scripture in the Jewish, Catholic, Orthodox or Protestant canons. Found "
                         "in more than a dozen copies among the Dead Sea Scrolls, which makes it "
                         "one of the most widely copied books at Qumran."),
        "canonical": False,
        "books": [{"name": "Jubilees", "chapters": chapters}],
    }
    path = os.path.join(LIB, "corpus", "JUBILEES.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    nv = sum(len(c) for c in chapters)
    print(f"wrote {os.path.relpath(path, ROOT)}: {len(chapters)} chapters, {nv} verses, "
          f"{os.path.getsize(path) // 1024} KB")

    mpath = os.path.join(LIB, "manifest.json")
    with open(mpath, encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest["versions"] = [x for x in manifest["versions"] if x.get("id") != "JUBILEES"]
    manifest["versions"].append({
        "version": "JUBILEES", "name": out["name"], "language": "en",
        "license": out["license"], "source": out["source"], "attribution": out["attribution"],
        "tradition": "Pseudepigrapha", "canon_status": out["canon_status"],
        "canonical": False, "id": "JUBILEES",
    })
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print("updated library/manifest.json — run scripts/shard_corpus.py next")


if __name__ == "__main__":
    main()
