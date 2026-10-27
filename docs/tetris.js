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
  DEFAULTS: { sound: true, volume: 0.7, showTouch: true, bgm: true, bgmVolume: 0.4, haptics: true, swipe: true, scheme: 'midnight', subject: 'none', bgDim: 0.55 },
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
  CUSTOM_IMG: 'tetris.customBg',
  loadCustomImg() { try { return localStorage.getItem(this.CUSTOM_IMG) || null; } catch { return null; } },
  saveCustomImg(dataUrl) { try { if (dataUrl) localStorage.setItem(this.CUSTOM_IMG, dataUrl); else localStorage.removeItem(this.CUSTOM_IMG); return true; } catch { return false; } },
};

/* ===== 오디오 (Web Audio로 효과음 + 배경음악 합성) ===== */
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

/* ===== 배경음악 BGM (Korobeiniki 스타일 멜로디를 Web Audio로 합성·반복) ===== */
const BGM = {
  playing: false, gain: null, timer: null, noteIdx: 0, startAt: 0,
  tempo: 0.14, // 한 박(8분음표) 길이(초) — 레벨 올라가면 빨라짐
  // [주파수Hz(0=쉼표), 길이(박)] — 테트리스 테마 한 소절(클래식 Korobeiniki A파트)
  melody: [
    [659,2],[494,1],[523,1],[587,2],[523,1],[494,1],
    [440,2],[440,1],[523,1],[659,2],[587,1],[523,1],
    [494,3],[523,1],[587,2],[659,2],
    [523,2],[440,2],[440,2],[0,2],
    [587,3],[698,1],[880,2],[784,1],[698,1],
    [659,3],[523,1],[659,2],[587,1],[523,1],
    [494,2],[494,1],[523,1],[587,2],[659,2],
    [523,2],[440,2],[440,2],[0,2],
  ],
  // 베이스 라인(2박마다 저음) — 멜로디와 함께 반복
  bass: [220,220,165,165,196,196,220,220,220,220,165,165,196,196,220,220],
  start() {
    if (this.playing) return; if (!this.settings.bgm) return;
    Sound.ensure(); if (!Sound.ctx) return;
    this.playing = true; this.noteIdx = 0;
    this.gain = Sound.ctx.createGain();
    this.gain.gain.value = this.settings.bgmVolume * 0.18;
    this.gain.connect(Sound.ctx.destination);
    this.startAt = Sound.ctx.currentTime + 0.05;
    this.schedule();
  },
  get settings() { return Sound.settings; },
  setLevel(level) { this.tempo = Math.max(0.085, 0.145 - (level - 1) * 0.006); },
  schedule() {
    if (!this.playing || !Sound.ctx) return;
    // 한 소절을 스케줄하고, 끝나기 전에 다음 소절 예약(끊김 없는 반복)
    let t = this.startAt, beat = this.tempo, barBeats = 0;
    this.melody.forEach(([f, len]) => {
      if (f > 0) this.tone(f, t, len * beat * 0.92, 'square', 1);
      t += len * beat; barBeats += len;
    });
    // 베이스: 2박 간격
    let bt = this.startAt;
    for (let i = 0; i < this.bass.length; i++) { this.tone(this.bass[i], bt, beat * 2 * 0.9, 'triangle', 0.5); bt += beat * 2; }
    const barDur = barBeats * beat;
    this.startAt += barDur;
    this.timer = setTimeout(() => this.schedule(), Math.max(50, (barDur - 0.3) * 1000));
  },
  tone(freq, when, dur, type, vol) {
    if (!this.gain || !Sound.ctx) return;
    const osc = Sound.ctx.createOscillator(), g = Sound.ctx.createGain();
    osc.type = type; osc.frequency.value = freq;
    g.gain.setValueAtTime(0.0001, when);
    g.gain.exponentialRampToValueAtTime(vol, when + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, when + dur);
    osc.connect(g); g.connect(this.gain); osc.start(when); osc.stop(when + dur + 0.02);
  },
  stop() {
    this.playing = false; clearTimeout(this.timer); this.timer = null;
    if (this.gain) { try { this.gain.disconnect(); } catch {} this.gain = null; }
  },
  setVolume(v) { if (this.gain) this.gain.gain.value = v * 0.18; },
  refresh() { // 설정 변경 시: bgm 꺼지면 정지, 켜지고 게임중이면 시작
    if (!this.settings.bgm) this.stop();
    else if (running && !paused && !game.gameOver && !this.playing) this.start();
  },
};

