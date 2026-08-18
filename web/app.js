/* Berean reader — read/compare + search + cross-references + saved study.
   Vanilla JS, no dependencies. Study data is stored in this browser (localStorage);
   Export/Import moves it between devices. Serve from the repo root; open /web/. */
"use strict";

const MANIFEST_URL = "../library/manifest.json";
const BOOKS_URL = "../library/books.json";
const indexUrl = (id) => `../library/corpus/${id}/index.json`;
const bookUrl = (id, code) => `../library/corpus/${id}/${code}.json`;
const bundleUrl = (id) => `../library/corpus/${id}.json`;          // whole version — search only
const xrefUrl = (code) => `../library/crossrefs/${code}.json`;
const STORE_KEY = "berean.study.v2";
const STORE_KEY_V1 = "berean.study.v1";
const PREFS_KEY = "berean.prefs.v1";   // remembered reader preferences (version, compare, search scope)

/* Every dataset keys on the book codes in library/books.json — a verse address is
   CODE.CHAPTER.VERSE (JHN.3.16). Display names live in that one registry, so
   renaming a book can never orphan a reader's saved study again. */
let registry = null;
const codeFor = (name) => (registry && registry.resolve[String(name).trim().toLowerCase()]) || null;
const nameFor = (code) => (registry && (registry.byCode[code] || {}).name) || code;

const el = (id) => document.getElementById(id);
const vref = (code, c1, v1) => `${code}.${c1}.${v1}`;                 // canonical verse address
const esc = (s) => (s || "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const vk = vref;                                                     // study data is keyed the same way
const cache = new Map();      // version id → index + whatever books have been opened
const bundles = new Map();    // version id → the whole-version file (search)
const crossrefs = new Map();  // book code → its cross-references
let xrefMeta = null;
let manifest = null;
let hashLock = false;

const state = { primary: null, compare: null, code: null, chapter: 0, sel: null, anchor: null };

/* ---------- study store (localStorage) ---------- */
function loadStore() {
  try { return Object.assign({ highlights: {}, notes: {}, collections: [], prayers: [] }, JSON.parse(localStorage.getItem(STORE_KEY) || "{}")); }
  catch { return { highlights: {}, notes: {}, collections: [], prayers: [] }; }
}
let store = loadStore();
function saveStore() { localStorage.setItem(STORE_KEY, JSON.stringify(store)); }

/* Study saved before book codes existed was keyed "Song of Solomon|2|1", which
   would have broken the day a book was renamed. Migrate it once, in place, and
   leave the old record alone so nothing is lost if this goes wrong. */
function migrateStore() {
  if (localStorage.getItem(STORE_KEY)) return;
  let old;
  try { old = JSON.parse(localStorage.getItem(STORE_KEY_V1) || "null"); } catch { return; }
  if (!old) return;
  const rekey = (k) => {
    const [name, c, v] = String(k).split("|");
    const code = codeFor(name);
    return code && c && v ? vref(code, +c, +v) : null;
  };
  const map = (obj) => Object.fromEntries(Object.entries(obj || {})
    .map(([k, val]) => [rekey(k), val]).filter(([k]) => k));
  store = {
    highlights: map(old.highlights),
    notes: map(old.notes),
    collections: (old.collections || []).map((c) =>
      ({ ...c, verses: (c.verses || []).map(rekey).filter(Boolean) })),
    prayers: old.prayers || [],
  };
  saveStore();
  const moved = Object.keys(store.highlights).length + Object.keys(store.notes).length;
  if (moved) setTimeout(() => toast(`Your study moved to the new verse addresses (${moved} items)`), 800);
}

function loadPrefs() { try { return JSON.parse(localStorage.getItem(PREFS_KEY) || "{}"); } catch { return {}; } }
function savePrefs() {
  localStorage.setItem(PREFS_KEY, JSON.stringify({
    primary: state.primary, compare: state.compare, searchAll: el("searchAll").checked,
    theme: comfort.theme, size: comfort.size, voice: comfort.voice, rate: comfort.rate,
    commentary: comfort.commentary, red: comfort.red,
  }));
}

/* Reader comfort: theme, text size, and reading voice/rate (all persisted). */
const comfort = { theme: "light", size: 1.18, voice: "", rate: 0.9, commentary: "", red: true };
function applyComfort() {
  document.body.classList.toggle("dark", comfort.theme === "dark");
  document.documentElement.style.setProperty("--reader-size", comfort.size + "rem");
  const tb = el("themeBtn"); if (tb) { tb.textContent = comfort.theme === "dark" ? "☀" : "☾"; }
  const rb = el("redBtn");
  if (rb) { rb.classList.toggle("active", comfort.red); rb.setAttribute("aria-pressed", String(!!comfort.red)); }
}

function toast(msg) {
  let t = el("toast");
  if (!t) { t = document.createElement("div"); t.id = "toast"; t.className = "toast"; document.body.appendChild(t); }
  t.textContent = msg; t.classList.add("show");
  clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("show"), 1500);
}

/* ---------- data --------------------------------------------------------------
   A version loads as its index — metadata and the verse count of every chapter,
   about 6 KB — which is everything the menus need. Books arrive one file at a
   time as they are opened, so the reader shows a chapter without downloading a
   Bible. `chapters` is sized from the index up front and filled in on demand,
   so anything reading `book.chapters.length` keeps working. */
async function loadRegistry() {
  if (!registry) {
    registry = await (await fetch(BOOKS_URL)).json();
    registry.byCode = Object.fromEntries(registry.books.map((b) => [b.code, b]));
  }
  return registry;
}
async function loadVersion(id) {
  if (cache.has(id)) return cache.get(id);
  const d = await (await fetch(indexUrl(id))).json();
  d.books = d.books.map((b) => ({ code: b.code, name: b.name, verseCounts: b.chapters,
                                  chapters: b.chapters.map(() => null), loaded: false }));
  d._byCode = Object.fromEntries(d.books.map((b) => [b.code, b]));
  d._byName = Object.fromEntries(d.books.map((b) => [b.name, b]));
  cache.set(id, d);
  return d;
}
/* Fetch one book's text if it is not already here. */
async function ensureBook(id, code) {
  const d = cache.get(id) || await loadVersion(id);
  const book = d._byCode[code];
  if (!book || book.loaded) return book || null;
  const shard = await (await fetch(bookUrl(id, code))).json();
  book.chapters = shard.chapters;
  book.loaded = true;
  return book;
}
/* The whole version in one file. Only search needs this. */
async function loadBundle(id) {
  if (!bundles.has(id)) bundles.set(id, await (await fetch(bundleUrl(id))).json());
  return bundles.get(id);
}
const primary = () => cache.get(state.primary);
const curBook = () => { const p = primary(); return p && p._byCode[state.code]; };
const bookAt = (id, code) => { const d = cache.get(id); return d && d._byCode[code]; };

/* ---------- links, share, read-aloud ---------- */
const base = () => `${location.origin}${location.pathname}`;
const verseLink = (s) => `${base()}#/${state.primary}/${encodeURIComponent(s.name)}/${s.c1}/${s.v1}`;
const bookIndex = (id, code) => { const d = cache.get(id); return d ? d.books.findIndex((b) => b.code === code) : -1; };
const chapterLink = () => `${base()}#/${state.primary}/${encodeURIComponent(curBook().name)}/${state.chapter + 1}`;

async function shareOrCopy({ title, text, url }) {
  if (navigator.share) {
    try { await navigator.share({ title, text, url }); return; }
    catch (e) { if (e && e.name === "AbortError") return; }   // user dismissed the sheet
  }
  try { await navigator.clipboard.writeText(url ? `${text ? text + "\n" : ""}${url}` : text); toast("Copied to clipboard"); }
  catch { toast("Sharing not available"); }
}

const ICON_PLAY = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><polygon points="6 4 20 12 6 20 6 4"/></svg>';
const ICON_STOP = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>';
let voices = [];
let speaking = false;

