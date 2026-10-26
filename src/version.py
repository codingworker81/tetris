"""애플리케이션 버전 단일 출처(single source of truth).

창 제목·릴리스 노트·패키징이 모두 이 값을 참조한다.
Pygame 비의존 모듈(테스트에서 그대로 import 가능).
"""

from __future__ import annotations

__version__ = "1.0.0"
APP_NAME = "Tetris"


def title() -> str:
    """창 제목 등에 쓰는 'Tetris v1.0.0' 형태의 문자열."""
    return f"{APP_NAME} v{__version__}"
