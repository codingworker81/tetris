"""Board 모델 단위 테스트 — Pygame 없이 순수 로직만 검증한다."""

import importlib.util
import os
import sys

import pytest

# src/ 를 import 경로에 추가 (패키지 설정 없이 단독 모듈 import)
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
sys.path.insert(0, SRC_DIR)

from board import COLS, EMPTY, ROWS, SPAWN_BUFFER, Board  # noqa: E402


def test_board_import_has_no_pygame():
    """board.py 는 pygame import 없이 단독으로 import 되어야 한다."""
    spec = importlib.util.find_spec("board")
    assert spec is not None
    source = open(spec.origin, encoding="utf-8").read()
    assert "import pygame" not in source
    assert "pygame" not in source


def test_empty_board_dimensions():
    b = Board()
    assert b.cols == COLS == 10
    assert b.visible_row_count == ROWS == 20
    assert b.spawn_buffer == SPAWN_BUFFER
    assert b.total_rows == ROWS + SPAWN_BUFFER


def test_empty_board_all_empty():
    b = Board()
    for row in range(b.total_rows):
        for col in range(b.cols):
            assert b.get(row, col) == EMPTY
            assert b.is_empty(row, col) is True
            assert b.is_cell_filled(row, col) is False


def test_visible_rows_shape():
    b = Board()
    vis = b.visible_rows()
    assert len(vis) == ROWS
    assert all(len(r) == COLS for r in vis)


def test_set_and_get_cell():
    b = Board()
    b.set(5, 3, 7)
    assert b.get(5, 3) == 7
    assert b.is_cell_filled(5, 3) is True
    assert b.is_empty(5, 3) is False


def test_in_bounds():
    b = Board()
    assert b.in_bounds(0, 0) is True
    assert b.in_bounds(b.total_rows - 1, b.cols - 1) is True
    assert b.in_bounds(-1, 0) is False
    assert b.in_bounds(0, -1) is False
    assert b.in_bounds(b.total_rows, 0) is False
    assert b.in_bounds(0, b.cols) is False


def test_out_of_bounds_get_raises():
    b = Board()
    with pytest.raises(IndexError):
        b.get(-1, 0)
    with pytest.raises(IndexError):
        b.get(0, b.cols)
    with pytest.raises(IndexError):
        b.get(b.total_rows, 0)


def test_out_of_bounds_set_raises():
    b = Board()
    with pytest.raises(IndexError):
        b.set(b.total_rows, 0, 1)


def test_out_of_bounds_is_empty_is_false():
    """경계 밖은 '막힘'으로 간주 — 충돌 판정에서 False(비어있지 않음)로 다룬다."""
    b = Board()
    assert b.is_empty(-1, 0) is False
    assert b.is_empty(0, -1) is False
    assert b.is_empty(b.total_rows, 0) is False
    assert b.is_cell_filled(-1, 0) is False  # 밖은 채워진 것도 아님


def test_is_row_full():
    b = Board()
    assert b.is_row_full(0) is False
    for c in range(b.cols):
        b.set(10, c, 1)
    assert b.is_row_full(10) is True


def test_clear_resets_board():
    b = Board()
    b.set(5, 5, 3)
    b.clear()
    assert b.get(5, 5) == EMPTY


def test_invalid_dimensions_raise():
    with pytest.raises(ValueError):
        Board(cols=0)
    with pytest.raises(ValueError):
        Board(visible_rows=0)
    with pytest.raises(ValueError):
        Board(spawn_buffer=-1)
