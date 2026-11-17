@echo off
:: Запуск pr_4 (этап 1).
::   run.bat          -- CLI depviz (аргументы пробрасываются)
::   run.bat test     -- юнит-тесты
::   run.bat style    -- проверка стиля
::   run.bat check    -- полный прогон проверок
setlocal
cd /d "%~dp0"

if "%1"=="test" (
    python -m unittest discover -s pr_4\tests -t .
    exit /b %ERRORLEVEL%
)
if "%1"=="style" (
    python pr_4\scripts\check_style.py .
    exit /b %ERRORLEVEL%
)
if "%1"=="check" (
    python pr_4\scripts\check_style.py .
    set "PYTHONPATH=pr_4\src"
    python -m unittest discover -s pr_4\tests -t .
    call pr_4\scripts\run_all.bat
    exit /b %ERRORLEVEL%
)

set "PYTHONPATH=pr_4\src"
python -m depviz %*
