#!/bin/sh
# Запуск pr_4 (этап 1): "./run.sh test" — юнит-тесты, иначе — CLI depviz.
# Скрипт работает из любого каталога: сначала переход в корень репозитория.
set -e
cd "$(dirname "$0")"

if [ "$1" = "test" ]; then
    python3 -m unittest discover -s pr_4/tests -t .
else
    PYTHONPATH=pr_4/src python3 -m depviz "$@"
fi
