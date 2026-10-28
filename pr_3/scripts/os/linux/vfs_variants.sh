#!/usr/bin/env bash
# ============================================================================
# Этап 3. Проверка работы эмулятора с различными вариантами VFS.
#
#   vfs/minimal.csv — минимальная VFS (корень и один файл);
#   vfs/multi.csv   — несколько файлов и каталогов (два уровня);
#   vfs/demo.csv    — не менее трёх уровней вложенности, base64, кириллица.
#
# Дополнительно проверяются ошибки загрузки CSV.
# ============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
EMU="${EMU:-$ROOT/build/bin/emu}"

PASSED=0
FAILED=0

if [ ! -x "$EMU" ]; then
    printf 'эмулятор не найден: %s\nсоберите проект: cmake -S pr_3 -B pr_3/build && cmake --build pr_3/build\n' "$EMU" >&2
    exit 1
fi

section() {
    printf '\n=== %s ===\n' "$1"
}

# expect <описание> <ожидаемый код> <входные команды> <аргументы эмулятора...>
expect() {
    local name="$1"
    local expected="$2"
    local input="$3"
    shift 3
    local output code
    output="$(printf '%s\n' "$input" | "$EMU" "$@" 2>&1)"
    code=$?
    printf '%s\n' "$output"
    if [ "$code" -eq "$expected" ]; then
        printf '  [PASS] %s (код %d)\n' "$name" "$code"
        PASSED=$((PASSED + 1))
    else
        printf '  [FAIL] %s: ожидался код %d, получен %d\n' "$name" "$expected" "$code"
        FAILED=$((FAILED + 1))
    fi
}

section "Минимальная VFS (vfs/minimal.csv)"
expect "просмотр корня" 0 'ls /
ls /hello.txt
exit 0' --vfs "$ROOT/vfs/minimal.csv" --no-debug

section "Несколько файлов (vfs/multi.csv)"
expect "просмотр двух уровней" 0 'ls /
ls /etc
cd /etc
ls
cd /
ls /tmp
exit 0' --vfs "$ROOT/vfs/multi.csv" --no-debug

section "Не менее трёх уровней (vfs/demo.csv)"
expect "обход четырёх уровней" 0 'ls /
cd /home/user/docs
ls
ls /var/log
ls /tmp
exit 0' --vfs "$ROOT/vfs/demo.csv" --no-debug

section "Ошибки загрузки VFS"
expect "файл VFS не найден" 1 'exit 0' --vfs "$ROOT/vfs/нет-такого.csv" --no-debug
expect "не CSV-заголовок" 1 'exit 0' --vfs "$ROOT/vfs/bad/no-header.csv" --no-debug
expect "дубликат имени" 1 'exit 0' --vfs "$ROOT/vfs/bad/duplicate.csv" --no-debug
expect "неизвестный родитель" 1 'exit 0' --vfs "$ROOT/vfs/bad/unknown-parent.csv" --no-debug
expect "ошибка base64" 1 'exit 0' --vfs "$ROOT/vfs/bad/bad-base64.csv" --no-debug
expect "неизвестная кодировка" 1 'exit 0' --vfs "$ROOT/vfs/bad/bad-encoding.csv" --no-debug
expect "незакрытая кавычка в CSV" 1 'exit 0' --vfs "$ROOT/vfs/bad/bad-quotes.csv" --no-debug

printf '\nИтого: успешно %d, провалено %d\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
