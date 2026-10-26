"""테트리스 보드(게임 상태) 모델 — Pygame과 완전히 분리된 순수 파이썬 모듈.

좌표계: 좌상단이 (row=0, col=0). row는 아래로, col은 오른쪽으로 증가한다.
그리드: 가로 10칸(COLS) x 세로 20칸(ROWS)이 "보이는" 영역이다.
상단에 스폰 버퍼(SPAWN_BUFFER)를 두어, 블록이 보이는 영역 위에서 생성될 수 있게 한다.
따라서 내부 셀 배열의 전체 높이는 ROWS + SPAWN_BUFFER 이다.

셀 값 규약:
- 0            : 빈칸
- 1 이상의 정수 : 고정된 블록(테트로미노 타입/색상 코드). 타입 코드는 단계 2에서 정의.
"""

from __future__ import annotations

# --- 보드 치수 (보이는 영역) ---
COLS = 10          # 가로 칸 수
ROWS = 20          # 세로 칸 수 (보이는 영역)
SPAWN_BUFFER = 2   # 상단 숨김 스폰 버퍼 (보이지 않음)

EMPTY = 0          # 빈 셀 값

# 내부 배열의 전체 높이 (스폰 버퍼 포함)
TOTAL_ROWS = ROWS + SPAWN_BUFFER


class Board:
    """테트리스 플레이필드의 셀 상태를 보관·조회하는 모델.

    내부 저장(_grid)은 버퍼를 포함한 전체 높이(TOTAL_ROWS) x COLS 이다.
    외부에 노출하는 row 좌표는 '보이는 영역' 기준이 아니라 '전체 배열' 기준이며,
    row 0 .. SPAWN_BUFFER-1 이 숨겨진 스폰 버퍼, row SPAWN_BUFFER .. TOTAL_ROWS-1 이
    보이는 영역이다. 렌더러는 visible_rows()로 보이는 부분만 그린다.
    """

    def __init__(self, cols: int = COLS, visible_rows: int = ROWS,
                 spawn_buffer: int = SPAWN_BUFFER) -> None:
        if cols <= 0 or visible_rows <= 0 or spawn_buffer < 0:
            raise ValueError("보드 치수는 양수여야 한다 (buffer는 0 이상).")
        self.cols = cols
        self.visible_row_count = visible_rows  # 보이는 행 수 (method visible_rows()와 이름 충돌 방지)
        self.spawn_buffer = spawn_buffer
        self.total_rows = visible_rows + spawn_buffer
        # 전체(버퍼 포함) 그리드를 빈칸으로 초기화
        self._grid: list[list[int]] = [
            [EMPTY for _ in range(self.cols)] for _ in range(self.total_rows)
        ]

    # --- 범위 검사 ---
    def in_bounds(self, row: int, col: int) -> bool:
        """(row, col)이 전체 그리드(버퍼 포함) 범위 안이면 True."""
        return 0 <= row < self.total_rows and 0 <= col < self.cols

    # --- 셀 접근 ---
    def get(self, row: int, col: int) -> int:
        """셀 값을 반환한다. 범위를 벗어나면 IndexError를 올린다.

        '보드 밖'을 방어적으로 True/False로 다루고 싶을 때는 in_bounds()를 먼저
        호출하라. 명시적 오류가 필요한 경로에서는 이 메서드가 예외를 던진다.
        """
        if not self.in_bounds(row, col):
            raise IndexError(f"보드 범위를 벗어난 접근: (row={row}, col={col})")
        return self._grid[row][col]

    def is_empty(self, row: int, col: int) -> bool:
        """해당 셀이 비어 있으면 True. 범위를 벗어나면 False(막힘으로 간주)."""
        if not self.in_bounds(row, col):
            return False
        return self._grid[row][col] == EMPTY

    def set(self, row: int, col: int, value: int) -> None:
        """셀 값을 설정한다. 범위를 벗어나면 IndexError."""
        if not self.in_bounds(row, col):
            raise IndexError(f"보드 범위를 벗어난 설정: (row={row}, col={col})")
        self._grid[row][col] = value

    # --- 조회 헬퍼 ---
    def is_cell_filled(self, row: int, col: int) -> bool:
        """셀이 고정 블록으로 차 있으면 True. 범위 밖은 False."""
        if not self.in_bounds(row, col):
            return False
        return self._grid[row][col] != EMPTY

    def is_row_full(self, row: int) -> bool:
        """해당 행이 전부 채워져 있으면 True (라인 클리어 판정용, 단계 4에서 사용)."""
        if not (0 <= row < self.total_rows):
            raise IndexError(f"보드 범위를 벗어난 행: {row}")
        return all(cell != EMPTY for cell in self._grid[row])

    def clear_full_rows(self) -> int:
        """꽉 찬 행을 모두 제거하고 위 블록들을 아래로 당긴다. 제거한 줄 수를 반환.

        구현: 꽉 차지 않은 행만 아래부터 다시 쌓고, 모자란 윗부분은 빈 행으로 채운다.
        한 번에 여러 줄을 처리하며, 중력(위 블록 당기기)이 자동으로 반영된다.
        """
        kept = [row for row in self._grid if not all(cell != EMPTY for cell in row)]
        cleared = self.total_rows - len(kept)
        empties = [[EMPTY for _ in range(self.cols)] for _ in range(cleared)]
        self._grid = empties + kept
        return cleared


    def visible_rows(self) -> list[list[int]]:
        """보이는 영역의 셀 2차원 배열(얕은 사본)을 반환한다. 렌더링용."""
        return [list(self._grid[r]) for r in range(self.spawn_buffer, self.total_rows)]

    def clear(self) -> None:
        """모든 셀을 빈칸으로 되돌린다 (새 게임 시작용)."""
        for r in range(self.total_rows):
            for c in range(self.cols):
                self._grid[r][c] = EMPTY

    def __repr__(self) -> str:  # pragma: no cover - 디버깅 편의
        return (f"Board(cols={self.cols}, visible_rows={self.visible_rows}, "
                f"spawn_buffer={self.spawn_buffer})")
