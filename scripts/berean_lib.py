#!/usr/bin/env python3
"""Shared helpers for Berean's build scripts: the book registry and corpus access."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "library")
CORPUS = os.path.join(LIB, "corpus")

_books = None


def registry():
    global _books
    if _books is None:
        with open(os.path.join(LIB, "books.json"), encoding="utf-8") as fh:
            _books = json.load(fh)
    return _books


def code_for(name):
    """Book code for a display name, code, or known alias. None if unknown."""
    return registry()["resolve"].get(str(name).strip().lower())


def name_for(code):
    for b in registry()["books"]:
        if b["code"] == code:
            return b["name"]
    return code


def order_of(code):
    for b in registry()["books"]:
        if b["code"] == code:
            return b["order"]
    return 10_000


def load_bundle(version):
    """The whole-version file. Kept for search, offline download, and builders."""
    with open(os.path.join(CORPUS, f"{version}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def books_by_code(version):
    """{code: {"name":…, "chapters":[[verse,…],…]}} for a version."""
    out = {}
    for b in load_bundle(version)["books"]:
        code = code_for(b["name"])
        if not code:
            raise SystemExit(f"{version}: no code for {b['name']!r} — add it to build_books.py")
        out[code] = b
    return out


def versions():
    with open(os.path.join(LIB, "manifest.json"), encoding="utf-8") as fh:
        return json.load(fh)["versions"]


def write_json(path, data, indent=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        if indent:
            json.dump(data, fh, ensure_ascii=False, indent=indent)
            fh.write("\n")
        else:
            json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
