"""Параметры командной строки (этап 1).

Аналог include/emu/config.hpp +
src/config.cpp из pr_3: один модуль
отвечает за разбор argv, проверку
значений и печать всех настроенных
параметров в формате «ключ — значение».

На этапе 1 это весь функционал
приложения: граф зависимостей ещё не
строится (это этапы 2–5), но
конфигурация уже полностью работает,
включая обработку ошибок для каждого
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

# Коды завершения (аналог pr_3:
# 0 — успех, 2 — ошибка параметров).
EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 2

# Значения по умолчанию. Единственный
# обязательный параметр — имя пакета:
# без него анализировать нечего,
# поэтому его отсутствие — ошибка
# (код 2).
DEFAULT_REPO = "https://repo.maven.apache.org/maven2"
DEFAULT_PACKAGE_VERSION = "latest"
DEFAULT_OUTPUT_FILE = "graph.png"

# Максимальная длина подстроки фильтра
# (в символах).
MAX_FILTER_LENGTH = 200

# Имя пакета в формате Maven:
# artifactId или groupId:artifactId.
# Допустимы буквы, цифры, точка,
# дефис и подчёркивание.
_PACKAGE_RE = re.compile(r"^[A-Za-z0-9_.\-]+(?::[A-Za-z0-9_.\-]+)?$")
# Версия пакета: 1.0.0,
# 2.0-SNAPSHOT, 1.0+build и т. п.
_VERSION_RE = re.compile(r"^[A-Za-z0-9_.\-+]+$")


@dataclass
class Config:
    """Все настраиваемые пользователем
    параметры (п. 2 этапа 1)."""

    # имя анализируемого пакета (обязательно)
    package: str | None = None
    repo: str = DEFAULT_REPO
    # режим работы с тестовым репозиторием
    test_repo_mode: bool = False
    # версия пакета
    package_version: str = DEFAULT_PACKAGE_VERSION
    # файл с изображением графа
    output_file: str = DEFAULT_OUTPUT_FILE
    # вывод зависимостей в формате ASCII-дерева
    ascii_tree: bool = False
    # подстрока для фильтрации пакетов
    filter_substring: str = ""
    help: bool = False
    # версия самого приложения (--version)
    version: bool = False


@dataclass
class ConfigParseResult:
    config: Config = field(default_factory=Config)
    error: str = ""  # пусто, если разбор успешен

    def ok(self) -> bool:
        return not self.error


# ---------------------------------------------------------------------------
# Проверка отдельных параметров
# (п. 4 задания: обработка ошибок для всех)
# ---------------------------------------------------------------------------


def _validate_package(value: str) -> str:
    """Проверяет имя пакета (Maven-координата artifactId или
    groupId:artifactId)."""
    if not value or not value.strip():
        return "имя пакета не должно быть пустым"
    if value.strip() != value:
        return (
            f"недопустимое имя пакета: {value!r} "
            "(пробелы по краям запрещены)"
        )
    if not _PACKAGE_RE.match(value):
        return (
            f"недопустимое имя пакета: {value!r} "
            "(допустимы буквы, цифры, '.', '-', '_' и один ':' "
            "в формате groupId:artifactId)"
        )
    if value.startswith((".", "-", ":")) or value.endswith((".", "-", ":")):
        return (
            f"недопустимое имя пакета: {value!r} "
            "(не может начинаться или оканчиваться на '.', '-' или ':')"
        )
    if ".." in value:
        return (
            f"недопустимое имя пакета: {value!r} "
            "(подстрока '..' запрещена)"
        )
    return ""


def _is_url(value: str) -> bool:
    """Проверяет, что строка — http/https URL с хостом."""
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _validate_repo(value: str, test_repo_mode: bool) -> str:
    """Проверяет адрес репозитория: URL в реальном режиме, путь к файлу
    в тестовом."""
    if not value or not value.strip():
        return "адрес репозитория не должен быть пустым"
    if any(ch.isspace() for ch in value):
        return (
            f"недопустимый адрес репозитория: {value!r} "
            "(пробелы запрещены)"
        )

    if test_repo_mode:
        # В тестовом режиме --repo — это путь к файлу, а не URL.
        if _is_url(value):
            return (
                f"в тестовом режиме (--test-repo) параметр --repo должен "
                f"быть путём к файлу тестового репозитория, а не URL: "
                f"{value!r}"
            )
        path = Path(value)
        if not path.exists():
            return f"файл тестового репозитория не найден: {value!r}"
        if path.is_dir():
            return (
                f"путь к тестовому репозиторию является каталогом, "
                f"а не файлом: {value!r}"
            )
        if not os.access(path, os.R_OK):
            return (
                f"файл тестового репозитория недоступен для чтения: "
                f"{value!r}"
            )
    else:
        # В реальном режиме --repo — это URL репозитория.
        if not _is_url(value):
            return (
                f"в режиме реального репозитория параметр --repo должен "
                f"быть URL (http:// или https://), получено: {value!r} "
                "(для локального файла используйте --test-repo)"
            )
    return ""


def _validate_package_version(value: str) -> str:
    """Проверяет версию пакета (1.0.0, 2.0-SNAPSHOT, 1.0+build и т. п.)."""
    if not value or not value.strip():
        return "версия пакета не должна быть пустой"
    if value.strip() != value:
        return (
            f"недопустимая версия пакета: {value!r} "
            "(пробелы по краям запрещены)"
        )
    if not _VERSION_RE.match(value):
        return (
            f"недопустимая версия пакета: {value!r} "
            "(допустимы буквы, цифры, '.', '-', '_' и '+', "
            "например 1.0.0 или 2.0-SNAPSHOT)"
        )
    return ""


def _validate_output_file(value: str) -> str:
    """Проверяет имя выходного PNG-файла (расширение .png,
    родительский каталог)."""
    if not value or not value.strip():
        return "имя выходного файла не должно быть пустым"
    if value.strip() != value:
        return (
            f"недопустимое имя выходного файла: {value!r} "
            "(пробелы по краям запрещены)"
        )
    if "\x00" in value:
        return (
            f"недопустимое имя выходного файла: {value!r} "
            "(символ NUL запрещён)"
        )
    if not value.lower().endswith(".png"):
        return (
            f"имя выходного файла должно оканчиваться на .png "
            f"(изображение графа сохраняется в PNG), получено: {value!r}"
        )
    path = Path(value)
    if path.exists() and path.is_dir():
        return (
            f"имя выходного файла является существующим каталогом: "
            f"{value!r}"
        )
    # Родительский каталог, если задан, должен существовать уже сейчас:
    # на этапе 1 мы ничего не создаём, поэтому молчаливое создание было
    # бы неожиданным. Пустой parent означает текущий каталог — он всегда
    # есть.
    parent = path.parent
    if str(parent) not in ("", ".") and not parent.exists():
        return (
            f"родительский каталог выходного файла не существует: "
            f"{str(parent)!r}"
        )
    return ""


def _validate_filter(value: str) -> str:
    """Проверяет подстроку фильтра (длина, отсутствие переводов строк)."""
    # Пустая строка означает «фильтр не задан» и допустима только как
    # значение по умолчанию; явно переданный пустой --filter — ошибка,
    # она проверяется в parse_command_line до вызова этой функции.
    if len(value) > MAX_FILTER_LENGTH:
        return (
            f"подстрока фильтрации слишком длинная "
            f"(максимум {MAX_FILTER_LENGTH} символов)"
        )
    if "\n" in value or "\r" in value:
        return (
            "подстрока фильтрации не должна содержать переводы строк"
        )
    return ""


def validate_config(config: Config) -> str:
    """Проверяет уже разобранную конфигурацию.

    Возвращает текст ошибки или пустую строку.
    """
    if config.package is None:
        return (
            "не задано имя анализируемого пакета "
            "(параметр --package обязателен)"
        )
    err = _validate_package(config.package)
    if err:
        return err
    err = _validate_repo(config.repo, config.test_repo_mode)
    if err:
        return err
    err = _validate_package_version(config.package_version)
    if err:
        return err
    err = _validate_output_file(config.output_file)
    if err:
        return err
    err = _validate_filter(config.filter_substring)
    if err:
        return err
    return ""


# ---------------------------------------------------------------------------
# Разбор командной строки
# ---------------------------------------------------------------------------

# Параметры со значением: имя -> (атрибут Config, отображаемое имя для
# ошибок)
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

# Параметры-флаги (без значения): имя -> (атрибут Config, значение)
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


def parse_command_line(args: list[str]) -> ConfigParseResult:
    """Разбирает argv (без имени программы) в Config.

    Поддерживаются обе формы записи, как в pr_3:
    ``--package guava`` и ``--package=guava``.
    При повторном указании параметра побеждает последнее значение.
    """
    result = ConfigParseResult()
    config = result.config

    i = 0
    while i < len(args):
        arg = args[i]

        # Форма --opt=value
        if "=" in arg and arg.startswith("-"):
            name, _, value = arg.partition("=")
            if name in _VALUE_OPTIONS:
                if value == "":
                    result.error = f"параметр {name} требует значения"
                    return result
                setattr(config, _VALUE_OPTIONS[name], value)
                i += 1
                continue
            if name in _FLAG_OPTIONS:
                result.error = f"параметр {name} не принимает значения"
                return result
            result.error = f"неизвестный параметр: {name}"
            return result

        if arg in _VALUE_OPTIONS:
            attr = _VALUE_OPTIONS[arg]
            if i + 1 >= len(args):
                result.error = f"параметр {arg} требует значения"
                return result
            value = args[i + 1]
            # Явно переданный пустой фильтр — ошибка, а не «не задан».
            if attr == "filter_substring" and value == "":
                result.error = (
                    "подстрока фильтрации не должна быть пустой "
                    "(или не указывайте --filter)"
                )
                return result
            setattr(config, attr, value)
            i += 2
            continue

        if arg in _FLAG_OPTIONS:
            attr, flag_value = _FLAG_OPTIONS[arg]
            setattr(config, attr, flag_value)
            i += 1
            continue

        if arg.startswith("-") and arg != "-":
            result.error = f"неизвестный параметр: {arg}"
            return result

        result.error = (
            f"неожиданный позиционный аргумент: {arg!r} "
            "(все параметры задаются опциями, см. --help)"
        )
        return result

    # --help / --version не требуют обязательных параметров.
    if config.help or config.version:
        return result

    result.error = validate_config(config)
    return result


def usage_text() -> str:
    """Возвращает текст справки по использованию программы."""
    return (
        "Использование: depviz [параметры]\n"
        "\n"
        "Настраиваемые параметры (все — опции командной строки):\n"
        "  -p, --package <имя>        имя анализируемого пакета (обязательно)\n"
        "  -r, --repo <URL|путь>      URL репозитория или путь к файлу\n"
        "                             тестового репозитория\n"
        "                             (по умолчанию: "
        "https://repo.maven.apache.org/maven2)\n"
        "  -t, --test-repo            режим работы с тестовым репозиторием:\n"
        "                             --repo трактуется как путь к файлу\n"
        "      --real-repo            режим реального репозитория (по "
        "умолчанию):\n"
        "                             --repo трактуется как URL\n"
        "  -v, --package-version <вер> версия пакета (по умолчанию: latest)\n"
        "  -o, --output <файл>        имя сгенерированного файла с "
        "изображением\n"
        "                             графа, только .png (по умолчанию: "
        "graph.png)\n"
        "      --ascii-tree           вывести зависимости в виде "
        "ASCII-дерева\n"
        "      --no-ascii-tree        не выводить ASCII-дерево (по "
        "умолчанию)\n"
        "  -f, --filter <подстрока>   подстрока для фильтрации пакетов\n"
        "  -h, --help                 эта справка\n"
        "  -V, --version              версия приложения\n"
        "\n"
        "Допустимы обе формы записи: --package guava и --package=guava.\n"
        "При запуске приложение печатает все параметры в формате "
        "ключ-значение.\n"
        "Этап 1: сбор графа зависимостей ещё не реализован (этапы 2–5).\n"
    )


def _quoted(value: str) -> str:
    """Оборачивает значение в кавычки для вывода в конфигурации."""
    return f'"{value}"'


def format_config(config: Config) -> str:
    """Все параметры в формате «ключ — значение» (п. 3 задания этапа 1)."""
    lines = ["[config] параметры запуска:"]
    lines.append(f"[config]   package: {_quoted(config.package or '')}")
    lines.append(f"[config]   repo: {_quoted(config.repo)}")
    if config.test_repo_mode:
        lines.append("[config]   test_repo_mode: true (тестовый "
                     "репозиторий)")
        try:
            absolute = Path(config.repo).expanduser().resolve()
            lines.append(f"[config]   repo (абс. путь): {absolute}")
        except OSError:
            pass
    else:
        lines.append("[config]   test_repo_mode: false (реальный "
                     "репозиторий)")
    lines.append(
        f"[config]   package_version: {_quoted(config.package_version)}"
    )
    lines.append(f"[config]   output_file: {_quoted(config.output_file)}")
    lines.append(
        f"[config]   ascii_tree: "
        f"{'true' if config.ascii_tree else 'false'}"
    )
    if config.filter_substring:
        lines.append(f"[config]   filter: {_quoted(config.filter_substring)}")
    else:
        lines.append('[config]   filter: "" (не задана)')
    lines.append(f"[config]   app_version: {APP_VERSION}")
    return "\n".join(lines) + "\n"


def print_config(config: Config, out=None) -> None:
    """Печатает параметры запуска. По умолчанию — в stdout."""
    if out is None:
        out = sys.stdout
    out.write(format_config(config))
    out.flush()
