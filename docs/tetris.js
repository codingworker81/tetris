/* Tetris — 웹 포팅 (PC Python 버전의 순수 로직을 1:1 이식)
 * 좌표계: row는 아래로 +, col은 오른쪽으로 + (board.py와 동일)
 * 모듈 구성(한 파일): 상수 → 보드 → 블록/회전 → 충돌/벽차기 → 7-bag →
 *   점수/레벨/중력 → 게임 상태머신 → 저장(localStorage) → 오디오 → 렌더 → 입력 → 루프
 */
'use strict';

/* ===== 상수 (board.py / piece.py) ===== */
const COLS = 10, ROWS = 20, SPAWN_BUFFER = 2;
const TOTAL_ROWS = ROWS + SPAWN_BUFFER;
const EMPTY = 0;
const I = 1, O = 2, T = 3, S = 4, Z = 5, J = 6, L = 7;
const TYPES = [I, O, T, S, Z, J, L];
const COLORS = {
  [I]: '#00f0f0', [O]: '#f0f000', [T]: '#a000f0',
  [S]: '#00f000', [Z]: '#f00000', [J]: '#0000f0', [L]: '#f0a000',
};
// 각 블록의 4개 회전 상태별 로컬 (row,col) 오프셋 — piece.py SHAPES 1:1
const SHAPES = {
  [I]: [[[1,0],[1,1],[1,2],[1,3]],[[0,2],[1,2],[2,2],[3,2]],[[2,0],[2,1],[2,2],[2,3]],[[0,1],[1,1],[2,1],[3,1]]],
  [O]: [[[0,1],[0,2],[1,1],[1,2]],[[0,1],[0,2],[1,1],[1,2]],[[0,1],[0,2],[1,1],[1,2]],[[0,1],[0,2],[1,1],[1,2]]],
  [T]: [[[0,1],[1,0],[1,1],[1,2]],[[0,1],[1,1],[1,2],[2,1]],[[1,0],[1,1],[1,2],[2,1]],[[0,1],[1,0],[1,1],[2,1]]],
  [S]: [[[0,1],[0,2],[1,0],[1,1]],[[0,1],[1,1],[1,2],[2,2]],[[1,1],[1,2],[2,0],[2,1]],[[0,0],[1,0],[1,1],[2,1]]],
  [Z]: [[[0,0],[0,1],[1,1],[1,2]],[[0,2],[1,1],[1,2],[2,1]],[[1,0],[1,1],[2,1],[2,2]],[[0,1],[1,0],[1,1],[2,0]]],
  [J]: [[[0,0],[1,0],[1,1],[1,2]],[[0,1],[0,2],[1,1],[2,1]],[[1,0],[1,1],[1,2],[2,2]],[[0,1],[1,1],[2,0],[2,1]]],
  [L]: [[[0,2],[1,0],[1,1],[1,2]],[[0,1],[1,1],[2,1],[2,2]],[[1,0],[1,1],[1,2],[2,0]],[[0,0],[0,1],[1,1],[2,1]]],
};
function cellsFor(type, rot) { return SHAPES[type][((rot % 4) + 4) % 4]; }

// SRS 벽차기 — collision.py와 동일 (저장 형식: [dcol, drow])
const KICKS_JLSTZ = {
  '0,1': [[0,0],[-1,0],[-1,-1],[0,2],[-1,2]],
  '1,0': [[0,0],[1,0],[1,1],[0,-2],[1,-2]],
  '1,2': [[0,0],[1,0],[1,1],[0,-2],[1,-2]],
  '2,1': [[0,0],[-1,0],[-1,-1],[0,2],[-1,2]],
  '2,3': [[0,0],[1,0],[1,-1],[0,2],[1,2]],
  '3,2': [[0,0],[-1,0],[-1,1],[0,-2],[-1,-2]],
  '3,0': [[0,0],[-1,0],[-1,1],[0,-2],[-1,-2]],
  '0,3': [[0,0],[1,0],[1,-1],[0,2],[1,2]],
};
const KICKS_I = {
  '0,1': [[0,0],[-2,0],[1,0],[-2,1],[1,-2]],
  '1,0': [[0,0],[2,0],[-1,0],[2,-1],[-1,2]],
  '1,2': [[0,0],[-1,0],[2,0],[-1,-2],[2,1]],
  '2,1': [[0,0],[1,0],[-2,0],[1,2],[-2,-1]],
  '2,3': [[0,0],[2,0],[-1,0],[2,-1],[-1,2]],
  '3,2': [[0,0],[-2,0],[1,0],[-2,1],[1,-2]],
  '3,0': [[0,0],[1,0],[-2,0],[1,2],[-2,-1]],
  '0,3': [[0,0],[-1,0],[2,0],[-1,-2],[2,1]],
};