/* ===== 햅틱(진동) 피드백 ===== */
const Haptics = {
  on() { return Sound.settings.haptics && typeof navigator.vibrate === 'function'; },
  tap() { if (this.on()) navigator.vibrate(10); },
  move() { if (this.on()) navigator.vibrate(8); },
  rotate() { if (this.on()) navigator.vibrate(12); },
  drop() { if (this.on()) navigator.vibrate(22); },
  clear(n) { if (this.on()) navigator.vibrate(n >= 4 ? [30, 40, 30, 40, 50] : [18, 25, 18]); },
  over() { if (this.on()) navigator.vibrate([60, 50, 60, 50, 120]); },
};

/* ===== 배경 테마 ===== */
const VERSION = '1.1.0';

// 화면 색상(스킴) — 미드나잇/라이트 2종만
const SCHEMES = {
  midnight: { name: '미드나잇', vars: { '--bg':'#0b0e1a','--panel':'#151a2e','--panel2':'#1e2440','--grid':'#222844','--text':'#e8ecff','--muted':'#8b93b8','--accent':'#5b8cff','--accent2':'#3a66d6','--danger':'#ff5b6e','--ok':'#38d39f' }, boardBg:'#05070f', gridLine:'#141a2e' },
  light:    { name: '라이트', vars: { '--bg':'#eef1f7','--panel':'#ffffff','--panel2':'#dfe4ee','--grid':'#c3cad8','--text':'#1a2036','--muted':'#5a6480','--accent':'#3a66d6','--accent2':'#5b8cff','--danger':'#d63a4e','--ok':'#1a9e74' }, boardBg:'#f7f9fc', gridLine:'#d5dce8' },
};

// 배경 주제 — CSS 그라데이션/패턴으로 구현(외부 이미지 없이, 오프라인 PWA 유지).
// icon: 미리보기 이모지, css: #bgLayer에 적용할 background 값. custom은 사용자 업로드 이미지.
const SUBJECTS = {
  none:   { name: '없음',       icon: '🚫', css: 'transparent' },
  animal: { name: '동물',       icon: '🐾', css: 'radial-gradient(circle at 20% 30%, rgba(255,183,94,.35), transparent 40%), radial-gradient(circle at 80% 70%, rgba(120,200,120,.3), transparent 45%), linear-gradient(160deg,#2b1d10,#13240f)' },
  anime:  { name: '애니메이션', icon: '✨', css: 'radial-gradient(circle at 30% 20%, rgba(255,120,200,.45), transparent 42%), radial-gradient(circle at 75% 60%, rgba(120,170,255,.4), transparent 45%), linear-gradient(140deg,#2a0f3a,#0f1740)' },
  flower: { name: '꽃',         icon: '🌸', css: 'radial-gradient(circle at 25% 25%, rgba(255,150,190,.5), transparent 38%), radial-gradient(circle at 70% 35%, rgba(255,210,120,.4), transparent 36%), radial-gradient(circle at 55% 80%, rgba(180,120,255,.4), transparent 40%), linear-gradient(160deg,#30182a,#17210f)' },
  city:   { name: '도시',       icon: '🌆', css: 'linear-gradient(180deg,#1a1033 0%,#3a2a66 45%,#ff7a4d 72%,#ffb37a 100%)' },
  nature: { name: '자연',       icon: '🏞️', css: 'linear-gradient(180deg,#8fd3ff 0%,#bfe8c8 45%,#5ba85f 72%,#2f6b35 100%)' },
  custom: { name: 'Custom',     icon: '🖼️', css: null }, // 사용자 이미지(data URL)
};

