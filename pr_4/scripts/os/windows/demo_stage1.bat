@echo off
REM ===========================================================================
REM Этап 1. Демонстрация конфигурации depviz (Windows).
REM ===========================================================================
setlocal

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%..\..\.."
pushd "%ROOT%" >nul
set "ROOT=%CD%"
popd >nul

if not defined PYTHON set "PYTHON=python"
set "PYTHONPATH=%ROOT%\src"
set "SAMPLE=%ROOT%\test_repo\sample.txt"

echo ################################################################
echo # Этап 1. Минимальный прототип с конфигурацией (depviz)
echo ################################################################

echo.
echo $ depviz --help
"%PYTHON%" -m depviz --help
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ depviz --version
"%PYTHON%" -m depviz --version
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ depviz --package guava
"%PYTHON%" -m depviz --package guava
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ depviz --package com.google.guava:guava --package-version 32.1.2 --output graph.png --ascii-tree --filter guava
"%PYTHON%" -m depviz --package com.google.guava:guava --package-version 32.1.2 --output graph.png --ascii-tree --filter guava
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ depviz --package A --repo test_repo\sample.txt --test-repo
"%PYTHON%" -m depviz --package A --repo "%SAMPLE%" --test-repo
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ depviz ^(нет --package^)
"%PYTHON%" -m depviz
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ depviz --package guava --output graph.jpg
"%PYTHON%" -m depviz --package guava --output graph.jpg
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ depviz --package guava --repo not-a-url
"%PYTHON%" -m depviz --package guava --repo not-a-url
echo [код возврата: %ERRORLEVEL%]

echo.
echo Полная проверка параметров:
call "%SCRIPT_DIR%check_cli.bat" >nul
echo check_cli.bat: все проверки пройдены ^(код %ERRORLEVEL%^)
endlocal
