#!/usr/bin/env python3
"""
Berean — verify that every citation in library/threads.json is real.

A Thread's whole claim is that you can open every step and read it yourself. That
only holds if each reference actually resolves in the text it names, so this
checks them the way the reader does — same reference grammar, same book aliases —
and fails loudly if one does not.

Steps with no `version` are cited by reference on purpose (the Quran, Jubilees,
Josephus): those are reported, not resolved, so it stays visible how much of a
thread rests on texts Berean does not host.

Run from the repo root:
    python3 scripts/check_threads.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "library")
REF_RE = re.compile(r"^(\d?\s?[A-Za-z ]+?)\s+(\d+):(\d+)(?:-(\d+))?$")   # as in web/app.js
ALIAS = {"Psalm": "Psalms", "Song of Songs": "Song of Solomon", "Canticles": "Song of Solomon"}

corpus = {}


def version(vid):
    if vid not in corpus:
        path = os.path.join(LIB, "corpus", f"{vid}.json")
        if not os.path.exists(path):
            corpus[vid] = None
        else:
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
            corpus[vid] = {b["name"]: b for b in d["books"]}
    return corpus[vid]


def resolve(ref, vid):
    m = REF_RE.match(ref)
    if not m:
        return None, "reference does not parse"
    name = ALIAS.get(m.group(1).strip(), m.group(1).strip())
    books = version(vid)
    if books is None:
        return None, f"version {vid} is not in library/corpus"
    book = books.get(name)
    if not book:
        return None, f"{name} is not in {vid}"
    c, v1 = int(m.group(2)), int(m.group(3))
    v2 = int(m.group(4)) if m.group(4) else v1
    if c > len(book["chapters"]):
        return None, f"{name} has no chapter {c} in {vid}"
    chapter = book["chapters"][c - 1]
    parts = [chapter[v - 1] for v in range(v1, min(v2, len(chapter)) + 1) if v <= len(chapter)]
    if not parts or not any(p.strip() for p in parts):
        return None, f"{ref} is empty in {vid}"
    return " ".join(parts), None


def main():
    with open(os.path.join(LIB, "threads.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    labels = data.get("statusLabels", {})
    bad = 0

    for thread in data.get("threads", []):
        resolved = byref = 0
        print(f"\n{thread['title']}  ({thread['id']})")
        for step in thread.get("steps", []):
            ref, vid = step.get("ref", ""), step.get("version")
            if step.get("status") not in labels:
                print(f"  FAIL  {ref}: unknown status {step.get('status')!r}")
                bad += 1
            if not vid:
                byref += 1
                print(f"  ref   {ref:<22} cited by reference ({step.get('tradition', '—')})")
                continue
            text, err = resolve(ref, vid)
            if err:
                print(f"  FAIL  {ref:<22} {err}")
                bad += 1
            else:
                resolved += 1
                print(f"  ok    {ref:<22} {vid}  {text[:58]}…")
        print(f"  → {resolved} resolved, {byref} cited by reference")

    print(f"\n{'FAILED' if bad else 'all citations resolve'}"
          f"{f' — {bad} problem(s)' if bad else ''}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
