#!/usr/bin/env bash
# ============================================================================
# Этап 1. Демонстрация конфигурации depviz в реальной ОС (Linux/macOS).
#
# Показывает вывод всех параметров в формате «ключ — значение»,
# работу с тестовым репозиторием и обработку ошибок для каждого параметра.
# ============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PYTHON="${PYTHON:-python3}"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
SAMPLE="$ROOT/test_repo/sample.txt"

show() {
    printf '\n$ %s\n' "$1"
    shift
    "$@"
    printf '[код возврата: %d]\n' "$?"
}

printf '################################################################\n'
printf '# Этап 1. Минимальный прототип с конфигурацией (depviz)\n'
printf '################################################################\n'

show "depviz --help" "$PYTHON" -m depviz --help
show "depviz --version" "$PYTHON" -m depviz --version

# Минимальный запуск: остальные параметры — значения по умолчанию.
show "depviz --package guava" "$PYTHON" -m depviz --package guava

# Все параметры сразу.
show "depviz --package com.google.guava:guava --package-version 32.1.2 --output graph.png --ascii-tree --filter guava" \
    "$PYTHON" -m depviz \
        --package com.google.guava:guava \
        --package-version 32.1.2 \
        --output graph.png \
        --ascii-tree \
        --filter guava

# Тестовый репозиторий: --repo — путь к файлу.
show "depviz --package A --repo test_repo/sample.txt --test-repo" \
    "$PYTHON" -m depviz --package A --repo "$SAMPLE" --test-repo

# Ошибки по каждому параметру.
show "depviz (нет --package)" "$PYTHON" -m depviz
show "depviz --package 'bad name!'" "$PYTHON" -m depviz --package "bad name!"
show "depviz --package guava --repo not-a-url" "$PYTHON" -m depviz --package guava --repo not-a-url
show "depviz --package guava --repo https://example.com --test-repo" \
    "$PYTHON" -m depviz --package guava --repo https://example.com --test-repo
show "depviz --package guava --repo нет-такого.txt --test-repo" \
    "$PYTHON" -m depviz --package guava --repo "$ROOT/test_repo/нет-такого.txt" --test-repo
show "depviz --package guava --package-version '1.0 /beta'" \
    "$PYTHON" -m depviz --package guava --package-version "1.0 /beta"
show "depviz --package guava --output graph.jpg" \
    "$PYTHON" -m depviz --package guava --output graph.jpg
show "depviz --package guava --filter ''" \
    "$PYTHON" -m depviz --package guava --filter ""
show "depviz --package guava --bogus" "$PYTHON" -m depviz --package guava --bogus
show "depviz --package (нет значения)" "$PYTHON" -m depviz --package

printf '\nПолная проверка параметров:\n'
bash "$SCRIPT_DIR/check_cli.sh" > /dev/null
printf 'check_cli.sh: все проверки пройдены (код %d)\n' "$?"
