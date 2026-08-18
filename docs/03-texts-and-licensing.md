# Texts & Licensing — read before adding any scripture text

This is the most important operational constraint in the project. Getting it wrong
means either copyright infringement or misrepresenting a tradition's canon. **Do
not add a scripture text to `library/` without checking it against this doc.**

## The copyright reality

- **Public domain (host directly, with attribution to the edition):**
  KJV (1769), American Standard Version (1901), Webster, Young's Literal (YLT),
  Darby, Douay-Rheims (Catholic), and the **World English Bible (WEB)** — a modern-
  English translation released into the public domain (a key asset).
  **✅ Ingested (2026-08-17):** the WEB *with Deuterocanon* edition from eBible.org
  (`eng-web_vpl.zip`, 81 books) via `scripts/ingest_web.py`. This is how Berean can
  show the Catholic and Orthodox books in full without licensing anything. Note
  eBible.org's terms: the text is public domain, but "World English Bible" is their
  trademark — the attribution string in the manifest says so.
  *(Note: the KJV is under perpetual Crown copyright in the UK specifically; PD
  elsewhere. Document per-jurisdiction where it matters.)*
- **Copyrighted — DO NOT host or redistribute; link or use a licensed API:**
  NIV, ESV, NASB, NKJV, CSB, NLT, and most modern translations. Integrate via a
  licensed provider (e.g. API.Bible / scripture APIs) under their terms, with
  required attribution and caching limits. Store *references*, not the text.
- **Septuagint (Greek OT):** ✅ Brenton's 1851 English translation is public domain and
  hosted (`scripts/ingest_brenton.py`). NOTE its versification follows the Greek, not
  the Hebrew — see `library/versification.json`, which is derived and checked, not asserted.
  The Greek text itself (`grclxx` on eBible.org) is also public domain, for the
  original-language phase.
- **Original languages:** Westminster Leningrad Codex (Hebrew, open); for Greek,
  prefer clearly-licensed editions (e.g. SBLGNT under its own license terms, or
  public-domain Tischendorf / Byzantine text) — check each edition's license.
- **Lexicons/reference:** Strong's Concordance and many 19th–early-20th-century
  works are public domain; modern lexicons (e.g. BDAG, HALOT) are copyrighted.

**Rule of thumb:** if it was published before ~1928 (US PD cutoff, which advances
yearly) or explicitly open-licensed, it can likely be hosted; otherwise link/API.
Record the source edition and license for **every** text in a manifest.

## The canon reality (why "versions and lost books" needs care)

Different traditions include different books. Berean must **label**, never assume:

- **Protestant** — 66 books (39 OT / 27 NT).
- **Catholic** — 73 books; adds the **deuterocanon** (Tobit, Judith, Wisdom,
  Sirach, Baruch, 1–2 Maccabees, additions to Esther/Daniel).
- **Eastern Orthodox** — the deuterocanon plus additional books (3 Maccabees,
  1 Esdras, Prayer of Manasseh, Psalm 151, …), varying by jurisdiction.
- **Tewahedo (Ethiopian) canon** — broader still (includes 1 Enoch, Jubilees).
- **Pseudepigrapha / "lost" & non-canonical books** — 1 Enoch ✅ and Jubilees ✅ (both
  Charles, PD, hosted and labeled), Jasher,
  Gospel of Thomas, etc.: **not scripture in most traditions**, but of real
  historical/scholarly interest. Present them clearly as such, never implied as
  canonical.

Every book in the Library carries metadata: `canon_status` per tradition, source
edition, translation, language, and license. The UI shows the reader *which*
canon they're viewing and what differs.

**✅ Implemented:** `library/canons.json` holds the per-tradition status of every
disputed book across five traditions, and the 📜 Canon view renders it as a
comparison you can read and click into. Books outside the Protestant 66 are marked
✦ in the book list and badged in the chapter header, so no one meets Tobit or
1 Enoch without being told where it stands. `scripts/check_threads.py` verifies
that every citation Berean makes in a Thread actually resolves in the text it
names — the integrity check behind "examine for yourself."

## Evidence & scholarship sourcing

Historical/manuscript/archaeological content must cite primary or reputable
secondary sources, and must distinguish **established**, **contested/scholarly-
debated**, and **faith** claims. No unsourced assertions in the Evidence pillar.

## A data manifest

`library/` (and `research/`) content is tracked in a manifest that records, per
item: title, edition/year, language, tradition/canon status, source URL, license,
and whether it is hosted or linked. This is the audit trail that keeps the project
legally clean and scholarly honest.
