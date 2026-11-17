@echo off
:: Запуск pr_4 (этап 1): "run.bat test" — юнит-тесты, иначе — CLI depviz.
setlocal
cd /d "%~dp0"

if "%1"=="test" (
    python -m unittest discover -s pr_4\tests -t .
) else (
    set "PYTHONPATH=pr_4\src"
    python -m depviz %*
)
