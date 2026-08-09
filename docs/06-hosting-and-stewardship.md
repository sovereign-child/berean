# Hosting, Cost & Stewardship — running Berean lean and generously

Two convictions govern how Berean is funded and run:

1. **Resourceful, not scarce.** Berean is built with what we already have — open
   data, free tooling, time, and existing infrastructure — not with money we
   don't. Nearly everything it needs is free or already owned.
2. **A culture of generosity.** *"Freely you have received; freely give"*
   (Matthew 10:8). The tools are free to users forever. What support comes in is
   used to cover costs, **grow the community, and give back** — a model that
   reflects the Bible's own ethic of sharing and open-handedness (2 Corinthians
   9:7, "God loves a cheerful giver").

*(Honest boundary: this lean model applies to Berean, which genuinely doesn't need
money to be real. Truly capital-gated things elsewhere — e.g. third-party
smart-contract audits on other projects — still require real funding and aren't
wished away.)*

## What it costs to run — near zero

| Need | How | Cost |
|---|---|---|
| Development | your time + AI | $0 |
| Scripture & study data | open datasets — BSB (CC0), WEB, KJV, SBLGNT, STEPBible, OpenScriptures Hebrew | $0 |
| Hosting | an **AWS server we already have access to** (or a free static tier as fallback) | ~$0 marginal — keep the footprint small |
| Search | local full-text index (SQLite FTS / lightweight engine) | $0 |
| Copyrighted-translation APIs | free non-commercial tiers, and deferred anyway | $0 |
| Custom domain | optional (`berean.*` ~\$10/yr) or a free subdomain | deferrable |
| Arweave permanence | the preservation pillar — a *later* phase | **deferred** (the one genuinely paid piece) |

## Hosting on the AWS box (the asset we already have)

- **Phase 1 (Library + original-language study layer)** is mostly **static + a
  search index** — serve it as static files (S3 + CloudFront) or straight off the
  instance with a light server. Small footprint, within existing/free-tier resources.
- The same server **unlocks the dynamic pillars later without new spend** — Church
  Operations (needs a DB + auth) and Sermon Studio can run on it when the time comes.
- **Keep it self-hostable** (a core Berean value): the AWS box is *our* instance;
  any church or student can run their own copy the same way.
- *Practical note:* AWS bills for compute/bandwidth/storage, so keep it modest —
  static-first keeps it effectively free within what's already covered. If it ever
  grows past the existing resources, that's exactly the kind of running cost the
  stewardship model below is meant to fund.

## Stewardship & funding — the ladder (never out-of-pocket)

Free to users always; support is optional, transparent, and generous in both
directions.

1. **Now:** nothing. We're spending time, not money.
2. **When someone wants to give / the first real bill appears:** **GitHub
   Sponsors** — free to set up, no commitment.
3. **When support flows regularly:** a **fiscal host** — it takes only a *percentage
   of donations received* (~5–10%), so it's never out-of-pocket; it gives clean
   books, receipts, and (with a 501(c)(3) host) **tax-deductibility**. Notes:
   Open Collective Foundation wound down in 2024; for deductible giving use a
   501(c)(3) sponsor (ideally **ministry-aligned**), since Open Source Collective
   is a 501(c)(6) and its donations aren't charitable-deductible.
4. **Only at real scale:** our own **501(c)(3)** for full mission-lock — and note a
   nonprofit's asset-dedication reinforces the "the Word endures" ethic.

## Giving back — what "generous" concretely means

Surplus beyond running costs is **reinvested into the mission and given onward**,
transparently. Candidate ways to give back (to decide together as the community grows):

- fund **open Bible translation into languages that don't yet have it** (partnering
  with efforts like unfoldingWord / eBible.org);
- keep the tools **free for under-resourced churches** and help them self-host;
- **contributor grants / recognition** for those who add texts, scholarship, or code;
- publish a **transparent ledger** so the community sees exactly where support goes.

## The one non-negotiable guardrail

**Funding never buys editorial or canonical influence.** No donor — denominational
or otherwise — gets to slant the canon, the versions, or the "evidence." Berean's
non-sectarian integrity is not for sale. Money keeps the lights on and serves the
community; it does not touch the text.

---

*"Each of you should give what you have decided in your heart to give, not
reluctantly or under compulsion, for God loves a cheerful giver."* — 2 Corinthians 9:7
