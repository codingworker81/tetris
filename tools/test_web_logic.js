/* 웹 포팅 로직 headless 검증 (Node) — PC pytest 기대값과 1:1 대조.
 * tetris.js는 브라우저 전역(window/document)에 의존하므로, 최소 shim을 주입해
 * 로직부만 로드한 뒤 window.__TETRIS__를 꺼내 검증한다.
 * 실행: node tools/test_web_logic.js  (tetris 폴더에서)
 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

// --- 브라우저 API 최소 shim (로직 로드만 목적; DOM 동작은 noop) ---
function fakeEl() {
  return new Proxy(function () {}, {
    get() { return fakeEl(); },
    apply() { return fakeEl(); },
    set() { return true; },
  });
}
const noopEl = { classList: { add() {}, remove() {}, toggle() {} }, dataset: {}, addEventListener() {}, getContext() { return fakeEl(); }, textContent: '', value: '', height: 0, width: 0, clientHeight: 480, clientWidth: 360, offsetWidth: 80, innerHTML: '', appendChild() {}, setAttribute() {}, getAttribute() { return ''; }, click() {}, style: { setProperty() {} }, files: [] };
const documentShim = {
  getElementById: () => noopEl,
  querySelector: () => ({ clientHeight: 480, clientWidth: 360, offsetWidth: 80, setAttribute() {}, getAttribute() { return ''; }, style: { setProperty() {} } }),
  querySelectorAll: () => [],
  createElement: () => Object.assign({}, noopEl, { classList: { add() {}, remove() {}, toggle() {} }, dataset: {}, style: { setProperty() {} }, addEventListener() {}, appendChild() {}, getContext() { return fakeEl(); }, toDataURL() { return ''; } }),
  documentElement: { style: { setProperty() {} } },
  addEventListener() {}, body: { addEventListener() {} },
};
function AudioStub() {
  this.state = 'running';
  this.resume = function () {};
  this.currentTime = 0;
  this.createOscillator = function () { return { connect() {}, start() {}, stop() {}, frequency: {}, type: '' }; };
  this.createGain = function () { return { connect() {}, disconnect() {}, gain: { value: 0, setValueAtTime() {}, exponentialRampToValueAtTime() {} } }; };
}
const windowShim = { addEventListener() {}, AudioContext: AudioStub };
const localStorageShim = (() => { const m = {}; return { getItem: k => (k in m ? m[k] : null), setItem: (k, v) => { m[k] = String(v); }, removeItem: k => { delete m[k]; } }; })();

const sandbox = {
  window: windowShim, document: documentShim, localStorage: localStorageShim,
  navigator: { vibrate() { return true; } },
  performance: { now: () => 0 },
  alert() {}, FileReader: function () { this.readAsDataURL = function () {}; }, Image: function () {},
  requestAnimationFrame: () => 0, setTimeout: () => 0, setInterval: () => 0, clearInterval: () => 0, clearTimeout: () => 0,
  console,
};
sandbox.window.webkitAudioContext = sandbox.window.AudioContext;
sandbox.window.localStorage = localStorageShim;
vm.createContext(sandbox);

const docsPath = path.join(__dirname, '..', 'docs', 'tetris.js');
const webPath = path.join(__dirname, '..', 'web', 'tetris.js');
const srcPath = fs.existsSync(docsPath) ? docsPath : webPath;
const code = fs.readFileSync(srcPath, 'utf8');
vm.runInContext(code, sandbox, { filename: 'tetris.js' });

const API = sandbox.window.__TETRIS__;
if (!API) { console.error('FAIL: __TETRIS__ not exposed'); process.exit(2); }

// --- 테스트 유틸 ---
let pass = 0, fail = 0; const fails = [];
function ok(name, cond) { if (cond) { pass++; } else { fail++; fails.push(name); } }
function eq(name, a, b) { ok(name + ` (got ${JSON.stringify(a)} want ${JSON.stringify(b)})`, JSON.stringify(a) === JSON.stringify(b)); }

const { Board, Piece, SevenBag, Scorer, Game, cellsFor, tryRotate, canMove, lineScore, levelForLines, gravityIntervalMs, COLS, ROWS, TYPES } = API;

// 1) 보드 치수
eq('board cols', COLS, 10); eq('board rows', ROWS, 20);
const b = new Board(); eq('board totalRows', b.totalRows, 22);

// 2) 7-bag: 7개마다 각 타입 정확히 1번
const bag = new SevenBag(); const first7 = []; for (let i = 0; i < 7; i++) first7.push(bag.nextType());
eq('7bag unique in first 7', new Set(first7).size, 7);
ok('7bag all valid types', first7.every(t => TYPES.includes(t)));
// peek 비파괴성
const pk = bag.peek(3); const taken = [bag.nextType(), bag.nextType(), bag.nextType()];
eq('7bag peek matches next', pk, taken);

// 3) 점수 (scoring.py 기대값)
eq('single lv1', lineScore(1, 1), 100);
eq('double lv1', lineScore(2, 1), 300);
eq('triple lv1', lineScore(3, 1), 500);
eq('tetris lv1', lineScore(4, 1), 800);
eq('tetris lv3', lineScore(4, 3), 2400);
eq('level for 0 lines', levelForLines(0), 1);
eq('level for 10 lines', levelForLines(10), 2);
eq('level for 25 lines', levelForLines(25), 3);
eq('gravity lv1', gravityIntervalMs(1), 800);
ok('gravity decreases', gravityIntervalMs(5) < gravityIntervalMs(1));
ok('gravity floor 60', gravityIntervalMs(99) === 60);

// 4) Scorer 누적
const sc = new Scorer(); sc.addLineClear(4); eq('scorer tetris', sc.score, 800); eq('scorer lines', sc.lines, 4);
sc.addHardDrop(5); eq('scorer harddrop +10', sc.score, 810);
sc.addSoftDrop(3); eq('scorer softdrop +3', sc.score, 813);

// 5) 회전/벽차기: O는 항상 성공, I 세로 전환
const bo = new Board(); const oPiece = new Piece(2, 5, 3, 0);
ok('O rotate always true', tryRotate(bo, oPiece, 1) === true);
const iPiece = new Piece(1, 5, 3, 0); const r0 = iPiece.rotation;
ok('I rotate cw changes state', tryRotate(bo, iPiece, 1) && iPiece.rotation === 1);

// 6) 라인 클리어: 맨 아랫줄을 꽉 채우면 1줄 삭제
const bc = new Board();
for (let c = 0; c < COLS; c++) bc.set(bc.totalRows - 1, c, 1);
eq('clear one full row', bc.clearFullRows(), 1);
eq('after clear bottom empty', bc.grid[bc.totalRows - 1].every(v => v === 0), true);

// 7) 게임: 스폰 정상, 하드드롭으로 바닥 고정 후 새 블록
const g = new Game(); ok('game spawns current', g.current !== null); ok('game not over at start', g.gameOver === false);
const beforeType = g.current.type; g.hardDrop();
ok('after harddrop new current exists', g.current !== null);
ok('something locked on board', g.board.grid.some(row => row.some(v => v !== 0)));

// 8) Hold: 첫 홀드는 보관+새 블록, 같은 블록 2연속 홀드 불가
const g2 = new Game(); const t0 = g2.current.type; ok('first hold ok', g2.hold() === true); eq('hold stored', g2.holdType, t0);
ok('second hold blocked (holdUsed)', g2.hold() === false);

// 9) 게임오버: 스폰 영역을 '부분적으로' 막아(꽉 찬 줄이 아니게) 다음 스폰이 실패하게 한다
const g3 = new Game();
// 보이는 영역 상단부터 스폰 버퍼까지 col 0만 비우고 나머지를 채움 → 라인클리어 안 되면서 스폰 자리 막힘
for (let r = 0; r < g3.board.totalRows; r++) for (let c = 1; c < COLS; c++) g3.board.set(r, c, 1);
// 현재 블록을 강제로 바닥까지 떨어뜨려 고정시키면 다음 스폰이 막힌 영역과 겹쳐 실패
let guard = 0;
while (!g3.gameOver && guard++ < 50) g3.hardDrop();
ok('game over when spawn area blocked', g3.gameOver === true);

// 10) v1.1 메타데이터: 버전·스킴(2종)·배경 주제 세트
const { VERSION, SCHEMES, SUBJECTS } = API;
eq('version is 1.1.12', VERSION, '1.1.12');
eq('schemes are midnight+light only', Object.keys(SCHEMES).sort(), ['light', 'midnight']);
ok('subjects include none/custom/city', ['none','animal','anime','flower','city','nature','custom'].every(k => k in SUBJECTS));

console.log(`\n== 웹 로직 검증 결과 ==\nPASS: ${pass}  FAIL: ${fail}`);
if (fail) { console.log('실패 항목:'); fails.forEach(f => console.log('  - ' + f)); process.exit(1); }
console.log('모든 포팅 로직 검증 통과 ✅');
