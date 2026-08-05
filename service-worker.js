const CACHE_PREFIX = "ddb-pwa-v3-";
const STATIC_CACHE = `${CACHE_PREFIX}static`;
const PAGE_CACHE = `${CACHE_PREFIX}pages`;
const DATA_CACHE = `${CACHE_PREFIX}data`;
const OFFLINE_URL = "/offline.html";
const MAX_PAGE_ENTRIES = 80;
const MAX_DATA_ENTRIES = 8;

const STATIC_ASSETS = [
  OFFLINE_URL,
  "/manifest.webmanifest",
  "/pwa.css",
  "/pwa.js",
  "/brand.css",
  "/evening-library.css",
  "/evening-library.js",
  "/favicon.svg",
  "/apple-touch-icon.png",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/header-art.png",
  "/mary-floral-blush.png",
  "/mary-floral-ivory.png",
  "/mary-floral-sprig.png"
];

const STATIC_PATHS = new Set(STATIC_ASSETS);
const CANONICAL_DATA_PATHS = new Set([
  "/archive.json",
  "/feed.xml",
  "/evening-catalog.json"
]);

self.addEventListener("install", (event) => {
  event.waitUntil(installStaticAssets());
});

async function installStaticAssets() {
  const entries = await Promise.all(STATIC_ASSETS.map(async (path) => {
    const request = new Request(path, { cache: "reload" });
    const response = await fetch(request);
    const url = new URL(request.url);
    if (url.origin !== self.location.origin || !canCache(response)) {
      throw new Error(`Refusing to cache ineligible shell response: ${path}`);
    }
    return [cleanCacheKey(request), response];
  }));

  const cache = await caches.open(STATIC_CACHE);
  await Promise.all(entries.map(
    ([cacheKey, response]) => cache.put(cacheKey, response)
  ));
}

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((names) => Promise.all(
      names
        .filter((name) => name.startsWith("ddb-pwa-") && !name.startsWith(CACHE_PREFIX))
        .map((name) => caches.delete(name))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "ACTIVATE_UPDATE") {
    self.skipWaiting();
  }
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    event.respondWith(networkFirst(event, PAGE_CACHE, OFFLINE_URL, MAX_PAGE_ENTRIES));
    return;
  }

  if (CANONICAL_DATA_PATHS.has(url.pathname)) {
    event.respondWith(networkFirst(event, DATA_CACHE, null, MAX_DATA_ENTRIES));
    return;
  }

  if (STATIC_PATHS.has(url.pathname)) {
    event.respondWith(url.search ? fetch(request) : cacheFirst(request, STATIC_CACHE));
  }
});

function canCache(response) {
  if (!response || !response.ok || response.type !== "basic" || response.redirected) {
    return false;
  }
  const cacheControl = response.headers.get("Cache-Control") || "";
  return !/(^|,)\s*no-store\b/i.test(cacheControl);
}

function cleanCacheKey(request) {
  const url = new URL(request.url);
  return url.pathname;
}

async function trimCache(cacheName, maximumEntries) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  const excess = keys.length - maximumEntries;
  if (excess <= 0) return;
  await Promise.all(keys.slice(0, excess).map((key) => cache.delete(key)));
}

async function storeSuccessfulResponse(cacheName, request, response, maximumEntries) {
  const url = new URL(request.url);
  if (url.search || !canCache(response)) return;
  const copy = response.clone();
  const cache = await caches.open(cacheName);
  await cache.put(cleanCacheKey(request), copy);
  await trimCache(cacheName, maximumEntries);
}

async function networkFirst(event, cacheName, fallbackUrl, maximumEntries) {
  const request = event.request;
  try {
    const response = await fetch(request, { cache: "no-store" });
    event.waitUntil(
      storeSuccessfulResponse(cacheName, request, response, maximumEntries).catch(() => {})
    );
    return response;
  } catch (error) {
    const cache = await caches.open(cacheName);
    const saved = await cache.match(cleanCacheKey(request));
    if (saved) return saved;
    if (fallbackUrl) {
      const fallback = await caches.match(fallbackUrl);
      if (fallback) return fallback;
    }
    throw error;
  }
}

async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const saved = await cache.match(cleanCacheKey(request));
  if (saved) return saved;
  const response = await fetch(request);
  const url = new URL(request.url);
  if (!url.search && canCache(response)) {
    await cache.put(cleanCacheKey(request), response.clone());
  }
  return response;
}
