"""로컬 데이터 저장 — Pygame과 분리된 순수 파이썬 모듈.

저장 위치: %APPDATA%\\Tetris\\ (Windows). 없으면 생성한다. 형식은 JSON.
- scores.json : 최고점수 Top 10
- settings.json : 키맵, 사운드 ON/OFF, 볼륨
설치 디렉터리에는 절대 쓰지 않는다 (%APPDATA% 경로만 사용).

테스트에서 임시 디렉터리를 쓸 수 있도록 base_dir를 주입받을 수 있다.
"""

from __future__ import annotations

import json
import os

APP_DIR_NAME = "Tetris"
SCORES_FILE = "scores.json"
SETTINGS_FILE = "settings.json"
TOP_N = 10

# 기본 설정값
DEFAULT_SETTINGS: dict = {
    "keymap": {
        "left": "LEFT",
        "right": "RIGHT",
        "soft_drop": "DOWN",
        "hard_drop": "SPACE",
        "rotate_cw": "UP",
        "rotate_ccw": "Z",
        "hold": "C",
        "pause": "P",
    },
    "sound": True,       # 사운드 ON/OFF
    "volume": 0.7,       # 0.0 ~ 1.0
}


def app_data_dir(base_dir: str | None = None) -> str:
    """저장 디렉터리 경로를 반환한다. 없으면 생성한다.

    base_dir를 주면 그 아래 Tetris/ 를 쓴다(테스트용 임시 디렉터리).
    주지 않으면 %APPDATA%\\Tetris\\ 를 쓴다. %APPDATA%가 없으면
    (비Windows 등) 사용자 홈 아래 .tetris 로 대체한다.
    """
    if base_dir is None:
        appdata = os.environ.get("APPDATA")
        if appdata:
            base = os.path.join(appdata, APP_DIR_NAME)
        else:
            base = os.path.join(os.path.expanduser("~"), ".tetris")
    else:
        base = os.path.join(base_dir, APP_DIR_NAME)
    os.makedirs(base, exist_ok=True)
    return base


def _read_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # 손상된 파일은 기본값으로 복구 (크래시 대신 graceful degradation)
        return default


def _write_json(path: str, data) -> None:
    # 원자적 쓰기: 임시 파일에 쓴 뒤 교체
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# --- 점수(랭킹) ---
def load_scores(base_dir: str | None = None) -> list[dict]:
    """Top 10 점수 리스트를 반환한다. 각 항목: {"name": str, "score": int, ...}."""
    path = os.path.join(app_data_dir(base_dir), SCORES_FILE)
    data = _read_json(path, [])
    if not isinstance(data, list):
        return []
    return data


def save_scores(scores: list[dict], base_dir: str | None = None) -> None:
    path = os.path.join(app_data_dir(base_dir), SCORES_FILE)
    _write_json(path, scores[:TOP_N])


def add_score(name: str, score: int, base_dir: str | None = None) -> list[dict]:
    """새 점수를 랭킹에 삽입하고 내림차순 정렬 + Top 10 유지. 갱신된 리스트 반환."""
    scores = load_scores(base_dir)
    scores.append({"name": name, "score": int(score)})
    scores.sort(key=lambda e: e.get("score", 0), reverse=True)
    scores = scores[:TOP_N]
    save_scores(scores, base_dir)
    return scores


def is_high_score(score: int, base_dir: str | None = None) -> bool:
    """해당 점수가 Top 10에 들어갈 자격이 있으면 True."""
    scores = load_scores(base_dir)
    if len(scores) < TOP_N:
        return score > 0
    lowest = min((e.get("score", 0) for e in scores), default=0)
    return score > lowest


# --- 설정 ---
def load_settings(base_dir: str | None = None) -> dict:
    """설정을 로드한다. 없거나 손상되면 기본값. 누락 키는 기본값으로 보충."""
    path = os.path.join(app_data_dir(base_dir), SETTINGS_FILE)
    data = _read_json(path, None)
    merged = json.loads(json.dumps(DEFAULT_SETTINGS))  # 깊은 복사
    if isinstance(data, dict):
        for k, v in data.items():
            if k == "keymap" and isinstance(v, dict):
                merged["keymap"].update(v)
            else:
                merged[k] = v
    return merged


def save_settings(settings: dict, base_dir: str | None = None) -> None:
    path = os.path.join(app_data_dir(base_dir), SETTINGS_FILE)
    _write_json(path, settings)
