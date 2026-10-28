#!/usr/bin/env bash
# ============================================================================
# Этап 2. Проверка всех параметров командной строки эмулятора.
#
# Скрипт реальной ОС (Linux/macOS): запускает эмулятор в разных режимах и
# сверяет коды возврата. Сборка эмулятора должна быть выполнена заранее:
#   cmake -S pr_3 -B pr_3/build && cmake --build pr_3/build
#
# Переменные окружения:
#   EMU — путь к исполняемому файлу (по умолчанию <repo>/pr_3/build/bin/emu)
#   VFS — путь, передаваемый в --vfs (на этапе 2 содержимое не читается)
# ============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
EMU="${EMU:-$ROOT/build/bin/emu}"
VFS="${VFS:-$ROOT/vfs/demo.csv}"
STARTUP="$ROOT/scripts/stage2.emu"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

printf 'ls /\ncd "/tmp/каталог с пробелом"\nexit 0\n' > "$TMP_DIR/interactive.emu"

PASSED=0
FAILED=0

section() {
    printf '\n=== %s ===\n' "$1"
}

# expect_code <описание> <ожидаемый код> <команда...>
expect_code() {
    local name="$1"
    local expected="$2"
    shift 2
    local output code
    output="$("$@" 2>&1)"
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

if [ ! -x "$EMU" ]; then
    printf 'эмулятор не найден: %s\nсоберите проект: cmake -S pr_3 -B pr_3/build && cmake --build pr_3/build\n' "$EMU" >&2
    exit 1
fi

section "Справка и версия"
expect_code "--help" 0 "$EMU" --help
expect_code "-h" 0 "$EMU" -h
expect_code "--version" 0 "$EMU" --version

section "Запуск без параметров (интерактивный режим)"
expect_code "без параметров" 0 "$EMU" < "$TMP_DIR/interactive.emu"

section "Параметр --vfs"
expect_code "--vfs <путь>" 0 "$EMU" --vfs "$VFS" < "$TMP_DIR/interactive.emu"
expect_code "--vfs=<путь>" 0 "$EMU" "--vfs=$VFS" < "$TMP_DIR/interactive.emu"

section "Параметр --script"
expect_code "--script <путь>" 0 "$EMU" --script "$STARTUP"
expect_code "--script=<путь>" 0 "$EMU" "--script=$STARTUP"

section "Совместное использование параметров"
expect_code "--vfs + --script" 0 "$EMU" --vfs "$VFS" --script "$STARTUP"
expect_code "--script + --interactive" 0 "$EMU" --script "$STARTUP" --interactive < "$TMP_DIR/interactive.emu"
expect_code "--no-debug" 0 "$EMU" --no-debug --script "$STARTUP"

section "Обработка ошибок командной строки"
expect_code "неизвестный параметр" 2 "$EMU" --bogus
expect_code "параметр без значения" 2 "$EMU" --vfs
expect_code "--interactive без --script" 2 "$EMU" --interactive
expect_code "отсутствующий стартовый скрипт" 1 "$EMU" --script "$TMP_DIR/нет-такого.emu"

printf '\nИтого: успешно %d, провалено %d\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
