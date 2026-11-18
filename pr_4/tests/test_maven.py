"""Тесты этапа 2: разбор POM."""

import importlib
import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

maven = importlib.import_module("depviz.maven")

GENERIC_POM = b"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <groupId>com.example</groupId>
  <artifactId>app</artifactId>
  <version>1.0.0</version>
  <properties>
    <guava.version>32.1.2-jre</guava.version>
  </properties>
  <dependencies>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>${guava.version}</version>
    </dependency>
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
      <version>4.13.2</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>
"""

BOM_POM = b"""<?xml version="1.0"?>
<project>
  <groupId>com.example</groupId>
  <artifactId>parent</artifactId>
  <version>2.0.0</version>
  <dependencyManagement>
    <dependencies>
      <dependency>
        <groupId>com.google.guava</groupId>
        <artifactId>guava</artifactId>
        <version>33.0.0-jre</version>
      </dependency>
    </dependencies>
  </dependencyManagement>
</project>
"""

CHILD_POM = b"""<?xml version="1.0"?>
<project>
  <parent>
    <groupId>com.example</groupId>
    <artifactId>parent</artifactId>
    <version>2.0.0</version>
  </parent>
  <artifactId>child</artifactId>
  <dependencies>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
    </dependency>
  </dependencies>
</project>
"""


def make_pom(data, group, artifact, version):
    """Строит объект PomFile из текста POM."""
    root = maven.parse_xml(data, "тест")
    coordinate = maven.Coordinate(group, artifact, version)
    return maven.PomFile(root, coordinate)


class TestCoordinate(unittest.TestCase):
    """Координаты артефакта."""

    def test_path_and_name(self):
        """Путь и имя POM по правилам Maven."""
        coordinate = maven.Coordinate(
            "com.google.guava", "guava", "32.1.2"
        )
        self.assertEqual(
            coordinate.path(),
            "com/google/guava/guava/32.1.2/",
        )
        self.assertEqual(
            coordinate.pom_name(), "guava-32.1.2.pom"
        )

    def test_key_and_full(self):
        """Ключ и полное имя корректны."""
        coordinate = maven.Coordinate("g", "a", "1")
        self.assertEqual(coordinate.key(), "g:a")
        self.assertEqual(coordinate.full(), "g:a:1")

    def test_parse_coordinate(self):
        """Строка разбирается на три части."""
        coordinate = maven.parse_coordinate("g:a:1.0")
        self.assertEqual(coordinate.group, "g")
        self.assertEqual(coordinate.artifact, "a")
        self.assertEqual(coordinate.version, "1.0")

    def test_parse_coordinate_without_version(self):
        """Версия может отсутствовать."""
        coordinate = maven.parse_coordinate("g:a")
        self.assertEqual(coordinate.version, "")

    def test_parse_coordinate_bad(self):
        """Строка без двоеточия отвергается."""
        with self.assertRaises(maven.PomError):
            maven.parse_coordinate("только-имя")


class TestPomFile(unittest.TestCase):
    """Разбор одного POM."""

    def test_declared_dependencies(self):
        """Прямые зависимости читаются."""
        pom = make_pom(GENERIC_POM, "com.example", "app", "1")
        self.assertEqual(len(pom.declared), 2)

    def test_property_substitution(self):
        """${...} заменяется свойством."""
        pom = make_pom(GENERIC_POM, "com.example", "app", "1")
        first = pom.declared[0]
        self.assertEqual(first["version"], "32.1.2-jre")

    def test_test_scope_read(self):
        """Область test сохраняется при чтении."""
        pom = make_pom(GENERIC_POM, "com.example", "app", "1")
        second = pom.declared[1]
        self.assertEqual(second["scope"], "test")

    def test_parent_read(self):
        """Родительский POM распознаётся."""
        pom = make_pom(CHILD_POM, "com.example", "child", "1")
        self.assertIsNotNone(pom.parent)
        self.assertEqual(pom.parent.artifact, "parent")
        self.assertEqual(pom.parent.version, "2.0.0")

    def test_management_read(self):
        """dependencyManagement читается."""
        pom = make_pom(BOM_POM, "com.example", "parent", "2")
        self.assertEqual(len(pom.managed), 1)
        self.assertEqual(
            pom.managed[0]["version"], "33.0.0-jre"
        )

    def test_broken_xml(self):
        """Битый XML даёт понятную ошибку."""
        with self.assertRaises(maven.PomError):
            maven.parse_xml(b"<project><oops>", "тест")


class TestPomResolver(unittest.TestCase):
    """Разрешение версий по цепочке POM."""

    def setUp(self):
        """Готовит поддельный репозиторий."""
        self.repository = FakeRepository(
            {
                "com.example:child:1": CHILD_POM,
                "com.example:parent:2.0.0": BOM_POM,
            }
        )
        self.resolver = maven.PomResolver(self.repository)

    def test_managed_version_applied(self):
        """Версия берётся из dependencyManagement."""
        coordinate = maven.Coordinate(
            "com.example", "child", "1"
        )
        deps = self.resolver.direct_dependencies(coordinate)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0]["version"], "33.0.0-jre")

    def test_chain_contains_parent(self):
        """Цепочка включает родителя."""
        coordinate = maven.Coordinate(
            "com.example", "child", "1"
        )
        chain = self.resolver.chain(coordinate)
        self.assertEqual(len(chain), 2)


class FakeRepository:
    """Поддельный репозиторий для тестов."""

    def __init__(self, poms):
        """Запоминает POM по ключам."""
        self.poms = poms

    def load_pom(self, coordinate):
        """Возвращает заранее заданный POM."""
        data = self.poms.get(coordinate.full())
        if data is None:
            raise maven.PomError(
                f"POM не найден: {coordinate.full()}"
            )
        root = maven.parse_xml(data, "тест")
        return maven.PomFile(root, coordinate)


if __name__ == "__main__":
    unittest.main()
