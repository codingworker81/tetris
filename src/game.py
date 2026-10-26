"""게임 상태 머신 — Pygame과 분리된 순수 파이썬 모듈.

보드 + 7-bag + 현재 블록을 하나로 묶어, 중력 낙하와 플레이어 조작(이동/회전/드롭),
고정(lock)과 다음 블록 스폰을 처리한다. 렌더링/입력 자체는 포함하지 않는다.

단계 3: 낙하·이동·충돌·고정·벽차기·7-bag. 단계 4: 라인클리어·점수·레벨·게임오버.
단계 5: Next 미리보기·Hold(블록당 1회)·고스트 피스 착지 위치.
"""

from __future__ import annotations

import random

import collision
from board import COLS, SPAWN_BUFFER, Board
from piece import Piece
from scoring import Scorer
from sevenbag import SevenBag

SPAWN_COL = (COLS - 4) // 2  # 4x4 박스 기준 중앙 정렬


class Game:
    """테트리스 한 판의 핵심 상태."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self.board = Board()
        self.bag = SevenBag(rng)
        self.scorer = Scorer()
        self.current: Piece | None = None
        self.hold_type: int | None = None   # 보관 중인 블록 타입
        self.hold_used = False               # 현재 블록에서 이미 홀드했는지
        self.game_over = False
        # 렌더/오디오 피드백용 1프레임 이벤트 신호
        self.last_cleared = 0                # 직전 lock에서 지운 줄 수
        self.last_level_up = False           # 직전 lock에서 레벨이 올랐는지
        self.last_locked = False             # 직전에 블록이 고정됐는지
        self._spawn_next()

    # --- 스폰 ---
    def _new_piece(self, piece_type: int) -> Piece:
        return Piece(piece_type, row=0, col=SPAWN_COL, rotation=0)

    def _spawn_next(self) -> None:
        """다음 블록을 7-bag에서 꺼내 스폰한다."""
        self._spawn_type(self.bag.next_type())

    def _spawn_type(self, piece_type: int) -> None:
        """지정한 타입을 스폰 위치에 올린다. 올릴 수 없으면 게임오버."""
        piece = self._new_piece(piece_type)
        self.hold_used = False  # 새 블록이 나오면 홀드 다시 가능
        if not collision.piece_fits(self.board, piece):
            self.current = piece
            self.game_over = True
            return
        self.current = piece

    # --- Next 미리보기 ---
    def next_types(self, count: int = 3) -> list[int]:
        """다음에 나올 블록 타입 count개를 비파괴적으로 반환."""
        return self.bag.peek(count)

    # --- Hold ---
    def hold(self) -> bool:
        """현재 블록을 보관/교체한다. 블록당 1회만 허용. 성공 시 True.

        - 보관이 비어 있으면: 현재 블록을 보관하고 다음 블록을 스폰.
        - 보관이 차 있으면: 보관 블록과 현재 블록을 맞교체(스폰 위치/회전 초기화).
        """
        if self.game_over or self.current is None or self.hold_used:
            return False
        cur_type = self.current.type
        if self.hold_type is None:
            self.hold_type = cur_type
            self._spawn_next()
        else:
            swap = self.hold_type
            self.hold_type = cur_type
            self._spawn_type(swap)
        self.hold_used = True
        return True

    # --- 고스트 피스 ---
    def ghost_cells(self) -> list[tuple[int, int]]:
        """현재 블록이 하드드롭될 착지 위치의 보드 셀을 반환(상태 불변)."""
        if self.current is None:
            return []
        drop = 0
        while collision.can_move(self.board, self.current, drop + 1, 0):
            drop += 1
        return [(r + drop, c) for r, c in self.current.board_cells()]

    # --- 플레이어 조작 ---
    def move_left(self) -> bool:
        if self.game_over or self.current is None:
            return False
        return collision.try_move(self.board, self.current, 0, -1)

    def move_right(self) -> bool:
        if self.game_over or self.current is None:
            return False
        return collision.try_move(self.board, self.current, 0, +1)

    def rotate_cw(self) -> bool:
        if self.game_over or self.current is None:
            return False
        return collision.try_rotate(self.board, self.current, +1)

    def rotate_ccw(self) -> bool:
        if self.game_over or self.current is None:
            return False
        return collision.try_rotate(self.board, self.current, -1)

    def soft_drop(self) -> bool:
        """한 칸 아래로. 내려가면 True, 바닥에 닿아 고정됐으면 False."""
        if self.game_over or self.current is None:
            return False
        if collision.try_move(self.board, self.current, +1, 0):
            self.scorer.add_soft_drop(1)
            return True
        self._lock_and_spawn()
        return False

    def hard_drop(self) -> int:
        """더 내려갈 수 없을 때까지 떨어뜨리고 즉시 고정. 내려간 칸 수 반환."""
        if self.game_over or self.current is None:
            return 0
        dropped = 0
        while collision.try_move(self.board, self.current, +1, 0):
            dropped += 1
        self.scorer.add_hard_drop(dropped)
        self._lock_and_spawn()
        return dropped

    def step_gravity(self) -> None:
        """중력 1틱: 한 칸 하강 시도, 못 내려가면 고정 후 다음 블록."""
        if self.game_over or self.current is None:
            return
        if not collision.try_move(self.board, self.current, +1, 0):
            self._lock_and_spawn()

    def _lock_and_spawn(self) -> None:
        assert self.current is not None
        collision.lock_piece(self.board, self.current)
        level_before = self.scorer.level
        cleared = self.board.clear_full_rows()
        if cleared:
            self.scorer.add_line_clear(cleared)
        # 피드백 이벤트 신호 설정
        self.last_cleared = cleared
        self.last_level_up = self.scorer.level > level_before
        self.last_locked = True
        self._spawn_next()

    def consume_events(self) -> tuple[int, bool, bool]:
        """1프레임 피드백 이벤트를 읽고 초기화한다. (지운 줄 수, 레벨업, 고정)."""
        ev = (self.last_cleared, self.last_level_up, self.last_locked)
        self.last_cleared = 0
        self.last_level_up = False
        self.last_locked = False
        return ev
