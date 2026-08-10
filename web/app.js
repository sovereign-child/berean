/* Berean reader — Phase 1 (Library MVP).
   Reads the normalized open-text corpus (library/) and provides: read a chapter,
   switch version, compare two versions side-by-side, and search within a version.
   Vanilla JS, no dependencies. Serve from the repo root; open /web/. */

"use strict";

const MANIFEST_URL = "../library/manifest.json";
const versionUrl = (id) => `../library/corpus/${id}.json`;

const el = (id) => document.getElementById(id);
const cache = new Map(); // version id -> version data

const state = { primary: null, compare: null, book: 0, chapter: 0 };

async function loadVersion(id) {
  if (cache.has(id)) return cache.get(id);
  const res = await fetch(versionUrl(id));
  if (!res.ok) throw new Error(`Failed to load version ${id}`);
  const data = await res.json();
  data._byName = Object.fromEntries(data.books.map((b) => [b.name, b]));
  cache.set(id, data);
  return data;
}

function primary() { return cache.get(state.primary); }
function compareData() { return state.compare ? cache.get(state.compare) : null; }

/* ---------- rendering ---------- */

function renderSelectors() {
  const p = primary();
  const book = p.books[state.book];
  // book select
  el("bookSel").innerHTML = p.books
    .map((b, i) => `<option value="${i}" ${i === state.book ? "selected" : ""}>${b.name}</option>`)
    .join("");
  // chapter select
  el("chapSel").innerHTML = book.chapters
    .map((_, i) => `<option value="${i}" ${i === state.chapter ? "selected" : ""}>${i + 1}</option>`)
    .join("");
  el("refLabel").textContent = `${book.name} ${state.chapter + 1}`;
}

function verseRow(n, text) {
  return `<p class="verse" id="v${n}"><span class="vnum">${n}</span>${text || ""}</p>`;
}

function renderChapter() {
  const p = primary();
  const book = p.books[state.book];
  const chA = book.chapters[state.chapter] || [];
  const cmp = compareData();

  if (!cmp) {
    el("reader").innerHTML = chA.map((t, i) => verseRow(i + 1, t)).join("");
    return;
  }
  // compare: align by verse index using the same book name + chapter index
  const bookB = cmp._byName[book.name];
  const chB = (bookB && bookB.chapters[state.chapter]) || [];
  const rows = Math.max(chA.length, chB.length);
  let html = `<div class="cmp"><div class="cmp__head">${p.name}</div><div class="cmp__head">${cmp.name}</div>`;
  for (let i = 0; i < rows; i++) {
    html += `<div class="row">`
      + `<div class="cell" id="v${i + 1}"><span class="vnum">${i + 1}</span>${chA[i] || ""}</div>`
      + `<div class="cell"><span class="vnum">${i + 1}</span>${chB[i] || ""}</div>`
      + `</div>`;
  }
  html += `</div>`;
  el("reader").innerHTML = html;
}

function showReader() { el("results").hidden = true; el("reader").hidden = false; }

function renderAttribution() {
  const ids = [state.primary, state.compare].filter(Boolean);
  const texts = ids.map((id) => cache.get(id).attribution);
  el("attribution").textContent = "Texts: " + texts.join("  ·  ");
}

/* ---------- navigation ---------- */

function gotoChapter(bookIdx, chapIdx, highlightVerse) {
  const p = primary();
  state.book = Math.max(0, Math.min(bookIdx, p.books.length - 1));
  const nCh = p.books[state.book].chapters.length;
  state.chapter = Math.max(0, Math.min(chapIdx, nCh - 1));
  renderSelectors();
  renderChapter();
  showReader();
  if (highlightVerse) {
    const v = el(`v${highlightVerse}`);
    if (v) { v.classList.add("hl"); v.scrollIntoView({ block: "center" }); }
  } else {
    window.scrollTo({ top: 0 });
  }
}

