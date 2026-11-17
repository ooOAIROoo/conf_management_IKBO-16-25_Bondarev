"""Точка входа приложения (этап 1).

На этапе 1 main делает только три
вещи:

1. разбирает и проверяет параметры
   командной строки;
2. печатает все параметры в формате
   «ключ — значение»;
3. сообщает, что сбор графа — задача
   следующих этапов.

Коды возврата:

* 0 — успех, --help или --version;
* 2 — ошибка разбора или проверки
  параметров командной строки.
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

ERROR_PREFIX = "depviz: "

STAGE_LINES = (
    "[stage1] конфигурация "
    "проверена. Сбор графа "
    "зависимостей (этапы 2–5) "
    "ещё не реализован.",
    "[stage1] в следующих этапах "
    "здесь будут: загрузка POM "
    "из репозитория, BFS-обход "
    "с учётом транзитивности, "
    "вывод ASCII-дерева и PNG "
    "через Graphviz.",
)


def _print_error(error: str) -> None:
    """Печатает ошибку и справку в stderr."""
    print(ERROR_PREFIX + error, file=sys.stderr)
    print(file=sys.stderr)
    print(usage_text(), file=sys.stderr, end="")


def main(argv: list[str] | None = None) -> int:
    """Точка входа: разбор argv и вывод."""
    args = list(sys.argv[1:] if argv is None else argv)

    parsed = parse_command_line(args)
    if not parsed.ok():
        _print_error(parsed.error)
        return EXIT_CODE_ERROR

    config = parsed.config

    if config.help:
        print(usage_text(), end="")
        return EXIT_CODE_SUCCESS
    if config.version:
        print(
            f"depviz {APP_VERSION} "
            f"({STAGE_DESCRIPTION})"
        )
        return EXIT_CODE_SUCCESS

    print_config(config)

    for line in STAGE_LINES:
        print(line)
    return EXIT_CODE_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
