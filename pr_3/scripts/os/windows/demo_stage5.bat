@echo off
REM ===========================================================================
REM Этап 5. Демонстрация touch и rmdir (Windows).
REM Доказывается, что изменения VFS выполняются только в памяти: копия
REM CSV-файла до и после работы совпадает, созданные файлы не появляются
REM на физическом диске.
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

set "VFS=%ROOT%\vfs\demo.csv"
set "BEFORE=%TEMP%\emu_vfs_before_%RANDOM%.csv"
set "TMP_IN=%TEMP%\emu_stage5_%RANDOM%.emu"

echo ################################################################
echo # Этап 5. Дополнительные команды: touch и rmdir
echo ################################################################

echo.
echo --- Все параметры командной строки ---
"%EMU%" --help
echo [--help, код: %ERRORLEVEL%]
"%EMU%" --version
echo [--version, код: %ERRORLEVEL%]
"%EMU%" --vfs
echo [--vfs без значения, код: %ERRORLEVEL%]

echo.
echo --- Варианты VFS ---
> "%TMP_IN%" echo tree /
>>"%TMP_IN%" echo touch /new.txt
>>"%TMP_IN%" echo ls -l /
>>"%TMP_IN%" echo exit 0
"%EMU%" --vfs "%ROOT%\vfs\minimal.csv" --no-debug < "%TMP_IN%"
echo [minimal.csv, код: %ERRORLEVEL%]

echo.
echo $ emu --vfs vfs\demo.csv --script scripts\stage5.emu
"%EMU%" --vfs "%VFS%" --script "%ROOT%\scripts\stage5.emu"
echo [код возврата: %ERRORLEVEL%]

echo.
echo --- Доказательство: изменения только в памяти ---
copy /y "%VFS%" "%BEFORE%" >nul
> "%TMP_IN%" echo touch /home/user/new.txt
>>"%TMP_IN%" echo rmdir /tmp/empty
>>"%TMP_IN%" echo touch /tmp/только-в-памяти.txt
>>"%TMP_IN%" echo exit 0
"%EMU%" --vfs "%VFS%" --no-debug < "%TMP_IN%" >nul
fc /b "%BEFORE%" "%VFS%" >nul
if errorlevel 1 (
    echo   [FAIL] CSV-файл VFS изменился!
) else (
    echo   [PASS] CSV-файл VFS не изменён
)
if exist "%ROOT%\home\user\new.txt" (
    echo   [FAIL] файл из VFS появился на диске
) else (
    echo   [PASS] созданные в VFS файлы отсутствуют на физическом диске
)
del "%BEFORE%" >nul 2>&1
del "%TMP_IN%" >nul 2>&1

echo.
echo Полная проверка параметров:
call "%SCRIPT_DIR%check_cli.bat"
echo.
echo Полная проверка вариантов VFS:
call "%SCRIPT_DIR%vfs_variants.bat"