const ThemeMgr = {
  scheme: 'midnight', subject: 'none', dim: 0.55, customImg: null,
  applyScheme(name) {
    const sc = SCHEMES[name] ? name : 'midnight'; this.scheme = sc;
    const th = SCHEMES[sc];
    const root = document.documentElement.style;
    Object.entries(th.vars).forEach(([k, v]) => root.setProperty(k, v));
    const meta = document.querySelector('meta[name="theme-color"]'); if (meta) meta.setAttribute('content', th.vars['--bg']);
    this.boardBg = th.boardBg; this.gridLine = th.gridLine;
    if (typeof game !== 'undefined' && game) render(game);
  },
  applySubject(name, customDataUrl) {
    this.subject = SUBJECTS[name] ? name : 'none';
    if (customDataUrl !== undefined) this.customImg = customDataUrl;
    this.renderBg();
  },
  setDim(v) { this.dim = Math.max(0, Math.min(0.95, v)); this.renderBg(); },
  renderBg() {
    const layer = document.getElementById('bgLayer'); if (!layer) return;
    const subj = SUBJECTS[this.subject] || SUBJECTS.none;
    let img = '';
    if (this.subject === 'custom' && this.customImg) img = `url("${this.customImg}")`;
    else if (subj.css && subj.css !== 'transparent') img = subj.css;
    if (!img) { layer.style.backgroundImage = 'none'; layer.style.opacity = '0'; return; }
    layer.style.opacity = '1';
    layer.style.backgroundImage = img;
    layer.style.backgroundSize = 'cover';
    layer.style.backgroundPosition = 'center';
    // 가독성: 어둡게 덮는 오버레이는 ::before(CSS)에서 처리, 여기서는 변수만
    layer.style.setProperty('--bg-dim', String(this.dim));
  },
  boardBg: '#05070f', gridLine: '#141a2e',
};

/* ===== 렌더 ===== */
const boardCanvas = document.getElementById('board');
const bctx = boardCanvas.getContext('2d');
const holdCanvas = document.getElementById('holdCanvas'), hctx = holdCanvas.getContext('2d');
const nextCanvas = document.getElementById('nextCanvas'), nctx = nextCanvas.getContext('2d');
let CELL = 24;

