# Local Gestures

English · [简体中文](README.zh-CN.md)

Mouse gestures for Chrome that never talk to a server.

**Zero network requests. No analytics. No account. No remote config.**
Nothing about your browsing leaves the machine — and you can verify that
yourself in about ten seconds (see [Verifying the privacy claim](#verifying-the-privacy-claim)).

Manifest V3 native. English / 简体中文 / 繁體中文.

---

## Why this exists

Manifest V2 stopped running in stable Chrome with version 138 (July 2025), and
Google removes the last MV2 extensions from the Web Store on **31 August 2026**.
A lot of long-standing gesture extensions did not make the transition, and users
were pushed toward whatever survived.

Gesture extensions are in an unusually sensitive position: to work at all, they
need to see mouse input on **every page you visit**. That is exactly the access
you would want an analytics pipeline to have. So the interesting question is not
"which one has the most features" — it is **"can I check what it does with that
access?"**

This one is built so that you can.

## Features

Everything below is implemented and covered by the end-to-end test suite.

| Trigger | What it is | Default |
|---|---|---|
| **Stroke gestures** | Hold the gesture button and draw. 19 gestures pre-bound, up to 3 strokes each | on |
| **Rocker gestures** | Hold one mouse button, click the other | on |
| **Wheel gestures** | Hold the gesture button and turn the wheel | on |
| **Super drag** | Drag a link / image / selection — the **direction** decides the action | on |
| **Popup wheel** | Hold still and eight actions fan out around the cursor | off |
| **Simple drag** | Straight left-button drag on empty page area | off |
| **Double click** | On empty page area only — double-clicking text still selects the word | off |
| **Touch gestures** | Multi-finger strokes, sharing the mouse gesture table | off |
| **Context menu** | Put chosen actions in the right-click menu | off |
| **Toolbar icon** | Click it to run any action | opens settings |
| **Keyboard shortcuts** | Four slots, bound in Chrome's own shortcut settings | on |

**45 actions** across navigation, tabs, windows, scrolling, zoom and page tools.

Also: live gesture trail, action name shown while you draw, per-site disable
list, settings import/export, and a drawing pad in the options page so you can
record a new gesture by drawing it rather than typing `DRU`.

### Defaults worth knowing

| Gesture | Action |
|---|---|
| `←` / `→` | Back / Forward |
| `↑` / `↓` | Scroll to top / bottom |
| `↓→` | Close tab |
| `↓↑` | Reopen closed tab |
| `↑↓` | Reload |
| `←→` / `→←` | Next / previous tab |

Hold right and click left to go back; hold right and scroll to switch tabs.

## Verifying the privacy claim

Do not take the word of a README. Check it:

```bash
# 1. No network APIs anywhere in the source
grep -rn "fetch(\|XMLHttpRequest\|WebSocket\|EventSource\|sendBeacon" src/
#    -> only the comment that promises there are none

# 2. No host permissions, no request interception, no history access
grep -n "host_permissions\|webRequest\|\"history\"\|\"cookies\"" manifest.json
#    -> no matches

# 3. Or just run the checker, which asserts all of the above
python tools/verify.py
```

`tools/verify.py` fails the build if a network call, a broad permission, an
untranslated string, or a dangling action reference ever appears.

### What it does ask for, and why

| Permission | Why | Could it be smaller? |
|---|---|---|
| `<all_urls>` content script | A gesture must be recognisable on whatever page you are on | No — this is inherent to gesture extensions. It is also why the questions above matter |
| `tabs` | Close / switch / pin / duplicate tabs, read the title for "copy title" | No |
| `sessions` | Reopen closed tab | No |
| `search` | Drag-to-search **using your own default engine** — no search URL is hard-coded here | No |
| `contextMenus` | Optional right-click entries | No |
| `downloads` | **Optional.** Only requested if you set a drag direction to "download" | Yes — off by default |
| `bookmarks` | **Optional.** Only requested if you bind the "Add bookmark" action | Yes — off by default |

Settings are stored with `chrome.storage.local`. Not `sync` — your gesture
configuration is not uploaded to a Google account either.

## Install

**From source** (until the Web Store listing is live):

1. Download or clone this repository
2. Open `chrome://extensions`
3. Turn on **Developer mode**
4. Click **Load unpacked** and pick the repository folder

Works in any Chromium browser with MV3 support: Chrome, Edge, Brave, Vivaldi.
Requires Chrome 116+.

## Known limitations

Stated up front rather than discovered later:

- **Gestures do not cross iframe boundaries.** Start a stroke in the page and
  drag into an embedded frame and the stroke is cut short. This affects every
  gesture extension built on content scripts.
- **No gestures on `chrome://` pages, the Web Store, or other extensions'
  pages.** Chrome forbids content scripts there; nothing can be done about it.
- **Simple drag and double click are off by default** because they compete with
  selecting text. Turn them on only if that trade-off suits you.
- **Four directions only** (no diagonals). Diagonals roughly double how
  precisely you have to draw, for very little gain.

## Development

```bash
python tools/verify.py     # static consistency + privacy checks
python tools/e2e_test.py   # loads a real Chrome, drives every input mode
python tools/demo.py       # opens a browser on the demo page to try by hand
```

The e2e suite asserts observable effects — URL changed, tab count changed,
scroll position reached the document's own maximum — rather than "the handler
ran". 109 checks. Two actions cannot be driven by automation at all and are
listed in [MANUAL-CHECKS.md](MANUAL-CHECKS.md) rather than quietly skipped.

> ⚠️ **Do not use Playwright's bundled Chromium to judge anything about
> rendering.** On some machines it starts without the user-agent stylesheet,
> so every block element computes to `display: inline` — tables collapse into
> a single line and `<style>` tags are painted as body text. The page looks
> completely broken while being perfectly fine in real Chrome. Anything that
> captures or measures layout (`gen_screenshots.py`) uses the installed
> Chrome and asserts `getComputedStyle(document.body).display === 'block'`
> before shooting.

Adding an action means touching four places, and `verify.py` will tell you if
you miss one:

1. `src/common/actions.js` — declare id, group, and where it runs
2. `src/background/service-worker.js` or `src/content/content.js` — implement it
3. `tools/gen_locales.py` — add the three translations, then re-run it
4. optionally a default binding in `src/common/defaults.js`

Translations live in one table in `tools/gen_locales.py` and are generated into
all three `_locales` folders, so the key sets cannot drift apart.
Icons likewise come from `tools/gen_icons.py`.

## Feedback

Bugs and feature requests: please open an issue. If a gesture does not fire on
a specific site, include the URL — that is almost always an iframe or a page
that swallows mouse events, and it is worth documenting either way.

## Licence

MIT — see [LICENSE](LICENSE).
