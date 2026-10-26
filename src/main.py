"""PC용 테트리스 - 메인 루프 · 씬(메뉴) 관리 · 렌더링.

게임 규칙(board/piece/collision/game/scoring)과 저장(storage)은 Pygame과 분리된
순수 모듈이며, 여기서는 그 상태를 읽어 화면에 그리고, 입력을 조작으로 전달하며,
씬(장면) 전환을 관리한다.

씬: MENU(메인) · PLAYING · PAUSED · GAMEOVER · RANKING · SETTINGS
단계 6: 메뉴 시스템 + %APPDATA%\\Tetris\\ JSON 저장(랭킹 Top10 · 설정).
단계 8: 한글 UI가 깨지지 않도록 번들 맑은 고딕 TTF로 렌더(get_font).
"""

import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storage  # noqa: E402
import resources  # noqa: E402
from version import title as app_title  # noqa: E402
from audio import Audio  # noqa: E402
from board import SPAWN_BUFFER  # noqa: E402
from game import Game  # noqa: E402
from piece import COLORS, cells_for  # noqa: E402

# --- 창 / 렌더 설정 ---
CELL_SIZE = 28
BOARD_MARGIN_TOP = 20
HOLD_PANEL_W = 120
NEXT_PANEL_W = 120
BOARD_COLS = 10
BOARD_ROWS = 20
GAP = 16

BOARD_MARGIN_LEFT = HOLD_PANEL_W + GAP
WINDOW_WIDTH = HOLD_PANEL_W + GAP + BOARD_COLS * CELL_SIZE + GAP + NEXT_PANEL_W + GAP
WINDOW_HEIGHT = BOARD_MARGIN_TOP * 2 + BOARD_ROWS * CELL_SIZE
WINDOW_TITLE = "Tetris"
TARGET_FPS = 60

DAS_DELAY_MS = 160
ARR_RATE_MS = 40

# 색상
COLOR_BG = (16, 16, 24)
COLOR_FIELD = (0, 0, 0)
COLOR_GRID = (40, 40, 56)
COLOR_BORDER = (120, 120, 140)
COLOR_TEXT = (220, 220, 230)
COLOR_GHOST = (90, 90, 110)
COLOR_HILITE = (255, 230, 120)

# 씬 상태
MENU, PLAYING, PAUSED, GAMEOVER, RANKING, SETTINGS = (
    "MENU", "PLAYING", "PAUSED", "GAMEOVER", "RANKING", "SETTINGS")


# ---------------------------------------------------------------- 폰트 로더
# 한글 UI가 깨지지 않도록 한글 글리프가 있는 TTF(맑은 고딕)로 렌더한다.
# 경로 탐색은 resources.font_file()(비 pygame)이 담당하고, 여기서 Font를 만든다.
_FONT_CACHE: dict = {}


def get_font(size: int, bold: bool = False):
    """한글이 깨지지 않는 pygame Font 객체(결과 캐시).

    번들/시스템 맑은 고딕 TTF -> SysFont('malgun gothic') -> 기본폰트 폴백.
    """
    key = (size, bool(bold))
    cached = _FONT_CACHE.get(key)
    if cached is not None:
        return cached

    path = resources.font_file(bold)
    f = None
    if path:
        try:
            f = pygame.font.Font(path, size)
            if bold and path.lower().endswith("malgun.ttf"):
                f.set_bold(True)  # 보통체로 대체된 경우 합성 볼드
        except Exception:
            f = None
    if f is None:
        try:
            f = pygame.font.SysFont("malgungothic,malgun gothic,gulim,dotum",
                                    size, bold=bold)
        except Exception:
            f = pygame.font.Font(None, size)

    _FONT_CACHE[key] = f
    return f


# ---------------------------------------------------------------- 보드 렌더
def _cell_rect(vis_row, col):
    x = BOARD_MARGIN_LEFT + col * CELL_SIZE
    y = BOARD_MARGIN_TOP + vis_row * CELL_SIZE
    return (x, y, CELL_SIZE, CELL_SIZE)


def _draw_block_cell(screen, vis_row, col, color, ghost=False):
    x, y, w, h = _cell_rect(vis_row, col)
    if ghost:
        pygame.draw.rect(screen, COLOR_GHOST, (x + 1, y + 1, w - 2, h - 2), width=2)
    else:
        pygame.draw.rect(screen, color, (x + 1, y + 1, w - 2, h - 2))
        pygame.draw.rect(screen, (0, 0, 0), (x + 1, y + 1, w - 2, h - 2), width=1)


