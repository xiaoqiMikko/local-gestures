/**
 * Options page.
 *
 * Every control is bound by element id to the config key of the same name,
 * which keeps this file mostly declarative. The exceptions — gesture table,
 * direction maps, popup wheel, context menu — get their own small builders.
 */
'use strict';

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const ARROW = { U: '↑', D: '↓', L: '←', R: '→' };
const DIRS = ['U', 'D', 'L', 'R'];

/** Drag outcomes are not regular actions, so they get their own vocabulary. */
const DRAG_MODES = {
  dragLink: ['newTabBg', 'newTabFg', 'newWindow', 'copy', 'none'],
  dragImage: ['newTabBg', 'newTabFg', 'newWindow', 'download', 'copy', 'none'],
  dragText: ['searchBg', 'searchFg', 'copy', 'none']
};

/** Plain inputs whose id equals their config key. */
const BOOLS = [
  'enabled', 'gesturesEnabled', 'rockerEnabled', 'wheelEnabled',
  'superDragEnabled', 'simpleDragEnabled', 'popupEnabled',
  'doubleClickEnabled', 'touchEnabled', 'contextMenuEnabled',
  'trailEnabled', 'hintEnabled', 'suppressContextMenu'
];
const NUMBERS = [
  'minDistance', 'minStroke', 'superDragDistance', 'simpleDragDistance',
  'popupDelay', 'trailWidth', 'gestureButton', 'touchFingers'
];
const TEXTS = ['trailColor', 'hintPosition', 'homeUrl'];
/** Selects holding a regular action id. */
const ACTION_SELECTS = [
  'rockerLeftRight', 'rockerRightLeft', 'wheelUp', 'wheelDown',
  'doubleClickAction', 'iconAction'
];
const COMMAND_SLOTS = ['slot1', 'slot2', 'slot3', 'slot4'];

let config = null;
let draft = '';   // gesture being composed in the pad

// --------------------------------------------------------------------- i18n

function t(key, fallback) {
  return chrome.i18n.getMessage(key) || fallback || key;
}

function applyI18n() {
  for (const el of $$('[data-i18n]')) {
    const msg = chrome.i18n.getMessage(el.dataset.i18n);
    if (msg) el.textContent = msg;
  }
  document.title = t('optionsTitle', 'Local Gestures');
}

function actionLabel(id) {
  if (!id) return '—';
  return t('action_' + id, id);
}

function toArrows(dirs) {
  let out = '';
  for (const c of String(dirs)) out += ARROW[c] || c;
  return out;
}

// ------------------------------------------------------------------ helpers

/** Builds an <option> list of every action, grouped. */
function fillActionSelect(sel, includeNone) {
  sel.textContent = '';
  const groups = self.LG_ACTION_GROUPS;
  for (const g of groups) {
    const actions = self.LG_ACTIONS.filter(
      (a) => a.group === g && (includeNone || a.id !== 'none')
    );
    if (!actions.length) continue;
    const og = document.createElement('optgroup');
    og.label = t('group_' + g, g);
    for (const a of actions) {
      const o = document.createElement('option');
      o.value = a.id;
      o.textContent = actionLabel(a.id) + (a.danger ? ' ⚠' : '');
      og.appendChild(o);
    }
    sel.appendChild(og);
  }
}

function fillModeSelect(sel, modes) {
  sel.textContent = '';
  for (const m of modes) {
    const o = document.createElement('option');
    o.value = m;
    o.textContent = t('drag_' + m, m);
    sel.appendChild(o);
  }
}

function toast(msg) {
  const el = $('#toast');
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { el.hidden = true; }, 2000);
}

async function persist() {
  await self.LG_saveConfig(config);
}

// -------------------------------------------------------------- gesture pad

