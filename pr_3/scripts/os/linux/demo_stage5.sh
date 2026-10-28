#!/usr/bin/env bash
# ============================================================================
# Этап 5. Демонстрация touch и rmdir в реальной ОС (Linux/macOS).
#
# Дополнительно доказывается, что изменения VFS выполняются только в памяти:
# контрольная сумма CSV-файла до и после работы не меняется, а созданные
# в VFS файлы не появляются на физическом диске.
# ============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
EMU="${EMU:-$ROOT/build/bin/emu}"
VFS="$ROOT/vfs/demo.csv"

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
printf '# Этап 5. Дополнительные команды: touch и rmdir\n'
printf '################################################################\n'

printf '\n--- Все параметры командной строки ---\n'
show "emu --help" "$EMU" --help
show "emu --version" "$EMU" --version
show "emu --vfs vfs/minimal.csv --no-debug" \
    bash -c "printf 'touch /new.txt\\nls -l /\\nexit 0\\n' | '$EMU' --vfs '$ROOT/vfs/minimal.csv' --no-debug"
show "emu --vfs (нет значения)" "$EMU" --vfs

printf '\n--- Варианты VFS ---\n'
show "emu --vfs vfs/multi.csv" \
    bash -c "printf 'tree /\\nrmdir /tmp\\nls -a /\\nexit 0\\n' | '$EMU' --vfs '$ROOT/vfs/multi.csv' --no-debug"
show "emu --vfs vfs/demo.csv --script scripts/stage5.emu" \
    "$EMU" --vfs "$VFS" --script "$ROOT/scripts/stage5.emu"

printf '\n--- Доказательство: изменения только в памяти ---\n'
BEFORE="$(cksum < "$VFS")"
printf 'контрольная сумма CSV до запуска:    %s\n' "$BEFORE"
"$EMU" --vfs "$VFS" --no-debug <<'EOF' > /dev/null
touch /home/user/new.txt
rmdir /tmp/empty
touch /tmp/только-в-памяти.txt
exit 0
EOF
AFTER="$(cksum < "$VFS")"
printf 'контрольная сумма CSV после запуска: %s\n' "$AFTER"
if [ "$BEFORE" = "$AFTER" ]; then
    printf '  [PASS] CSV-файл VFS не изменён\n'
else
    printf '  [FAIL] CSV-файл VFS изменился!\n'
fi

FOUND=0
while IFS= read -r created; do
    [ -e "$created" ] && FOUND=1
done <<EOF
$ROOT/home/user/new.txt
$ROOT/new.txt
$ROOT/tmp/только-в-памяти.txt
$ROOT/только-в-памяти.txt
$ROOT/pr_3/home/user/new.txt
EOF
if [ "$FOUND" -eq 0 ]; then
    printf '  [PASS] созданные в VFS файлы отсутствуют на физическом диске\n'
else
    printf '  [FAIL] файл из VFS появился на физическом диске!\n'
fi

printf '\nПолная проверка параметров и вариантов VFS:\n'
bash "$SCRIPT_DIR/check_cli.sh" > /dev/null
printf 'check_cli.sh: код %d\n' "$?"
bash "$SCRIPT_DIR/vfs_variants.sh" > /dev/null
printf 'vfs_variants.sh: код %d\n' "$?"
