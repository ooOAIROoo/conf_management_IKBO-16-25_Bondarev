"""Этап 3: граф с транзитивностью.

Граф строится обходом в ширину (BFS)
с явной очередью, без рекурсии. Обход
учитывает предельную глубину и
подстроку фильтра, а циклы обрываются
по признаку «вершина уже раскрыта на
такой же или меньшей глубине».

Ошибка загрузки корневого пакета
фатальна, у остальных пакетов она
превращается в предупреждение, и пакет
считается листом графа.
"""

from __future__ import annotations

import sys

ROOT_DEPTH = 0
STEP = 1
WARN_PREFIX = "Предупреждение: "


class GraphNode:
    """Вершина графа: имя и список детей."""

    def __init__(self, name: str, version: str = ""):
        """Создаёт вершину с именем и версией."""
        self.name = name
        self.version = version
        self.children: list[str] = []

    def label(self) -> str:
        """Подпись вершины для вывода."""
        if self.version:
            return f"{self.name}:{self.version}"
        return self.name


class Graph:
    """Граф зависимостей: вершины и рёбра."""

    def __init__(self, root: str):
        """Создаёт граф с корневой вершиной."""
        self.root = root
        self.nodes: dict[str, GraphNode] = {}
        self.order: list[str] = []

    def ensure(self, name: str, version: str = "") -> GraphNode:
        """Вершина; создаётся при отсутствии."""
        node = self.nodes.get(name)
        if node is None:
            node = GraphNode(name, version)
            self.nodes[name] = node
            self.order.append(name)
        return node

    def add_edge(self, parent: str, child: str) -> None:
        """Добавляет ребро parent -> child."""
        node = self.ensure(parent)
        if child not in node.children:
            node.children.append(child)

    def vertex_count(self) -> int:
        """Число вершин."""
        return len(self.nodes)

    def edge_count(self) -> int:
        """Число рёбер."""
        total = 0
        for node in self.nodes.values():
            total += len(node.children)
        return total

    def children_of(self, name: str) -> list[str]:
        """Дети вершины; у листа пусто."""
        node = self.nodes.get(name)
        if node is None:
            return []
        return node.children


def apply_filter(names: list[str], substring: str) -> list[str]:
    """Убирает имена с подстрокой."""
    if not substring:
        return list(names)
    return [name for name in names if substring not in name]


def load_children(package: str, get_children, substring: str,
                  is_root: bool) -> list[str]:
    """Зависимости с учётом фильтра.

    Ошибка корня фатальна, у остальных
    она превращается в предупреждение.
    """
    try:
        children = get_children(package)
    except ValueError as error:
        if is_root:
            raise
        message = WARN_PREFIX + f"{package}: {error}"
        print(message, file=sys.stderr)
        children = []
    return apply_filter(children, substring)


def bfs_graph(root: str, get_children, max_depth: int,
              substring: str = "") -> Graph:
    """Строит граф обходом в ширину.

    Очередь хранит пары (пакет, глубина).
    Словарь expanded помнит минимальную
    глубину раскрытия вершины: повторный
    заход на такую же или большую глубину
    пропускается, и это обрывает циклы.
    """
    graph = Graph(root)
    graph.ensure(root)
    expanded: dict[str, int] = {}
    queue: list[tuple[str, int]] = [(root, ROOT_DEPTH)]
    head = 0
    while head < len(queue):
        package, depth = queue[head]
        head += 1
        if package in expanded and depth >= expanded[package]:
            continue
        expanded[package] = depth
        if depth >= max_depth:
            continue
        is_root = depth == ROOT_DEPTH
        children = load_children(
            package, get_children, substring, is_root
        )
        for child in children:
            graph.add_edge(package, child)
            graph.ensure(child)
        for child in children:
            queue.append((child, depth + STEP))
    return graph


def build_reverse(root: str, get_children, max_depth: int,
                  substring: str = "") -> Graph:
    """Граф обратных зависимостей.

    Обход начинается с искомого пакета и
    идёт по инвертированным рёбрам: для
    каждой вершины заново собираются все
    пакеты репозитория и выясняется, кто
    от неё зависит. Глубина ограничивает
    длину цепочки «кто зависит».
    """
    graph = Graph(root)
    graph.ensure(root)
    expanded: dict[str, int] = {}
    queue: list[tuple[str, int]] = [(root, ROOT_DEPTH)]
    head = 0
    while head < len(queue):
        package, depth = queue[head]
        head += 1
        if package in expanded and depth >= expanded[package]:
            continue
        expanded[package] = depth
        if depth >= max_depth:
            continue
        parents = find_dependents(package, get_children)
        for parent in parents:
            graph.add_edge(package, parent)
            graph.ensure(parent)
        for parent in parents:
            queue.append((parent, depth + STEP))
    return graph


def find_dependents(target: str, get_children) -> list[str]:
    """Ищет пакеты, у которых есть ребро в target.

    Обходятся все пакеты, известные
    функции зависимостей. Ошибки загрузки
    отдельных пакетов игнорируются, чтобы
    один недоступный POM не ломал поиск.
    """
    candidates = get_all_names(get_children)
    result = []
    for name in candidates:
        if name == target:
            continue
        try:
            children = get_children(name)
        except ValueError:
            continue
        filtered = apply_filter(children, "")
        if target in filtered:
            result.append(name)
    return result


def get_all_names(get_children) -> list[str]:
    """Все пакеты, известные функции.

    Список прикладывается к геттеру
    атрибутом all_names.
    """
    names = getattr(get_children, "all_names", None)
    if names is None:
        return []
    return list(names)


def collect_parents(graph: Graph, target: str) -> list[str]:
    """Пакеты, зависящие от target."""
    parents = []
    for name in graph.order:
        if target in graph.children_of(name):
            parents.append(name)
    return parents
