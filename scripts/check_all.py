#!/usr/bin/env python3
"""
Berean — run every check.

"Examine for yourself" is the whole claim, so it should be mechanical rather
than aspirational. This runs each dataset's own checker, verifies the library
holds together structurally, and confirms nothing has changed underneath the
recorded hashes.

    python3 scripts/check_all.py            # verify
    python3 scripts/check_all.py --update   # re-record the hashes after a rebuild

Exits non-zero if anything fails, so it can gate a commit or a deploy.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import berean_lib as lib   # noqa: E402

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
INTEGRITY = os.path.join(lib.LIB, "integrity.json")

CHECKERS = ["check_words_of_jesus.py", "check_threads.py", "check_ot_quotations.py"]

# Datasets whose contents are recorded, so a silent change is visible.
TRACKED = ["books.json", "manifest.json", "canons.json", "threads.json", "prayers.json",
           "crossrefs.json", "words-of-jesus.json", "ot-quotations.json",
           "corpus/BSB.json", "corpus/KJV.json", "corpus/WEB.json", "corpus/ENOCH.json"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_checkers():
    failed = []
    for name in CHECKERS:
        proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, name)],
                              capture_output=True, text=True)
        tail = [ln for ln in proc.stdout.strip().splitlines() if ln][-1:] or [""]
        print(f"{'ok  ' if proc.returncode == 0 else 'FAIL'}  {name:<28} {tail[0][:70]}")
        if proc.returncode != 0:
            failed.append(name)
            for ln in proc.stdout.splitlines():
                if "FAIL" in ln or "MISS" in ln:
                    print(f"        {ln}")
    return failed


def check_structure():
    """The library has to agree with itself: every version in the manifest has a
    bundle and shards, every shard book has a code, every canon entry Berean
    claims to host can actually be opened."""
    problems = []
    reg = {b["code"] for b in lib.registry()["books"]}

    for v in lib.versions():
        vid = v["id"]
        bundle = os.path.join(lib.CORPUS, f"{vid}.json")
        shards = os.path.join(lib.CORPUS, vid)
        if not os.path.exists(bundle):
            problems.append(f"{vid}: no bundle at corpus/{vid}.json")
            continue
        if not os.path.isdir(shards):
            problems.append(f"{vid}: not sharded — run scripts/shard_corpus.py")
            continue
        with open(os.path.join(shards, "index.json"), encoding="utf-8") as fh:
            index = json.load(fh)
        codes = [b["code"] for b in index["books"]]
        missing = [c for c in codes if c not in reg]
        if missing:
            problems.append(f"{vid}: codes not in books.json — {missing}")
        absent = [c for c in codes if not os.path.exists(os.path.join(shards, f"{c}.json"))]
        if absent:
            problems.append(f"{vid}: index lists books with no file — {absent}")
        with open(bundle, encoding="utf-8") as fh:
            nbundle = len(json.load(fh)["books"])
        if nbundle != len(codes):
            problems.append(f"{vid}: bundle has {nbundle} books, shards have {len(codes)}")

    with open(os.path.join(lib.LIB, "canons.json"), encoding="utf-8") as fh:
        canons = json.load(fh)
    for b in canons["books"]:
        if not b.get("hosted"):
            continue
        code = b.get("code")
        path = os.path.join(lib.CORPUS, b["hosted"], f"{code}.json")
        if not code or not os.path.exists(path):
            problems.append(f"canons.json claims to host {b['name']} in {b['hosted']}, "
                            f"but {code}.json is not there")

    for name in TRACKED:
        if not os.path.exists(os.path.join(lib.LIB, name)):
            problems.append(f"tracked dataset missing: {name}")

    print(f"{'ok  ' if not problems else 'FAIL'}  library structure          "
          f"{len(lib.versions())} versions, corpus + shards + canon links")
    for p in problems:
        print(f"        {p}")
    return problems


def integrity(update):
    recorded = {}
    if os.path.exists(INTEGRITY):
        with open(INTEGRITY, encoding="utf-8") as fh:
            recorded = json.load(fh).get("sha256", {})
    current = {n: sha256(os.path.join(lib.LIB, n)) for n in TRACKED
               if os.path.exists(os.path.join(lib.LIB, n))}
    if update:
        lib.write_json(INTEGRITY, {
            "note": ("SHA-256 of every dataset Berean hosts. Anyone can verify a copy of this "
                     "library is the copy that was published; the build scripts are in scripts/ "
                     "and every dataset can be rebuilt from its stated source."),
            "sha256": current,
        }, indent=1)
        print(f"ok    integrity                 recorded {len(current)} hashes")
        return []
    changed = [n for n, h in current.items() if recorded.get(n) and recorded[n] != h]
    new = [n for n in current if n not in recorded]
    print(f"{'ok  ' if not (changed or new) else 'FAIL'}  integrity                 "
          f"{len(current)} datasets hashed")
    for n in changed:
        print(f"        changed since last recorded: {n}  (rerun with --update if intended)")
    for n in new:
        print(f"        not yet recorded: {n}  (rerun with --update)")
    return changed + new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="re-record dataset hashes")
    args = ap.parse_args()

    print("Berean — checking the library\n")
    failed = run_checkers()
    problems = check_structure()
    drift = integrity(args.update)

    total = len(failed) + len(problems) + (0 if args.update else len(drift))
    print("\n" + ("all checks pass" if not total else f"FAILED — {total} problem(s)"))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
