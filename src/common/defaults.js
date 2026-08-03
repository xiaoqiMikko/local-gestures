/**
 * Default settings + storage helpers shared by every context.
 *
 * Everything lives in chrome.storage.local. Nothing is synced to a Google
 * account and nothing leaves the machine — see README.
 *
 * Feature coverage mirrors smartUp Gestures (archived 2024-03), which is the
 * yardstick users coming from Edge will measure this against:
 *   stroke / rocker / wheel / simple drag / super drag / popup wheel /
 *   double click / touch / toolbar icon / context menu / keyboard shortcuts.
 */
(function (root) {
  'use strict';

  const SCHEMA_VERSION = 2;

  /** Gesture strings are sequences of U/D/L/R, e.g. "DR" = down then right. */
  const DEFAULT_GESTURES = {
    L: 'back',
    R: 'forward',
    U: 'scrollTop',
    D: 'scrollBottom',
    UD: 'reload',
    DU: 'reopenTab',
    DR: 'closeTab',
    UR: 'newTab',
    LR: 'nextTab',
    RL: 'prevTab',
    DL: 'duplicateTab',
    UL: 'togglePin',
    RD: 'toggleMute',
    LU: 'zoomReset',
    RU: 'toggleFullscreen',
    LD: 'newWindow',
    RUL: 'closeOtherTabs',
    LDR: 'viewSource',
    UDU: 'reloadHard'
  };

  /** Drag targets resolve by direction, the way smartUp does it. */
  const DEFAULT_DRAG_LINK = {
    U: 'newTabFg', D: 'newTabBg', L: 'copy', R: 'newWindow'
  };
  const DEFAULT_DRAG_IMAGE = {
    U: 'newTabFg', D: 'newTabBg', L: 'copy', R: 'download'
  };
  const DEFAULT_DRAG_TEXT = {
    U: 'searchFg', D: 'searchBg', L: 'copy', R: 'searchBg'
  };

  /** Left-button straight drag on empty page area. Off by default: it
   *  competes with text selection, so it must be opt-in. */
  const DEFAULT_SIMPLE_DRAG = {
    U: 'scrollTop', D: 'scrollBottom', L: 'back', R: 'forward'
  };

  /** Eight slots, clockwise from north. '' leaves the slot empty. */
  const DEFAULT_POPUP = [
    'newTab', 'nextTab', 'forward', 'closeTab',
    'reopenTab', 'back', 'prevTab', 'reload'
  ];

  const DEFAULT_CONTEXT_ITEMS = ['copyTitleUrl', 'duplicateTab', 'viewSource'];

  const DEFAULTS = {
    schemaVersion: SCHEMA_VERSION,
    enabled: true,

    // --- stroke gestures --------------------------------------------------
    /** 2 = right button, 1 = middle button. */
    gestureButton: 2,
    gesturesEnabled: true,
    gestures: DEFAULT_GESTURES,
    /** Pixels of travel before a direction is committed. */
    minDistance: 16,
    /** A single stroke must beat this to register (filters jitter). */
    minStroke: 24,

    // --- rocker -----------------------------------------------------------
    rockerEnabled: true,
    rockerLeftRight: 'forward',
    rockerRightLeft: 'back',

    // --- wheel ------------------------------------------------------------
    wheelEnabled: true,
    wheelUp: 'prevTab',
    wheelDown: 'nextTab',

    // --- super drag (link / image / selected text) -------------------------
    superDragEnabled: true,
    superDragDistance: 45,
    dragLink: DEFAULT_DRAG_LINK,
    dragImage: DEFAULT_DRAG_IMAGE,
    dragText: DEFAULT_DRAG_TEXT,

    // --- simple drag (left button, empty area) ----------------------------
    simpleDragEnabled: false,
    simpleDragDistance: 60,
    simpleDrag: DEFAULT_SIMPLE_DRAG,

    // --- popup wheel ------------------------------------------------------
    popupEnabled: false,
    /** Hold the gesture button still this long to summon the wheel. */
    popupDelay: 350,
    popupItems: DEFAULT_POPUP,

    // --- double click -----------------------------------------------------
    doubleClickEnabled: false,
    doubleClickAction: 'closeTab',

    // --- touch ------------------------------------------------------------
    touchEnabled: false,
    touchFingers: 2,

    // --- toolbar icon -----------------------------------------------------
    iconAction: 'openOptions',

    // --- context menu -----------------------------------------------------
    contextMenuEnabled: false,
    contextMenuItems: DEFAULT_CONTEXT_ITEMS,

    // --- keyboard shortcuts ----------------------------------------------
    /** Keys match the command names declared in the manifest. The shortcut
     *  itself is owned by Chrome (chrome://extensions/shortcuts); we only
     *  decide what each slot does. */
    commandSlots: {
      slot1: 'reopenTab',
      slot2: 'duplicateTab',
      slot3: 'togglePin',
      slot4: 'copyTitleUrl'
    },

    // --- appearance -------------------------------------------------------
    trailEnabled: true,
    trailColor: '#2f81f7',
    trailWidth: 3,
    hintEnabled: true,
    hintPosition: 'bottom',

    suppressContextMenu: true,

    /** Glob-ish patterns; matching pages get no handling at all. */
    excludes: [],
    /** Empty means "open a new tab". */
    homeUrl: ''
  };

  /** Keys whose value is a {U,D,L,R} map — merged, not replaced, on load. */
  const DIR_MAPS = ['dragLink', 'dragImage', 'dragText', 'simpleDrag'];

  function clone(obj) {
    return JSON.parse(JSON.stringify(obj));
  }

  /** Fill in whatever an older or partial stored config is missing. */
  function withDefaults(stored) {
    const out = clone(DEFAULTS);
    if (!stored || typeof stored !== 'object') return out;

    for (const key of Object.keys(DEFAULTS)) {
      if (stored[key] === undefined) continue;
      if (key === 'gestures') {
        out.gestures = Object.assign({}, stored.gestures);
      } else if (DIR_MAPS.includes(key) || key === 'commandSlots') {
        out[key] = Object.assign({}, DEFAULTS[key], stored[key]);
      } else if (key === 'popupItems') {
        const src = Array.isArray(stored.popupItems) ? stored.popupItems : [];
        out.popupItems = DEFAULT_POPUP.map((d, i) =>
          src[i] === undefined ? d : src[i]);
      } else {
        out[key] = stored[key];
      }
    }
    out.schemaVersion = SCHEMA_VERSION;
    return out;
  }

  /**
   * Small pattern matcher for the exclude list.
   * '*' is a wildcard; everything else is literal.
   */
  function isExcluded(url, patterns) {
    if (!url || !patterns || !patterns.length) return false;
    for (const raw of patterns) {
      const p = String(raw).trim();
      if (!p) continue;
      const rx = new RegExp(
        '^' + p.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*') + '$',
        'i'
      );
      if (rx.test(url)) return true;
    }
    return false;
  }

  function load() {
    return new Promise((resolve) => {
      chrome.storage.local.get(null, (stored) => resolve(withDefaults(stored)));
    });
  }

  function save(config) {
    return new Promise((resolve) => {
      chrome.storage.local.set(withDefaults(config), resolve);
    });
  }

  root.LG_DEFAULTS = DEFAULTS;
  root.LG_SCHEMA_VERSION = SCHEMA_VERSION;
  root.LG_DIR_MAPS = DIR_MAPS;
  root.LG_withDefaults = withDefaults;
  root.LG_isExcluded = isExcluded;
  root.LG_loadConfig = load;
  root.LG_saveConfig = save;
  root.LG_clone = clone;
})(typeof self !== 'undefined' ? self : globalThis);
