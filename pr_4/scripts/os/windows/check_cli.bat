@echo off
REM ===========================================================================
REM Этап 1. Проверка всех параметров командной строки depviz (Windows).
REM Запуск: python -m depviz ... (PYTHONPATH=src)
REM Переменная PYTHON может задавать путь к python.exe вручную.
REM ===========================================================================
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%..\..\.."
pushd "%ROOT%" >nul
set "ROOT=%CD%"
popd >nul

if not defined PYTHON set "PYTHON=python"
set "PYTHONPATH=%ROOT%\src"
set "SAMPLE=%ROOT%\test_repo\sample.txt"

set PASSED=0
set FAILED=0

echo.
echo === Справка и версия ===
call :expect 0 "--help" --help
call :expect 0 "-h" -h
call :expect 0 "--version" --version
call :expect 0 "-V" -V

echo.
echo === Минимальный запуск ===
call :expect 0 "--package guava" --package guava
call :expect 0 "-p guava" -p guava
call :expect 0 "--package=guava" --package=guava
call :expect 0 "groupId:artifactId" --package com.google.guava:guava

echo.
echo === Все параметры вместе ===
call :expect 0 "все параметры" --package com.google.guava:guava --repo https://repo.maven.apache.org/maven2 --package-version 32.1.2 --output graph.png --ascii-tree --filter guava

echo.
echo === Тестовый репозиторий ===
call :expect 0 "--test-repo с файлом" --package A --repo "%SAMPLE%" --test-repo

echo.
echo === Обработка ошибок: общие ===
call :expect 2 "без параметров" 
call :expect 2 "неизвестный параметр" --package guava --bogus
call :expect 2 "параметр без значения" --package
call :expect 2 "пустое значение через =" --package=
call :expect 2 "позиционный аргумент" guava
call :expect 2 "флаг со значением" --package guava --ascii-tree=true

echo.
echo === Обработка ошибок: параметры ===
call :expect 2 "недопустимое имя пакета" --package "bad name!"
call :expect 2 "не URL в реальном режиме" --package guava --repo not-a-url
call :expect 2 "URL в тестовом режиме" --package guava --repo https://example.com/repo --test-repo
call :expect 2 "файл не найден" --package guava --repo "%TEMP%\нет-такого.txt" --test-repo
call :expect 2 "недопустимая версия" --package guava --package-version "1.0 /beta"
call :expect 2 "не .png" --package guava --output graph.jpg
call :expect 2 "пустой фильтр" --package guava --filter ""

echo.
echo Итого: успешно %PASSED%, провалено %FAILED%
if not "%FAILED%"=="0" exit /b 1
exit /b 0

:expect
REM %1 — ожидаемый код, %2 — описание, далее — аргументы depviz.
set "EXPECTED=%~1"
set "NAME=%~2"
shift
shift
"%PYTHON%" -m depviz %* >nul 2>&1
set "CODE=!ERRORLEVEL!"
if "!CODE!"=="%EXPECTED%" (
    echo   [PASS] %NAME% ^(код !CODE!^)
    set /a PASSED+=1
) else (
    echo   [FAIL] %NAME%: ожидался код %EXPECTED%, получен !CODE!
    set /a FAILED+=1
)
exit /b 0
