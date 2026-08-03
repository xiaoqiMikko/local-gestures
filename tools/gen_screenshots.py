# -*- coding: utf-8 -*-
"""Produce store screenshots at 1280x800.

Browser choice is forced, not preferred: Chrome 137 dropped --load-extension
and Chrome 150 ignores it even with --enable-unsafe-extension-debugging
(verified — developerPrivate.getExtensionsInfo comes back empty). So the only
browser that can still load an unpacked extension is Playwright's own build.

That build has a failure mode worth knowing: if its install is missing
resources.pak it starts without the user-agent stylesheet and every block
element computes to display:inline. The screenshots come out looking like the
extension destroyed the page. sanity() refuses to shoot in that state — see
MANUAL-CHECKS.md for the fix.

Two shots are captured mid-interaction: the gesture trail only exists while
the button is held, and the popup wheel only while it is open.

Output: store/screenshots/<locale>/*.png
"""
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import gettempdir

from PIL import Image
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
EXT = HERE.parent
WWW = HERE / "fixtures"
OUT = EXT / "store" / "screenshots"
W, H = 1280, 800
MARK = "/src/background/service-worker.js"

LOCALES = [("zh-CN", "zh_CN"), ("en-US", "en")]


class Quiet(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass


srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(WWW)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_address[1]}"


def sanity(page):
    """Refuse to ship screenshots of a page the browser rendered wrong."""
    d = page.evaluate("() => getComputedStyle(document.body).display")
    if d != "block":
        raise SystemExit(
            f"渲染异常:body 的 display 是 {d},应为 block。\n"
            "浏览器缺 resources.pak,不是页面的问题。\n"
            "修:python -m playwright install --force chromium(要跑完)")


def shoot(page, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    page.evaluate("() => document.body.offsetHeight")
    page.wait_for_timeout(400)
    tmp = path.with_suffix(".raw.png")
    page.screenshot(path=str(tmp))
    im = Image.open(tmp)
    if im.width < W or im.height < H:
        im = im.resize((max(W, im.width), max(H, im.height)), Image.LANCZOS)
    im.crop((0, 0, W, H)).save(path)
    im.close()
    tmp.unlink(missing_ok=True)
    print("  ", path.relative_to(EXT))


def worker(ctx, page):
    """Wait for our own service worker.

    Chrome ships pre-installed component extensions whose workers show up here
    too; matching on the path stops us from grabbing one of those and then
    reporting success for code that never ran.
    """
    for _ in range(30):
        for w in ctx.service_workers:
            if w.url.endswith(MARK):
                return w
        page.reload()
        page.wait_for_timeout(600)
    return None


for locale, tag in LOCALES:
    print(f"\n=== {locale} ===")
    profile = Path(gettempdir()) / f"lg-shot-{tag}-{int(time.time())}"

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(profile),
            headless=False,
            viewport={"width": W, "height": H},
            ignore_default_args=["--disable-extensions"],
            args=[
                f"--disable-extensions-except={EXT}",
                f"--load-extension={EXT}",
                f"--lang={locale}",
                "--force-device-scale-factor=1",
                "--no-first-run", "--no-default-browser-check",
            ],
        )
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(f"{BASE}/demo.html")
            page.wait_for_timeout(1200)
            sanity(page)

            sw = worker(ctx, page)
            if sw is None:
                print("  扩展没加载,跳过")
                continue
            ext_id = sw.url.split("/")[2]
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
            page.wait_for_timeout(500)

            # 2 ── popup wheel
            sw.evaluate("() => chrome.storage.local.set("
                        "{ popupEnabled: true, popupDelay: 250 })")
            page.wait_for_timeout(500)
            page.goto(f"{BASE}/demo.html")
            page.wait_for_timeout(900)
            page.mouse.move(640, 420)
            page.mouse.down(button="right")
            page.wait_for_timeout(700)
            page.mouse.move(640, 320)
            page.wait_for_timeout(250)
            shoot(page, OUT / tag / "2-popup-wheel.png")
            page.mouse.move(640, 420)
            page.mouse.up(button="right")
            page.wait_for_timeout(400)
            sw.evaluate("() => chrome.storage.local.set("
                        "{ popupEnabled: false })")

            # 3-5 ── settings pages
            opt = ctx.new_page()
            opt.goto(f"chrome-extension://{ext_id}/src/options/options.html")
            opt.wait_for_timeout(1200)
            sanity(opt)
            shoot(opt, OUT / tag / "3-settings-gestures.png")

            opt.locator("#tabs .tab").nth(3).click()
            opt.wait_for_timeout(500)
            shoot(opt, OUT / tag / "4-settings-drag.png")

            opt.locator("#tabs .tab").nth(6).click()
            opt.wait_for_timeout(500)
            shoot(opt, OUT / tag / "5-settings-privacy.png")
        finally:
            ctx.close()

srv.shutdown()
print("\n完成。")
