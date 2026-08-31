/* Offline cache for /term/ only. Scope is this directory; the site worker at
   the root spares caches named term-*, and this worker touches nothing else.
   To ship a change, bump CACHE. The next legitimate bump is December 2026. */
const CACHE = "term-v1";
const FILES = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon-180.png",
  "./icon-192.png",
  "./icon-512.png"
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(FILES))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k.indexOf("term-") === 0 && k !== CACHE)
          .map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then(hit =>
      hit || fetch(req).catch(() => caches.match("./index.html"))
    )
  );
});
