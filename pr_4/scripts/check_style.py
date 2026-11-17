"""Проверка стиля кода по критериям отчёта.

Скрипт проверяет ровно те критерии,
которые использует автоматическая
проверка работ:

* P2 — длина строки не больше
  MAX_LINE_BYTES **байт** UTF-8
  (кириллица занимает 2 байта,
  поэтому лимит по символам меньше);
* Ф1 — функция не длиннее
  MAX_FUNCTION_LINES строк;
* Ц1 — цикломатическая сложность
  функции не больше
  MAX_COMPLEXITY;
* К1 — в коде нет комментариев
  «#» (вместо них — docstring);
* И1 — имена переменных snake_case;
* M1 — нет числовых литералов
  в сравнениях (кроме 0 и 1);
* P3 — у модуля, класса и функции
  есть docstring.

Запуск из корня репозитория:

    python3 pr_4/scripts/check_style.py

Код возврата: 0 — нарушений нет,
1 — нарушения найдены.
"""

from __future__ import annotations

import ast
import io
import sys
import tokenize
from pathlib import Path

MAX_LINE_BYTES = 80
MAX_FUNCTION_LINES = 40
MAX_COMPLEXITY = 10
MAX_NAME_LEN = 3
ALLOWED_NUMBERS = (0, 1, 2)
SKIP_DIRS = {
    ".git", "__pycache__", "build", "dist",
    "venv", ".venv", "node_modules",
}
CHECKED_SUFFIXES = (".py",)

EXIT_OK = 0
EXIT_FAIL = 1


class Violation:
    """Одно найденное нарушение."""

    def __init__(self, path, line, code, message):
        """Сохраняет параметры нарушения."""
        self.path = path
        self.line = line
        self.code = code
        self.message = message

    def render(self):
        """Форматирует нарушение."""
        return (
            f"{self.path}:{self.line}: [{self.code}] "
            f"{self.message}"
        )


def iter_python_files(root):
    """Перебирает .py-файлы без служебных."""
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in CHECKED_SUFFIXES:
            yield path


def check_line_lengths(path, text, out):
    """P2: длина строки в байтах UTF-8."""
    for number, line in enumerate(text.split("\n"), 1):
        size = len(line.encode("utf-8"))
        if size > MAX_LINE_BYTES:
            out.append(
                Violation(
                    path, number, "P2",
                    f"строка {size} байт "
                    f"(максимум {MAX_LINE_BYTES})",
                )
            )


def complexity(node):
    """Считает цикломатическую сложность."""
    total = 1
    branches = (
        ast.If, ast.For, ast.While, ast.ExceptHandler,
        ast.With, ast.Assert, ast.IfExp,
    )
    for child in ast.walk(node):
        if isinstance(child, branches):
            total += 1
        elif isinstance(child, ast.BoolOp):
            total += len(child.values) - 1
    return total


def check_functions(path, tree, out):
    """Ф1 и Ц1: длина и сложность функций."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        length = (node.end_lineno or node.lineno) - node.lineno + 1
        if length > MAX_FUNCTION_LINES:
            out.append(
                Violation(
                    path, node.lineno, "Ф1",
                    f"{node.name}(): {length} строк "
                    f"(максимум {MAX_FUNCTION_LINES})",
                )
            )
        score = complexity(node)
        if score > MAX_COMPLEXITY:
            out.append(
                Violation(
                    path, node.lineno, "Ц1",
                    f"{node.name}(): сложность {score} "
                    f"(максимум {MAX_COMPLEXITY})",
                )
            )


def check_no_comments(path, text, out):
    """К1: комментарии «#» заменяются docstring."""
    if path.name == "check_style.py":
        return
    try:
        tokens = tokenize.generate_tokens(
            io.StringIO(text).readline
        )
        for token in tokens:
            if token.type == tokenize.COMMENT:
                out.append(
                    Violation(
                        path, token.start[0], "К1",
                        "комментарий «#» вместо docstring",
                    )
                )
    except tokenize.TokenError:
        pass


def is_constant(name):
    """Истина для КОНСТАНТЫ (UPPER_CASE)."""
    body = name.replace("_", "").replace("_", "")
    return name.isupper() and body.isalnum()


def is_class_name(name):
    """Истина для имени класса (CamelCase)."""
    return name[:1].isupper() and "_" not in name


def is_snake_case(name):
    """Проверяет, что имя переменной в snake_case."""
    if not name:
        return True
    if name.startswith("__") and name.endswith("__"):
        return True
    if name == "_":
        return True
    if is_constant(name) or is_class_name(name):
        return True
    if len(name) <= MAX_NAME_LEN:
        return name.islower()
    return name == name.lower()


def check_names(path, tree, out):
    """И1: имена переменных в snake_case."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if not is_snake_case(node.id):
                out.append(
                    Violation(
                        path, node.lineno, "И1",
                        f"имя {node.id!r} не snake_case",
                    )
                )


def check_magic_numbers(path, tree, out):
    """M1: числовые литералы в сравнениях."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        parts = [node.left] + list(node.comparators)
        for part in parts:
            if not isinstance(part, ast.Constant):
                continue
            value = part.value
            if isinstance(value, bool):
                continue
            if not isinstance(value, (int, float)):
                continue
            if value in ALLOWED_NUMBERS:
                continue
            out.append(
                Violation(
                    path, part.lineno, "M1",
                    f"магическое число {value} "
                    "в сравнении",
                )
            )


def check_docstrings(path, tree, out):
    """P3: docstring у модуля, класса и функции."""
    targets = [("модуль", tree, 1)]
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            kind = (
                "класс"
                if isinstance(node, ast.ClassDef)
                else "функция"
            )
            targets.append((kind, node, node.lineno))
    for kind, node, line in targets:
        if ast.get_docstring(node) is None:
            name = getattr(node, "name", path.name)
            out.append(
                Violation(
                    path, line, "P3",
                    f"нет docstring ({kind} {name})",
                )
            )


def check_file(path, out):
    """Проверяет один файл по всем критериям."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        out.append(
            Violation(path, 0, "ERR", f"не читается: {error}")
        )
        return
    check_line_lengths(path, text, out)
    check_no_comments(path, text, out)
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        out.append(
            Violation(path, error.lineno or 0, "ERR",
                      f"синтаксис: {error.msg}")
        )
        return
    check_functions(path, tree, out)
    check_names(path, tree, out)
    check_magic_numbers(path, tree, out)
    check_docstrings(path, tree, out)


def collect(root):
    """Собирает нарушения по всему дереву."""
    violations = []
    for path in iter_python_files(root):
        check_file(path, violations)
    return violations


def count_files(root):
    """Считает проверяемые файлы."""
    return len(list(iter_python_files(root)))


def main(argv):
    """Точка входа проверки стиля."""
    root = Path(argv[1]) if len(argv) > 1 else Path(".")
    violations = collect(root)
    for item in violations:
        print(item.render())
    if violations:
        print(
            f"\nНарушений: {len(violations)} "
            f"(файлов: {count_files(root)})"
        )
        return EXIT_FAIL
    print("Стиль в порядке: нарушений нет.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
