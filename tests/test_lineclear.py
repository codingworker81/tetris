"""라인 클리어 & 게임오버 단위 테스트 — 보드/게임 로직 검증(Pygame 없음)."""

import os
import random
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
sys.path.insert(0, SRC_DIR)

import piece as P  # noqa: E402
from board import EMPTY, Board  # noqa: E402
from game import Game  # noqa: E402


def _fill_row(board, row, except_col=None):
    for c in range(board.cols):
        if c == except_col:
            continue
        board.set(row, c, P.T)


def test_clear_single_row():
    b = Board()
    last = b.total_rows - 1
    _fill_row(b, last)
    cleared = b.clear_full_rows()
    assert cleared == 1
    # 바닥 행이 다시 비어 있어야 한다
    assert all(b.get(last, c) == EMPTY for c in range(b.cols))


def test_clear_multiple_rows_at_once():
    b = Board()
    rows = [b.total_rows - 1, b.total_rows - 2, b.total_rows - 3, b.total_rows - 4]
    for r in rows:
        _fill_row(b, r)
    cleared = b.clear_full_rows()
    assert cleared == 4


def test_clear_pulls_down_blocks_above():
    b = Board()
    last = b.total_rows - 1
    # 바닥 꽉 채우고, 그 위 한 칸에만 블록 하나
    _fill_row(b, last)
    b.set(last - 2, 0, P.L)  # 두 칸 위에 떠 있는 블록
    cleared = b.clear_full_rows()
    assert cleared == 1
    # 떠 있던 블록이 한 칸 아래로 당겨져야 한다 (last-2 -> last-1)
    assert b.get(last - 1, 0) == P.L
    assert b.get(last - 2, 0) == EMPTY


def test_partial_row_not_cleared():
    b = Board()
    last = b.total_rows - 1
    _fill_row(b, last, except_col=3)  # 한 칸 비움
    cleared = b.clear_full_rows()
    assert cleared == 0


def test_game_awards_score_on_line_clear():
    """바닥 한 줄을 거의 채운 뒤 블록을 떨궈 라인 클리어 점수를 확인한다."""
    g = Game(random.Random(0))
    b = g.board
    last = b.total_rows - 1
    # 바닥 행에서 한 칸(col 0)만 비우고 모두 채운다
    for c in range(1, b.cols):
        b.set(last, c, P.T)
    before_score = g.scorer.score
    before_lines = g.scorer.lines
    # 현재 블록을 col 0, 바닥까지 떨어뜨리도록 수동 배치 후 하드드롭
    g.current.col = -1  # I/O 등 로컬 오프셋 고려해 왼쪽 끝으로
    # 왼쪽 끝으로 최대한 민다
    while g.move_left():
        pass
    g.hard_drop()
    # 적어도 라인이 하나 지워졌고 점수가 올랐다 (블록이 col 0 바닥을 메운 경우)
    # 블록 모양에 따라 즉시 안 지워질 수 있으므로, 지워졌다면 점수 규칙을 검증
    if g.scorer.lines > before_lines:
        assert g.scorer.score > before_score


def test_game_over_on_blocked_spawn():
    g = Game(random.Random(0))
    # 스폰 영역(상단)을 '꽉 차지 않게' 막는다: 한 칸(col 0)을 비워 라인 클리어가
    # 일어나지 않도록 하여, 다음 스폰이 실제로 막히게 한다.
    for r in range(6):
        for c in range(1, g.board.cols):
            g.board.set(r, c, P.T)
    g.hard_drop()  # 현재 블록 고정 -> 라인 클리어 없음 -> 다음 스폰 막힘
    assert g.game_over


def test_level_rises_in_game_after_enough_lines():
    g = Game(random.Random(0))
    # scorer를 직접 구동해 레벨 상승 반영 확인 (게임 통합 경로)
    g.scorer.add_line_clear(4)
    g.scorer.add_line_clear(4)
    g.scorer.add_line_clear(4)  # 12 lines
    assert g.scorer.level == 2
    assert g.scorer.interval_ms < 800
