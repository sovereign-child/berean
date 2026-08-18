/* Berean — offline service worker.

   The library is public-domain text that should keep working when the network
   does not. The app shell is precached on install; everything else is cached as
   it is read, so the chapters you actually study are the ones that stay with
   you. Nothing is ever evicted for being old — only when a new version of the
   app ships, which is when the caches are renamed.

   Text is immutable: a chapter of the Berean Standard Bible does not change. So
   library files are served from the cache first and refreshed in the background;
   the app's own files go to the network first, so an update is never missed. */
const VERSION = "berean-v1";
const SHELL = `${VERSION}-shell`;
const LIBRARY = `${VERSION}-library`;

const SHELL_FILES = [
  "./", "./index.html", "./app.js", "./styles.css",
  "./manifest.webmanifest", "./icon.svg",
  "../library/manifest.json", "../library/books.json",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(SHELL).then((c) => c.addAll(SHELL_FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => !k.startsWith(VERSION)).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

const isLibrary = (url) => url.pathname.includes("/library/");

self.addEventListener("fetch", (e) => {
  const { request } = e;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== location.origin) return;

  if (isLibrary(url)) {
    // Scripture does not change: serve what we have, and quietly refresh it.
    e.respondWith(caches.open(LIBRARY).then(async (cache) => {
      const hit = await cache.match(request);
      const fetching = fetch(request).then((res) => {
        if (res.ok) cache.put(request, res.clone());
        return res;
      }).catch(() => hit);
      return hit || fetching;
    }));
    return;
  }

  // The app itself: newest wins, with the cache as the fallback when offline.
  e.respondWith(fetch(request)
    .then((res) => {
      if (res.ok) caches.open(SHELL).then((c) => c.put(request, res.clone()));
      return res;
    })
    .catch(() => caches.match(request).then((hit) => hit || caches.match("./index.html"))));
});
