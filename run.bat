@echo off
:: Запуск всех проверок этапа 1 pr_4 (аналог pr_3/scripts/run_all.bat в корне репозитория)
setlocal enabledelayedexpansion

set "REPO_ROOT=%~dp0"
set "PR4=%REPO_ROOT%pr_4"

echo ==> Запуск юнит-тестов pr_4...
set "PYTHONPATH=%PR4%\src"
python3 -m unittest discover -s "%PR4%\tests" -v

if errorlevel 1 (
    echo ОШИБКА: юнит-тесты не прошли.
    exit /b 1
)

echo ==> Запуск проверки CLI pr_4...
call "%PR4%\scripts\run_all.bat"

if errorlevel 1 (
    echo ОШИБКА: проверка CLI не прошла.
    exit /b 1
)

echo ==> Все проверки пройдены.
