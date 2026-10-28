@echo off
REM ===========================================================================
REM Этап 2. Проверка всех параметров командной строки эмулятора (Windows).
REM Сборка: cmake -S pr_3 -B pr_3\build && cmake --build pr_3\build --config Release
REM Переменная EMU может задавать путь к emu.exe вручную.
REM ===========================================================================
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
set "ROOT=%SCRIPT_DIR%..\..\.."
pushd "%ROOT%" >nul
set "ROOT=%CD%"
popd >nul

if not defined EMU set "EMU=%ROOT%\build\bin\Release\emu.exe"
if not exist "%EMU%" if exist "%ROOT%\build\bin\emu.exe" set "EMU=%ROOT%\build\bin\emu.exe"
if not exist "%EMU%" (
    echo эмулятор не найден: "%EMU%"
    echo соберите проект и при необходимости задайте переменную EMU.
    exit /b 1
)

set "VFS=%ROOT%\vfs\demo.csv"
set "STARTUP=%ROOT%\scripts\stage2.emu"
set "TMP_IN=%TEMP%\emu_interactive_%RANDOM%.emu"
> "%TMP_IN%" echo ls /
>>"%TMP_IN%" echo cd "/tmp/каталог с пробелом"
>>"%TMP_IN%" echo exit 0

set PASSED=0
set FAILED=0

echo.
echo === Справка и версия ===
call :expect 0 "--help" --help
call :expect 0 "-h" -h
call :expect 0 "--version" --version

echo.
echo === Запуск без параметров (интерактивный режим) ===
call :expect 0 "без параметров" ^< "%TMP_IN%"

echo.
echo === Параметр --vfs ===
call :expect 0 "--vfs ^<путь^>" --vfs "%VFS%" ^< "%TMP_IN%"
call :expect 0 "--vfs=^<путь^>" "--vfs=%VFS%" ^< "%TMP_IN%"

echo.
echo === Параметр --script ===
call :expect 0 "--script ^<путь^>" --script "%STARTUP%"
call :expect 0 "--script=^<путь^>" "--script=%STARTUP%"

echo.
echo === Совместное использование параметров ===
call :expect 0 "--vfs + --script" --vfs "%VFS%" --script "%STARTUP%"
call :expect 0 "--script + --interactive" --script "%STARTUP%" --interactive ^< "%TMP_IN%"
call :expect 0 "--no-debug" --no-debug --script "%STARTUP%"

echo.
echo === Обработка ошибок командной строки ===
call :expect 2 "неизвестный параметр" --bogus
call :expect 2 "параметр без значения" --vfs
call :expect 2 "--interactive без --script" --interactive
call :expect 1 "отсутствующий стартовый скрипт" --script "%TEMP%\нет-такого.emu"

del "%TMP_IN%" >nul 2>&1
echo.
echo Итого: успешно %PASSED%, провалено %FAILED%
if not "%FAILED%"=="0" exit /b 1
exit /b 0

:expect
REM %1 — ожидаемый код, %2 — описание, далее — аргументы эмулятора.
set "EXPECTED=%~1"
set "NAME=%~2"
shift
shift
"%EMU%" %* >nul 2>&1
set "CODE=!ERRORLEVEL!"
if "!CODE!"=="%EXPECTED%" (
    echo   [PASS] %NAME% ^(код !CODE!^)
    set /a PASSED+=1
) else (
    echo   [FAIL] %NAME%: ожидался код %EXPECTED%, получен !CODE!
    set /a FAILED+=1
)
exit /b 0