/* ===== 보드 (board.py) ===== */
class Board {
  constructor() {
    this.cols = COLS; this.totalRows = TOTAL_ROWS; this.spawnBuffer = SPAWN_BUFFER;
    this.grid = Array.from({ length: TOTAL_ROWS }, () => new Array(COLS).fill(EMPTY));
  }
  inBounds(r, c) { return r >= 0 && r < this.totalRows && c >= 0 && c < this.cols; }
  isCellFilled(r, c) { return this.inBounds(r, c) ? this.grid[r][c] !== EMPTY : false; }
  set(r, c, v) { if (this.inBounds(r, c)) this.grid[r][c] = v; }
  clearFullRows() {
    const kept = this.grid.filter(row => !row.every(cell => cell !== EMPTY));
    const cleared = this.totalRows - kept.length;
    const empties = Array.from({ length: cleared }, () => new Array(COLS).fill(EMPTY));
    this.grid = empties.concat(kept);
    return cleared;
  }
  clear() { this.grid = Array.from({ length: TOTAL_ROWS }, () => new Array(COLS).fill(EMPTY)); }
}

/* ===== 블록 (piece.py) ===== */
class Piece {
  constructor(type, row = 0, col = 0, rot = 0) {
    this.type = type; this.row = row; this.col = col; this.rotation = ((rot % 4) + 4) % 4;
  }
  localCells() { return cellsFor(this.type, this.rotation); }
  boardCells() { return this.localCells().map(([dr, dc]) => [this.row + dr, this.col + dc]); }
  copy() { return new Piece(this.type, this.row, this.col, this.rotation); }
}

/* ===== 충돌/벽차기 (collision.py) ===== */
function cellsValid(board, cells) {
  for (const [r, c] of cells) {
    if (!board.inBounds(r, c)) return false;
    if (board.isCellFilled(r, c)) return false;
  }
  return true;
}
function pieceFits(board, p) { return cellsValid(board, p.boardCells()); }
function canMove(board, p, drow, dcol) {
  return cellsValid(board, p.boardCells().map(([r, c]) => [r + drow, c + dcol]));
}
function tryMove(board, p, drow, dcol) {
  if (canMove(board, p, drow, dcol)) { p.row += drow; p.col += dcol; return true; }
  return false;
}
function tryRotate(board, p, dir) {
  if (p.type === O) return true;
  const oldRot = p.rotation, newRot = ((oldRot + dir) % 4 + 4) % 4;
  const table = p.type === I ? KICKS_I : KICKS_JLSTZ;
  const kicks = table[`${oldRot},${newRot}`] || [[0, 0]];
  const base = cellsFor(p.type, newRot).map(([dr, dc]) => [p.row + dr, p.col + dc]);
  for (const [dcol, drow] of kicks) {
    const cand = base.map(([r, c]) => [r + drow, c + dcol]);
    if (cellsValid(board, cand)) { p.rotation = newRot; p.row += drow; p.col += dcol; return true; }
  }
  return false;
}
function lockPiece(board, p) { for (const [r, c] of p.boardCells()) if (board.inBounds(r, c)) board.set(r, c, p.type); }

