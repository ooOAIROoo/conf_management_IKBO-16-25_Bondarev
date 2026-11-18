#!/usr/bin/env bash
# Демонстрация этапов 2-5 на тестовом репозитории.
# Сеть не требуется: граф берётся из test_repo/sample.txt.
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PYTHON="${PYTHON:-python3}"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

SAMPLE="$ROOT/test_repo/sample.txt"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

line() {
    printf '\n=== %s ===\n' "$1"
}

line "Этап 2-3: обход графа, ASCII-дерево"
"$PYTHON" -m depviz --package A --repo "$SAMPLE" \
    --test-repo --ascii-tree --output "$OUT/tree.png"

line "Этап 3: предельная глубина (--max-depth 1)"
"$PYTHON" -m depviz --package A --repo "$SAMPLE" \
    --test-repo --ascii-tree --max-depth 1 \
    --output "$OUT/depth.png"

line "Этап 3: фильтр по подстроке (--filter D)"
"$PYTHON" -m depviz --package A --repo "$SAMPLE" \
    --test-repo --ascii-tree --filter D \
    --output "$OUT/filter.png"

line "Этап 3: цикл помечается '(цикл)'"
"$PYTHON" -m depviz --package X --repo "$SAMPLE" \
    --test-repo --ascii-tree --output "$OUT/cycle.png"

line "Этап 4: обратные зависимости (--reverse)"
"$PYTHON" -m depviz --package F --repo "$SAMPLE" \
    --test-repo --reverse --ascii-tree \
    --output "$OUT/reverse.png"

line "Этап 5: исходник Graphviz (.dot)"
"$PYTHON" -m depviz --package A --repo "$SAMPLE" \
    --test-repo --output "$OUT/graph.dot" > /dev/null
head -n 8 "$OUT/graph.dot"

line "Этап 5: PNG"
"$PYTHON" -m depviz --package A --repo "$SAMPLE" \
    --test-repo --output "$OUT/graph.png" | tail -n 2
ls -l "$OUT"/*.png "$OUT"/*.dot 2>/dev/null

line "Ошибки этапов 3-4"
"$PYTHON" -m depviz --package A --repo "$SAMPLE" \
    --test-repo --max-depth abc > /dev/null 2>&1
printf '  max-depth abc -> код %d\n' "$?"
"$PYTHON" -m depviz --package A --repo "$SAMPLE" \
    --test-repo --max-depth 1000 > /dev/null 2>&1
printf '  max-depth 1000 -> код %d\n' "$?"

line "Готово"
