"""단계 7 리소스/오디오 자산 테스트 — 경로 로더 + SFX 생성(오디오 장치 불요)."""

import importlib.util
import os
import sys
import wave

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import resources  # noqa: E402


def test_resources_has_no_pygame():
    spec = importlib.util.find_spec("resources")
    src = open(spec.origin, encoding="utf-8").read()
    assert "pygame" not in src


def test_base_path_is_project_root_in_dev():
    # 개발 환경에서는 프로젝트 루트(= src의 부모)를 가리킨다
    bp = resources.base_path()
    assert os.path.isdir(os.path.join(bp, "src"))
    assert os.path.isdir(os.path.join(bp, "assets"))


def test_asset_path_composes():
    p = resources.asset_path("sfx", "move.wav")
    assert p.endswith(os.path.join("assets", "sfx", "move.wav"))


def test_meipass_override(monkeypatch):
    # PyInstaller 런타임을 흉내: sys._MEIPASS 가 있으면 그걸 base로 쓴다
    monkeypatch.setattr(sys, "_MEIPASS", r"X:\bundle", raising=False)
    assert resources.base_path() == r"X:\bundle"
    assert resources.asset_path("sfx", "move.wav") == os.path.join(
        r"X:\bundle", "assets", "sfx", "move.wav")


def test_sfx_files_exist_and_are_valid_wav():
    names = ["sfx/move.wav", "sfx/rotate.wav", "sfx/harddrop.wav",
             "sfx/lineclear.wav", "sfx/gameover.wav", "bgm/theme.wav"]
    for rel in names:
        path = resources.asset_path(*rel.split("/"))
        assert os.path.exists(path), f"누락: {path}"
        with wave.open(path, "r") as w:
            assert w.getframerate() == 44100
            assert w.getsampwidth() == 2
            assert w.getnframes() > 0


def test_make_sfx_generates_into_tmp(tmp_path):
    import make_sfx
    created = make_sfx.make_all(str(tmp_path))
    assert len(created) == 6
    for p in created:
        assert os.path.exists(p)
