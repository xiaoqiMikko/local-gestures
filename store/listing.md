# 应用商店上架材料

给 Edge Add-ons(以及日后 Chrome Web Store)填表用。**直接复制粘贴。**

> 🔴 **商店描述里绝不能出现其他浏览器名（Chrome / Google 等）。**
> Partner Center 会当场弹出「避免在扩展说明中引用其他浏览器」的警告，硬发大概率被打回。
> Manifest V2 那段故事改成只说标准名（"Manifest V2 已于 2025 年停止运行"），
> 「你 Chrome 里设的默认搜索引擎」改成「你浏览器里设的默认搜索引擎」。
> 权限用途说明那一栏不受此限 —— 那是给审核员看的，不公开展示。

- 隐私政策 URL:`https://github.com/xiaoqiMikko/local-gestures/blob/main/PRIVACY.md`
- 主页 URL:`https://github.com/xiaoqiMikko/local-gestures`
- 支持 URL:`https://github.com/xiaoqiMikko/local-gestures/issues`
- 类别:**生产力工具**(Productivity)
- 截图:`store/screenshots/<语言>/`,1280×800,5 张

---

## 名称

```
Local Gestures
```

## 单一用途说明(Single purpose)

> 审核必答项。写得越窄越好 —— 说得越宽,审核越会追问你为什么要那么多权限。

```
The extension has one purpose: to let the user trigger browser actions by
drawing mouse gestures. Every permission it requests exists to perform an
action the user explicitly bound to a gesture. It has no second function.
```

---

## English

### Short description (≤ 132 chars)

```
Mouse gestures that never talk to a server. Zero network requests, no analytics, no account — and you can verify that yourself.
```

### Detailed description

```
Draw with your mouse to control the browser. Hold the right button, move, and
release — back, forward, close tab, reopen a closed tab, switch tabs, scroll,
zoom, and 38 more actions.

WHY ANOTHER GESTURE EXTENSION

Manifest V2 stopped running in Chrome 138, and a lot of long-standing gesture
extensions did not make the transition. Users were pushed toward whatever
survived.

Gesture extensions are in an unusually sensitive position. To work at all, one
must see mouse input on every page you visit. That is exactly the access you
would want an analytics pipeline to have. So the question worth asking is not
"which one has the most features" — it is "can I check what it does with that
access?"

This one is built so you can. The complete source is public, a few thousand
readable lines, not minified.

WHAT IT DOES NOT DO

• No network requests. There is no fetch, XMLHttpRequest or WebSocket anywhere
  in the source
• No analytics, no telemetry, no crash reporting
• No account, no login, no remote configuration
• No host permissions in the manifest
• No reading of browsing history or cookies
• Settings are stored locally — not even synced to your browser account

INPUT METHODS

• Stroke gestures — hold a button and draw. 19 bound out of the box
• Rocker gestures — hold one mouse button, click the other
• Wheel gestures — hold a button and turn the wheel
• Super drag — drag a link, image or selection; the direction picks the action
• Popup wheel — hold still and eight actions fan out around the cursor
• Simple drag, double click, touch gestures
• Right-click menu entries and four keyboard shortcuts

45 ACTIONS

Navigation, tab management, window management, scrolling, zoom, page tools —
plus copy URL, copy title, open a link in the background, search the selected
text with your own default engine.

ALSO

Live gesture trail, action name shown while you draw, per-site disable list,
settings import and export, and a drawing pad in the settings so you can
record a gesture by drawing it instead of typing "DRU".

English, 简体中文 and 繁體中文.

Source and installation guide:
https://github.com/xiaoqiMikko/local-gestures
```

### Search terms

```
mouse gestures, gesture, rocker gesture, super drag, privacy
```

---

## 简体中文

### 简短说明(≤ 132 字符)

```
完全不联网的鼠标手势扩展。零网络请求、无统计、无账号 —— 而且你可以自己验证。
```

### 详细说明

