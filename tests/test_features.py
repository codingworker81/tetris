"""단계 5 기능(Next·Hold·고스트) 단위 테스트 — Pygame 없이 순수 로직만 검증한다."""

import os
import random
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
sys.path.insert(0, SRC_DIR)

import collision  # noqa: E402
import piece as P  # noqa: E402
from game import Game  # noqa: E402


# --- Next 미리보기 ---
def test_next_preview_matches_future_pieces():
    g = Game(random.Random(123))
    preview = g.next_types(3)
    assert len(preview) == 3
    # 현재 블록은 이미 꺼냈으므로, preview[0]이 다음 스폰될 타입이어야 한다
    first_next = preview[0]
    g.hard_drop()  # 현재 블록 고정 -> preview[0] 스폰
    assert g.current.type == first_next


def test_next_preview_non_destructive():
    g = Game(random.Random(1))
    a = g.next_types(5)
    b = g.next_types(5)
    assert a == b  # 미리보기는 상태를 바꾸지 않음


# --- Hold ---
def test_hold_into_empty_slot_takes_next():
    g = Game(random.Random(0))
    cur = g.current.type
    next_type = g.next_types(1)[0]
    ok = g.hold()
    assert ok is True
    assert g.hold_type == cur
    assert g.current.type == next_type  # 보관이 비었으므로 다음 블록이 나옴


def test_hold_blocked_twice_on_same_piece():
    g = Game(random.Random(0))
    assert g.hold() is True
    # 같은 블록(교체로 나온 블록)에서 두 번째 홀드는 막혀야 한다
    assert g.hold() is False


def test_hold_allowed_again_after_new_piece():
    g = Game(random.Random(0))
    assert g.hold() is True
    g.hard_drop()  # 새 블록 스폰 -> 홀드 플래그 리셋
    assert g.hold() is True


def test_hold_swaps_with_stored():
    g = Game(random.Random(2))
    first = g.current.type
    g.hold()                 # first 보관, 새 블록 A 등장
    a = g.current.type
    g.hard_drop()            # A 고정, 새 블록 B 등장 (홀드 리셋)
    b = g.current.type
    g.hold()                 # B<->first 교체
    assert g.hold_type == b
    assert g.current.type == first
    # 교체된 블록은 스폰 위치/회전으로 초기화
    assert g.current.rotation == 0


# --- 고스트 피스 ---
def test_ghost_matches_hard_drop_landing():
    g = Game(random.Random(7))
    ghost = set(g.ghost_cells())
    # 하드드롭 직전 블록 셀을 하드드롭 결과와 비교하기 위해 복제 상태로 계산
    # ghost는 '현재 블록이 떨어질 위치'이므로, 하드드롭 후 그 셀들이 보드에 채워져야 한다
    g.hard_drop()
    for (r, c) in ghost:
        assert g.board.is_cell_filled(r, c), f"ghost 셀 {(r, c)} 가 착지와 불일치"


def test_ghost_on_empty_board_is_at_bottom():
    g = Game(random.Random(0))
    ghost = g.ghost_cells()
    max_row = max(r for r, _ in ghost)
    # 바닥(마지막 행)에 닿아 있어야 한다
    assert max_row == g.board.total_rows - 1


def test_ghost_does_not_mutate_state():
    g = Game(random.Random(0))
    before = set(g.current.board_cells())
    g.ghost_cells()
    assert set(g.current.board_cells()) == before


def test_hold_resets_rotation_and_position():
    g = Game(random.Random(0))
    g.rotate_cw()
    g.move_left()
    g.hold()
    # 새로 나온 블록은 기본 스폰 상태여야 한다
    from game import SPAWN_COL
    assert g.current.rotation == 0
    assert g.current.col == SPAWN_COL


# --- 피드백 이벤트 신호 (단계 7) ---
def test_consume_events_signals_lock():
    g = Game(random.Random(0))
    g.hard_drop()
    cleared, level_up, locked = g.consume_events()
    assert locked is True
    # 소비 후 다시 읽으면 초기화되어 있어야 한다
    cleared2, level_up2, locked2 = g.consume_events()
    assert (cleared2, level_up2, locked2) == (0, False, False)


def test_consume_events_signals_line_clear():
    g = Game(random.Random(0))
    b = g.board
    last = b.total_rows - 1
    for c in range(1, b.cols):
        b.set(last, c, P.T)
    from piece import I, Piece
    g.current = Piece(I, row=0, col=0, rotation=1)
    while g.move_left():
        pass
    g.hard_drop()
    cleared, _level_up, locked = g.consume_events()
    assert locked is True
    assert cleared >= 1
