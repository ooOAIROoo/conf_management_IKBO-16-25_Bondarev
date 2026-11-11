#!/usr/bin/env bash
# Запуск всех проверок этапа 1 pr_4 (аналог pr_3/scripts/run_all.sh в корне репозитория)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PR4="${REPO_ROOT}/pr_4"

echo "==> Запуск юнит-тестов pr_4..."
PYTHONPATH="${PR4}/src" python3 -m unittest discover -s "${PR4}/tests" -v

echo "==> Запуск проверки CLI pr_4..."
bash "${PR4}/scripts/run_all.sh"

echo "==> Все проверки пройдены."
