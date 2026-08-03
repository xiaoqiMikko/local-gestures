/**
 * Turns a stream of pointer positions into a direction string like "DR".
 *
 * Four directions only (U/D/L/R). Diagonals are deliberately not supported:
 * they roughly double the number of strokes a user must draw accurately, and
 * every real-world gesture set worth copying sticks to four.
 */
(function (root) {
  'use strict';

  function LGRecognizer(minDistance) {
    this.minDistance = minDistance || 16;
    this.reset(0, 0);
  }

  LGRecognizer.prototype.reset = function (x, y) {
    this.lastX = x;
    this.lastY = y;
    this.startX = x;
    this.startY = y;
    this.travel = 0;
    this.dirs = [];
  };

  /**
   * Feed a new position.
   * @returns {boolean} true when a new direction was appended.
   */
  LGRecognizer.prototype.push = function (x, y) {
    const dx = x - this.lastX;
    const dy = y - this.lastY;
    const adx = Math.abs(dx);
    const ady = Math.abs(dy);

    if (adx < this.minDistance && ady < this.minDistance) return false;

    this.travel += Math.sqrt(dx * dx + dy * dy);
    this.lastX = x;
    this.lastY = y;

    // Dominant axis wins. Ties go to horizontal, which matters only for
    // perfectly diagonal movement and has to go somewhere.
    const dir = adx >= ady ? (dx > 0 ? 'R' : 'L') : (dy > 0 ? 'D' : 'U');

    if (this.dirs[this.dirs.length - 1] === dir) return false;
    this.dirs.push(dir);
    return true;
  };

  LGRecognizer.prototype.toString = function () {
    return this.dirs.join('');
  };

  /** Straight-line distance from where the gesture began. */
  LGRecognizer.prototype.displacement = function () {
    const dx = this.lastX - this.startX;
    const dy = this.lastY - this.startY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  root.LGRecognizer = LGRecognizer;
})(typeof self !== 'undefined' ? self : globalThis);
