"""리소스 경로 로더 — PyInstaller 패키징 후에도 경로가 깨지지 않도록 한다.

개발 중에는 프로젝트의 assets/ 폴더를 가리키고, PyInstaller onefile로 묶이면
런타임 임시 추출 폴더(sys._MEIPASS) 아래 assets/ 를 가리킨다.

이 모듈 자체는 Pygame을 import 하지 않는다(경로 계산만 담당).
"""

from __future__ import annotations

import os
import sys


def base_path() -> str:
    """리소스의 기준 경로를 반환한다.

    - PyInstaller 번들: sys._MEIPASS (임시 추출 폴더)
    - 개발 환경: 이 파일(src/)의 부모(프로젝트 루트)
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return meipass
    # src/resources.py -> 프로젝트 루트는 상위 폴더
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(*parts: str) -> str:
    """assets 등 리소스의 절대 경로를 조립해 반환한다.

    예: resource_path("assets", "sfx", "move.wav")
    """
    return os.path.join(base_path(), *parts)


def asset_path(*parts: str) -> str:
    """assets/ 아래 리소스 경로. 예: asset_path("sfx", "move.wav")."""
    return resource_path("assets", *parts)


def font_file(bold: bool = False) -> str | None:
    """한글 글리프가 있는 번들/시스템 폰트의 TTF 경로를 반환한다(없으면 None).

    경로 계산만 수행하므로 이 모듈은 Pygame 비의존을 유지한다. 실제 Font 객체
    생성은 렌더 레이어(main.py)가 담당한다.
    우선순위: 번들된 맑은 고딕 -> 시스템 맑은 고딕.
    """
    name = "malgunbd.ttf" if bold else "malgun.ttf"
    # 1) 번들/개발 트리
    for cand in (asset_path("fonts", name), asset_path("fonts", "malgun.ttf")):
        if os.path.exists(cand):
            return cand
    # 2) Windows 시스템 폰트
    win = os.environ.get("WINDIR") or r"C:\Windows"
    for cand in (os.path.join(win, "Fonts", name),
                 os.path.join(win, "Fonts", "malgun.ttf")):
        if os.path.exists(cand):
            return cand
    return None
