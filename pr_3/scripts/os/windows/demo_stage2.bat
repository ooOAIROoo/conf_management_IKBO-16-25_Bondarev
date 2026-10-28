@echo off
REM ===========================================================================
REM Этап 2. Демонстрация конфигурации эмулятора (Windows).
REM Показывает отладочный вывод параметров и выполнение стартового скрипта.
REM ===========================================================================
setlocal

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%..\..\.."
pushd "%ROOT%" >nul
set "ROOT=%CD%"
popd >nul

if not defined EMU set "EMU=%ROOT%\build\bin\Release\emu.exe"
if not exist "%EMU%" if exist "%ROOT%\build\bin\emu.exe" set "EMU=%ROOT%\build\bin\emu.exe"
if not exist "%EMU%" (
    echo эмулятор не найден: "%EMU%"
    exit /b 1
)

set "VFS=%ROOT%\README.md"
set "STARTUP=%ROOT%\scripts\stage2.emu"

echo ################################################################
echo # Этап 2. Конфигурация эмулятора
echo ################################################################

echo.
echo $ emu --help
"%EMU%" --help
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ emu --version
"%EMU%" --version
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ emu --vfs README.md --script scripts\stage2.emu
"%EMU%" --vfs "%VFS%" --script "%STARTUP%"
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ emu --script scripts\stage2.emu --no-debug
"%EMU%" --script "%STARTUP%" --no-debug
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ emu --vfs   (нет значения)
"%EMU%" --vfs
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ emu --script нет-такого.emu
"%EMU%" --script "%ROOT%\scripts\нет-такого.emu"
echo [код возврата: %ERRORLEVEL%]

echo.
echo Полная проверка параметров:
call "%SCRIPT_DIR%check_cli.bat"
