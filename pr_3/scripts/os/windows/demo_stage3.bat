@echo off
REM ===========================================================================
REM Этап 3. Демонстрация VFS (Windows): загрузка трёх вариантов VFS,
REM обход дерева, ls/cd, обработка ошибок, стартовый скрипт.
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
echo # Этап 3. Виртуальная файловая система в памяти
echo ################################################################

echo.
echo $ emu --vfs vfs\demo.csv --script scripts\stage3.emu
"%EMU%" --vfs "%ROOT%\vfs\demo.csv" --script "%ROOT%\scripts\stage3.emu"
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ emu --vfs vfs\bad\duplicate.csv
"%EMU%" --vfs "%ROOT%\vfs\bad\duplicate.csv" --no-debug
echo [код возврата: %ERRORLEVEL%]

echo.
echo $ emu --vfs vfs\bad\bad-base64.csv
"%EMU%" --vfs "%ROOT%\vfs\bad\bad-base64.csv" --no-debug
echo [код возврата: %ERRORLEVEL%]

echo.
echo Полная проверка вариантов VFS:
call "%SCRIPT_DIR%vfs_variants.bat"
