# web/ — the Berean reader (Phase 1: Library MVP)

A dependency-free static reader over the open-text corpus in `../library/`:
read a chapter, switch version, **compare two versions side-by-side**, and
**search within a version**. No framework, no external fonts/CDNs — it self-hosts
anywhere (the AWS box, any static host, or later IPFS).

## Run locally

Serve from the **repo root** (so both `web/` and `library/` are reachable), then
open the app:

```bash
cd berean            # ← the repo ROOT (must contain BOTH web/ and library/)
python3 -m http.server 8000
# open http://localhost:8000/   (redirects into the reader; or go straight to /web/)
```

Two things that cause a **404**:
- **Running the server from the wrong folder.** Start it from the repo root
  (`berean/`), *not* from inside `web/` — the reader loads `../library/`, which is
  only reachable when the root contains both `web/` and `library/`.
- Opening the wrong path. Just open `http://localhost:8000/`.

(Opening `index.html` via `file://` won't work either — the app `fetch()`es the
corpus, which browsers block on `file://`. Use the static server above.)

## Populate / refresh the texts

The corpus is generated from open sources by the ingest pipeline:

```bash
python3 scripts/ingest.py     # fetches BSB (CC0) + KJV (PD) → library/corpus/*.json + manifest.json
```

Only public-domain / openly-licensed texts are ingested and hosted. Copyrighted
translations (ESV/NIV/…) are a later, API-only pass-through — never hosted (see
`../docs/03-texts-and-licensing.md`).

## Deploy (free / self-host)

It's static files + JSON. Point any static host at the **repo root** and serve
`/web/` (or copy `web/` + `library/` together to the web root):

- **AWS** (the box we have): put the files behind nginx/Caddy, or push to S3 +
  CloudFront. Static — tiny footprint.
- **Free tiers:** GitHub Pages / Cloudflare Pages / Netlify — deploy the repo root.

## What's here

- `index.html` / `styles.css` / `app.js` — the reader (parchment-and-ink, reverent, accessible).
- Data comes from `../library/manifest.json` and `../library/corpus/<ID>.json`.

## Next (per ../ROADMAP.md)

Phase 2 adds the original-language study layer (interlinear + morphology + Strong's
over the open Hebrew/Greek datasets). This reader is the foundation it builds on.