```
用鼠标画一下就能控制浏览器。按住右键、划动、松开 —— 后退、前进、关闭标签页、
恢复刚关掉的标签页、切换标签页、滚动、缩放,以及另外 38 个动作。

为什么还要再做一个手势扩展

Manifest V2 在 Chrome 138 上彻底停止运行,很多用了很多年的手势扩展没能完成
迁移。用户只能被推向那些活下来的。

手势扩展的处境很特殊:它要能工作,就必须看到你访问的**每一个页面**上的鼠标
输入。这恰好就是一条数据统计管线最想要的权限。所以真正值得问的问题不是
「哪个功能最多」,而是「我能不能查清楚它拿这个权限干了什么」。

这个扩展就是照着「你能查」来做的。全部源码公开,几千行,没有压缩混淆。

它不做什么

• 不联网。整个源码里没有任何一处 fetch / XMLHttpRequest / WebSocket
• 没有统计、没有埋点、没有崩溃上报
• 没有账号、不用登录、没有远程配置
• manifest 里没有 host_permissions
• 不读浏览历史,不读 cookie
• 配置存在本机,连你的浏览器账号都不同步

输入方式

• 手势 —— 按住按键画。默认已绑好 19 个
• 摇杆手势 —— 按住一个键,点另一个键
• 滚轮手势 —— 按住按键滚滚轮
• 超级拖拽 —— 拖链接、图片或选中的文字,**方向**决定执行什么
• 轮盘菜单 —— 按住不动,八个动作以光标为中心展开
• 简单拖拽、双击、触摸手势
• 右键菜单项,以及四个键盘快捷键

45 个动作

导航、标签页管理、窗口管理、滚动、缩放、页面工具,还有复制网址、复制标题、
后台打开链接、用**你自己的默认搜索引擎**搜索选中的文字。

其他

实时手势轨迹、画的时候显示将要执行的动作名、按站点禁用、配置导入导出,
以及设置页里的手写板 —— 直接画一个手势录进去,不用手敲「DRU」。

支持 English、简体中文、繁體中文。

源码与安装教程:
https://github.com/xiaoqiMikko/local-gestures
```

### 搜索关键词

```
鼠标手势, 手势, 摇杆手势, 超级拖拽, 隐私
```

---

## 繁體中文

### 簡短說明(≤ 132 字元)

```
完全不連網的滑鼠手勢擴充功能。零網路請求、無統計、無帳號 —— 而且你可以自己驗證。
```

### 詳細說明

```
用滑鼠畫一下就能控制瀏覽器。按住右鍵、劃動、放開 —— 上一頁、下一頁、關閉分頁、
還原剛關掉的分頁、切換分頁、捲動、縮放,以及另外 38 個動作。

為什麼還要再做一個手勢擴充功能

Manifest V2 在 Chrome 138 上徹底停止運行,很多用了很多年的手勢擴充功能沒能
完成遷移。使用者只能被推向那些活下來的。

手勢擴充功能的處境很特殊:它要能運作,就必須看到你造訪的**每一個頁面**上的
滑鼠輸入。這恰好就是一條數據統計管線最想要的權限。所以真正值得問的問題不是
「哪一個功能最多」,而是「我能不能查清楚它拿這個權限做了什麼」。

這個擴充功能就是照著「你能查」來做的。全部原始碼公開,幾千行,沒有壓縮混淆。

它不做什麼

• 不連網。整個原始碼裡沒有任何一處 fetch / XMLHttpRequest / WebSocket
• 沒有統計、沒有埋點、沒有當機回報
• 沒有帳號、不用登入、沒有遠端設定
• manifest 裡沒有 host_permissions
• 不讀瀏覽紀錄,不讀 cookie
• 設定存在本機,連你的瀏覽器帳號都不同步

輸入方式

• 手勢 —— 按住按鍵畫。預設已綁好 19 個
• 搖桿手勢 —— 按住一個鍵,點另一個鍵
• 滾輪手勢 —— 按住按鍵滾滾輪
• 超級拖曳 —— 拖連結、圖片或選取的文字,**方向**決定執行什麼
• 輪盤選單 —— 按住不動,八個動作以游標為中心展開
• 簡單拖曳、雙擊、觸控手勢
• 右鍵選單項目,以及四個鍵盤快速鍵

45 個動作

導覽、分頁管理、視窗管理、捲動、縮放、頁面工具,還有複製網址、複製標題、
背景開啟連結、用**你自己的預設搜尋引擎**搜尋選取的文字。

其他

即時手勢軌跡、畫的時候顯示即將執行的動作名稱、依網站停用、設定匯入匯出,
以及設定頁裡的手寫板 —— 直接畫一個手勢錄進去,不用手打「DRU」。

支援 English、简体中文、繁體中文。

原始碼與安裝教學:
https://github.com/xiaoqiMikko/local-gestures
```

