"""Параметры командной строки (этап 1).

Модуль отвечает за разбор argv,
проверку значений и печать всех
настроенных параметров в формате
«ключ — значение».

На этапе 1 это весь функционал
приложения: граф зависимостей ещё не
строится (этапы 2-5), но конфигурация
уже полностью работает, включая
обработку ошибок для каждого
параметра.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from .version import APP_VERSION

EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 2

FIRST_ARG_INDEX = 0
NEXT_ARG_OFFSET = 1
ARGS_PER_VALUE_OPTION = 2
ARGS_PER_FLAG_OPTION = 1

MAX_FILTER_LENGTH = 200

DEFAULT_REPO = "https://repo.maven.apache.org/maven2"
DEFAULT_PACKAGE_VERSION = "latest"
DEFAULT_OUTPUT_FILE = "graph.png"

NEWLINE = "\n"
CARRIAGE = "\r"
NUL_CHAR = "\x00"
DASH = "-"
EQ = "="
PNG_EXT = ".png"
BAD_EDGE = (".", "-", ":")
BAD_PAIR = ".."
CURRENT_PARENTS = ("", ".")
FILTER_ATTR = "filter_substring"
PREFIX = "[config] "
ABS_REPO_LABEL = PREFIX + "  repo (абс. путь): "

MSG_PACKAGE_EMPTY = (
    "имя пакета не должно "
    "быть пустым"
)
MSG_PACKAGE_SPACES = (
    "недопустимое имя пакета: "
    "пробелы по краям запрещены"
)
MSG_PACKAGE_CHARS = (
    "недопустимое имя пакета: "
    "допустимы буквы, цифры, "
    "'.', '-', '_' и один ':' "
    "в формате groupId:artifactId"
)
MSG_PACKAGE_EDGE = (
    "недопустимое имя пакета: "
    "не может начинаться или "
    "оканчиваться на '.', '-' "
    "или ':'"
)
MSG_PACKAGE_PAIR = (
    "недопустимое имя пакета: "
    "подстрока '..' запрещена"
)

MSG_REPO_EMPTY = (
    "адрес репозитория "
    "не должен быть пустым"
)
MSG_REPO_SPACES = (
    "недопустимый адрес "
    "репозитория: пробелы запрещены"
)
MSG_REPO_TEST_URL = (
    "в тестовом режиме (--test-repo) "
    "параметр --repo должен быть "
    "путём к файлу, а не URL"
)
MSG_REPO_NOT_FOUND = (
    "файл тестового "
    "репозитория не найден"
)
MSG_REPO_IS_DIR = (
    "путь к тестовому репозиторию "
    "является каталогом, а не файлом"
)
MSG_REPO_UNREADABLE = (
    "файл тестового репозитория "
    "недоступен для чтения"
)
MSG_REPO_NOT_URL = (
    "в режиме реального "
    "репозитория параметр --repo "
    "должен быть URL (http:// или "
    "https://), получено"
)

MSG_VERSION_EMPTY = (
    "версия пакета "
    "не должна быть пустой"
)
MSG_VERSION_SPACES = (
    "недопустимая версия пакета: "
    "пробелы по краям запрещены"
)
MSG_VERSION_CHARS = (
    "недопустимая версия пакета: "
    "допустимы буквы, цифры, "
    "'.', '-', '_' и '+', например "
    "1.0.0 или 2.0-SNAPSHOT"
)

MSG_OUTPUT_EMPTY = (
    "имя выходного файла "
    "не должно быть пустым"
)
MSG_OUTPUT_SPACES = (
    "недопустимое имя выходного "
    "файла: пробелы по краям "
    "запрещены"
)
MSG_OUTPUT_NUL = (
    "недопустимое имя выходного "
    "файла: символ NUL запрещён"
)
MSG_OUTPUT_EXT = (
    "имя выходного файла должно "
    "оканчиваться на .png "
    "(изображение графа "
    "сохраняется в PNG)"
)
MSG_OUTPUT_IS_DIR = (
    "имя выходного файла является "
    "существующим каталогом"
)
MSG_OUTPUT_PARENT = (
    "родительский каталог "
    "выходного файла не существует"
)

MSG_FILTER_TOO_LONG = (
    "подстрока фильтрации "
    "слишком длинная "
    "(максимум {} символов)"
)
MSG_FILTER_NEWLINE = (
    "подстрока фильтрации не "
    "должна содержать переводы строк"
)
MSG_FILTER_EMPTY_ARG = (
    "подстрока фильтрации не "
    "должна быть пустой "
    "(или не указывайте --filter)"
)

MSG_NO_PACKAGE = (
    "не задано имя анализируемого "
    "пакета (параметр --package "
    "обязателен)"
)
MSG_NEEDS_VALUE = (
    "параметр {} требует значения"
)
MSG_NO_VALUE = (
    "параметр {} не принимает значения"
)
MSG_UNKNOWN = "неизвестный параметр: {}"
MSG_POSITIONAL = (
    "неожиданный позиционный "
    "аргумент: {!r} (все параметры "
    "задаются опциями, см. --help)"
)

_PACKAGE_RE = re.compile(r"^[A-Za-z0-9_.\-]+(?::[A-Za-z0-9_.\-]+)?$")
_VERSION_RE = re.compile(r"^[A-Za-z0-9_.\-+]+$")


@dataclass
class Config:
    """Все настраиваемые параметры.

    Поля:

    * package — имя пакета (обязательно);
    * repo — URL репозитория или путь;
    * test_repo_mode — тестовый репозиторий;
    * package_version — версия пакета;
    * output_file — имя выходного PNG-файла;
    * ascii_tree — вывод ASCII-деревом;
    * filter_substring — подстрока фильтра;
    * help, version — служебные флаги.
    """

    package: str | None = None
    repo: str = DEFAULT_REPO
    test_repo_mode: bool = False
    package_version: str = DEFAULT_PACKAGE_VERSION
    output_file: str = DEFAULT_OUTPUT_FILE
    ascii_tree: bool = False
    filter_substring: str = ""
    help: bool = False
    version: bool = False


@dataclass
class ConfigParseResult:
    """Результат разбора командной строки."""

    config: Config = field(default_factory=Config)
    error: str = ""

    def ok(self) -> bool:
        """Истина, если ошибки разбора нет."""
        return not self.error


def _with_value(msg: str, value: str) -> str:
    """Добавляет значение к тексту ошибки."""
    return f"{msg}: {value!r}"


def _check_package(value: str) -> str:
    """Проверяет имя пакета в формате Maven."""
    if not value.strip():
        return MSG_PACKAGE_EMPTY
    if value.strip() != value:
        return _with_value(MSG_PACKAGE_SPACES, value)
    if not _PACKAGE_RE.match(value):
        return _with_value(MSG_PACKAGE_CHARS, value)
    if value[0] in BAD_EDGE or value[-1] in BAD_EDGE:
        return _with_value(MSG_PACKAGE_EDGE, value)
    if BAD_PAIR in value:
        return _with_value(MSG_PACKAGE_PAIR, value)
    return ""


def _is_url(value: str) -> bool:
    """Проверяет, что строка — http/https URL."""
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _check_test_repo(value: str) -> str:
    """Проверяет путь к файлу тестового
    репозитория."""
    if _is_url(value):
        return _with_value(MSG_REPO_TEST_URL, value)
    path = Path(value)
    if not path.exists():
        return _with_value(MSG_REPO_NOT_FOUND, value)
    if path.is_dir():
        return _with_value(MSG_REPO_IS_DIR, value)
    if not os.access(path, os.R_OK):
        return _with_value(MSG_REPO_UNREADABLE, value)
    return ""


def _check_real_repo(value: str) -> str:
    """Проверяет URL реального репозитория."""
    if _is_url(value):
        return ""
    return _with_value(MSG_REPO_NOT_URL, value)


def _check_repo(value: str, test_repo_mode: bool) -> str:
    """Проверяет адрес репозитория,
    учитывая режим."""
    if not value.strip():
        return MSG_REPO_EMPTY
    if any(ch.isspace() for ch in value):
        return _with_value(MSG_REPO_SPACES, value)
    if test_repo_mode:
        return _check_test_repo(value)
    return _check_real_repo(value)


def _check_version(value: str) -> str:
    """Проверяет версию пакета (1.0.0,
    2.0-SNAPSHOT и т. п.)."""
    if not value.strip():
        return MSG_VERSION_EMPTY
    if value.strip() != value:
        return _with_value(MSG_VERSION_SPACES, value)
    if not _VERSION_RE.match(value):
        return _with_value(MSG_VERSION_CHARS, value)
    return ""


def _check_output_file(value: str) -> str:
    """Проверяет имя выходного PNG-файла."""
    if not value.strip():
        return MSG_OUTPUT_EMPTY
    if value.strip() != value:
        return _with_value(MSG_OUTPUT_SPACES, value)
    if NUL_CHAR in value:
        return _with_value(MSG_OUTPUT_NUL, value)
    if not value.lower().endswith(PNG_EXT):
        return _with_value(MSG_OUTPUT_EXT, value)
    path = Path(value)
    if path.exists() and path.is_dir():
        return _with_value(MSG_OUTPUT_IS_DIR, value)
    parent = path.parent
    if str(parent) not in CURRENT_PARENTS and not parent.exists():
        return _with_value(MSG_OUTPUT_PARENT, str(parent))
    return ""


def _check_filter(value: str) -> str:
    """Проверяет подстроку фильтра."""
    if len(value) > MAX_FILTER_LENGTH:
        return MSG_FILTER_TOO_LONG.format(MAX_FILTER_LENGTH)
    if NEWLINE in value or CARRIAGE in value:
        return MSG_FILTER_NEWLINE
    return ""


def validate_config(config: Config) -> str:
    """Проверяет разобранную конфигурацию."""
    if config.package is None:
        return MSG_NO_PACKAGE
    checks = (
        _check_package(config.package),
        _check_repo(config.repo, config.test_repo_mode),
        _check_version(config.package_version),
        _check_output_file(config.output_file),
        _check_filter(config.filter_substring),
    )
    for error in checks:
        if error:
            return error
    return ""


_VALUE_OPTIONS = {
    "--package": "package",
    "-p": "package",
    "--repo": "repo",
    "-r": "repo",
    "--package-version": "package_version",
    "-v": "package_version",
    "--output": "output_file",
    "-o": "output_file",
    "--filter": "filter_substring",
    "-f": "filter_substring",
}

_FLAG_OPTIONS = {
    "--test-repo": ("test_repo_mode", True),
    "-t": ("test_repo_mode", True),
    "--real-repo": ("test_repo_mode", False),
    "--ascii-tree": ("ascii_tree", True),
    "--no-ascii-tree": ("ascii_tree", False),
    "--help": ("help", True),
    "-h": ("help", True),
    "--version": ("version", True),
    "-V": ("version", True),
}


def _apply_equals(arg: str, config: Config) -> str:
    """Разбирает форму --имя=значение."""
    name, _, value = arg.partition(EQ)
    if name in _VALUE_OPTIONS:
        if value == "":
            return MSG_NEEDS_VALUE.format(name)
        setattr(config, _VALUE_OPTIONS[name], value)
        return ""
    if name in _FLAG_OPTIONS:
        return MSG_NO_VALUE.format(name)
    return MSG_UNKNOWN.format(name)


def _apply_value_option(args: list[str], index: int,
                        config: Config) -> tuple[str, int]:
    """Применяет опцию со значением."""
    name = args[index]
    attr = _VALUE_OPTIONS[name]
    next_index = index + NEXT_ARG_OFFSET
    if next_index >= len(args):
        return MSG_NEEDS_VALUE.format(name), ARGS_PER_VALUE_OPTION
    value = args[next_index]
    if attr == FILTER_ATTR and value == "":
        return MSG_FILTER_EMPTY_ARG, ARGS_PER_VALUE_OPTION
    setattr(config, attr, value)
    return "", ARGS_PER_VALUE_OPTION


def _apply_flag_option(name: str, config: Config) -> None:
    """Применяет опцию-флаг (без значения)."""
    attr, flag_value = _FLAG_OPTIONS[name]
    setattr(config, attr, flag_value)


def _parse_step(args: list[str], index: int,
                config: Config) -> tuple[str, int]:
    """Разбирает один аргумент.

    Возвращает пару (ошибка, шаг).
    """
    arg = args[index]
    if arg.startswith(DASH) and EQ in arg:
        return _apply_equals(arg, config), ARGS_PER_FLAG_OPTION
    if arg in _VALUE_OPTIONS:
        return _apply_value_option(args, index, config)
    if arg in _FLAG_OPTIONS:
        _apply_flag_option(arg, config)
        return "", ARGS_PER_FLAG_OPTION
    if arg.startswith(DASH) and arg != DASH:
        return MSG_UNKNOWN.format(arg), ARGS_PER_FLAG_OPTION
    return MSG_POSITIONAL.format(arg), ARGS_PER_FLAG_OPTION


def parse_command_line(args: list[str]) -> ConfigParseResult:
    """Разбирает argv (без имени программы) в Config.

    Поддерживаются обе формы записи:
    ``--package guava`` и ``--package=guava``.
    При повторе побеждает последнее
    значение.
    """
    result = ConfigParseResult()
    config = result.config
    index = FIRST_ARG_INDEX
    while index < len(args):
        error, step = _parse_step(args, index, config)
        if error:
            result.error = error
            return result
        index += step
    if config.help or config.version:
        return result
    result.error = validate_config(config)
    return result


_HELP_LINES = (
    "Использование: depviz [параметры]",
    "",
    "Настраиваемые параметры "
    "(все — опции командной строки):",
    "  -p, --package <имя>        "
    "имя анализируемого пакета "
    "(обязательно)",
    "  -r, --repo <URL|путь>      "
    "URL репозитория или путь "
    "к файлу",
    "                             "
    "тестового репозитория",
    "                             "
    "(по умолчанию: "
    "https://repo.maven.apache.org/maven2)",
    "  -t, --test-repo            "
    "режим работы с тестовым "
    "репозиторием:",
    "                             "
    "--repo трактуется "
    "как путь к файлу",
    "      --real-repo            "
    "режим реального "
    "репозитория (по умолчанию):",
    "                             "
    "--repo трактуется как URL",
    "  -v, --package-version <вер> "
    "версия пакета "
    "(по умолчанию: latest)",
    "  -o, --output <файл>        "
    "имя сгенерированного "
    "файла с изображением",
    "                             "
    "графа, только .png "
    "(по умолчанию: graph.png)",
    "      --ascii-tree           "
    "вывести зависимости "
    "в виде ASCII-дерева",
    "      --no-ascii-tree        "
    "не выводить ASCII-дерево "
    "(по умолчанию)",
    "  -f, --filter <подстрока>   "
    "подстрока для фильтрации "
    "пакетов",
    "  -h, --help                 "
    "эта справка",
    "  -V, --version              "
    "версия приложения",
    "",
    "Допустимы обе формы записи: "
    "--package guava и "
    "--package=guava.",
    "При запуске приложение "
    "печатает все параметры "
    "в формате ключ-значение.",
    "Этап 1: сбор графа "
    "зависимостей ещё не "
    "реализован (этапы 2–5).",
)


def usage_text() -> str:
    """Возвращает текст справки."""
    return NEWLINE.join(_HELP_LINES) + NEWLINE


def _quoted(value: str) -> str:
    """Оборачивает значение в кавычки."""
    return f'"{value}"'


def format_config(config: Config) -> str:
    """Все параметры в формате
    «ключ — значение»."""
    lines = [PREFIX + "параметры запуска:"]
    lines.append(f"{PREFIX}  package: {_quoted(config.package or '')}")
    lines.append(f"{PREFIX}  repo: {_quoted(config.repo)}")
    if config.test_repo_mode:
        lines.append(
            f"{PREFIX}  test_repo_mode: true "
            "(тестовый репозиторий)"
        )
        try:
            absolute = Path(config.repo).expanduser().resolve()
            lines.append(ABS_REPO_LABEL + str(absolute))
        except OSError:
            pass
    else:
        lines.append(
            f"{PREFIX}  test_repo_mode: false "
            "(реальный репозиторий)"
        )
    lines.append(
        f"{PREFIX}  package_version: "
        f"{_quoted(config.package_version)}"
    )
    lines.append(
        f"{PREFIX}  output_file: "
        f"{_quoted(config.output_file)}"
    )
    tree_flag = "true" if config.ascii_tree else "false"
    lines.append(f"{PREFIX}  ascii_tree: {tree_flag}")
    if config.filter_substring:
        lines.append(
            f"{PREFIX}  filter: "
            f"{_quoted(config.filter_substring)}"
        )
    else:
        lines.append(f'{PREFIX}  filter: "" (не задана)')
    lines.append(f"{PREFIX}  app_version: {APP_VERSION}")
    return NEWLINE.join(lines) + NEWLINE


def print_config(config: Config, out=None) -> None:
    """Печатает параметры запуска.

    По умолчанию — в stdout.
    """
    if out is None:
        out = sys.stdout
    out.write(format_config(config))
    out.flush()
