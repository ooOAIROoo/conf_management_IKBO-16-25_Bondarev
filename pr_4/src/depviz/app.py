"""Точка входа приложения.

Приложение проходит пять этапов:

1. разбор и проверка параметров;
2. получение зависимостей (Maven POM
   или тестовый репозиторий);
3. обход графа в ширину;
4. обратные зависимости при
   ``--reverse``;
5. вывод: ASCII-дерево, список,
   Graphviz ``.dot`` и PNG.

Коды возврата:

* 0 — успех, --help или --version;
* 2 — ошибка параметров;
* 1 — ошибка получения данных.
"""

from __future__ import annotations

import sys

from . import maven, render, testrepo
from .config import (
    DOT_EXT,
    EXIT_CODE_ERROR,
    EXIT_CODE_SUCCESS,
    parse_command_line,
    print_config,
    usage_text,
)
from .graph import bfs_graph, build_reverse
from .version import APP_VERSION, STAGE_DESCRIPTION

ERROR_PREFIX = "depviz: "
EXIT_CODE_DATA_ERROR = 1
PNG_EXT = ".png"

SUMMARY_VERTICES = "Вершин: {}"
SUMMARY_EDGES = "Рёбер: {}"
MODE_REVERSE = "обратные зависимости"
MODE_DIRECT = "прямые зависимости"
ENGINE_TEXT = "PNG сохранён ({}) в {}"
DOT_TEXT = "исходник Graphviz сохранён в {}"
SUCCESS_TEXT = "Готово."


def _print_error(error: str, show_usage: bool = True) -> None:
    """Печатает ошибку и справку."""
    print(ERROR_PREFIX + error, file=sys.stderr)
    if not show_usage:
        return
    print(file=sys.stderr)
    print(usage_text(), file=sys.stderr, end="")


def _make_getter(config):
    """Функция зависимостей по режиму."""
    if config.test_repo_mode:
        getter, _ = testrepo.make_test_getter(config.repo)
        return getter
    return maven.make_maven_getter(
        config.repo, config.package_version
    )


def _print_help() -> int:
    """Печатает справку."""
    print(usage_text(), end="")
    return EXIT_CODE_SUCCESS


def _print_version() -> int:
    """Печатает версию приложения."""
    print(f"depviz {APP_VERSION} ({STAGE_DESCRIPTION})")
    return EXIT_CODE_SUCCESS


def _print_tree(graph, config) -> None:
    """Печатает ASCII-дерево или список."""
    if config.ascii_tree:
        lines = render.render_tree(graph, config.max_depth)
    else:
        lines = render.render_list(graph)
    for line in lines:
        print(line)


def _save_output(graph, config) -> None:
    """Сохраняет PNG или исходник Graphviz."""
    output = config.output_file
    if output.lower().endswith(DOT_EXT):
        text = render.graph_to_dot(graph)
        with open(output, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(DOT_TEXT.format(output))
        return
    engine = render.write_png(graph, output)
    print(ENGINE_TEXT.format(engine, output))


def _build_graph(config, getter):
    """Строит граф: прямой или обратный."""
    if config.reverse:
        return build_reverse(
            config.package,
            getter,
            config.max_depth,
            config.filter_substring,
        )
    return bfs_graph(
        config.package,
        getter,
        config.max_depth,
        config.filter_substring,
    )


def run(config) -> int:
    """Выполняет этапы 2-5."""
    print_config(config)
    getter = _make_getter(config)
    try:
        graph = _build_graph(config, getter)
    except ValueError as error:
        _print_error(str(error), show_usage=False)
        return EXIT_CODE_DATA_ERROR
    mode = MODE_REVERSE if config.reverse else MODE_DIRECT
    print(f"Режим: {mode}")
    print(SUMMARY_VERTICES.format(graph.vertex_count()))
    print(SUMMARY_EDGES.format(graph.edge_count()))
    _print_tree(graph, config)
    try:
        _save_output(graph, config)
    except OSError as error:
        _print_error(
            f"не удалось записать файл: {error}",
            show_usage=False,
        )
        return EXIT_CODE_DATA_ERROR
    print(SUCCESS_TEXT)
    return EXIT_CODE_SUCCESS


def main(argv: list[str] | None = None) -> int:
    """Точка входа: разбор argv и запуск этапов."""
    args = list(sys.argv[1:] if argv is None else argv)
    parsed = parse_command_line(args)
    if not parsed.ok():
        _print_error(parsed.error)
        return EXIT_CODE_ERROR
    config = parsed.config
    if config.help:
        return _print_help()
    if config.version:
        return _print_version()
    try:
        return run(config)
    except (maven.PomError, testrepo.TestRepoError) as error:
        _print_error(str(error), show_usage=False)
        return EXIT_CODE_DATA_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
