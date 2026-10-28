#!/usr/bin/env bash
# ============================================================================
# Полный прогон эмулятора: этапы 2–5, параметры командной строки и VFS.
# Возвращает 0, если все проверки прошли успешно.
# ============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EMU="${EMU:-$ROOT/build/bin/emu}"

PASSED=0
FAILED=0

run() {
    local name="$1"
    shift
    "$@" > /dev/null 2>&1
    if [ "$?" -eq 0 ]; then
        printf '[PASS] %s\n' "$name"
        PASSED=$((PASSED + 1))
    else
        printf '[FAIL] %s\n' "$name"
        FAILED=$((FAILED + 1))
    fi
}

if [ ! -x "$EMU" ]; then
    printf 'эмулятор не найден: %s\n' "$EMU" >&2
    exit 1
fi

run "этап 2: стартовый скрипт" "$EMU" --vfs "$ROOT/vfs/demo.csv" --script "$ROOT/scripts/stage2.emu"
run "этап 3: VFS и команды" "$EMU" --vfs "$ROOT/vfs/demo.csv" --script "$ROOT/scripts/stage3.emu"
run "этап 4: основные команды" "$EMU" --vfs "$ROOT/vfs/demo.csv" --script "$ROOT/scripts/stage4.emu"
run "этап 5: touch и rmdir" "$EMU" --vfs "$ROOT/vfs/demo.csv" --script "$ROOT/scripts/stage5.emu"
run "параметры командной строки" bash "$SCRIPT_DIR/os/linux/check_cli.sh"
run "варианты VFS" bash "$SCRIPT_DIR/os/linux/vfs_variants.sh"

printf '\nИтого: успешно %d, провалено %d\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
