# Audio narration & devotional media (Phase 9)

Berean can read Scripture aloud in two ways, in order of preference:

1. **Pre-rendered narration** — soothing, natural audio generated ahead of time
   with [Piper](https://github.com/rhasspy/piper) (open-source neural TTS) and
   served as small static MP3s. Identical quality for every listener, ~$0 to host.
2. **Browser voice (fallback)** — the device's built-in speech synthesis, used
   automatically wherever a chapter has no pre-rendered audio yet. The reader
   already picks the best available voice and reads at a calm pace.

The reader checks `library/audio/manifest.json` and uses a chapter's MP3 when one
exists; otherwise it falls back to the browser voice. So you can render a few
favorite chapters first and expand coverage over time — nothing breaks in between.

## Why pre-render?

The browser voice is free but its quality depends on the listener's device, and
it can't do SSML-style pacing. Pre-rendering once gives everyone the same warm,
consistent narration, costs effectively nothing to serve (static files), and is
the foundation for the devotional / prayer / sleep media below.

## One-time setup

```sh
pip install piper-tts                 # the TTS engine  (or use a `piper` binary)
sudo apt-get install ffmpeg           # Debian/Ubuntu   (macOS: brew install ffmpeg)
python3 scripts/tts_chapter.py --check
```

Download a **voice model** (a `.onnx` file + its `.onnx.json`) from the Piper
voices collection (`huggingface.co/rhasspy/piper-voices`). Soothing options:

| Voice | Character |
|-------|-----------|
| `en_US-lessac-medium` | clear, calm, neutral — a good default |
| `en_US-amy-medium` | warm, gentle female |
| `en_US-ryan-high` | rich, measured male |
| `en_GB-alba-medium` | soft British female |

Keep models in a local `voices/` folder (git-ignored — they're large).

## Rendering audio

```sh
# one chapter
python3 scripts/tts_chapter.py --model voices/en_US-lessac-medium.onnx \
    --version BSB --book John --chapters 3 \
    --voice-name "Lessac (Piper)" --license "MIT" \
    --attribution "Piper voice en_US-lessac-medium"

# a whole book
python3 scripts/tts_chapter.py --model voices/en_US-lessac-medium.onnx --book John --chapters all

# everything (long-running)
python3 scripts/tts_chapter.py --model voices/en_US-lessac-medium.onnx --all-books
```

Tuning for a meditative feel: `--length-scale 1.1` (higher = slower) and
`--sentence-silence 0.5` (seconds of pause between sentences) are the defaults;
raise them for an even calmer read. Use `--dry-run` to preview without synthesizing.

Output: `library/audio/<VERSION>/<bookIndex>/<chapter>.mp3` plus the manifest.

## Licensing (must-read)

- **Only render CC0 / public-domain texts.** The **BSB is CC0** — ideal for audio
  and video. Do not render copyrighted translations. See
  [03-texts-and-licensing.md](03-texts-and-licensing.md).
- **Each Piper voice has its own license.** Record it with `--license` /
  `--attribution` so the manifest carries it and the app can credit the voice.

## Roadmap: devotional & sleep media (next in Phase 9)

Building on this pipeline:

- **Devotional / prayer tracks** — pair a passage (CC0 Scripture) with *clearly
  labeled, original* encouragement (non-sectarian, sourced), mixed under
  **royalty-free / CC ambient** audio, rendered with `ffmpeg`.
- **Video** — the same audio over a still image or gentle Ken-Burns motion with
  on-screen text; batch-built to static MP4.
- **Sleep & encouragement playlists** — long, gapless, low-volume, fade in/out,
  timer/loop friendly.

Integrity rules: Scripture and human devotional text stay clearly separated and
sourced; only openly-licensed assets; attribute everything; never imply endorsement.
