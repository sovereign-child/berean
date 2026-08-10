# Berean — Roadmap

The canonical plan of record. It integrates the vision (five pillars), the
open-data landscape research, the licensing/canon constraints, the lean hosting
model, and the generous stewardship model. Build **corpus-first, one pillar at a
time**; every phase ends with a working artifact.

See also: [vision](docs/01-vision.md) · [architecture](docs/02-architecture.md) ·
[texts & licensing](docs/03-texts-and-licensing.md) ·
[preservation](docs/05-preservation-and-integrity.md) ·
[hosting & stewardship](docs/06-hosting-and-stewardship.md) ·
[dedication](DEDICATION.md).

## Principles that gate every phase

- **Licensing discipline** — only public-domain / openly-licensed texts are hosted;
  copyrighted translations are linked or API-accessed, never hosted. Every text has
  a manifest entry (edition, language, tradition, `canon_status`, source, license).
- **Non-sectarian by construction** — label canon by tradition; present ranges, not
  one enumeration; source all evidence and mark consensus vs debate vs faith.
- **Lean & resourceful** — open data + free tooling + the **AWS server we already
  have**; keep the footprint small; defer the only paid pieces (Arweave, domain).
- **Free to users, generous back** — free forever; support (when it comes) covers
  costs, grows the community, and gives back. Funding never buys editorial influence.
- **Ship value each phase** — each phase has a definition of done (DoD).

## Legend
🟢 buildable now on open data · 🟡 needs a licensed API · 🔴 hard/contested or
paid/deferred · effort: S / M / L

---

## Phase 0 — Foundation ✅ (done)
Vision, dedication, texts-&-licensing, architecture, preservation & hosting/
stewardship docs; repo + private remote (`sovereign-child/berean`).

## Phase 1 — The Library MVP 🟢 (effort: M) ✅ **SHIPPED (2026-08-09)**
The reading foundation, on open data only.
- ✅ Normalized **corpus schema** (`version → book → chapter → verse`) + `library/manifest.json`.
- ✅ Reproducible ingest pipeline (`scripts/ingest.py`, stdlib-only) → **Berean
  Standard Bible (CC0)** + **King James Version (PD)**, normalized to 66 books /
  ~31,100 verses each (validated: Genesis 1 = 31 verses, Psalms = 150 chapters).
- ✅ Dependency-free reader (`web/`): read a chapter, **switch version**,
  **side-by-side compare**, and **search within a version** — verified serving +
  read/search/compare against the real corpus.
- ✅ Self-hostable (AWS box or any static host); attributions shown per the licensing manifest.
- **DoD met** for 2 open versions (BSB + KJV).

### Phase 1.5 — Study tools 🟢 ✅ **SHIPPED (2026-08-09)**
Built on the Library, all client-side / $0:
- ✅ **Permalinks** — every location is a shareable URL (`#/VERSION/Book/ch/verse`); + **copy verse** (with reference) and **copy link**.
- ✅ **Saved study (localStorage, private)** — highlight (4 colors), per-verse notes,
  and named **collections**; **Export / Import** JSON to move study between devices.
- ✅ **Related verses** — a cross-reference panel from the **OpenBible.info** dataset
  (CC BY, 29,319 verses / 323k links, ingested by `scripts/ingest_crossrefs.py`).
- ✅ **Better search** — search one version or **all versions**, whole-word ranking, highlighted snippets.
- ✅ **Remembered preferences** — your version, compare version, and search scope
  persist across visits (`localStorage`); a shared permalink still overrides them.
- ✅ **Share & listen (icon actions)** — native **Share** sheet (falls back to copy)
  and **Read aloud** (offline text-to-speech) at both verse and chapter level;
  chapter **share / copy-link** in the chapter toolbar. Icons are inline SVG (no
  icon fonts / CDNs — fully offline & CSP-safe).
- ✅ **Passage selection** — Shift-click a second verse number to select a **range**;
  highlight / note / save / copy / share / read-aloud act on the whole passage.
- ✅ **Reading comfort** — **dark mode** + **text-size** controls, remembered across visits.
- ✅ **Voice picker + soothing cadence** — choose any device voice (auto-prefers
  higher-quality *neural* voices when present, ★-marked), slower measured rate, and
  gentle pauses between verses. *This is the free, in-browser baseline; the premium
  narration path is Phase 9.*
