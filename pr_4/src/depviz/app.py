"""Точка входа приложения (аналог src/main.cpp из pr_3).

На этапе 1 main делает только три вещи:
1. разбирает и проверяет параметры командной строки;
2. печатает все параметры в формате «ключ — значение»;
3. сообщает, что сбор графа — задача следующих этапов.

Коды возврата (как в pr_3):
* 0 — успех, --help или --version;
* 2 — ошибка разбора или проверки параметров командной строки.
"""

from __future__ import annotations

import sys

from .config import (
    EXIT_CODE_ERROR,
    EXIT_CODE_SUCCESS,
    parse_command_line,
    print_config,
    usage_text,
)
from .version import APP_VERSION, STAGE_DESCRIPTION


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    parsed = parse_command_line(args)
    if not parsed.ok():
        print(f"depviz: {parsed.error}", file=sys.stderr)
        print(file=sys.stderr)
        print(usage_text(), file=sys.stderr, end="")
        return EXIT_CODE_ERROR

    config = parsed.config

    if config.help:
        print(usage_text(), end="")
        return EXIT_CODE_SUCCESS
    if config.version:
        print(f"depviz {APP_VERSION} ({STAGE_DESCRIPTION})")
        return EXIT_CODE_SUCCESS

    # П. 3 задания этапа 1: вывести все параметры при запуске.
    print_config(config)

    print(
        "[stage1] конфигурация проверена. "
        "Сбор графа зависимостей (этапы 2–5) ещё не реализован."
    )
    print(
        "[stage1] в следующих этапах здесь будут: загрузка POM из "
        "репозитория, BFS-обход с учётом транзитивности, вывод "
        "ASCII-дерева и PNG через Graphviz."
    )
    return EXIT_CODE_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
