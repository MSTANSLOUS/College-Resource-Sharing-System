// ─── Service Worker ───
const CACHE_NAME = 'srs-v3';
const OFFLINE_URL = '/offline';

// Files to cache on install
const urlsToCache = [
  '/static/manifest.json',
  '/static/android-chrome-192x192.png',
  '/static/android-chrome-512x512.png',
  '/static/favicon-32x32.png',
  '/static/favicon-16x16.png',
  '/static/apple-touch-icon.png',
  '/static/favicon.ico',
];

// ─── Install Event ───
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('🔧 Caching app shell...');
        // Cache each file individually to avoid failing on one bad file
        return Promise.all(
          urlsToCache.map(function(url) {
            return fetch(url)
              .then(function(response) {
                if (response.status === 200) {
                  return cache.put(url, response);
                }
                console.warn('⚠️ Failed to cache:', url);
                return Promise.resolve();
              })
              .catch(function(err) {
                console.warn('⚠️ Network error for:', url, err);
                return Promise.resolve();
              });
          })
        );
      })
      .then(function() {
        return self.skipWaiting();
      })
  );
});

// ─── Activate Event ───
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('🧹 Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(function() {
      return self.clients.claim();
    })
  );
});

// ─── Fetch Event ───
self.addEventListener('fetch', function(event) {
  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  // For HTML pages: network first, fallback to cache, then offline page
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then(function(response) {
          // Cache the fresh response
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(event.request, responseClone);
          });
          return response;
        })
        .catch(function() {
          // Network failed – try cache
          return caches.match(event.request).then(function(cachedResponse) {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Fallback to offline page
            return caches.match(OFFLINE_URL);
          });
        })
    );
    return;
  }

  // For static assets: cache first, then network
  event.respondWith(
    caches.match(event.request)
      .then(function(cachedResponse) {
        if (cachedResponse) {
          // Return cached version, update in background
          fetch(event.request)
            .then(function(response) {
              if (response && response.status === 200) {
                caches.open(CACHE_NAME).then(function(cache) {
                  cache.put(event.request, response);
                });
              }
            })
            .catch(function() { /* ignore */ });
          return cachedResponse;
        }
        // Not in cache – fetch from network
        return fetch(event.request)
          .then(function(response) {
            if (response && response.status === 200) {
              const responseClone = response.clone();
              caches.open(CACHE_NAME).then(function(cache) {
                cache.put(event.request, responseClone);
              });
            }
            return response;
          })
          .catch(function() {
            // If all fails, return offline page
            return caches.match(OFFLINE_URL);
          });
      })
  );
});

// ─── Push Notification (placeholder) ───
self.addEventListener('push', function(event) {
  // ... (optional)
});

self.addEventListener('notificationclick', function(event) {
  // ... (optional)
});