/* ===== 7-bag (sevenbag.py) ===== */
class SevenBag {
  constructor() { this.queue = []; }
  refill() {
    const bag = TYPES.slice();
    for (let i = bag.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [bag[i], bag[j]] = [bag[j], bag[i]]; }
    this.queue.push(...bag);
  }
  ensure(n) { while (this.queue.length < n) this.refill(); }
  nextType() { this.ensure(1); return this.queue.shift(); }
  peek(n) { this.ensure(n); return this.queue.slice(0, n); }
}

/* ===== 점수/레벨/중력 (scoring.py) ===== */
const LINE_BASE = { 0: 0, 1: 100, 2: 300, 3: 500, 4: 800 };
const LINES_PER_LEVEL = 10, BASE_INTERVAL = 800, MIN_INTERVAL = 60;
function lineScore(lines, level) { return (LINE_BASE[lines] || 0) * level; }
function levelForLines(total) { return 1 + Math.floor(total / LINES_PER_LEVEL); }
function gravityIntervalMs(level) { return Math.max(MIN_INTERVAL, Math.floor(BASE_INTERVAL * Math.pow(0.85, level - 1))); }
class Scorer {
  constructor() { this.score = 0; this.lines = 0; this.level = 1; }
  addLineClear(c) { const g = lineScore(c, this.level); this.score += g; this.lines += c; this.level = levelForLines(this.lines); return g; }
  addSoftDrop(c) { this.score += Math.max(0, c); }
  addHardDrop(c) { this.score += Math.max(0, c) * 2; }
  get intervalMs() { return gravityIntervalMs(this.level); }
}

/* ===== 게임 상태머신 (game.py) ===== */
const SPAWN_COL = Math.floor((COLS - 4) / 2);
class Game {
  constructor() {
    this.board = new Board(); this.bag = new SevenBag(); this.scorer = new Scorer();
    this.current = null; this.holdType = null; this.holdUsed = false; this.gameOver = false;
    this.lastCleared = 0; this.lastLevelUp = false; this.lastLocked = false;
    this.spawnNext();
  }
  newPiece(type) { return new Piece(type, 0, SPAWN_COL, 0); }
  spawnNext() { this.spawnType(this.bag.nextType()); }
  spawnType(type) {
    const p = this.newPiece(type); this.holdUsed = false;
    if (!pieceFits(this.board, p)) { this.current = p; this.gameOver = true; return; }
    this.current = p;
  }
  nextTypes(n = 3) { return this.bag.peek(n); }
  hold() {
    if (this.gameOver || !this.current || this.holdUsed) return false;
    const cur = this.current.type;
    if (this.holdType === null) { this.holdType = cur; this.spawnNext(); }
    else { const swap = this.holdType; this.holdType = cur; this.spawnType(swap); }
    this.holdUsed = true; return true;
  }
  ghostCells() {
    if (!this.current) return [];
    let drop = 0;
    while (canMove(this.board, this.current, drop + 1, 0)) drop++;
    return this.current.boardCells().map(([r, c]) => [r + drop, c]);
  }
  moveLeft() { return !this.gameOver && this.current && tryMove(this.board, this.current, 0, -1); }
  moveRight() { return !this.gameOver && this.current && tryMove(this.board, this.current, 0, 1); }
  rotateCw() { return !this.gameOver && this.current && tryRotate(this.board, this.current, 1); }
  rotateCcw() { return !this.gameOver && this.current && tryRotate(this.board, this.current, -1); }
  softDrop() {
    if (this.gameOver || !this.current) return false;
    if (tryMove(this.board, this.current, 1, 0)) { this.scorer.addSoftDrop(1); return true; }
    this.lockAndSpawn(); return false;
  }
  hardDrop() {
    if (this.gameOver || !this.current) return 0;
    let dropped = 0;
    while (tryMove(this.board, this.current, 1, 0)) dropped++;
    this.scorer.addHardDrop(dropped); this.lockAndSpawn(); return dropped;
  }
  stepGravity() {
    if (this.gameOver || !this.current) return;
    if (!tryMove(this.board, this.current, 1, 0)) this.lockAndSpawn();
  }
  lockAndSpawn() {
    lockPiece(this.board, this.current);
    const levelBefore = this.scorer.level;
    const cleared = this.board.clearFullRows();
    if (cleared) this.scorer.addLineClear(cleared);
    this.lastCleared = cleared; this.lastLevelUp = this.scorer.level > levelBefore; this.lastLocked = true;
    this.spawnNext();
  }
  consumeEvents() {
    const ev = [this.lastCleared, this.lastLevelUp, this.lastLocked];
    this.lastCleared = 0; this.lastLevelUp = false; this.lastLocked = false; return ev;
  }
}