function resizeBoard() {
  // 보드 캔버스를 사용 가능한 '가로/세로 모두'에 맞춰 셀 크기 산출 (좌우 잘림 방지)
  const wrap = document.querySelector('.game-wrap');
  const leftSide = document.querySelector('.side.left');
  const rightSide = document.querySelector('.side.right');
  const availH = wrap.clientHeight - 8;
  // 좌우 패널이 가로로 공간을 차지하므로 보드가 쓸 수 있는 가로폭을 뺀다
  const sideW = (leftSide ? leftSide.offsetWidth : 0) + (rightSide ? rightSide.offsetWidth : 0);
  const gaps = 10 * 2 + 16; // game-wrap gap(10)*2 + padding 여유
  const availW = wrap.clientWidth - sideW - gaps;
  const cellByH = Math.floor(availH / ROWS);
  const cellByW = Math.floor(availW / COLS);
  CELL = Math.max(10, Math.min(cellByH, cellByW)); // 둘 중 작은 값 → 항상 화면 안에
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
  const subjectOn = ThemeMgr.subject && ThemeMgr.subject !== 'none';
  if (subjectOn) {
    // 배경 주제가 보이도록 보드를 반투명하게
    bctx.clearRect(0, 0, boardCanvas.width, boardCanvas.height);
    bctx.fillStyle = ThemeMgr.scheme === 'light' ? 'rgba(247,249,252,0.55)' : 'rgba(5,7,15,0.55)';
    bctx.fillRect(0, 0, boardCanvas.width, boardCanvas.height);
  } else {
    bctx.fillStyle = ThemeMgr.boardBg; bctx.fillRect(0, 0, boardCanvas.width, boardCanvas.height);
  }
  // 그리드 라인
  bctx.strokeStyle = ThemeMgr.gridLine; bctx.lineWidth = 1;
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
  hctx.fillStyle = ThemeMgr.boardBg; hctx.fillRect(0, 0, holdCanvas.width, holdCanvas.height);
  if (game.holdType) drawMini(hctx, game.holdType, holdCanvas.width, holdCanvas.height, 0);
  // NEXT (3개)
  nctx.fillStyle = ThemeMgr.boardBg; nctx.fillRect(0, 0, nextCanvas.width, nextCanvas.height);
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

let lastBgmLevel = 1;
function handleEvents() {
  const [cleared, levelUp, locked] = game.consumeEvents();
  if (cleared > 0) { Sound.lineclear(cleared); Haptics.clear(cleared); }
  else if (locked) { Sound.harddrop(); Haptics.drop(); }
  if (levelUp && game.scorer.level !== lastBgmLevel) { lastBgmLevel = game.scorer.level; BGM.setLevel(game.scorer.level); }
}

function startGame() {
  game = new Game(); running = true; paused = false; lastTime = 0; dropAcc = 0; lastBgmLevel = 1;
  el('pauseOverlay').classList.add('hidden'); el('overOverlay').classList.add('hidden');
  Sound.ensure(); showScreen('game'); BGM.setLevel(1); BGM.stop(); BGM.start(); requestAnimationFrame(loop);
}

function onGameOver() {
  running = false; BGM.stop(); Sound.gameover(); Haptics.over();
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
    case 'ArrowLeft': if (game.moveLeft()) { Sound.move(); Haptics.move(); } break;
    case 'ArrowRight': if (game.moveRight()) { Sound.move(); Haptics.move(); } break;
    case 'ArrowDown': game.softDrop(); handleEvents(); break;
    case ' ': game.hardDrop(); handleEvents(); break;
    case 'ArrowUp': case 'x': case 'X': if (game.rotateCw()) { Sound.rotate(); Haptics.rotate(); } break;
    case 'z': case 'Z': if (game.rotateCcw()) { Sound.rotate(); Haptics.rotate(); } break;
    case 'c': case 'C': if (game.hold()) { Sound.rotate(); Haptics.tap(); } break;
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
    case 'left': if (game.moveLeft()) { Sound.move(); Haptics.move(); } break;
    case 'right': if (game.moveRight()) { Sound.move(); Haptics.move(); } break;
    case 'soft': game.softDrop(); handleEvents(); break;
    case 'hard': game.hardDrop(); handleEvents(); break;
    case 'rcw': if (game.rotateCw()) { Sound.rotate(); Haptics.rotate(); } break;
    case 'rccw': if (game.rotateCcw()) { Sound.rotate(); Haptics.rotate(); } break;
    case 'hold': if (game.hold()) { Sound.rotate(); Haptics.tap(); } break;
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

/* ===== 입력: 스와이프 제스처 (보드 위) =====
 * 가로 스와이프 = 좌우 이동(거리에 비례해 여러 칸),
 * 아래로 빠르게 쓸기 = 하드드롭, 천천히 아래로 = 소프트드롭,
 * 짧은 탭 = 시계회전. 설정에서 끌 수 있음. */
let sw = null;
function onSwipeStart(x, y) {
  if (!running || game.gameOver || paused || !Sound.settings.swipe) { sw = null; return; }
  Sound.ensure();
  sw = { x0: x, y0: y, x: x, y: y, t0: performance.now(), movedCols: 0, softCount: 0, dropped: false, moved: false };
}
function onSwipeMove(x, y) {
  if (!sw || sw.dropped) return;
  const unit = Math.max(18, CELL); // 한 칸 이동에 필요한 픽셀
  // 가로 이동
  const dx = x - sw.x0;
  const targetCols = Math.trunc(dx / unit);
  while (sw.movedCols < targetCols) { if (game.moveRight()) { Sound.move(); Haptics.move(); sw.moved = true; } sw.movedCols++; }
  while (sw.movedCols > targetCols) { if (game.moveLeft()) { Sound.move(); Haptics.move(); sw.moved = true; } sw.movedCols--; }
  // 세로(아래)
  const dy = y - sw.y;
  if (dy > unit * 0.9) {
    const steps = Math.floor(dy / (unit * 0.9));
    for (let i = 0; i < steps; i++) { game.softDrop(); handleEvents(); sw.softCount++; sw.moved = true; }
    sw.y = y;
  }
  sw.x = x;
}
function onSwipeEnd(x, y) {
  if (!sw) return;
  const dt = performance.now() - sw.t0;
  const dy = y - sw.y0, dx = x - sw.x0;
  const unit = Math.max(18, CELL);
  // 빠르게 아래로 크게 쓸기 = 하드드롭(플릭)
  if (!sw.dropped && dy > unit * 2.2 && dt < 260 && Math.abs(dy) > Math.abs(dx)) {
    game.hardDrop(); handleEvents();
  } else if (!sw.moved && dt < 220 && Math.abs(dx) < unit * 0.6 && Math.abs(dy) < unit * 0.6) {
    // 짧은 탭 = 시계회전
    if (game.rotateCw()) { Sound.rotate(); Haptics.rotate(); }
  }
  sw = null;
}
boardCanvas.addEventListener('touchstart', (e) => { const t = e.touches[0]; onSwipeStart(t.clientX, t.clientY); e.preventDefault(); }, { passive: false });
boardCanvas.addEventListener('touchmove', (e) => { const t = e.touches[0]; onSwipeMove(t.clientX, t.clientY); e.preventDefault(); }, { passive: false });
boardCanvas.addEventListener('touchend', (e) => { const t = (e.changedTouches && e.changedTouches[0]) || {}; onSwipeEnd(t.clientX || sw?.x || 0, t.clientY || sw?.y || 0); }, { passive: false });
boardCanvas.addEventListener('touchcancel', () => { sw = null; });

/* ===== 메뉴/오버레이 버튼 ===== */
function togglePause() {
  if (!running || game.gameOver) return;
  paused = !paused;
  el('pauseOverlay').classList.toggle('hidden', !paused);
  if (paused) { BGM.stop(); }
  else { BGM.start(); lastTime = 0; requestAnimationFrame(loop); }
}
document.body.addEventListener('click', (e) => {
  const action = e.target.dataset && e.target.dataset.action;
  if (!action) return;
  switch (action) {
    case 'start': startGame(); break;
    case 'ranking': renderRanking(); showScreen('ranking'); break;
    case 'settings': syncSettingsUI(); showScreen('settings'); break;
    case 'toMenu': running = false; BGM.stop(); showScreen('menu'); break;
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
  el('setBgm').dataset.on = String(s.bgm); el('setBgm').textContent = s.bgm ? '켜짐' : '꺼짐';
  el('setBgmVol').value = Math.round(s.bgmVolume * 100); el('bgmVolLabel').textContent = Math.round(s.bgmVolume * 100) + '%';
  el('setHaptics').dataset.on = String(s.haptics); el('setHaptics').textContent = s.haptics ? '켜짐' : '꺼짐';
  el('setSwipe').dataset.on = String(s.swipe); el('setSwipe').textContent = s.swipe ? '켜짐' : '꺼짐';
  el('setBgDim').value = Math.round(s.bgDim * 100); el('bgDimLabel').textContent = Math.round(s.bgDim * 100) + '%';
  // 선택 상태 표시
  document.querySelectorAll('#schemeGrid .theme-btn').forEach(b => b.classList.toggle('sel', b.dataset.scheme === s.scheme));
  document.querySelectorAll('#subjectGrid .theme-btn').forEach(b => b.classList.toggle('sel', b.dataset.subject === s.subject));
}
el('setSound').addEventListener('click', () => { const s = STORE.loadSettings(); s.sound = !s.sound; STORE.saveSettings(s); Sound.settings.sound = s.sound; syncSettingsUI(); el('soundBtn').textContent = s.sound ? '🔊' : '🔇'; });
el('setTouch').addEventListener('click', () => { const s = STORE.loadSettings(); s.showTouch = !s.showTouch; STORE.saveSettings(s); syncSettingsUI(); });
el('setVolume').addEventListener('input', (e) => { const s = STORE.loadSettings(); s.volume = e.target.value / 100; STORE.saveSettings(s); Sound.settings.volume = s.volume; el('volLabel').textContent = e.target.value + '%'; });
el('setBgm').addEventListener('click', () => { const s = STORE.loadSettings(); s.bgm = !s.bgm; STORE.saveSettings(s); Sound.settings.bgm = s.bgm; syncSettingsUI(); BGM.refresh(); });
el('setBgmVol').addEventListener('input', (e) => { const s = STORE.loadSettings(); s.bgmVolume = e.target.value / 100; STORE.saveSettings(s); Sound.settings.bgmVolume = s.bgmVolume; BGM.setVolume(s.bgmVolume); el('bgmVolLabel').textContent = e.target.value + '%'; });
el('setHaptics').addEventListener('click', () => { const s = STORE.loadSettings(); s.haptics = !s.haptics; STORE.saveSettings(s); Sound.settings.haptics = s.haptics; syncSettingsUI(); if (s.haptics && navigator.vibrate) navigator.vibrate(20); });
el('setSwipe').addEventListener('click', () => { const s = STORE.loadSettings(); s.swipe = !s.swipe; STORE.saveSettings(s); Sound.settings.swipe = s.swipe; syncSettingsUI(); });
el('setBgDim').addEventListener('input', (e) => { const s = STORE.loadSettings(); s.bgDim = e.target.value / 100; STORE.saveSettings(s); ThemeMgr.setDim(s.bgDim); el('bgDimLabel').textContent = e.target.value + '%'; });

// 화면 색상(스킴) 버튼
(function buildSchemeButtons() {
  const wrap = el('schemeGrid'); if (!wrap) return;
  Object.entries(SCHEMES).forEach(([key, sc]) => {
    const b = document.createElement('button');
    b.className = 'theme-btn'; b.dataset.scheme = key; b.type = 'button';
    b.innerHTML = `<span class="sw" style="background:${sc.vars['--accent']}"></span><span class="sw2" style="background:${sc.boardBg}"></span><span class="tn">${sc.name}</span>`;
    b.addEventListener('click', () => {
      const s = STORE.loadSettings(); s.scheme = key; STORE.saveSettings(s);
      ThemeMgr.applyScheme(key); syncSettingsUI(); Haptics.tap();
    });
    wrap.appendChild(b);
  });
})();

// 배경 주제 버튼
(function buildSubjectButtons() {
  const wrap = el('subjectGrid'); if (!wrap) return;
  Object.entries(SUBJECTS).forEach(([key, sj]) => {
    const b = document.createElement('button');
    b.className = 'theme-btn'; b.dataset.subject = key; b.type = 'button';
    b.innerHTML = `<span class="ic">${sj.icon}</span><span class="tn">${sj.name}</span>`;
    b.addEventListener('click', () => {
      if (key === 'custom') { el('customImgInput').click(); return; }
      const s = STORE.loadSettings(); s.subject = key; STORE.saveSettings(s);
      ThemeMgr.applySubject(key); syncSettingsUI(); Haptics.tap();
    });
    wrap.appendChild(b);
  });
})();

// Custom 이미지 업로드 → 리사이즈 후 data URL로 저장(용량 절감)
el('customImgInput').addEventListener('change', (e) => {
  const file = e.target.files && e.target.files[0]; if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const img = new Image();
    img.onload = () => {
      // 긴 변 기준 1080px로 축소해 localStorage 용량 절감
      const maxSide = 1080; let w = img.width, h = img.height;
      if (Math.max(w, h) > maxSide) { const r = maxSide / Math.max(w, h); w = Math.round(w * r); h = Math.round(h * r); }
      const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
      cv.getContext('2d').drawImage(img, 0, 0, w, h);
      let dataUrl; try { dataUrl = cv.toDataURL('image/jpeg', 0.82); } catch { dataUrl = reader.result; }
      const ok = STORE.saveCustomImg(dataUrl);
      if (!ok) { alert('이미지가 너무 커서 저장하지 못했어요. 더 작은 이미지를 선택해 주세요.'); return; }
      const s = STORE.loadSettings(); s.subject = 'custom'; STORE.saveSettings(s);
      ThemeMgr.applySubject('custom', dataUrl); syncSettingsUI(); Haptics.tap();
    };
    img.onerror = () => alert('이미지를 불러오지 못했어요.');
    img.src = reader.result;
  };
  reader.readAsDataURL(file);
  e.target.value = '';
});

/* ===== PWA 설치 프롬프트 ===== */
let deferredPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); deferredPrompt = e; el('installBtn').classList.remove('hidden'); });
el('installBtn').addEventListener('click', async () => { if (!deferredPrompt) return; deferredPrompt.prompt(); await deferredPrompt.userChoice; deferredPrompt = null; el('installBtn').classList.add('hidden'); });

/* ===== 초기화 ===== */
window.addEventListener('resize', () => { if (el('game').classList.contains('active')) resizeBoard(); });
(function init() {
  const s = STORE.loadSettings();
  Sound.settings = s;
  ThemeMgr.customImg = STORE.loadCustomImg();
  ThemeMgr.dim = s.bgDim;
  ThemeMgr.applyScheme(s.scheme);
  ThemeMgr.applySubject(s.subject, ThemeMgr.customImg);
  el('soundBtn').textContent = s.sound ? '🔊' : '🔇';
  el('touchpad').classList.toggle('hidden', !s.showTouch);
  const vl = el('verLabel'); if (vl) vl.textContent = 'v' + VERSION;
  showScreen('menu');
})();

/* 테스트 훅: 로직 모듈을 전역에 노출 (headless 검증용) */
window.__TETRIS__ = { Board, Piece, SevenBag, Scorer, Game, cellsFor, tryRotate, canMove, lineScore, levelForLines, gravityIntervalMs, COLS, ROWS, TYPES, VERSION, SCHEMES, SUBJECTS };
