# -*- coding: utf-8 -*-
"""Load the extension into a real Chrome and exercise every input mode.

Every assertion checks an observable effect (URL changed, tab count changed,
clipboard content) rather than "did the handler run" — the fastjson lesson:
verify the rendered result, not a proxy for it.
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
# Fresh directory per run: a half-deleted profile from a crashed run is the
# quickest way to get a browser that silently refuses to load the extension.
PROFILE = Path(tempfile.gettempdir()) / f"lg-test-profile-{int(time.time())}"

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"   {detail}" if detail else ""))


# ---------------------------------------------------------------- http server
class NoCacheHandler(SimpleHTTPRequestHandler):
    """Chrome was serving a half-stale mix of old and new test pages.

    Editing the fixtures between runs is normal here, so never let anything
    be cached — a wrong fixture looks exactly like a wrong extension.
    """

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_head(self):
        # Defeat If-Modified-Since so we never answer 304.
        self.headers.replace_header("If-Modified-Since", "") \
            if "If-Modified-Since" in self.headers else None
        if "If-None-Match" in self.headers:
            del self.headers["If-None-Match"]
        return super().send_head()

    def log_message(self, *a):
        pass


handler = partial(NoCacheHandler, directory=str(WWW))
srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{PORT}"
print(f"test server: {BASE}")

# Sweep profiles left behind by earlier runs. Only ones matching our own
# prefix — the daily-driver browser profile lives elsewhere and is untouched.
for old in PROFILE.parent.glob("lg-test-profile-*"):
    if old != PROFILE:
        shutil.rmtree(old, ignore_errors=True)


def gesture(page, path, button="right", step=14):
    """Draw a stroke. path is a list of (x, y) waypoints."""
    x0, y0 = path[0]
    page.mouse.move(x0, y0)
    page.mouse.down(button=button)
    cx, cy = x0, y0
    for (tx, ty) in path[1:]:
        dist = max(abs(tx - cx), abs(ty - cy))
        n = max(2, int(dist / step))
        for i in range(1, n + 1):
            page.mouse.move(cx + (tx - cx) * i / n, cy + (ty - cy) * i / n)
            page.wait_for_timeout(6)
        cx, cy = tx, ty
    try:
        page.mouse.up(button=button)
        page.wait_for_timeout(700)
    except Exception:
        # A gesture bound to "close tab" destroys the very page we are
        # driving. That is success, not an error.
        time.sleep(0.7)


with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE),
        headless=False,
        args=[
            f"--disable-extensions-except={EXT}",
            f"--load-extension={EXT}",
            "--no-first-run",
            "--disable-features=DisableLoadExtensionCommandLineSwitch",
            "--window-size=1280,900",
            "--window-position=40,40",
        ],
        locale="zh-CN",
        # A forced viewport uses CDP device-metrics emulation, which in headed
        # mode squashed the test pages flat (scrollHeight == innerHeight).
        # Let the real window decide instead.
        no_viewport=True,
    )

    # ---------------------------------------------------------- 0. worker up
    # An unpacked extension's id is derived from its path, so it is stable
    # across runs. Handy as a fallback: an MV3 worker can stay asleep until
    # something touches the extension, and then service_workers is empty.
    EXT_ID = "dcdhadchdbhljbodkgllnpniafmlanco"

    def wait_worker(seconds):
        for _ in range(int(seconds * 4)):
            if ctx.service_workers:
                return ctx.service_workers[0]
            time.sleep(0.25)
        return None

    sw = wait_worker(8)
    if not sw:
        # Poke the extension: loading its options page wakes the worker.
        probe = ctx.new_page()
        try:
            probe.goto(f"chrome-extension://{EXT_ID}/src/options/options.html",
                       timeout=15000)
            probe.wait_for_timeout(1500)
        except Exception as e:
            print(f"     [diag] 唤醒失败: {type(e).__name__}")
        sw = wait_worker(8)
        probe.close()

    check("service worker 启动", sw is not None,
          sw.url.split("/")[-1] if sw else "未出现")
    if not sw:
        ctx.close()
        srv.shutdown()
        sys.exit(1)

    ext_id = sw.url.split("/")[2]
    print(f"extension id: {ext_id}\n")

    errors = []
    ctx.on("weberror", lambda e: errors.append(str(e.error)))

    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    # ------------------------------------------------------- 1. options page
    opt = ctx.new_page()
    opt.goto(f"chrome-extension://{ext_id}/src/options/options.html")
    opt.wait_for_timeout(900)

    tabs = opt.locator("#tabs .tab").count()
    check("设置页 7 个分栏", tabs == 7, f"实际 {tabs}")

    n_act = opt.locator("#newAction option").count()
    check("动作下拉有 45 项(不含 none)", n_act == 45, f"实际 {n_act}")

    rows = opt.locator("#gestureTable tbody tr").count()
    check("默认手势 19 条", rows == 19, f"实际 {rows}")

    wheel_cells = opt.locator("#popupGrid .wheel-cell").count()
    check("轮盘 8 格", wheel_cells == 8, f"实际 {wheel_cells}")

    dir_rows = opt.locator("table.dirs tbody tr").count()
    check("方向表 4 张 × 4 行 = 16", dir_rows == 16, f"实际 {dir_rows}")

    # i18n actually resolved (locale is zh-CN)
    title = opt.locator("#tabs .tab").first.inner_text()
    check("中文界面生效", title == "手势", f"首个分栏 = {title!r}")
    back_label = opt.evaluate(
        "() => [...document.querySelectorAll('#newAction option')]"
        ".find(o => o.value === 'back')?.textContent")
    check("动作名已本地化", back_label == "后退", f"back = {back_label!r}")

    untranslated = opt.evaluate(
        "() => [...document.querySelectorAll('[data-i18n]')]"
        ".filter(e => !e.textContent.trim()).length")
    check("没有空白文案", untranslated == 0, f"空白 {untranslated} 处")

    # -------------------------------------------------- 2. stroke: L = back
    page.goto(f"{BASE}/a.html")
    page.wait_for_timeout(400)
    page.click("#toB")
    page.wait_for_load_state()
    page.wait_for_timeout(400)
    check("导航到 B", page.url.endswith("b.html"), page.url)

    gesture(page, [(600, 500), (300, 500)])          # L
    check("手势 ← 触发后退", page.url.endswith("a.html"), page.url)

    # ---------------------------------------------- 3. stroke: R = forward
    gesture(page, [(300, 500), (600, 500)])          # R
    check("手势 → 触发前进", page.url.endswith("b.html"), page.url)

    # ---------------------------------------------- 4. stroke: UR = new tab
    before = len(ctx.pages)
    gesture(page, [(500, 600), (500, 350), (760, 350)])   # U then R
    page.wait_for_timeout(500)
    check("手势 ↑→ 新建标签页", len(ctx.pages) == before + 1,
          f"{before} -> {len(ctx.pages)}")

    # ------------------------------------------- 5. stroke: DR = close tab
    extra = ctx.pages[-1]
    extra.bring_to_front()
    extra.goto(f"{BASE}/a.html")
    extra.wait_for_load_state()
    extra.wait_for_timeout(800)
    print("     [diag] 新标签页 url =", extra.url)
    print("     [diag] 画 DR 前:", [p.url.split('/')[-1] for p in ctx.pages])
    # First prove the *stroke* is recognised, using a harmless action, so a
    # failure below can only mean closeTab itself is broken.
    opt.evaluate("""() => new Promise(r => chrome.storage.local.get('gestures',
        s => { const g = Object.assign({}, s.gestures); g.DR = 'newTab';
               chrome.storage.local.set({ gestures: g }, r); }))""")
    opt.wait_for_timeout(500)
    n0 = len(ctx.pages)
    gesture(extra, [(500, 300), (500, 620), (800, 620)])  # D then R
    time.sleep(1.0)
    print(f"     [diag] DR 绑到 newTab 时: {n0} -> {len(ctx.pages)}")
    check("笔画 ↓→ 被正确识别", len(ctx.pages) == n0 + 1,
          f"{n0} -> {len(ctx.pages)}")
    if len(ctx.pages) == n0 + 1:
        ctx.pages[-1].close()
        time.sleep(0.4)

    # restore and test the real thing
    opt.evaluate("""() => new Promise(r => chrome.storage.local.get('gestures',
        s => { const g = Object.assign({}, s.gestures); g.DR = 'closeTab';
               chrome.storage.local.set({ gestures: g }, r); }))""")
    opt.wait_for_timeout(500)
    extra.bring_to_front()
    extra.wait_for_timeout(300)
    before = len(ctx.pages)
    gesture(extra, [(500, 300), (500, 620), (800, 620)])  # D then R
    time.sleep(1.2)
    print("     [diag] 画 DR 后:", [p.url.split('/')[-1] for p in ctx.pages])
    check("手势 ↓→ 关闭标签页", len(ctx.pages) == before - 1,
          f"{before} -> {len(ctx.pages)}")
    # if it survived, close it so later counts stay meaningful
    if len(ctx.pages) == before and not extra.is_closed():
        extra.close()
        time.sleep(0.4)

    # ------------------------------------------------------ 6. wheel gesture
    page.bring_to_front()
    page.goto(f"{BASE}/a.html")
    t2 = ctx.new_page()
    t2.goto(f"{BASE}/b.html")
    t2.wait_for_timeout(300)
    page.bring_to_front()
    page.wait_for_timeout(300)

    page.mouse.move(600, 500)
    page.mouse.down(button="right")
    page.mouse.wheel(0, 240)          # wheel down = next tab
    page.wait_for_timeout(400)
    page.mouse.up(button="right")
    page.wait_for_timeout(500)
    active = ctx.pages[-1].evaluate("() => document.visibilityState")
    check("滚轮手势切换了标签页",
          t2.evaluate("() => document.visibilityState") == "visible",
          f"B 页 visibility = {t2.evaluate('() => document.visibilityState')}")

    # ------------------------------------------------------- 7. rocker: back
    page.bring_to_front()
    page.goto(f"{BASE}/a.html")
    page.wait_for_timeout(300)
    page.click("#toB")
    page.wait_for_load_state()
    page.wait_for_timeout(400)

    page.mouse.move(600, 500)
    page.mouse.down(button="right")
    page.wait_for_timeout(120)
    page.mouse.down(button="left")
    page.wait_for_timeout(120)
    page.mouse.up(button="left")
    page.mouse.up(button="right")
    page.wait_for_timeout(800)
    check("摇杆(按住右键点左键)后退", page.url.endswith("a.html"), page.url)

    # ------------------------------- 7b. page-side action: D = scroll bottom
    page.goto(f"{BASE}/a.html")
    page.wait_for_timeout(500)

    def max_scroll(pg):
        return pg.evaluate(
            "() => (document.scrollingElement || document.documentElement)"
            ".scrollHeight - window.innerHeight")

    metrics = page.evaluate("""() => ({
        scrollHeight: (document.scrollingElement || document.documentElement).scrollHeight,
        innerHeight: window.innerHeight,
        padH: document.querySelector('.pad')?.offsetHeight,
        fillerH: document.getElementById('filler')?.offsetHeight,
        lines: document.querySelectorAll('.line').length,
        bodyH: document.body.offsetHeight
    })""")
    print("     [diag] 页面滚动指标:", metrics)
    page.evaluate("() => window.scrollTo({ top: 1200, behavior: 'smooth' })")
    page.wait_for_timeout(1200)
    print("     [diag] 页面自己 scrollTo 后 scrollY =",
          page.evaluate("() => window.scrollY"))
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(400)
    # Coordinates depend on the real window size now, so derive them.
    pad_box = page.locator(".pad").bounding_box()
    print("     [diag] .pad 位置:", pad_box)

    limit = max_scroll(page)
    gesture(page, [(600, 300), (600, 700)])       # D
    ys = 0
    for _ in range(30):
        ys = page.evaluate("() => window.scrollY")
        if ys >= limit - 4:
            break
        page.wait_for_timeout(120)
    # "Bottom" means the document's own maximum, not an arbitrary pixel count.
    check("手势 ↓ 滚动到底部(页面内动作)",
          limit > 50 and ys >= limit - 4,
          f"scrollY = {ys} / 最大 {limit}")

    gesture(page, [(600, 700), (600, 300)])       # U = scroll top
    yt = 999
    for _ in range(30):
        yt = page.evaluate("() => window.scrollY")
        if yt < 50:
            break
        page.wait_for_timeout(120)
    check("手势 ↑ 滚动回顶部", yt < 50, f"scrollY = {yt}")

    # ------------------------------------------- 8. context menu suppressed
    page.evaluate("""() => {
      window.__ctx = 0;
      document.addEventListener('contextmenu', () => { window.__ctx++; },
                                { capture: false });
    }""")
    gesture(page, [(600, 500), (600, 300)])       # U = scroll top, valid
    fired = page.evaluate("() => window.__ctx")
    check("手势后右键菜单被吃掉", fired == 0, f"contextmenu 触发 {fired} 次")

    # a plain right click must still open the menu
    page.evaluate("() => { window.__ctx = 0; }")
    page.mouse.move(600, 500)
    page.mouse.down(button="right")
    page.mouse.up(button="right")
    page.wait_for_timeout(400)
    fired2 = page.evaluate("() => window.__ctx")
    check("单纯右键仍然弹菜单", fired2 == 1, f"contextmenu 触发 {fired2} 次")
    page.keyboard.press("Escape")

    # --------------------------------------------- 9. popup wheel (opt-in)
    opt.bring_to_front()
    opt.evaluate("""() => new Promise(r =>
        chrome.storage.local.set({ popupEnabled: true, popupDelay: 250 }, r))""")
    opt.wait_for_timeout(400)
    page.bring_to_front()
    page.goto(f"{BASE}/a.html")
    page.wait_for_timeout(500)

    page.mouse.move(600, 450)
    page.mouse.down(button="right")
    page.wait_for_timeout(700)          # hold still -> wheel appears
    hosts = page.evaluate(
        "() => document.querySelectorAll('div').length")
    # the wheel lives in a closed shadow root, so detect the host element
    has_host = page.evaluate("""() => {
      return [...document.documentElement.children]
        .some(el => el.tagName === 'DIV' && el.style.zIndex === '2147483647');
    }""")
    check("长按弹出轮盘", has_host, "")
    page.mouse.move(600, 330)           # move north -> slot 0
    page.wait_for_timeout(200)
    before = len(ctx.pages)
    page.mouse.up(button="right")
    page.wait_for_timeout(700)
    check("轮盘选中项已执行(新建标签页)", len(ctx.pages) == before + 1,
          f"{before} -> {len(ctx.pages)}")

    # ------------------------------------------------- 10. double click
    opt.bring_to_front()
    opt.evaluate("""() => new Promise(r => chrome.storage.local.set(
        { popupEnabled: false, doubleClickEnabled: true,
          doubleClickAction: 'scrollBottom' }, r))""")
    opt.wait_for_timeout(400)
    page.bring_to_front()
    page.goto(f"{BASE}/a.html")
    page.wait_for_timeout(500)
    # Far left, away from the centred label: double-clicking *text* selects a
    # word and must NOT fire the action, which is the behaviour we want.
    cfg = opt.evaluate("""() => new Promise(r => chrome.storage.local.get(
        ['doubleClickEnabled','doubleClickAction'], r))""")
    print("     [diag] 双击配置:", cfg)
    # Pick a point inside .pad but well away from its centred label.
    pb = page.locator(".pad").bounding_box()
    dx_pt = pb["x"] + 60
    dy_pt = pb["y"] + pb["height"] / 2
    tgt = page.evaluate("""([x, y]) => {
        const el = document.elementFromPoint(x, y);
        return el ? el.tagName + '.' + el.className : 'null';
    }""", [dx_pt, dy_pt])
    print(f"     [diag] 双击点 ({dx_pt:.0f},{dy_pt:.0f}) 处元素: {tgt}")

    limit2 = max_scroll(page)
    page.mouse.dblclick(dx_pt, dy_pt)
    # smooth scrolling takes a while — poll instead of guessing a delay
    y = 0
    for _ in range(30):
        y = page.evaluate("() => window.scrollY")
        if y >= limit2 - 4:
            break
        page.wait_for_timeout(120)
    sel = page.evaluate("() => String(getSelection())")
    check("双击空白处执行动作(滚到底部)",
          limit2 > 50 and y >= limit2 - 4,
          f"scrollY = {y} / 最大 {limit2}, 选中文本 = {sel!r}")

    # and the inverse: double-clicking a word selects it, no action
    page.evaluate("() => window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    box = page.locator("#sel").bounding_box()
    page.mouse.dblclick(box["x"] + 40, box["y"] + box["height"] / 2)
    page.wait_for_timeout(1000)
    y2 = page.evaluate("() => window.scrollY")
    sel2 = page.evaluate("() => String(getSelection()).trim()")
    check("双击文字只选词、不触发动作", y2 < 100 and len(sel2) > 0,
          f"scrollY = {y2}, 选中 = {sel2!r}")

    # -------------------------------------------- 11. exclude list works
    opt.bring_to_front()
    opt.evaluate("""() => new Promise(r => chrome.storage.local.set(
        { excludes: ['*127.0.0.1*'] }, r))""")
    opt.wait_for_timeout(500)
    page.bring_to_front()
    page.goto(f"{BASE}/a.html")
    page.wait_for_timeout(300)
    page.click("#toB")
    page.wait_for_load_state()
    page.wait_for_timeout(400)
    gesture(page, [(600, 500), (300, 500)])       # L would be back
    check("排除列表生效(手势不响应)", page.url.endswith("b.html"), page.url)

    opt.bring_to_front()
    opt.evaluate("""() => new Promise(r =>
        chrome.storage.local.set({ excludes: [] }, r))""")
    opt.wait_for_timeout(400)

    # ------------------------------------------------- 12. runtime errors
    check("运行期无未捕获错误", len(errors) == 0, "; ".join(errors[:3]))

    opt.screenshot(path=str(PROFILE.parent / "lg-options.png"), full_page=True)
    ctx.close()

srv.shutdown()

print("\n" + "=" * 60)
bad = [r for r in results if not r[1]]
print(f"通过 {len(results) - len(bad)} / {len(results)}")
for name, ok, detail in bad:
    print(f"  ✗ {name}  {detail}")
sys.exit(1 if bad else 0)
