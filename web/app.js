/* Berean reader — read/compare + search + cross-references + saved study.
   Vanilla JS, no dependencies. Study data is stored in this browser (localStorage);
   Export/Import moves it between devices. Serve from the repo root; open /web/. */
"use strict";

const MANIFEST_URL = "../library/manifest.json";
const versionUrl = (id) => `../library/corpus/${id}.json`;
const CROSSREFS_URL = "../library/crossrefs.json";
const STORE_KEY = "berean.study.v1";

// Canonical 66-book order — used to resolve cross-reference book indices + permalinks.
const BOOKS = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth","1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles","Ezra","Nehemiah","Esther","Job","Psalms","Proverbs","Ecclesiastes","Song of Solomon","Isaiah","Jeremiah","Lamentations","Ezekiel","Daniel","Hosea","Joel","Amos","Obadiah","Jonah","Micah","Nahum","Habakkuk","Zephaniah","Haggai","Zechariah","Malachi","Matthew","Mark","Luke","John","Acts","Romans","1 Corinthians","2 Corinthians","Galatians","Ephesians","Philippians","Colossians","1 Thessalonians","2 Thessalonians","1 Timothy","2 Timothy","Titus","Philemon","Hebrews","James","1 Peter","2 Peter","1 John","2 John","3 John","Jude","Revelation"];

const el = (id) => document.getElementById(id);
const esc = (s) => (s || "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const vk = (name, c1, v1) => `${name}|${c1}|${v1}`;              // version-agnostic verse key
const cache = new Map();
let crossrefs = null;
let manifest = null;
let hashLock = false;

const state = { primary: null, compare: null, book: 0, chapter: 0, selected: null };

/* ---------- study store (localStorage) ---------- */
function loadStore() {
  try { return Object.assign({ highlights: {}, notes: {}, collections: [] }, JSON.parse(localStorage.getItem(STORE_KEY) || "{}")); }
  catch { return { highlights: {}, notes: {}, collections: [] }; }
}
let store = loadStore();
function saveStore() { localStorage.setItem(STORE_KEY, JSON.stringify(store)); }

function toast(msg) {
  let t = el("toast");
  if (!t) { t = document.createElement("div"); t.id = "toast"; t.className = "toast"; document.body.appendChild(t); }
  t.textContent = msg; t.classList.add("show");
  clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("show"), 1500);
}

/* ---------- data ---------- */
async function loadVersion(id) {
  if (cache.has(id)) return cache.get(id);
  const d = await (await fetch(versionUrl(id))).json();
  d._byName = Object.fromEntries(d.books.map((b) => [b.name, b]));
  cache.set(id, d);
  return d;
}
async function loadCrossrefs() {
  if (!crossrefs) crossrefs = await (await fetch(CROSSREFS_URL)).json();
  return crossrefs;
}
const primary = () => cache.get(state.primary);

/* ---------- render ---------- */
function renderSelectors() {
  const p = primary(), book = p.books[state.book];
  el("bookSel").innerHTML = p.books.map((b, i) => `<option value="${i}" ${i === state.book ? "selected" : ""}>${b.name}</option>`).join("");
  el("chapSel").innerHTML = book.chapters.map((_, i) => `<option value="${i}" ${i === state.chapter ? "selected" : ""}>${i + 1}</option>`).join("");
  el("refLabel").textContent = `${book.name} ${state.chapter + 1}`;
}

function renderChapter() {
  const p = primary(), book = p.books[state.book], c1 = state.chapter + 1;
  const chA = book.chapters[state.chapter] || [];
  const cmp = state.compare ? cache.get(state.compare) : null;

  if (cmp) {
    const bookB = cmp._byName[book.name];
    const chB = (bookB && bookB.chapters[state.chapter]) || [];
    const rows = Math.max(chA.length, chB.length);
    let h = `<div class="cmp"><div class="cmp__head">${p.name}</div><div class="cmp__head">${cmp.name}</div>`;
    for (let i = 0; i < rows; i++)
      h += `<div class="row"><div class="cell"><span class="vnum">${i + 1}</span>${esc(chA[i] || "")}</div><div class="cell"><span class="vnum">${i + 1}</span>${esc(chB[i] || "")}</div></div>`;
    el("reader").innerHTML = h + `</div>`;
    return;
  }
  el("reader").innerHTML = chA.map((t, i) => {
    const v1 = i + 1, key = vk(book.name, c1, v1);
    const color = store.highlights[key], note = store.notes[key];
    const sel = state.selected && state.selected.key === key;
    return `<p class="verse${color ? ` hl-${color}` : ""}${sel ? " sel" : ""}" id="v${v1}" data-v="${v1}">`
      + `<span class="vnum" role="button" tabindex="0">${v1}</span>${esc(t)}`
      + (note ? `<span class="noteflag" title="note">✎</span><span class="noteline">${esc(note)}</span>` : "")
      + `</p>`;
  }).join("");
}

