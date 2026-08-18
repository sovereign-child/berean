# The library: how it is built, and the rules it follows

*Written 2026-08-18, after the work described in ROADMAP Phase 3 + Foundations.*

This is the engineering reference for `library/` and `scripts/`. It exists because
most of what Berean now does is **derived** — computed from open texts by scripts in
this repo — and derived data is only trustworthy if the method is written down, the
result is checked, and the failure modes are stated rather than discovered later by
a reader.

If you are extending the library, read the five rules first. They are load-bearing.

---

## The five rules

### 1. One address for everything

`library/books.json` is the registry. Every dataset keys on its book codes — USFM
where USFM defines one, `standard: "berean_ext"` where it does not (1 Enoch,
Jubilees). **A verse address is `CODE.CHAPTER.VERSE`**: `JHN.3.16`, `TOB.3.16`.

This replaced two older schemes and both had already caused real bugs:

- Cross-references were keyed to a book's *position in the Protestant 66*, so a
  cross-reference could not point at Tobit even in principle.
- Everything else keyed on *display names*, so switching from a 66-book Bible to an
  81-book one landed you in a different book at the same index, and renaming a book
  would have silently orphaned every highlight a reader had saved.

Readers' saved study lives under the same addresses and migrated once, in place
(`migrateStore()` in `web/app.js`), leaving the v1 record untouched.

### 2. Offsets, never copies

A derived layer stores **character offsets into a corpus**, not a copy of the text.
`words-of-jesus.json` is 71 KB rather than a megabyte, partial verses render exactly
(Luke 15:11 shows only the spoken half), and the layer **cannot drift** from the
translation it describes. Do this for anything new that points at text.

### 3. Derive, don't assert — and therefore check

Where a fact could be copied from a reference book or computed from the texts,
compute it. An asserted table cannot be verified; a derived one can, and must be.

`library/versification.json` is the clearest case: rather than copy a Septuagint/
Masoretic chapter table, `build_versification.py` matches each Greek chapter against
the Hebrew-based chapter it most shares distinctive wording with, and
`check_versification.py` confirms the result reproduces the 20 correspondences
scholarship documents independently.

The exception is a genuinely editorial judgment, which gets **curated** and marked as
such: `canons.json`, the ten hand-listed passages in the Words of Jesus, the Threads.
Curated entries carry a reason.

### 4. Every dataset: a builder, a checker, a manifest entry, a hash

    scripts/build_*.py  or  ingest_*.py     produces it
    scripts/check_*.py                      verifies it
    library/manifest.json                   records source, licence, attribution
    library/integrity.json                  records its SHA-256

`scripts/check_all.py` runs every checker, verifies the library agrees with itself,
and compares hashes. CI runs it on every push, **then rebuilds the derived layers and
fails if the output differs from what is committed**. That last step caught real
nondeterminism on its first run: tied scores in the quotation builder were being
resolved by set iteration order, so the same input produced a slightly different file
each run. Ties now break canonically.

### 5. Shard for reading, bundle for search

    corpus/BSB.json          the whole version — search, offline download, builders
    corpus/BSB/index.json    metadata + verse counts per chapter (~6 KB)
    corpus/BSB/JHN.json      one book, fetched when opened

First load went from 3,920 KB to 273 KB. The index carries verse counts so the menus
can be drawn without fetching a book. Cross-references shard the same way, one file
per book.

---

## What is in the library

