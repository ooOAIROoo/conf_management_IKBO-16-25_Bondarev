@echo off
REM ===========================================================================
REM Этап 4. Демонстрация основных команд (Windows).
REM Проверяются параметры командной строки, варианты VFS и команды
REM ls/cd/who/tree/uname, включая обработку ошибок.
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

echo ################################################################
echo # Этап 4. Основные команды
echo ################################################################

echo.
echo $ emu --vfs vfs\demo.csv --script scripts\stage4.emu
"%EMU%" --vfs "%ROOT%\vfs\demo.csv" --script "%ROOT%\scripts\stage4.emu"
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ emu --vfs vfs\minimal.csv --no-debug
"%EMU%" --vfs "%ROOT%\vfs\minimal.csv" --no-debug < nul
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ emu --vfs (нет значения)
"%EMU%" --vfs
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ emu --vfs vfs\bad\duplicate.csv
"%EMU%" --vfs "%ROOT%\vfs\bad\duplicate.csv" --no-debug
echo [код возврата: %ERRORLEVEL%]

echo.
echo Полная проверка параметров:
call "%SCRIPT_DIR%check_cli.bat"
echo.
echo Полная проверка вариантов VFS:
call "%SCRIPT_DIR%vfs_variants.bat"
