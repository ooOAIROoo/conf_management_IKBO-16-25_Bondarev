#!/usr/bin/env bash
# ============================================================================
# Этап 4. Демонстрация основных команд в реальной ОС (Linux/macOS).
#
# Проверяются все параметры командной строки, три варианта VFS и команды
# ls/cd/who/tree/uname в различных режимах, включая обработку ошибок.
# ============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
EMU="${EMU:-$ROOT/build/bin/emu}"

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
printf '# Этап 4. Основные команды\n'
printf '################################################################\n'

# Все параметры командной строки (этап 2) — с полной VFS.
show "emu --vfs vfs/demo.csv --script scripts/stage4.emu" \
    "$EMU" --vfs "$ROOT/vfs/demo.csv" --script "$ROOT/scripts/stage4.emu"

printf '\n--- Параметры командной строки ---\n'
show "emu --help" "$EMU" --help
show "emu --version" "$EMU" --version
show "emu --vfs vfs/minimal.csv --no-debug" \
    bash -c "printf 'ls /\\nuname -a\\nexit 0\\n' | '$EMU' --vfs '$ROOT/vfs/minimal.csv' --no-debug"
show "emu --vfs vfs/multi.csv --script scripts/startup.emu --interactive" \
    bash -c "printf 'who\\nexit 0\\n' | '$EMU' --vfs '$ROOT/vfs/multi.csv' --script '$ROOT/scripts/startup.emu' --interactive"
show "emu --vfs (нет значения)" "$EMU" --vfs
show "emu --vfs vfs/bad/duplicate.csv" "$EMU" --vfs "$ROOT/vfs/bad/duplicate.csv" --no-debug

printf '\n--- Команды в интерактивном режиме (ввод через конвейер) ---\n'
show "ls -la / | uname -a | who" \
    bash -c "printf 'ls -la /\\nuname -a\\nwho\\nexit 0\\n' | '$EMU' --vfs '$ROOT/vfs/demo.csv' --no-debug"

printf '\nПолная проверка параметров и вариантов VFS:\n'
bash "$SCRIPT_DIR/check_cli.sh" > /dev/null
printf 'check_cli.sh: код %d\n' "$?"
bash "$SCRIPT_DIR/vfs_variants.sh" > /dev/null
printf 'vfs_variants.sh: код %d\n' "$?"
