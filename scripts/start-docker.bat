@echo off
setlocal
cd /d "%~dp0.."

rem Docker Desktop is often running while "docker" is missing from PATH (Cursor, some terminals).
set "DOCKER_BIN=C:\Program Files\Docker\Docker\resources\bin"
if exist "%DOCKER_BIN%\docker.exe" (
  set "PATH=%DOCKER_BIN%;%PATH%"
) else (
  echo ERROR: Docker CLI not found at "%DOCKER_BIN%\docker.exe"
  echo Install Docker Desktop or add its bin folder to your user PATH.
  exit /b 1
)

docker version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Docker engine not reachable. Open Docker Desktop and wait until it says "Engine running".
  exit /b 1
)

echo.
echo SmartEd Support - Docker stack
echo   Chatbot UI:  http://localhost:8080
echo   API health:  http://localhost:8080/health
echo   API docs:    http://localhost:8080/docs  (proxied via nginx if configured)
echo.
echo Rebuilding images so API matches latest code (flows + Groq)...
docker compose up --build -d
if errorlevel 1 exit /b 1

echo.
echo Waiting for API health...
timeout /t 8 /nobreak >nul
curl -sS http://localhost:8080/health
echo.
echo Done. Open http://localhost:8080 in your browser.
endlocal