/* ===== 저장 (storage.py → localStorage) ===== */
const STORE = {
  SCORES: 'tetris.scores', SETTINGS: 'tetris.settings', TOP_N: 10,
  DEFAULTS: { sound: true, volume: 0.7, showTouch: true },
  loadScores() { try { const v = JSON.parse(localStorage.getItem(this.SCORES)); return Array.isArray(v) ? v : []; } catch { return []; } },
  saveScores(s) { localStorage.setItem(this.SCORES, JSON.stringify(s.slice(0, this.TOP_N))); },
  addScore(name, score) {
    const s = this.loadScores(); s.push({ name: String(name || '익명').slice(0, 8), score: Math.floor(score) });
    s.sort((a, b) => b.score - a.score); const top = s.slice(0, this.TOP_N); this.saveScores(top); return top;
  },
  isHighScore(score) {
    const s = this.loadScores(); if (s.length < this.TOP_N) return score > 0;
    return score > Math.min(...s.map(e => e.score || 0));
  },
  loadSettings() { try { return Object.assign({}, this.DEFAULTS, JSON.parse(localStorage.getItem(this.SETTINGS)) || {}); } catch { return Object.assign({}, this.DEFAULTS); } },
  saveSettings(s) { localStorage.setItem(this.SETTINGS, JSON.stringify(s)); },
};

