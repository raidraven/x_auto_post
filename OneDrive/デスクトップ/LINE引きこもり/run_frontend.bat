@echo off
chcp 65001 > nul
echo === フロントエンド起動 ===
echo ブラウザで http://localhost:5500/frontend/index.html を開いてください
cd /d "%~dp0"

where python > nul 2>&1
if %errorlevel% neq 0 (
  echo [エラー] Python が見つかりません。
  pause
  exit /b 1
)

python -m http.server 5500
