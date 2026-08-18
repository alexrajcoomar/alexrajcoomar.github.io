// Placeholder service worker. Registers cleanly, caches nothing.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