- ✅ **Prayer builder** — compose personalized prayers by subject (12 themes),
  for yourself or someone by name, with an optional situation woven in; Guided/Simple
  structure and Contemporary(BSB)/Traditional(KJV) wording. Scripture is quoted **live
  from the corpus** (references verified to resolve; never fabricated) and the result
  lands in an **editable** box — make it your own. Read aloud (soothing voice), copy,
  share, and **save** (rides along in the My Study export). Data: `library/prayers.json`
  (references + non-sectarian connective phrasing; clearly a scaffold, not a fixed form).
- *Follow-ups:* add WEB / more PD versions; **Nave's Topical Bible** (topic→verse) —
  no clean open dataset found yet, needs sourcing; **semantic/meaning search** (later,
  client-side embeddings); per-book split + prebuilt index if load size grows.

### Phase 1.6 — Commentary layer 🟢 **STARTED (2026-08-10)**
Multiple faithful voices on a passage — the most "Berean" study upgrade (examine &
compare, not one verdict) and the **sourced ground truth the AI layer will cite**.
- ✅ **Pipeline + reader panel** — `scripts/ingest_commentary.py` vendors openly-licensed
  commentaries from **HelloAO's Free Use Bible API** into `library/commentary/…` +
  a manifest; the reader's **Commentary** panel (📖 in the chapter toolbar) lazy-loads
  per chapter, lets you switch between works, links each block back to its verse, and
  shows license/attribution. Public-domain: **Matthew Henry, Jamieson-Fausset-Brown,
  Adam Clarke, John Gill, John Calvin, Keil-Delitzsch (OT)**; plus **Tyndale Open Study
  Notes (CC BY-SA 4.0)**.
- ✅ **Shipped data:** Matthew Henry + JFB for the Gospel of John. *Expand with
  `--all-books` / more commentaries as desired.*
- *Follow-ups:* ingest more books/works; AI "compare what the commentators say" (Phase 10).

## Phase 2 — Original-language study layer 🟢 (effort: L) ← the differentiator
The highest-value, fully-open capability (what closed tools charge for).
- Ingest **OpenScriptures Hebrew (WLC + morphology, CC BY)**, **STEPBible
  TAHOT/TAGNT (CC BY)**, **SBLGNT critical Greek (CC BY)**, **Strong's (PD)**.
- **Interlinear** alignment + **morphology** + **Strong's / lexicon** word study.
- **DoD:** tap any word in a verse → lemma, morphology, Strong's number, gloss;
  interlinear available for the Hebrew OT and the Greek NT.

