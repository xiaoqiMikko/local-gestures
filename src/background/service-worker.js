/**
 * Service worker: executes everything that needs a chrome.* API.
 *
 * MV3 workers are killed aggressively, so no state is kept in module scope
 * beyond caches that can be rebuilt. Anything that must survive a restart
 * goes into chrome.storage.session.
 *
 * No fetch, no XMLHttpRequest, no WebSocket. Ever.
 */
'use strict';

importScripts('/src/common/actions.js', '/src/common/defaults.js');

// --------------------------------------------------------------- tab memory

const RECENT_KEY = 'recentTabs';

chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  const { [RECENT_KEY]: list = [] } = await chrome.storage.session.get(RECENT_KEY);
  const next = [tabId, ...list.filter((id) => id !== tabId)].slice(0, 4);
  await chrome.storage.session.set({ [RECENT_KEY]: next });
});

chrome.tabs.onRemoved.addListener(async (tabId) => {
  const { [RECENT_KEY]: list = [] } = await chrome.storage.session.get(RECENT_KEY);
  await chrome.storage.session.set({
    [RECENT_KEY]: list.filter((id) => id !== tabId)
  });
});

async function lastUsedTabId(currentId) {
  const { [RECENT_KEY]: list = [] } = await chrome.storage.session.get(RECENT_KEY);
  return list.find((id) => id !== currentId) ?? null;
}

// -------------------------------------------------------------------- utils

async function currentTab(sender) {
  if (sender && sender.tab && sender.tab.id != null) return sender.tab;
  const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
  return tab || null;
}

/** Tabs of the window, in display order. */
async function siblings(tab) {
  return chrome.tabs.query({ windowId: tab.windowId });
}

async function hasPermission(name) {
  if (!name) return true;
  return chrome.permissions.contains({ permissions: [name] });
}

const ZOOM_STEPS = [0.25, 0.33, 0.5, 0.67, 0.75, 0.8, 0.9, 1,
  1.1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 5];

async function stepZoom(tabId, dir) {
  const z = await chrome.tabs.getZoom(tabId);
  // Nearest step, then move one along. Float comparison is deliberately
  // loose because Chrome returns values like 1.0999999999999999.
  let i = 0;
  let best = Infinity;
  ZOOM_STEPS.forEach((v, idx) => {
    const d = Math.abs(v - z);
    if (d < best) { best = d; i = idx; }
  });
  const next = ZOOM_STEPS[Math.min(ZOOM_STEPS.length - 1, Math.max(0, i + dir))];
  await chrome.tabs.setZoom(tabId, next);
}

// ------------------------------------------------------------------ actions

/**
 * @returns {Promise<object>} `{}` on success, `{clipboard}` when the page
 *          must write text, `{error}` when the action could not run.
 */
