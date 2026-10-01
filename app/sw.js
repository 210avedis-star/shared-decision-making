/* Offline cache for the SDM form.
   This worker only ever downloads the blank form files (GET requests to this site).
   It never sees, stores or sends anything typed into the form: the page's
   Content-Security-Policy blocks all outbound connections from the form itself. */
const CACHE = 'sdm-form-v19';
const FILES = ['./', './index.html', './manifest.webmanifest', './apple-touch-icon.png', './icon-192.png', './icon-512.png', './vendor/html2canvas.min.js', './vendor/jspdf.umd.min.js'];

self.addEventListener('install', e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting()));
});

self.addEventListener('activate', e=>{
  e.waitUntil(
    caches.keys()
      .then(keys=>Promise.all(keys.filter(k=>k !== CACHE).map(k=>caches.delete(k))))
      .then(()=>self.clients.claim())
  );
});

/* Network first (so every iPad picks up form updates whenever it is online),
   falling back to the cached copy when offline. Only same-site GETs are handled. */
self.addEventListener('fetch', e=>{
  const req = e.request;
  if(req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  e.respondWith(
    fetch(req, {cache:'no-store'})
      .then(res=>{
        if(res.ok){ const copy = res.clone(); caches.open(CACHE).then(c=>c.put(req, copy)); }
        return res;
      })
      .catch(()=>caches.match(req, {ignoreSearch:true}).then(r=>r || caches.match('./index.html')))
  );
});
