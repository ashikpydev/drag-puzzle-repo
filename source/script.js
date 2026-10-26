/* Drag puzzle field plug-in, v1.0.0
 *
 * A select_one field shown as a drag-and-drop puzzle for young children.
 *   - The picture with the missing piece comes from the question image (media:image column).
 *   - Each choice is one piece; its image comes from the choice image column.
 *   - The child drags a piece into the gap. The stored answer is the VALUE of the choice dropped,
 *     whether it is the right piece or a wrong one.
 *   - Optional log (attempts, order, time) is saved as plug-in metadata and can be read in the form
 *     with plug-in-metadata(${field_name}).
 *
 * Parameters (all optional except the gap position), for example:
 *   custom-drag-puzzle(gap_x=44, gap_y=29, gap_w=22, correct=1)
 * See README.md for the full list.
 */
(function () {
  'use strict';

  /* ---------- Helpers ---------- */

  function param(name, def) {
    try {
      var v = getPluginParameter(name);
      return (v === undefined || v === null || v === '') ? def : v;
    } catch (e) {
      return def;
    }
  }
  function num(v, d) { var n = parseFloat(v); return isNaN(n) ? d : n; }
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;'); }
  function secs(ms) { return (Math.round(ms / 100) / 10).toFixed(1); }
  function shuffled(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  /* ---------- Page elements ---------- */

  var root = document.getElementById('dp-root');
  var stage = document.getElementById('dp-stage');
  var game = document.getElementById('dp-game');
  var deco = document.getElementById('dp-deco');
  var speaker = document.getElementById('dp-speaker');
  var audioEl = document.getElementById('dp-audio');
  var problemEl = document.getElementById('dp-problem');
  var gear = document.getElementById('dp-gear');
  var panel = document.getElementById('dp-panel');
  var statusEl = document.getElementById('dp-status');
  var btnCannot = document.getElementById('dp-cannot');
  var btnRefuse = document.getElementById('dp-refuse');
  var btnRestart = document.getElementById('dp-restart');

  var FP = (typeof fieldProperties !== 'undefined') ? fieldProperties : {};
  var readOnly = !!FP.READONLY;

  var problems = [];
  function problem(msg) {
    if (problems.indexOf(msg) !== -1) { return; }
    problems.push(msg);
    problemEl.hidden = false;
    problemEl.textContent = 'Puzzle setup problem: ' + problems.join(' | ');
    try { console.error('drag-puzzle: ' + msg); } catch (e) { /* ignore */ }
  }

  /* ---------- Parameters ---------- */

  var practice = String(param('practice', '0')) === '1';
  var tries = clamp(parseInt(param('tries', practice ? 9 : 1), 10) || 1, 1, 9);
  var record = String(param('record', 'first')).toLowerCase() === 'last' ? 'last' : 'first';
  var reveal = String(param('reveal', practice ? '1' : '0')) === '1';
  var hintSec = Math.max(0, num(param('hint', practice ? 8 : 0), 0));
  var demoOn = String(param('demo', practice ? '1' : '0')) === '1';
  var theme = String(param('theme', 'sky')).toLowerCase();
  var soundOn = String(param('sound', '1')) !== '0';
  var volume = clamp(num(param('volume', 0.7), 0.7), 0, 1);
  var confettiOn = String(param('confetti', '1')) !== '0';
  var doShuffle = String(param('shuffle', '1')) !== '0';
  var maxWidth = Math.max(240, num(param('max_width', 720), 720));
  var codeCannot = String(param('code_cannot', '96'));
  var codeRefuse = String(param('code_refuse', '97'));

  if (['sky', 'forest', 'ocean', 'candy', 'sunny'].indexOf(theme) === -1) { problem('unknown theme "' + theme + '", using sky.'); theme = 'sky'; }
  root.className = 'dp-theme-' + theme;

  /* ---------- Model: pieces from the choice list ---------- */

  var pieces = [];
  (FP.CHOICES || []).forEach(function (c) {
    var v = String(c.CHOICE_VALUE);
    if (v === codeCannot || v === codeRefuse) { return; }   // special codes are not pieces
    if (!c.CHOICE_IMAGE) { problem('choice "' + v + '" has no image (fill the image column of the choices sheet).'); return; }
    pieces.push({ id: v, label: String(c.CHOICE_LABEL || ''), img: c.CHOICE_IMAGE });
  });
  if (pieces.length < 2) { problem('the choice list needs at least 2 pieces with images.'); }

  var correctId = String(param('correct', ''));
  if (correctId === '') {
    correctId = pieces.some(function (p) { return p.id === '1'; }) ? '1' : (pieces[0] ? pieces[0].id : '');
  }
  if (!pieces.some(function (p) { return p.id === correctId; })) {
    problem('correct=' + correctId + ' is not one of the piece choice values.');
    correctId = pieces[0] ? pieces[0].id : '';
  }

  var sceneSrc = FP.MEDIAIMAGE || '';
  if (!sceneSrc) { problem('the question needs the picture in its media:image column.'); }

  function pieceById(id) {
    for (var i = 0; i < pieces.length; i++) { if (pieces[i].id === id) { return pieces[i]; } }
    return null;
  }

  /* ---------- State ---------- */

  var gap = { x: 40, y: 40, w: 22, h: 22 };   // percent of the picture
  var aspect = 1;                              // picture height / width
  var t0 = Date.now();
  var tFirst = null, moves = 0, attempts = 0, seq = [];
  var stored = '';                             // the value saved as the answer
  var finished = false, finalStatus = '', specialCode = '';
  var order = [], els = {}, slots = {};
  var W = 0, H = 0, pw = 0, ph = 0;
  var drag = null;
  var sceneEl = null, gapEl = null;
  var idleTimer = null, demoNodes = [], demoAnims = [];

  /* ---------- Sounds (synthesised, no audio files needed) ---------- */

  var Sound = {
    ctx: null,
    unlock: function () {
      if (!soundOn) { return; }
      try {
        if (!this.ctx) {
          var AC = window.AudioContext || window.webkitAudioContext;
          if (AC) { this.ctx = new AC(); }
        }
        if (this.ctx && this.ctx.state === 'suspended') { this.ctx.resume(); }
      } catch (e) { /* sound is optional */ }
    },
    tone: function (f, at, dur, type, vol) {
      if (!soundOn || !this.ctx) { return; }
      try {
        var c = this.ctx, o = c.createOscillator(), g = c.createGain(), t = c.currentTime + at;
        o.type = type || 'sine';
        o.frequency.setValueAtTime(f, t);
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(Math.max(0.0002, (vol || 0.3) * volume), t + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
        o.connect(g); g.connect(c.destination);
        o.start(t); o.stop(t + dur + 0.05);
      } catch (e) { /* ignore */ }
    },
    pickup: function () { this.tone(520, 0, 0.09, 'sine', 0.25); this.tone(780, 0.05, 0.09, 'sine', 0.22); },
    tick: function () { this.tone(330, 0, 0.07, 'triangle', 0.18); },
    near: function () { this.tone(900, 0, 0.05, 'sine', 0.1); },
    win: function () {
      var self = this;
      [523.25, 659.25, 783.99, 1046.5].forEach(function (f, i) { self.tone(f, i * 0.11, 0.3, 'triangle', 0.3); });
      this.tone(1568, 0.46, 0.25, 'sine', 0.14);
      this.tone(2093, 0.56, 0.3, 'sine', 0.1);
    },
    wrong: function () { this.tone(392, 0, 0.18, 'triangle', 0.22); this.tone(311, 0.16, 0.3, 'triangle', 0.22); },
    end: function () { this.tone(440, 0, 0.2, 'sine', 0.2); this.tone(523.25, 0.16, 0.34, 'sine', 0.2); }
  };

  /* ---------- Build ---------- */

  function buildDeco() {
    deco.innerHTML = '';
    for (var i = 0; i < 8; i++) {
      var s = document.createElement('span');
      var size = 14 + Math.round(Math.random() * 34);
      s.style.width = size + 'px';
      s.style.height = size + 'px';
      s.style.left = Math.round(Math.random() * 96) + '%';
      s.style.animationDuration = (9 + Math.random() * 10).toFixed(1) + 's';
      s.style.animationDelay = (-Math.random() * 14).toFixed(1) + 's';
      s.style.setProperty('--dx', Math.round(-40 + Math.random() * 80) + 'px');
      deco.appendChild(s);
    }
  }

  function build() {
    order = doShuffle ? shuffled(pieces) : pieces.slice();
    els = {};
    game.innerHTML = '';
    sceneEl = document.createElement('div');
    sceneEl.className = 'dp-scene';
    sceneEl.id = 'dp-scene';
    sceneEl.innerHTML = '<img src="' + esc(sceneSrc) + '" alt="" draggable="false" class="dp-simg">';
    gapEl = document.createElement('div');
    gapEl.className = 'dp-gap';
    gapEl.style.left = gap.x + '%';
    gapEl.style.top = gap.y + '%';
    gapEl.style.width = gap.w + '%';
    gapEl.style.height = gap.h + '%';
    sceneEl.appendChild(gapEl);
    game.appendChild(sceneEl);
    var si = sceneEl.querySelector('img');
    si.addEventListener('error', function () { problem('image not found: ' + sceneSrc + ' (attach it to the form).'); });

    order.forEach(function (p, i) {
      var el = document.createElement('div');
      el.className = 'dp-piece';
      el.setAttribute('data-id', p.id);
      el.style.setProperty('--delay', (250 + i * 90) + 'ms');
      var inner = document.createElement('div');
      inner.className = 'dp-inner';
      inner.style.setProperty('--bobdelay', (i * 380) + 'ms');
      inner.innerHTML = '<img src="' + esc(p.img) + '" alt="" draggable="false" class="dp-pimg">';
      el.appendChild(inner);
      inner.querySelector('img').addEventListener('error', function () {
        problem('image not found: ' + p.img + ' (attach it to the form).');
      });
      el.addEventListener('animationend', function (e) {
        if (e.animationName === 'dp-enter') { el.classList.add('dp-entered'); }
      });
      el.addEventListener('pointerdown', onDown);
      el.addEventListener('pointermove', onMove);
      el.addEventListener('pointerup', onUp);
      el.addEventListener('pointercancel', onUp);
      game.appendChild(el);
      els[p.id] = el;
    });
  }

  /* Tablet-first layout. Landscape: picture on the left, pieces in a column on the right.
     Portrait: picture on top, pieces in a row below. The picture is made as large as the screen allows,
     so the whole puzzle is visible without scrolling. */
  var gameW = 0, gameH = 0, mode = 'stacked';

  function sizesFor(sceneW) {
    var sH = sceneW * aspect;
    return { sw: sceneW, sh: sH, pw: gap.w / 100 * sceneW, ph: gap.h / 100 * sH };
  }

  function fitStacked(availW, availH) {
    var n = order.length, sp = 12;
    for (var w = Math.min(availW, maxWidth); w >= 240; w -= 8) {
      var z = sizesFor(w), perRow, rows;
      if (n * z.pw + (n + 1) * 4 <= w) { perRow = n; sp = Math.min(12, (w - n * z.pw) / (n + 1)); }
      else { sp = 12; perRow = Math.max(1, Math.floor((w - sp) / (z.pw + sp))); }
      rows = Math.ceil(n / perRow);
      var h = z.sh + 16 + rows * (z.ph + sp) + 6;
      if (h <= availH || w - 8 < 240) {
        return { mode: 'stacked', z: z, sp: sp, perRow: perRow, rows: rows, gameW: w, gameH: h };
      }
    }
    return null;
  }

  function fitSide(availW, availH) {
    var n = order.length, sp = 12, gutter = 16;
    for (var w = Math.min(availW - 120, maxWidth); w >= 240; w -= 8) {
      var z = sizesFor(w);
      if (z.sh > availH && w - 8 >= 240) { continue; }
      var cols = Math.max(1, Math.ceil(n * (z.ph + sp) / Math.max(z.sh, z.ph + sp)));
      var trayW = cols * (z.pw + sp) + sp;
      var rowsPerCol = Math.ceil(n / cols);
      var trayH = rowsPerCol * (z.ph + sp) + sp;
      var total = w + gutter + trayW;
      var h = Math.max(z.sh, trayH);
      if ((total <= availW && h <= availH) || w - 8 < 240) {
        return { mode: 'side', z: z, sp: sp, cols: cols, rowsPerCol: rowsPerCol, trayW: trayW, gutter: gutter, gameW: total, gameH: h };
      }
    }
    return null;
  }

  function layout() {
    var pad = 28;
    var availW = (root.clientWidth || 360) - pad;
    var top = stage.getBoundingClientRect().top + (window.pageYOffset || 0);
    var vh = window.innerHeight || 800;
    var availH = Math.max(300, vh - Math.min(top, vh * 0.3) - 96);
    var want = String(param('layout', 'auto')).toLowerCase();
    var a = fitStacked(availW, availH);
    var b = fitSide(availW, availH);
    var pick = a;
    if (want === 'side' && b) { pick = b; }
    else if (want !== 'stacked' && b && a && b.z.sw > a.z.sw * 1.08) { pick = b; }
    var L = pick || a || b;
    mode = L.mode;
    W = L.z.sw; H = L.z.sh; pw = L.z.pw; ph = L.z.ph;
    gameW = L.gameW; gameH = L.gameH;
    game.classList.toggle('dp-side', mode === 'side');
    stage.style.width = (gameW + pad) + 'px';
    game.style.width = gameW + 'px';
    game.style.height = gameH + 'px';
    sceneEl.style.width = W + 'px';
    sceneEl.style.height = H + 'px';
    var n = order.length;
    order.forEach(function (p, i) {
      var pos;
      if (mode === 'side') {
        var col = Math.floor(i / L.rowsPerCol), row = i % L.rowsPerCol;
        var inCol = Math.min(L.rowsPerCol, n - col * L.rowsPerCol);
        var colH = inCol * (ph + L.sp) - L.sp;
        pos = { left: W + L.gutter + L.sp + col * (pw + L.sp), top: Math.max(L.sp, (gameH - colH) / 2) + row * (ph + L.sp) };
      } else {
        var r = Math.floor(i / L.perRow), c = i % L.perRow;
        var inRow = Math.min(L.perRow, n - r * L.perRow);
        var startX = (gameW - (inRow * pw + (inRow - 1) * L.sp)) / 2;
        pos = { left: startX + c * (pw + L.sp), top: H + 16 + r * (ph + L.sp) };
      }
      slots[p.id] = pos;
      var el = els[p.id];
      el.style.width = pw + 'px';
      el.style.height = ph + 'px';
      if (!drag || drag.id !== p.id) { place(p.id); }
    });
  }

  function gapPos() { return { left: gap.x / 100 * W, top: gap.y / 100 * H }; }

  function place(id) {
    var el = els[id];
    var pos = el.classList.contains('dp-placed') ? gapPos() : slots[id];
    el.style.left = pos.left + 'px';
    el.style.top = pos.top + 'px';
  }

  /* ---------- Interaction ---------- */

  function canPlay() { return !finished && !readOnly; }

  function onDown(e) {
    if (!canPlay() || drag) { return; }
    e.preventDefault();
    Sound.unlock();
    stopDemo();
    var el = e.currentTarget;
    el.classList.add('dp-entered');
    var er = el.getBoundingClientRect();
    drag = { id: el.getAttribute('data-id'), el: el, pid: e.pointerId, offX: e.clientX - er.left, offY: e.clientY - er.top, near: false };
    if (tFirst === null) { tFirst = Date.now() - t0; }
    moves++;
    try { el.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
    el.classList.add('dp-drag');
    Sound.pickup();
  }

  function nearGap(left, top, factor) {
    var g = gapPos();
    var d = Math.sqrt(Math.pow(left - g.left, 2) + Math.pow(top - g.top, 2));
    return d < Math.max(pw, ph) * factor;
  }

  function onMove(e) {
    if (!drag || e.pointerId !== drag.pid) { return; }
    e.preventDefault();
    var gr = game.getBoundingClientRect();
    var left = e.clientX - gr.left - drag.offX;
    var top = e.clientY - gr.top - drag.offY;
    left = clamp(left, -pw * 0.2, gameW - pw * 0.8);
    top = clamp(top, -ph * 0.2, gameH - ph * 0.8);
    drag.el.style.left = left + 'px';
    drag.el.style.top = top + 'px';
    var n = nearGap(left, top, 0.9);
    if (n !== drag.near) {
      drag.near = n;
      gapEl.classList.toggle('dp-near', n);
      if (n) { Sound.near(); }
    }
  }

  function onUp(e) {
    if (!drag || e.pointerId !== drag.pid) { return; }
    var el = drag.el, id = drag.id;
    el.classList.remove('dp-drag');
    gapEl.classList.remove('dp-near');
    try { el.releasePointerCapture(e.pointerId); } catch (err) { /* ignore */ }
    drag = null;
    var left = parseFloat(el.style.left), top = parseFloat(el.style.top);
    if (e.type !== 'pointercancel' && nearGap(left, top, 0.6)) {
      attempt(id);
    } else {
      place(id);
      Sound.tick();
      resetIdle();
    }
  }

  function attempt(id) {
    attempts++;
    seq.push(id);
    if (record === 'last' || stored === '') { stored = id; }
    setAnswer(stored);
    var right = (id === correctId);
    if (right) {
      els[id].classList.add('dp-placed', 'dp-right');
      place(id);
      finish('correct');
      return;
    }
    var el = els[id];
    place(id);
    el.classList.add('dp-shake');
    setTimeout(function () { el.classList.remove('dp-shake'); }, 450);
    Sound.wrong();
    saveMeta('open');
    if (attempts >= tries) {
      if (reveal && els[correctId]) {
        els[correctId].classList.add('dp-placed', 'dp-right');
        place(correctId);
        gapEl.classList.add('dp-off');
      }
      finish('incorrect');
    } else {
      resetIdle();
    }
  }

  /* ---------- Saving ---------- */

  function buildLog(status) {
    return 'v=1;status=' + status +
      ';answer=' + stored +
      ';correct=' + correctId +
      ';attempts=' + attempts +
      ';seq=' + seq.join(',') +
      ';moves=' + moves +
      ';t_first=' + (tFirst === null ? '' : secs(tFirst)) +
      ';t_done=' + secs(Date.now() - t0) +
      ';order=' + order.map(function (p) { return p.id; }).join(',');
  }

  function saveMeta(status) {
    try { if (typeof setMetaData === 'function') { setMetaData(buildLog(status)); } } catch (e) { /* ignore */ }
  }

  function lockAll() {
    Object.keys(els).forEach(function (id) { els[id].classList.add('dp-locked'); });
  }

  function fadeOthers(delay) {
    setTimeout(function () {
      Object.keys(els).forEach(function (id) {
        if (!els[id].classList.contains('dp-placed')) { els[id].classList.add('dp-fade'); }
      });
    }, delay);
  }

  function finish(status) {
    finished = true;
    finalStatus = status;
    lockAll();
    stopDemo();
    saveMeta(status);
    if (status === 'correct') {
      gapEl.classList.add('dp-off');
      celebrate();
    } else {
      Sound.end();
      fadeOthers(900);
    }
    updateStatus();
  }

  function celebrate() {
    Sound.win();
    sceneEl.classList.add('dp-win');
    var star = document.createElement('div');
    star.className = 'dp-star';
    star.innerHTML = '<svg viewBox="0 0 100 100"><polygon points="50,5 61,38 96,38 67,58 78,92 50,71 22,92 33,58 4,38 39,38" fill="#FFD84D" stroke="#F2A900" stroke-width="5" stroke-linejoin="round"/></svg>';
    game.appendChild(star);
    setTimeout(function () { if (star.parentNode) { star.parentNode.removeChild(star); } }, 1200);
    var g = gapPos();
    burst(g.left + pw / 2, g.top + ph / 2);
    fadeOthers(1100);
  }

  function burst(cx, cy) {
    if (!confettiOn || !game.animate) { return; }
    var colors = ['#FF5252', '#FFD740', '#69F0AE', '#40C4FF', '#E040FB', '#FF9100'];
    for (var i = 0; i < 26; i++) {
      var d = document.createElement('div');
      d.className = 'dp-confetti';
      d.style.left = cx + 'px';
      d.style.top = cy + 'px';
      d.style.background = colors[i % colors.length];
      game.appendChild(d);
      var ang = Math.random() * Math.PI * 2, dist = 70 + Math.random() * 120;
      var dx = Math.cos(ang) * dist, dy = Math.sin(ang) * dist - 50, rot = Math.round(-360 + Math.random() * 720);
      var a = d.animate([
        { transform: 'translate(0,0) rotate(0deg)', opacity: 1 },
        { transform: 'translate(' + dx + 'px,' + dy + 'px) rotate(' + rot + 'deg)', opacity: 1, offset: 0.6 },
        { transform: 'translate(' + (dx * 1.05) + 'px,' + (dy + 110) + 'px) rotate(' + (rot * 1.5) + 'deg)', opacity: 0 }
      ], { duration: 900 + Math.random() * 600, easing: 'cubic-bezier(.2,.7,.3,1)' });
      (function (node) {
        a.onfinish = function () { if (node.parentNode) { node.parentNode.removeChild(node); } };
        setTimeout(function () { if (node.parentNode) { node.parentNode.removeChild(node); } }, 2200);
      })(d);
    }
  }

  /* ---------- Hint hand / demo ---------- */

  function stopDemo() {
    clearTimeout(idleTimer);
    demoAnims.forEach(function (a) { try { a.cancel(); } catch (e) { /* ignore */ } });
    demoAnims = [];
    demoNodes.forEach(function (n) { if (n.parentNode) { n.parentNode.removeChild(n); } });
    demoNodes = [];
  }

  function resetIdle() {
    clearTimeout(idleTimer);
    if (hintSec > 0 && !finished && !readOnly) {
      idleTimer = setTimeout(runDemo, hintSec * 1000);
    }
  }

  function runDemo() {
    if (finished || readOnly || drag || !game.animate || !els[correctId]) { return; }
    var s = slots[correctId], g = gapPos();
    var ghost = document.createElement('div');
    ghost.className = 'dp-ghost';
    ghost.style.left = s.left + 'px';
    ghost.style.top = s.top + 'px';
    ghost.style.width = pw + 'px';
    ghost.style.height = ph + 'px';
    ghost.style.border = '3px solid #2b2b2b';
    ghost.style.borderRadius = '8px';
    ghost.style.boxSizing = 'border-box';
    ghost.style.overflow = 'hidden';
    ghost.innerHTML = '<img src="' + esc(pieceById(correctId).img) + '" alt="" style="display:block;width:100%;height:100%;object-fit:fill">';
    var hand = document.createElement('div');
    hand.className = 'dp-hand';
    hand.style.left = (s.left + pw * 0.45) + 'px';
    hand.style.top = (s.top + ph * 0.5) + 'px';
    hand.innerHTML = '<svg viewBox="0 0 48 48"><path d="M20 6c-2 0-3.500 1.600-3.500 3.500V25l-3-3c-1.400-1.400-3.600-1.400-4.900 0-1.200 1.200-1.300 3.100-.2 4.400l9.400 12.200c1.600 2 3.900 3.100 6.400 3.100h5.800c4.400 0 8-3.600 8-8V22c0-1.700-1.300-3-3-3s-3 1.300-3 3v-3c0-1.700-1.300-3-3-3s-3 1.300-3 3v-2c0-1.700-1.300-3-3-3-.9 0-1.700.4-2.300 1V9.500C23.500 7.600 22 6 20 6z" fill="#fff" stroke="#333" stroke-width="2" stroke-linejoin="round"/></svg>';
    game.appendChild(ghost);
    game.appendChild(hand);
    demoNodes.push(ghost, hand);
    var dx = g.left - s.left, dy = g.top - s.top;
    var kf = [
      { transform: 'translate(0,0) scale(1)', opacity: 0 },
      { transform: 'translate(0,0) scale(1)', opacity: 1, offset: 0.1 },
      { transform: 'translate(0,0) scale(1.12)', opacity: 1, offset: 0.2 },
      { transform: 'translate(' + dx + 'px,' + dy + 'px) scale(1.12)', opacity: 1, offset: 0.72 },
      { transform: 'translate(' + dx + 'px,' + dy + 'px) scale(1)', opacity: 1, offset: 0.85 },
      { transform: 'translate(' + dx + 'px,' + dy + 'px) scale(1)', opacity: 0 }
    ];
    var opt = { duration: 2800, easing: 'ease-in-out' };
    var a1 = ghost.animate(kf, opt);
    var a2 = hand.animate(kf, opt);
    demoAnims.push(a1, a2);
    a1.onfinish = function () {
      stopDemo();
      resetIdle();
    };
  }

  /* ---------- Enumerator panel ---------- */

  function updateStatus() {
    var txt;
    if (specialCode) {
      txt = 'Saved special code ' + specialCode + '.';
    } else if (stored !== '') {
      var p = pieceById(stored);
      txt = 'Stored answer: ' + stored + (p && p.label ? ' (' + p.label + ')' : '') + '. ' +
        (finished ? 'Result: ' + finalStatus + '. ' : 'Still playing. ') + 'Attempts: ' + attempts + ', moves: ' + moves + '.';
    } else {
      txt = 'Waiting for the child. Correct piece value: ' + correctId + '. Tries allowed: ' + tries + '.';
    }
    statusEl.textContent = txt;
    var answered = (stored !== '' || specialCode !== '');
    btnCannot.disabled = answered || readOnly;
    btnRefuse.disabled = answered || readOnly;
    btnRestart.style.display = (practice && !readOnly) ? 'block' : 'none';
  }

  function setSpecial(code) {
    if (readOnly || finished || stored !== '') { return; }
    specialCode = code;
    finished = true;
    stopDemo();
    lockAll();
    setAnswer(code);
    saveMeta('special');
    updateStatus();
  }

  function resetState() {
    stopDemo();
    finished = false; finalStatus = ''; specialCode = ''; stored = '';
    attempts = 0; seq = []; moves = 0; tFirst = null; t0 = Date.now();
    build();
    layout();
    startHints();
    updateStatus();
  }

  function restart() {
    if (readOnly || !practice) { return; }
    resetState();
    setAnswer('');
    try { if (typeof setMetaData === 'function') { setMetaData(''); } } catch (e) { /* ignore */ }
  }

  // Required by SurveyCTO: called when the field is cleared (for example when it is hidden by relevance).
  window.clearAnswer = function () {
    resetState();
    setAnswer('');
  };

  gear.addEventListener('click', function () { panel.hidden = !panel.hidden; });
  btnCannot.addEventListener('click', function () { setSpecial(codeCannot); });
  btnRefuse.addEventListener('click', function () { setSpecial(codeRefuse); });
  btnRestart.addEventListener('click', restart);
  speaker.addEventListener('click', function () {
    try { audioEl.currentTime = 0; audioEl.play(); } catch (e) { /* ignore */ }
  });

  /* ---------- Start ---------- */

  function startHints() {
    if (finished || readOnly) { return; }
    if (demoOn) { idleTimer = setTimeout(runDemo, 1500); }
    else { resetIdle(); }
  }

  function restoreIfAnswered() {
    var ans = String(FP.CURRENT_ANSWER === undefined || FP.CURRENT_ANSWER === null ? '' : FP.CURRENT_ANSWER);
    if (!ans) { return; }
    if (ans === codeCannot || ans === codeRefuse) {
      specialCode = ans; finished = true; lockAll();
      return;
    }
    var p = pieceById(ans);
    if (!p) { return; }
    stored = ans;
    finished = true;
    finalStatus = (ans === correctId) ? 'correct' : 'incorrect';
    var meta = '';
    try { meta = (typeof getMetaData === 'function') ? String(getMetaData() || '') : ''; } catch (e) { meta = ''; }
    var a = meta.match(/attempts=(\d+)/), mv = meta.match(/moves=(\d+)/);
    attempts = a ? parseInt(a[1], 10) : 1;
    moves = mv ? parseInt(mv[1], 10) : 0;
    lockAll();
    els[ans].classList.add('dp-placed');
    gapEl.classList.add('dp-off');
    if (ans === correctId) { els[ans].classList.add('dp-right'); }
    Object.keys(els).forEach(function (id) { if (id !== ans) { els[id].classList.add('dp-fade'); } });
  }

  function start() {
    buildDeco();
    // gap size and position (percent of the picture)
    var gw = num(param('gap_w', 22), 22);
    var gh = num(param('gap_h', gw / aspect), gw / aspect);
    if (gw <= 0 || gw >= 100 || gh <= 0 || gh >= 100) {
      problem('gap_w and gap_h must be between 0 and 100.');
      gw = 22; gh = 22 / aspect;
    }
    var gx = num(param('gap_x', NaN), NaN), gy = num(param('gap_y', NaN), NaN);
    if (isNaN(gx) || isNaN(gy)) {
      problem('gap_x and gap_y are missing (use the puzzle maker to get them).');
      gx = (100 - gw) / 2; gy = (100 - gh) / 2;
    }
    gap = { x: clamp(gx, 0, 100 - gw), y: clamp(gy, 0, 100 - gh), w: gw, h: gh };
    build();
    restoreIfAnswered();
    layout();
    startHints();
    updateStatus();
    if (FP.MEDIAAUDIO) { audioEl.src = FP.MEDIAAUDIO; speaker.hidden = false; }
    window.addEventListener('resize', layout);
    window.addEventListener('orientationchange', function () { setTimeout(layout, 250); });
  }

  if (!sceneSrc) {
    start();
  } else {
    var probe = new Image();
    var started = false;
    probe.onload = function () {
      if (started) { return; }
      started = true;
      aspect = probe.naturalHeight / probe.naturalWidth;
      start();
    };
    probe.onerror = function () {
      if (started) { return; }
      started = true;
      start();   // build() reports the missing image
    };
    probe.src = sceneSrc;
  }
})();
