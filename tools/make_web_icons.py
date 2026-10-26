"""Tetris PWA 아이콘 생성기 — Pillow로 192/512/maskable PNG를 docs/icons에 만든다.
외부 이미지를 쓰지 않고 테트로미노 도형으로 직접 그린다. 생성 후 파일 존재를 검증해 리포트한다.
실행: tetris/.venv의 python으로 이 파일을 실행.
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(__file__)
OUT = os.path.abspath(os.path.join(HERE, "..", "docs", "icons"))
os.makedirs(OUT, exist_ok=True)

BG = (11, 14, 26)
CYAN = (0, 240, 240)
PURPLE = (160, 0, 240)
ORANGE = (240, 160, 0)


def cell(d, x, y, s, color):
    d.rectangle([x, y, x + s, y + s], fill=color)
    hl = tuple(min(255, c + 45) for c in color)
    d.rectangle([x + s // 10, y + s // 10, x + s - s // 10, y + s // 3], fill=hl)
    d.rectangle([x, y, x + s, y + s], outline=(255, 255, 255), width=max(1, s // 20))


def make_icon(size, maskable):
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)
    pad = int(size * (0.24 if maskable else 0.14))
    area = size - 2 * pad
    c = area // 3
    ox = (size - c * 3) // 2
    oy = (size - c * 3) // 2
    gap = max(1, c // 14)
    # T 블록(보라) + 아래 라인(시안/주황)
    for (r, cc) in [(0, 1), (1, 0), (1, 1), (1, 2)]:
        cell(d, ox + cc * c, oy + r * c, c - gap, PURPLE)
    for cc in range(3):
        cell(d, ox + cc * c, oy + 2 * c, c - gap, CYAN if cc == 1 else ORANGE)
    return img


def main():
    specs = [("icon-192.png", 192, False), ("icon-512.png", 512, False), ("icon-maskable-512.png", 512, True)]
    lines = []
    for name, size, mask in specs:
        p = os.path.join(OUT, name)
        make_icon(size, mask).save(p, "PNG")
        exists = os.path.exists(p)
        lines.append(f"{name}\t{size}\texists={exists}\tbytes={os.path.getsize(p) if exists else 0}")
    report = os.path.join(OUT, "_report.txt")
    with open(report, "w", encoding="utf-8") as f:
        f.write(f"OUT={OUT}\n" + "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
