@echo off
REM ===========================================================================
REM Этап 3. Проверка работы эмулятора с различными вариантами VFS (Windows).
REM   vfs\minimal.csv — минимальная VFS;
REM   vfs\multi.csv   — несколько файлов;
REM   vfs\demo.csv    — не менее трёх уровней вложенности, base64, кириллица.
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

set "TMP_IN=%TEMP%\emu_vfs_%RANDOM%.emu"

echo.
echo === Минимальная VFS (vfs\minimal.csv) ===
> "%TMP_IN%" echo ls /
>>"%TMP_IN%" echo ls /hello.txt
>>"%TMP_IN%" echo exit 0
"%EMU%" --vfs "%ROOT%\vfs\minimal.csv" --no-debug < "%TMP_IN%"
echo [код: %ERRORLEVEL%]

echo.
echo === Несколько файлов (vfs\multi.csv) ===
> "%TMP_IN%" echo ls /
>>"%TMP_IN%" echo ls /etc
>>"%TMP_IN%" echo cd /etc
>>"%TMP_IN%" echo ls
>>"%TMP_IN%" echo exit 0
"%EMU%" --vfs "%ROOT%\vfs\multi.csv" --no-debug < "%TMP_IN%"
echo [код: %ERRORLEVEL%]

echo.
echo === Не менее трёх уровней (vfs\demo.csv) ===
> "%TMP_IN%" echo ls /
>>"%TMP_IN%" echo cd /home/user/docs
>>"%TMP_IN%" echo ls
>>"%TMP_IN%" echo ls /var/log
>>"%TMP_IN%" echo ls /tmp
>>"%TMP_IN%" echo exit 0
"%EMU%" --vfs "%ROOT%\vfs\demo.csv" --no-debug < "%TMP_IN%"
echo [код: %ERRORLEVEL%]

echo.
echo === Ошибки загрузки VFS (ожидаются коды 1) ===
"%EMU%" --vfs "%ROOT%\vfs\нет-такого.csv" --no-debug
echo [нет файла, код: %ERRORLEVEL%]
"%EMU%" --vfs "%ROOT%\vfs\bad\no-header.csv" --no-debug
echo [нет заголовка, код: %ERRORLEVEL%]
"%EMU%" --vfs "%ROOT%\vfs\bad\duplicate.csv" --no-debug
echo [дубликат, код: %ERRORLEVEL%]
"%EMU%" --vfs "%ROOT%\vfs\bad\unknown-parent.csv" --no-debug
echo [неизвестный родитель, код: %ERRORLEVEL%]
"%EMU%" --vfs "%ROOT%\vfs\bad\bad-base64.csv" --no-debug
echo [ошибка base64, код: %ERRORLEVEL%]
"%EMU%" --vfs "%ROOT%\vfs\bad\bad-encoding.csv" --no-debug
echo [кодировка, код: %ERRORLEVEL%]
"%EMU%" --vfs "%ROOT%\vfs\bad\bad-quotes.csv" --no-debug
echo [кавычки в CSV, код: %ERRORLEVEL%]

del "%TMP_IN%" >nul 2>&1
exit /b 0
