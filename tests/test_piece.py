"""Piece/테트로미노 단위 테스트 — Pygame 없이 순수 로직만 검증한다."""

import importlib.util
import os
import sys

import pytest

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
sys.path.insert(0, SRC_DIR)

import piece as P  # noqa: E402
from piece import COLORS, SHAPES, TYPES, Piece, cells_for  # noqa: E402


def test_piece_import_has_no_pygame():
    spec = importlib.util.find_spec("piece")
    assert spec is not None
    source = open(spec.origin, encoding="utf-8").read()
    assert "pygame" not in source


def test_seven_types_defined():
    assert len(TYPES) == 7
    assert set(TYPES) == {P.I, P.O, P.T, P.S, P.Z, P.J, P.L}


def test_every_type_has_four_rotations_of_four_cells():
    for t in TYPES:
        rotations = SHAPES[t]
        assert len(rotations) == 4, f"{P.TYPE_NAMES[t]} 회전 상태가 4개가 아님"
        for rot in rotations:
            assert len(rot) == 4, f"{P.TYPE_NAMES[t]} 셀이 4개가 아님"
            # 중복 셀 없음
            assert len(set(rot)) == 4, f"{P.TYPE_NAMES[t]} 셀 중복"


def test_every_type_has_distinct_color():
    for t in TYPES:
        assert t in COLORS
        assert len(COLORS[t]) == 3
    # 7색 모두 서로 다름
    assert len({COLORS[t] for t in TYPES}) == 7


def test_o_piece_rotation_invariant():
    """O블록은 어떤 회전 상태에서도 셀 집합이 동일해야 한다."""
    base = set(cells_for(P.O, 0))
    for rot in range(4):
        assert set(cells_for(P.O, rot)) == base


def test_i_piece_alternates_horizontal_vertical():
    """I블록: 0/2 상태는 가로(모든 셀 같은 row), 1/3은 세로(모든 셀 같은 col)."""
    for rot in (0, 2):
        rows = {r for r, _ in cells_for(P.I, rot)}
        assert len(rows) == 1, f"I rot {rot} 가 가로가 아님"
    for rot in (1, 3):
        cols = {c for _, c in cells_for(P.I, rot)}
        assert len(cols) == 1, f"I rot {rot} 가 세로가 아님"


def test_rotation_cycles_back_cw():
    p = Piece(P.T)
    start = set(p.board_cells())
    for _ in range(4):
        p.rotate_cw()
    assert set(p.board_cells()) == start
    assert p.rotation == 0


def test_rotation_cycles_back_ccw():
    p = Piece(P.J)
    start = set(p.board_cells())
    for _ in range(4):
        p.rotate_ccw()
    assert set(p.board_cells()) == start
    assert p.rotation == 0


def test_cw_then_ccw_restores():
    for t in TYPES:
        p = Piece(t)
        before = set(p.board_cells())
        p.rotate_cw()
        p.rotate_ccw()
        assert set(p.board_cells()) == before, f"{P.TYPE_NAMES[t]} CW->CCW 불일치"


def test_board_cells_apply_position():
    p = Piece(P.T, row=5, col=3)
    local = cells_for(P.T, 0)
    expected = {(5 + r, 3 + c) for r, c in local}
    assert set(p.board_cells()) == expected


def test_rotated_cells_does_not_mutate_state():
    p = Piece(P.S, row=2, col=2)
    rot_before = p.rotation
    preview = p.rotated_cells(+1)
    assert p.rotation == rot_before  # 미리보기는 상태를 바꾸지 않음
    p.rotate_cw()
    assert set(p.board_cells()) == set(preview)


def test_s_and_z_distinct():
    """S와 Z는 스폰 모양이 서로 달라야 한다 (거울상)."""
    assert set(cells_for(P.S, 0)) != set(cells_for(P.Z, 0))


def test_each_rotation_stays_within_4x4():
    for t in TYPES:
        for rot in range(4):
            for r, c in cells_for(t, rot):
                assert 0 <= r < 4 and 0 <= c < 4, f"{P.TYPE_NAMES[t]} rot {rot} 범위 초과"


def test_color_and_name_properties():
    p = Piece(P.L)
    assert p.color == COLORS[P.L]
    assert p.name == "L"


def test_unknown_type_raises():
    with pytest.raises(ValueError):
        Piece(99)
    with pytest.raises(ValueError):
        cells_for(99, 0)
