#!/usr/bin/env python3
"""
Berean audio narration — generate soothing, pre-rendered Scripture audio ($0).

Uses Piper (open-source neural TTS) to synthesize a WAV per chapter, then ffmpeg
to encode a small static MP3. Output is plain files under library/audio/ plus a
manifest the reader uses to prefer real narration over the browser's built-in
voice. Because it is pre-rendered to static files, hosting cost is ~$0 and the
quality is identical for every listener regardless of their device.

Reproducible, stdlib only (it shells out to `piper` and `ffmpeg`). Nothing is
downloaded automatically — you point --model at a voice you have chosen.

QUICK START
    pip install piper-tts            # the TTS engine (or use a piper binary)
    sudo apt-get install ffmpeg      # or: brew install ffmpeg
    # download a soothing voice model (see docs/07-audio.md), e.g. en_US-lessac-medium
    python3 scripts/tts_chapter.py --check
    python3 scripts/tts_chapter.py --model voices/en_US-lessac-medium.onnx \
        --version BSB --book John --chapters 3
    # whole book:      --book John --chapters all
    # everything:      --all-books           (long-running)

The reader auto-detects library/audio/manifest.json and uses these files; where a
chapter has no audio yet, it falls back to the browser voice. So you can render a
few favorite chapters first and grow coverage over time.

LICENSING: only render CC0 / public-domain texts (the BSB is CC0 — ideal). Each
Piper voice has its own license; record it via --license / --attribution so the
manifest and player can credit it. See docs/03-texts-and-licensing.md + docs/07-audio.md.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "library")

RECOMMENDED = [
    "en_US-lessac-medium   — clear, calm, neutral (a good default)",
    "en_US-amy-medium      — warm, gentle female",
    "en_US-ryan-high       — rich, measured male",
    "en_GB-alba-medium     — soft British female",
]
VOICES_NOTE = ("Download voices from the Piper voices collection "
               "(huggingface.co/rhasspy/piper-voices); each model is a .onnx file "
               "plus a .onnx.json config beside it. Verify each voice's license.")


def find_piper(explicit):
    """Return a command list to invoke Piper, or None."""
    if explicit:
        return explicit.split()
    if shutil.which("piper"):
        return ["piper"]
    # fall back to the Python module form (only if the module actually imports)
    try:
        r = subprocess.run([sys.executable, "-m", "piper", "--help"],
                           capture_output=True, timeout=20)
        if r.returncode == 0:
            return [sys.executable, "-m", "piper"]
    except Exception:
        pass
    return None


def tool_status(args):
    piper = find_piper(args.piper_cmd)
    ff = shutil.which("ffmpeg")
    print("Piper :", " ".join(piper) if piper else "MISSING  (pip install piper-tts)")
    print("ffmpeg:", ff or "MISSING  (apt-get install ffmpeg  /  brew install ffmpeg)")
    print("\nRecommended soothing voices:")
    for v in RECOMMENDED:
        print("   ", v)
    print("\n" + VOICES_NOTE)
    return bool(piper) and bool(ff)


def load_version(version_id):
    with open(os.path.join(LIB, "corpus", f"{version_id}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def resolve_book(data, book_arg):
    """book_arg may be a 0-based index or a (case-insensitive) name."""
    if book_arg.isdigit():
        i = int(book_arg)
        if 0 <= i < len(data["books"]):
            return i
        sys.exit(f"book index {i} out of range (0..{len(data['books'])-1})")
    low = book_arg.strip().lower()
    for i, b in enumerate(data["books"]):
        if b["name"].lower() == low:
            return i
    sys.exit(f"book '{book_arg}' not found in {data['name']}")


def parse_chapters(spec, n):
    if spec in ("all", "*"):
        return list(range(1, n + 1))
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return sorted(c for c in out if 1 <= c <= n)


def load_manifest():
    path = os.path.join(LIB, "audio", "manifest.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {"engine": "piper", "voice": {}, "files": {}}


def save_manifest(m):
    os.makedirs(os.path.join(LIB, "audio"), exist_ok=True)
    with open(os.path.join(LIB, "audio", "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=2)


def synth_chapter(piper, model, text, out_wav, length_scale, silence):
    cmd = piper + ["--model", model, "--output_file", out_wav,
                   "--length_scale", str(length_scale),
                   "--sentence_silence", str(silence)]
    subprocess.run(cmd, input=text.encode("utf-8"), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def encode_mp3(wav, mp3, bitrate):
    subprocess.run(["ffmpeg", "-y", "-i", wav, "-codec:a", "libmp3lame",
                    "-b:a", bitrate, mp3], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    ap = argparse.ArgumentParser(description="Generate pre-rendered Scripture audio with Piper.")
    ap.add_argument("--check", action="store_true", help="report tool availability and exit")
    ap.add_argument("--dry-run", action="store_true", help="show what would be rendered, synth nothing")
    ap.add_argument("--version", default="BSB", help="corpus version id (default BSB, which is CC0)")
    ap.add_argument("--book", help="book name or 0-based index")
    ap.add_argument("--chapters", default="all", help="e.g. '3', '1-5', '1,3,5', or 'all'")
    ap.add_argument("--all-books", action="store_true", help="render every book (long)")
    ap.add_argument("--model", help="path to a Piper voice .onnx model")
    ap.add_argument("--voice-name", default="", help="human label for the voice (manifest)")
    ap.add_argument("--license", default="", help="the voice's license (manifest)")
    ap.add_argument("--attribution", default="", help="voice attribution text (manifest)")
    ap.add_argument("--length-scale", type=float, default=1.1, help=">1 = slower/calmer (default 1.1)")
    ap.add_argument("--sentence-silence", type=float, default=0.5, help="pause between sentences, seconds")
    ap.add_argument("--bitrate", default="96k", help="MP3 bitrate (default 96k)")
    ap.add_argument("--piper-cmd", default="", help="override the Piper invocation")
    args = ap.parse_args()

    if args.check:
        ok = tool_status(args)
        print("\n" + ("READY to render." if ok else "Install the missing tool(s) above, then re-run."))
        sys.exit(0 if ok else 1)

    data = load_version(args.version)
    books = range(len(data["books"])) if args.all_books else None
    if not args.all_books and not args.book:
        sys.exit("specify --book NAME|INDEX (or --all-books)")

    piper = None if args.dry_run else find_piper(args.piper_cmd)
    if not args.dry_run:
        if not args.model:
            sys.exit("--model PATH is required (see: python3 scripts/tts_chapter.py --check)")
        if not piper:
            sys.exit("Piper not found — pip install piper-tts (or pass --piper-cmd)")
        if not shutil.which("ffmpeg"):
            sys.exit("ffmpeg not found — install it, then re-run")
        if not os.path.exists(args.model):
            sys.exit(f"voice model not found: {args.model}")

    manifest = load_manifest()
    if not args.dry_run:
        manifest["engine"] = "piper"
        manifest["length_scale"] = args.length_scale
        manifest["sentence_silence"] = args.sentence_silence
        manifest["voice"] = {"name": args.voice_name or os.path.basename(args.model),
                             "model": os.path.basename(args.model),
                             "license": args.license, "attribution": args.attribution}
    files = manifest.setdefault("files", {})

    book_indices = list(books) if args.all_books else [resolve_book(data, args.book)]
    total = 0
    for bi in book_indices:
        book = data["books"][bi]
        chapter_nums = (list(range(1, len(book["chapters"]) + 1)) if args.all_books
                        else parse_chapters(args.chapters, len(book["chapters"])))
        for cn in chapter_nums:
            verses = book["chapters"][cn - 1]
            text = " ".join(v.strip() for v in verses if v and v.strip())
            rel = os.path.join("audio", args.version, str(bi), f"{cn}.mp3")
            abspath = os.path.join(LIB, rel)
            if args.dry_run:
                print(f"[dry-run] {book['name']} {cn}  ->  library/{rel}  ({len(text)} chars)")
                total += 1
                continue
            os.makedirs(os.path.dirname(abspath), exist_ok=True)
            with tempfile.TemporaryDirectory() as td:
                wav = os.path.join(td, "c.wav")
                synth_chapter(piper, args.model, text, wav, args.length_scale, args.sentence_silence)
                encode_mp3(wav, abspath, args.bitrate)
            (files.setdefault(args.version, {}).setdefault(str(bi), {}))[str(cn)] = {
                "path": rel.replace(os.sep, "/"), "bytes": os.path.getsize(abspath)}
            total += 1
            print(f"  rendered {book['name']} {cn}  ({os.path.getsize(abspath)//1024} KB)")

    if not args.dry_run:
        save_manifest(manifest)
        print(f"\nDone: {total} chapter(s). Manifest: library/audio/manifest.json")
    else:
        print(f"\n[dry-run] {total} chapter(s) would be rendered.")


if __name__ == "__main__":
    main()
