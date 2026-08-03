/**
 * Trail + hint overlay.
 *
 * Everything lives inside a shadow root so page CSS can never reach it and
 * our CSS can never leak into the page. The host element is created lazily,
 * on the first gesture, and removed as soon as the gesture ends.
 */
(function (root) {
  'use strict';

  const HOST_ID = 'local-gestures-overlay';
  const TOAST_ID = 'local-gestures-toast';

  function LGOverlay() {
    this.host = null;
    this.shadow = null;
    this.canvas = null;
    this.ctx = null;
    this.hint = null;
    this.dpr = 1;
    this.points = [];
  }

  LGOverlay.prototype._ensure = function () {
    if (this.host && this.host.isConnected) return true;
    const parent = document.documentElement || document.body;
    if (!parent) return false;

    const host = document.createElement('div');
    host.id = HOST_ID;
    // Inline styles on the host: the page cannot override these because we
    // also re-assert them via !important inside the shadow root.
    host.style.cssText = [
      'all: initial',
      'position: fixed',
      'inset: 0',
      'z-index: 2147483647',
      'pointer-events: none'
    ].join(';');

    const shadow = host.attachShadow({ mode: 'closed' });
    const style = document.createElement('style');
    style.textContent = `
      :host { pointer-events: none !important; }
      canvas { position: fixed; inset: 0; pointer-events: none; }
      .hint {
        position: fixed;
        left: 50%;
        transform: translateX(-50%);
        max-width: 80vw;
        padding: 8px 14px;
        border-radius: 8px;
        background: rgba(20, 22, 26, 0.88);
        color: #f2f4f8;
        font: 500 14px/1.4 system-ui, -apple-system, "Segoe UI", Roboto,
              "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei",
              sans-serif;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        pointer-events: none;
      }
      .hint.bottom { bottom: 48px; }
      .hint.top { top: 48px; }
      .hint .arrows {
        opacity: 0.72;
        margin-right: 8px;
        letter-spacing: 2px;
      }
      .hint.unknown { background: rgba(120, 30, 30, 0.88); }
    `;

    const canvas = document.createElement('canvas');
    const hint = document.createElement('div');
    hint.className = 'hint bottom';
    hint.style.display = 'none';

    shadow.append(style, canvas, hint);
    parent.appendChild(host);

    this.host = host;
    this.shadow = shadow;
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.hint = hint;
    this._resize();
    return true;
  };

  LGOverlay.prototype._resize = function () {
    if (!this.canvas) return;
    const dpr = window.devicePixelRatio || 1;
    this.dpr = dpr;
    this.canvas.width = Math.max(1, Math.round(window.innerWidth * dpr));
    this.canvas.height = Math.max(1, Math.round(window.innerHeight * dpr));
    this.canvas.style.width = window.innerWidth + 'px';
    this.canvas.style.height = window.innerHeight + 'px';
    if (this.ctx) this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  };

  LGOverlay.prototype.begin = function (config, x, y) {
    if (!config.trailEnabled && !config.hintEnabled) return;
    if (!this._ensure()) return;
    this._resize();
    this.points = [{ x: x, y: y }];
    this.config = config;
    if (this.ctx) {
      this.ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
      this.ctx.strokeStyle = config.trailColor || '#2f81f7';
      this.ctx.lineWidth = config.trailWidth || 3;
      this.ctx.lineCap = 'round';
      this.ctx.lineJoin = 'round';
    }
    if (this.hint) {
      this.hint.className = 'hint ' + (config.hintPosition === 'top' ? 'top' : 'bottom');
      this.hint.style.display = 'none';
    }
  };

  LGOverlay.prototype.addPoint = function (x, y) {
    if (!this.ctx || !this.config || !this.config.trailEnabled) return;
    const prev = this.points[this.points.length - 1];
    this.points.push({ x: x, y: y });
    if (!prev) return;
    this.ctx.beginPath();
    this.ctx.moveTo(prev.x, prev.y);
    this.ctx.lineTo(x, y);
    this.ctx.stroke();
  };

  /**
   * @param {string} arrows  human readable direction glyphs, e.g. "↓→"
   * @param {string} label   resolved action name, or '' when unmapped
   */
  LGOverlay.prototype.setHint = function (arrows, label) {
    if (!this.hint || !this.config || !this.config.hintEnabled) return;
    if (!arrows) {
      this.hint.style.display = 'none';
      return;
    }
    this.hint.textContent = '';
    const a = document.createElement('span');
    a.className = 'arrows';
    a.textContent = arrows;
    const t = document.createElement('span');
    t.textContent = label || chrome.i18n.getMessage('hintUnassigned') || '—';
    this.hint.append(a, t);
    this.hint.classList.toggle('unknown', !label);
    this.hint.style.display = '';
  };

  LGOverlay.prototype.end = function () {
    this.points = [];
    if (this.host && this.host.parentNode) this.host.parentNode.removeChild(this.host);
    this.host = null;
    this.shadow = null;
    this.canvas = null;
    this.ctx = null;
    this.hint = null;
  };

  const ARROW = { U: '↑', D: '↓', L: '←', R: '→' };
  LGOverlay.toArrows = function (dirs) {
    let out = '';
    for (const c of String(dirs)) out += ARROW[c] || c;
    return out;
  };

  /**
   * Transient message, independent of any gesture in progress.
   *
   * Exists because a silently failing action is indistinguishable from a
   * broken extension: if an action needs a permission that was never granted,
   * the user has to be told, and told where to fix it.
   */
  let toastHost = null;
  let toastTimer = null;

  LGOverlay.toast = function (text) {
    if (!text) return;
    const parent = document.documentElement || document.body;
    if (!parent) return;

    if (toastHost && toastHost.parentNode) toastHost.parentNode.removeChild(toastHost);
    clearTimeout(toastTimer);

    const host = document.createElement('div');
    host.id = TOAST_ID;
    host.style.cssText = [
      'all: initial',
      'position: fixed',
      'inset: auto 0 0 0',
      'z-index: 2147483647',
      'pointer-events: none'
    ].join(';');

    const shadow = host.attachShadow({ mode: 'closed' });
    const style = document.createElement('style');
    style.textContent = `
      .t {
        position: fixed;
        left: 50%;
        bottom: 90px;
        transform: translateX(-50%);
        max-width: 74vw;
        padding: 9px 16px;
        border-radius: 8px;
        background: rgba(150, 40, 34, 0.94);
        color: #fff;
        font: 500 13px/1.45 system-ui, -apple-system, "Segoe UI", Roboto,
              "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei",
              sans-serif;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
        pointer-events: none;
        animation: lgfade 220ms ease-out;
      }
      @keyframes lgfade {
        from { opacity: 0; transform: translateX(-50%) translateY(6px); }
        to   { opacity: 1; transform: translateX(-50%) translateY(0); }
      }
    `;
    const box = document.createElement('div');
    box.className = 't';
    box.textContent = text;

    shadow.append(style, box);
    parent.appendChild(host);
    toastHost = host;

    toastTimer = setTimeout(function () {
      if (host.parentNode) host.parentNode.removeChild(host);
      if (toastHost === host) toastHost = null;
    }, 2600);
  };

  root.LGOverlay = LGOverlay;
})(typeof self !== 'undefined' ? self : globalThis);
