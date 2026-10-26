"""충돌·고정·7-bag·게임 상태 단위 테스트 — Pygame 없이 순수 로직만 검증한다."""

import importlib.util
import os
import random
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
sys.path.insert(0, SRC_DIR)

import collision  # noqa: E402
import piece as P  # noqa: E402
from board import COLS, Board  # noqa: E402
from game import Game  # noqa: E402
from piece import Piece  # noqa: E402
from sevenbag import SevenBag  # noqa: E402


def _no_pygame(mod_name):
    spec = importlib.util.find_spec(mod_name)
    src = open(spec.origin, encoding="utf-8").read()
    assert "pygame" not in src, f"{mod_name} 에 pygame 참조"


def test_modules_have_no_pygame():
    for m in ("collision", "game", "sevenbag"):
        _no_pygame(m)


# --- 충돌 검사 ---
def test_cells_valid_in_empty_board():
    b = Board()
    assert collision.cells_valid(b, [(0, 0), (5, 5), (b.total_rows - 1, b.cols - 1)])


def test_cells_invalid_out_of_bounds():
    b = Board()
    assert not collision.cells_valid(b, [(-1, 0)])
    assert not collision.cells_valid(b, [(0, -1)])
    assert not collision.cells_valid(b, [(0, b.cols)])
    assert not collision.cells_valid(b, [(b.total_rows, 0)])


def test_cells_invalid_overlap_filled():
    b = Board()
    b.set(5, 5, P.T)
    assert not collision.cells_valid(b, [(5, 5)])


def test_can_move_blocked_by_wall():
    b = Board()
    p = Piece(P.O, row=0, col=0)
    # O 셀은 col 1~2 사용 -> 왼쪽으로 1칸은 col 0~1, 아직 OK; 2칸은 음수 -> 불가
    assert collision.can_move(b, p, 0, -1)
    assert not collision.can_move(b, p, 0, -2)


def test_try_move_updates_only_on_success():
    b = Board()
    p = Piece(P.O, row=0, col=0)
    assert collision.try_move(b, p, 0, -1) is True
    assert p.col == -1
    assert collision.try_move(b, p, 0, -1) is False  # 벽
    assert p.col == -1  # 변하지 않음


# --- 고정 ---
def test_lock_piece_writes_cells():
    b = Board()
    p = Piece(P.O, row=3, col=3)
    collision.lock_piece(b, p)
    for r, c in p.board_cells():
        assert b.get(r, c) == P.O


# --- 벽차기 ---
def test_rotate_against_left_wall_does_not_pierce():
    """왼쪽 벽에 붙은 블록을 회전해도 보드를 뚫지 않는다(모든 셀 유효)."""
    b = Board()
    for t in P.TYPES:
        p = Piece(t, row=5, col=-1)  # 살짝 왼쪽으로 밀어 벽에 붙임
        # 유효 위치가 아니면 이 테스트 케이스는 건너뜀
        if not collision.piece_fits(b, p):
            p = Piece(t, row=5, col=0)
        before = p.rotation
        collision.try_rotate(b, p, +1)
        # 회전이 적용됐든 거부됐든, 결과 셀은 항상 보드 안에 있어야 한다
        assert collision.piece_fits(b, p), f"{P.TYPE_NAMES[t]} 회전 후 보드 밖"


def test_o_rotate_always_true():
    b = Board()
    p = Piece(P.O, row=5, col=4)
    assert collision.try_rotate(b, p, +1) is True


# --- 7-bag ---
def test_seven_bag_each_type_once_per_bag():
    bag = SevenBag(random.Random(42))
    first7 = [bag.next_type() for _ in range(7)]
    assert sorted(first7) == sorted(P.TYPES)
    second7 = [bag.next_type() for _ in range(7)]
    assert sorted(second7) == sorted(P.TYPES)


def test_seven_bag_peek_matches_next():
    bag = SevenBag(random.Random(7))
    preview = bag.peek(5)
    actual = [bag.next_type() for _ in range(5)]
    assert preview == actual


def test_seven_bag_not_overly_biased():
    """100봉지(700개)에서 각 타입이 정확히 100번씩 나와야 한다."""
    bag = SevenBag(random.Random(1))
    counts = {t: 0 for t in P.TYPES}
    for _ in range(700):
        counts[bag.next_type()] += 1
    assert all(v == 100 for v in counts.values())


# --- 게임 상태 ---
def test_game_spawns_current_piece():
    g = Game(random.Random(0))
    assert g.current is not None
    assert not g.game_over


def test_gravity_moves_piece_down():
    g = Game(random.Random(0))
    r0 = g.current.row
    g.step_gravity()
    assert g.current.row == r0 + 1


def test_hard_drop_locks_and_spawns_new():
    g = Game(random.Random(0))
    first = g.current
    dropped = g.hard_drop()
    assert dropped >= 0
    # 보드에 고정 흔적이 남고, 새 블록이 스폰됐다
    assert g.current is not first or g.game_over
    filled = sum(1 for r in range(g.board.total_rows)
                 for c in range(g.board.cols) if g.board.is_cell_filled(r, c))
    assert filled == 4  # 블록 하나가 고정됨


def test_soft_drop_eventually_locks():
    g = Game(random.Random(0))
    # 바닥까지 소프트드롭 반복
    safety = 0
    while g.soft_drop():
        safety += 1
        assert safety < 100
    # 고정 후 새 블록 스폰
    filled = sum(1 for r in range(g.board.total_rows)
                 for c in range(g.board.cols) if g.board.is_cell_filled(r, c))
    assert filled == 4


def test_game_over_when_spawn_blocked():
    g = Game(random.Random(0))
    # 스폰 영역을 '꽉 차지 않게' 채워(한 칸 비움) 라인 클리어 없이 스폰을 막는다
    for r in range(6):
        for c in range(1, g.board.cols):
            g.board.set(r, c, P.T)
    g.hard_drop()  # 현재 블록 고정 후 스폰 시도 -> 막힘
    assert g.game_over