/* ===== 오디오 (Web Audio로 효과음 합성 — PC의 make_sfx.py 역할) ===== */
const Sound = {
  ctx: null, settings: STORE.loadSettings(),
  ensure() { if (!this.ctx) { try { this.ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch { this.ctx = null; } } if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume(); },
  beep(freq, dur, type = 'square', vol = 1) {
    if (!this.settings.sound) return; this.ensure(); if (!this.ctx) return;
    const t = this.ctx.currentTime, osc = this.ctx.createOscillator(), g = this.ctx.createGain();
    osc.type = type; osc.frequency.value = freq;
    const v = this.settings.volume * vol * 0.25;
    g.gain.setValueAtTime(v, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.connect(g); g.connect(this.ctx.destination); osc.start(t); osc.stop(t + dur);
  },
  move() { this.beep(220, 0.05, 'square', 0.6); },
  rotate() { this.beep(330, 0.06, 'triangle', 0.7); },
  harddrop() { this.beep(140, 0.09, 'sawtooth', 0.8); },
  lineclear(n) { const base = 440; for (let i = 0; i < Math.max(1, n); i++) setTimeout(() => this.beep(base + i * 120, 0.12, 'square', 0.9), i * 60); },
  gameover() { [330, 262, 196, 131].forEach((f, i) => setTimeout(() => this.beep(f, 0.22, 'sawtooth', 0.9), i * 160)); },
};

/* ===== 렌더 ===== */
const boardCanvas = document.getElementById('board');
const bctx = boardCanvas.getContext('2d');
const holdCanvas = document.getElementById('holdCanvas'), hctx = holdCanvas.getContext('2d');
const nextCanvas = document.getElementById('nextCanvas'), nctx = nextCanvas.getContext('2d');
let CELL = 24;

function resizeBoard() {
  // 보드 캔버스를 사용 가능한 세로 높이에 맞춰 셀 크기 산출
  const wrap = document.querySelector('.game-wrap');
  const avail = wrap.clientHeight - 8;
  CELL = Math.max(12, Math.floor(avail / ROWS));
  boardCanvas.width = CELL * COLS;
  boardCanvas.height = CELL * ROWS;
}

function drawCell(ctx, x, y, color, size = CELL) {
  ctx.fillStyle = color; ctx.fillRect(x, y, size, size);
  ctx.strokeStyle = 'rgba(255,255,255,0.18)'; ctx.lineWidth = 1;
  ctx.strokeRect(x + 0.5, y + 0.5, size - 1, size - 1);
  // 하이라이트
  ctx.fillStyle = 'rgba(255,255,255,0.12)'; ctx.fillRect(x + 1, y + 1, size - 2, Math.max(2, size * 0.14));
}

function render(game) {
  bctx.fillStyle = '#05070f'; bctx.fillRect(0, 0, boardCanvas.width, boardCanvas.height);
  // 그리드 라인
  bctx.strokeStyle = '#141a2e'; bctx.lineWidth = 1;
  for (let c = 0; c <= COLS; c++) { bctx.beginPath(); bctx.moveTo(c * CELL, 0); bctx.lineTo(c * CELL, ROWS * CELL); bctx.stroke(); }
  for (let r = 0; r <= ROWS; r++) { bctx.beginPath(); bctx.moveTo(0, r * CELL); bctx.lineTo(COLS * CELL, r * CELL); bctx.stroke(); }
  // 고정 블록 (보이는 영역)
  for (let r = SPAWN_BUFFER; r < TOTAL_ROWS; r++)
    for (let c = 0; c < COLS; c++) {
      const v = game.board.grid[r][c];
      if (v !== EMPTY) drawCell(bctx, c * CELL, (r - SPAWN_BUFFER) * CELL, COLORS[v]);
    }
  // 고스트
  if (game.current && !game.gameOver) {
    for (const [r, c] of game.ghostCells()) {
      const vr = r - SPAWN_BUFFER; if (vr < 0) continue;
      bctx.fillStyle = COLORS[game.current.type] + '33';
      bctx.fillRect(c * CELL, vr * CELL, CELL, CELL);
      bctx.strokeStyle = COLORS[game.current.type] + '88'; bctx.strokeRect(c * CELL + 0.5, vr * CELL + 0.5, CELL - 1, CELL - 1);
    }
    // 현재 블록
    for (const [r, c] of game.current.boardCells()) {
      const vr = r - SPAWN_BUFFER; if (vr < 0) continue;
      drawCell(bctx, c * CELL, vr * CELL, COLORS[game.current.type]);
    }
  }
  // HOLD
  hctx.fillStyle = '#05070f'; hctx.fillRect(0, 0, holdCanvas.width, holdCanvas.height);
  if (game.holdType) drawMini(hctx, game.holdType, holdCanvas.width, holdCanvas.height, 0);
  // NEXT (3개)
  nctx.fillStyle = '#05070f'; nctx.fillRect(0, 0, nextCanvas.width, nextCanvas.height);
  game.nextTypes(3).forEach((t, i) => drawMini(nctx, t, nextCanvas.width, 86, i * 86));
}

function drawMini(ctx, type, w, h, yOff) {
  const cells = cellsFor(type, 0);
  const cols = cells.map(c => c[1]), rows = cells.map(c => c[0]);
  const minC = Math.min(...cols), maxC = Math.max(...cols), minR = Math.min(...rows), maxR = Math.max(...rows);
  const pw = maxC - minC + 1, ph = maxR - minR + 1;
  const sz = Math.min(Math.floor((w - 16) / 4), 18);
  const ox = (w - pw * sz) / 2, oy = yOff + (h - ph * sz) / 2;
  for (const [r, c] of cells) drawCell(ctx, ox + (c - minC) * sz, oy + (r - minR) * sz, COLORS[type], sz);
}

/* ===== 게임 루프 + 화면 상태 ===== */
let game = null, running = false, paused = false, lastTime = 0, dropAcc = 0;
const el = (id) => document.getElementById(id);

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  el(id).classList.add('active');
  if (id === 'game') resizeBoard();
}

function updateHud() { el('score').textContent = game.scorer.score; el('lines').textContent = game.scorer.lines; el('level').textContent = game.scorer.level; }

function loop(ts) {
  if (!running) return;
  if (!lastTime) lastTime = ts;
  const dt = ts - lastTime; lastTime = ts;
  if (!paused && !game.gameOver) {
    dropAcc += dt;
    const interval = game.scorer.intervalMs;
    while (dropAcc >= interval) { game.stepGravity(); dropAcc -= interval; handleEvents(); }
  }
  render(game); updateHud();
  if (game.gameOver) { onGameOver(); return; }
  requestAnimationFrame(loop);
}

function handleEvents() {
  const [cleared, , locked] = game.consumeEvents();
  if (cleared > 0) Sound.lineclear(cleared);
  else if (locked) Sound.harddrop();
}

function startGame() {
  game = new Game(); running = true; paused = false; lastTime = 0; dropAcc = 0;
  el('pauseOverlay').classList.add('hidden'); el('overOverlay').classList.add('hidden');
  Sound.ensure(); showScreen('game'); requestAnimationFrame(loop);
}

function onGameOver() {
  running = false; Sound.gameover();
  el('finalScore').textContent = game.scorer.score;
  const entry = el('nameEntry');
  if (STORE.isHighScore(game.scorer.score)) { entry.classList.remove('hidden'); el('nameInput').value = ''; }
  else entry.classList.add('hidden');
  el('overOverlay').classList.remove('hidden');
}

function renderRanking() {
  const list = el('rankList'); const scores = STORE.loadScores(); list.innerHTML = '';
  if (!scores.length) { const li = document.createElement('li'); li.className = 'empty'; li.textContent = '아직 기록이 없습니다'; list.appendChild(li); return; }
  scores.forEach((e, i) => {
    const li = document.createElement('li');
    li.innerHTML = `<span class="rk">${i + 1}</span><span class="nm">${escapeHtml(e.name)}</span><span class="sc">${e.score}</span>`;
    list.appendChild(li);
  });
}
function escapeHtml(s) { return String(s).replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m])); }

