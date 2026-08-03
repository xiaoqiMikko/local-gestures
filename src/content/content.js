/**
 * Content script: captures input and asks the service worker to act.
 *
 * Input modes, each independently switchable:
 *   1. stroke gestures - hold the gesture button and draw
 *   2. popup wheel     - hold the gesture button still, pick from a radial menu
 *   3. rocker gestures - hold one button, click the other
 *   4. wheel gestures  - hold the gesture button and scroll
 *   5. super drag      - drag a link / image / selection, direction decides
 *   6. simple drag     - left-button straight drag on empty page area
 *   7. double click    - on empty page area
 *   8. touch gestures  - multi-finger stroke on touch screens
 *
 * This file performs no network access of any kind. See README for the
 * one-line grep that proves it across the whole repository.
 */
(function () {
  'use strict';

  const LGRecognizer = self.LGRecognizer;
  const LGOverlay = self.LGOverlay;
  const LGPopupWheel = self.LGPopupWheel;

  let config = null;
  let active = false;
  const overlay = new LGOverlay();
  const wheelMenu = new LGPopupWheel();
  const rec = new LGRecognizer(16);

  // --- stroke state -------------------------------------------------------
  let pressed = false;
  let moved = false;
  let popupTimer = null;
  let popupMode = false;

  // --- button bookkeeping -------------------------------------------------
  let leftDown = false;
  let rightDown = false;
  let rockerFired = false;
  let wheelFired = false;
  let suppressNextContext = false;
  let suppressNextClick = false;

  // --- simple drag --------------------------------------------------------
  let simpleDrag = null;

  // --- super drag ---------------------------------------------------------
  let dragInfo = null;
  let dragLastX = 0;
  let dragLastY = 0;

  // --- touch --------------------------------------------------------------
  let touching = false;

  // ------------------------------------------------------------------ utils

  function actionLabel(id) {
    if (!id || id === 'none') return '';
    return chrome.i18n.getMessage('action_' + id) || id;
  }

  function send(message) {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage(message, (res) => {
          // Touching lastError silences the "unchecked runtime.lastError"
          // console noise when the worker is asleep mid-navigation.
          void chrome.runtime.lastError;
          resolve(res || null);
        });
      } catch (e) {
        resolve(null);
      }
    });
  }

  async function writeClipboard(text) {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      return;
    } catch (e) { /* needs focus; fall through */ }
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.cssText = 'position:fixed;top:-1000px;opacity:0';
      (document.body || document.documentElement).appendChild(ta);
      ta.select();
      document.execCommand('copy');
      ta.remove();
    } catch (e) { /* never break the page over a copy */ }
  }

  /** Actions that run right here in the page. */
  function runPageAction(id) {
    const doc = document.scrollingElement || document.documentElement;
    switch (id) {
      case 'stop': window.stop(); return true;
      case 'scrollTop':
        window.scrollTo({ top: 0, behavior: 'smooth' }); return true;
      case 'scrollBottom':
        window.scrollTo({ top: doc.scrollHeight, behavior: 'smooth' }); return true;
      case 'scrollPageUp':
        window.scrollBy({ top: -window.innerHeight * 0.9, behavior: 'smooth' });
        return true;
      case 'scrollPageDown':
        window.scrollBy({ top: window.innerHeight * 0.9, behavior: 'smooth' });
        return true;
      case 'print': window.print(); return true;
      case 'parentDir': {
        const u = new URL(location.href);
        const parts = u.pathname.split('/').filter(Boolean);
        parts.pop();
        u.pathname = '/' + parts.join('/');
        u.search = '';
        u.hash = '';
        location.href = u.toString();
        return true;
      }
      case 'siteRoot': location.href = location.origin + '/'; return true;
      case 'none': return true;
      default: return false;
    }
  }

  /**
   * Surface a failed action instead of swallowing it.
   *
   * A silent no-op is indistinguishable from a broken extension, and the
   * most common cause — an optional permission that was never granted — is
   * something only the user can fix, so they have to be told where.
   */
  function report(error) {
    const s = String(error || '');
    let msg;
    if (s.indexOf('missing-permission:') === 0) {
      msg = chrome.i18n.getMessage('errMissingPermission');
    } else if (s === 'blocked-scheme') {
      msg = chrome.i18n.getMessage('errBlockedScheme');
    } else if (s === 'gone') {
      msg = chrome.i18n.getMessage('errTabGone');
    } else {
      msg = chrome.i18n.getMessage('errFailed');
    }
    LGOverlay.toast(msg);
  }

  async function execute(id) {
    if (!id || id === 'none') return;
    if (runPageAction(id)) return;
    const res = await send({ type: 'lg-exec', action: id });
    if (!res) return;                       // worker asleep mid-navigation
    if (res.clipboard) await writeClipboard(res.clipboard);
    if (res.error) report(res.error);
  }

  /** Dominant axis of a displacement, as a single U/D/L/R character. */
  function mainDirection(dx, dy) {
    return Math.abs(dx) >= Math.abs(dy)
      ? (dx > 0 ? 'R' : 'L')
      : (dy > 0 ? 'D' : 'U');
  }

  /** True when the point is plain page background, not text or a control. */
  function isEmptyArea(target) {
    if (!target || !target.closest) return false;
    if (target.closest('a,button,input,textarea,select,img,video,audio,' +
                       '[contenteditable],[role="button"],[role="link"]')) {
      return false;
    }
    const sel = window.getSelection && window.getSelection();
    if (sel && !sel.isCollapsed) return false;
    return true;
  }

  // -------------------------------------------------------------- gestures

  function beginGesture(e) {
    pressed = true;
    moved = false;
    popupMode = false;
    rec.minDistance = config.minDistance;
    rec.reset(e.clientX, e.clientY);
    overlay.begin(config, e.clientX, e.clientY);

    if (config.popupEnabled) {
      clearTimeout(popupTimer);
      popupTimer = setTimeout(() => {
        if (!pressed || moved) return;
        popupMode = true;
        overlay.end();
        wheelMenu.open(config.popupItems, e.clientX, e.clientY, actionLabel);
      }, config.popupDelay);
    }
  }

  function updateGesture(e) {
    if (popupMode) {
      wheelMenu.track(e.clientX, e.clientY);
      return;
    }
    overlay.addPoint(e.clientX, e.clientY);
    const changed = rec.push(e.clientX, e.clientY);
    if (!changed) return;
    moved = true;
    clearTimeout(popupTimer);      // real movement cancels the radial menu
    const dirs = rec.toString();
    overlay.setHint(LGOverlay.toArrows(dirs), actionLabel(config.gestures[dirs]));
  }

  /** @returns {boolean} true when something ran (so the menu must be eaten). */
  function endGesture() {
    clearTimeout(popupTimer);
    pressed = false;

    if (popupMode) {
      popupMode = false;
      const id = wheelMenu.commit();
      if (id) execute(id);
      return true;    // the wheel always swallows the menu, even on cancel
    }

    const dirs = rec.toString();
    const longEnough = rec.displacement() >= config.minStroke || dirs.length > 1;
    overlay.end();
    if (!moved || !dirs || !longEnough) return false;
    const id = config.gestures[dirs];
    if (id) execute(id);
    return true;
  }

  function cancelGesture() {
    clearTimeout(popupTimer);
    overlay.end();
    wheelMenu.close();
    pressed = false;
    moved = false;
    popupMode = false;
  }

  // ---------------------------------------------------------------- mouse

  function onMouseDown(e) {
    if (!active || !config) return;
    if (e.button === 0) leftDown = true;
    if (e.button === 2) rightDown = true;

    // Rocker first: it is a two-button chord, so it must win over treating
    // the second press as the start of anything else. A press can only set
    // its own flag, so `leftDown` here still means "left was already held".
    if (config.rockerEnabled) {
      const chord =
        (e.button === 2 && leftDown) ? config.rockerLeftRight :
        (e.button === 0 && rightDown) ? config.rockerRightLeft : null;

      if (chord !== null) {
        rockerFired = true;
        // Both pending releases must be swallowed: right would raise a
        // context menu, left would raise a click.
        suppressNextContext = true;
        suppressNextClick = true;
        cancelGesture();
        e.preventDefault();
        e.stopPropagation();
        execute(chord);
        return;
      }
    }

    if (config.gesturesEnabled && e.button === config.gestureButton) {
      beginGesture(e);
      return;
    }

    if (config.simpleDragEnabled && e.button === 0 && isEmptyArea(e.target)) {
      simpleDrag = { x: e.clientX, y: e.clientY, fired: false };
    }
  }

  function onMouseMove(e) {
    if (!active || !config) return;

    if (pressed) {
      updateGesture(e);
      return;
    }

    if (simpleDrag && !simpleDrag.fired) {
      const dx = e.clientX - simpleDrag.x;
      const dy = e.clientY - simpleDrag.y;
      if (Math.hypot(dx, dy) >= config.simpleDragDistance) {
        simpleDrag.fired = true;
        simpleDrag.dir = mainDirection(dx, dy);
      }
    }
  }

  function onMouseUp(e) {
    if (e.button === 0) leftDown = false;
    if (e.button === 2) rightDown = false;
    if (!active || !config) return;

    if (rockerFired) {
      if (!leftDown && !rightDown) rockerFired = false;
      return;
    }

    if (simpleDrag && e.button === 0) {
      const sd = simpleDrag;
      simpleDrag = null;
      if (sd.fired && sd.dir) {
        suppressNextClick = true;
        execute(config.simpleDrag[sd.dir]);
        return;
      }
    }

    if (pressed && e.button === config.gestureButton) {
      const fired = endGesture();
      // A wheel gesture always eats the menu: the user asked for a tab
      // switch, not a context menu, regardless of the stroke setting.
      if (wheelFired || (fired && config.suppressContextMenu)) {
        suppressNextContext = true;
      }
      wheelFired = false;
    }
  }

  function onContextMenu(e) {
    if (!active) return;
    if (suppressNextContext) {
      suppressNextContext = false;
      e.preventDefault();
      e.stopPropagation();
    }
  }

  function onClick(e) {
    if (!active) return;
    if (suppressNextClick) {
      suppressNextClick = false;
      e.preventDefault();
      e.stopPropagation();
    }
  }

  function onDblClick(e) {
    if (!active || !config || !config.doubleClickEnabled) return;
    if (!isEmptyArea(e.target)) return;
    e.preventDefault();
    execute(config.doubleClickAction);
  }

  function onWheel(e) {
    if (!active || !config || !config.wheelEnabled || !pressed) return;
    e.preventDefault();
    e.stopPropagation();
    wheelFired = true;
    moved = false;               // the wheel replaces the stroke
    clearTimeout(popupTimer);
    rec.reset(e.clientX, e.clientY);
    overlay.setHint('', '');
    execute(e.deltaY < 0 ? config.wheelUp : config.wheelDown);
  }

  function onBlur() {
    if (pressed || simpleDrag) cancelGesture();
    simpleDrag = null;
    leftDown = false;
    rightDown = false;
  }

  // ------------------------------------------------------------ super drag

  function classifyDragTarget(target) {
    if (!target || !target.closest) return null;
    const link = target.closest('a[href]');
    if (link && link.href) return { kind: 'link', value: link.href };
    if (target.tagName === 'IMG' && target.src) {
      return { kind: 'image', value: target.src };
    }
    const sel = String(window.getSelection ? window.getSelection() : '').trim();
    if (sel) return { kind: 'text', value: sel };
    return null;
  }

  function onDragStart(e) {
    if (!active || !config || !config.superDragEnabled) return;
    dragInfo = classifyDragTarget(e.target);
    if (!dragInfo) return;
    dragInfo.startX = e.clientX;
    dragInfo.startY = e.clientY;
    dragLastX = e.clientX;
    dragLastY = e.clientY;
  }

  function onDragOver(e) {
    if (!dragInfo) return;
    if (e.clientX || e.clientY) {
      dragLastX = e.clientX;
      dragLastY = e.clientY;
    }
  }

  async function onDragEnd(e) {
    if (!active || !config || !dragInfo) { dragInfo = null; return; }
    const info = dragInfo;
    dragInfo = null;

    const x = e.clientX || dragLastX;
    const y = e.clientY || dragLastY;
    const dx = x - info.startX;
    const dy = y - info.startY;
    if (Math.hypot(dx, dy) < config.superDragDistance) return;

    const table =
      info.kind === 'link' ? config.dragLink :
      info.kind === 'image' ? config.dragImage : config.dragText;

    const mode = table[mainDirection(dx, dy)];
    if (!mode || mode === 'none') return;
    if (mode === 'copy') { await writeClipboard(info.value); return; }

    const res = await send({
      type: 'lg-drag', mode: mode, value: info.value, kind: info.kind
    });
    if (res && res.error) report(res.error);
  }

  // ----------------------------------------------------------------- touch

  function onTouchStart(e) {
    if (!active || !config || !config.touchEnabled) return;
    if (e.touches.length !== config.touchFingers) { touching = false; return; }
    const t = e.touches[0];
    touching = true;
    moved = false;
    rec.minDistance = config.minDistance;
    rec.reset(t.clientX, t.clientY);
    overlay.begin(config, t.clientX, t.clientY);
  }

  function onTouchMove(e) {
    if (!touching) return;
    const t = e.touches[0];
    if (!t) return;
    e.preventDefault();
    overlay.addPoint(t.clientX, t.clientY);
    if (!rec.push(t.clientX, t.clientY)) return;
    moved = true;
    const dirs = rec.toString();
    overlay.setHint(LGOverlay.toArrows(dirs), actionLabel(config.gestures[dirs]));
  }

  function onTouchEnd() {
    if (!touching) return;
    touching = false;
    const dirs = rec.toString();
    const longEnough = rec.displacement() >= config.minStroke || dirs.length > 1;
    overlay.end();
    if (!moved || !dirs || !longEnough) return;
    const id = config.gestures[dirs];
    if (id) execute(id);
  }

  // ----------------------------------------------------------------- setup

  function applyConfig(cfg) {
    config = cfg;
    active = !!cfg.enabled && !self.LG_isExcluded(location.href, cfg.excludes);
    if (!active) cancelGesture();
  }

  function attach() {
    const cap = { capture: true };
    document.addEventListener('mousedown', onMouseDown, cap);
    document.addEventListener('mousemove', onMouseMove, cap);
    document.addEventListener('mouseup', onMouseUp, cap);
    document.addEventListener('contextmenu', onContextMenu, cap);
    document.addEventListener('click', onClick, cap);
    document.addEventListener('dblclick', onDblClick, cap);
    document.addEventListener('wheel', onWheel, { capture: true, passive: false });
    document.addEventListener('dragstart', onDragStart, cap);
    document.addEventListener('dragover', onDragOver, cap);
    document.addEventListener('dragend', onDragEnd, cap);
    document.addEventListener('touchstart', onTouchStart, { capture: true, passive: true });
    document.addEventListener('touchmove', onTouchMove, { capture: true, passive: false });
    document.addEventListener('touchend', onTouchEnd, cap);
    document.addEventListener('touchcancel', onTouchEnd, cap);
    window.addEventListener('blur', onBlur);
    window.addEventListener('resize', () => { if (pressed) cancelGesture(); });
  }

  self.LG_loadConfig().then((cfg) => {
    applyConfig(cfg);
    attach();
  });

  chrome.storage.onChanged.addListener((_changes, area) => {
    if (area !== 'local') return;
    self.LG_loadConfig().then(applyConfig);
  });

  // The worker has no DOM, so anything needing one — writing the clipboard,
  // showing a failure — is bounced back here by the context menu, keyboard
  // shortcut and toolbar icon paths.
  chrome.runtime.onMessage.addListener((msg) => {
    if (!msg || window.top !== window) return false;
    if (msg.type === 'lg-clipboard') writeClipboard(msg.value);
    else if (msg.type === 'lg-error') report(msg.value);
    return false;
  });
})();
