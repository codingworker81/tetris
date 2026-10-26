"""효과음·배경음 생성기 — 표준 라이브러리만으로 WAV를 직접 합성한다.

외부 오디오를 내려받지 않고 사인파/노이즈로 직접 만들어 assets/ 아래에 저장한다.
따라서 라이선스가 완전히 깔끔하다(자체 제작, 사실상 CC0/퍼블릭 도메인).

사용:  python tools/make_sfx.py        (프로젝트 루트에서)
생성:  assets/sfx/{move,rotate,harddrop,lineclear,gameover}.wav
       assets/bgm/theme.wav  (짧은 루프)

numpy 등 외부 의존성 없이 stdlib(wave, math, struct)만 사용한다.
"""

from __future__ import annotations

import math
import os
import struct
import wave

SAMPLE_RATE = 44100
AMP = 0.35  # 기본 진폭(0~1), 클리핑 방지용으로 낮게


def _write_wav(path: str, samples: list[float]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)      # 16-bit
        w.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for s in samples:
            v = int(max(-1.0, min(1.0, s)) * 32767)
            frames += struct.pack("<h", v)
        w.writeframes(bytes(frames))


def _tone(freq: float, dur: float, amp: float = AMP, decay: bool = True,
          wave_type: str = "sine") -> list[float]:
    """단일 톤을 생성한다. decay=True면 끝으로 갈수록 소리가 줄어든다."""
    n = int(SAMPLE_RATE * dur)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = (1.0 - i / n) if decay else 1.0
        if wave_type == "square":
            val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        elif wave_type == "saw":
            val = 2.0 * ((freq * t) % 1.0) - 1.0
        else:  # sine
            val = math.sin(2 * math.pi * freq * t)
        out.append(amp * env * val)
    return out


def _sweep(f0: float, f1: float, dur: float, amp: float = AMP) -> list[float]:
    """주파수가 f0->f1로 변하는 글라이드(하드드롭/게임오버 효과용)."""
    n = int(SAMPLE_RATE * dur)
    out = []
    phase = 0.0
    for i in range(n):
        frac = i / n
        freq = f0 + (f1 - f0) * frac
        phase += 2 * math.pi * freq / SAMPLE_RATE
        env = 1.0 - frac
        out.append(amp * env * math.sin(phase))
    return out


def _concat(*chunks: list[float]) -> list[float]:
    out: list[float] = []
    for c in chunks:
        out.extend(c)
    return out


def make_all(assets_dir: str) -> list[str]:
    """모든 효과음/배경음을 생성하고 생성된 파일 경로 목록을 반환한다."""
    created = []
    sfx = os.path.join(assets_dir, "sfx")
    bgm = os.path.join(assets_dir, "bgm")

    # 이동: 짧고 낮은 클릭
    p = os.path.join(sfx, "move.wav")
    _write_wav(p, _tone(220, 0.04, amp=0.25, wave_type="square")); created.append(p)

    # 회전: 조금 높은 틱
    p = os.path.join(sfx, "rotate.wav")
    _write_wav(p, _tone(440, 0.05, amp=0.25, wave_type="square")); created.append(p)

    # 하드드롭: 아래로 떨어지는 쿵
    p = os.path.join(sfx, "harddrop.wav")
    _write_wav(p, _sweep(400, 90, 0.12, amp=0.4)); created.append(p)

    # 라인클리어: 상승하는 아르페지오
    p = os.path.join(sfx, "lineclear.wav")
    _write_wav(p, _concat(
        _tone(523, 0.07, amp=0.3), _tone(659, 0.07, amp=0.3),
        _tone(784, 0.07, amp=0.3), _tone(1047, 0.1, amp=0.3),
    )); created.append(p)

    # 게임오버: 하강하는 음
    p = os.path.join(sfx, "gameover.wav")
    _write_wav(p, _concat(
        _tone(392, 0.18, amp=0.35), _tone(330, 0.18, amp=0.35),
        _tone(262, 0.3, amp=0.35),
    )); created.append(p)

    # 배경음: 간단한 코로베이니키풍 멜로디 루프(자체 작성 모티프)
    p = os.path.join(bgm, "theme.wav")
    notes = [  # (주파수, 길이초)
        (659, 0.2), (494, 0.1), (523, 0.1), (587, 0.2), (523, 0.1), (494, 0.1),
        (440, 0.2), (440, 0.1), (523, 0.1), (659, 0.2), (587, 0.1), (523, 0.1),
        (494, 0.3), (523, 0.1), (587, 0.2), (659, 0.2), (523, 0.2), (440, 0.2),
        (440, 0.4),
    ]
    melody: list[float] = []
    for freq, dur in notes:
        melody += _tone(freq, dur, amp=0.22, decay=False, wave_type="saw")
        melody += [0.0] * int(SAMPLE_RATE * 0.02)  # 음 사이 짧은 간격
    _write_wav(p, melody); created.append(p)

    return created


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets = os.path.join(root, "assets")
    files = make_all(assets)
    print(f"생성 완료 ({len(files)}개):")
    for f in files:
        print("  ", f)