// Rank the device's voices so "Auto" prefers higher-quality neural voices when present.
function voiceScore(v) {
  let s = 0;
  if (/natural|neural|premium|enhanced|siri|wavenet|journey|studio/i.test(v.name)) s += 4;
  if (/google/i.test(v.name)) s += 2;
  if (/^en[-_]/i.test(v.lang)) s += 1;
  if (v.localService) s += 0.5;   // offline voices avoid network hitches
  return s;
}
function pickVoice() {
  if (comfort.voice) { const v = voices.find((x) => x.name === comfort.voice); if (v) return v; }
  return voices.slice().sort((a, b) => voiceScore(b) - voiceScore(a))[0] || null;
}
function loadVoices() {
  voices = window.speechSynthesis ? window.speechSynthesis.getVoices() : [];
  const sel = el("voiceSel"); if (!sel) return;
  const best = pickVoice();
  sel.innerHTML = `<option value="">Auto voice${best ? " · " + esc(best.name) : ""}</option>`
    + voices.map((v) => `<option value="${esc(v.name)}" ${v.name === comfort.voice ? "selected" : ""}>${esc(v.name)} (${esc(v.lang)})${voiceScore(v) >= 4 ? " ★" : ""}</option>`).join("");
}
function makeUtterance(text) {
  const u = new SpeechSynthesisUtterance(text);
  u.rate = comfort.rate;   // < 1 = calmer, more measured
  u.pitch = 1.0; u.volume = 1.0;
  const v = pickVoice(); if (v) { u.voice = v; u.lang = v.lang; }
  return u;
}
function stopSpeak() {
  speaking = false;
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  document.querySelectorAll(".verse.speaking").forEach((n) => n.classList.remove("speaking"));
  const b = el("listenChapter"); if (b) { b.classList.remove("active"); b.innerHTML = ICON_PLAY; b.title = "Read chapter aloud"; }
}
function speakChapter() {
  if (!window.speechSynthesis) { toast("Read-aloud isn’t supported in this browser"); return; }
  if (state.compare) { toast("Turn off Compare to listen"); return; }
  const verses = curBook().chapters[state.chapter] || [];
  speaking = true;
  const b = el("listenChapter"); b.classList.add("active"); b.innerHTML = ICON_STOP; b.title = "Stop";
  let i = 0;
  const next = () => {
    if (!speaking || i >= verses.length) { stopSpeak(); return; }
    const idx = i;
    document.querySelectorAll(".verse.speaking").forEach((n) => n.classList.remove("speaking"));
    const vEl = el(`v${idx + 1}`); if (vEl) { vEl.classList.add("speaking"); vEl.scrollIntoView({ block: "center" }); }
    const u = makeUtterance(verses[idx]);
    u.onend = () => { i++; if (speaking) setTimeout(next, 350); };   // a gentle pause between verses
    window.speechSynthesis.speak(u);
  };
  next();
}
function speakText(t) {
  if (!window.speechSynthesis) { toast("Read-aloud isn’t supported in this browser"); return; }
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(makeUtterance(t));
}

// Pre-rendered narration (scripts/tts_chapter.py) when present; browser voice otherwise.
const chapterAudio = new Audio();
let audioPlaying = false;
let audioManifest = null;
async function loadAudioManifest() {
  if (audioManifest === null) {
    try { audioManifest = await (await fetch("../library/audio/manifest.json")).json(); }
    catch { audioManifest = { files: {} }; }
  }
  return audioManifest;
}
function chapterAudioFile(m) {
  return !state.compare && m.files && m.files[state.primary]
    && m.files[state.primary][state.code] && m.files[state.primary][state.code][state.chapter + 1];
}
function setListenIcon(on) { const b = el("listenChapter"); if (!b) return; b.classList.toggle("active", on); b.innerHTML = on ? ICON_STOP : ICON_PLAY; b.title = on ? "Stop" : "Read chapter aloud"; }
function stopAudio() { audioPlaying = false; try { chapterAudio.pause(); } catch (e) {} }
function stopListening() { stopSpeak(); stopAudio(); setListenIcon(false); }
chapterAudio.addEventListener("ended", () => { audioPlaying = false; setListenIcon(false); });
function playChapterAudio(path) {
  stopSpeak();
  chapterAudio.src = path;
  chapterAudio.play()
    .then(() => { audioPlaying = true; setListenIcon(true); })
    .catch(() => { audioPlaying = false; setListenIcon(false); toast("Couldn’t play audio — using the browser voice"); speakChapter(); });
}

/* ---------- render ---------- */
/* Books outside the Protestant 66 are marked wherever they are read, so nobody
   meets one without knowing which traditions receive it. */
const versionMeta = () => (manifest && manifest.versions.find((v) => v.id === state.primary)) || null;
const outsideCanon = () => { const m = versionMeta(); return !!(m && m.canonical === false); };
const disputed = (code) => {
  const p = primary();
  return !!(p && p.deuterocanonical && p.deuterocanonical.indexOf(code) >= 0);
};
function renderSelectors() {
  const p = primary(), book = curBook();
  el("bookSel").innerHTML = p.books.map((b) =>
    `<option value="${b.code}" ${b.code === state.code ? "selected" : ""}>${b.name}${disputed(b.code) ? " ✦" : ""}</option>`).join("");
  el("chapSel").innerHTML = book.chapters.map((_, i) => `<option value="${i}" ${i === state.chapter ? "selected" : ""}>${i + 1}</option>`).join("");
  el("refLabel").innerHTML = `${esc(book.name)} ${state.chapter + 1}`
    + (disputed(book.code)
        ? ` <button class="canonbadge" id="refCanon" title="Which traditions receive this book?">✦ disputed between traditions</button>`
        : (outsideCanon()
            ? ` <button class="canonbadge canonbadge--outside" id="refCanon" title="Where does this text stand?">outside the biblical canon</button>` : ""));
}

function renderChapter() {
  const p = primary(), book = curBook(), c1 = state.chapter + 1;
  const chA = book.chapters[state.chapter] || [];
  const cmp = state.compare ? cache.get(state.compare) : null;

  if (cmp) {
    const bookB = cmp._byCode[book.code];
    const chB = (bookB && bookB.chapters[state.chapter]) || [];
    const rows = Math.max(chA.length, chB.length);
    let h = `<div class="cmp"><div class="cmp__head">${p.name}</div><div class="cmp__head">${cmp.name}</div>`;
    for (let i = 0; i < rows; i++)
      h += `<div class="row"><div class="cell"><span class="vnum">${i + 1}</span>${escRed(chA[i] || "", redRanges(book.code, c1, i + 1))}</div><div class="cell"><span class="vnum">${i + 1}</span>${esc(chB[i] || "")}</div></div>`;
    el("reader").innerHTML = h + `</div>`;
    return;
  }
  el("reader").innerHTML = chA.map((t, i) => {
    const v1 = i + 1, key = vk(book.code, c1, v1);
    const color = store.highlights[key], note = store.notes[key];
    const sel = state.sel && state.sel.code === book.code && state.sel.c1 === c1 && v1 >= state.sel.from && v1 <= state.sel.to;
    return `<p class="verse${color ? ` hl-${color}` : ""}${sel ? " sel" : ""}" id="v${v1}" data-v="${v1}">`
      + `<span class="vnum" role="button" tabindex="0">${v1}</span>${escRed(t, redRanges(book.code, c1, v1))}`
      + (note ? `<span class="noteflag" title="note">✎</span><span class="noteline">${esc(note)}</span>` : "")
      + `</p>`;
  }).join("");
}

function renderAttribution() {
  const ids = [state.primary, state.compare].filter(Boolean);
  el("attribution").textContent = "Texts: " + ids.map((id) => cache.get(id).attribution).join("  ·  ");
}

const PANELS = ["results", "related", "commentary", "canon", "woj", "threads", "study", "prayer"];
let lastFocus = null;

/* On a wide screen a reference panel opens BESIDE the text rather than instead
   of it — reading with something open is the whole posture of study. On a narrow
   one it takes the screen, as before. */
