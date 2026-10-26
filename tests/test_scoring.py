"""점수·레벨·낙하속도 단위 테스트 — Pygame 없이 순수 로직만 검증한다."""

import importlib.util
import os
import sys

import pytest

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
sys.path.insert(0, SRC_DIR)

import scoring  # noqa: E402
from scoring import (  # noqa: E402
    Scorer,
    gravity_interval_ms,
    hard_drop_score,
    level_for_lines,
    line_score,
    soft_drop_score,
)


def test_scoring_has_no_pygame():
    spec = importlib.util.find_spec("scoring")
    src = open(spec.origin, encoding="utf-8").read()
    assert "pygame" not in src


def test_line_score_at_level_1():
    assert line_score(1, 1) == 100
    assert line_score(2, 1) == 300
    assert line_score(3, 1) == 500
    assert line_score(4, 1) == 800
    assert line_score(0, 1) == 0


def test_line_score_scales_with_level():
    assert line_score(1, 3) == 300
    assert line_score(4, 5) == 4000


def test_invalid_line_count_raises():
    with pytest.raises(ValueError):
        line_score(5, 1)


def test_drop_scores():
    assert soft_drop_score(7) == 7
    assert hard_drop_score(7) == 14
    assert soft_drop_score(0) == 0
    assert hard_drop_score(-3) == 0  # 음수 방어


def test_level_for_lines():
    assert level_for_lines(0) == 1
    assert level_for_lines(9) == 1
    assert level_for_lines(10) == 2
    assert level_for_lines(25) == 3


def test_gravity_speeds_up_with_level():
    i1 = gravity_interval_ms(1)
    i5 = gravity_interval_ms(5)
    i20 = gravity_interval_ms(20)
    assert i1 > i5 > i20
    assert i1 == 800
    assert i20 >= 60  # 하한


def test_scorer_accumulates():
    s = Scorer()
    s.add_line_clear(1)      # 100 * level 1
    assert s.score == 100
    assert s.lines == 1
    assert s.level == 1
    s.add_soft_drop(5)       # +5
    s.add_hard_drop(3)       # +6
    assert s.score == 111


def test_scorer_level_up_after_10_lines():
    s = Scorer()
    s.add_line_clear(4)      # +800 @lv1, 4 lines
    s.add_line_clear(4)      # +800 @lv1, 8 lines
    s.add_line_clear(2)      # +300 @lv1 (Double=300), 10 lines -> level 2
    assert s.lines == 10
    assert s.level == 2
    assert s.score == 1900
    # 레벨 2에서 트리플은 500*2 = 1000
    before = s.score
    s.add_line_clear(3)
    assert s.score - before == 1000


def test_scorer_interval_property_tracks_level():
    s = Scorer()
    assert s.interval_ms == gravity_interval_ms(1)
    for _ in range(3):
        s.add_line_clear(4)  # 12 lines -> level 2
    assert s.level == 2
    assert s.interval_ms == gravity_interval_ms(2)
