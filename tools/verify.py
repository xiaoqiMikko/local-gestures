# -*- coding: utf-8 -*-
"""Static consistency checks for the extension.

Catches the class of mistake that only shows up at runtime otherwise:
a control bound to an id that no longer exists, an i18n key nobody wrote,
an action referenced in defaults that was renamed, a stray fetch().

Run:  python tools/verify.py
Exit code is non-zero when anything fails, so CI can use it directly.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fails = []
warns = []


def fail(msg):
    fails.append(msg)


def warn(msg):
    warns.append(msg)


def read(p):
    return (ROOT / p).read_text(encoding="utf-8")


def code_only(src):
    """Blank out comments, keeping offsets so line numbers stay correct.

    Needed because this file's own prose says "no fetch, no XMLHttpRequest",
    and a naive grep would flag the promise as a violation of itself.
    String literals are preserved: they are real code.
    """
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in "'\"`":
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == c:
                    break
                j += 1
            out.append(src[i:j + 1])
            i = j + 1
        elif src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            # keep newlines so reported line numbers do not drift
            out.append("".join(ch if ch == "\n" else " " for ch in src[i:j]))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


# --------------------------------------------------------------- 1. manifest
manifest = json.loads(read("manifest.json"))

referenced = []
referenced += list(manifest.get("icons", {}).values())
referenced.append(manifest["background"]["service_worker"])
referenced.append(manifest["options_ui"]["page"])
for cs in manifest.get("content_scripts", []):
    referenced += cs.get("js", [])

for rel in referenced:
    if not (ROOT / rel).exists():
        fail(f"manifest 引用了不存在的文件: {rel}")

# ------------------------------------------------- 2. content script ordering
cs_js = manifest["content_scripts"][0]["js"]
provides = {}          # symbol -> index of the file that defines it
for i, rel in enumerate(cs_js):
    src = read(rel)
    for sym in re.findall(r"root\.(LG\w+)\s*=", src):
        provides.setdefault(sym, i)

for i, rel in enumerate(cs_js):
    src = read(rel)
    for sym in set(re.findall(r"self\.(LG\w+)", src)):
        if sym not in provides:
            fail(f"{rel} 用到 self.{sym},但没有任何文件定义它")
        elif provides[sym] > i:
            fail(f"{rel} 用到 self.{sym},但它在 {cs_js[provides[sym]]} "
                 f"里才定义 —— content_scripts 顺序错了")

# ------------------------------------------------------------------ 3. i18n
locales = {}
for d in (ROOT / "_locales").iterdir():
    if d.is_dir():
        locales[d.name] = json.loads((d / "messages.json").read_text(encoding="utf-8"))

if not locales:
    fail("_locales 下没有任何语言")

base = manifest["default_locale"]
if base not in locales:
    fail(f"default_locale={base} 不存在")

base_keys = set(locales.get(base, {}))
for name, msgs in locales.items():
    missing = base_keys - set(msgs)
    extra = set(msgs) - base_keys
    if missing:
        fail(f"语言 {name} 缺少 {len(missing)} 个 key: {sorted(missing)[:6]}")
    if extra:
        fail(f"语言 {name} 多出 {len(extra)} 个 key: {sorted(extra)[:6]}")
    for k, v in msgs.items():
        if not str(v.get("message", "")).strip():
            fail(f"语言 {name} 的 {k} 是空字符串")

# manifest __MSG_x__ placeholders
for m in re.findall(r"__MSG_(\w+)__", read("manifest.json")):
    if m not in base_keys:
        fail(f"manifest 用了 __MSG_{m}__,但 {base} 里没有这个 key")

# data-i18n in html
html = read("src/options/options.html")
for key in re.findall(r'data-i18n="([^"]+)"', html):
    if key not in base_keys:
        fail(f"options.html 的 data-i18n=\"{key}\" 在 {base} 里没有对应文案")

# getMessage('literal') across all js.
# The closing paren is required: getMessage('action_' + id) is a runtime
# lookup, not a literal, and is covered by the action checks below instead.
for js in ROOT.rglob("src/**/*.js"):
    src = code_only(js.read_text(encoding="utf-8"))
    for key in re.findall(r"getMessage\(\s*['\"]([\w]+)['\"]\s*[,)]", src):
        if key not in base_keys:
            fail(f"{js.relative_to(ROOT)} 取了不存在的文案 key: {key}")

# ----------------------------------------------------------------- 4. actions
actions_src = read("src/common/actions.js")
action_ids = re.findall(r"\{\s*id:\s*'([^']+)'", actions_src)
if len(action_ids) != len(set(action_ids)):
    dupes = {a for a in action_ids if action_ids.count(a) > 1}
    fail(f"actions.js 有重复的动作 id: {sorted(dupes)}")

for a in action_ids:
    if "action_" + a not in base_keys:
        fail(f"动作 {a} 没有 action_{a} 文案")

groups = re.findall(r"const GROUPS = \[([^\]]+)\]", actions_src)
declared_groups = re.findall(r"'([^']+)'", groups[0]) if groups else []
used_groups = set(re.findall(r"group:\s*'([^']+)'", actions_src))
for g in used_groups:
    if g not in declared_groups:
        fail(f"动作用了未声明的分组: {g}")
    if "group_" + g not in base_keys:
        fail(f"分组 {g} 没有 group_{g} 文案")

# service worker must handle every 'bg' action
sw = read("src/background/service-worker.js")
handled = set(re.findall(r"case '([\w]+)':", sw))
for m in re.finditer(r"\{\s*id:\s*'([^']+)'[^}]*where:\s*'bg'", actions_src):
    aid = m.group(1)
    if aid not in handled:
        fail(f"动作 {aid} 标为 where:'bg',但 service worker 没有对应 case")

content_js = read("src/content/content.js")
page_handled = set(re.findall(r"case '([\w]+)':", content_js))
for m in re.finditer(r"\{\s*id:\s*'([^']+)'[^}]*where:\s*'page'", actions_src):
    aid = m.group(1)
    if aid not in page_handled:
        fail(f"动作 {aid} 标为 where:'page',但 content.js 没有对应 case")

# ---------------------------------------------------------------- 5. defaults
defaults_src = read("src/common/defaults.js")

# every action id mentioned in the default tables must exist
for block in ["DEFAULT_GESTURES", "DEFAULT_POPUP", "DEFAULT_CONTEXT_ITEMS",
              "DEFAULT_SIMPLE_DRAG"]:
    m = re.search(block + r"\s*=\s*[\[{](.*?)[\]}];", defaults_src, re.S)
    if not m:
        fail(f"defaults.js 找不到 {block}")
        continue
    for val in re.findall(r"'([\w]+)'", m.group(1)):
        if val in ("U", "D", "L", "R"):
            continue
        if val not in action_ids:
            fail(f"{block} 引用了不存在的动作: {val}")

for slot in re.findall(r"slot\d:\s*'([\w]+)'", defaults_src):
    if slot not in action_ids:
        fail(f"commandSlots 引用了不存在的动作: {slot}")

for key in ["rockerLeftRight", "rockerRightLeft", "wheelUp", "wheelDown",
            "doubleClickAction", "iconAction"]:
    m = re.search(key + r":\s*'([\w]+)'", defaults_src)
    if m and m.group(1) not in action_ids:
        fail(f"{key} 默认值引用了不存在的动作: {m.group(1)}")

# drag modes understood by content.js + service worker
DRAG_MODES = {"newTabBg", "newTabFg", "newWindow", "copy", "download",
              "searchBg", "searchFg", "none"}
for block in ["DEFAULT_DRAG_LINK", "DEFAULT_DRAG_IMAGE", "DEFAULT_DRAG_TEXT"]:
    m = re.search(block + r"\s*=\s*\{(.*?)\};", defaults_src, re.S)
    if not m:
        fail(f"defaults.js 找不到 {block}")
        continue
    for val in re.findall(r":\s*'([\w]+)'", m.group(1)):
        if val not in DRAG_MODES:
            fail(f"{block} 用了未知的拖拽模式: {val}")
        if "drag_" + val not in base_keys:
            fail(f"拖拽模式 {val} 没有 drag_{val} 文案")

# and the worker must actually implement the non-page ones
for mode in DRAG_MODES - {"copy", "none"}:
    if f"'{mode}'" not in sw:
        fail(f"service worker 没有处理拖拽模式 {mode}")

# ------------------------------------------------- 6. options.js <-> html ids
html_ids = set(re.findall(r'\bid="([^"]+)"', html))
opts = read("src/options/options.js")
for hit in re.findall(r"\$\('#([\w-]+)'\)", opts):
    if hit not in html_ids:
        fail(f"options.js 引用了 HTML 里不存在的 id: #{hit}")

# id lists declared in options.js must map to real config keys
config_keys = set(re.findall(r"^\s{4}(\w+):", defaults_src, re.M))
for name in ["BOOLS", "NUMBERS", "TEXTS", "ACTION_SELECTS"]:
    m = re.search(name + r"\s*=\s*\[(.*?)\];", opts, re.S)
    if not m:
        fail(f"options.js 找不到 {name}")
        continue
    for key in re.findall(r"'([\w]+)'", m.group(1)):
        if key not in config_keys:
            fail(f"options.js 的 {name} 含有非配置项: {key}")
        if key not in html_ids:
            fail(f"options.js 的 {name} 含有 {key},但 HTML 里没有这个 id")

# ------------------------------------------------------- 7. no network access
NET = re.compile(
    r"\b(fetch\s*\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon|"
    r"importScripts\s*\(\s*['\"]https?:|navigator\.connection)"
)
for js in list(ROOT.rglob("src/**/*.js")) + [ROOT / "manifest.json"]:
    src = code_only(js.read_text(encoding="utf-8"))
    for m in NET.finditer(src):
        line = src[:m.start()].count("\n") + 1
        fail(f"发现疑似网络调用 {js.relative_to(ROOT)}:{line} -> {m.group(0)}")

for bad_key in ["host_permissions", "web_accessible_resources"]:
    if bad_key in manifest:
        warn(f"manifest 含有 {bad_key} —— 卖点是最小权限,确认真的需要")

for p in manifest.get("permissions", []):
    if p in ("webRequest", "history", "cookies", "management", "proxy"):
        fail(f"权限 {p} 与「零数据收集」定位冲突")

# ------------------------------------------------------------------- report
print("=" * 62)
print(f"动作 {len(action_ids)} 个 | 语言 {len(locales)} 种 | "
      f"文案 {len(base_keys)} 条 | content 脚本 {len(cs_js)} 个")
print("=" * 62)

for w in warns:
    print("WARN  " + w)
for f in fails:
    print("FAIL  " + f)

if fails:
    print(f"\n❌ {len(fails)} 项不通过")
    sys.exit(1)
print("\n✅ 全部通过")
