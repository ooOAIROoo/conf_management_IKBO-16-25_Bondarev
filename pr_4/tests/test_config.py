"""Юнит-тесты разбора и проверки параметров.

Запуск из корня репозитория:

    ./run.sh test

или напрямую:

    PYTHONPATH=pr_4/src python3 -m unittest
                                  discover -s pr_4/tests -v
"""

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

config_module = importlib.import_module("depviz.config")
parse_command_line = config_module.parse_command_line

DEFAULT_REPO_URL = "https://repo.maven.apache.org/maven2"


def _make_repo_file(text: str) -> str:
    """Создаёт временный файл
    тестового репозитория.

    Возвращает путь к нему.
    """
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False
    )
    with handle as tmp:
        tmp.write(text)
    return handle.name


class TestDefaults(unittest.TestCase):
    """Проверяет значения по умолчанию."""

    def test_minimal_run_uses_defaults(self):
        """Один --package задаёт все умолчания."""
        result = parse_command_line(["--package", "guava"])
        self.assertTrue(result.ok(), result.error)
        cfg = result.config
        self.assertEqual(cfg.package, "guava")
        self.assertEqual(cfg.repo, DEFAULT_REPO_URL)
        self.assertFalse(cfg.test_repo_mode)
        self.assertEqual(cfg.package_version, "latest")
        self.assertEqual(cfg.output_file, "graph.png")
        self.assertFalse(cfg.ascii_tree)
        self.assertEqual(cfg.filter_substring, "")

    def test_group_artifact_package(self):
        """Имя вида groupId:artifactId допустимо."""
        result = parse_command_line(
            ["-p", "com.google.guava:guava"]
        )
        self.assertTrue(result.ok(), result.error)
        self.assertEqual(
            result.config.package,
            "com.google.guava:guava",
        )

    def test_equals_form(self):
        """Работает форма --имя=значение."""
        result = parse_command_line(
            ["--package=guava",
             "--package-version=32.1.2"]
        )
        self.assertTrue(result.ok(), result.error)
        self.assertEqual(
            result.config.package_version, "32.1.2"
        )

    def test_last_value_wins(self):
        """При повторе побеждает
        последнее значение."""
        result = parse_command_line(
            ["--package", "first",
             "--package", "second"]
        )
        self.assertTrue(result.ok(), result.error)
        self.assertEqual(result.config.package, "second")

    def test_help_and_version_skip_required_package(self):
        """--help и --version не требуют --package."""
        for args in (
            ["--help"], ["-h"],
            ["--version"], ["-V"],
        ):
            result = parse_command_line(args)
            self.assertTrue(
                result.ok(), f"{args}: {result.error}"
            )


class TestAllParameters(unittest.TestCase):
    """Проверяет все опции вместе."""

    def test_all_parameters_together(self):
        """Все семь параметров задаются сразу."""
        tmp_path = _make_repo_file("A -> B\n")
        result = parse_command_line(
            [
                "--package", "com.example:app",
                "--repo", tmp_path,
                "--test-repo",
                "--package-version", "1.0.0",
                "--output", "graph.png",
                "--ascii-tree",
                "--filter", "guava",
            ]
        )
        self.assertTrue(result.ok(), result.error)
        cfg = result.config
        self.assertEqual(cfg.package, "com.example:app")
        self.assertEqual(cfg.repo, tmp_path)
        self.assertTrue(cfg.test_repo_mode)
        self.assertEqual(cfg.package_version, "1.0.0")
        self.assertEqual(cfg.output_file, "graph.png")
        self.assertTrue(cfg.ascii_tree)
        self.assertEqual(cfg.filter_substring, "guava")

    def test_real_repo_flag_overrides_test_repo(self):
        """--real-repo: --repo снова URL."""
        tmp_path = _make_repo_file("A\n")
        result = parse_command_line(
            [
                "-p", "guava",
                "-r", tmp_path,
                "--test-repo",
                "--real-repo",
            ]
        )
        self.assertFalse(result.ok())
        self.assertIn("URL", result.error)


class TestErrors(unittest.TestCase):
    """Проверяет ошибки параметров."""

    def assert_error(self, args, needle):
        """Проверяет, что разбор вернул ошибку."""
        result = parse_command_line(args)
        self.assertFalse(
            result.ok(), f"ожидалась ошибка для {args}"
        )
        self.assertIn(needle, result.error)

    def test_missing_package(self):
        """Без --package выдаётся ошибка."""
        self.assert_error([], "--package")

    def test_unknown_parameter(self):
        """Неизвестная опция распознаётся."""
        self.assert_error(
            ["--package", "guava", "--bogus"],
            "неизвестный параметр",
        )

    def test_missing_value(self):
        """Опция без значения распознаётся."""
        self.assert_error(
            ["--package"], "требует значения"
        )

    def test_empty_equals_value(self):
        """Пустое значение после "=" — ошибка."""
        self.assert_error(
            ["--package="], "требует значения"
        )

    def test_positional_argument(self):
        """Позиционный аргумент запрещён."""
        self.assert_error(
            ["guava"], "позиционный аргумент"
        )

    def test_flag_with_value(self):
        """Флаг не принимает значение."""
        self.assert_error(
            [
                "--package", "guava",
                "--ascii-tree=true",
            ],
            "не принимает значения",
        )

    def test_bad_package_name(self):
        """Пробел и "!" в имени — ошибка."""
        self.assert_error(
            ["--package", "bad name!"],
            "недопустимое имя пакета",
        )

    def test_bad_package_version(self):
        """Пробелы и '/' в версии запрещены."""
        self.assert_error(
            [
                "--package", "guava",
                "--package-version", "1.0 /beta",
            ],
            "недопустимая версия пакета",
        )

    def test_bad_output_extension(self):
        """Выходной файл обязан быть .png."""
        self.assert_error(
            [
                "--package", "guava",
                "--output", "graph.jpg",
            ],
            ".png",
        )

    def test_empty_filter(self):
        """Пустой --filter запрещён."""
        self.assert_error(
            ["--package", "guava", "--filter", ""],
            "не должна быть пустой",
        )

    def test_repo_not_url_in_real_mode(self):
        """В реальном режиме --repo обязан быть URL."""
        self.assert_error(
            ["--package", "guava", "--repo", "not-a-url"],
            "URL",
        )

    def test_repo_url_in_test_mode(self):
        """В тестовом режиме URL запрещён."""
        self.assert_error(
            [
                "--package", "guava",
                "--repo", "https://example.com/repo",
                "--test-repo",
            ],
            "путём к файлу",
        )

    def test_test_repo_file_not_found(self):
        """Отсутствующий файл распознаётся."""
        self.assert_error(
            [
                "--package", "guava",
                "--repo", "/tmp/нет-такого-файла.txt",
                "--test-repo",
            ],
            "не найден",
        )

    def test_test_repo_is_directory(self):
        """Каталог вместо файла распознаётся."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assert_error(
                [
                    "--package", "guava",
                    "--repo", tmpdir,
                    "--test-repo",
                ],
                "каталогом",
            )

    def test_output_parent_not_exists(self):
        """Нет родительского каталога."""
        self.assert_error(
            [
                "--package", "guava",
                "--output",
                "нет-такого-каталога/graph.png",
            ],
            "родительский каталог",
        )


if __name__ == "__main__":
    unittest.main()
