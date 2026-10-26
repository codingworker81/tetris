"""충돌 검사 & 벽차기(wall kick) — Pygame과 분리된 순수 파이썬 모듈.

보드(board.Board)와 블록(piece.Piece)만 알고, 그 사이의 충돌/이동 가능 여부와
회전 시 벽차기 오프셋을 계산한다.
"""

from __future__ import annotations

from board import Board
from piece import I, O, Piece

# --- SRS 벽차기(wall kick) 오프셋 테이블 ---
# 각 (시작회전 -> 끝회전) 전환마다 시도할 (dcol, drow) 오프셋 목록.
# 주의: SRS 표준은 (x, y)에서 y가 위로 +이지만, 여기 보드는 row가 아래로 +이므로
# y 성분의 부호를 뒤집어 (dcol, drow)로 저장했다. 즉 표준 테이블의 (x, y) -> (x, -y).
# JLSTZ 공통 테이블
KICKS_JLSTZ: dict[tuple[int, int], list[tuple[int, int]]] = {
    (0, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (1, 0): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (1, 2): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (2, 1): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (2, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (3, 2): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (3, 0): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (0, 3): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
}
# I 블록 전용 테이블
KICKS_I: dict[tuple[int, int], list[tuple[int, int]]] = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],
}


def cells_valid(board: Board, cells: list[tuple[int, int]]) -> bool:
    """주어진 보드 셀 좌표들이 모두 보드 안이고 비어 있으면 True."""
    for r, c in cells:
        if not board.in_bounds(r, c):
            return False
        if board.is_cell_filled(r, c):
            return False
    return True


def piece_fits(board: Board, piece: Piece) -> bool:
    """현재 블록이 지금 위치/회전에서 유효하게 놓일 수 있으면 True."""
    return cells_valid(board, piece.board_cells())


def can_move(board: Board, piece: Piece, drow: int, dcol: int) -> bool:
    """블록을 (drow, dcol)만큼 옮겼을 때 유효하면 True."""
    moved = [(r + drow, c + dcol) for r, c in piece.board_cells()]
    return cells_valid(board, moved)


def try_move(board: Board, piece: Piece, drow: int, dcol: int) -> bool:
    """이동 가능하면 실제로 옮기고 True, 아니면 그대로 두고 False."""
    if can_move(board, piece, drow, dcol):
        piece.row += drow
        piece.col += dcol
        return True
    return False


def try_rotate(board: Board, piece: Piece, direction: int) -> bool:
    """SRS 벽차기를 적용해 회전을 시도한다. 성공하면 상태를 갱신하고 True.

    direction: +1 시계, -1 반시계. O블록은 회전해도 동일하므로 항상 성공 처리.
    """
    if piece.type == O:
        return True  # O는 회전 불변

    old_rot = piece.rotation
    new_rot = (old_rot + direction) % 4
    table = KICKS_I if piece.type == I else KICKS_JLSTZ
    kicks = table.get((old_rot, new_rot), [(0, 0)])

    base_cells = [(piece.row + dr, piece.col + dc)
                  for dr, dc in _local_cells(piece.type, new_rot)]

    for dcol, drow in kicks:
        candidate = [(r + drow, c + dcol) for r, c in base_cells]
        if cells_valid(board, candidate):
            piece.rotation = new_rot
            piece.row += drow
            piece.col += dcol
            return True
    return False


def _local_cells(piece_type: int, rotation: int) -> list[tuple[int, int]]:
    from piece import cells_for
    return cells_for(piece_type, rotation)


def lock_piece(board: Board, piece: Piece) -> None:
    """블록을 보드에 고정한다(각 셀에 타입 코드를 기록)."""
    for r, c in piece.board_cells():
        if board.in_bounds(r, c):
            board.set(r, c, piece.type)
