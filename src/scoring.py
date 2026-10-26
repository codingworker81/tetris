"""점수 · 레벨 · 낙하 속도 — Pygame과 분리된 순수 파이썬 모듈.

점수 규칙(가이드라인 기반):
- 라인 클리어: Single 100, Double 300, Triple 500, Tetris 800 (각각 현재 레벨 N 배수).
- 소프트드롭: 내려간 칸당 +1.
- 하드드롭: 내려간 칸당 +2.
레벨: 누적 라인 10개마다 +1. 레벨이 오르면 낙하 간격(ms)이 짧아진다.
"""

from __future__ import annotations

# 라인 수 -> 기본 점수 (레벨 1 기준). 레벨 N이면 N을 곱한다.
LINE_BASE_SCORE = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}

LINES_PER_LEVEL = 10

# 레벨별 중력 간격(ms). 레벨이 오를수록 짧아진다(=빨라진다).
# 고전 테트리스 느낌의 완만한 곡선. 상한/하한을 둔다.
_BASE_INTERVAL_MS = 800
_MIN_INTERVAL_MS = 60


def line_score(lines: int, level: int) -> int:
    """지운 줄 수와 현재 레벨로 라인 클리어 점수를 계산한다."""
    if lines not in LINE_BASE_SCORE:
        raise ValueError(f"지원하지 않는 라인 수: {lines}")
    return LINE_BASE_SCORE[lines] * level


def soft_drop_score(cells: int) -> int:
    """소프트드롭으로 내려간 칸당 +1."""
    return max(0, cells)


def hard_drop_score(cells: int) -> int:
    """하드드롭으로 내려간 칸당 +2."""
    return max(0, cells) * 2


def level_for_lines(total_lines: int) -> int:
    """누적 라인 수로 현재 레벨을 계산한다(레벨 1부터 시작)."""
    return 1 + total_lines // LINES_PER_LEVEL


def gravity_interval_ms(level: int) -> int:
    """레벨에 따른 중력 간격(ms). 레벨이 오를수록 짧아진다."""
    # 레벨 1에서 800ms, 레벨당 약 15%씩 단축, 최소 60ms.
    interval = _BASE_INTERVAL_MS * (0.85 ** (level - 1))
    return max(_MIN_INTERVAL_MS, int(interval))


class Scorer:
    """한 판의 점수/라인/레벨 상태를 누적 관리한다."""

    def __init__(self) -> None:
        self.score = 0
        self.lines = 0          # 누적 지운 라인 수
        self.level = 1

    def add_line_clear(self, cleared: int) -> int:
        """지운 줄 수를 반영해 점수·라인·레벨을 갱신한다. 추가된 점수를 반환."""
        gained = line_score(cleared, self.level)
        self.score += gained
        self.lines += cleared
        self.level = level_for_lines(self.lines)
        return gained

    def add_soft_drop(self, cells: int) -> None:
        self.score += soft_drop_score(cells)

    def add_hard_drop(self, cells: int) -> None:
        self.score += hard_drop_score(cells)

    @property
    def interval_ms(self) -> int:
        return gravity_interval_ms(self.level)