| File | Built by | Checked by | Notes |
|---|---|---|---|
| `books.json` | `build_books.py` | (validates on build) | 86 books; every hosted book must resolve |
| `corpus/{BSB,KJV,WEB,LXX,ENOCH,JUBILEES}.json` | `ingest_*.py` | `check_all.py` | + per-book shards from `shard_corpus.py` |
| `crossrefs/` | `shard_crossrefs.py` | `check_all.py` | openbible.info, CC BY; 66-book canon only |
| `commentary/{id}/{CODE}/{n}.json` | `ingest_commentary.py` | — | HelloAO API, PD works |
| `words-of-jesus.json` | `build_words_of_jesus.py` | `check_words_of_jesus.py` | 542 passages / 1,753 verses |
| `ot-quotations.json` | `build_ot_quotations.py` | `check_ot_quotations.py` | 180 quotations, 72 echoes |
| `versification.json` | `build_versification.py` | `check_versification.py` | 179 chapters differ, 7 books |
| `canons.json` | curated | `check_all.py` | 19 disputed books × 5 traditions |
| `threads.json` | curated | `check_threads.py` | every citation must resolve |
| `integrity.json` | `check_all.py --update` | `check_all.py` | SHA-256 of 15 datasets |

Six hosted texts: **BSB** (CC0), **KJV**, **WEB with Deuterocanon** (81 books),
**Brenton's Septuagint** (1851), **1 Enoch** and **Jubilees** (Charles). All public
domain or CC0. Nothing copyrighted is hosted — see `docs/03`.

---

## The derived layers, and how they fail

### The Words of Jesus

Compiled from the **BSB's own quotation marks**. No red-letter dataset was licensed.

Two structural facts make it work: BSB reserves `“ ”` for the outermost level of
speech and nests with `‘ ’`, so speech is a **boolean state, not a depth counter**;
and speeches cross chapter boundaries (the Sermon on the Mount is one quotation from
Matthew 5:3 to 7:27), so each book is scanned as one stream.

Attribution reads **only the narrator's clause**, with all quoted material stripped
out first. Every bug found in this parser had the same consequence — someone else's
words in His mouth — and any change here should be tested against all of them:

| Failure | Example | Rule that fixes it |
|---|---|---|
| Object read as subject | "He came **to Jesus** … and said" | a name after a preposition is where the speech *went* |
| Two people in one clause | "**John** saw **Jesus** … and said" | English is subject-first: earliest candidate wins |
| Trailing clause claimed by the wrong quote | "…?" **Jesus asked.** "Seven," they replied | a finished sentence attributes the quote *before* it; a clause ending in a comma introduces the one *after* |
| Fall-through after a named speaker | "…old?" **Nicodemus asked.** | a named non-Jesus speaker settles it — never fall back to the previous quote's clause |
| Missing speech verb | "dared to **ask** Him," | keep the verb list current, or it silently falls through |
| Inheritance across a gap | "…?" / "From childhood," **he said.** | a quote with its own trailing attribution does not inherit |
| Passive voice | "He **was told**," | names who was spoken *to* |

Unattributed speech is **left out**, not guessed: 1,119 quotations are omitted. Ten
passages that name their speaker from inside ("I am Jesus, whom you are persecuting")
are curated with reasons. Revelation is curated whole, because a vision changes
speaker with no narrator at all. **The Father's voice is labeled separately and never
folded in** — red-letter editions disagree, and Berean does not decide.

The checker holds 27 landmark passages, 10 phrases the text gives to someone else
(checked against what passages *quote*, since a verse can hold both voices), and an
offset-integrity pass.

### The Old Testament in the New

Every NT verse is compared against an index of every four-word sequence in the OT, in
one translation carrying both.

The two things that had to be right: **weighting** (a sequence is worth what it can
identify — "the angel of the LORD" identifies nothing, but a hard rarity cutoff threw
away Romans 10:13, which is Joel 2:32 word for word in common phrases, so sequences
are weighted by how many verses they appear in); and **reach** (a citation formula
introduces the verse under it, not the paragraph around it — two verses of reach let
"to fulfill what the prophet said" in Matthew 1:22 label the genealogy either side).

**Quotations and echoes are kept apart.** A quotation is marked as Scripture by the
writer or overlaps heavily; an echo is overlap with no formula.

