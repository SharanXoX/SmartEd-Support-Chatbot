@echo off
setlocal
cd /d "%~dp0.."

rem Prefer Docker stack when Docker CLI is available (engine may run but PATH is missing).
set "DOCKER_BIN=C:\Program Files\Docker\Docker\resources\bin"
if exist "%DOCKER_BIN%\docker.exe" (
  set "PATH=%DOCKER_BIN%;%PATH%"
  docker version >nul 2>&1
  if not errorlevel 1 (
    echo Docker detected — use scripts\start-docker.bat for http://localhost:8080
    echo Or continuing with local dev servers below...
    echo.
  )
)

echo.
echo SmartEd Support - starting API + UI
echo   Chatbot UI:  http://localhost:5173
echo   API health: http://127.0.0.1:8000/health
echo   API docs:   http://127.0.0.1:8000/docs
echo.
if not exist "node_modules\concurrently\" (
  echo Installing root dev dependencies (first run only^)...
  call npm install
)
if not exist "frontend\node_modules\vite\" (
  echo Installing frontend dependencies (first run only^)...
  pushd frontend
  call npm install
  popd
)
call npm run dev
endlocal
