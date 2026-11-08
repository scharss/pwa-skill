# PWA checklist

## Before you start

- [ ] The site is served over **HTTPS** (or `localhost` for testing).
- [ ] There is a clear entry URL (`/`, `/app/`, etc.).
- [ ] The first screen works without requiring a session.
- [ ] A logo PNG of at least 512×512 is available.

## Manifest

- [ ] `manifest.json` is reachable with a JSON `Content-Type`.
- [ ] `name` and `short_name` are set.
- [ ] `start_url` returns 200 and lives inside `scope`.
- [ ] `display`: `standalone`.
- [ ] `theme_color` and `background_color`.
- [ ] Correct `lang`.
- [ ] `<link rel="manifest" href="/manifest.json">` in the `<head>`.

## Icons

- [ ] `icon-192.png` (192×192).
- [ ] `icon-512.png` (512×512).
- [ ] `maskable-512.png` with the logo inside the central 80%.
- [ ] `apple-touch-icon.png` (180×180).
- [ ] `favicon-32.png`.
- [ ] Files exist and dimensions match the manifest.

## Service worker

- [ ] `sw.js` at the root of the scope.
- [ ] Registered with `navigator.serviceWorker.register('/sw.js')`.
- [ ] State `activated and is running` in DevTools.
- [ ] `VERSION` changes on every deployment.
- [ ] It does not cache `/api/` or POST requests.
- [ ] `Cache-Control: no-cache` on `sw.js`.
- [ ] It does not precache private routes.

## Head and metadata

- [ ] `<meta name="theme-color">`.
- [ ] `apple-touch-icon`.
- [ ] `apple-mobile-web-app-capable`.
- [ ] `apple-mobile-web-app-title`.
- [ ] `viewport` with `viewport-fit=cover`.

## iOS

- [ ] Splash screens via `apple-touch-startup-image` for the main sizes.
- [ ] Install instructions (Share → Add to Home Screen).
- [ ] Tested on real Safari, not only in the simulator.

## Installation

- [ ] `beforeinstallprompt` handled on Android/Chrome/Edge.
- [ ] Install button hidden when already installed (`display-mode: standalone`).
- [ ] `appinstalled` event handled.
- [ ] iOS shows the correct instructions.

## Offline

- [ ] `offline.html` exists and is styled.
- [ ] It is included in `PRECACHE`.
- [ ] With DevTools "Offline", navigation shows the fallback.
- [ ] Data requests fail with a clear message, not a blank screen.

## Testing

- [ ] `python scripts/check_pwa.py --dir .` reports no errors.
- [ ] Lighthouse → PWA with no critical failures.
- [ ] DevTools → Application → Manifest with no errors.
- [ ] Real installation on Android.
- [ ] Real installation on iPhone/iPad.
- [ ] Installation on desktop Chrome/Edge (Windows, macOS, Linux).
- [ ] Update flow: bump `VERSION`, deploy and confirm the prompt.

## Deployment

- [ ] `manifest.json` served with the correct MIME type.
- [ ] `sw.js` not cached long-term.
- [ ] Icons cached long-term.
- [ ] `offline.html` reachable.
- [ ] HTTPS certificate renewed (Let's Encrypt).

## After installing

- [ ] The app opens without the browser bar.
- [ ] The icon looks right on the home screen.
- [ ] The splash screen does not show a white flash.
- [ ] The back button behaves reasonably.
- [ ] External links open in the browser, not inside the app.
