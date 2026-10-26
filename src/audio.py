"""오디오 매니저 — 효과음/배경음 재생. 설정의 ON/OFF·볼륨에 연동한다.

리소스는 resources.asset_path()로 로드해 PyInstaller 패키징 후에도 경로가 깨지지
않는다. 오디오 장치가 없거나(headless/CI) 믹서 초기화에 실패하면, 크래시 대신
조용히 비활성화(enabled=False)되어 게임은 정상 동작한다.
"""

from __future__ import annotations

import pygame

from resources import asset_path

SFX_NAMES = ("move", "rotate", "harddrop", "lineclear", "gameover")
BGM_FILE = ("bgm", "theme.wav")


class Audio:
    def __init__(self, sound_on: bool = True, volume: float = 0.7) -> None:
        self.sound_on = sound_on
        self.volume = volume
        self.enabled = False      # 믹서가 실제로 열렸는지
        self._sfx: dict[str, pygame.mixer.Sound] = {}
        self._bgm_loaded = False
        self._init_mixer()

    def _init_mixer(self) -> None:
        try:
            pygame.mixer.init()
            self.enabled = True
        except pygame.error:
            # 오디오 장치 없음 -> 조용히 비활성화
            self.enabled = False
            return
        self._load_sfx()

    def _load_sfx(self) -> None:
        for name in SFX_NAMES:
            path = asset_path("sfx", f"{name}.wav")
            try:
                snd = pygame.mixer.Sound(path)
                snd.set_volume(self.volume)
                self._sfx[name] = snd
            except (pygame.error, FileNotFoundError):
                pass  # 개별 파일 누락은 무시(그 효과음만 음소거)

    # --- 설정 반영 ---
    def set_sound_on(self, on: bool) -> None:
        self.sound_on = on
        if not on:
            self.stop_music()
        elif self.enabled and self._bgm_loaded:
            pygame.mixer.music.unpause()

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        for snd in self._sfx.values():
            snd.set_volume(self.volume)
        if self.enabled:
            pygame.mixer.music.set_volume(self.volume)

    # --- 재생 ---
    def play(self, name: str) -> None:
        if not (self.enabled and self.sound_on):
            return
        snd = self._sfx.get(name)
        if snd is not None:
            snd.play()

    def play_music(self, loop: bool = True) -> None:
        if not self.enabled:
            return
        try:
            pygame.mixer.music.load(asset_path(*BGM_FILE))
            pygame.mixer.music.set_volume(self.volume)
            self._bgm_loaded = True
            if self.sound_on:
                pygame.mixer.music.play(-1 if loop else 0)
        except (pygame.error, FileNotFoundError):
            self._bgm_loaded = False

    def stop_music(self) -> None:
        if self.enabled:
            pygame.mixer.music.stop()
