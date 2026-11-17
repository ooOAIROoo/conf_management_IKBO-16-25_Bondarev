#!/bin/sh
# Запуск pr_4 (этап 1).
#   ./run.sh          -- CLI depviz (аргументы пробрасываются)
#   ./run.sh test     -- юнит-тесты
#   ./run.sh style    -- проверка стиля по критериям отчёта
#   ./run.sh check    -- полный прогон всех проверок
# Скрипт работает из любого каталога.
set -e
cd "$(dirname "$0")"

case "$1" in
    test)
        python3 -m unittest discover -s pr_4/tests -t .
        ;;
    style)
        python3 pr_4/scripts/check_style.py .
        ;;
    check)
        python3 pr_4/scripts/check_style.py .
        PYTHONPATH=pr_4/src python3 -m unittest discover \
            -s pr_4/tests -t .
        bash pr_4/scripts/run_all.sh
        ;;
    *)
        PYTHONPATH=pr_4/src python3 -m depviz "$@"
        ;;
esac
