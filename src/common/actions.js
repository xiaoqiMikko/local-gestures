/**
 * Action catalogue.
 *
 * Loaded as a classic script in three places (content script, service worker
 * via importScripts, options page), so everything hangs off globalThis rather
 * than using ES module syntax.
 *
 * where:
 *   'page' - runs inside the frame that captured the gesture (DOM work)
 *   'bg'   - runs in the service worker (needs chrome.tabs / chrome.windows)
 * clip:
 *   true   - service worker returns a string, the page writes it to the
 *            clipboard (the worker has no DOM, so it cannot do it itself)
 * needs:
 *   optional permission required before the action can run
 */
(function (root) {
  'use strict';

  const ACTIONS = [
    // --- navigation -------------------------------------------------------
    { id: 'back', group: 'nav', where: 'bg' },
    { id: 'forward', group: 'nav', where: 'bg' },
    { id: 'reload', group: 'nav', where: 'bg' },
    { id: 'reloadHard', group: 'nav', where: 'bg' },
    { id: 'stop', group: 'nav', where: 'page' },
    { id: 'home', group: 'nav', where: 'bg' },
    { id: 'parentDir', group: 'nav', where: 'page' },
    { id: 'siteRoot', group: 'nav', where: 'page' },

    // --- tabs -------------------------------------------------------------
    { id: 'newTab', group: 'tab', where: 'bg' },
    { id: 'closeTab', group: 'tab', where: 'bg' },
    { id: 'reopenTab', group: 'tab', where: 'bg' },
    { id: 'duplicateTab', group: 'tab', where: 'bg' },
    { id: 'togglePin', group: 'tab', where: 'bg' },
    { id: 'toggleMute', group: 'tab', where: 'bg' },
    { id: 'prevTab', group: 'tab', where: 'bg' },
    { id: 'nextTab', group: 'tab', where: 'bg' },
    { id: 'firstTab', group: 'tab', where: 'bg' },
    { id: 'lastTab', group: 'tab', where: 'bg' },
    { id: 'lastUsedTab', group: 'tab', where: 'bg' },
    { id: 'closeOtherTabs', group: 'tab', where: 'bg', danger: true },
    { id: 'closeRightTabs', group: 'tab', where: 'bg', danger: true },
    { id: 'closeLeftTabs', group: 'tab', where: 'bg', danger: true },
    { id: 'moveTabLeft', group: 'tab', where: 'bg' },
    { id: 'moveTabRight', group: 'tab', where: 'bg' },
    { id: 'detachTab', group: 'tab', where: 'bg' },

    // --- windows ----------------------------------------------------------
    { id: 'newWindow', group: 'win', where: 'bg' },
    { id: 'newIncognito', group: 'win', where: 'bg' },
    { id: 'closeWindow', group: 'win', where: 'bg', danger: true },
    { id: 'minimizeWindow', group: 'win', where: 'bg' },
    { id: 'toggleMaximize', group: 'win', where: 'bg' },
    { id: 'toggleFullscreen', group: 'win', where: 'bg' },

    // --- scrolling --------------------------------------------------------
    { id: 'scrollTop', group: 'scroll', where: 'page' },
    { id: 'scrollBottom', group: 'scroll', where: 'page' },
    { id: 'scrollPageUp', group: 'scroll', where: 'page' },
    { id: 'scrollPageDown', group: 'scroll', where: 'page' },

    // --- zoom -------------------------------------------------------------
    { id: 'zoomIn', group: 'zoom', where: 'bg' },
    { id: 'zoomOut', group: 'zoom', where: 'bg' },
    { id: 'zoomReset', group: 'zoom', where: 'bg' },

    // --- page -------------------------------------------------------------
    { id: 'viewSource', group: 'page', where: 'bg' },
    { id: 'print', group: 'page', where: 'page' },
    { id: 'copyUrl', group: 'page', where: 'bg', clip: true },
    { id: 'copyTitle', group: 'page', where: 'bg', clip: true },
    { id: 'copyTitleUrl', group: 'page', where: 'bg', clip: true },
    { id: 'addBookmark', group: 'page', where: 'bg', needs: 'bookmarks' },
    { id: 'openOptions', group: 'page', where: 'bg' },

    // --- nothing ----------------------------------------------------------
    { id: 'none', group: 'misc', where: 'page' }
  ];

  const BY_ID = Object.create(null);
  for (const a of ACTIONS) BY_ID[a.id] = a;

  const GROUPS = ['nav', 'tab', 'win', 'scroll', 'zoom', 'page', 'misc'];

  root.LG_ACTIONS = ACTIONS;
  root.LG_ACTION_BY_ID = BY_ID;
  root.LG_ACTION_GROUPS = GROUPS;
})(typeof self !== 'undefined' ? self : globalThis);
