#!/usr/bin/env bash
# ============================================================================
# Полный прогон этапа 1: юнит-тесты и проверка параметров командной строки.
# Возвращает 0, если все проверки прошли успешно.
# ============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="${PYTHON:-python3}"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

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

run "юнит-тесты конфигурации" "$PYTHON" -m unittest discover -s "$ROOT/tests"
run "параметры командной строки" bash "$SCRIPT_DIR/os/linux/check_cli.sh"

printf '\nИтого: успешно %d, провалено %d\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
