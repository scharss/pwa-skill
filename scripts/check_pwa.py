#!/usr/bin/env python3
"""Validate a PWA on disk or at a URL.

Usage:
    python check_pwa.py --dir .
    python check_pwa.py --url https://yourdomain.com
    python check_pwa.py --dir . --url https://yourdomain.com

Output: [OK] / [WARN] / [ERROR] lines. Exits 1 when errors are found.
Pillow is only required to verify icon dimensions.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

OK, WARN, ERROR = "OK", "WARN", "ERROR"
results: list[tuple[str, str]] = []


def add(level: str, message: str) -> None:
    results.append((level, message))


def is_local(url: str) -> bool:
    host = urllib.parse.urlparse(url).hostname or ""
    return host in ("localhost", "127.0.0.1", "::1")


def find_manifest_link(html: str) -> str:
    match = re.search(
        r'<link[^>]+rel=["\']manifest["\'][^>]*href=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\']manifest["\']',
            html,
            re.IGNORECASE,
        )
    return match.group(1) if match else ""


def find_sw_register(html: str) -> str:
    match = re.search(r"serviceWorker\.register\(\s*['\"]([^'\"]+)['\"]", html)
    return match.group(1) if match else ""


def check_manifest_data(manifest: dict, label: str = "") -> None:
    prefix = f"{label} " if label else ""
    for field in ("name", "short_name", "start_url", "display"):
        if not manifest.get(field):
            add(ERROR, f"{prefix}manifest: missing '{field}'")

    icons = manifest.get("icons") or []
    sizes = {icon.get("sizes", "") for icon in icons}
    purposes = {icon.get("purpose", "any") for icon in icons}
    if "192x192" not in sizes:
        add(ERROR, f"{prefix}manifest: missing 192x192 icon")
    if "512x512" not in sizes:
        add(ERROR, f"{prefix}manifest: missing 512x512 icon")
    if "maskable" not in purposes:
        add(WARN, f"{prefix}manifest: no icon with purpose 'maskable'")

    if manifest.get("display") not in ("standalone", "fullscreen", "minimal-ui"):
        add(WARN, f"{prefix}manifest: display='{manifest.get('display')}' is not install-friendly")

    if not manifest.get("theme_color"):
        add(WARN, f"{prefix}manifest: missing theme_color")
    if not manifest.get("background_color"):
        add(WARN, f"{prefix}manifest: missing background_color")


def check_dir(root: pathlib.Path) -> None:
    if not root.is_dir():
        add(ERROR, f"Folder not found: {root}")
        return

    index = root / "index.html"
    html = index.read_text(encoding="utf-8", errors="replace") if index.exists() else ""

    manifest_path = None
    for name in ("manifest.json", "manifest.webmanifest"):
        candidate = root / name
        if candidate.exists():
            manifest_path = candidate
            break

    if manifest_path is None:
        link = find_manifest_link(html)
        if link:
            candidate = root / link.lstrip("/")
            if candidate.exists():
                manifest_path = candidate

    if manifest_path is None:
        add(ERROR, "manifest.json not found")
        return

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        add(OK, f"valid manifest: {manifest_path.name}")
        check_manifest_data(manifest)
    except json.JSONDecodeError as exc:
        add(ERROR, f"invalid manifest: {exc}")
        return

    for icon in manifest.get("icons", []):
        src = str(icon.get("src", "")).lstrip("/")
        path = root / src
        if not path.exists():
            add(ERROR, f"icon not found: {src}")
            continue
        if Image is not None:
            try:
                with Image.open(path) as image:
                    expected = icon.get("sizes", "")
                    actual = f"{image.width}x{image.height}"
                    if expected and expected != actual:
                        add(ERROR, f"{src}: declares {expected} but measures {actual}")
                    else:
                        add(OK, f"icon {src} ({actual})")
            except Exception as exc:
                add(ERROR, f"{src}: cannot open ({exc})")

    sw_path = root / "sw.js"
    if sw_path.exists():
        add(OK, "sw.js present")
    else:
        add(ERROR, "sw.js is missing")

    if find_sw_register(html):
        add(OK, "service worker registration found in HTML")
    else:
        add(WARN, "serviceWorker.register not found in HTML")

    offline = root / "offline.html"
    if offline.exists():
        add(OK, "offline.html present")
    else:
        add(WARN, "offline.html is missing (offline fallback)")

    if not re.search(r'<meta[^>]+name=["\']theme-color["\']', html, re.IGNORECASE):
        add(WARN, "missing theme-color meta tag")
    if not re.search(r'apple-touch-icon', html, re.IGNORECASE):
        add(WARN, "missing apple-touch-icon")
    if not re.search(r'apple-mobile-web-app-capable', html, re.IGNORECASE):
        add(WARN, "missing apple-mobile-web-app-capable")


def fetch(url: str, method: str = "GET") -> tuple[int, bytes, dict]:
    request = urllib.request.Request(url, method=method, headers={"User-Agent": "pwa-check"})
    with urllib.request.urlopen(request, timeout=20) as response:
        body = b"" if method == "HEAD" else response.read()
        return response.status, body, {key.lower(): value for key, value in response.headers.items()}


def check_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" and not is_local(url):
        add(ERROR, "the PWA must be served over HTTPS (except localhost)")

    try:
        status, body, headers = fetch(url)
    except Exception as exc:
        add(ERROR, f"cannot open {url}: {exc}")
        return

    if status != 200:
        add(ERROR, f"{url} returned HTTP {status}")
    html = body.decode("utf-8", errors="replace")

    manifest_href = find_manifest_link(html)
    if not manifest_href:
        add(ERROR, "the HTML does not declare <link rel='manifest'>")
        return
    manifest_url = urllib.parse.urljoin(url, manifest_href)

    try:
        status, body, headers = fetch(manifest_url)
        manifest = json.loads(body.decode("utf-8", errors="replace"))
        if status != 200:
            add(ERROR, f"manifest returned HTTP {status}")
        else:
            add(OK, f"manifest reachable: {manifest_url}")
        check_manifest_data(manifest)
    except Exception as exc:
        add(ERROR, f"manifest is invalid or unreachable: {exc}")
        return

    ctype = headers.get("content-type", "")
    if "json" not in ctype and "manifest" not in ctype:
        add(WARN, f"manifest has Content-Type '{ctype}'")

    start_url = urllib.parse.urljoin(manifest_url, manifest.get("start_url", "/"))
    scope = urllib.parse.urljoin(manifest_url, manifest.get("scope", "/"))
    if not start_url.startswith(scope):
        add(ERROR, "start_url is outside the scope")
    else:
        add(OK, "start_url is inside the scope")

    try:
        status, _, _ = fetch(start_url, "HEAD")
        if status == 200:
            add(OK, f"start_url returns 200: {start_url}")
        else:
            add(ERROR, f"start_url returned HTTP {status}")
    except Exception as exc:
        add(ERROR, f"start_url is not responding: {exc}")

    for icon in manifest.get("icons", []):
        icon_url = urllib.parse.urljoin(manifest_url, str(icon.get("src", "")))
        try:
            status, _, headers = fetch(icon_url, "HEAD")
            if status != 200:
                add(ERROR, f"icon HTTP {status}: {icon_url}")
            elif "image" not in headers.get("content-type", ""):
                add(WARN, f"icon has an unexpected Content-Type: {icon_url}")
            else:
                add(OK, f"icon reachable: {icon_url}")
        except Exception as exc:
            add(ERROR, f"icon unreachable: {icon_url} ({exc})")

    sw_href = find_sw_register(html) or "/sw.js"
    sw_url = urllib.parse.urljoin(url, sw_href)
    try:
        status, _, headers = fetch(sw_url, "HEAD")
        if status == 200:
            add(OK, f"service worker reachable: {sw_url}")
            cache = headers.get("cache-control", "")
            if "no-cache" not in cache and "no-store" not in cache:
                add(WARN, "sw.js is missing Cache-Control no-cache")
        else:
            add(ERROR, f"service worker HTTP {status}: {sw_url}")
    except Exception as exc:
        add(ERROR, f"service worker unreachable: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a PWA")
    parser.add_argument("--dir", help="Site folder")
    parser.add_argument("--url", help="Public URL")
    args = parser.parse_args()

    if not args.dir and not args.url:
        parser.error("Provide --dir and/or --url")

    if args.dir:
        print(f"\n== Local analysis: {args.dir} ==")
        check_dir(pathlib.Path(args.dir).resolve())
    if args.url:
        print(f"\n== Remote analysis: {args.url} ==")
        check_url(args.url)

    errors = 0
    for level, message in results:
        print(f"[{level}] {message}")
        if level == ERROR:
            errors += 1

    print(f"\nSummary: {len(results)} checks, {errors} errors")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
