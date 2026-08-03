/**
 * Radial popup menu ("Popup Actions" in smartUp terms).
 *
 * Hold the gesture button still for `popupDelay` ms and eight action slots
 * fan out around the cursor. Move toward one and release to run it; release
 * near the centre to cancel.
 *
 * Lives in its own closed shadow root for the same reason the trail does:
 * page CSS must not be able to touch it.
 */
(function (root) {
  'use strict';

  const SLOTS = 8;
  const RADIUS = 96;          // px from centre to slot centre
  const DEAD_ZONE = 34;       // release inside this = cancel

  function LGPopupWheel() {
    this.host = null;
    this.shadow = null;
    this.nodes = [];
    this.cx = 0;
    this.cy = 0;
    this.active = false;
    this.index = -1;
    this.items = [];
  }

  LGPopupWheel.prototype.isOpen = function () {
    return this.active;
  };

  LGPopupWheel.prototype.open = function (items, x, y, labelFor) {
    this.close();
    const parent = document.documentElement || document.body;
    if (!parent) return;

    this.items = items.slice(0, SLOTS);
    this.cx = x;
    this.cy = y;

    const host = document.createElement('div');
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
      .slot {
        position: fixed;
        transform: translate(-50%, -50%);
        max-width: 128px;
        padding: 7px 11px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.14);
        background: rgba(20, 22, 26, 0.9);
        color: #e8eaed;
        font: 500 12px/1.3 system-ui, -apple-system, "Segoe UI", Roboto,
              "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei",
              sans-serif;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        transition: background 90ms linear, transform 90ms ease-out;
        pointer-events: none;
      }
      .slot.on {
        background: #2f81f7;
        border-color: #2f81f7;
        color: #fff;
        transform: translate(-50%, -50%) scale(1.08);
      }
      .slot.empty { opacity: 0.32; }
      .hub {
        position: fixed;
        width: 12px; height: 12px;
        margin: -6px 0 0 -6px;
        border-radius: 50%;
        background: rgba(255,255,255,0.55);
        box-shadow: 0 0 0 4px rgba(20,22,26,0.55);
        pointer-events: none;
      }
    `;
    shadow.appendChild(style);

    const hub = document.createElement('div');
    hub.className = 'hub';
    hub.style.left = x + 'px';
    hub.style.top = y + 'px';
    shadow.appendChild(hub);

    this.nodes = [];
    for (let i = 0; i < SLOTS; i++) {
      // Clockwise starting at north.
      const angle = (-90 + i * (360 / SLOTS)) * Math.PI / 180;
      const el = document.createElement('div');
      el.className = 'slot' + (this.items[i] ? '' : ' empty');
      el.textContent = this.items[i] ? labelFor(this.items[i]) : '·';
      el.style.left = (x + Math.cos(angle) * RADIUS) + 'px';
      el.style.top = (y + Math.sin(angle) * RADIUS) + 'px';
      shadow.appendChild(el);
      this.nodes.push(el);
    }

    parent.appendChild(host);
    this.host = host;
    this.shadow = shadow;
    this.active = true;
    this.index = -1;
  };

  /** @returns {number} slot index under the cursor, or -1 for the dead zone. */
  LGPopupWheel.prototype.track = function (x, y) {
    if (!this.active) return -1;
    const dx = x - this.cx;
    const dy = y - this.cy;
    const dist = Math.hypot(dx, dy);

    let idx = -1;
    if (dist >= DEAD_ZONE) {
      // Angle measured clockwise from north, matching the layout above.
      let deg = Math.atan2(dy, dx) * 180 / Math.PI + 90;
      if (deg < 0) deg += 360;
      idx = Math.round(deg / (360 / SLOTS)) % SLOTS;
      if (!this.items[idx]) idx = -1;
    }

    if (idx !== this.index) {
      this.nodes.forEach((el, i) => el.classList.toggle('on', i === idx));
      this.index = idx;
    }
    return idx;
  };

  /** @returns {string|null} the chosen action id. */
  LGPopupWheel.prototype.commit = function () {
    const id = this.index >= 0 ? this.items[this.index] : null;
    this.close();
    return id || null;
  };

  LGPopupWheel.prototype.close = function () {
    if (this.host && this.host.parentNode) {
      this.host.parentNode.removeChild(this.host);
    }
    this.host = null;
    this.shadow = null;
    this.nodes = [];
    this.active = false;
    this.index = -1;
  };

  LGPopupWheel.SLOTS = SLOTS;
  root.LGPopupWheel = LGPopupWheel;
})(typeof self !== 'undefined' ? self : globalThis);
