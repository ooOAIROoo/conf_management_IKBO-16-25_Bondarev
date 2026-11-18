"""Этап 3: тестовый репозиторий из файла.

Формат файла — по строке на пакет::

    A -> B, C
    B -> D
    D ->

Пакеты называются заглавными
латинскими буквами, строки с ``#``
считаются комментариями, пустые строки
пропускаются. Такой репозиторий
позволяет проверять обход графа,
фильтр и циклы без обращения в сеть.
"""

from __future__ import annotations

ARROW = "->"
COMMENT_MARK = "#"
SEPARATOR = ","
ARROW_PARTS = 2
COMMENT_PARTS = 0


class TestRepoError(ValueError):
    """Файл тестового репо некорректен."""


def is_test_name(name: str) -> bool:
    """Имя из заглавных латинских букв."""
    return (
        bool(name)
        and name.isascii()
        and name.isalpha()
        and name.isupper()
    )


def check_name(name: str, where: str) -> None:
    """Проверяет имя пакета."""
    if is_test_name(name):
        return
    raise TestRepoError(
        f"{where}: имя {name!r} должно состоять "
        "из заглавных латинских букв"
    )


def split_dependencies(text: str) -> list[str]:
    """Разбирает правую часть строки."""
    parts = text.split(SEPARATOR)
    result = []
    for part in parts:
        name = part.strip()
        if name:
            result.append(name)
    return result


def parse_line(line: str, where: str) -> tuple[str, list[str]]:
    """Разбирает строку 'A -> B, C'."""
    parts = line.split(ARROW)
    if len(parts) != ARROW_PARTS:
        raise TestRepoError(
            f"{where}: ожидался формат "
            "'A -> B, C'"
        )
    name = parts[0].strip()
    check_name(name, where)
    dependencies = split_dependencies(parts[ARROW_PARTS - 1])
    for item in dependencies:
        check_name(item, where)
    return name, dependencies


def read_lines(path: str) -> list[str]:
    """Читает файл в список строк."""
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.readlines()
    except OSError as error:
        raise TestRepoError(
            f"не удалось прочитать "
            f"{path}: {error}"
        )
    except UnicodeDecodeError as error:
        raise TestRepoError(
            f"{path}: файл не в кодировке UTF-8 ({error})"
        )


def skip_line(line: str) -> bool:
    """Истина для пропускаемой строки."""
    text = line.strip()
    return not text or text.startswith(COMMENT_MARK)


def read_repository(path: str) -> dict[str, list[str]]:
    """Словарь зависимостей из файла."""
    repository: dict[str, list[str]] = {}
    for number, line in enumerate(read_lines(path), 1):
        if skip_line(line):
            continue
        where = f"{path}, строка {number}"
        name, dependencies = parse_line(line.strip(), where)
        if name in repository:
            raise TestRepoError(
                f"{where}: пакет {name!r} описан повторно"
            )
        repository[name] = dependencies
    return repository


def make_test_getter(path: str):
    """Функция зависимостей и словарь.

    Пакет, которого нет в файле, считается
    пакетом без зависимостей.
    """
    repository = read_repository(path)

    def get_children(name: str) -> list[str]:
        """Зависимости пакета из файла."""
        return list(repository.get(name, []))

    get_children.all_names = sorted(repository)
    return get_children, repository