## Phase 3 — The wider canon & the "lost books" 🟢🔴 (effort: M) — **STARTED (2026-08-10)**
Berean's distinctive: the wider canon, openly and non-sectarianly.
- ✅ **1 Enoch (R.H. Charles, 1917, Public Domain)** ingested (`scripts/ingest_enoch.py`
  from Project Gutenberg #77935) → `library/corpus/ENOCH.json`, 108 chapters / 1,012
  verses, selectable in the reader and **clearly labeled** (`tradition: Pseudepigrapha`,
  `canon_status`: non-canonical in most traditions, canonical in Ethiopian Tewahedo,
  quoted in Jude 14-15). Canonical-only features (cross-refs, commentary) are guarded
  off for non-canonical texts.
- ✅ **Threads** — a "follow the documented trail" feature (🧵 in the header). Each step
  is a **real, resolving citation** across the canon *and* the wider canon, with a
  status badge (consensus / debate / textual / extra-biblical) and sources; Berean
  presents, it does not decide. First thread: **The Divine Council & the Watchers**
  (Ps 82 → 1 Kings 22 → Job 1 → Deut 32:8 [DSS/LXX variant] → Gen 6 → 1 Enoch 6/10 →
  2 Peter 2 / Jude 6 / Jude 14-15 quoting Enoch → Ps 82:6-7). Data: `library/threads.json`.
- *Follow-ups:* **Jubilees** (no clean PD machine-readable source found yet — staged;
  cited by reference only for now), more pseudepigrapha, deuterocanon; more Threads.
- Ingest the deuterocanon/apocrypha and pseudepigrapha (**R.H. Charles 1913, PD** —
  verify actual contents + OCR quality first; seek cleaner open sources too).
- Label `canon_status` per tradition (Protestant 66 / Catholic 73 / Orthodox /
  Ethiopian Tewahedo 81 / Jewish Tanakh), **with the honesty note that enumerations
  aren't fixed to one list** (🔴 sensitivity — present ranges/traditions fairly).
- A **canon-comparison view**.
- **DoD:** browse the wider canon with clear tradition labels and a fair
  canon-comparison; every book in the manifest with its per-tradition status.

## Phase 4 — The Evidence layer 🟢🔴 (effort: L)
"See if these things were so."
- **Manuscript viewer** linking (not rehosting) the **Codex Sinaiticus Project**
  and the **Leon Levy Dead Sea Scrolls Digital Library**.
- **Verse-level textual variants** with witnesses (using TAGNT edition markers +
  the famous cases: Mark 16:9–20, John 7:53–8:11, 1 John 5:7).
- Archaeology / historical context — **sourced**, each labeled consensus / debate /
  faith (🔴 avoid scholarly overreach).
- **DoD:** for a passage, see key variants + linked manuscript imagery + sourced,
  fairly-labeled historical context.

## Phase 5 — Copyrighted translations via licensed APIs 🟡 (effort: S–M)
Optional pass-through so readers can use popular modern versions.
- Integrate **Crossway ESV API** and **API.Bible** (NIV/NASB/NLT/CSB…) as
  reference-only pass-throughs — **re-verify current terms**, respect quotas &
  attribution, never host the text.
- **DoD:** read a copyrighted version via API with proper attribution and within
  quota, clearly separated from hosted open texts.

## Phase 6 — Sermon Studio 🟢 (effort: L) — **gated on a ministry-landscape study**
> First run a focused follow-up research on the ministry/tooling gap (Logos,
> BibleHub, Blue Letter Bible, STEP, Sefaria, sermon-prep tools) — the landscape
> research under-covered this. Scope this pillar from evidence.
- Topic/passage → gathered references & parallels, original-language notes (Phase 2),
  public-domain commentary, historical context (Phase 4) → outline, key points,
  illustrations → export (handout / slides / manuscript).
- **DoD:** build and export a sermon/lesson from a topic, drawing on Phases 1–4.

## Phase 7 — Church Operations 🟢 (effort: L) — same research gate; uses the AWS box
Open, self-hostable operations + community (the dynamic pillar).
- Members/households, small groups, volunteer scheduling, events/calendar,
  communications, sermon/teaching archive tied to the Library.
- Giving/tithing only via **compliant third-party integrations**, later — Berean
  never handles raw funds.
- **DoD:** a church can manage members/groups/events and archive sermons on a
  self-hosted instance.

## Phase 8 — Preservation & integrity 🔴 (effort: M, **paid — deferred**)
Censorship-resistant permanence (funded by stewardship first).
- Content-address the corpus (**IPFS**) + **Arweave** permanence (costs money) +
  **on-chain Merkle-root integrity anchors**; verify-by-hash; append-only/versioned;
  many editions with provenance (never "one true text"); **no token**.
- **DoD:** any hosted edition is content-addressed, anchored, and independently
  verifiable, with CC-BY attribution preserved.

## Phase 9 — Audio, prayer & devotional media 🟢🟡 (effort: L) — **STARTED (2026-08-10)**
Great, *soothing* narration of Scripture, plus devotional audio/video that links
Scripture to encouragement — to listen through the day or while falling asleep.
- ✅ **Pipeline built** — `scripts/tts_chapter.py` (Piper → ffmpeg → static MP3 +
  `library/audio/manifest.json`) with `--check` / `--dry-run`; the reader prefers
  pre-rendered narration and falls back to the browser voice per-chapter. See
  [docs/07-audio.md](docs/07-audio.md). *Awaiting local Piper + ffmpeg install to
  render actual audio.*
- **Premium narration** (beyond the browser's built-in voices):
  - 🟢 **Free / self-hosted:** batch-generate audio with **Piper** (open-source
    neural TTS, runs locally, permissive license) → serve as **static MP3** per
    chapter. Marginal cost ~$0; fits the static-hosting model.
  - 🟡 **AWS-native (we already have the box):** **Amazon Polly Neural** voices,
    generated **once to static files** (not per-request) so cost is tiny + bounded.
  - Both keep to **CC0 / public-domain** text (the BSB is CC0 — clean for audio).
- **Devotional / prayer media:** short pieces that pair a passage with original,
  clearly-labeled encouragement (non-sectarian, sourced), mixed with **royalty-free
  / CC ambient audio**, rendered to audio and optionally **video** (still or gentle
  motion) via **ffmpeg** — all batch-built to static files.
- **Sleep & encouragement playlists**: gapless, low-volume, timer/loop friendly.
- **Licensing gates:** audio may only use CC0/PD Scripture + royalty-free music +
  original devotional text; attribute everything; never imply endorsement.
- **DoD:** a listener can play a chapter in a warm, natural voice, and play a
  looping devotional/prayer track built entirely from openly-licensed assets.

## Phase 10 — Grounded AI study layer 🟡 (effort: L) — **the vision (2026-08-10)**
Make Berean the greatest tool for *understanding* the Bible — AI as a guide **to**
the sources, never a replacement for them. **Non-negotiable guardrails:**
retrieval-grounded on the open corpus + commentaries + lexicons; **every claim
cited**; **cite-or-refuse** (say "the text doesn't say" rather than invent);
**non-sectarian** (show the range where traditions differ); Scripture always primary
and clearly separated from commentary; and it is always labeled a **study aid, not an
authority**. **$0 for the project:** default to **bring-your-own-API-key** (user pays
their own usage), **precompute embeddings to static files** (semantic search free at
runtime), self-host open-weight models on the AWS box later.

Top-10 features (ranked by impact on understanding):
1. **Grounded AI study companion** — natural-language Q&A built only from the open
   texts, every claim linked to its source; cite-or-refuse. *(flagship)*
2. **Original-language word study** (Phase 2) with AI nuance grounded in the lexicon.
3. **Multi-voice commentary + AI comparison** (Phase 1.6) — summarize agreement/difference.
4. **Semantic ("meaning") search** — precomputed embeddings; $0 at runtime; offline.
5. **Passage context cards** — author/audience/date/genre/context, labeled consensus/debate/faith.
6. **"Why do the translations differ here?"** — grounded in variants + lexical data.
7. **AI-curated topical + cross-reference graph** — clusters themes, explains the thread
   (responsibly fills the Nave's-Topical gap; suggested + cited + reviewable).
8. **Reading plans + AI study guide** — summaries & discussion questions (feeds Sermon Studio).
9. **Manuscript & textual-variant viewer, explained** (Phase 4) in plain, sourced language.
10. **Active learning** — spaced-repetition memorization, journaling, and an AI tutor that
    quizzes comprehension and checks understanding.

**Build order (recommended):** build the sources the AI cites *first* — **commentary
layer (✅ started) + semantic search** — then the **grounded companion** on top, so
every answer is grounded and honest from day one.
- **DoD (flagship):** ask a question, get a grounded, **cited**, non-sectarian answer
  drawn only from the open texts, with a clear "not covered" when sources are silent.

---

## Continuous (not a phase) — Community & Stewardship
- Contribution & moderation norms ([CONTRIBUTING](CONTRIBUTING.md)), i18n, and a
  learning community throughout.
- Funding ladder: **GitHub Sponsors** → **fiscal host** (when money flows) → own
  501(c)(3) only at scale. Transparent ledger; give back (open translation for
  unreached languages, free tools for under-resourced churches, contributor grants).

## The sequence in one line
**Foundation ✅ → Library → Original languages → Wider canon → Evidence →
(API translations) → [ministry research] → Sermon Studio → Church Ops →
Preservation** — with community + stewardship woven through all of it.

## Top risks & mitigations
- **Copyright** → manifest + PD/CC-BY-only hosting + API pass-through; re-verify API terms.
- **Sectarian bias** → label by tradition, present ranges, funding buys no influence.
- **Scholarly overreach** → source everything; consensus/debate/faith labels.
- **Cost creep** → lean on the AWS box + open data; defer Arweave/domain; stewardship funds growth.
- **Scope sprawl** → corpus-first, one pillar at a time; ministry pillars gated on research.
