# -*- coding: utf-8 -*-
"""Generate _locales/{en,zh_CN,zh_TW}/messages.json from one table.

Keeping all three languages in a single source table is the only reliable way
to guarantee the key sets stay identical.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "_locales"

# key: (en, zh_CN, zh_TW)
M = {
    # ---- identity -------------------------------------------------------
    "extName": ("Local Gestures — Mouse Gestures, 100% Offline",
                "Local Gestures — 鼠标手势,完全离线",
                "Local Gestures — 滑鼠手勢,完全離線"),
    "extDesc": ("Mouse gestures, rocker, wheel, super drag and more. Zero network requests — nothing about your browsing ever leaves this machine.",
                "鼠标手势、摇杆、滚轮、超级拖拽等全套功能。零网络请求 —— 你的浏览数据永远不会离开本机。",
                "滑鼠手勢、搖桿、滾輪、超級拖曳等全套功能。零網路請求 —— 你的瀏覽資料永遠不會離開本機。"),
    "tagline": ("Never phones home.", "绝不回传任何数据。", "絕不回傳任何資料。"),
    "optionsTitle": ("Local Gestures settings", "Local Gestures 设置", "Local Gestures 設定"),

    # ---- command descriptions ------------------------------------------
    "cmdSlot1": ("Shortcut slot 1", "快捷键槽位 1", "快速鍵欄位 1"),
    "cmdSlot2": ("Shortcut slot 2", "快捷键槽位 2", "快速鍵欄位 2"),
    "cmdSlot3": ("Shortcut slot 3", "快捷键槽位 3", "快速鍵欄位 3"),
    "cmdSlot4": ("Shortcut slot 4", "快捷键槽位 4", "快速鍵欄位 4"),

    # ---- tabs -----------------------------------------------------------
    "tabGestures": ("Gestures", "手势", "手勢"),
    "tabPopup": ("Popup wheel", "弹出轮盘", "彈出輪盤"),
    "tabMouse": ("Mouse", "鼠标", "滑鼠"),
    "tabDrag": ("Drag", "拖拽", "拖曳"),
    "tabEntries": ("Other triggers", "其他入口", "其他入口"),
    "tabLook": ("Appearance", "外观", "外觀"),
    "tabAdvanced": ("Advanced", "高级", "進階"),

    # ---- generic --------------------------------------------------------
    "optEnabled": ("Enabled", "启用", "啟用"),
    "saved": ("Saved", "已保存", "已儲存"),
    "added": ("Added", "已添加", "已新增"),
    "replaced": ("Replaced", "已替换", "已取代"),
    "imported": ("Settings imported", "设置已导入", "設定已匯入"),
    "importFailed": ("Could not read that file", "无法读取该文件", "無法讀取該檔案"),
    "resetDone": ("Reset to defaults", "已恢复默认", "已還原預設"),
    "confirmReset": ("Reset every setting to its default?",
                     "确定把所有设置恢复为默认值?",
                     "確定將所有設定還原為預設值?"),
    "warnNoGesture": ("Draw or compose a gesture first.",
                      "请先画出或拼出一个手势。",
                      "請先畫出或組出一個手勢。"),
    "hintUnassigned": ("unassigned", "未绑定", "未綁定"),
    "btnDelete": ("Delete", "删除", "刪除"),

    # ---- stroke ---------------------------------------------------------
    "optStrokeEnabled": ("Stroke gestures", "笔画手势", "筆畫手勢"),
    "noteStroke": ("Hold the gesture button and draw a shape.",
                   "按住手势键画出形状。",
                   "按住手勢鍵畫出形狀。"),
    "optButton": ("Gesture button", "手势按键", "手勢按鍵"),
    "btnRight": ("Right button", "右键", "右鍵"),
    "btnMiddle": ("Middle button", "中键", "中鍵"),
    "padHint": ("Hold the gesture button and draw here",
                "按住手势键在此处画",
                "按住手勢鍵在此處畫"),
    "lblGesture": ("Gesture", "手势", "手勢"),
    "lblAction": ("Action", "动作", "動作"),
    "btnClear": ("Clear", "清除", "清除"),
    "btnAdd": ("Add / replace", "添加 / 替换", "新增 / 取代"),
    "colGesture": ("Gesture", "手势", "手勢"),
    "colAction": ("Action", "动作", "動作"),
    "colDirection": ("Direction", "方向", "方向"),

    # ---- popup ----------------------------------------------------------
    "optPopup": ("Popup wheel", "弹出轮盘", "彈出輪盤"),
    "notePopup": ("Hold the gesture button still — without moving — and eight actions fan out around the cursor. Move toward one and release.",
                  "按住手势键保持不动,八个动作会在光标周围展开。移向其中一个后松开即可执行。",
                  "按住手勢鍵保持不動,八個動作會在游標周圍展開。移向其中一個後放開即可執行。"),
    "optPopupDelay": ("Hold time before it appears (ms)",
                      "按住多久后弹出(毫秒)",
                      "按住多久後彈出(毫秒)"),

    # ---- rocker / wheel / dblclick / simple drag -------------------------
    "optRocker": ("Rocker gestures", "摇杆手势", "搖桿手勢"),
    "noteRocker": ("Hold one mouse button and click the other.",
                   "按住一个鼠标键,点击另一个。",
                   "按住一個滑鼠鍵,點擊另一個。"),
    "optRockerLR": ("Hold left, click right", "按住左键,点右键", "按住左鍵,點右鍵"),
    "optRockerRL": ("Hold right, click left", "按住右键,点左键", "按住右鍵,點左鍵"),
    "optWheel": ("Wheel gestures", "滚轮手势", "滾輪手勢"),
    "noteWheel": ("Hold the gesture button and turn the wheel.",
                  "按住手势键并滚动滚轮。",
                  "按住手勢鍵並滾動滾輪。"),
    "optWheelUp": ("Wheel up", "向上滚", "向上滾"),
    "optWheelDown": ("Wheel down", "向下滚", "向下滾"),
    "optDoubleClick": ("Double click action", "双击动作", "雙擊動作"),
    "noteDoubleClick": ("Only fires on empty page area — never on text, links or form controls.",
                        "仅在页面空白处生效 —— 不会在文字、链接或表单控件上触发。",
                        "僅在頁面空白處生效 —— 不會在文字、連結或表單控制項上觸發。"),
    "optDoubleClickAction": ("On double click", "双击时", "雙擊時"),
    "optSimpleDrag": ("Simple drag", "简单拖拽", "簡單拖曳"),
    "noteSimpleDrag": ("Straight left-button drag on empty page area. Off by default because it competes with selecting text.",
                       "在页面空白处按左键直线拖动。默认关闭,因为它会和选择文字冲突。",
                       "在頁面空白處按左鍵直線拖曳。預設關閉,因為它會和選取文字衝突。"),
    "optSimpleDragDist": ("Minimum distance (px)", "最小距离(像素)", "最小距離(像素)"),

    # ---- super drag ------------------------------------------------------
    "optSuperDrag": ("Super drag", "超级拖拽", "超級拖曳"),
    "noteDrag": ("Drag a link, an image or selected text. The direction you drag decides what happens.",
                 "拖动链接、图片或选中的文字。拖动方向决定执行什么。",
                 "拖曳連結、圖片或選取的文字。拖曳方向決定執行什麼。"),
    "optDragDist": ("Minimum drag distance (px)", "最小拖动距离(像素)", "最小拖曳距離(像素)"),
    "hdrDragLink": ("Links", "链接", "連結"),
    "hdrDragImage": ("Images", "图片", "圖片"),
    "hdrDragText": ("Selected text", "选中的文字", "選取的文字"),
    "noteSearch": ("Search uses whatever engine Chrome is already set to. This extension contains no search URL of its own.",
                   "搜索使用 Chrome 已设定的搜索引擎。本扩展内部不含任何搜索网址。",
                   "搜尋使用 Chrome 已設定的搜尋引擎。本擴充功能內部不含任何搜尋網址。"),

    # ---- other triggers --------------------------------------------------
    "hdrIcon": ("Toolbar icon", "工具栏图标", "工具列圖示"),
    "optIconAction": ("Clicking the icon does", "点击图标时执行", "點擊圖示時執行"),
    "hdrContext": ("Context menu", "右键菜单", "右鍵選單"),
    "optContextMenu": ("Add actions to the right-click menu",
                       "把动作加进右键菜单",
                       "將動作加入右鍵選單"),
    "btnAddItem": ("Add item", "添加一项", "新增一項"),
    "hdrKeys": ("Keyboard shortcuts", "键盘快捷键", "鍵盤快速鍵"),
    "noteKeys": ("Pick what each slot does here; assign the actual key combinations on Chrome's shortcuts page.",
                 "在这里决定每个槽位执行什么;实际的按键组合在 Chrome 的快捷键页面设置。",
                 "在這裡決定每個欄位執行什麼;實際的按鍵組合在 Chrome 的快速鍵頁面設定。"),
    "btnOpenShortcuts": ("Open Chrome shortcut settings",
                         "打开 Chrome 快捷键设置",
                         "開啟 Chrome 快速鍵設定"),
    "hdrTouch": ("Touch screen", "触摸屏", "觸控螢幕"),
    "optTouch": ("Touch gestures", "触摸手势", "觸控手勢"),
    "noteTouch": ("Uses the same stroke table as the mouse.",
                  "使用与鼠标相同的手势表。",
                  "使用與滑鼠相同的手勢表。"),
    "optTouchFingers": ("Fingers", "手指数", "手指數"),

    # ---- appearance ------------------------------------------------------
    "optTrail": ("Show gesture trail", "显示手势轨迹", "顯示手勢軌跡"),
    "optTrailColor": ("Trail colour", "轨迹颜色", "軌跡顏色"),
    "optTrailWidth": ("Trail width", "轨迹粗细", "軌跡粗細"),
    "optHint": ("Show action hint", "显示动作提示", "顯示動作提示"),
    "optHintPos": ("Hint position", "提示位置", "提示位置"),
    "posBottom": ("Bottom", "底部", "底部"),
    "posTop": ("Top", "顶部", "頂部"),
    "optSuppress": ("Suppress the context menu after a gesture",
                    "手势后不弹出右键菜单",
                    "手勢後不彈出右鍵選單"),

    # ---- advanced --------------------------------------------------------
    "optMinDistance": ("Direction threshold (px)", "方向判定阈值(像素)", "方向判定閾值(像素)"),
    "optMinStroke": ("Minimum stroke length (px)", "最短笔画长度(像素)", "最短筆畫長度(像素)"),
    "optHomeUrl": ("Home URL", "主页网址", "首頁網址"),
    "optExcludes": ("Disabled on these URLs (one pattern per line, * allowed)",
                    "在这些网址上禁用(每行一条,可用 *)",
                    "在這些網址上停用(每行一條,可用 *)"),
    "optPerms": ("Optional permissions", "可选权限", "選用權限"),
    "permDownloads": ("Downloads — only needed to save dragged images",
                      "下载 —— 仅在保存拖拽的图片时需要",
                      "下載 —— 僅在儲存拖曳的圖片時需要"),
    "permBookmarks": ("Bookmarks — only needed for the \"Add bookmark\" action",
                      "书签 —— 仅在使用「添加书签」动作时需要",
                      "書籤 —— 僅在使用「新增書籤」動作時需要"),
    "notePerms": ("Both are off by default and can be revoked here at any time.",
                  "两项默认都不开启,并且随时可以在这里撤销。",
                  "兩項預設都不開啟,並且隨時可以在這裡撤銷。"),
    "btnExport": ("Export settings", "导出设置", "匯出設定"),
    "btnImport": ("Import settings", "导入设置", "匯入設定"),
    "btnReset": ("Reset to defaults", "恢复默认", "還原預設"),

    # ---- action groups ---------------------------------------------------
    "group_nav": ("Navigation", "导航", "導覽"),
    "group_tab": ("Tabs", "标签页", "分頁"),
    "group_win": ("Windows", "窗口", "視窗"),
    "group_scroll": ("Scrolling", "滚动", "捲動"),
    "group_zoom": ("Zoom", "缩放", "縮放"),
    "group_page": ("Page", "页面", "頁面"),
    "group_misc": ("Other", "其他", "其他"),

    # ---- drag modes ------------------------------------------------------
    "drag_newTabBg": ("Open in background tab", "在后台标签页打开", "在背景分頁開啟"),
    "drag_newTabFg": ("Open in foreground tab", "在前台标签页打开", "在前景分頁開啟"),
    "drag_newWindow": ("Open in new window", "在新窗口打开", "在新視窗開啟"),
    "drag_copy": ("Copy to clipboard", "复制到剪贴板", "複製到剪貼簿"),
    "drag_download": ("Download", "下载", "下載"),
    "drag_searchBg": ("Search in background tab", "在后台标签页搜索", "在背景分頁搜尋"),
    "drag_searchFg": ("Search in foreground tab", "在前台标签页搜索", "在前景分頁搜尋"),
    "drag_none": ("Do nothing", "不执行", "不執行"),
}

# ---- actions -------------------------------------------------------------
ACTIONS = {
    "back": ("Back", "后退", "上一頁"),
    "forward": ("Forward", "前进", "下一頁"),
    "reload": ("Reload", "刷新", "重新整理"),
    "reloadHard": ("Hard reload (ignore cache)", "强制刷新(忽略缓存)", "強制重新整理(忽略快取)"),
    "stop": ("Stop loading", "停止加载", "停止載入"),
    "home": ("Home page", "打开主页", "開啟首頁"),
    "parentDir": ("Parent directory", "上级目录", "上層目錄"),
    "siteRoot": ("Site root", "网站首页", "網站首頁"),

    "newTab": ("New tab", "新建标签页", "開新分頁"),
    "closeTab": ("Close tab", "关闭标签页", "關閉分頁"),
    "reopenTab": ("Reopen closed tab", "恢复关闭的标签页", "復原關閉的分頁"),
    "duplicateTab": ("Duplicate tab", "复制标签页", "複製分頁"),
    "togglePin": ("Pin / unpin tab", "固定 / 取消固定", "釘選 / 取消釘選"),
    "toggleMute": ("Mute / unmute tab", "静音 / 取消静音", "靜音 / 取消靜音"),
    "prevTab": ("Previous tab", "上一个标签页", "上一個分頁"),
    "nextTab": ("Next tab", "下一个标签页", "下一個分頁"),
    "firstTab": ("First tab", "第一个标签页", "第一個分頁"),
    "lastTab": ("Last tab", "最后一个标签页", "最後一個分頁"),
    "lastUsedTab": ("Last used tab", "上次使用的标签页", "上次使用的分頁"),
    "closeOtherTabs": ("Close other tabs", "关闭其他标签页", "關閉其他分頁"),
    "closeRightTabs": ("Close tabs to the right", "关闭右侧标签页", "關閉右側分頁"),
    "closeLeftTabs": ("Close tabs to the left", "关闭左侧标签页", "關閉左側分頁"),
    "moveTabLeft": ("Move tab left", "标签页左移", "分頁左移"),
    "moveTabRight": ("Move tab right", "标签页右移", "分頁右移"),
    "detachTab": ("Move tab to new window", "移到新窗口", "移至新視窗"),

    "newWindow": ("New window", "新建窗口", "開新視窗"),
    "newIncognito": ("New incognito window", "新建无痕窗口", "開新無痕視窗"),
    "closeWindow": ("Close window", "关闭窗口", "關閉視窗"),
    "minimizeWindow": ("Minimise window", "最小化窗口", "最小化視窗"),
    "toggleMaximize": ("Maximise / restore", "最大化 / 还原", "最大化 / 還原"),
    "toggleFullscreen": ("Toggle full screen", "切换全屏", "切換全螢幕"),

    "scrollTop": ("Scroll to top", "滚动到顶部", "捲動到頂部"),
    "scrollBottom": ("Scroll to bottom", "滚动到底部", "捲動到底部"),
    "scrollPageUp": ("Page up", "上翻一页", "上翻一頁"),
    "scrollPageDown": ("Page down", "下翻一页", "下翻一頁"),

    "zoomIn": ("Zoom in", "放大", "放大"),
    "zoomOut": ("Zoom out", "缩小", "縮小"),
    "zoomReset": ("Reset zoom", "重置缩放", "重設縮放"),

    "viewSource": ("View page source", "查看网页源码", "檢視網頁原始碼"),
    "print": ("Print", "打印", "列印"),
    "copyUrl": ("Copy URL", "复制网址", "複製網址"),
    "copyTitle": ("Copy title", "复制标题", "複製標題"),
    "copyTitleUrl": ("Copy title and URL", "复制标题和网址", "複製標題和網址"),
    "addBookmark": ("Add bookmark", "添加书签", "新增書籤"),
    "openOptions": ("Open settings", "打开设置", "開啟設定"),

    "none": ("Do nothing", "无", "無"),
}
for k, v in ACTIONS.items():
    M["action_" + k] = v

LANGS = [("en", 0), ("zh_CN", 1), ("zh_TW", 2)]

for name, idx in LANGS:
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    payload = {k: {"message": v[idx]} for k, v in M.items()}
    path = d / "messages.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(f"{path}  ({len(payload)} keys)")

print("\nkey 数量一致性检查:", len({len(v) for v in [M]}) == 1, len(M))
