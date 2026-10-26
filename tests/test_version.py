"""단계 9 — 버전 메타데이터 테스트."""

import os
import re
import sys

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
sys.path.insert(0, SRC_DIR)

import version  # noqa: E402


def test_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", version.__version__)


def test_title_contains_name_and_version():
    t = version.title()
    assert version.APP_NAME in t
    assert version.__version__ in t


def test_version_module_has_no_pygame():
    # 버전 모듈은 로직/메타 계층 — Pygame 비의존이어야 한다
    import importlib.util
    spec = importlib.util.find_spec("version")
    src = open(spec.origin, encoding="utf-8").read()
    assert "pygame" not in src
