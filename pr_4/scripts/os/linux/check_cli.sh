#!/usr/bin/env bash
# ============================================================================
# Этап 1. Проверка всех параметров командной строки depviz (Linux/macOS).
#
# Скрипт реальной ОС: запускает приложение в разных режимах и сверяет
# коды возврата. Зависимостей нет, нужен только Python 3.9+.
#
# Переменные окружения:
#   PYTHON — интерпретатор Python (по умолчанию python3)
#   DEPviz — не используется; приложение запускается как модуль:
#            PYTHONPATH=src python3 -m depviz ...
# ============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PYTHON="${PYTHON:-python3}"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

SAMPLE="$ROOT/test_repo/sample.txt"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

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

run_depviz() {
    "$PYTHON" -m depviz "$@"
}

section "Справка и версия"
expect_code "--help" 0 run_depviz --help
expect_code "-h" 0 run_depviz -h
expect_code "--version" 0 run_depviz --version
expect_code "-V" 0 run_depviz -V

section "Минимальный запуск (только обязательный --package)"
expect_code "--package guava" 0 run_depviz --package guava
expect_code "-p guava" 0 run_depviz -p guava
expect_code "--package=guava" 0 run_depviz --package=guava
expect_code "groupId:artifactId" 0 run_depviz --package com.google.guava:guava

section "Все параметры вместе (реальный репозиторий)"
expect_code "все параметры" 0 run_depviz \
    --package com.google.guava:guava \
    --repo https://repo.maven.apache.org/maven2 \
    --package-version 32.1.2 \
    --output graph.png \
    --ascii-tree \
    --filter guava

section "Тестовый репозиторий"
expect_code "--test-repo с файлом" 0 run_depviz \
    --package A --repo "$SAMPLE" --test-repo
expect_code "--test-repo + --real-repo (последний побеждает)" 2 run_depviz \
    --package A --repo "$SAMPLE" --test-repo --real-repo

section "Обработка ошибок: общие"
expect_code "без параметров (нет --package)" 2 run_depviz
expect_code "неизвестный параметр" 2 run_depviz --package guava --bogus
expect_code "параметр без значения" 2 run_depviz --package
expect_code "пустое значение через =" 2 run_depviz --package=
expect_code "позиционный аргумент" 2 run_depviz guava
expect_code "флаг со значением" 2 run_depviz --package guava --ascii-tree=true

section "Обработка ошибок: --package"
expect_code "недопустимое имя пакета" 2 run_depviz --package "bad name!"

section "Обработка ошибок: --repo"
expect_code "не URL в реальном режиме" 2 run_depviz --package guava --repo not-a-url
expect_code "URL в тестовом режиме" 2 run_depviz \
    --package guava --repo https://example.com/repo --test-repo
expect_code "файл тестового репозитория не найден" 2 run_depviz \
    --package guava --repo "$TMP_DIR/нет-такого.txt" --test-repo
expect_code "каталог вместо файла тестового репозитория" 2 run_depviz \
    --package guava --repo "$TMP_DIR" --test-repo

section "Обработка ошибок: --package-version"
expect_code "недопустимая версия" 2 run_depviz \
    --package guava --package-version "1.0 /beta"

section "Обработка ошибок: --output"
expect_code "не .png" 2 run_depviz --package guava --output graph.jpg
expect_code "родительский каталог не существует" 2 run_depviz \
    --package guava --output "$TMP_DIR/нет-каталога/graph.png"

section "Обработка ошибок: --filter"
expect_code "пустой фильтр" 2 run_depviz --package guava --filter ""

printf '\nИтого: успешно %d, провалено %d\n' "$PASSED" "$FAILED"
[ "$FAILED" -eq 0 ]