/* ===== 입력: 키보드 ===== */
const KEY_REPEAT = { down: false };
document.addEventListener('keydown', (e) => {
  if (!running) return;
  if (game.gameOver) return;
  let used = true;
  switch (e.key) {
    case 'ArrowLeft': if (game.moveLeft()) Sound.move(); break;
    case 'ArrowRight': if (game.moveRight()) Sound.move(); break;
    case 'ArrowDown': game.softDrop(); handleEvents(); break;
    case ' ': game.hardDrop(); handleEvents(); break;
    case 'ArrowUp': case 'x': case 'X': if (game.rotateCw()) Sound.rotate(); break;
    case 'z': case 'Z': if (game.rotateCcw()) Sound.rotate(); break;
    case 'c': case 'C': if (game.hold()) Sound.rotate(); break;
    case 'p': case 'P': case 'Escape': togglePause(); break;
    default: used = false;
  }
  if (used) e.preventDefault();
}, { passive: false });

/* ===== 입력: 터치 (반복 처리 포함) ===== */
const repeatTimers = {};
function doAction(k) {
  if (!running || game.gameOver || paused) return;
  switch (k) {
    case 'left': if (game.moveLeft()) Sound.move(); break;
    case 'right': if (game.moveRight()) Sound.move(); break;
    case 'soft': game.softDrop(); handleEvents(); break;
    case 'hard': game.hardDrop(); handleEvents(); break;
    case 'rcw': if (game.rotateCw()) Sound.rotate(); break;
    case 'rccw': if (game.rotateCcw()) Sound.rotate(); break;
    case 'hold': if (game.hold()) Sound.rotate(); break;
  }
}
document.querySelectorAll('.tbtn').forEach(btn => {
  const k = btn.dataset.k;
  const press = (e) => {
    e.preventDefault(); Sound.ensure(); doAction(k);
    if (k === 'left' || k === 'right' || k === 'soft') {
      clearInterval(repeatTimers[k]);
      repeatTimers[k] = setInterval(() => doAction(k), 90);
    }
  };
  const release = () => { clearInterval(repeatTimers[k]); };
  btn.addEventListener('touchstart', press, { passive: false });
  btn.addEventListener('touchend', release); btn.addEventListener('touchcancel', release);
  btn.addEventListener('mousedown', press); btn.addEventListener('mouseup', release); btn.addEventListener('mouseleave', release);
});

