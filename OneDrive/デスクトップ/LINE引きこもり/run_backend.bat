@echo off
chcp 65001 > nul
echo === バックエンド起動 ===
cd /d "%~dp0backend"

if not exist ".env" (
  echo [エラー] .env ファイルがありません。.env.example をコピーして ANTHROPIC_API_KEY を設定してください。
  pause
  exit /b 1
)

.venv\Scripts\uvicorn main:app --reload --host 0.0.0.0 --port 8000
