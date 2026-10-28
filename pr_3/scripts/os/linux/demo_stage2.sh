#!/usr/bin/env bash
# ============================================================================
# Этап 2. Демонстрация конфигурации эмулятора в реальной ОС (Linux/macOS).
#
# Показывает отладочный вывод параметров, выполнение стартового скрипта,
# а также обработку ошибок командной строки и ошибок внутри скрипта.
# ============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
EMU="${EMU:-$ROOT/build/bin/emu}"
VFS="${VFS:-$ROOT/README.md}"
STARTUP="$ROOT/scripts/stage2.emu"

show() {
    printf '\n$ %s\n' "$1"
    shift
    "$@"
    printf '[код возврата: %d]\n' "$?"
}

if [ ! -x "$EMU" ]; then
    printf 'эмулятор не найден: %s\n' "$EMU" >&2
    exit 1
fi

printf '################################################################\n'
printf '# Этап 2. Конфигурация эмулятора\n'
printf '################################################################\n'

# Все поддерживаемые параметры командной строки.
show "emu --help" "$EMU" --help
show "emu --version" "$EMU" --version

show "emu --vfs README.md --no-debug" \
    bash -c "printf 'ls /\\nexit 0\\n' | '$EMU' --vfs '$VFS' --no-debug"

show "emu --script scripts/stage2.emu" "$EMU" --script "$STARTUP"

show "emu --vfs README.md --script scripts/stage2.emu" \
    "$EMU" --vfs "$VFS" --script "$STARTUP"

# Ошибки командной строки.
show "emu --vfs (нет значения)" "$EMU" --vfs
show "emu --неизвестный-параметр" "$EMU" --неизвестный-параметр
show "emu --script нет-такого.emu" "$EMU" --script "$ROOT/scripts/нет-такого.emu"

printf '\nПолная проверка параметров:\n'
bash "$SCRIPT_DIR/check_cli.sh" > /dev/null
printf 'check_cli.sh: все проверки пройдены (код %d)\n' "$?"