function renderAttribution() {
  const ids = [state.primary, state.compare].filter(Boolean);
  el("attribution").textContent = "Texts: " + ids.map((id) => cache.get(id).attribution).join("  ·  ");
}

function showOnly(section) {
  for (const s of ["results", "related", "study", "reader"]) el(s).hidden = s !== section;
}

/* ---------- navigation + permalinks ---------- */
function updateHash() {
  const p = primary(), name = p.books[state.book].name;
  hashLock = true;
  location.hash = `/${state.primary}/${encodeURIComponent(name)}/${state.chapter + 1}`;
  setTimeout(() => (hashLock = false), 0);
}
function gotoChapter(bookIdx, chapIdx, highlightVerse) {
  const p = primary();
  state.book = Math.max(0, Math.min(bookIdx, p.books.length - 1));
  state.chapter = Math.max(0, Math.min(chapIdx, p.books[state.book].chapters.length - 1));
  renderSelectors(); renderChapter(); showOnly("reader"); updateHash();
  if (highlightVerse) { const v = el(`v${highlightVerse}`); if (v) { v.scrollIntoView({ block: "center" }); } }
  else window.scrollTo({ top: 0 });
}
function step(d) {
  const p = primary(); let b = state.book, c = state.chapter + d;
  if (c < 0) { if (--b < 0) return; c = p.books[b].chapters.length - 1; }
  else if (c >= p.books[b].chapters.length) { if (++b >= p.books.length) return; c = 0; }
  clearSelection(); gotoChapter(b, c);
}
async function applyHash() {
  const m = location.hash.match(/^#\/([^/]+)\/([^/]+)\/(\d+)(?:\/(\d+))?/);
  if (!m) return false;
  const [, ver, bookEnc, ch, v] = m;
  if (!manifest.versions.some((x) => x.id === ver)) return false;
  state.primary = ver; el("verSel").value = ver; await loadVersion(ver);
  const name = decodeURIComponent(bookEnc);
  const bi = primary().books.findIndex((b) => b.name === name);
  if (bi < 0) return false;
  gotoChapter(bi, (+ch) - 1, v ? +v : 0);
  renderAttribution();
  return true;
}

/* ---------- verse selection + action bar ---------- */
function selectVerse(v1) {
  const p = primary(), book = p.books[state.book], c1 = state.chapter + 1;
  state.selected = { bi: state.book, name: book.name, c1, v1, key: vk(book.name, c1, v1) };
  renderChapter();
  el("verseBarRef").textContent = `${book.name} ${c1}:${v1}`;
  // populate collection <select>
  el("vbSave").innerHTML = `<option value="">Save to…</option>`
    + store.collections.map((c) => `<option value="${c.id}">＋ ${esc(c.name)}</option>`).join("")
    + `<option value="__new">＋ New collection…</option>`;
  el("verseBar").hidden = false;
}
function clearSelection() { state.selected = null; el("verseBar").hidden = true; }
function selectedText() {
  const p = primary(), s = state.selected;
  return p.books[s.bi].chapters[s.c1 - 1][s.v1 - 1] || "";
}

/* ---------- related verses (cross-references) ---------- */
function xrefDisplay(t) {
  const [main, end] = t.split("-");
  const [bi, ch, v] = main.split(".").map(Number);
  return { bi, ch, v, label: `${BOOKS[bi]} ${ch}:${v}${end ? "–" + end : ""}` };
}
async function showRelated() {
  const s = state.selected; if (!s) return;
  await loadCrossrefs();
  const key = `${s.bi}.${s.c1}.${s.v1}`;
  const list = crossrefs.refs[key] || [];
  el("relatedHead").textContent = `Related to ${s.name} ${s.c1}:${s.v1} — ${list.length} cross-reference${list.length === 1 ? "" : "s"}`;
  const p = primary();
  el("relatedList").innerHTML = list.map((t) => {
    const r = xrefDisplay(t);
    const verse = p.books[r.bi] && p.books[r.bi].chapters[r.ch - 1] && p.books[r.bi].chapters[r.ch - 1][r.v - 1];
    return `<li data-b="${r.bi}" data-c="${r.ch - 1}" data-v="${r.v}"><span class="r-ref">${r.label}</span> <span class="r-text">${esc((verse || "").slice(0, 160))}</span></li>`;
  }).join("") || "<li>No cross-references for this verse.</li>";
  el("relatedAttr").textContent = crossrefs.attribution;
  showOnly("related");
  window.scrollTo({ top: 0 });
}

/* ---------- search ---------- */
async function runSearch(q, allVersions) {
  q = q.trim(); if (!q) return;
  const needle = q.toLowerCase();
  const wordRe = new RegExp(`\\b${q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "i");
  const ids = allVersions ? manifest.versions.map((v) => v.id) : [state.primary];
  for (const id of ids) await loadVersion(id);
  const hits = [];
  const CAP = 500;
  for (const id of ids) {
    const d = cache.get(id);
    for (let bi = 0; bi < d.books.length; bi++) {
      const b = d.books[bi];
      for (let ci = 0; ci < b.chapters.length; ci++) {
        const ch = b.chapters[ci];
        for (let vi = 0; vi < ch.length; vi++) {
          const txt = ch[vi];
          if (txt && txt.toLowerCase().includes(needle)) {
            hits.push({ id, vid: d.name, bi, ci, vi, ref: `${b.name} ${ci + 1}:${vi + 1}`, text: txt, word: wordRe.test(txt) });
            if (hits.length >= CAP) { ci = 1e9; bi = 1e9; break; }
          }
        }
      }
    }
  }
  hits.sort((a, b) => (b.word - a.word)); // whole-word matches first; stable otherwise
  const mark = (s) => {
    const i = s.toLowerCase().indexOf(needle); if (i < 0) return esc(s);
    return esc(s.slice(0, i)) + "<mark>" + esc(s.slice(i, i + q.length)) + "</mark>" + esc(s.slice(i + q.length));
  };
  el("resultsCount").textContent = `${hits.length}${hits.length >= CAP ? "+" : ""} result${hits.length === 1 ? "" : "s"} for “${q}”${allVersions ? " (all versions)" : " in " + primary().name}`;
  el("resultsList").innerHTML = hits.map((h) =>
    `<li data-id="${h.id}" data-b="${h.bi}" data-c="${h.ci}" data-v="${h.vi + 1}"><span class="r-ref">${h.ref}</span> ${allVersions ? `<span class="r-ver">${h.vid}</span>` : ""} <span class="r-text">${mark(h.text)}</span></li>`
  ).join("") || "<li>No results.</li>";
  showOnly("results"); window.scrollTo({ top: 0 });
}

/* ---------- My Study panel ---------- */
function renderStudy() {
  const p = primary();
  const refFromKey = (key) => { const [n, c, v] = key.split("|"); return { name: n, c: +c, v: +v, bi: BOOKS.indexOf(n) }; };
  const jump = (key) => { const r = refFromKey(key); if (r.bi >= 0) { clearSelection(); gotoChapter(r.bi, r.c - 1, r.v); } };
  const textOf = (key) => { const r = refFromKey(key); const b = p.books[r.bi]; return (b && b.chapters[r.c - 1] && b.chapters[r.c - 1][r.v - 1]) || ""; };

  const colls = store.collections.length ? store.collections.map((c) =>
    `<div><h3>${esc(c.name)} <span class="tiny">(${c.verses.length})</span></h3><ul>` +
    (c.verses.map((k) => { const r = refFromKey(k); return `<li><span class="s-ref" data-jump="${k}">${r.name} ${r.c}:${r.v}</span><span class="s-text">${esc(textOf(k).slice(0, 120))}</span><button class="s-del" data-rmcoll="${c.id}" data-key="${k}">✕</button></li>`; }).join("") || `<li class="empty">empty</li>`) +
    `</ul></div>`).join("") : `<p class="empty">No collections yet. Select a verse → “Save to…” to start one.</p>`;

  const hlKeys = Object.keys(store.highlights);
  const hls = hlKeys.length ? `<ul>` + hlKeys.map((k) => { const r = refFromKey(k); return `<li><span class="dot" style="background:${{y:"#fff4c2",g:"#d8f3dc",b:"#d7e9ff",p:"#ffe0ef"}[store.highlights[k]] || "#eee"}"></span><span class="s-ref" data-jump="${k}">${r.name} ${r.c}:${r.v}</span><span class="s-text">${esc(textOf(k).slice(0, 120))}</span><button class="s-del" data-rmhl="${k}">✕</button></li>`; }).join("") + `</ul>` : `<p class="empty">No highlights yet.</p>`;

  const noteKeys = Object.keys(store.notes);
  const notes = noteKeys.length ? `<ul>` + noteKeys.map((k) => { const r = refFromKey(k); return `<li><span class="s-ref" data-jump="${k}">${r.name} ${r.c}:${r.v}</span><span class="s-text">${esc(store.notes[k])}</span><button class="s-del" data-rmnote="${k}">✕</button></li>`; }).join("") + `</ul>` : `<p class="empty">No notes yet.</p>`;

  el("studyBody").innerHTML = `<div><h3>Collections</h3>${colls}<div class="newcoll"><input id="newCollName" placeholder="New collection name…" /><button class="vbbtn" id="newCollBtn" style="background:var(--ink)">Create</button></div></div><div><h3>Highlights</h3>${hls}</div><div><h3>Notes</h3>${notes}</div>`;
  showOnly("study");

  el("studyBody").querySelectorAll("[data-jump]").forEach((n) => n.addEventListener("click", () => jump(n.dataset.jump)));
  el("studyBody").querySelectorAll("[data-rmhl]").forEach((n) => n.addEventListener("click", () => { delete store.highlights[n.dataset.rmhl]; saveStore(); renderStudy(); }));
  el("studyBody").querySelectorAll("[data-rmnote]").forEach((n) => n.addEventListener("click", () => { delete store.notes[n.dataset.rmnote]; saveStore(); renderStudy(); }));
  el("studyBody").querySelectorAll("[data-rmcoll]").forEach((n) => n.addEventListener("click", () => { const c = store.collections.find((x) => x.id === n.dataset.rmcoll); if (c) c.verses = c.verses.filter((k) => k !== n.dataset.key); saveStore(); renderStudy(); }));
  el("newCollBtn").addEventListener("click", () => { const v = el("newCollName").value.trim(); if (v) { store.collections.push({ id: "c" + Date.now().toString(36), name: v, verses: [] }); saveStore(); renderStudy(); } });
}

function exportStudy() {
  const blob = new Blob([JSON.stringify(store, null, 2)], { type: "application/json" });
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "berean-study.json"; a.click();
  toast("Study exported");
}
function importStudy(file) {
  const r = new FileReader();
  r.onload = () => { try {
    const d = JSON.parse(r.result);
    store.highlights = Object.assign(store.highlights, d.highlights || {});
    store.notes = Object.assign(store.notes, d.notes || {});
    const byName = Object.fromEntries(store.collections.map((c) => [c.name, c]));
    for (const c of d.collections || []) { if (byName[c.name]) byName[c.name].verses = [...new Set([...byName[c.name].verses, ...c.verses])]; else store.collections.push(c); }
    saveStore(); renderStudy(); toast("Study imported (merged)");
  } catch { toast("Import failed — not a valid file"); } };
  r.readAsText(file);
}

/* ---------- init ---------- */
async function init() {
  try { manifest = await (await fetch(MANIFEST_URL)).json(); }
  catch { el("reader").innerHTML = `<p>Could not load the library. Run <code>python3 scripts/ingest.py</code> and serve from the repo root.</p>`; return; }
  const opts = manifest.versions.map((v) => `<option value="${v.id}">${v.name}</option>`).join("");
  el("verSel").innerHTML = opts;
  el("cmpSel").innerHTML = `<option value="">— none —</option>` + opts;

  state.primary = manifest.versions[0].id;
  await loadVersion(state.primary);
  if (!(location.hash && await applyHash())) gotoChapter(0, 0);
  renderAttribution();

  el("bookSel").addEventListener("change", (e) => { clearSelection(); gotoChapter(+e.target.value, 0); });
  el("chapSel").addEventListener("change", (e) => { clearSelection(); gotoChapter(state.book, +e.target.value); });
  el("prevBtn").addEventListener("click", () => step(-1));
  el("nextBtn").addEventListener("click", () => step(1));
  el("verSel").addEventListener("change", async (e) => { state.primary = e.target.value; await loadVersion(state.primary); clearSelection(); gotoChapter(state.book, state.chapter); renderAttribution(); });
  el("cmpSel").addEventListener("change", async (e) => { state.compare = e.target.value || null; if (state.compare) await loadVersion(state.compare); clearSelection(); renderChapter(); showOnly("reader"); renderAttribution(); });

  el("searchForm").addEventListener("submit", (e) => { e.preventDefault(); runSearch(el("searchInput").value, el("searchAll").checked); });
  el("studyBtn").addEventListener("click", renderStudy);
  el("exportBtn").addEventListener("click", exportStudy);
  el("importBtn").addEventListener("click", () => el("importFile").click());
  el("importFile").addEventListener("change", (e) => { if (e.target.files[0]) importStudy(e.target.files[0]); });

  document.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", () => showOnly("reader")));

  // verse number → select (single-column reading only)
  el("reader").addEventListener("click", (e) => {
    const num = e.target.closest(".vnum"); if (!num || state.compare) return;
    const p = num.closest(".verse"); if (p) selectVerse(+p.dataset.v);
  });
  // results / related navigation
  el("resultsList").addEventListener("click", async (e) => {
    const li = e.target.closest("li[data-b]"); if (!li) return;
    if (li.dataset.id && li.dataset.id !== state.primary) { state.primary = li.dataset.id; el("verSel").value = li.dataset.id; await loadVersion(state.primary); renderAttribution(); }
    clearSelection(); gotoChapter(+li.dataset.b, +li.dataset.c, +li.dataset.v);
  });
  el("relatedList").addEventListener("click", (e) => { const li = e.target.closest("li[data-b]"); if (!li) return; clearSelection(); gotoChapter(+li.dataset.b, +li.dataset.c, +li.dataset.v); });

  // verse action bar
  document.querySelectorAll(".sw").forEach((sw) => sw.addEventListener("click", () => {
    if (!state.selected) return; const c = sw.dataset.color;
    if (c) store.highlights[state.selected.key] = c; else delete store.highlights[state.selected.key];
    saveStore(); renderChapter();
  }));
  el("vbNote").addEventListener("click", () => {
    if (!state.selected) return;
    const cur = store.notes[state.selected.key] || "";
    const n = prompt(`Note on ${state.selected.name} ${state.selected.c1}:${state.selected.v1}`, cur);
    if (n === null) return; if (n.trim()) store.notes[state.selected.key] = n.trim(); else delete store.notes[state.selected.key];
    saveStore(); renderChapter();
  });
  el("vbSave").addEventListener("change", (e) => {
    if (!state.selected) return; let id = e.target.value; e.target.value = "";
    if (!id) return;
    if (id === "__new") { const name = prompt("New collection name:"); if (!name || !name.trim()) return; const coll = { id: "c" + Date.now().toString(36), name: name.trim(), verses: [] }; store.collections.push(coll); id = coll.id; }
    const coll = store.collections.find((c) => c.id === id); if (!coll) return;
    if (!coll.verses.includes(state.selected.key)) coll.verses.push(state.selected.key);
    saveStore(); toast(`Saved to “${coll.name}”`); selectVerse(state.selected.v1); // refresh select options
  });
  el("vbRelated").addEventListener("click", showRelated);
  el("vbCopy").addEventListener("click", async () => { const s = state.selected; if (!s) return; await navigator.clipboard.writeText(`${selectedText()} — ${s.name} ${s.c1}:${s.v1} (${primary().name})`).then(() => toast("Verse copied")).catch(() => toast("Copy failed")); });
  el("vbLink").addEventListener("click", async () => { const s = state.selected; if (!s) return; const url = `${location.origin}${location.pathname}#/${state.primary}/${encodeURIComponent(s.name)}/${s.c1}/${s.v1}`; await navigator.clipboard.writeText(url).then(() => toast("Link copied")).catch(() => toast("Copy failed")); });
  el("vbClose").addEventListener("click", clearSelection);

  window.addEventListener("hashchange", () => { if (!hashLock) applyHash(); });
}

document.addEventListener("DOMContentLoaded", init);