function showOnly(section) {
  for (const p of PANELS) el(p).hidden = p !== section;
  const open = section !== "reader";
  el("reader").hidden = false;
  document.body.classList.toggle("panel-open", open);
  if (open) {
    const panel = el(section);
    const head = panel.querySelector(".panel__head");
    if (head) { head.setAttribute("tabindex", "-1"); head.focus({ preventScroll: true }); }
  } else if (lastFocus && document.contains(lastFocus)) {
    lastFocus.focus({ preventScroll: true });
    lastFocus = null;
  }
}

/* Panels live in the URL, so they can be shared and the Back button closes them. */
const PANEL_ROUTES = {
  canon: { open: () => openCanon() },
  woj: { open: (arg) => openWoj(arg) },
  threads: { open: (arg) => openThreads(arg) },
  prayer: { open: () => openPrayer() },
  study: { open: () => renderStudy() },
};
let readingHash = "";
function panelHash(name, arg) { return `#/panel/${name}${arg ? "/" + encodeURIComponent(arg) : ""}`; }
function openPanelRoute(name, arg) {
  lastFocus = document.activeElement;
  closeStudyMenu();
  if (!location.hash.startsWith("#/panel/")) readingHash = location.hash;
  hashLock = true;
  location.hash = panelHash(name, arg);
  setTimeout(() => (hashLock = false), 0);
  const route = PANEL_ROUTES[name];
  if (route) route.open(arg);
}
function closePanel() {
  if (location.hash.startsWith("#/panel/")) { history.back(); return; }
  showOnly("reader");
}

/* ---------- navigation + permalinks ---------- */
function updateHash() {
  const name = curBook().name;
  hashLock = true;
  location.hash = `/${state.primary}/${encodeURIComponent(name)}/${state.chapter + 1}`;
  setTimeout(() => (hashLock = false), 0);
}
/* Every navigation goes through here, so a book is always fetched before it is
   drawn — and the compare column's book too. */