async function runAction(id, sender) {
  const tab = await currentTab(sender);
  if (!tab) return { error: 'no-tab' };

  const meta = self.LG_ACTION_BY_ID[id];
  if (!meta) return { error: 'unknown-action' };
  if (meta.needs && !(await hasPermission(meta.needs))) {
    return { error: 'missing-permission:' + meta.needs };
  }

  const config = await self.LG_loadConfig();

  switch (id) {
    // --- navigation -----------------------------------------------------
    case 'back': await chrome.tabs.goBack(tab.id); return {};
    case 'forward': await chrome.tabs.goForward(tab.id); return {};
    case 'reload': await chrome.tabs.reload(tab.id); return {};
    case 'reloadHard':
      await chrome.tabs.reload(tab.id, { bypassCache: true });
      return {};
    case 'home':
      if (config.homeUrl) await chrome.tabs.update(tab.id, { url: config.homeUrl });
      else await chrome.tabs.create({});
      return {};

    // --- tabs -----------------------------------------------------------
    case 'newTab': await chrome.tabs.create({}); return {};
    case 'closeTab': await chrome.tabs.remove(tab.id); return {};
    case 'reopenTab': await chrome.sessions.restore(); return {};
    case 'duplicateTab': await chrome.tabs.duplicate(tab.id); return {};
    case 'togglePin':
      await chrome.tabs.update(tab.id, { pinned: !tab.pinned });
      return {};
    case 'toggleMute':
      await chrome.tabs.update(tab.id, {
        muted: !(tab.mutedInfo && tab.mutedInfo.muted)
      });
      return {};

    case 'prevTab':
    case 'nextTab': {
      const all = await siblings(tab);
      if (all.length < 2) return {};
      const i = all.findIndex((t) => t.id === tab.id);
      const step = id === 'nextTab' ? 1 : -1;
      const target = all[(i + step + all.length) % all.length];
      await chrome.tabs.update(target.id, { active: true });
      return {};
    }
    case 'firstTab':
    case 'lastTab': {
      const all = await siblings(tab);
      if (!all.length) return {};
      const target = id === 'firstTab' ? all[0] : all[all.length - 1];
      await chrome.tabs.update(target.id, { active: true });
      return {};
    }
    case 'lastUsedTab': {
      const other = await lastUsedTabId(tab.id);
      if (other == null) return {};
      try {
        const t = await chrome.tabs.get(other);
        await chrome.windows.update(t.windowId, { focused: true });
        await chrome.tabs.update(other, { active: true });
      } catch (e) { return { error: 'gone' }; }
      return {};
    }

    case 'closeOtherTabs':
    case 'closeRightTabs':
    case 'closeLeftTabs': {
      const all = await siblings(tab);
      const doomed = all.filter((t) => {
        if (t.id === tab.id || t.pinned) return false;   // never kill pinned
        if (id === 'closeRightTabs') return t.index > tab.index;
        if (id === 'closeLeftTabs') return t.index < tab.index;
        return true;
      }).map((t) => t.id);
      if (doomed.length) await chrome.tabs.remove(doomed);
      return {};
    }

    case 'moveTabLeft':
      await chrome.tabs.move(tab.id, { index: Math.max(0, tab.index - 1) });
      return {};
    case 'moveTabRight':
      await chrome.tabs.move(tab.id, { index: tab.index + 1 });
      return {};
    case 'detachTab': {
      const all = await siblings(tab);
      if (all.length < 2) return {};
      await chrome.windows.create({ tabId: tab.id });
      return {};
    }

    // --- windows --------------------------------------------------------
    case 'newWindow': await chrome.windows.create({}); return {};
    case 'newIncognito': await chrome.windows.create({ incognito: true }); return {};
    case 'closeWindow': await chrome.windows.remove(tab.windowId); return {};
    case 'minimizeWindow':
      await chrome.windows.update(tab.windowId, { state: 'minimized' });
      return {};
    case 'toggleMaximize': {
      const w = await chrome.windows.get(tab.windowId);
      await chrome.windows.update(tab.windowId, {
        state: w.state === 'maximized' ? 'normal' : 'maximized'
      });
      return {};
    }
    case 'toggleFullscreen': {
      const w = await chrome.windows.get(tab.windowId);
      await chrome.windows.update(tab.windowId, {
        state: w.state === 'fullscreen' ? 'normal' : 'fullscreen'
      });
      return {};
    }

    // --- zoom -----------------------------------------------------------
    case 'zoomIn': await stepZoom(tab.id, 1); return {};
    case 'zoomOut': await stepZoom(tab.id, -1); return {};
    case 'zoomReset': await chrome.tabs.setZoom(tab.id, 0); return {};

    // --- page -----------------------------------------------------------
    case 'viewSource':
      await chrome.tabs.create({
        url: 'view-source:' + tab.url,
        index: tab.index + 1
      });
      return {};
    case 'copyUrl': return { clipboard: tab.url || '' };
    case 'copyTitle': return { clipboard: tab.title || '' };
    case 'copyTitleUrl':
      return { clipboard: (tab.title || '') + '\n' + (tab.url || '') };
    case 'addBookmark':
      await chrome.bookmarks.create({ title: tab.title, url: tab.url });
      return {};
    case 'openOptions':
      await chrome.runtime.openOptionsPage();
      return {};

    default:
      return { error: 'not-implemented:' + id };
  }
}

// --------------------------------------------------------------- super drag