function setupPad() {
  const pad = $('#pad');
  const canvas = $('#padCanvas');
  const ctx = canvas.getContext('2d');
  let drawing = false;
  let rec = null;
  let last = null;

  function resize() {
    const r = pad.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(r.width * dpr);
    canvas.height = Math.round(r.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  window.addEventListener('resize', resize);

  function clear() {
    const r = pad.getBoundingClientRect();
    ctx.clearRect(0, 0, r.width, r.height);
  }

  pad.addEventListener('contextmenu', (e) => e.preventDefault());

  pad.addEventListener('mousedown', (e) => {
    if (e.button !== config.gestureButton) return;
    e.preventDefault();
    drawing = true;
    clear();
    const r = pad.getBoundingClientRect();
    last = { x: e.clientX - r.left, y: e.clientY - r.top };
    rec = { minDistance: config.minDistance, lastX: last.x, lastY: last.y, dirs: [] };
    ctx.strokeStyle = config.trailColor;
    ctx.lineWidth = config.trailWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    draft = '';
    $('#newGesture').textContent = '—';
  });

  pad.addEventListener('mousemove', (e) => {
    if (!drawing) return;
    const r = pad.getBoundingClientRect();
    const x = e.clientX - r.left;
    const y = e.clientY - r.top;

    ctx.beginPath();
    ctx.moveTo(last.x, last.y);
    ctx.lineTo(x, y);
    ctx.stroke();
    last = { x: x, y: y };

    const dx = x - rec.lastX;
    const dy = y - rec.lastY;
    if (Math.abs(dx) < rec.minDistance && Math.abs(dy) < rec.minDistance) return;
    rec.lastX = x;
    rec.lastY = y;
    const dir = Math.abs(dx) >= Math.abs(dy)
      ? (dx > 0 ? 'R' : 'L') : (dy > 0 ? 'D' : 'U');
    if (rec.dirs[rec.dirs.length - 1] === dir) return;
    rec.dirs.push(dir);
    draft = rec.dirs.join('');
    $('#newGesture').textContent = toArrows(draft) || '—';
  });

  window.addEventListener('mouseup', () => {
    if (!drawing) return;
    drawing = false;
    setTimeout(clear, 400);
  });

  for (const b of $$('.dpad button[data-dir]')) {
    b.addEventListener('click', () => {
      const d = b.dataset.dir;
      if (draft[draft.length - 1] === d) return;   // no repeats
      draft += d;
      $('#newGesture').textContent = toArrows(draft);
    });
  }
  $('#clearGesture').addEventListener('click', () => {
    draft = '';
    $('#newGesture').textContent = '—';
    $('#addWarn').textContent = '';
    clear();
  });
}

// ------------------------------------------------------------ gesture table

function renderGestureTable() {
  const tbody = $('#gestureTable tbody');
  tbody.textContent = '';
  const keys = Object.keys(config.gestures).sort(
    (a, b) => a.length - b.length || a.localeCompare(b)
  );
  for (const g of keys) {
    const tr = document.createElement('tr');

    const tdG = document.createElement('td');
    tdG.textContent = toArrows(g);
    tdG.title = g;

    const tdA = document.createElement('td');
    const sel = document.createElement('select');
    fillActionSelect(sel, true);
    sel.value = config.gestures[g];
    sel.addEventListener('change', async () => {
      config.gestures[g] = sel.value;
      await persist();
      toast(t('saved', 'Saved'));
    });
    tdA.appendChild(sel);

    const tdX = document.createElement('td');
    const del = document.createElement('button');
    del.className = 'del';
    del.textContent = '✕';
    del.title = t('btnDelete', 'Delete');
    del.addEventListener('click', async () => {
      delete config.gestures[g];
      await persist();
      renderGestureTable();
    });
    tdX.appendChild(del);

    tr.append(tdG, tdA, tdX);
    tbody.appendChild(tr);
  }
}

function setupAddGesture() {
  $('#addGesture').addEventListener('click', async () => {
    const warn = $('#addWarn');
    warn.textContent = '';
    if (!draft) {
      warn.textContent = t('warnNoGesture', 'Draw or compose a gesture first.');
      return;
    }
    const existed = config.gestures[draft];
    config.gestures[draft] = $('#newAction').value;
    await persist();
    renderGestureTable();
    toast(existed
      ? t('replaced', 'Replaced') + ' ' + toArrows(draft)
      : t('added', 'Added') + ' ' + toArrows(draft));
    draft = '';
    $('#newGesture').textContent = '—';
  });
}

// ----------------------------------------------------------- direction maps

function renderDirTables() {
  for (const table of $$('table.dirs')) {
    const key = table.dataset.map;
    const modes = DRAG_MODES[key];
    const tbody = table.querySelector('tbody');
    tbody.textContent = '';

    for (const d of DIRS) {
      const tr = document.createElement('tr');
      const tdD = document.createElement('td');
      tdD.textContent = ARROW[d];

      const tdA = document.createElement('td');
      const sel = document.createElement('select');
      if (modes) fillModeSelect(sel, modes);
      else fillActionSelect(sel, true);
      sel.value = config[key][d];
      sel.addEventListener('change', async () => {
        config[key][d] = sel.value;
        await persist();
        toast(t('saved', 'Saved'));
      });
      tdA.appendChild(sel);

      tr.append(tdD, tdA);
      tbody.appendChild(tr);
    }
  }
}

// --------------------------------------------------------------- popup grid

/** Slot order is clockwise from north, matching the on-page wheel. */
const POPUP_LABELS = ['↑', '↗', '→', '↘', '↓', '↙', '←', '↖'];

function renderPopupGrid() {
  const grid = $('#popupGrid');
  grid.textContent = '';
  for (let i = 0; i < 8; i++) {
    const cell = document.createElement('div');
    cell.className = 'wheel-cell';

    const lab = document.createElement('span');
    lab.className = 'wheel-dir';
    lab.textContent = POPUP_LABELS[i];

    const sel = document.createElement('select');
    fillActionSelect(sel, true);
    sel.value = config.popupItems[i] || 'none';
    sel.addEventListener('change', async () => {
      config.popupItems[i] = sel.value === 'none' ? '' : sel.value;
      await persist();
      toast(t('saved', 'Saved'));
    });

    cell.append(lab, sel);
    grid.appendChild(cell);
  }
}

// -------------------------------------------------------------- context menu

function renderContextItems() {
  const wrap = $('#contextItems');
  wrap.textContent = '';
  config.contextMenuItems.forEach((id, i) => {
    const row = document.createElement('div');
    row.className = 'row';

    const sel = document.createElement('select');
    fillActionSelect(sel, false);
    sel.value = id;
    sel.addEventListener('change', async () => {
      config.contextMenuItems[i] = sel.value;
      await persist();
    });

    const del = document.createElement('button');
    del.className = 'del';
    del.textContent = '✕';
    del.addEventListener('click', async () => {
      config.contextMenuItems.splice(i, 1);
      await persist();
      renderContextItems();
    });

    row.append(sel, del);
    wrap.appendChild(row);
  });
}

// --------------------------------------------------------------- permissions

async function refreshPermissionToggles() {
  const has = async (p) => chrome.permissions.contains({ permissions: [p] });
  $('#permDownloads').checked = await has('downloads');
  $('#permBookmarks').checked = await has('bookmarks');
}

function bindPermission(id, name) {
  $(id).addEventListener('change', async (e) => {
    const want = e.target.checked;
    let ok;
    if (want) ok = await chrome.permissions.request({ permissions: [name] });
    else ok = await chrome.permissions.remove({ permissions: [name] });
    if (!ok) e.target.checked = !want;
    await refreshPermissionToggles();
  });
}

// ------------------------------------------------------------------ binding

function bindSimpleControls() {
  for (const id of BOOLS) {
    const el = $('#' + id);
    if (!el) continue;
    el.addEventListener('change', async () => {
      config[id] = el.checked;
      await persist();
    });
  }
  for (const id of NUMBERS) {
    const el = $('#' + id);
    if (!el) continue;
    el.addEventListener('change', async () => {
      const n = Number(el.value);
      if (Number.isFinite(n)) config[id] = n;
      await persist();
    });
  }
  for (const id of TEXTS) {
    const el = $('#' + id);
    if (!el) continue;
    el.addEventListener('change', async () => {
      config[id] = el.value;
      await persist();
    });
  }
  for (const id of ACTION_SELECTS) {
    const el = $('#' + id);
    if (!el) continue;
    el.addEventListener('change', async () => {
      config[id] = el.value;
      await persist();
    });
  }
  for (const slot of COMMAND_SLOTS) {
    const el = $('#' + slot);
    if (!el) continue;
    el.addEventListener('change', async () => {
      config.commandSlots[slot] = el.value;
      await persist();
    });
  }
  $('#excludes').addEventListener('change', async () => {
    config.excludes = $('#excludes').value
      .split('\n').map((s) => s.trim()).filter(Boolean);
    await persist();
  });
}

function fillFromConfig() {
  for (const id of BOOLS) {
    const el = $('#' + id);
    if (el) el.checked = !!config[id];
  }
  for (const id of NUMBERS) {
    const el = $('#' + id);
    if (el) el.value = config[id];
  }
  for (const id of TEXTS) {
    const el = $('#' + id);
    if (el) el.value = config[id];
  }
  for (const id of ACTION_SELECTS) {
    const el = $('#' + id);
    if (!el) continue;
    fillActionSelect(el, true);
    el.value = config[id];
  }
  for (const slot of COMMAND_SLOTS) {
    const el = $('#' + slot);
    if (!el) continue;
    fillActionSelect(el, true);
    el.value = config.commandSlots[slot] || 'none';
  }
  fillActionSelect($('#newAction'), false);
  $('#excludes').value = (config.excludes || []).join('\n');

  renderGestureTable();
  renderDirTables();
  renderPopupGrid();
  renderContextItems();
}

// ---------------------------------------------------------------- transfer

function setupTransfer() {
  $('#exportBtn').addEventListener('click', () => {
    const blob = new Blob([JSON.stringify(config, null, 2)],
      { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'local-gestures-settings.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  $('#importBtn').addEventListener('click', () => $('#importFile').click());

  $('#importFile').addEventListener('change', async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    try {
      const parsed = JSON.parse(await file.text());
      config = self.LG_withDefaults(parsed);
      await persist();
      fillFromConfig();
      toast(t('imported', 'Settings imported'));
    } catch (err) {
      toast(t('importFailed', 'Could not read that file'));
    }
    e.target.value = '';
  });

  $('#resetBtn').addEventListener('click', async () => {
    if (!window.confirm(t('confirmReset', 'Reset every setting to its default?'))) {
      return;
    }
    await chrome.storage.local.clear();
    config = self.LG_withDefaults(null);
    await persist();
    fillFromConfig();
    toast(t('resetDone', 'Reset to defaults'));
  });

  $('#addContextItem').addEventListener('click', async () => {
    config.contextMenuItems.push('copyUrl');
    await persist();
    renderContextItems();
  });

  $('#openShortcuts').addEventListener('click', () => {
    chrome.tabs.create({ url: 'chrome://extensions/shortcuts' });
  });
}

function setupTabs() {
  for (const tab of $$('#tabs .tab')) {
    tab.addEventListener('click', () => {
      $$('#tabs .tab').forEach((t2) => t2.classList.toggle('active', t2 === tab));
      $$('.panel').forEach((p) => {
        p.classList.toggle('active', p.id === tab.dataset.panel);
      });
    });
  }
}

// -------------------------------------------------------------------- start

(async function init() {
  applyI18n();
  config = await self.LG_loadConfig();
  setupTabs();
  setupPad();
  setupAddGesture();
  bindSimpleControls();
  setupTransfer();
  bindPermission('#permDownloads', 'downloads');
  bindPermission('#permBookmarks', 'bookmarks');
  fillFromConfig();
  await refreshPermissionToggles();
})();
