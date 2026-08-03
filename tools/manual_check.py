# -*- coding: utf-8 -*-
"""Open a browser with the extension loaded, for the checks in MANUAL-CHECKS.md.

The browser is Playwright's Chromium rather than the installed Chrome because
Chrome 137 dropped --load-extension and Chrome 150 ignores it even with
--enable-unsafe-extension-debugging (verified: developerPrivate reports no
extensions installed). That leaves exactly one browser that can still load an
unpacked extension without a manual click-through.

It is also launched *through* Playwright rather than as a detached process,
which took a few tries to get right: started on its own, that binary exits
immediately with code 3 and no error in its log. So the script stays running
and holds the browser open, and ends when the last window is closed.

The profile persists between runs, so permissions granted and settings changed
during a session are still there next time.
"""
import sys
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
PROFILE = Path.home() / ".local-gestures-manual-profile"


class Quiet(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass


srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(WWW)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{srv.server_address[1]}/demo.html"

GUIDE = f"""
================================================================
  人工验证浏览器已启动 —— 扩展已加载,配置会保留
================================================================

演示页:{URL}
设置页:地址栏 chrome://extensions → Local Gestures → 扩展选项

7 项在 MANUAL-CHECKS.md,按这个顺序点:

  1. 新建无痕窗口 —— 唯一可能真是 bug 的一项,先测这个
       设置页 → 手势 → 把 ↑← 改成「新建无痕窗口」→ 在网页上画
       期望:弹出无痕窗口,原窗口一切正常,没崩

  2. 打印 —— 绑一个手势到「打印」,画出来
       期望:弹出打印预览,Esc 关掉后页面正常

  3. 键盘快捷键 —— 直接按 Alt+Shift+1
       期望:恢复最近关闭的标签页

  4. 右键菜单 —— 设置页 → 其他入口 → 打开「加进右键菜单」,再点右键
       期望:出现 Local Gestures 子菜单,点了能执行

  5. 工具栏图标 —— 点右上角拼图钉住图标,再点图标
       期望:打开设置页

  6. 可选权限 —— 设置页 → 高级 → 勾「下载」
       期望:弹出授权框;允许后把某个拖拽方向设成下载,拖张图试试

  7. 触摸手势 —— 有触摸屏才测

关掉所有窗口,这个脚本自己结束。
================================================================
"""

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(PROFILE),
        headless=False,
        no_viewport=True,
        ignore_default_args=["--disable-extensions"],
        args=[
            f"--disable-extensions-except={EXT}",
            f"--load-extension={EXT}",
            "--no-first-run", "--no-default-browser-check",
            "--start-maximized",
        ],
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(URL)
    print(GUIDE, flush=True)

    # Hold the browser open. Playwright kills what it launched the moment this
    # process ends, so "ends when you close the window" has to be explicit.
    while True:
        try:
            if not ctx.pages:
                break
        except Exception:
            break
        time.sleep(2)

srv.shutdown()
print("浏览器已关闭。")
