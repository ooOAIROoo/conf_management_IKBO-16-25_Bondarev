"""Этап 2: загрузка POM из Maven-репозитория.

Maven хранит артефакты по пути
``groupId/artifactId/version/artifactId-version.pom``.
В POM прямые зависимости лежат в
``<dependencies>``, а версии могут
приходить из трёх мест:

1. явно у зависимости;
2. из ``<parent>`` (наследование);
3. из ``<dependencyManagement>``,
   в том числе из импортированных BOM
   (``<scope>import</scope>``).

Модуль умеет всё перечисленное, чтобы
разрешать версии так же, как Maven.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as xml_tree
from urllib.parse import quote

from .http_client import NotFoundError, fetch

MAVEN_CENTRAL = "https://repo.maven.apache.org/maven2"
POM_SUFFIX = ".pom"
METADATA_FILE = "maven-metadata.xml"
SNAPSHOT_SUFFIX = "-SNAPSHOT"
GROUP_SEPARATOR = "."
PATH_SEPARATOR = "/"

TAG_PARENT = "parent"
TAG_GROUP = "groupId"
TAG_ARTIFACT = "artifactId"
TAG_VERSION = "version"
TAG_DEPENDENCIES = "dependencies"
TAG_DEPENDENCY = "dependency"
TAG_MANAGEMENT = "dependencyManagement"
TAG_SCOPE = "scope"
TAG_TYPE = "type"
TAG_VALUE = "value"
TAG_DEPENDENCY_MANAGEMENT = TAG_MANAGEMENT
SCOPE_IMPORT = "import"
SCOPE_TEST = "test"
SCOPE_PROVIDED = "provided"
SKIPPED_SCOPES = (SCOPE_TEST, SCOPE_PROVIDED)

MAX_PARENT_DEPTH = 10
SNAPSHOT_PATTERN = re.compile(r"^(?P<base>.+)-SNAPSHOT$")


class PomError(ValueError):
    """POM нельзя разобрать или разрешить."""


def _local(tag: str) -> str:
    """Отбрасывает XML-namespace у имени тега."""
    return tag.split("}")[-1]


def _text(node, name: str) -> str:
    """Возвращает текст дочернего элемента."""
    if node is None:
        return ""
    for child in node:
        if _local(child.tag) == name:
            return (child.text or "").strip()
    return ""


def _children(node, name: str) -> list:
    """Дочерние элементы с именем."""
    if node is None:
        return []
    return [c for c in node if _local(c.tag) == name]


def parse_xml(data: bytes, where: str):
    """Разбирает XML с понятной ошибкой."""
    try:
        return xml_tree.fromstring(data)
    except xml_tree.ParseError as error:
        raise PomError(
            f"{where}: некорректный XML ({error})"
        )


class Coordinate:
    """Координаты артефакта Maven."""

    def __init__(self, group: str, artifact: str,
                 version: str = ""):
        """Создаёт координаты groupId:artifactId:version."""
        self.group = group
        self.artifact = artifact
        self.version = version

    def key(self) -> str:
        """Ключ без версии: groupId:artifactId."""
        return f"{self.group}:{self.artifact}"

    def full(self) -> str:
        """Полное имя с версией."""
        if self.version:
            return f"{self.key()}:{self.version}"
        return self.key()

    def path(self) -> str:
        """Путь к каталогу артефакта."""
        group_path = self.group.replace(
            GROUP_SEPARATOR, PATH_SEPARATOR
        )
        return (
            f"{group_path}/{self.artifact}/"
            f"{self.version}/"
        )

    def pom_name(self) -> str:
        """Имя POM-файла."""
        return f"{self.artifact}-{self.version}{POM_SUFFIX}"

    def __repr__(self) -> str:
        """Строка для отладки."""
        return f"Coordinate({self.full()!r})"


def parse_coordinate(text: str) -> Coordinate:
    """Разбирает строку groupId:artifactId[:version]."""
    parts = text.split(":")
    if len(parts) < 2:
        raise PomError(
            f"ожидалось groupId:artifactId, получено {text!r}"
        )
    group, artifact = parts[0], parts[1]
    version = parts[2] if len(parts) > 2 else ""
    return Coordinate(group, artifact, version)


class MavenRepository:
    """Клиент Maven-репозитория по HTTP."""

    def __init__(self, base_url: str):
        """Запоминает базовый URL репозитория."""
        self.base_url = base_url.rstrip(PATH_SEPARATOR)
        self._pom_cache: dict[str, object] = {}
        self._version_cache: dict[str, list[str]] = {}

    def url_for(self, coordinate: Coordinate) -> str:
        """Собирает URL POM для координат."""
        return (
            f"{self.base_url}/"
            f"{quote(coordinate.path())}"
            f"{quote(coordinate.pom_name())}"
        )

    def metadata_url(self, group: str, artifact: str) -> str:
        """Собирает URL maven-metadata.xml артефакта."""
        group_path = group.replace(
            GROUP_SEPARATOR, PATH_SEPARATOR
        )
        return (
            f"{self.base_url}/{group_path}/"
            f"{artifact}/{METADATA_FILE}"
        )

    def read_metadata_versions(self, group: str,
                               artifact: str) -> list[str]:
        """Версии из maven-metadata.xml."""
        url = self.metadata_url(group, artifact)
        data = fetch(url)
        root = parse_xml(data, url)
        versions = []
        for node in root.iter():
            if _local(node.tag) != "version":
                continue
            text = (node.text or "").strip()
            if text and text not in versions:
                versions.append(text)
        return versions

    def resolve_version(self, coordinate: Coordinate) -> str:
        """Определяет версию артефакта."""
        version = coordinate.version
        if version and version != "latest":
            return version
        try:
            versions = self.read_metadata_versions(
                coordinate.group, coordinate.artifact
            )
        except (NotFoundError, ValueError) as error:
            raise PomError(
                f"не удалось определить версию "
                f"{coordinate.key()}: {error}"
            )
        if not versions:
            raise PomError(
                f"у артефакта {coordinate.key()} нет версий"
            )
        stable = [
            v for v in versions if SNAPSHOT_SUFFIX not in v
        ]
        return (stable or versions)[-1]

    def load_pom(self, coordinate: Coordinate):
        """Загружает и разбирает POM.

        Результат кешируется.
        """
        key = coordinate.full()
        cached = self._pom_cache.get(key)
        if cached is not None:
            return cached
        url = self.url_for(coordinate)
        try:
            data = fetch(url)
        except NotFoundError as error:
            raise PomError(
                f"POM не найден: {key} ({error})"
            )
        except ValueError as error:
            raise PomError(f"ошибка загрузки {key}: {error}")
        root = parse_xml(data, url)
        pom = PomFile(root, coordinate)
        self._pom_cache[key] = pom
        return pom


class PomFile:
    """Разобранный POM одного артефакта."""

    def __init__(self, root, coordinate: Coordinate):
        """Сохраняет дерево XML и координаты."""
        self.root = root
        self.coordinate = coordinate
        self.parent = self._read_parent()
        self.properties = self._read_properties()
        self.managed = self._read_management()
        self.declared = self._read_declared()

    def _read_parent(self) -> Coordinate | None:
        """Читает координаты родительского POM."""
        node = None
        for child in self.root:
            if _local(child.tag) == TAG_PARENT:
                node = child
                break
        if node is None:
            return None
        group = _text(node, TAG_GROUP)
        artifact = _text(node, TAG_ARTIFACT)
        version = _text(node, TAG_VERSION)
        if not group or not artifact:
            return None
        return Coordinate(group, artifact, version)

    def _read_properties(self) -> dict[str, str]:
        """Читает блок <properties>."""
        result = {}
        for child in self.root:
            if _local(child.tag) != "properties":
                continue
            for item in child:
                name = _local(item.tag)
                value = (item.text or "").strip()
                if name and value:
                    result[name] = value
        return result

    def substitute(self, value: str) -> str:
        """Подставляет ${...} из properties и parent."""
        text = value
        for _ in range(MAX_PARENT_DEPTH):
            changed = False
            for name, replacement in self.properties.items():
                token = "${" + name + "}"
                if token in text:
                    text = text.replace(token, replacement)
                    changed = True
            if not changed:
                break
        if self.parent is not None:
            text = text.replace(
                "${project.parent.version}",
                self.parent.version,
            )
            text = text.replace(
                "${project.parent.groupId}",
                self.parent.group,
            )
        return text

    def _dependency_list(self, container) -> list[dict]:
        """Читает список <dependency> из контейнера."""
        items = []
        for block in _children(container, TAG_DEPENDENCIES):
            for node in _children(block, TAG_DEPENDENCY):
                items.append(self._read_dependency(node))
        return items

    def _read_dependency(self, node) -> dict:
        """Читает одну зависимость."""
        return {
            "group": self.substitute(
                _text(node, TAG_GROUP)
            ),
            "artifact": self.substitute(
                _text(node, TAG_ARTIFACT)
            ),
            "version": self.substitute(
                _text(node, TAG_VERSION)
            ),
            "scope": self.substitute(
                _text(node, TAG_SCOPE)
            ),
            "type": self.substitute(
                _text(node, TAG_TYPE)
            ),
        }

    def _read_declared(self) -> list[dict]:
        """Читает прямые зависимости POM."""
        return self._dependency_list(self.root)

    def _read_management(self) -> list[dict]:
        """Читает <dependencyManagement>."""
        for child in self.root:
            if _local(child.tag) == TAG_MANAGEMENT:
                return self._dependency_list(child)
        return []


class PomResolver:
    """Разрешает версии по цепочке POM."""

    def __init__(self, repository: MavenRepository):
        """Запоминает клиент репозитория."""
        self.repository = repository
        self._chain_cache: dict[str, list] = {}

    def chain(self, coordinate: Coordinate) -> list:
        """Цепочка POM: сам, затем родители."""
        key = coordinate.full()
        cached = self._chain_cache.get(key)
        if cached is not None:
            return cached
        pom = self.repository.load_pom(coordinate)
        result = [pom]
        current = pom
        seen = {key}
        for _ in range(MAX_PARENT_DEPTH):
            parent = current.parent
            if parent is None:
                break
            if not parent.version:
                break
            parent_key = parent.full()
            if parent_key in seen:
                break
            seen.add(parent_key)
            parent_pom = self.repository.load_pom(parent)
            result.append(parent_pom)
            current = parent_pom
        self._chain_cache[key] = result
        return result

    def managed_versions(self, coordinate: Coordinate) -> dict:
        """Версии из dependencyManagement."""
        result = {}
        for pom in self.chain(coordinate):
            for item in pom.managed:
                key = f"{item['group']}:{item['artifact']}"
                if item["version"] and key not in result:
                    result[key] = item["version"]
        return result

    def direct_dependencies(self,
                            coordinate: Coordinate) -> list:
        """Прямые зависимости с версиями."""
        poms = self.chain(coordinate)
        managed = self.managed_versions(coordinate)
        result = []
        seen = set()
        for pom in poms:
            for item in pom.declared:
                key = f"{item['group']}:{item['artifact']}"
                if key in seen:
                    continue
                if item["scope"] in SKIPPED_SCOPES:
                    continue
                seen.add(key)
                version = item["version"] or managed.get(key, "")
                result.append(
                    {
                        "key": key,
                        "version": version,
                        "scope": item["scope"],
                    }
                )
        return result

    def all_versions(self, group: str,
                     artifact: str) -> list[str]:
        """Версии артефакта из метаданных."""
        return self.repository.read_metadata_versions(
            group, artifact
        )


def make_maven_getter(base_url: str, version: str = ""):
    """Функция зависимостей для Maven."""
    repository = MavenRepository(base_url)
    resolver = PomResolver(repository)

    def get_dependencies(name: str) -> list:
        """Прямые зависимости пакета."""
        coordinate = parse_coordinate(name)
        if not coordinate.version:
            coordinate.version = (
                version if version and version != "latest"
                else resolver.repository.resolve_version(
                    coordinate
                )
            )
        return [
            item["key"] + (
                ":" + item["version"]
                if item["version"] else ""
            )
            for item in resolver.direct_dependencies(coordinate)
        ]

    return get_dependencies