function step(delta) {
  const p = primary();
  let b = state.book, c = state.chapter + delta;
  if (c < 0) { b -= 1; if (b < 0) return; c = p.books[b].chapters.length - 1; }
  else if (c >= p.books[b].chapters.length) { b += 1; if (b >= p.books.length) return; c = 0; }
  gotoChapter(b, c);
}

/* ---------- search ---------- */

function runSearch(q) {
  q = q.trim();
  if (!q) return;
  const p = primary();
  const needle = q.toLowerCase();
  const hits = [];
  const CAP = 400;
  outer:
  for (let bi = 0; bi < p.books.length; bi++) {
    const b = p.books[bi];
    for (let ci = 0; ci < b.chapters.length; ci++) {
      const ch = b.chapters[ci];
      for (let vi = 0; vi < ch.length; vi++) {
        if (ch[vi] && ch[vi].toLowerCase().includes(needle)) {
          hits.push({ bi, ci, vi, ref: `${b.name} ${ci + 1}:${vi + 1}`, text: ch[vi] });
          if (hits.length >= CAP) break outer;
        }
      }
    }
  }
  const esc = (s) => s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const mark = (s) => {
    const i = s.toLowerCase().indexOf(needle);
    if (i < 0) return esc(s);
    return esc(s.slice(0, i)) + "<mark>" + esc(s.slice(i, i + q.length)) + "</mark>" + esc(s.slice(i + q.length));
  };
  el("resultsCount").textContent =
    `${hits.length}${hits.length >= CAP ? "+" : ""} result${hits.length === 1 ? "" : "s"} for “${q}” in ${p.name}`;
  el("resultsList").innerHTML = hits
    .map((h) => `<li data-b="${h.bi}" data-c="${h.ci}" data-v="${h.vi}"><span class="r-ref">${h.ref}</span> <span class="r-text">${mark(h.text)}</span></li>`)
    .join("") || "<li>No results.</li>";
  el("reader").hidden = true;
  el("results").hidden = false;
  window.scrollTo({ top: 0 });
}

/* ---------- init + events ---------- */

async function init() {
  let manifest;
  try {
    manifest = await (await fetch(MANIFEST_URL)).json();
  } catch (e) {
    el("reader").innerHTML = `<p>Could not load the library. Run <code>python3 scripts/ingest.py</code> and serve from the repo root.</p>`;
    return;
  }
  const versions = manifest.versions;
  el("verSel").innerHTML = versions.map((v) => `<option value="${v.id}">${v.name}</option>`).join("");
  el("cmpSel").innerHTML = `<option value="">— none —</option>` +
    versions.map((v) => `<option value="${v.id}">${v.name}</option>`).join("");

  state.primary = versions[0].id;
  await loadVersion(state.primary);
  gotoChapter(0, 0);
  renderAttribution();

  el("bookSel").addEventListener("change", (e) => gotoChapter(+e.target.value, 0));
  el("chapSel").addEventListener("change", (e) => gotoChapter(state.book, +e.target.value));
  el("prevBtn").addEventListener("click", () => step(-1));
  el("nextBtn").addEventListener("click", () => step(1));

  el("verSel").addEventListener("change", async (e) => {
    state.primary = e.target.value;
    await loadVersion(state.primary);
    // keep book/chapter within range
    gotoChapter(state.book, state.chapter);
    renderAttribution();
  });
  el("cmpSel").addEventListener("change", async (e) => {
    state.compare = e.target.value || null;
    if (state.compare) await loadVersion(state.compare);
    renderChapter();
    showReader();
    renderAttribution();
  });

  el("searchForm").addEventListener("submit", (e) => { e.preventDefault(); runSearch(el("searchInput").value); });
  el("resultsClose").addEventListener("click", showReader);
  el("resultsList").addEventListener("click", (e) => {
    const li = e.target.closest("li[data-b]");
    if (!li) return;
    gotoChapter(+li.dataset.b, +li.dataset.c, +li.dataset.v + 1);
  });
}

document.addEventListener("DOMContentLoaded", init);
