#!/usr/bin/env python3
"""
Berean commentary ingest.

Vendors openly-licensed, public-domain Bible commentaries from HelloAO's Free Use
Bible API (bible.helloao.org) into local static files the reader lazy-loads. This
is the sourced "ground truth" the study/AI layers cite — never fabricated.

Commentaries available upstream (all Public Domain except Tyndale = CC BY-SA 4.0):
    adam-clarke, jamieson-fausset-brown, john-calvin, john-gill,
    keil-delitzsch (OT), matthew-henry, tyndale

Reproducible, stdlib only. Run from repo root, e.g.:
    python3 scripts/ingest_commentary.py --list
    python3 scripts/ingest_commentary.py --commentary matthew-henry --book John
    python3 scripts/ingest_commentary.py --commentary matthew-henry,jamieson-fausset-brown --book John
    python3 scripts/ingest_commentary.py --commentary matthew-henry --all-books   # long

Output:
    library/commentary/<id>/<bookIndex>/<chapter>.json   (bookIndex 0..65 canonical)
    library/commentary/manifest.json                     (commentaries + coverage)
"""
import argparse
import json
import os
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "library")
API = "https://bible.helloao.org/api"

# Canonical 66-book order (index shared with the corpus + cross-references) -> USFM codes.
BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth",
         "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
         "Nehemiah", "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon",
         "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
         "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah",
         "Malachi", "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians",
         "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians",
         "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
         "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"]
USFM = ["GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "1SA", "2SA", "1KI", "2KI", "1CH",
        "2CH", "EZR", "NEH", "EST", "JOB", "PSA", "PRO", "ECC", "SNG", "ISA", "JER", "LAM", "EZK",
        "DAN", "HOS", "JOL", "AMO", "OBA", "JON", "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL",
        "MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP", "COL", "1TH",
        "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS", "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"]
ALIAS = {"psalm": "Psalms", "song of songs": "Song of Solomon", "canticles": "Song of Solomon"}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "berean/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def chapter_counts():
    """Chapters per book, taken from the local BSB corpus (source of truth)."""
    with open(os.path.join(LIB, "corpus", "BSB.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    return {b["name"]: len(b["chapters"]) for b in data["books"]}


def flatten(node):
    """Recursively pull readable text out of HelloAO content nodes."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return " ".join(flatten(n) for n in node)
    if isinstance(node, dict):
        if "text" in node and isinstance(node["text"], str):
            return node["text"]
        if "content" in node:
            return flatten(node["content"])
    return ""


def resolve_book(arg):
    if arg.isdigit():
        i = int(arg)
        if 0 <= i < 66:
            return i
        raise SystemExit(f"book index {i} out of range 0..65")
    name = ALIAS.get(arg.strip().lower(), arg.strip())
    for i, b in enumerate(BOOKS):
        if b.lower() == name.lower():
            return i
    raise SystemExit(f"unknown book: {arg}")


def load_manifest():
    path = os.path.join(LIB, "commentary", "manifest.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {"source": "https://bible.helloao.org", "commentaries": []}


def save_manifest(m):
    os.makedirs(os.path.join(LIB, "commentary"), exist_ok=True)
    with open(os.path.join(LIB, "commentary", "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=2)


def upstream_meta():
    try:
        d = fetch(f"{API}/available_commentaries.json")
        return {c["id"]: c for c in d.get("commentaries", [])}
    except Exception as e:
        raise SystemExit(f"could not reach HelloAO API: {e}")


def ingest_one(cid, meta, book_indices, chapters_spec, counts, dry):
    covered = set()
    total = 0
    for bi in book_indices:
        name, code = BOOKS[bi], USFM[bi]
        n = counts.get(name, 0)
        if chapters_spec in ("all", None):
            chapter_nums = range(1, n + 1)
        else:
            chapter_nums = [c for c in parse_spec(chapters_spec) if 1 <= c <= n]
        for cn in chapter_nums:
            url = f"{API}/c/{cid}/{code}/{cn}.json"
            try:
                d = fetch(url)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    continue  # this commentary doesn't cover this chapter
                raise
            ch = d.get("chapter", {})
            blocks = []
            for item in ch.get("content", []):
                if item.get("type") == "verse":
                    text = flatten(item.get("content", [])).strip()
                    if text:
                        blocks.append({"verse": item.get("number"), "text": text})
            if not blocks:
                continue
            covered.add(code)
            total += 1
            if dry:
                print(f"[dry-run] {cid} {name} {cn}  ({len(blocks)} blocks)")
                continue
            out = {"commentary": cid, "book": name, "code": code, "chapter": cn,
                   "intro": flatten(ch.get("introduction", "")).strip(), "blocks": blocks}
            path = os.path.join(LIB, "commentary", cid, code, f"{cn}.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
            print(f"  {cid}: {name} {cn}  ({len(blocks)} blocks, {os.path.getsize(path)//1024} KB)")
    return covered, total


def parse_spec(spec):
    out = set()
    for part in str(spec).split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser(description="Vendor public-domain commentaries from HelloAO.")
    ap.add_argument("--list", action="store_true", help="list upstream commentaries and exit")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--commentary", help="id or comma list (or 'all')")
    ap.add_argument("--book", help="book name or 0-based index")
    ap.add_argument("--all-books", action="store_true")
    ap.add_argument("--chapters", default="all", help="'3', '1-5', '1,3,5', or 'all'")
    args = ap.parse_args()

    meta = upstream_meta()
    if args.list:
        for cid, c in meta.items():
            print(f"  {cid:24} {c.get('name')}   [{c.get('licenseUrl') or c.get('license','')}]")
        return

    if not args.commentary:
        raise SystemExit("specify --commentary ID[,ID...]|all  (see --list)")
    cids = list(meta.keys()) if args.commentary == "all" else args.commentary.split(",")
    for cid in cids:
        if cid not in meta:
            raise SystemExit(f"unknown commentary '{cid}' (see --list)")
    if not args.all_books and not args.book:
        raise SystemExit("specify --book NAME|INDEX (or --all-books)")

    counts = chapter_counts()
    book_indices = list(range(66)) if args.all_books else [resolve_book(args.book)]
    manifest = load_manifest()
    by_id = {c["id"]: c for c in manifest["commentaries"]}

    for cid in cids:
        m = meta[cid]
        lic = m.get("licenseUrl") or m.get("license", "")
        print(f"\n== {cid} — {m.get('name')} ==")
        covered, total = ingest_one(cid, m, book_indices, args.chapters, counts, args.dry_run)
        if args.dry_run:
            print(f"[dry-run] {cid}: {total} chapter(s) would be written.")
            continue
        entry = by_id.get(cid, {"id": cid})
        entry.update({"name": m.get("name"), "englishName": m.get("englishName", m.get("name")),
                      "license": lic, "licenseUrl": m.get("licenseUrl", ""),
                      "attribution": f"{m.get('name')} — via HelloAO Free Use Bible API (bible.helloao.org). {lic}"})
        prev = set(entry.get("books", []))
        entry["books"] = sorted(prev | covered, key=lambda c: USFM.index(c) if c in USFM else 999)
        by_id[cid] = entry
        print(f"  {cid}: wrote {total} chapter(s); covers {len(entry['books'])} book(s).")

    if not args.dry_run:
        manifest["commentaries"] = [by_id[c] for c in by_id]
        save_manifest(manifest)
        print(f"\nManifest: library/commentary/manifest.json")


if __name__ == "__main__":
    main()
