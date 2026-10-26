"""로컬 저장(storage) 단위 테스트 — 임시 디렉터리 사용, 실제 %APPDATA% 미오염."""

import importlib.util
import json
import os
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
sys.path.insert(0, SRC_DIR)

import storage  # noqa: E402
from storage import (  # noqa: E402
    DEFAULT_SETTINGS,
    TOP_N,
    add_score,
    is_high_score,
    load_scores,
    load_settings,
    save_settings,
)


def test_storage_has_no_pygame():
    spec = importlib.util.find_spec("storage")
    src = open(spec.origin, encoding="utf-8").read()
    assert "pygame" not in src


def test_creates_dir_under_base(tmp_path):
    d = storage.app_data_dir(str(tmp_path))
    assert os.path.isdir(d)
    assert d.endswith("Tetris")


def test_empty_scores_initially(tmp_path):
    assert load_scores(str(tmp_path)) == []


def test_add_score_sorts_desc(tmp_path):
    base = str(tmp_path)
    add_score("A", 100, base)
    add_score("B", 500, base)
    add_score("C", 300, base)
    scores = load_scores(base)
    assert [e["score"] for e in scores] == [500, 300, 100]
    assert scores[0]["name"] == "B"


def test_top_10_truncation(tmp_path):
    base = str(tmp_path)
    for i in range(15):
        add_score(f"P{i}", i * 10, base)
    scores = load_scores(base)
    assert len(scores) == TOP_N
    # 가장 높은 10개만 남아야 한다: 140,130,...,50
    assert [e["score"] for e in scores] == [140, 130, 120, 110, 100, 90, 80, 70, 60, 50]


def test_is_high_score(tmp_path):
    base = str(tmp_path)
    assert is_high_score(10, base) is True   # 비어 있으면 양수면 등재 가능
    for i in range(TOP_N):
        add_score(f"P{i}", 100 + i, base)    # 100..109
    assert is_high_score(50, base) is False  # 최저(100)보다 낮음
    assert is_high_score(105, base) is True  # 최저보다 높음
    assert is_high_score(100, base) is False  # 최저와 같으면 등재 불가


def test_scores_persist_across_reload(tmp_path):
    base = str(tmp_path)
    add_score("Z", 999, base)
    # 새 로드가 디스크에서 다시 읽어온다
    reloaded = load_scores(base)
    assert reloaded[0] == {"name": "Z", "score": 999}
    # 실제 파일이 존재한다
    assert os.path.exists(os.path.join(base, "Tetris", "scores.json"))


def test_settings_defaults_when_absent(tmp_path):
    s = load_settings(str(tmp_path))
    assert s["sound"] == DEFAULT_SETTINGS["sound"]
    assert s["volume"] == DEFAULT_SETTINGS["volume"]
    assert "left" in s["keymap"]


def test_settings_save_and_load(tmp_path):
    base = str(tmp_path)
    s = load_settings(base)
    s["sound"] = False
    s["volume"] = 0.3
    s["keymap"]["hard_drop"] = "RETURN"
    save_settings(s, base)
    loaded = load_settings(base)
    assert loaded["sound"] is False
    assert loaded["volume"] == 0.3
    assert loaded["keymap"]["hard_drop"] == "RETURN"
    # 재배치하지 않은 키는 기본값 유지
    assert loaded["keymap"]["left"] == DEFAULT_SETTINGS["keymap"]["left"]


def test_corrupted_file_recovers_to_default(tmp_path):
    base = str(tmp_path)
    d = storage.app_data_dir(base)
    with open(os.path.join(d, "settings.json"), "w", encoding="utf-8") as f:
        f.write("{ this is not valid json ")
    # 손상돼도 크래시 없이 기본값으로 복구
    s = load_settings(base)
    assert s["sound"] == DEFAULT_SETTINGS["sound"]


def test_missing_keymap_keys_filled(tmp_path):
    base = str(tmp_path)
    d = storage.app_data_dir(base)
    with open(os.path.join(d, "settings.json"), "w", encoding="utf-8") as f:
        json.dump({"keymap": {"left": "A"}, "sound": False}, f)
    s = load_settings(base)
    assert s["keymap"]["left"] == "A"          # 저장된 값 유지
    assert s["keymap"]["right"] == DEFAULT_SETTINGS["keymap"]["right"]  # 누락분 보충
    assert s["sound"] is False
