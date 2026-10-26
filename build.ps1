# Tetris 빌드 스크립트 (Windows / PowerShell)
#
# 사용법 (프로젝트 루트에서):
#   .\build.ps1
#
# 수행 내용:
#   1) 가상환경 활성화(.venv) 확인
#   2) 런타임 + 빌드 의존성 설치
#   3) 효과음/아이콘 리소스 생성
#   4) PyInstaller 로 dist\Tetris.exe 빌드
#
# 결과: dist\Tetris.exe (단일 실행본, 콘솔 숨김, 아이콘 적용)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$py = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "가상환경이 없습니다. 먼저 만들어 주세요:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv"
    exit 1
}

Write-Host "[1/4] 의존성 설치..." -ForegroundColor Cyan
& $py -m pip install --quiet -r requirements.txt
& $py -m pip install --quiet -r requirements-build.txt

Write-Host "[2/4] 리소스 생성 (효과음/배경음)..." -ForegroundColor Cyan
& $py tools\make_sfx.py

Write-Host "[3/4] 아이콘 생성..." -ForegroundColor Cyan
& $py tools\make_icon.py

Write-Host "[4/4] PyInstaller 빌드..." -ForegroundColor Cyan
& $py -m PyInstaller --noconfirm --clean tetris.spec

$exe = ".\dist\Tetris.exe"
if (Test-Path $exe) {
    $size = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host "`n빌드 성공: $exe ($size MB)" -ForegroundColor Green
    Write-Host "실행: .\dist\Tetris.exe"
} else {
    Write-Host "`n빌드 실패: $exe 가 생성되지 않았습니다." -ForegroundColor Red
    exit 1
}
