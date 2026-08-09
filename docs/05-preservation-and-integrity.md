# Preservation & Integrity — keeping the Word censorship-resistant

A future pillar. The goal: the Scripture corpus Berean assembles should be
**censorship-resistant** — no single company, government, or actor can delete it,
alter it, or quietly suppress it, and **any copy can be verified as unaltered.**

## What "censorship-resistant" means here (precisely)

- **No central point of deletion.** The text is addressed by its **hash**
  (content addressing), not by a URL or a server you can seize. Kill one host and
  the content lives on wherever anyone holds it; the hash still resolves it.
- **Tamper-evident.** Any byte changed changes the hash. A reader can verify a
  copy against the canonical hash and *know* it's the real thing — not "trust the
  website," but "verify the text."
- **Publicly anchored + timestamped.** The hashes live on a public blockchain no
  single party controls, so the integrity record itself can't be quietly erased or
  back-dated.
- **What it does NOT mean (be honest):** it does **not** guarantee that every
  government lets its citizens *reach* the network. A censor can block gateways or
  the protocol at the ISP level locally — the record survives and re-emerges
  elsewhere, but *access* can be impeded in a given place. Censorship-resistance
  is about "cannot be deleted or altered," not "readable everywhere no matter what."

## The architecture (bulk off-chain, proofs on-chain)

1. **Permanent storage for the text** — **Arweave** (pay-once, endowed ~200-year
   permanent "permaweb" storage across a decentralized miner network) and/or
   **IPFS + Filecoin** (content-addressed, incentivized replication). This is where
   the actual bytes of each version/book/manuscript live.
2. **On-chain integrity registry** — only the **Merkle root hash** of each edition
   goes on a public chain: a small, immutable, timestamped anchor proving "this CID
   is the canonical <edition>, unaltered, as of this time." Cheap on-chain,
   verifiable by anyone.
3. **Wide mirroring** — anyone can pin/replicate the content and run a gateway. The
   more independent copies, the more uncensorable. Gateways are many and swappable.

Verification flow: reader has bytes → hashes them → checks the hash against the
on-chain anchor → confirms authenticity, with no trusted intermediary.

## Honest guardrails (so the tech serves the mission, not the reverse)

- **Anchor many editions, not "the one true text."** Immutability guarantees the
  *integrity of each edition* — every translation, manuscript, and canon, labeled
  by tradition and provenance (per [03-texts-and-licensing.md](03-texts-and-licensing.md)).
  It must not be used to crown a single canonical text; that would betray Berean's
  non-sectarian, show-the-variants principle.
- **Append-only, versioned.** Immutability means you can't fix an OCR typo in
  place — you publish a new checksummed version and anchor it. Design for versions
  from the start.
- **Preservation-pure — no token.** The value is permanence + verifiable
  integrity. Berean will **not** tokenize Scripture or attach a speculative coin to
  it. This is notarization and preservation, not a market.
- **Belt and suspenders.** On-chain anchor + permaweb + IPFS + ordinary mirrors +
  offline/physical copies. Redundancy across independent methods is the real
  guarantee; the blockchain is the integrity anchor, not the only copy.

## Where this fits

- Built **on the corpus + manifest** once assembled — you anchor what exists, so
  this follows Phase 1+ of the [roadmap](04-roadmap.md), not before.
- Uses **existing permanence infrastructure** (Arweave / IPFS / Filecoin) — it's a
  Berean *feature*, kept separate from the other projects; it does not require or
  merge with any of them.
- The point, in one line: the Bible already survives through sheer redundancy;
  this pillar makes the digital record **provably unaltered and impossible for any
  one authority to erase.**

*"The grass withers and the flowers fall, but the word of our God endures
forever."* — Isaiah 40:8