def _draw_mini_piece(screen, piece_type, px, py, cell=18):
    if piece_type is None:
        return
    for r, c in cells_for(piece_type, 0):
        rect = (px + c * cell, py + r * cell, cell - 1, cell - 1)
        pygame.draw.rect(screen, COLORS[piece_type], rect)


def draw_game(screen, game: Game, font, paused=False, flash=0.0, flash_text=None):
    board = game.board
    cols, rows = board.cols, board.visible_row_count
    field_w, field_h = cols * CELL_SIZE, rows * CELL_SIZE
    ox, oy = BOARD_MARGIN_LEFT, BOARD_MARGIN_TOP

    pygame.draw.rect(screen, COLOR_FIELD, (ox, oy, field_w, field_h))

    for vis_r, row_cells in enumerate(board.visible_rows()):
        for c, val in enumerate(row_cells):
            if val != 0:
                _draw_block_cell(screen, vis_r, c, COLORS[val])

    if game.current is not None and not game.game_over:
        for r, c in game.ghost_cells():
            vis_r = r - SPAWN_BUFFER
            if 0 <= vis_r < rows and 0 <= c < cols:
                _draw_block_cell(screen, vis_r, c, None, ghost=True)

    if game.current is not None:
        for r, c in game.current.board_cells():
            vis_r = r - SPAWN_BUFFER
            if 0 <= vis_r < rows and 0 <= c < cols:
                _draw_block_cell(screen, vis_r, c, game.current.color)

    for c in range(cols + 1):
        x = ox + c * CELL_SIZE
        pygame.draw.line(screen, COLOR_GRID, (x, oy), (x, oy + field_h))
    for r in range(rows + 1):
        y = oy + r * CELL_SIZE
        pygame.draw.line(screen, COLOR_GRID, (ox, y), (ox + field_w, y))
    pygame.draw.rect(screen, COLOR_BORDER, (ox, oy, field_w, field_h), width=2)

    small = get_font(16)
    hold_x = GAP
    screen.blit(small.render("HOLD", True, COLOR_TEXT), (hold_x, oy))
    _draw_mini_piece(screen, game.hold_type, hold_x, oy + 24)

    y = oy + 120
    for label_text, value in (("SCORE", game.scorer.score),
                              ("LEVEL", game.scorer.level),
                              ("LINES", game.scorer.lines)):
        screen.blit(small.render(label_text, True, COLOR_TEXT), (hold_x, y))
        screen.blit(small.render(str(value), True, (255, 255, 160)), (hold_x, y + 18))
        y += 50

    next_x = ox + field_w + GAP
    screen.blit(small.render("NEXT", True, COLOR_TEXT), (next_x, oy))
    ny = oy + 24
    for t in game.next_types(3):
        _draw_mini_piece(screen, t, next_x, ny)
        ny += 70

    # 라인 클리어 / 레벨업 플래시 (0~1 세기)
    if flash > 0.0:
        overlay = pygame.Surface((field_w, field_h))
        overlay.set_alpha(int(140 * min(1.0, flash)))
        overlay.fill((255, 255, 255))
        screen.blit(overlay, (ox, oy))
        if flash_text:
            ft = font.render(flash_text, True, COLOR_HILITE)
            screen.blit(ft, (ox + field_w // 2 - ft.get_width() // 2,
                             oy + field_h // 2 - 60))

    if paused:
        overlay = pygame.Surface((field_w, field_h))
        overlay.set_alpha(160)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (ox, oy))
        label = font.render("PAUSED", True, (240, 240, 120))
        screen.blit(label, (ox + field_w // 2 - 60, oy + field_h // 2))


# ---------------------------------------------------------------- 메뉴 렌더
def draw_center_menu(screen, title, items, selected, font, subtitle=None):
    screen.fill(COLOR_BG)
    cx = WINDOW_WIDTH // 2
    tfont = get_font(40, bold=True)
    t = tfont.render(title, True, COLOR_HILITE)
    screen.blit(t, (cx - t.get_width() // 2, 80))
    if subtitle:
        sfont = get_font(18)
        s = sfont.render(subtitle, True, COLOR_TEXT)
        screen.blit(s, (cx - s.get_width() // 2, 140))
    y = 220
    for i, item in enumerate(items):
        color = COLOR_HILITE if i == selected else COLOR_TEXT
        prefix = "> " if i == selected else "  "
        line = font.render(prefix + item, True, color)
        screen.blit(line, (cx - line.get_width() // 2, y))
        y += 48


def draw_ranking(screen, scores, font):
    screen.fill(COLOR_BG)
    cx = WINDOW_WIDTH // 2
    tfont = get_font(36, bold=True)
    t = tfont.render("RANKING", True, COLOR_HILITE)
    screen.blit(t, (cx - t.get_width() // 2, 40))
    small = get_font(20)
    y = 110
    if not scores:
        line = small.render("(기록 없음)", True, COLOR_TEXT)
        screen.blit(line, (cx - line.get_width() // 2, y))
    else:
        for i, e in enumerate(scores):
            txt = f"{i + 1:2d}.  {e.get('name', '---'):<6}  {e.get('score', 0):>8}"
            line = small.render(txt, True, COLOR_TEXT)
            screen.blit(line, (cx - 140, y))
            y += 32
    hint = small.render("Esc / Enter: 뒤로", True, COLOR_GHOST)
    screen.blit(hint, (cx - hint.get_width() // 2, WINDOW_HEIGHT - 50))


def draw_settings(screen, settings, selected, font):
    screen.fill(COLOR_BG)
    cx = WINDOW_WIDTH // 2
    tfont = get_font(36, bold=True)
    t = tfont.render("SETTINGS", True, COLOR_HILITE)
    screen.blit(t, (cx - t.get_width() // 2, 40))
    small = get_font(20)
    rows = [
        ("사운드", "ON" if settings["sound"] else "OFF"),
        ("볼륨", f"{int(settings['volume'] * 100)}%"),
        ("뒤로", ""),
    ]
    y = 160
    for i, (label, value) in enumerate(rows):
        color = COLOR_HILITE if i == selected else COLOR_TEXT
        prefix = "> " if i == selected else "  "
        line = small.render(f"{prefix}{label}   {value}", True, color)
        screen.blit(line, (cx - 120, y))
        y += 44
    hint = small.render("←/→: 변경   ↑/↓: 이동   Enter: 선택", True, COLOR_GHOST)
    screen.blit(hint, (cx - hint.get_width() // 2, WINDOW_HEIGHT - 50))


# ---------------------------------------------------------------- 메인 루프
def main() -> int:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(app_title())
    clock = pygame.time.Clock()
    font = get_font(28, bold=True)

    settings = storage.load_settings()
    audio = Audio(sound_on=settings["sound"], volume=settings["volume"])

    scene = MENU
    menu_items = ["시작", "랭킹", "설정", "종료"]
    menu_sel = 0
    settings_sel = 0

    game = None
    gravity_acc = 0
    move_dir = 0
    das_timer = arr_timer = 0
    pending_score = None  # 게임오버 시 저장할 점수(한 번만 저장)
    flash = 0.0           # 플래시 세기(0~1), 매 프레임 감쇠
    flash_text = None

    def start_game():
        nonlocal game, gravity_acc, move_dir, das_timer, arr_timer, pending_score
        game = Game()
        gravity_acc = 0
        move_dir = das_timer = arr_timer = 0
        pending_score = None
        audio.play_music(loop=True)

    running = True
    while running:
        dt = clock.tick(TARGET_FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if event.type != pygame.KEYDOWN and event.type != pygame.KEYUP:
                continue

            if event.type == pygame.KEYUP:
                if scene == PLAYING:
                    if event.key == pygame.K_LEFT and move_dir == -1:
                        move_dir = 0
                    elif event.key == pygame.K_RIGHT and move_dir == +1:
                        move_dir = 0
                continue

            # KEYDOWN
            key = event.key
            if scene == MENU:
                if key in (pygame.K_UP, pygame.K_w):
                    menu_sel = (menu_sel - 1) % len(menu_items)
                elif key in (pygame.K_DOWN, pygame.K_s):
                    menu_sel = (menu_sel + 1) % len(menu_items)
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    choice = menu_items[menu_sel]
                    if choice == "시작":
                        start_game()
                        scene = PLAYING
                    elif choice == "랭킹":
                        scene = RANKING
                    elif choice == "설정":
                        settings_sel = 0
                        scene = SETTINGS
                    elif choice == "종료":
                        running = False
                elif key == pygame.K_ESCAPE:
                    running = False

            elif scene == PLAYING:
                if key in (pygame.K_ESCAPE, pygame.K_p):
                    scene = PAUSED
                    if audio.enabled:
                        pygame.mixer.music.pause()
                elif key == pygame.K_LEFT:
                    game.move_left()
                    audio.play("move")
                    move_dir, das_timer, arr_timer = -1, 0, 0
                elif key == pygame.K_RIGHT:
                    game.move_right()
                    audio.play("move")
                    move_dir, das_timer, arr_timer = +1, 0, 0
                elif key == pygame.K_DOWN:
                    game.soft_drop(); gravity_acc = 0
                elif key == pygame.K_SPACE:
                    game.hard_drop(); gravity_acc = 0
                    audio.play("harddrop")
                elif key in (pygame.K_UP, pygame.K_x):
                    if game.rotate_cw():
                        audio.play("rotate")
                elif key in (pygame.K_z, pygame.K_LCTRL, pygame.K_RCTRL):
                    if game.rotate_ccw():
                        audio.play("rotate")
                elif key == pygame.K_c:
                    game.hold()

            elif scene == PAUSED:
                if key in (pygame.K_ESCAPE, pygame.K_p):
                    scene = PLAYING
                    if audio.enabled and audio.sound_on:
                        pygame.mixer.music.unpause()
                elif key == pygame.K_q:
                    scene = MENU
                    audio.stop_music()

            elif scene == GAMEOVER:
                if key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    scene = MENU

            elif scene == RANKING:
                if key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    scene = MENU

            elif scene == SETTINGS:
                if key in (pygame.K_UP, pygame.K_w):
                    settings_sel = (settings_sel - 1) % 3
                elif key in (pygame.K_DOWN, pygame.K_s):
                    settings_sel = (settings_sel + 1) % 3
                elif key in (pygame.K_LEFT, pygame.K_RIGHT):
                    if settings_sel == 0:  # 사운드 토글
                        settings["sound"] = not settings["sound"]
                        audio.set_sound_on(settings["sound"])
                        storage.save_settings(settings)
                    elif settings_sel == 1:  # 볼륨
                        step = 0.1 if key == pygame.K_RIGHT else -0.1
                        settings["volume"] = round(
                            min(1.0, max(0.0, settings["volume"] + step)), 1)
                        audio.set_volume(settings["volume"])
                        storage.save_settings(settings)
                elif key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    if settings_sel == 2 or key == pygame.K_ESCAPE:
                        storage.save_settings(settings)
                        scene = MENU

        # --- 업데이트 ---
        if flash > 0.0:
            flash = max(0.0, flash - dt / 300.0)  # 약 0.3초에 걸쳐 감쇠

        if scene == PLAYING and game is not None:
            if game.game_over:
                scene = GAMEOVER
                audio.stop_music()
                audio.play("gameover")
                if pending_score is None:
                    pending_score = game.scorer.score
                    if storage.is_high_score(pending_score):
                        storage.add_score("YOU", pending_score)
            else:
                if move_dir != 0:
                    das_timer += dt
                    if das_timer >= DAS_DELAY_MS:
                        arr_timer += dt
                        while arr_timer >= ARR_RATE_MS:
                            arr_timer -= ARR_RATE_MS
                            game.move_left() if move_dir < 0 else game.move_right()
                gravity_acc += dt
                if gravity_acc >= game.scorer.interval_ms:
                    gravity_acc = 0
                    game.step_gravity()

                # 피드백 이벤트 소비
                cleared, level_up, _locked = game.consume_events()
                if cleared:
                    audio.play("lineclear")
                    flash = 1.0
                    flash_text = ("TETRIS!" if cleared == 4
                                  else f"{cleared} LINE" + ("S" if cleared > 1 else ""))
                if level_up:
                    flash = 1.0
                    flash_text = f"LEVEL {game.scorer.level}"

        # --- 렌더 ---
        if scene == MENU:
            draw_center_menu(screen, "TETRIS", menu_items, menu_sel, font,
                             subtitle="↑↓ 이동 · Enter 선택")
        elif scene in (PLAYING, PAUSED):
            screen.fill(COLOR_BG)
            draw_game(screen, game, font, paused=(scene == PAUSED),
                      flash=flash, flash_text=flash_text)
        elif scene == GAMEOVER:
            screen.fill(COLOR_BG)
            draw_game(screen, game, font)
            cx = WINDOW_WIDTH // 2
            label = font.render("GAME OVER", True, (240, 80, 80))
            screen.blit(label, (cx - label.get_width() // 2, WINDOW_HEIGHT // 2 - 40))
            small = get_font(18)
            s2 = small.render(f"SCORE {game.scorer.score}  ·  Enter: 메뉴", True, COLOR_TEXT)
            screen.blit(s2, (cx - s2.get_width() // 2, WINDOW_HEIGHT // 2 + 8))
        elif scene == RANKING:
            draw_ranking(screen, storage.load_scores(), font)
        elif scene == SETTINGS:
            draw_settings(screen, settings, settings_sel, font)

        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
