@echo off
REM ===========================================================================
REM Полный прогон этапа 1 (Windows): юнит-тесты и параметры командной строки.
REM ===========================================================================
setlocal

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."
pushd "%ROOT%" >nul
set "ROOT=%CD%"
popd >nul

if not defined PYTHON set "PYTHON=python"
set "PYTHONPATH=%ROOT%\src"

set PASSED=0
set FAILED=0

"%PYTHON%" -m unittest discover -s "%ROOT%\tests" >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo [PASS] юнит-тесты конфигурации
    set /a PASSED+=1
) else (
    echo [FAIL] юнит-тесты конфигурации
    set /a FAILED+=1
)

call "%SCRIPT_DIR%\os\windows\check_cli.bat" >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo [PASS] параметры командной строки
    set /a PASSED+=1
) else (
    echo [FAIL] параметры командной строки
    set /a FAILED+=1
)

echo.
echo Итого: успешно %PASSED%, провалено %FAILED%
if not "%FAILED%"=="0" exit /b 1
exit /b 0
