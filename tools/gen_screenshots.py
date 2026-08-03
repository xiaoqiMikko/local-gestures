# -*- coding: utf-8 -*-
"""Produce store screenshots at 1280x800, using the real installed Chrome.

Why not Playwright's bundled Chromium: on some machines it starts without the
user-agent stylesheet, so every block element computes to display:inline —
tables collapse into one line and <style> tags render as body text. Perfect
screenshots of a page that no real user will ever see. So we launch Chrome
ourselves and merely attach to it.

Two shots are captured mid-interaction: the gesture trail only exists while
the button is held, and the popup wheel only while it is open.

Output: store/screenshots/<locale>/*.png
"""
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
EXT = HERE.parent
WWW = HERE / "fixtures"
OUT = EXT / "store" / "screenshots"
W, H = 1280, 800

CHROME_CANDIDATES = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe",
]
CHROME = next((p for p in CHROME_CANDIDATES if p.exists()), None)
if CHROME is None:
    sys.exit("找不到系统安装的 Chrome")

LOCALES = [("zh-CN", "zh_CN"), ("en-US", "en")]


class Quiet(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass


srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(WWW)))
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{PORT}"


def cdp(port, path):
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}{path}", timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def shoot(page, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    page.evaluate("() => document.body.offsetHeight")
    page.wait_for_timeout(500)
    tmp = path.with_suffix(".raw.png")
    page.screenshot(path=str(tmp))
    im = Image.open(tmp)
    if im.width < W or im.height < H:
        im = im.resize((max(W, im.width), max(H, im.height)), Image.LANCZOS)
    im.crop((0, 0, W, H)).save(path)
    im.close()
    tmp.unlink(missing_ok=True)
    print("  ", path.relative_to(EXT))


def sanity(page):
    """Refuse to ship screenshots of a page the browser rendered wrong."""
    d = page.evaluate("() => getComputedStyle(document.body).display")
    if d != "block":
        raise SystemExit(f"渲染异常:body 的 display 是 {d},应为 block。"
                         "换一个浏览器再截。")


for i, (locale, tag) in enumerate(LOCALES):
    port = 9400 + i
    profile = Path(tempfile.gettempdir()) / f"lg-shot-{tag}-{int(time.time())}"
    for old in profile.parent.glob(f"lg-shot-{tag}-*"):
        if old != profile:
            shutil.rmtree(old, ignore_errors=True)
    profile.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {locale} ===")
    proc = subprocess.Popen([
        str(CHROME),
        f"--user-data-dir={profile}",
        f"--remote-debugging-port={port}",
        f"--disable-extensions-except={EXT}",
        f"--load-extension={EXT}",
        "--disable-features=DisableLoadExtensionCommandLineSwitch",
        f"--lang={locale}",
        "--no-first-run", "--no-default-browser-check",
        "--force-device-scale-factor=1",
        f"--window-size={W + 16},{H + 170}", "--window-position=20,20",
        "about:blank",
    ])

    for _ in range(80):
        if cdp(port, "/json/version"):
            break
        time.sleep(0.5)

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
            ctx = browser.contexts[0]

            # Load a page first: an MV3 worker starts lazily, so before
            # something touches the extension there is no target to find.
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(f"{BASE}/demo.html")
            page.wait_for_timeout(2000)
            sanity(page)

            # Match our own worker path: Chrome ships pre-installed component
            # extensions (Docs Offline and friends) whose targets appear here
            # too, and taking the first chrome-extension:// URL grabs one of
            # those instead.
            MARK = "/src/background/service-worker.js"
            ext_id = None
            for _ in range(40):
                for t in (cdp(port, "/json/list") or []):
                    u = str(t.get("url", ""))
                    if u.startswith("chrome-extension://") and u.endswith(MARK):
                        ext_id = u.split("/")[2]
                        break
                for w in ctx.service_workers:
                    if w.url.endswith(MARK):
                        ext_id = w.url.split("/")[2]
                if ext_id:
                    break
                page.reload()
                page.wait_for_timeout(700)
            if not ext_id:
                print("  扩展没加载。当前 targets:")
                for t in (cdp(port, "/json/list") or []):
                    print("     ", t.get("type"), "|", str(t.get("url"))[:80])
                print("  Playwright 看到的 workers:",
                      [w.url[:80] for w in ctx.service_workers])
                continue
            print("   扩展 id:", ext_id)

            # 1 ── gesture trail, captured while the button is still down
            page.mouse.move(640, 360)
            page.mouse.down(button="right")
            cx, cy = 640, 360
            for (tx, ty) in [(640, 540), (940, 540)]:
                n = 22
                for k in range(1, n + 1):
                    page.mouse.move(cx + (tx - cx) * k / n,
                                    cy + (ty - cy) * k / n)
                    page.wait_for_timeout(6)
                cx, cy = tx, ty
            page.wait_for_timeout(250)
            shoot(page, OUT / tag / "1-gesture-trail.png")
            page.mouse.move(300, 300)     # bail out into an unbound shape
            page.mouse.up(button="right")
            page.wait_for_timeout(600)
            page.keyboard.press("Escape")

            # 2 ── popup wheel
            sws = [w for w in ctx.service_workers if w.url.endswith(MARK)]
            if sws:
                sws[0].evaluate("() => chrome.storage.local.set("
                                "{ popupEnabled: true, popupDelay: 250 })")
            page.wait_for_timeout(600)
            page.goto(f"{BASE}/demo.html")
            page.wait_for_timeout(1000)
            page.mouse.move(640, 420)
            page.mouse.down(button="right")
            page.wait_for_timeout(700)
            page.mouse.move(640, 320)
            page.wait_for_timeout(250)
            shoot(page, OUT / tag / "2-popup-wheel.png")
            page.mouse.move(640, 420)
            page.mouse.up(button="right")
            page.wait_for_timeout(400)
            if sws:
                sws[0].evaluate(
                    "() => chrome.storage.local.set({ popupEnabled: false })")

            # 3-5 ── settings pages
            opt = ctx.new_page()
            opt.goto(f"chrome-extension://{ext_id}/src/options/options.html")
            opt.wait_for_timeout(1500)
            sanity(opt)
            shoot(opt, OUT / tag / "3-settings-gestures.png")

            opt.locator("#tabs .tab").nth(3).click()
            opt.wait_for_timeout(600)
            shoot(opt, OUT / tag / "4-settings-drag.png")

            opt.locator("#tabs .tab").nth(6).click()
            opt.wait_for_timeout(600)
            shoot(opt, OUT / tag / "5-settings-privacy.png")
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except Exception:
            pass

srv.shutdown()
print("\n完成。")
