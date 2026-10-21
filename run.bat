@echo off
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
cd /d "%~dp0"

rem Without arguments, run the demo configuration.
if "%~1"=="" (
    py main.py --package demo-app --repository test-repository.json --test-repo-mode local
) else (
    py main.py %*
)

rem Save the application's exit code before PAUSE changes it.
set "APP_EXIT_CODE=%ERRORLEVEL%"
echo.
if "%APP_EXIT_CODE%"=="0" (
    echo Application finished successfully.
) else (
    echo Application finished with error code %APP_EXIT_CODE%.
)
echo.
pause
exit /b %APP_EXIT_CODE%