### 搜尋關鍵字

```
滑鼠手勢, 手勢, 搖桿手勢, 超級拖曳, 隱私
```

---

## 权限用途说明(审核必填)

> 这一栏是整个上架流程里唯一会被卡的地方 —— 因为要在**所有网站**上注入内容
> 脚本。写法上有一条原则:**说清楚"不做什么"比说"做什么"更重要**,并且
> 每一条都给出可核对的位置,让审核员能自己去仓库里查。

### `<all_urls>` / activeTab(内容脚本)

```
A mouse gesture must be recognisable on whatever page the user is currently
on, so the content script has to be injected broadly. This is inherent to the
category — there is no narrower match pattern that would still let the feature
work.

What the content script actually does is limited to input handling:
- listens for mousedown / mousemove / mouseup / wheel / touch events
- draws the gesture trail on a canvas inside a closed shadow root
- reads the drag payload (link URL, image URL, or selected text) ONLY at the
  moment the user completes a drag gesture, in order to perform the action the
  user bound to that direction

It does NOT read page content, does NOT modify the page, does NOT inject
anything into the page's own JavaScript context, and does NOT transmit
anything. There are no network APIs anywhere in the source: `fetch`,
`XMLHttpRequest`, `WebSocket`, `EventSource` and `navigator.sendBeacon` do not
appear in src/ at all, and the manifest declares no host_permissions.

This is verifiable in one command against the public source:
  grep -rn "fetch(\|XMLHttpRequest\|WebSocket\|sendBeacon" src/
Source: https://github.com/xiaoqiMikko/local-gestures
```

### `tabs`

```
Required for the tab actions the user binds to gestures: close, close others,
close to the right, duplicate, pin, switch to next/previous, move between
windows. Also used to read the active tab's title and URL for the "copy title"
and "copy URL" actions — that text goes to the clipboard only.
```

### `sessions`

```
Required for the "reopen closed tab" action (chrome.sessions.restore).
```

### `search`

```
Required for the "search with selected text" drag action. It calls
chrome.search.query, which uses the user's own configured default search
engine. No search URL is hard-coded in this extension, and it does not learn
which engine the user has set.
```

### `contextMenus`

```
Optional feature, off by default: the user can choose to place selected
actions into the right-click menu. Only used to build those menu entries.
```

### `storage`

```
Stores the user's gesture bindings and preferences with chrome.storage.local.
Deliberately not chrome.storage.sync — the configuration is not uploaded
anywhere, including to the user's own browser account.
```

### `downloads`(可选权限,安装时不申请)

```
Declared as an optional permission and NOT granted at install time. It is
requested at runtime only if the user assigns "download" to a drag direction,
and can be revoked from the settings page at any time.
```

### `bookmarks`(可选权限,安装时不申请)

```
Declared as an optional permission and NOT granted at install time. It is
requested at runtime only if the user binds the "add bookmark" action, and can
be revoked from the settings page at any time.
```

---

## 上架前自查

- [ ] 截图 5 张,1280×800,`store/screenshots/` 下已生成且能正常打开
- [ ] `PRIVACY.md` 在 GitHub 上可公开访问(仓库是 public)
- [ ] `manifest.json` 的 `version` 是否要抬一位
- [ ] `python tools/verify.py` 通过
- [ ] `python tools/e2e_test.py` 通过
- [ ] `MANUAL-CHECKS.md` 里 7 项人工验证过一遍
- [ ] 打包:把仓库目录压成 zip,**不要**包含 `tools/`、`store/`、`.git/`
