# Privacy Policy — Local Gestures

**Last updated: 4 August 2026**

## The short version

**Local Gestures collects nothing, sends nothing, and stores nothing outside
your own browser.** There is no server, no analytics, no account, no remote
configuration, and no telemetry of any kind.

## What data is collected

**None.**

The extension does not collect, transmit, sell, rent, or share any information
about you or your browsing. There is no back end for it to send data to — the
source code contains no network calls at all.

You can confirm this yourself without trusting this document. In the source
repository:

```bash
grep -rn "fetch(\|XMLHttpRequest\|WebSocket\|EventSource\|sendBeacon" src/
```

The only matches are comments stating that no such calls exist. The project's
own checker (`python tools/verify.py`) fails the build if any network API,
`host_permissions` entry, or request-interception permission is ever added.

## What is stored, and where

Your settings — gesture bindings, which input modes are on, colours, the
per-site disable list — are stored using `chrome.storage.local`.

- **`local`, not `sync`.** The data stays on the machine and is **not** uploaded
  to a Microsoft or Google account.
- It never leaves your browser profile.
- Uninstalling the extension deletes it.
- You can export it to a file, or wipe it, from the extension's own settings
  page at any time.

## Why the extension needs the permissions it asks for

| Permission | What it is used for |
|---|---|
| Access to all websites | A mouse gesture must be recognisable on whatever page you are currently on. The extension only listens for mouse, wheel and touch input, and draws the gesture trail. It does not read page content, and does not send anything anywhere. |
| `tabs` | Performing tab actions you bound to a gesture — close, switch, pin, duplicate — and reading the current tab's title and URL for the "copy title / copy URL" actions. That text is placed on your clipboard and nowhere else. |
| `sessions` | The "reopen closed tab" action. |
| `search` | The drag-to-search action. It uses **your browser's own default search engine**; this extension does not contain a search URL of its own and does not know which engine you use. |
| `contextMenus` | Optional right-click menu entries, off by default. |
| `downloads` | **Optional, not requested at install.** Only asked for if you set a drag direction to "download". You can revoke it at any time from the settings page. |
| `bookmarks` | **Optional, not requested at install.** Only asked for if you bind the "add bookmark" action. Revocable the same way. |

## Third parties

There are none. No SDKs, no libraries loaded from a CDN, no advertising, no
crash reporting, no A/B testing.

When you use drag-to-search, the browser navigates to your own default search
engine, exactly as if you had typed the query into the address bar. That is a
normal browser navigation — the extension is not involved beyond asking the
browser to perform it.

## Children

The extension collects no data from anyone, including children.

## Changes to this policy

If a future version ever changes what data is handled, this document will be
updated before that version ships, and the change will be described in the
release notes. Given that the design goal is "no network access at all", the
intent is that this section stays unused.

## Contact

Please open an issue on the project's GitHub repository.
