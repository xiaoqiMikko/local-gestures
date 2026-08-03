# Installation (step by step)

[简体中文](INSTALL.zh-CN.md)

**No technical knowledge needed. About three minutes.**

The extension is not in the Web Store yet, so it is installed through
**Developer mode**. That is a normal, officially supported Chrome feature — no
patching, no system settings changed.

Works in Chrome, Edge, Brave, Vivaldi and any other Chromium browser.

---

## 1. Download

1. Open https://github.com/xiaoqiMikko/local-gestures
2. Click the green **`< > Code`** button near the top right
3. Click **Download ZIP**

## 2. Unzip

Right-click the zip → **Extract All** → choose a place **you will not delete
by accident**.

> ⚠️ **This matters.**
> The extracted folder must stay where it is — do not delete, rename or move
> it. The browser reads the extension from that exact path on every start.
>
> Somewhere like `D:\extensions\local-gestures` is fine.
> **Not** your Downloads folder or the Desktop, which tend to get cleaned out.

Open the folder and check: **`manifest.json` should be right there.**
If instead you see another `local-gestures-main` folder inside, go one level
deeper — the correct folder is the one containing `manifest.json`.

## 3. Open the extensions page

Type this in the address bar and press Enter:

```
chrome://extensions
```

(On Edge: `edge://extensions`)

## 4. Turn on Developer mode

Top **right** of that page there is a **Developer mode** switch. Turn it on.
Three buttons appear at the top left.

## 5. Load it

Click **Load unpacked**, select the folder from step 2 — the one containing
`manifest.json` — and confirm.

✅ Done. **Local Gestures** now appears in the list.

## 6. Try it

Open any ordinary web page, **hold the right mouse button and drag left**,
then release. You should go back one page.

Also try:
- hold right, drag **right** → forward
- hold right, drag **down then right** → close tab
- hold right, drag **down then up** → reopen the closed tab

## 7. Optional: pin the icon

Click the **puzzle piece** 🧩 at the top right → find Local Gestures → click
the **pin**. Clicking the icon opens the settings page.

---

## Troubleshooting

### "Disable developer mode extensions" pops up on every launch

Chrome shows this for *every* unpacked extension. It does not mean anything is
wrong with this one. Click **Cancel** and it stays working; it will not ask
again during that session. The only real fix is a Web Store listing.

### Installed, but gestures do nothing

In this order:

1. **Try a normal web page.** Extensions are forbidden by the browser on
   `chrome://` pages, the Web Store and the new-tab page. Nothing can change that.
2. **Check it is enabled** — the toggle on the card in `chrome://extensions`.
3. **Draw further.** A stroke needs 16 px before it counts.
4. **Reload the page.** A freshly installed extension does not enter tabs that
   were already open.

### Incognito

`chrome://extensions` → **Details** on Local Gestures → **Allow in Incognito**.

### Updating

1. Download and extract the new ZIP
2. Overwrite the old folder with the new contents
3. Click the **reload arrow** ⟳ on the Local Gestures card

Your settings are preserved.

### Uninstalling

`chrome://extensions` → **Remove** on the Local Gestures card.

### Backing up settings

Settings page → last tab → **Export** writes a json file. **Import** restores it.

---

## About safety

Being wary of installing extensions is the correct instinct. Every claim here
is checkable:

- **All source is here**, a few thousand readable lines, not minified
- **No network code** — no `fetch`, `XMLHttpRequest`, WebSocket anywhere in `src/`
- **No host permissions** in `manifest.json`
- **No history, no cookies**
- Settings live in `chrome.storage.local` — not even synced to your Google account

To check for yourself:

```bash
python tools/verify.py
```

It fails if any of the above stops being true. See [PRIVACY.md](PRIVACY.md).
