# Architecture (proposed)

Deliberately data-first. The hard, durable part of Berean is a clean, normalized,
well-licensed **corpus** (texts + evidence + metadata); the apps are views onto it.

## Layers

1. **Corpus (data)** — the source of truth. A normalized schema keyed by
   `version → book → chapter → verse`, plus:
   - version/edition metadata (language, tradition, `canon_status`, license, source);
   - original-language tokens with morphology + lexicon links (interlinear alignment);
   - cross-reference and concordance indexes;
   - an **evidence** store (manuscripts, variants, archaeology) with citations.
   Tracked by the manifest in [03-texts-and-licensing.md](03-texts-and-licensing.md).
2. **API / search** — read API over the corpus + full-text and word search
   (original-language aware). Reference-only for API-sourced copyrighted texts.
3. **Apps** — the Library reader/compare, Study & Community, **Sermon Studio**,
   and **Church Operations**. Each app is a view/tool over the corpus + API.

## Directory layout (this repo)

```
berean/
├── docs/            # vision, architecture, texts-&-licensing, roadmap
├── library/         # the corpus: texts, versions, original languages, wider canon (+ manifest)
├── research/        # the Evidence pillar: manuscripts, textual criticism, archaeology (sourced)
├── tools/
│   ├── sermon-studio/   # sermon/lesson builder
│   └── church-ops/      # church operations & community management
└── community/       # how the learning community works; contribution + moderation norms
```

## Stack (candidate — not yet fixed)

- **Web app:** a TypeScript app (Next.js or Vite/React) fits a read-mostly study
  UI with search; matches the wider ecosystem's tooling. Self-hostable is a hard
  requirement (churches own their instance).
- **Data pipeline:** ingest scripts that pull **open** sources into the normalized
  schema — candidates to evaluate for license fit: the World English Bible and
  other PD texts (e.g. eBible.org), Hebrew/Tanakh (e.g. Sefaria's openly-licensed
  data), tagged originals (e.g. STEPBible TAHOT/TAGNT — check license), Strong's.
- **Search:** a local full-text index (e.g. SQLite FTS / a lightweight engine) so
  the reader app can be self-hosted without heavy infrastructure.
- **Church-ops** likely wants persistence + auth; scope it as its own service.

Nothing here is committed yet — the roadmap builds the corpus first, then one app
at a time. Stack is chosen at Phase 1, not now.
