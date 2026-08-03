# -*- coding: utf-8 -*-
"""Open a browser with the extension loaded, for the checks in MANUAL-CHECKS.md.

Not driven by Playwright — Playwright owns the browser process it launches and
kills it when the script ends, which is the opposite of what is wanted here.
So the binary is started directly and the script just keeps the local test
page served until the window is closed.

The browser is Playwright's Chromium rather than the installed Chrome because
Chrome 137 dropped --load-extension and Chrome 150 ignores it even with
--enable-unsafe-extension-debugging (verified: developerPrivate reports no
extensions installed). That leaves exactly one browser that can still load an
unpacked extension without a manual click-through.

The profile is kept between runs, so permissions granted and settings changed
during a check session are still there next time.
"""
import subprocess
import sys
import threading
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
BASE = f"http://127.0.0.1:{srv.server_address[1]}"

with sync_playwright() as p:
    exe = p.chromium.executable_path
PROFILE.mkdir(parents=True, exist_ok=True)

print(f"""
================================================================
  人工验证浏览器已启动 —— 扩展已加载,配置会保留
================================================================

演示页:{BASE}/demo.html

要点的 7 项在 MANUAL-CHECKS.md,按顺序:

  1. 新建无痕窗口 —— 唯一可能真是 bug 的一项,先测这个
       设置页 → 手势 → 把 ↑← 改成「新建无痕窗口」→ 在网页上画
       期望:弹出无痕窗口,原窗口一切正常,没崩

  2. 打印 —— 绑一个手势到「打印」,画出来
       期望:弹出打印预览,Esc 关掉后页面正常

  3. 键盘快捷键 —— 直接按 Alt+Shift+1
       期望:恢复最近关闭的标签页

  4. 右键菜单 —— 设置页 → 其他入口 → 打开「加进右键菜单」,然后点右键
       期望:出现 Local Gestures 子菜单,点了能执行

  5. 工具栏图标 —— 点右上角拼图 🧩 钉住图标,再点图标
       期望:打开设置页

  6. 可选权限 —— 设置页 → 高级 → 勾「下载」
       期望:弹出授权框;允许后把某个拖拽方向设成下载,拖张图试试

  7. 触摸手势 —— 有触摸屏才测

关掉浏览器窗口,这个脚本就结束。
================================================================
""")

proc = subprocess.Popen([
    exe,
    f"--user-data-dir={PROFILE}",
    f"--disable-extensions-except={EXT}",
    f"--load-extension={EXT}",
    "--no-first-run", "--no-default-browser-check",
    f"{BASE}/demo.html",
])
try:
    proc.wait()
finally:
    srv.shutdown()
print("浏览器已关闭。")
