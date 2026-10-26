"""앱 아이콘(.ico) 생성기 — 외부 이미지 없이 코드로 직접 그린다.

테트리스 느낌의 블록 아이콘을 여러 크기(16/32/48/64/128/256)로 렌더해
assets/icon.ico 로 저장한다. Pillow가 있으면 ICO로, 없으면 PNG로 저장 후
안내한다. 라이선스 깔끔(자체 제작).

사용:  python tools/make_icon.py   (프로젝트 루트에서)
"""

from __future__ import annotations

import os

import pygame

# 블록 색 (piece.py 색상과 유사)
PALETTE = [
    (0, 240, 240), (240, 240, 0), (160, 0, 240),
    (0, 240, 0), (240, 0, 0), (0, 0, 240), (240, 160, 0),
]


def _render_icon(size: int) -> "pygame.Surface":
    surf = pygame.Surface((size, size))
    surf.fill((16, 16, 24))
    # 4x4 격자에 몇 개 블록을 배치 (T 모양 느낌)
    cells = size // 4
    pattern = [(1, 0), (1, 1), (1, 2), (2, 1)]  # T 블록
    for i, (r, c) in enumerate(pattern):
        color = PALETTE[2]  # 보라(T)
        rect = (c * cells + 1, r * cells + 1, cells - 2, cells - 2)
        pygame.draw.rect(surf, color, rect)
        pygame.draw.rect(surf, (0, 0, 0), rect, 1)
    return surf


def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets = os.path.join(root, "assets")
    os.makedirs(assets, exist_ok=True)
    pygame.init()

    sizes = [16, 32, 48, 64, 128, 256]

    ico = os.path.join(assets, "icon.ico")
    try:
        from PIL import Image

        # 256px 소스 하나를 PNG로 저장 후 Pillow로 열어, 여러 크기를 담은 ICO로 저장.
        src_png = os.path.join(assets, "_icon_src.png")
        pygame.image.save(_render_icon(256), src_png)
        with Image.open(src_png) as img:
            img.load()  # 핸들을 즉시 로드해 파일 잠금 해제 가능하게
            img.save(ico, format="ICO", sizes=[(s, s) for s in sizes])
        os.remove(src_png)
        print("ICO 생성:", ico, f"(크기 {sizes})")
    except ImportError:
        fallback = os.path.join(assets, "icon.png")
        pygame.image.save(_render_icon(256), fallback)
        print("Pillow 미설치 -> PNG 아이콘만 생성:", fallback)
        print("ICO가 필요하면: pip install pillow 후 다시 실행")
    pygame.quit()


if __name__ == "__main__":
    main()
