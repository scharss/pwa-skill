---
name: pwa-skill
description: >-
  Turn any website into a native App or an installable PWA for Android, iPhone/iPad, Windows, macOS, and Linux. This covers the manifest, icons, service worker, iOS splash screens, the installation experience, testing, and deployment.
version: 1.0.0
platforms: [linux, macos, windows]
---

# Installable PWA

## When to use this skill

When the user wants their website to:

- be **installable** on a phone or desktop;
- open without the browser bar (`display: standalone`);
- work **offline** or on an unreliable network;
- have its own icon, splash screen and name on the home screen;
- pass a PWA audit (Lighthouse / DevTools).

You do not need to rewrite the site: you add a few files and tags.

## Non-negotiable requirements

| Requirement | Detail |
|---|---|
| HTTPS | Required except on `localhost` |
| `manifest.json` | Valid, reachable, with 192 and 512 icons |
| Service worker | Registered with a scope that covers `start_url` |
| `start_url` | Must return 200 and live inside `scope` |
| Icons | Real PNGs matching the dimensions declared in the manifest |

If any of these is missing, the browser will not offer installation.

## Quick diagnosis

1. Open DevTools → **Application → Manifest**. No red errors.
2. **Application → Service Workers**: state `activated and is running`.
3. **Lighthouse → PWA**: no critical failures.
4. Test on a phone: Chrome (Android) or Safari (iOS).

Included script:

```bash
python scripts/check_pwa.py --dir /path/to/site
python scripts/check_pwa.py --url https://yourdomain.com
```

## Step 1 - Manifest

Create `manifest.json` at the site root (or wherever the `<link>` points).
A ready-to-use base is in `templates/manifest.json`.

| Field | Recommended value |
|---|---|
| `name` | Full name (max. 45 characters) |
| `short_name` | Short name for the icon (max. 12) |
| `start_url` | `/` or the entry route; **inside `scope`** |
| `scope` | Folder controlled by the PWA (e.g. `/app/`) |
| `display` | `standalone` (or `minimal-ui`) |
| `orientation` | `any` unless the app is single-orientation |
| `theme_color` | System bar color |
| `background_color` | Splash background color |
| `lang` | `en` |
| `icons` | 192, 512 `any` and 512 `maskable` |

Link it in the `<head>`:

```html
<link rel="manifest" href="/manifest.json">
```

Serve it with `Content-Type: application/manifest+json` (or `application/json`).

### Icons

```bash
# From a logo
python scripts/generate_icons.py --source logo.png --out assets/icons

# Without a logo: generate an icon with an initial
python scripts/generate_icons.py --text "B" --bg "#FFC107" --fg "#101418" --out assets/icons

# Also generate iOS splash screens
python scripts/generate_icons.py --source logo.png --out assets/icons --splash assets/splash
```

It generates `icon-192.png`, `icon-512.png`, `maskable-512.png`,
`apple-touch-icon.png` and `favicon-32.png`.

**Maskable** icon rule: important content must fit inside the central 80%.
The script scales the logo to 60% over the background so Android does not crop
it.

## Step 2 - Service worker

Base in `templates/sw.js`. Copy it to the root as `sw.js` and adjust:

```js
const VERSION = 'v1';           // bump on every deployment
const PRECACHE = ['/', '/offline.html', '/assets/styles.css', '/assets/app.js'];
```

Included strategies:

| Resource | Strategy |
|---|---|
| Navigation (HTML) | network-first with `/offline.html` fallback |
| Static assets (CSS, JS, images) | stale-while-revalidate |
| `/api/` and non-GET requests | never cached |

Rules:

- Bump `VERSION` on every deployment; otherwise clients keep the old cache.
- Never precache routes that require a session.
- The service worker must be served from the root of its scope (`/sw.js` for
  `scope: /`).
- Serve `sw.js` with `Cache-Control: no-cache` so browsers detect changes.

### Registration and updates

`templates/register.js` includes:

- Registration on `load`.
- New-version detection and a reload prompt.
- `skipWaiting` controlled by a message.

```html
<script src="/assets/register.js" defer></script>
```

## Step 3 - Head and metadata

`templates/head.html` has the full block. Minimum:

```html
<meta name="theme-color" content="#FFC107">
<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="My App">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
```

### iOS: splash screens

iOS does not use the manifest `background_color` for the splash screen. You must
declare images per size:

```html
<link rel="apple-touch-startup-image" media="(device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3)" href="/assets/splash/1170x2532.png">
```

`generate_icons.py --splash` creates the most common iPhone and iPad sizes.

## Step 4 - Install experience

### Android / Chrome / Edge / desktop

```js
let deferredPrompt = null;
window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  deferredPrompt = event;
  showInstallButton();
});

async function install() {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  deferredPrompt = null;
}
```

### iOS / iPadOS

Safari does not fire `beforeinstallprompt`. Show instructions instead:

> Share → **Add to Home Screen**.

Detect iOS:

```js
const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
const standalone = window.matchMedia('(display-mode: standalone)').matches
  || navigator.standalone === true;
```

## Step 5 - Offline

- Create `offline.html` with its own styling and a retry button.
- Include it in `PRECACHE`.
- In `fetch`, if navigation fails and there is no cache, return `offline.html`.
- Never return a blank page or a raw browser error.

## Step 6 - Testing

1. `python scripts/check_pwa.py --dir .` → no errors.
2. DevTools → Application → Manifest: correct fields and icons.
3. DevTools → Application → Service Workers: active.
4. DevTools → Network → **Offline** and reload: the fallback must appear.
5. Lighthouse → PWA.
6. Install on Android (Chrome) and iPhone (Safari).
7. Verify that a deployment shows the new version.

## Step 7 - Deployment

| File | Content-Type | Cache |
|---|---|---|
| `manifest.json` | `application/manifest+json` | short |
| `sw.js` | `application/javascript` | `no-cache` |
| icons | `image/png` | long (hashed filenames ideal) |
| `offline.html` | `text/html` | short |

Apache (Hestia):

```apache
AddType application/manifest+json .webmanifest
<Files "sw.js">
  Header set Cache-Control "no-cache, no-store, must-revalidate"
</Files>
```

Nginx:

```nginx
location = /sw.js {
  add_header Cache-Control "no-cache, no-store, must-revalidate";
  types { application/javascript js; }
}
```

## Common errors

| Symptom | Cause |
|---|---|
| No "Install" prompt | Missing manifest, 192/512 icon, or inactive service worker |
| "Start URL is not within scope" | `start_url` outside `scope` |
| Installs but opens blank | `start_url` returns 404 or redirects outside the scope |
| Icon cropped on Android | Missing `purpose: maskable` or logo outside the safe area |
| No updates | `VERSION` not bumped or `sw.js` cached |
| No iOS splash | Missing `apple-touch-startup-image` links |
| Works in Chrome, not on iPhone | Safari does not support `beforeinstallprompt`; use instructions |
| Service worker not controlling the page | `sw.js` outside the scope or registered under another path |
| Manifest MIME error | Server returns `text/plain` |

## Final checklist

See `references/checklist.md`.

## Real-world reference

`apichatbusiness` (the Business Copilot chat) is a complete implementation:
`manifest.json`, `sw.js`, `inc/pwa_head.php`, `inc/pwa_splash.php`,
`assets/icons/` and `assets/splash/`. It is a good example of structure and
cache versioning.
