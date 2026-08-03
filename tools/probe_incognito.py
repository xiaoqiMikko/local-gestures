# -*- coding: utf-8 -*-
"""Decisive test: we own the Chrome process, Playwright only attaches.

With launch_persistent_context Playwright owns the browser and will kill it
when it loses track of targets — which makes "the browser died" ambiguous.
Attaching over CDP removes Playwright from the equation entirely: if the
process is gone afterwards, Chrome really did exit.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
EXT = Path(r"E:\code\projectExtend\local-gestures")
PORT = 9335
PROFILE = Path(tempfile.gettempdir()) / f"lg-incog3-{int(time.time())}"
for old in PROFILE.parent.glob("lg-incog3-*"):
    if old != PROFILE:
        shutil.rmtree(old, ignore_errors=True)
PROFILE.mkdir(parents=True, exist_ok=True)


def cdp(path):
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{PORT}{path}", timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"__error__": type(e).__name__}


proc = subprocess.Popen([
    CHROME,
    f"--user-data-dir={PROFILE}",
    f"--remote-debugging-port={PORT}",
    f"--disable-extensions-except={EXT}",
    f"--load-extension={EXT}",
    "--no-first-run",
    "--no-default-browser-check",
    "--window-size=1100,800",
    "about:blank",
])

print("等待 Chrome 起来...")
for _ in range(60):
    if "__error__" not in cdp("/json/version"):
        break
    time.sleep(0.5)

info = cdp("/json/version")
print("Chrome:", info.get("Browser"))
print("进程存活:", proc.poll() is None)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
    ctx = browser.contexts[0]

    sw = None
    for _ in range(40):
        if ctx.service_workers:
            sw = ctx.service_workers[0]
            break
        time.sleep(0.25)

    if not sw:
        tl = cdp("/json/list")
        print("worker 缺席。当前 targets:")
        if isinstance(tl, list):
            for t in tl:
                print("   ", t.get("type"), "|", str(t.get("url"))[:70])
        proc.terminate()
        sys.exit(1)

    print("扩展 id:", sw.url.split("/")[2])
    n0 = sw.evaluate("() => chrome.windows.getAll().then(w => w.length)")
    print("窗口数(前):", n0)

    print("\n>>> 执行 newIncognito")
    try:
        r = sw.evaluate("() => runAction('newIncognito', null)")
        print("runAction 返回:", r)
    except Exception as e:
        print("Playwright 通道:", type(e).__name__)

    time.sleep(3)

    v2 = cdp("/json/version")
    alive_http = "__error__" not in v2
    alive_proc = proc.poll() is None
    print("\nCDP HTTP 可达:", alive_http)
    print("Chrome 进程存活:", alive_proc, "(exit code:", proc.poll(), ")")

    tl = cdp("/json/list")
    if isinstance(tl, list):
        print(f"target 数: {len(tl)}")

    print()
    if alive_proc and alive_http:
        print("✅ 系统 Chrome 上完全正常。之前的『浏览器挂了』是 Playwright")
        print("   在丢失 target 追踪后主动杀掉了它自己启动的 Chromium。")
    else:
        print("❌ 系统 Chrome 也退出了 —— 确认是产品 bug,必须处理。")

try:
    proc.terminate()
    proc.wait(timeout=10)
except Exception:
    pass
