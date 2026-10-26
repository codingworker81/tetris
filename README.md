# Tetris

클래식 테트리스 — **PC(Python/Pygame)** 버전과 **웹 PWA**(안드로이드 · 아이폰 · PC 브라우저) 버전.

## 웹으로 플레이 / 설치 (GitHub Pages)

배포 URL: **https://codingworker81.github.io/tetris/**

- **안드로이드**: 크롬으로 위 URL 접속 → 메뉴 "홈 화면에 추가" (또는 화면의 **앱 설치** 버튼) → 앱처럼 실행
- **아이폰**: 사파리로 접속 → 공유 → "홈 화면에 추가"
- **PC**: 브라우저로 접속해 바로 플레이 (키보드 조작)

오프라인에서도 동작합니다(서비스워커 캐시).

### 조작
| 동작 | 키보드 | 터치 |
|------|--------|------|
| 이동 | ← → | ◀ ▶ |
| 소프트드롭 | ↓ | ▼ 소프트 |
| 하드드롭 | Space | ⬇ 하드드롭 |
| 시계 회전 | ↑ / X | ↻ |
| 반시계 회전 | Z | ↺ |
| 홀드 | C | HOLD |
| 일시정지 | P / Esc | ⏸ |

## 구성

```
docs/        ← 웹 PWA (GitHub Pages가 이 폴더를 서비스)
  index.html, style.css, tetris.js, manifest.webmanifest, sw.js, icons/
src/         ← PC 버전 (Python/Pygame) 순수 로직 + 렌더
tests/       ← PC 버전 pytest (93개)
tools/       ← 아이콘/효과음 생성, 웹 로직 검증 스크립트
```

웹 버전의 게임 로직(SRS 회전·7-bag·점수/레벨/중력·라인클리어·홀드·고스트)은 PC 버전의 순수 로직 모듈을 JavaScript로 1:1 포팅했으며, `tools/test_web_logic.js`로 검증합니다(33개 통과).

## 개발

### PC 버전
```
.venv\Scripts\python.exe -m pytest        # 테스트
.venv\Scripts\python.exe -m PyInstaller tetris.spec   # exe 빌드
```

### 웹 버전 로직 검증
```
node tools/test_web_logic.js
```

### 로컬에서 웹 미리보기
```
.venv\Scripts\python.exe -m http.server 8777 --bind 127.0.0.1 --directory docs
```