async function gotoChapter(code, chapIdx, highlightVerse) {
  stopListening();
  const p = primary();
  const book = p._byCode[code] || p.books[0];
  state.code = book.code;
  state.chapter = Math.max(0, Math.min(chapIdx, book.chapters.length - 1));
  await ensureBook(state.primary, state.code);
  if (state.compare && bookAt(state.compare, state.code)) {
    try { await ensureBook(state.compare, state.code); } catch (e) { /* absent in that version */ }
  }
  renderSelectors(); renderChapter(); showOnly("reader"); updateHash();
  maybeLoadRedLetters();
  if (highlightVerse) { const v = el(`v${highlightVerse}`); if (v) { v.scrollIntoView({ block: "center" }); } }
  else window.scrollTo({ top: 0 });
}
function step(d) {
  const p = primary();
  let bi = bookIndex(state.primary, state.code), c = state.chapter + d;
  if (c < 0) { if (--bi < 0) return; c = p.books[bi].chapters.length - 1; }
  else if (c >= p.books[bi].chapters.length) { if (++bi >= p.books.length) return; c = 0; }
  clearSelection(); gotoChapter(p.books[bi].code, c);
}
async function applyHash() {
  const panel = location.hash.match(/^#\/panel\/([a-z]+)(?:\/([^/]+))?/);
  if (panel) {
    const route = PANEL_ROUTES[panel[1]];
    if (route) { await route.open(panel[2] ? decodeURIComponent(panel[2]) : undefined); return true; }
    return false;
  }
  const m = location.hash.match(/^#\/([^/]+)\/([^/]+)\/(\d+)(?:\/(\d+))?/);
  if (!m) return false;
  const [, ver, bookEnc, ch, v] = m;
  if (!manifest.versions.some((x) => x.id === ver)) return false;
  state.primary = ver; el("verSel").value = ver; await loadVersion(ver);
  const code = codeFor(decodeURIComponent(bookEnc));
  if (!code || !primary()._byCode[code]) return false;
  await gotoChapter(code, (+ch) - 1, v ? +v : 0);
  renderAttribution();
  return true;
}

/* ---------- verse selection + action bar (supports a contiguous range) ---------- */
function refreshSaveOptions() {
  el("vbSave").innerHTML = `<option value="">Save to…</option>`
    + store.collections.map((c) => `<option value="${c.id}">＋ ${esc(c.name)}</option>`).join("")
    + `<option value="__new">＋ New collection…</option>`;
}
function selectVerse(v1, extend) {
  const book = curBook(), c1 = state.chapter + 1;
  if (extend && state.sel && state.sel.c1 === c1 && state.sel.code === book.code) {
    const a = state.anchor || state.sel.from;
    state.sel = { code: book.code, name: book.name, c1, from: Math.min(a, v1), to: Math.max(a, v1) };
  } else {
    state.anchor = v1;
    state.sel = { code: book.code, name: book.name, c1, from: v1, to: v1 };
  }
  renderChapter();
  el("verseBarRef").textContent = selRefText();
  refreshSaveOptions();
  el("verseBar").hidden = false;
}
function clearSelection() { state.sel = null; state.anchor = null; el("verseBar").hidden = true; }
const selRefText = () => { const s = state.sel; return s.from === s.to ? `${s.name} ${s.c1}:${s.from}` : `${s.name} ${s.c1}:${s.from}–${s.to}`; };
function selKeys() { const s = state.sel, out = []; for (let v = s.from; v <= s.to; v++) out.push(vk(s.code, s.c1, v)); return out; }
function selVerses() {
  const s = state.sel, b = bookAt(state.primary, s.code), ch = (b && b.chapters[s.c1 - 1]) || [];
  const out = []; for (let v = s.from; v <= s.to; v++) out.push(ch[v - 1] || ""); return out;
}
const selPassageText = () => selVerses().join(" ");
const selFrom = () => ({ name: state.sel.name, c1: state.sel.c1, v1: state.sel.from });

/* ---------- related verses (cross-references) ---------------------------------
   Keyed CODE.CHAPTER.VERSE and stored one file per book, so looking up a verse
   fetches that book's references rather than all 3.7 MB of them. */
function xrefDisplay(t) {
  const [main, end] = t.split("-");
  const [code, ch, v] = main.split(".");
  return { code, ch: +ch, v: +v, label: `${nameFor(code)} ${+ch}:${+v}${end ? "–" + end : ""}` };
}
async function loadCrossrefs(code) {
  if (!xrefMeta) xrefMeta = await (await fetch("../library/crossrefs/index.json")).json();
  if (!crossrefs.has(code)) {
    if (xrefMeta.books.indexOf(code) < 0) crossrefs.set(code, {});
    else crossrefs.set(code, await (await fetch(xrefUrl(code))).json());
  }
  return crossrefs.get(code);
}
async function showRelated() {
  if (!state.sel) return;
  const s = state.sel;
  const refs = await loadCrossrefs(s.code);
  const list = refs[vref(s.code, s.c1, s.from)] || [];
  if (!xrefMeta.books.length || xrefMeta.books.indexOf(s.code) < 0) {
    el("relatedHead").textContent = `Related — not available for ${s.name}`;
    el("relatedList").innerHTML = `<li>The cross-reference set covers the 66-book canon. `
      + `${esc(s.name)} is outside it, so Berean shows nothing rather than guessing.</li>`;
    el("relatedAttr").textContent = "";
    showOnly("related"); window.scrollTo({ top: 0 }); return;
  }
  el("relatedHead").textContent = `Related to ${s.name} ${s.c1}:${s.from} — ${list.length} cross-reference${list.length === 1 ? "" : "s"}`;
  // fetch only the books actually cited, then fill the previews in
  const rows = list.map(xrefDisplay);
  el("relatedList").innerHTML = rows.map((r) =>
    `<li data-code="${esc(r.code)}" data-c="${r.ch - 1}" data-v="${r.v}">`
    + `<span class="r-ref">${esc(r.label)}</span> <span class="r-text" data-preview="${esc(vref(r.code, r.ch, r.v))}"></span></li>`).join("")
    || "<li>No cross-references for this verse.</li>";
  el("relatedAttr").textContent = xrefMeta.attribution;
  showOnly("related");
  window.scrollTo({ top: 0 });
  const p = primary();
  await Promise.all([...new Set(rows.map((r) => r.code))]
    .filter((c) => p._byCode[c])
    .map((c) => ensureBook(state.primary, c).catch(() => null)));
  for (const r of rows) {
    const b = p._byCode[r.code];
    const text = b && b.chapters[r.ch - 1] && b.chapters[r.ch - 1][r.v - 1];
    const node = el("relatedList").querySelector(`[data-preview="${vref(r.code, r.ch, r.v)}"]`);
    if (node) node.textContent = (text || "").slice(0, 160);
  }
}

/* ---------- search ------------------------------------------------------------
   Reading needs one book; searching needs the whole text, so this is the one
   place that pulls a version's bundle — and only when someone actually searches. */
async function runSearch(q, allVersions) {
  q = q.trim(); if (!q) return;
  const needle = q.toLowerCase();
  const wordRe = new RegExp(`\\b${q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "i");
  const ids = allVersions ? manifest.versions.map((v) => v.id) : [state.primary];
  el("resultsCount").textContent = "Searching…";
  el("resultsList").innerHTML = "";
  showOnly("results");
  const hits = [];
  const CAP = 500;
  for (const id of ids) {
    const d = await loadBundle(id);
    outer:
    for (const b of d.books) {
      const code = codeFor(b.name);
      for (let ci = 0; ci < b.chapters.length; ci++) {
        const ch = b.chapters[ci];
        for (let vi = 0; vi < ch.length; vi++) {
          const txt = ch[vi];
          if (txt && txt.toLowerCase().includes(needle)) {
            hits.push({ id, vid: d.name, code, ci, vi, ref: `${b.name} ${ci + 1}:${vi + 1}`,
                        text: txt, word: wordRe.test(txt) });
            if (hits.length >= CAP) break outer;
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
    `<li data-id="${h.id}" data-code="${h.code}" data-c="${h.ci}" data-v="${h.vi + 1}"><span class="r-ref">${h.ref}</span> ${allVersions ? `<span class="r-ver">${h.vid}</span>` : ""} <span class="r-text">${mark(h.text)}</span></li>`
  ).join("") || "<li>No results.</li>";
  window.scrollTo({ top: 0 });
}

/* ---------- My Study panel ---------- */
async function renderStudy() {
  const p = primary();
  const refFromKey = (key) => { const [code, c, v] = key.split("."); return { code, name: nameFor(code), c: +c, v: +v }; };
  const jump = (key) => { const r = refFromKey(key); if (p._byCode[r.code]) { clearSelection(); gotoChapter(r.code, r.c - 1, r.v); } };
  const textOf = (key) => { const r = refFromKey(key); const b = p._byCode[r.code]; return (b && b.chapters[r.c - 1] && b.chapters[r.c - 1][r.v - 1]) || ""; };

  // pull in whatever books this reader's own study touches, so previews are real
  const keys = [...Object.keys(store.highlights), ...Object.keys(store.notes),
                ...store.collections.flatMap((c) => c.verses)];
  await Promise.all([...new Set(keys.map((k) => k.split(".")[0]))]
    .filter((code) => p._byCode[code])
    .map((code) => ensureBook(state.primary, code).catch(() => null)));

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
    const seen = new Set(store.prayers.map((p) => p.id));
    for (const p of d.prayers || []) if (!seen.has(p.id)) { store.prayers.push(p); seen.add(p.id); }
    saveStore(); renderStudy(); toast("Study imported (merged)");
  } catch { toast("Import failed — not a valid file"); } };
  r.readAsText(file);
}

/* ---------- commentary (public-domain, sourced; the ground truth AI will cite) ---------- */
const COMMENTARY_MANIFEST = "../library/commentary/manifest.json";
let commentaryManifest = null;
const commentaryCache = new Map();
async function loadCommentaryManifest() {
  if (commentaryManifest === null) {
    try { commentaryManifest = await (await fetch(COMMENTARY_MANIFEST)).json(); }
    catch { commentaryManifest = { commentaries: [] }; }
  }
  return commentaryManifest;
}
const commentariesForBook = (m, code) => (m.commentaries || []).filter((c) => (c.books || []).includes(code));
async function openCommentary() {
  const m = await loadCommentaryManifest();
  const bookName = curBook().name;
  const avail = commentariesForBook(m, state.code);
  if (!avail.length) {
    el("commentarySel").innerHTML = "";
    el("commentaryHead").textContent = `Commentary — ${bookName} ${state.chapter + 1}`;
    el("commentaryBody").innerHTML = `<p class="empty">No commentary is loaded for ${esc(bookName)} yet. Generate it with <code>python3 scripts/ingest_commentary.py --commentary matthew-henry --book "${esc(bookName)}"</code>.</p>`;
    el("commentaryAttr").textContent = "";
    showOnly("commentary"); window.scrollTo({ top: 0 }); return;
  }
  const want = avail.some((c) => c.id === comfort.commentary) ? comfort.commentary : avail[0].id;
  el("commentarySel").innerHTML = avail.map((c) => `<option value="${c.id}" ${c.id === want ? "selected" : ""}>${esc(c.name)}</option>`).join("");
  await renderCommentary(want);
  showOnly("commentary"); window.scrollTo({ top: 0 });
}
async function renderCommentary(cid) {
  const m = await loadCommentaryManifest();
  const meta = (m.commentaries || []).find((c) => c.id === cid);
  const bookName = curBook().name, cn = state.chapter + 1;
  el("commentaryHead").textContent = `${meta ? meta.name : "Commentary"} — ${bookName} ${cn}`;
  const key = `${cid}/${state.code}/${cn}`;
  let data = commentaryCache.get(key);
  if (data === undefined) {
    try { data = await (await fetch(`../library/commentary/${cid}/${state.code}/${cn}.json`)).json(); }
    catch { data = null; }
    commentaryCache.set(key, data);
  }
  if (!data || !data.blocks || !data.blocks.length) {
    el("commentaryBody").innerHTML = `<p class="empty">No commentary for ${esc(bookName)} ${cn} in this work yet.</p>`;
  } else {
    const paras = (t) => t.split(/\n+/).map((p) => p.trim()).filter(Boolean).map((p) => `<p>${esc(p)}</p>`).join("") || `<p>${esc(t)}</p>`;
    el("commentaryBody").innerHTML =
      (data.intro ? `<div class="intro">${esc(data.intro)}</div>` : "")
      + data.blocks.map((b) => `<div class="block" id="cm-v${b.verse}"><span class="block__ref" data-v="${b.verse}">${esc(bookName)} ${cn}:${b.verse}</span>${paras(b.text)}</div>`).join("");
  }
  el("commentaryAttr").textContent = meta ? meta.attribution : "";
  comfort.commentary = cid; savePrefs();
}

/* ---------- the study launcher + keyboard -------------------------------------
   One entry point instead of a row of buttons that grows with every feature. */
function closeStudyMenu() {
  const m = el("studyMenu"); if (!m || m.hidden) return;
  m.hidden = true;
  el("studyMenuBtn").setAttribute("aria-expanded", "false");
}
function toggleStudyMenu() {
  const m = el("studyMenu"), open = m.hidden;
  m.hidden = !open;
  el("studyMenuBtn").setAttribute("aria-expanded", String(open));
  if (open) { const first = m.querySelector("button"); if (first) first.focus(); }
}
function bindKeys() {
  document.addEventListener("keydown", (e) => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target.tagName || "").toUpperCase());
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); toggleStudyMenu(); return; }
    if (e.key === "Escape") {
      if (!el("studyMenu").hidden) { closeStudyMenu(); el("studyMenuBtn").focus(); return; }
      if (state.sel) { clearSelection(); renderChapter(); return; }
      if (document.body.classList.contains("panel-open")) closePanel();
      return;
    }
    if (typing) return;
    if (e.key === "/") { e.preventDefault(); el("searchInput").focus(); return; }
    if (document.body.classList.contains("panel-open")) return;
    if (e.key === "ArrowRight") { step(1); }
    else if (e.key === "ArrowLeft") { step(-1); }
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".launcher")) closeStudyMenu();
  });
}

/* ---------- Canon — which tradition receives which book -----------------------
   Berean labels and lets the reader open the actual book; it does not adjudicate.
   Data: library/canons.json (hand-authored reference, with its sources listed). */
const CANONS_URL = "../library/canons.json";
let canons = null;

async function loadCanons() {
  if (!canons) canons = await (await fetch(CANONS_URL)).json();
  return canons;
}
async function openCanon() {
  try { await loadCanons(); } catch { toast("Could not load the canon data"); return; }
  renderCanon();
  showOnly("canon");
  window.scrollTo({ top: 0 });
}
function renderCanon() {
  const d = canons, tr = d.traditions;
  const label = (st) => (d.statusLabels && d.statusLabels[st]) || st;
  const cell = (st) => `<td class="canon__cell canon__cell--${st}" title="${esc(label(st))}">`
    + `<span class="canon__dot"></span><span class="canon__st">${esc(label(st))}</span></td>`;

  el("canonHead").innerHTML = `Canon <span class="tiny">— who receives which book</span>`;
  el("canonBody").innerHTML =
      `<p class="canon__intro">${esc(d.framing)}</p>`
    + `<div class="canon__traditions">` + tr.map((t) =>
        `<div class="canon__tradition"><h3>${esc(t.name)} <span class="canon__count">${esc(t.count)}</span></h3>`
        + `<p class="tiny">${esc(t.shape)}</p><p>${esc(t.note)}</p></div>`).join("") + `</div>`
    + `<p class="canon__shared"><strong>${d.shared.count} books are shared.</strong> ${esc(d.shared.note)}</p>`
    + `<div class="canon__tablewrap"><table class="canon__table">`
    + `<thead><tr><th>Book</th>` + tr.map((t) => `<th>${esc(t.name)}</th>`).join("") + `</tr></thead><tbody>`
    + d.books.map((b) => {
        const open = b.hosted
          ? `<button class="canon__open" data-book="${esc(b.code || "")}" data-ver="${esc(b.hosted)}">${esc(b.name)} →</button>`
          : `<span class="canon__book">${esc(b.name)}</span> <span class="canon__tag">not hosted</span>`;
        return `<tr><th scope="row"><div>${open}</div>`
          + `<div class="tiny">${esc(b.era)} · ${esc(b.note)}</div></th>`
          + tr.map((t) => cell(b.in[t.id] || "absent")).join("") + `</tr>`;
      }).join("")
    + `</tbody></table></div>`
    + `<div class="canon__tanakh"><h3>The Jewish order</h3><p>${esc(d.tanakhOrder.note)}</p>`
    + d.tanakhOrder.sections.map((sec) =>
        `<p class="canon__section"><strong>${esc(sec.name)}</strong> <span class="tiny">${esc(sec.meaning)}</span> — `
        + sec.books.map((x) => esc(x)).join(" · ") + `</p>`).join("")
    + `</div>`
    + `<div class="canon__sources"><h3>Sources</h3><ul>`
    + d.sources.map((x) => `<li>${esc(x)}</li>`).join("") + `</ul>`
    + `<p class="tiny">${esc(d.honesty)}</p><p class="tiny">${esc(d.note)}</p></div>`;
}

/* Open a disputed book in the version that carries it. */
async function openCanonBook(code, versionId) {
  try { await loadVersion(versionId); } catch { toast("Could not load that text"); return; }
  if (!cache.get(versionId)._byCode[code]) { toast("Not in this text"); return; }
  if (versionId !== state.primary) {
    state.primary = versionId; el("verSel").value = versionId;
    if (state.compare === versionId) { state.compare = null; el("cmpSel").value = ""; }
    renderAttribution(); savePrefs();
  }
  clearSelection();
  await gotoChapter(code, 0);
}

/* ---------- The Words of Jesus ----------------------------------------------
   Compiled by scripts/build_words_of_jesus.py from the BSB's own quotation marks.
   The file stores character offsets, never a copy of the text, so the compiled
   book is always sliced live out of the translation the reader already loaded. */
const WOJ_URL = "../library/words-of-jesus.json";
let woj = null;          // the compiled book
let redIndex = null;     // { book: { chapter: { verse: [[start, end], …] } } } — for red letters
let wojBook = null;      // which book the panel is showing

async function loadWoj() {
  if (!woj) {
    woj = await (await fetch(WOJ_URL)).json();
    redIndex = buildRedIndex(woj);
  }
  await loadVersion(woj.version);      // the compiled book always quotes its source text
  return woj;
}
/* Red letters only exist in the New Testament, so the compiled book is fetched
   when a reader actually opens one — never for Genesis. */
const inNT = (code) => !!(registry && registry.byCode[code] && registry.byCode[code].section === "nt");
async function maybeLoadRedLetters() {
  if (!comfort.red || woj || !inNT(state.code)) return;
  try { await loadWoj(); renderChapter(); } catch (e) { /* red letters simply stay off */ }
}

/* The panel slices its text out of the source translation, so the books it is
   about to show have to be here first. */
async function ensureWojBooks(codes) {
  await Promise.all(codes.map((c) => ensureBook(woj.version, c).catch(() => null)));
}

/* Character ranges of Jesus' speech, per verse, so the reader can red-letter it. */
function buildRedIndex(d) {
  const idx = {};
  for (const entry of d.books) {
    const byChapter = (idx[entry.code] = idx[entry.code] || {});
    for (const p of entry.passages) {
      if (p.voice !== "jesus") continue;
      for (const part of p.parts) {
        const [c1, v1, o1] = part.from, [c2, v2, o2] = part.to;
        for (let c = c1; c <= c2; c++) {
          const lo = c === c1 ? v1 : 1, hi = c === c2 ? v2 : 1e4;
          const verses = (byChapter[c] = byChapter[c] || {});
          for (let v = lo; v <= hi && v <= (c === c2 ? v2 : lo + 400); v++) {
            const a = (c === c1 && v === v1) ? o1 : 0;
            const b = (c === c2 && v === v2) ? o2 : 1e6;   // to end of verse
            (verses[v] = verses[v] || []).push([a, b]);
          }
        }
      }
    }
  }
  return idx;
}
const redRanges = (code, c1, v1) =>
  (comfort.red && redIndex && woj && state.primary === woj.version
    && redIndex[code] && redIndex[code][c1] && redIndex[code][c1][v1]) || null;

/* Escape a verse, wrapping the ranges Jesus speaks. Offsets are into the raw
   text, so each piece is escaped after slicing, never before. */
function escRed(text, ranges) {
  if (!ranges || !ranges.length) return esc(text);
  const merged = [];
  for (const [a, b] of ranges.slice().sort((x, y) => x[0] - y[0])) {
    const s = Math.max(0, Math.min(a, text.length)), e = Math.max(s, Math.min(b, text.length));
    if (e <= s) continue;
    const last = merged[merged.length - 1];
    if (last && s <= last[1]) last[1] = Math.max(last[1], e); else merged.push([s, e]);
  }
  let out = "", pos = 0;
  for (const [a, b] of merged) {
    if (a > pos) out += esc(text.slice(pos, a));
    out += `<span class="jw">${esc(text.slice(a, b))}</span>`;
    pos = b;
  }
  return out + esc(text.slice(pos));
}

/* The text of one compiled passage, sliced live out of the source translation. */
function wojText(code, passage) {
  const src = cache.get(woj.version), book = src && src._byCode[code];
  if (!book) return "";
  const out = [];
  for (const part of passage.parts) {
    const [c1, v1, o1] = part.from, [c2, v2, o2] = part.to;
    for (let c = c1; c <= c2; c++) {
      const chapter = book.chapters[c - 1] || [];
      const lo = c === c1 ? v1 : 1, hi = c === c2 ? v2 : chapter.length;
      for (let v = lo; v <= hi; v++) {
        const t = chapter[v - 1] || "";
        const a = (c === c1 && v === v1) ? o1 : 0;
        const b = (c === c2 && v === v2) ? o2 : t.length;
        const piece = t.slice(a, b).trim();
        if (piece) out.push(piece);
      }
    }
  }
  return out.join(" ").replace(/[“”]/g, "").trim();
}

async function openWoj(code) {
  await loadWoj();
  if (code && woj.books.some((b) => b.code === code)) wojBook = code;
  if (!wojBook) wojBook = woj.books[0].code;
  await ensureWojBooks([wojBook]);
  renderWoj();
  showOnly("woj");
  window.scrollTo({ top: 0 });
}
function renderWoj() {
  const d = woj;
  el("wojHead").innerHTML = `${esc(d.title)} <span class="tiny">— ${esc(d.subtitle)} · `
    + `${d.stats.verses} verses · ${esc(cache.get(d.version).name)}</span>`;
  el("wojBooks").innerHTML = d.books.map((b) =>
    `<button class="woj__tab${b.code === wojBook ? " is-on" : ""}" data-wojbook="${esc(b.code)}"`
    + ` role="tab" aria-selected="${b.code === wojBook}">${esc(b.book)}`
    + ` <span class="tiny">${b.passages.filter((p) => p.voice === "jesus").length}</span></button>`).join("");
  const entry = d.books.find((b) => b.code === wojBook) || d.books[0];
  el("wojBody").innerHTML = entry.passages.map((p) => {
    const text = wojText(entry.code, p);
    if (!text) return "";
    const tags = (p.voice === "father"
        ? `<span class="woj__tag woj__tag--father">${esc(d.voices.father)}</span>` : "")
      + (p.src === "curated" ? `<span class="woj__tag" title="${esc(p.why || "")}">listed by hand</span>` : "");
    return `<div class="woj__passage woj__passage--${p.voice}">`
      + `<div class="woj__head"><button class="woj__ref" data-ref="${esc(p.ref)}">${esc(p.ref)} →</button>${tags}</div>`
      + `<p class="woj__text">${esc(text)}</p></div>`;
  }).join("");
  el("wojNote").textContent = d.note + "  " + d.attribution;
}

/* ---------- Threads — follow a documented trail across texts (all citations real) ---------- */
const THREADS_URL = "../library/threads.json";
let threadsData = null;
async function loadThreads() {
  if (!threadsData) { try { threadsData = await (await fetch(THREADS_URL)).json(); } catch { threadsData = { threads: [], statusLabels: {}, note: "" }; } }
  return threadsData;
}
async function openThreads(id) {
  await loadThreads();
  if (id && (threadsData.threads || []).some((t) => t.id === id)) await renderThread(id);
  else renderThreadList();
  showOnly("threads"); window.scrollTo({ top: 0 });
}
function renderThreadList() {
  const d = threadsData;
  el("threadsHead").innerHTML = `Threads <span class="tiny">— follow a documented trail; examine for yourself</span>`;
  el("threadsBody").innerHTML = `<p class="threads__intro">${esc(d.note || "")}</p>`
    + (d.threads || []).map((t) => `<div class="thread-card"><h3>${esc(t.title)}</h3><p>${esc(t.summary)}</p><button class="vbbtn" data-thread="${t.id}">Follow this thread →</button></div>`).join("");
}
async function renderThread(id) {
  const d = threadsData, t = (d.threads || []).find((x) => x.id === id);
  if (!t) return;
  for (const v of new Set((t.steps || []).map((s) => s.version).filter(Boolean))) {
    try {
      await loadVersion(v);
      await ensureRefs((t.steps || []).filter((s) => s.version === v).map((s) => s.ref), v);
    } catch (e) { /* a step Berean cannot resolve is shown as cited by reference */ }
  }
  const badge = (s) => `<span class="thread-badge thread-badge--${s}">${esc((d.statusLabels && d.statusLabels[s]) || s)}</span>`;
  const steps = (t.steps || []).map((s) => {
    const res = s.version ? resolveRef(s.ref, s.version) : null;
    const verse = res ? `<p class="thread-verse">“${esc(res.text)}”</p>`
      : `<p class="thread-verse thread-verse--missing">(text not loaded in Berean yet — cited by reference)</p>`;
    const nav = res ? `<button class="linkbtn" data-ref="${esc(s.ref)}" data-ver="${esc(s.version)}">open ${esc(s.ref)} →</button>` : "";
    return `<div class="thread-step"><div class="thread-step__head"><span class="thread-step__ref">${esc(s.ref)}</span>${badge(s.status)}<span class="tiny">${esc(s.tradition || "")}</span></div>${verse}<p class="thread-note">${esc(s.note)}</p>${nav}</div>`;
  }).join("");
  el("threadsHead").textContent = t.title;
  el("threadsBody").innerHTML = `<button class="linkbtn" data-back="1">← all threads</button>`
    + `<p class="threads__intro">${esc(t.summary)}</p>`
    + `<div class="thread-steps">${steps}</div>`
    + `<div class="thread-sources"><h3>Sources</h3><ul>${(t.sources || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul><p class="tiny">${esc(d.note || "")}</p></div>`;
}
async function navigateRef(refStr, versionId) {
  const m = REF_RE.exec(refStr); if (!m) return;
  const code = codeFor(m[1].trim());
  const ch = +m[2], v = +m[3];
  if (versionId && versionId !== state.primary) { await loadVersion(versionId); state.primary = versionId; el("verSel").value = versionId; renderAttribution(); savePrefs(); }
  if (!code || !primary()._byCode[code]) { toast("Passage not in this text"); return; }
  clearSelection(); await gotoChapter(code, ch - 1, v);
}

/* ---------- prayer builder ---------- */
const PRAYERS_URL = "../library/prayers.json";
let prayers = null;
const REF_RE = /^(\d?\s?[A-Za-z ]+?)\s+(\d+):(\d+)(?:-(\d+))?$/;
async function loadPrayers() { if (!prayers) prayers = await (await fetch(PRAYERS_URL)).json(); return prayers; }

// Pull the actual verse text from a loaded version — prayers.json stores references only.
/* References resolve out of loaded books, and books arrive one at a time — so
   anything about to resolve a list of them fetches those books first. */
async function ensureRefs(refs, versionId) {
  const codes = [...new Set(refs.map((r) => {
    const m = REF_RE.exec(String(r).trim());
    return m ? codeFor(m[1].trim()) : null;
  }).filter(Boolean))];
  await Promise.all(codes.map((c) => ensureBook(versionId, c).catch(() => null)));
}

function resolveRef(refStr, versionId) {
  const m = REF_RE.exec(refStr); if (!m) return null;
  const code = codeFor(m[1].trim());
  const ch = +m[2], v1 = +m[3], v2 = m[4] ? +m[4] : v1;
  const d = cache.get(versionId); if (!d || !code) return null;
  const b = d._byCode[code]; if (!b || !b.chapters[ch - 1]) return null;
  const chap = b.chapters[ch - 1], parts = [];
  for (let v = v1; v <= v2 && v <= chap.length; v++) parts.push(chap[v - 1]);
  return parts.length ? { ref: refStr, text: parts.join(" ") } : null;
}
function composePrayer(subj, opts) {
  const versionId = opts.tone === "traditional" ? "KJV" : "BSB";
  const forOther = opts.forWhom === "other" && (opts.name || "").trim();
  const name = (opts.name || "").trim();
  const fill = (s) => s.replace(/\{name\}/g, name || "them");
  const petition = fill(forOther ? subj.petitionOther : subj.petitionSelf);
  const n = opts.style === "simple" ? 1 : 2;
  const verseLines = [], refsUsed = [];
  for (const r of subj.verses.slice(0, n)) {
    const res = resolveRef(r, versionId);
    if (res) { verseLines.push(`Your Word says, “${res.text}” (${res.ref}).`); refsUsed.push(res.ref); }
  }
  const situation = (opts.situation || "").trim();
  const sitLine = situation
    ? (forOther ? `You know what ${name || "they"} ${name ? "is" : "are"} facing: ${situation}.`
                : `You know what is on my heart: ${situation}.`)
    : "";
  const close = opts.close === "amen" ? "Amen." : "In Jesus’ name, amen.";
  const paras = [];
  if (opts.style === "simple") {
    paras.push(`Heavenly Father, You are ${subj.attribute}.`);
    if (verseLines[0]) paras.push(verseLines[0]);
    paras.push([sitLine, petition].filter(Boolean).join(" "));
    paras.push(close);
  } else {
    paras.push(`Heavenly Father, You are ${subj.attribute}. Thank You ${subj.thanks}.`);
    if (verseLines[0]) paras.push(verseLines[0]);
    if (verseLines[1]) paras.push(verseLines[1]);
    const opener = forOther ? `I lift up ${name || "this person"} to You today.` : `I come to You today.`;
    paras.push([opener, sitLine, petition].filter(Boolean).join(" "));
    paras.push(`I trust You. ${close}`);
  }
  return { text: paras.join("\n\n"), refs: refsUsed };
}
function renderPrayerSubjects() { el("prSubject").innerHTML = prayers.subjects.map((s) => `<option value="${s.id}">${esc(s.title)}</option>`).join(""); }
async function buildPrayer() {
  await loadPrayers();
  const subj = prayers.subjects.find((s) => s.id === el("prSubject").value) || prayers.subjects[0];
  const tone = el("prTone").value;
  const versionId = tone === "traditional" ? "KJV" : "BSB";
  await loadVersion(versionId);
  await ensureRefs(prayers.subjects.flatMap((s) => s.verses || []), versionId);
  const { text, refs } = composePrayer(subj, {
    tone, style: el("prStyle").value, forWhom: el("prFor").value,
    name: el("prName").value, situation: el("prSituation").value, close: el("prClose").value,
  });
  el("prText").value = text;
  el("prRefs").textContent = refs.length
    ? `Scripture: ${refs.join(" · ")} — ${tone === "traditional" ? "King James Version (Public Domain)" : "Berean Standard Bible (CC0)"}`
    : "";
}
function savePrayer() {
  const text = el("prText").value.trim(); if (!text) { toast("Nothing to save yet"); return; }
  const subj = prayers && prayers.subjects.find((s) => s.id === el("prSubject").value);
  store.prayers.unshift({ id: "p" + Date.now().toString(36), title: subj ? subj.title : "Prayer", subject: el("prSubject").value, text, created: new Date().toISOString().slice(0, 10) });
  saveStore(); renderSavedPrayers(); toast("Prayer saved");
}
function renderSavedPrayers() {
  el("prSaved").innerHTML = store.prayers.length ? store.prayers.map((p) =>
    `<li data-id="${p.id}"><span class="prayer__saved-ref">${esc(p.title)}</span> <span class="tiny">${esc(p.created || "")}</span><br>`
    + `<span class="r-text">${esc(p.text.slice(0, 140))}${p.text.length > 140 ? "…" : ""}</span>`
    + `<div class="prayer__actions" style="margin-top:.4rem"><button class="vbbtn" data-open="${p.id}">Open</button><button class="vbbtn" data-speak="${p.id}">🔊</button><button class="vbbtn" data-del="${p.id}">Delete</button></div></li>`
  ).join("") : `<li class="empty">No saved prayers yet.</li>`;
}
async function openPrayer() {
  await loadPrayers();
  if (!el("prSubject").options.length) renderPrayerSubjects();
  renderSavedPrayers();
  showOnly("prayer"); window.scrollTo({ top: 0 });
}

/* ---------- init ---------- */
async function init() {
  try {
    [manifest] = await Promise.all([(await fetch(MANIFEST_URL)).json(), loadRegistry()]);
  }
  catch { el("reader").innerHTML = `<p>Could not load the library. Run <code>python3 scripts/ingest.py</code> and serve from the repo root.</p>`; return; }
  migrateStore();
  const opts = manifest.versions.map((v) => `<option value="${v.id}">${v.name}</option>`).join("");
  el("verSel").innerHTML = opts;
  el("cmpSel").innerHTML = `<option value="">— none —</option>` + opts;

  // Restore saved preferences (a shared permalink, applied below, still wins over these).
  const prefs = loadPrefs();
  const has = (id) => manifest.versions.some((v) => v.id === id);
  state.primary = (prefs.primary && has(prefs.primary)) ? prefs.primary : manifest.versions[0].id;
  el("verSel").value = state.primary;
  if (prefs.compare && has(prefs.compare) && prefs.compare !== state.primary) { state.compare = prefs.compare; el("cmpSel").value = prefs.compare; await loadVersion(prefs.compare); }
  if (prefs.searchAll) el("searchAll").checked = true;
  comfort.theme = prefs.theme === "dark" ? "dark" : "light";
  if (typeof prefs.size === "number" && prefs.size >= 0.95 && prefs.size <= 1.7) comfort.size = prefs.size;
  if (typeof prefs.rate === "number" && prefs.rate >= 0.6 && prefs.rate <= 1.3) comfort.rate = prefs.rate;
  comfort.voice = prefs.voice || "";
  comfort.commentary = prefs.commentary || "";
  comfort.red = prefs.red !== false;
  applyComfort();

  await loadVersion(state.primary);
  state.code = primary().books[0].code;
  if (!(location.hash && await applyHash())) await gotoChapter(state.code, 0);
  if (state.compare && state.compare === state.primary) { state.compare = null; el("cmpSel").value = ""; renderChapter(); }
  else if (state.compare) { await ensureBook(state.compare, state.code).catch(() => null); renderChapter(); }
  renderAttribution();

  await maybeLoadRedLetters();   // only when the chapter on screen could have any
  applyComfort();

  el("bookSel").addEventListener("change", (e) => { clearSelection(); gotoChapter(e.target.value, 0); });
  el("chapSel").addEventListener("change", (e) => { clearSelection(); gotoChapter(state.code, +e.target.value); });
  el("prevBtn").addEventListener("click", () => step(-1));
  el("nextBtn").addEventListener("click", () => step(1));
  // switching version keeps your place by BOOK, not by position — book 40 is
  // Matthew in a 66-book Bible and Tobit in an 81-book one.
  el("verSel").addEventListener("change", async (e) => {
    state.primary = e.target.value;
    await loadVersion(state.primary);
    const keep = primary()._byCode[state.code] ? state.code : primary().books[0].code;
    if (keep !== state.code) toast(`${nameFor(state.code)} is not in this text`);
    clearSelection(); await gotoChapter(keep, keep === state.code ? state.chapter : 0);
    renderAttribution(); savePrefs();
  });
  el("cmpSel").addEventListener("change", async (e) => {
    state.compare = e.target.value || null;
    if (state.compare) { await loadVersion(state.compare); await ensureBook(state.compare, state.code).catch(() => null); }
    clearSelection(); renderChapter(); showOnly("reader"); renderAttribution(); savePrefs();
  });

  el("searchForm").addEventListener("submit", (e) => { e.preventDefault(); runSearch(el("searchInput").value, el("searchAll").checked); });
  el("searchAll").addEventListener("change", savePrefs);

  // reading comfort + voice
  el("themeBtn").addEventListener("click", () => { comfort.theme = comfort.theme === "dark" ? "light" : "dark"; applyComfort(); savePrefs(); });
  el("textSmaller").addEventListener("click", () => { comfort.size = Math.max(0.95, +(comfort.size - 0.08).toFixed(2)); applyComfort(); savePrefs(); });
  el("textLarger").addEventListener("click", () => { comfort.size = Math.min(1.7, +(comfort.size + 0.08).toFixed(2)); applyComfort(); savePrefs(); });
  el("voiceSel").addEventListener("change", (e) => { comfort.voice = e.target.value; savePrefs(); toast("Voice set — press ▶ to hear it"); });
  loadVoices();
  if (window.speechSynthesis) window.speechSynthesis.onvoiceschanged = loadVoices;
  el("studyBtn").addEventListener("click", () => openPanelRoute("study"));
  el("commentaryBtn").addEventListener("click", openCommentary);
  el("commentarySel").addEventListener("change", (e) => renderCommentary(e.target.value));
  el("commentaryBody").addEventListener("click", (e) => { const r = e.target.closest(".block__ref"); if (r) { clearSelection(); gotoChapter(state.code, state.chapter, +r.dataset.v); } });
  el("studyMenuBtn").addEventListener("click", (e) => { e.stopPropagation(); toggleStudyMenu(); });
  bindKeys();
  el("canonBtn").addEventListener("click", () => openPanelRoute("canon"));
  el("refLabel").addEventListener("click", (e) => { if (e.target.closest("#refCanon")) openCanon(); });
  el("canonBody").addEventListener("click", (e) => {
    const b = e.target.closest("[data-book]"); if (b) openCanonBook(b.dataset.book, b.dataset.ver);
  });
  el("wojBtn").addEventListener("click", () => openPanelRoute("woj", wojBook || undefined));
  el("wojBooks").addEventListener("click", (e) => {
    const b = e.target.closest("[data-wojbook]"); if (!b) return;
    openPanelRoute("woj", b.dataset.wojbook);
  });
  el("wojBody").addEventListener("click", (e) => {
    const r = e.target.closest("[data-ref]"); if (r) navigateRef(r.dataset.ref.split("–")[0], woj.version);
  });
  // Red letters are drawn from the compiled book, so it has to be loaded first.
  el("redBtn").addEventListener("click", async () => {
    comfort.red = !comfort.red;
    if (comfort.red && !woj && inNT(state.code)) { try { await loadWoj(); } catch { toast("Could not load the words of Jesus"); } }
    applyComfort(); renderChapter(); savePrefs();
    toast(comfort.red ? "Red letters on" : "Red letters off");
  });
  el("threadsBtn").addEventListener("click", () => openPanelRoute("threads"));
  el("threadsBody").addEventListener("click", (e) => {
    if (e.target.closest("[data-back]")) { renderThreadList(); window.scrollTo({ top: 0 }); return; }
    const tc = e.target.closest("[data-thread]"); if (tc) { openPanelRoute("threads", tc.dataset.thread); window.scrollTo({ top: 0 }); return; }
    const r = e.target.closest("[data-ref]"); if (r) navigateRef(r.dataset.ref, r.dataset.ver);
  });
  el("prayerBtn").addEventListener("click", () => openPanelRoute("prayer"));
  el("prFor").addEventListener("change", (e) => { el("prNameWrap").hidden = e.target.value !== "other"; });
  el("prGenerate").addEventListener("click", buildPrayer);
  el("prSpeak").addEventListener("click", () => { const t = el("prText").value.trim(); if (t) speakText(t); });
  el("prCopy").addEventListener("click", async () => { const t = el("prText").value.trim(); if (!t) return; await navigator.clipboard.writeText(t).then(() => toast("Prayer copied")).catch(() => toast("Copy failed")); });
  el("prShare").addEventListener("click", () => { const t = el("prText").value.trim(); if (!t) return; shareOrCopy({ title: "A prayer · bereanlamp.com", text: t }); });
  el("prSave").addEventListener("click", savePrayer);
  el("prSaved").addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    if (b.dataset.open) { const p = store.prayers.find((x) => x.id === b.dataset.open); if (p) { el("prText").value = p.text; if (p.subject) el("prSubject").value = p.subject; el("prRefs").textContent = ""; window.scrollTo({ top: 0 }); } }
    else if (b.dataset.speak) { const p = store.prayers.find((x) => x.id === b.dataset.speak); if (p) speakText(p.text); }
    else if (b.dataset.del) { store.prayers = store.prayers.filter((x) => x.id !== b.dataset.del); saveStore(); renderSavedPrayers(); }
  });
  el("exportBtn").addEventListener("click", exportStudy);
  el("importBtn").addEventListener("click", () => el("importFile").click());
  el("importFile").addEventListener("change", (e) => { if (e.target.files[0]) importStudy(e.target.files[0]); });

  document.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", closePanel));

  // verse number → select (single-column reading only); Shift-click extends to a range
  el("reader").addEventListener("click", (e) => {
    const num = e.target.closest(".vnum"); if (!num || state.compare) return;
    const p = num.closest(".verse"); if (p) selectVerse(+p.dataset.v, e.shiftKey);
  });
  // results / related navigation
  el("resultsList").addEventListener("click", async (e) => {
    const li = e.target.closest("li[data-code]"); if (!li) return;
    if (li.dataset.id && li.dataset.id !== state.primary) { state.primary = li.dataset.id; el("verSel").value = li.dataset.id; await loadVersion(state.primary); renderAttribution(); }
    clearSelection(); gotoChapter(li.dataset.code, +li.dataset.c, +li.dataset.v);
  });
  el("relatedList").addEventListener("click", (e) => { const li = e.target.closest("li[data-code]"); if (!li) return; clearSelection(); gotoChapter(li.dataset.code, +li.dataset.c, +li.dataset.v); });

  // verse action bar — all actions apply to the whole selection (1+ verses)
  document.querySelectorAll(".sw").forEach((sw) => sw.addEventListener("click", () => {
    if (!state.sel) return; const c = sw.dataset.color;
    for (const key of selKeys()) { if (c) store.highlights[key] = c; else delete store.highlights[key]; }
    saveStore(); renderChapter();
  }));
  el("vbNote").addEventListener("click", () => {
    if (!state.sel) return; const key = vk(state.sel.name, state.sel.c1, state.sel.from);
    const cur = store.notes[key] || "";
    const n = prompt(`Note on ${state.sel.name} ${state.sel.c1}:${state.sel.from}`, cur);
    if (n === null) return; if (n.trim()) store.notes[key] = n.trim(); else delete store.notes[key];
    saveStore(); renderChapter();
  });
  el("vbSave").addEventListener("change", (e) => {
    if (!state.sel) return; let id = e.target.value; e.target.value = "";
    if (!id) return;
    if (id === "__new") { const name = prompt("New collection name:"); if (!name || !name.trim()) return; const coll = { id: "c" + Date.now().toString(36), name: name.trim(), verses: [] }; store.collections.push(coll); id = coll.id; }
    const coll = store.collections.find((c) => c.id === id); if (!coll) return;
    for (const key of selKeys()) if (!coll.verses.includes(key)) coll.verses.push(key);
    saveStore(); toast(`Saved to “${coll.name}”`); refreshSaveOptions();
  });
  el("vbRelated").addEventListener("click", showRelated);
  el("vbCopy").addEventListener("click", async () => { if (!state.sel) return; await navigator.clipboard.writeText(`${selPassageText()} — ${selRefText()} (${primary().name})`).then(() => toast("Copied")).catch(() => toast("Copy failed")); });
  el("vbLink").addEventListener("click", async () => { if (!state.sel) return; await navigator.clipboard.writeText(verseLink(selFrom())).then(() => toast("Link copied")).catch(() => toast("Copy failed")); });
  el("vbShare").addEventListener("click", () => { if (!state.sel) return; shareOrCopy({ title: selRefText(), text: `${selPassageText()} — ${selRefText()} (${primary().name})`, url: verseLink(selFrom()) }); });
  el("vbSpeak").addEventListener("click", () => { if (state.sel) speakText(selPassageText()); });
  el("vbClose").addEventListener("click", clearSelection);

  // Chapter-level actions
  el("listenChapter").addEventListener("click", async () => {
    if (speaking || audioPlaying) { stopListening(); return; }
    const f = chapterAudioFile(await loadAudioManifest());
    if (f) playChapterAudio("../library/" + f.path); else speakChapter();
  });
  el("copyChapterLink").addEventListener("click", async () => { await navigator.clipboard.writeText(chapterLink()).then(() => toast("Chapter link copied")).catch(() => toast("Copy failed")); });
  el("shareChapter").addEventListener("click", () => { const name = curBook().name, c = state.chapter + 1; shareOrCopy({ title: `${name} ${c}`, text: `${name} ${c} — ${primary().name}`, url: chapterLink() }); });

  window.addEventListener("hashchange", () => {
    if (hashLock) return;
    if (!location.hash.startsWith("#/panel/")) showOnly("reader");
    applyHash();
  });
}

document.addEventListener("DOMContentLoaded", init);
