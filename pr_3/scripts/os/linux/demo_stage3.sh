#!/usr/bin/env bash
# ============================================================================
# Этап 3. Демонстрация VFS в реальной ОС (Linux/macOS).
#
# Показывает загрузку трёх вариантов VFS, обход дерева, работу ls/cd,
# обработку ошибок и выполнение стартового скрипта.
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
printf '# Этап 3. Виртуальная файловая система в памяти\n'
printf '################################################################\n'

show "emu --vfs vfs/minimal.csv" \
    bash -c "printf 'ls /\\nls /hello.txt\\nexit 0\\n' | '$EMU' --vfs '$ROOT/vfs/minimal.csv'"

show "emu --vfs vfs/multi.csv" \
    bash -c "printf 'ls /\\nls /etc\\ncd /etc\\nls\\nexit 0\\n' | '$EMU' --vfs '$ROOT/vfs/multi.csv'"

show "emu --vfs vfs/demo.csv (отладочный вывод VFS)" \
    bash -c "printf 'ls /\\ncd /home/user/docs\\nls\\nls /tmp\\nexit 0\\n' | '$EMU' --vfs '$ROOT/vfs/demo.csv'"

show "emu --vfs vfs/demo.csv --script scripts/stage3.emu" \
    "$EMU" --vfs "$ROOT/vfs/demo.csv" --script "$ROOT/scripts/stage3.emu"

show "emu --vfs vfs/bad/duplicate.csv" "$EMU" --vfs "$ROOT/vfs/bad/duplicate.csv" --no-debug
show "emu --vfs vfs/bad/bad-base64.csv" "$EMU" --vfs "$ROOT/vfs/bad/bad-base64.csv" --no-debug

printf '\nПолная проверка вариантов VFS:\n'
bash "$SCRIPT_DIR/vfs_variants.sh" > /dev/null
printf 'vfs_variants.sh: все проверки пройдены (код %d)\n' "$?"
