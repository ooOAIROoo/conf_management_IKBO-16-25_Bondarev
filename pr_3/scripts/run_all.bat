@echo off
REM ===========================================================================
REM Полный прогон эмулятора: этапы 2–5, параметры командной строки и VFS.
REM ===========================================================================
setlocal

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%.."
pushd "%ROOT%" >nul
set "ROOT=%CD%"
popd >nul

if not defined EMU set "EMU=%ROOT%\build\bin\Release\emu.exe"
if not exist "%EMU%" if exist "%ROOT%\build\bin\emu.exe" set "EMU=%ROOT%\build\bin\emu.exe"
if not exist "%EMU%" (
    echo эмулятор не найден: "%EMU%"
    exit /b 1
)

"%EMU%" --vfs "%ROOT%\vfs\demo.csv" --script "%ROOT%\scripts\stage2.emu" >nul 2>&1
echo [этап 2] код: %ERRORLEVEL%
"%EMU%" --vfs "%ROOT%\vfs\demo.csv" --script "%ROOT%\scripts\stage3.emu" >nul 2>&1
echo [этап 3] код: %ERRORLEVEL%
"%EMU%" --vfs "%ROOT%\vfs\demo.csv" --script "%ROOT%\scripts\stage4.emu" >nul 2>&1
echo [этап 4] код: %ERRORLEVEL%
"%EMU%" --vfs "%ROOT%\vfs\demo.csv" --script "%ROOT%\scripts\stage5.emu" >nul 2>&1
echo [этап 5] код: %ERRORLEVEL%

echo.
call "%SCRIPT_DIR%os\windows\check_cli.bat"
echo.
call "%SCRIPT_DIR%os\windows\vfs_variants.bat"
