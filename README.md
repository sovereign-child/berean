# Berean — Study the Word

> *"Now the Berean Jews were of more noble character than those in Thessalonica,
> for they received the message with great eagerness and **examined the Scriptures
> every day to see if what Paul said was true.**"* — Acts 17:11

**Berean** is an open, community-driven **research and study tool for the Holy
Bible** — and a toolkit for the churches and ministers who teach it. It exists to
help anyone study Scripture deeply and honestly: across every translation and the
original languages, alongside the historical and manuscript evidence, in a
community that examines and verifies rather than merely repeats.

The name is the mission: the Bereans were commended not for believing quickly but
for *searching the Scriptures* to see whether things were so. Berean is built to
make that kind of study possible for everyone.

**Home: [bereanlamp.com](https://bereanlamp.com)** — *"Your word is a lamp to my
feet and a light to my path."* (Psalm 119:105)

> **Please begin with the [Dedication & the story of the name](DEDICATION.md)** —
> to whom this work is dedicated (the Most High), why it is called *Berean*, and
> the people across history whom we honor for studying, preserving, and carrying
> the Word.

## The five pillars

1. **The Library** — every version and translation (public-domain texts hosted
   directly; copyrighted ones via licensed APIs), the **original languages**
   (Hebrew, Aramaic, Greek) with lexicons and interlinears, and the **wider canon**:
   the apocryphal / deuterocanonical books and the "lost" books (Enoch, Jubilees,
   the pseudepigrapha, the non-canonical gospels), each clearly labeled by the
   tradition that receives it.
2. **The Evidence** — the manuscript and historical record: the Dead Sea Scrolls,
   the great codices, papyri and textual variants, archaeology, and historical
   context — presented with sources so readers can weigh it themselves.
3. **Study & Community** — reading plans, topical and word study, cross-references
   and concordance, and a place for people to learn together in the Berean spirit.
4. **Sermon Studio** — tools for priests and pastors to build sermons by topic or
   passage: gather cross-references, commentary, original-language notes, historical
   context, outlines, and illustrations, and export a finished study.
5. **Church Operations** — open, self-hostable tools to help a church run its
   operations and shepherd its community (members, groups, events, communications,
   sermon archive) without surrendering its data to a closed platform.

## Convictions that shape the design

- **Examine, don't just assert.** Every historical or textual claim is sourced;
  the tool helps you check it, as the Bereans did.
- **Non-sectarian by construction.** Protestant, Catholic, and Orthodox traditions
  differ on canon and translation. Berean *presents* those differences plainly and
  lets the reader see them, rather than taking a side.
- **Reverence and rigor together.** Faithful to the text, honest about the scholarship.
- **Open and ownable.** Free, open-source, and self-hostable so churches and
  students own their tools and data.

## Status

**The reader works, and it does things no free Bible app puts together.** A
dependency-free reader in [`web/`](web/) — no framework, no CDN, no analytics, no
account — over four hosted texts: the **Berean Standard Bible** (CC0), the **King
James Version**, the **World English Bible with Deuterocanon** (81 books), and
**1 Enoch** (Charles, 1917). Run it with `./serve.sh` → open `/web/`.

What is in it now:

- **Read, compare, and search** — two versions side by side, and search scoped to
  this version, every version, **the words of Jesus**, the disputed books, or
  Berean's own notes.
- **📜 Canon** — who receives which book, across five traditions, with every
  hosted book one click away. Nothing was subtracted from one original Bible, and
  the table says so — along with the one case that is real.
- **✝ The Words of Jesus** — 542 passages, 1,753 verses, every passage He speaks
  in canonical order, plus red letters while you read. Compiled from the BSB's own
  quotation marks; the Father's voice is labeled separately, never folded in.
- **The Old Testament in the New** — 180 quotations and 72 echoes, found by
  matching the testaments against each other, shown under the verse you are reading.
- **🧵 Threads** — documented trails through Scripture and the wider canon, every
  citation resolving in the app, each step labeled consensus / debate / textual /
  extra-biblical. Berean presents; it does not decide.
- **🙏 Prayer builder** and **✦ My Study** — highlights, notes and collections kept
  in your browser, with shareable permalinks and Export / Import.
- **Offline** — it keeps working with no network, and installs to a home screen.

Every dataset has a build script and a checker, and
[`scripts/check_all.py`](scripts/check_all.py) runs all of them: every citation in
every thread resolves against the actual corpus, every landmark passage carries
the voice it should, and the SHA-256 of all twelve datasets is recorded so a
silent change is visible. CI runs it on every push, then rebuilds the derived
layers and fails if they differ from what is committed.

Next up (per the [roadmap](ROADMAP.md)): the original-language study layer.
Earlier phases (vision, dedication, texts-&-licensing, architecture,
preservation, stewardship) remain below.

## Read next

- [docs/01-vision.md](docs/01-vision.md) — the pillars in depth
- [docs/02-architecture.md](docs/02-architecture.md) — proposed structure & stack
- [docs/03-texts-and-licensing.md](docs/03-texts-and-licensing.md) — **which texts
  we can host, which we must link, and how canon differs by tradition** (read this
  before adding any scripture text)
- **[ROADMAP.md](ROADMAP.md) — the canonical roadmap** (phases, definitions of done, buildable-now vs API vs deferred)
- [docs/05-preservation-and-integrity.md](docs/05-preservation-and-integrity.md) — the censorship-resistant preservation pillar (future)
- [docs/06-hosting-and-stewardship.md](docs/06-hosting-and-stewardship.md) — running lean (free/AWS) + the generous, community-first funding model
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to help

## License

The **code** is MIT (see [LICENSE](LICENSE)). **Scripture texts and scholarly works
carry their own licenses** — some are public domain, many modern translations are
copyrighted and may only be linked or accessed via licensed APIs. See
[docs/03-texts-and-licensing.md](docs/03-texts-and-licensing.md).
