"""테트로미노 정의 & 회전 — Pygame과 분리된 순수 파이썬 모듈.

7종 블록(I, O, T, S, Z, J, L)을 SRS(Super Rotation System) 기준의 스폰 모양과
4개 회전 상태로 정의한다. 각 셀 좌표는 블록의 로컬 (row, col) 오프셋이며,
row는 아래로, col은 오른쪽으로 증가한다 (board.py와 동일한 좌표계).

회전 상태 인덱스:
  0 = 스폰(기본), 1 = 시계 90도(R), 2 = 180도, 3 = 반시계 90도(L).

이 단계에서는 보드 충돌/벽차기를 다루지 않는다 — 모양과 회전만 정확히 정의한다.
"""

from __future__ import annotations

# --- 타입 코드 (board 셀 값으로도 사용: 1~7) ---
I, O, T, S, Z, J, L = 1, 2, 3, 4, 5, 6, 7

TYPES = (I, O, T, S, Z, J, L)
TYPE_NAMES = {I: "I", O: "O", T: "T", S: "S", Z: "Z", J: "J", L: "L"}

# --- 색상 (RGB) — 표준 테트리스 가이드라인 색 ---
COLORS = {
    I: (0, 240, 240),    # 시안
    O: (240, 240, 0),    # 노랑
    T: (160, 0, 240),    # 보라
    S: (0, 240, 0),      # 초록
    Z: (240, 0, 0),      # 빨강
    J: (0, 0, 240),      # 파랑
    L: (240, 160, 0),    # 주황
}

# --- 각 블록의 4개 회전 상태별 셀 (row, col) 오프셋 ---
# SRS 기준. I와 O는 가이드라인 관례를 따른다.
SHAPES: dict[int, list[list[tuple[int, int]]]] = {
    # I: 4x4 박스 안에서 수평<->수직
    I: [
        [(1, 0), (1, 1), (1, 2), (1, 3)],   # 0: 가로
        [(0, 2), (1, 2), (2, 2), (3, 2)],   # 1: 세로(오른쪽 열)
        [(2, 0), (2, 1), (2, 2), (2, 3)],   # 2: 가로(아래)
        [(0, 1), (1, 1), (2, 1), (3, 1)],   # 3: 세로(왼쪽 열)
    ],
    # O: 회전해도 모양 불변 (2x2)
    O: [
        [(0, 1), (0, 2), (1, 1), (1, 2)],
        [(0, 1), (0, 2), (1, 1), (1, 2)],
        [(0, 1), (0, 2), (1, 1), (1, 2)],
        [(0, 1), (0, 2), (1, 1), (1, 2)],
    ],
    # T
    T: [
        [(0, 1), (1, 0), (1, 1), (1, 2)],   # 0
        [(0, 1), (1, 1), (1, 2), (2, 1)],   # 1 (R)
        [(1, 0), (1, 1), (1, 2), (2, 1)],   # 2
        [(0, 1), (1, 0), (1, 1), (2, 1)],   # 3 (L)
    ],
    # S
    S: [
        [(0, 1), (0, 2), (1, 0), (1, 1)],   # 0
        [(0, 1), (1, 1), (1, 2), (2, 2)],   # 1 (R)
        [(1, 1), (1, 2), (2, 0), (2, 1)],   # 2
        [(0, 0), (1, 0), (1, 1), (2, 1)],   # 3 (L)
    ],
    # Z
    Z: [
        [(0, 0), (0, 1), (1, 1), (1, 2)],   # 0
        [(0, 2), (1, 1), (1, 2), (2, 1)],   # 1 (R)
        [(1, 0), (1, 1), (2, 1), (2, 2)],   # 2
        [(0, 1), (1, 0), (1, 1), (2, 0)],   # 3 (L)
    ],
    # J
    J: [
        [(0, 0), (1, 0), (1, 1), (1, 2)],   # 0
        [(0, 1), (0, 2), (1, 1), (2, 1)],   # 1 (R)
        [(1, 0), (1, 1), (1, 2), (2, 2)],   # 2
        [(0, 1), (1, 1), (2, 0), (2, 1)],   # 3 (L)
    ],
    # L
    L: [
        [(0, 2), (1, 0), (1, 1), (1, 2)],   # 0
        [(0, 1), (1, 1), (2, 1), (2, 2)],   # 1 (R)
        [(1, 0), (1, 1), (1, 2), (2, 0)],   # 2
        [(0, 0), (0, 1), (1, 1), (2, 1)],   # 3 (L)
    ],
}


def cells_for(piece_type: int, rotation: int) -> list[tuple[int, int]]:
    """타입+회전 상태에 해당하는 로컬 셀 (row,col) 오프셋 리스트를 반환."""
    if piece_type not in SHAPES:
        raise ValueError(f"알 수 없는 블록 타입: {piece_type}")
    return list(SHAPES[piece_type][rotation % 4])


class Piece:
    """현재 블록: 타입, 회전 상태, 보드상 기준 위치(row, col).

    position(row, col)은 블록 로컬 좌표의 원점이 보드의 어느 셀에 놓이는지를 뜻한다.
    실제 보드 셀 좌표는 (row + dr, col + dc) 로 계산한다 (board_cells 참조).
    """

    def __init__(self, piece_type: int, row: int = 0, col: int = 0,
                 rotation: int = 0) -> None:
        if piece_type not in SHAPES:
            raise ValueError(f"알 수 없는 블록 타입: {piece_type}")
        self.type = piece_type
        self.row = row
        self.col = col
        self.rotation = rotation % 4

    @property
    def color(self) -> tuple[int, int, int]:
        return COLORS[self.type]

    @property
    def name(self) -> str:
        return TYPE_NAMES[self.type]

    def local_cells(self) -> list[tuple[int, int]]:
        """현재 회전 상태의 로컬 셀 오프셋."""
        return cells_for(self.type, self.rotation)

    def board_cells(self) -> list[tuple[int, int]]:
        """현재 위치/회전을 반영한 보드 셀 (row, col) 리스트."""
        return [(self.row + dr, self.col + dc) for dr, dc in self.local_cells()]

    def rotated_cells(self, direction: int) -> list[tuple[int, int]]:
        """회전만 적용했을 때의 보드 셀을 미리 계산(실제 상태는 바꾸지 않음).

        direction: +1 시계, -1 반시계. 충돌 검사(단계 3)에서 적용 전 확인용.
        """
        new_rot = (self.rotation + direction) % 4
        return [(self.row + dr, self.col + dc) for dr, dc in cells_for(self.type, new_rot)]

    def rotate_cw(self) -> None:
        """시계 방향 90도 회전 (상태 갱신)."""
        self.rotation = (self.rotation + 1) % 4

    def rotate_ccw(self) -> None:
        """반시계 방향 90도 회전 (상태 갱신)."""
        self.rotation = (self.rotation - 1) % 4

    def copy(self) -> "Piece":
        return Piece(self.type, self.row, self.col, self.rotation)

    def __repr__(self) -> str:  # pragma: no cover
        return (f"Piece({self.name}, row={self.row}, col={self.col}, "
                f"rot={self.rotation})")