async function runDrag(msg, sender) {
  const tab = await currentTab(sender);
  const index = tab ? tab.index + 1 : undefined;

  // Search uses the browser's own default engine. No search URL is hard
  // coded anywhere in this extension, so switching engines in Chrome
  // switches it here too.
  if (msg.mode === 'searchFg') {
    await chrome.search.query({ text: msg.value, disposition: 'NEW_TAB' });
    return {};
  }
  if (msg.mode === 'searchBg') {
    // chrome.search.query has no "background" disposition, but it does
    // accept a target tab — so open one unfocused and search inside it.
    const bg = await chrome.tabs.create({ active: false, index: index });
    await chrome.search.query({ text: msg.value, tabId: bg.id });
    return {};
  }

  if (msg.mode === 'download') {
    if (!(await hasPermission('downloads'))) {
      return { error: 'missing-permission:downloads' };
    }
    await chrome.downloads.download({ url: msg.value });
    return {};
  }

  const url = msg.value;
  if (!/^https?:|^ftp:|^data:image\//i.test(url)) return { error: 'blocked-scheme' };

  if (msg.mode === 'newWindow') {
    await chrome.windows.create({ url: url });
    return {};
  }
  if (msg.mode === 'newTabFg' || msg.mode === 'newTabBg') {
    await chrome.tabs.create({
      url: url,
      index: index,
      active: msg.mode === 'newTabFg'
    });
    return {};
  }
  return { error: 'unknown-mode:' + msg.mode };
}

// -------------------------------------------------------------- context menu

const MENU_PREFIX = 'lg:';

async function rebuildContextMenu() {
  await chrome.contextMenus.removeAll();
  const config = await self.LG_loadConfig();
  if (!config.contextMenuEnabled) return;

  const items = (config.contextMenuItems || []).filter(
    (id) => id && id !== 'none' && self.LG_ACTION_BY_ID[id]
  );
  if (!items.length) return;

  const label = (id) =>
    chrome.i18n.getMessage('action_' + id) || id;

  if (items.length === 1) {
    chrome.contextMenus.create({
      id: MENU_PREFIX + items[0],
      title: label(items[0]),
      contexts: ['page', 'frame', 'selection', 'link', 'image']
    });
    return;
  }

  const parent = chrome.contextMenus.create({
    id: MENU_PREFIX + '__root',
    title: chrome.i18n.getMessage('extName') || 'Local Gestures',
    contexts: ['page', 'frame', 'selection', 'link', 'image']
  });
  for (const id of items) {
    chrome.contextMenus.create({
      id: MENU_PREFIX + id,
      parentId: parent,
      title: label(id),
      contexts: ['page', 'frame', 'selection', 'link', 'image']
    });
  }
}

/**
 * Run an action on behalf of a non-page trigger (menu, shortcut, icon) and
 * relay anything the page has to finish — clipboard writes need a DOM, and a
 * failure needs to be shown to the user rather than dropped.
 */
async function runAndRelay(id, tab) {
  let res;
  try {
    res = await runAction(id, tab ? { tab: tab } : null);
  } catch (e) {
    res = { error: String((e && e.message) || e) };
  }
  if (!res || !tab || tab.id == null) return res;
  if (res.clipboard) {
    chrome.tabs.sendMessage(tab.id, {
      type: 'lg-clipboard', value: res.clipboard
    }, () => void chrome.runtime.lastError);
  }
  if (res.error) {
    chrome.tabs.sendMessage(tab.id, {
      type: 'lg-error', value: res.error
    }, () => void chrome.runtime.lastError);
  }
  return res;
}

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (!String(info.menuItemId).startsWith(MENU_PREFIX)) return;
  const id = String(info.menuItemId).slice(MENU_PREFIX.length);
  if (id === '__root') return;
  await runAndRelay(id, tab);
});

// ------------------------------------------------------- keyboard shortcuts

chrome.commands.onCommand.addListener(async (command) => {
  const config = await self.LG_loadConfig();
  const id = (config.commandSlots || {})[command];
  if (!id || id === 'none') return;
  await runAndRelay(id, await currentTab(null));
});

// ------------------------------------------------------------------ wiring

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || typeof msg.type !== 'string') return false;

  const work =
    msg.type === 'lg-exec' ? runAction(msg.action, sender) :
    msg.type === 'lg-drag' ? runDrag(msg, sender) : null;

  if (!work) return false;

  work.then(sendResponse, (err) => {
    sendResponse({ error: String((err && err.message) || err) });
  });
  return true;   // keep the message channel open for the async reply
});

chrome.runtime.onInstalled.addListener(async ({ reason }) => {
  // Seed defaults so the options page never shows an empty form.
  const cfg = await self.LG_loadConfig();
  await self.LG_saveConfig(cfg);
  await rebuildContextMenu();
  if (reason === 'install') chrome.runtime.openOptionsPage();
});

chrome.runtime.onStartup.addListener(rebuildContextMenu);

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'local') return;
  if (changes.contextMenuEnabled || changes.contextMenuItems) {
    rebuildContextMenu();
  }
});

chrome.action.onClicked.addListener(async (tab) => {
  const config = await self.LG_loadConfig();
  await runAndRelay(config.iconAction || 'openOptions', tab);
});
