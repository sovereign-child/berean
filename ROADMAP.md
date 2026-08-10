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
- *Follow-ups:* add WEB / more PD versions; **Nave's Topical Bible** (topic→verse) —
  no clean open dataset found yet, needs sourcing; **semantic/meaning search** (later,
  client-side embeddings); per-book split + prebuilt index if load size grows.

## Phase 2 — Original-language study layer 🟢 (effort: L) ← the differentiator
The highest-value, fully-open capability (what closed tools charge for).
- Ingest **OpenScriptures Hebrew (WLC + morphology, CC BY)**, **STEPBible
  TAHOT/TAGNT (CC BY)**, **SBLGNT critical Greek (CC BY)**, **Strong's (PD)**.
- **Interlinear** alignment + **morphology** + **Strong's / lexicon** word study.
- **DoD:** tap any word in a verse → lemma, morphology, Strong's number, gloss;
  interlinear available for the Hebrew OT and the Greek NT.

## Phase 3 — The wider canon & the "lost books" 🟢🔴 (effort: M)
Berean's distinctive: the wider canon, openly and non-sectarianly.
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
