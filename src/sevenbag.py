"""7-bag 랜덤 생성기 — Pygame과 분리된 순수 파이썬 모듈.

7종 블록을 한 '봉지(bag)'에 담아 섞어 하나씩 꺼내고, 봉지가 비면 다시 7종을
새로 섞어 채운다. 이렇게 하면 7개 안에서 각 블록이 정확히 1번씩 나와 편중을 막는다.

내부적으로 '다음에 나올 타입'들을 큐(_queue)에 쌓아두어, peek()이 실제로 나올
순서를 비파괴적으로 정확히 미리 볼 수 있게 한다(단계 5 Next 미리보기용).
"""

from __future__ import annotations

import random
from collections import deque

from piece import TYPES


class SevenBag:
    """7-bag 큐. next_type()으로 다음 블록 타입을 하나씩 꺼낸다."""

    def __init__(self, rng: random.Random | None = None) -> None:
        # 테스트에서 시드 고정이 가능하도록 rng를 주입받는다.
        self._rng = rng or random.Random()
        self._queue: deque[int] = deque()

    def _refill(self) -> None:
        """새 봉지(7종)를 섞어 큐 뒤에 이어 붙인다."""
        bag = list(TYPES)
        self._rng.shuffle(bag)
        self._queue.extend(bag)

    def _ensure(self, count: int) -> None:
        while len(self._queue) < count:
            self._refill()

    def next_type(self) -> int:
        """다음 블록 타입을 반환한다. 큐가 비면 새 봉지를 채운다."""
        self._ensure(1)
        return self._queue.popleft()

    def peek(self, count: int) -> list[int]:
        """다음 count개 블록 타입을 비파괴적으로 미리 본다(실제 나올 순서)."""
        self._ensure(count)
        return [self._queue[i] for i in range(count)]
