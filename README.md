# PWA Skill

Turn any website into a native App or an installable PWA for Android, iPhone/iPad, Windows, macOS, and Linux. This covers the manifest, icons, service worker, iOS splash screens, the installation experience, testing, and deployment.

It does not rewrite the site: it adds the files and tags the browser needs to
offer installation, run in standalone mode and work offline.

## Contents

```text
.
├─ README.md
├─ SKILL.md
├─ scripts/
│  ├─ generate_icons.py
│  └─ check_pwa.py
├─ templates/
│  ├─ manifest.json
│  ├─ sw.js
│  ├─ head.html
│  └─ register.js
└─ references/
   └─ checklist.md
```

## For AI agents

The entry point is `SKILL.md`. It contains the full flow:
requirements, manifest, icons, service worker, iOS metadata, installation,
testing and deployment.

Load the skill and ask, for example:

> Turn this website into an installable PWA.

## For people

### 1. Copy the templates

```text
templates/manifest.json  ->  /manifest.json
templates/sw.js          ->  /sw.js
templates/head.html      ->  block inside the <head>
templates/register.js    ->  /assets/register.js
```

Adjust paths, name, colors and the `PRECACHE` list.

### 2. Generate icons and splash screens

Pillow is required:

```bash
pip install pillow
```

From a logo:

```bash
python scripts/generate_icons.py \
  --source logo.png \
  --out assets/icons \
  --splash assets/splash \
  --splash-label "My App"
```

Without a logo, using an initial:

```bash
python scripts/generate_icons.py \
  --text "B" --bg "#FFC107" --fg "#101418" \
  --out assets/icons
```

It generates:

- `icon-192.png`
- `icon-512.png`
- `maskable-512.png`
- `apple-touch-icon.png`
- `favicon-32.png`
- iOS splash screens (optional)

### 3. Validate

On disk:

```bash
python scripts/check_pwa.py --dir .
```

At a URL:

```bash
python scripts/check_pwa.py --url https://yourdomain.com
```

The script checks the manifest, icons, service worker, `start_url`, scope,
MIME types and metadata. It exits with code 1 when it finds errors.

### 4. Test

1. DevTools → Application → Manifest.
2. DevTools → Application → Service Workers.
3. DevTools → Network → Offline and reload.
4. Lighthouse → PWA.
5. Install on a real Android phone and a real iPhone.

## What it covers

- A complete, valid manifest.
- Standard and **maskable** icons.
- Service worker with network-first for HTML, stale-while-revalidate for static
  assets and an offline fallback.
- Registration, updates and new-version prompts.
- iOS metadata and per-size splash screens.
- Install prompt on Android/Chrome/Edge.
- Instructions for Safari on iOS.
- Common errors and how to diagnose them.
- Deployment checklist.

## Requirements

- Python 3.10 or newer for the scripts.
- Pillow to generate and validate icons.
- HTTPS in production (except `localhost`).

## Notes

- The templates are starting points: adapt them to the project stack.
- The service worker must be served from the root of its scope.
- Bump the cache version on every deployment.
- No `AGENTS.md` is included: a skill is documented by its `SKILL.md`.

## Support

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mercaplace)

## Developer

**Sharss Azael** — [github.com/scharss](https://github.com/scharss/)