**Known blind spot, stated in the data:** the NT quotes the Greek while an English OT
renders the Hebrew, so where the two traditions word a verse differently there is
nothing to match on. Three landmark quotations that fall in that gap are named in the
checker as known limitations rather than quietly dropped. *This is the same phenomenon
the Greek Old Testament thread is about.*

### Versification

Brenton follows the Greek: Psalm 23 is Psalm 22, Jeremiah 25:15 is Jeremiah 32:15,
Esdras B is Ezra and Nehemiah as one book. Three passes were needed:

1. Matching within a book forced Ezra's last 13 chapters to find something in Ezra.
2. Searching every book found Psalms in Romans and Joel in Acts — those are
   quotations, not renumbering. Targets are Old Testament only.
3. Parallel passages (Samuel and Chronicles telling one story) still looked like
   renumbering, so a difference must clearly beat the chapter of the same number.

Chapters the method cannot place are `unplaced`, **not** "no counterpart" — usually
they are simply short. Psalm 151 genuinely has none, and that is recorded as the
documented fact it is.

The reader shows the other numbering in the chapter header, warns in compare mode,
and marks the 328 verse slots (1%) where the Greek has nothing to put. Those slots
are kept rather than renumbered away.

---

## How the reader loads

1. `manifest.json` + `books.json` (small).
2. The version's `index.json` — metadata and verse counts, enough to draw the menus.
3. The opened book's shard.
4. Layers, only when they could apply: the Words of Jesus and OT quotations when a
   **New Testament** book is opened; versification when a Greek-numbered text is in
   play; cross-references for the book being read; the search bundle only on search.

Panels are routes (`#/panel/threads/abrahams-two-sons`), so Back closes them and a
thread can be linked to. A service worker precaches the shell and keeps whatever is
read; Scripture is served cache-first and refreshed behind the reader, the app's own
files network-first so updates land.

---

## Deployment

Static. **The site must be served from the repo root** — `web/` fetches `../library/`,
and the root `index.html` redirects to `web/`. Publishing `web/` alone breaks it, and
that is the most likely deploy failure.

- **GitHub Pages** (`.github/workflows/deploy-pages.yml`) runs `check_all.py` before
  publishing. Pages stamps `Cache-Control: max-age=600` and offers no configuration,
  so `no-cache` on `index.html`/`sw.js` is unreachable there. In practice this is
  tolerable: browsers bypass the HTTP cache for the service worker script itself
  during update checks, so the exposure is a ≤10 minute stale window on the HTML.
- **S3 + CloudFront** (`scripts/deploy_s3.sh`) verifies first, then syncs with the
  headers that matter. Compression is not optional — the corpus is JSON and
  compresses about 4:1.
- Service workers require a **secure context**. While a custom domain's certificate
  is still being issued, the site is HTTP-only and offline support is simply absent —
  it switches itself on when HTTPS is valid, with no code change.

---

## Adding a text

1. Find an open source. Prefer **structured** over scanned: the blocker on Jubilees
   was never the licence — Charles 1917 has always been public domain — it was that
   every copy was OCR or wrapped in someone's site, until Sefaria's API turned out to
   publish it with chapter and verse intact.
2. Write `scripts/ingest_*.py`. Verify the licence *in the script* and refuse to
   write if it does not match (see `ingest_jubilees.py`, `ingest_brenton.py`).
3. Add any missing codes to `build_books.py`.
4. Run `shard_corpus.py`, add the file to `TRACKED` in `check_all.py`, run
   `check_all.py --update`.
5. If its numbering differs, rebuild `versification.json` and say so in the metadata.
6. Update `canons.json` if a tradition receives it, and `docs/03`.

## Adding a derived layer

Same shape: a builder that stores **offsets**, a checker with landmarks *and*
negative cases, an entry in `TRACKED`, and a note in the data stating the method and
what it cannot see. If the output is not byte-identical across runs, fix the ordering
— CI will catch it, but it is your bug.
