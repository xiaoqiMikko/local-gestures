# -*- coding: utf-8 -*-
"""Open a real Chrome with the extension loaded, on the demo page.

Uses a throwaway profile, so it never touches any signed-in browser.
The browser stays open until you close it.
"""
import shutil
import sys
import tempfile
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
EXT = HERE.parent
WWW = HERE / "fixtures"
PROFILE = Path(tempfile.gettempdir()) / f"lg-demo-profile-{int(time.time())}"


class Quiet(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass


for old in PROFILE.parent.glob("lg-demo-profile-*"):
    if old != PROFILE:
        shutil.rmtree(old, ignore_errors=True)

srv = ThreadingHTTPServer(("127.0.0.1", 0),
                          partial(Quiet, directory=str(WWW)))
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

print(f"演示页: http://127.0.0.1:{port}/demo.html")
print("浏览器已打开,关掉窗口即结束。\n")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE),
        headless=False,
        args=[
            f"--disable-extensions-except={EXT}",
            f"--load-extension={EXT}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=DisableLoadExtensionCommandLineSwitch",
            "--window-size=1400,960",
            "--window-position=30,20",
        ],
        locale="zh-CN",
        no_viewport=True,
    )

    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(f"http://127.0.0.1:{port}/demo.html")

    # A second tab so wheel / tab-switching gestures have somewhere to go.
    second = ctx.new_page()
    second.goto(f"http://127.0.0.1:{port}/a.html")
    page.bring_to_front()

    # Wait for the user to close the window.
    try:
        while ctx.pages:
            time.sleep(1)
    except Exception:
        pass

srv.shutdown()
print("演示结束。")
