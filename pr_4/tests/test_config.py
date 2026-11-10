"""Юнит-тесты разбора и проверки параметров (этап 1).

Запуск из корня pr_4:
    python3 -m unittest discover -s tests -v
или:
    PYTHONPATH=src python3 -m unittest discover -s tests -v
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from depviz.config import parse_command_line  # noqa: E402


class TestDefaults(unittest.TestCase):
    def test_minimal_run_uses_defaults(self):
        result = parse_command_line(["--package", "guava"])
        self.assertTrue(result.ok(), result.error)
        cfg = result.config
        self.assertEqual(cfg.package, "guava")
        self.assertEqual(cfg.repo, "https://repo.maven.apache.org/maven2")
        self.assertFalse(cfg.test_repo_mode)
        self.assertEqual(cfg.package_version, "latest")
        self.assertEqual(cfg.output_file, "graph.png")
        self.assertFalse(cfg.ascii_tree)
        self.assertEqual(cfg.filter_substring, "")

    def test_group_artifact_package(self):
        result = parse_command_line(["-p", "com.google.guava:guava"])
        self.assertTrue(result.ok(), result.error)
        self.assertEqual(result.config.package, "com.google.guava:guava")

    def test_equals_form(self):
        result = parse_command_line(["--package=guava", "--package-version=32.1.2"])
        self.assertTrue(result.ok(), result.error)
        self.assertEqual(result.config.package_version, "32.1.2")

    def test_last_value_wins(self):
        result = parse_command_line(
            ["--package", "first", "--package", "second"]
        )
        self.assertTrue(result.ok(), result.error)
        self.assertEqual(result.config.package, "second")

    def test_help_and_version_skip_required_package(self):
        for args in (["--help"], ["-h"], ["--version"], ["-V"]):
            result = parse_command_line(args)
            self.assertTrue(result.ok(), f"{args}: {result.error}")


class TestAllParameters(unittest.TestCase):
    def test_all_parameters_together(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False
        ) as tmp:
            tmp.write("A -> B\n")
            tmp_path = tmp.name
        result = parse_command_line(
            [
                "--package", "com.example:app",
                "--repo", tmp_path,
                "--test-repo",
                "--package-version", "1.0.0",
                "--output", "out/graph.png" if False else "graph.png",
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
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tmp:
            tmp.write("A\n")
            tmp_path = tmp.name
        result = parse_command_line(
            ["-p", "guava", "-r", tmp_path, "--test-repo", "--real-repo"]
        )
        # После --real-repo --repo снова трактуется как URL, поэтому
        # локальный путь должен дать ошибку — это и проверяем.
        self.assertFalse(result.ok())
        self.assertIn("URL", result.error)


class TestErrors(unittest.TestCase):
    def assert_error(self, args, needle):
        result = parse_command_line(args)
        self.assertFalse(result.ok(), f"ожидалась ошибка для {args}")
        self.assertIn(needle, result.error)

    def test_missing_package(self):
        self.assert_error([], "--package")

    def test_unknown_parameter(self):
        self.assert_error(["--package", "guava", "--bogus"], "неизвестный параметр")

    def test_missing_value(self):
        self.assert_error(["--package"], "требует значения")

    def test_empty_equals_value(self):
        self.assert_error(["--package="], "требует значения")

    def test_positional_argument(self):
        self.assert_error(["guava"], "позиционный аргумент")

    def test_flag_with_value(self):
        self.assert_error(["--package", "guava", "--ascii-tree=true"], "не принимает значения")

    def test_bad_package_name(self):
        self.assert_error(["--package", "bad name!"], "недопустимое имя пакета")

    def test_bad_package_version(self):
        self.assert_error(
            ["--package", "guava", "--package-version", "1.0 /beta"],
            "недопустимая версия пакета",
        )

    def test_bad_output_extension(self):
        self.assert_error(
            ["--package", "guava", "--output", "graph.jpg"],
            ".png",
        )

    def test_empty_filter(self):
        self.assert_error(
            ["--package", "guava", "--filter", ""],
            "не должна быть пустой",
        )

    def test_repo_not_url_in_real_mode(self):
        self.assert_error(
            ["--package", "guava", "--repo", "not-a-url"],
            "URL",
        )

    def test_repo_url_in_test_mode(self):
        self.assert_error(
            ["--package", "guava", "--repo", "https://example.com/repo", "--test-repo"],
            "путём к файлу",
        )

    def test_test_repo_file_not_found(self):
        self.assert_error(
            ["--package", "guava", "--repo", "/tmp/нет-такого-файла.txt", "--test-repo"],
            "не найден",
        )

    def test_test_repo_is_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assert_error(
                ["--package", "guava", "--repo", tmpdir, "--test-repo"],
                "каталогом",
            )

    def test_output_parent_not_exists(self):
        self.assert_error(
            ["--package", "guava", "--output", "нет-такого-каталога/graph.png"],
            "родительский каталог",
        )


if __name__ == "__main__":
    unittest.main()