/* ===== 메뉴/오버레이 버튼 ===== */
function togglePause() {
  if (!running || game.gameOver) return;
  paused = !paused;
  el('pauseOverlay').classList.toggle('hidden', !paused);
  if (!paused) { lastTime = 0; requestAnimationFrame(loop); }
}
document.body.addEventListener('click', (e) => {
  const action = e.target.dataset && e.target.dataset.action;
  if (!action) return;
  switch (action) {
    case 'start': startGame(); break;
    case 'ranking': renderRanking(); showScreen('ranking'); break;
    case 'settings': syncSettingsUI(); showScreen('settings'); break;
    case 'toMenu': running = false; showScreen('menu'); break;
    case 'resume': togglePause(); break;
    case 'restart': startGame(); break;
    case 'saveScore': { STORE.addScore(el('nameInput').value.trim(), game.scorer.score); el('nameEntry').classList.add('hidden'); break; }
  }
});
el('pauseBtn').addEventListener('click', togglePause);
el('soundBtn').addEventListener('click', () => {
  Sound.settings.sound = !Sound.settings.sound; const s = STORE.loadSettings(); s.sound = Sound.settings.sound; STORE.saveSettings(s);
  el('soundBtn').textContent = Sound.settings.sound ? '🔊' : '🔇';
});

/* ===== 설정 화면 ===== */
function syncSettingsUI() {
  const s = STORE.loadSettings();
  el('setSound').dataset.on = String(s.sound); el('setSound').textContent = s.sound ? '켜짐' : '꺼짐';
  el('setVolume').value = Math.round(s.volume * 100); el('volLabel').textContent = Math.round(s.volume * 100) + '%';
  el('setTouch').dataset.on = String(s.showTouch); el('setTouch').textContent = s.showTouch ? '켜짐' : '꺼짐';
  el('touchpad').classList.toggle('hidden', !s.showTouch);
}
el('setSound').addEventListener('click', () => { const s = STORE.loadSettings(); s.sound = !s.sound; STORE.saveSettings(s); Sound.settings.sound = s.sound; syncSettingsUI(); el('soundBtn').textContent = s.sound ? '🔊' : '🔇'; });
el('setTouch').addEventListener('click', () => { const s = STORE.loadSettings(); s.showTouch = !s.showTouch; STORE.saveSettings(s); syncSettingsUI(); });
el('setVolume').addEventListener('input', (e) => { const s = STORE.loadSettings(); s.volume = e.target.value / 100; STORE.saveSettings(s); Sound.settings.volume = s.volume; el('volLabel').textContent = e.target.value + '%'; });

/* ===== PWA 설치 프롬프트 ===== */
let deferredPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); deferredPrompt = e; el('installBtn').classList.remove('hidden'); });
el('installBtn').addEventListener('click', async () => { if (!deferredPrompt) return; deferredPrompt.prompt(); await deferredPrompt.userChoice; deferredPrompt = null; el('installBtn').classList.add('hidden'); });

/* ===== 초기화 ===== */
window.addEventListener('resize', () => { if (el('game').classList.contains('active')) resizeBoard(); });
(function init() {
  const s = STORE.loadSettings();
  Sound.settings = s;
  el('soundBtn').textContent = s.sound ? '🔊' : '🔇';
  el('touchpad').classList.toggle('hidden', !s.showTouch);
  // 버전 라벨(선택): 전역에서 노출되면 반영
  showScreen('menu');
})();

/* 테스트 훅: 로직 모듈을 전역에 노출 (headless 검증용) */
window.__TETRIS__ = { Board, Piece, SevenBag, Scorer, Game, cellsFor, tryRotate, canMove, lineScore, levelForLines, gravityIntervalMs, COLS, ROWS, TYPES };
