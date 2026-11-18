"""Тесты этапов 3-5: обход, фильтр, вывод."""

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

graph_module = importlib.import_module("depviz.graph")
render_module = importlib.import_module("depviz.render")
testrepo_module = importlib.import_module("depviz.testrepo")

CHAIN = {"A": ["B", "C"], "B": ["D"], "C": ["D", "E"],
         "D": ["F"], "E": ["F"], "F": []}

CYCLE = {"X": ["Y"], "Y": ["Z"], "Z": ["X"]}


def getter_from(mapping):
    """Геттер по словарю зависимостей."""

    def get_children(name):
        """Зависимости из словаря."""
        return list(mapping.get(name, []))

    get_children.all_names = sorted(mapping)
    return get_children


class TestFilter(unittest.TestCase):
    """Подстрока фильтра."""

    def test_empty_filter_keeps_all(self):
        """Пустой фильтр ничего не убирает."""
        names = ["B", "C"]
        self.assertEqual(
            graph_module.apply_filter(names, ""), ["B", "C"]
        )

    def test_filter_removes_matches(self):
        """Имена с подстрокой убираются."""
        names = ["guava", "guava-testlib", "other"]
        result = graph_module.apply_filter(names, "guava")
        self.assertEqual(result, ["other"])


class TestBfs(unittest.TestCase):
    """Обход в ширину."""

    def test_all_vertices_reached(self):
        """Все вершины попадают в граф."""
        graph = graph_module.bfs_graph(
            "A", getter_from(CHAIN), 10
        )
        self.assertEqual(graph.vertex_count(), 6)

    def test_edges_counted(self):
        """Число рёбер считается без дублей."""
        graph = graph_module.bfs_graph(
            "A", getter_from(CHAIN), 10
        )
        self.assertEqual(graph.edge_count(), 7)

    def test_depth_limits_expansion(self):
        """Глубина ограничивает раскрытие."""
        graph = graph_module.bfs_graph(
            "A", getter_from(CHAIN), 1
        )
        self.assertEqual(graph.children_of("B"), [])

    def test_cycle_terminates(self):
        """Цикл не приводит к зацикливанию."""
        graph = graph_module.bfs_graph(
            "X", getter_from(CYCLE), 5
        )
        self.assertEqual(graph.vertex_count(), 3)

    def test_unknown_root_is_leaf(self):
        """Неизвестный пакет — одна вершина."""
        graph = graph_module.bfs_graph(
            "Z", getter_from(CHAIN), 5
        )
        self.assertEqual(graph.vertex_count(), 1)

    def test_broken_child_is_warning(self):
        """Ошибка не у корня не роняет обход."""

        def broken(name):
            """Падает для пакета B."""
            if name == "B":
                raise ValueError("нет данных")
            return CHAIN.get(name, [])

        broken.all_names = sorted(CHAIN)
        graph = graph_module.bfs_graph("A", broken, 5)
        self.assertIn("A", graph.nodes)

    def test_broken_root_raises(self):
        """Ошибка корня пробрасывается."""

        def broken(name):
            """Всегда падает."""
            raise ValueError("нет данных")

        broken.all_names = []
        with self.assertRaises(ValueError):
            graph_module.bfs_graph("A", broken, 5)


class TestReverse(unittest.TestCase):
    """Обратные зависимости (этап 4)."""

    def test_dependents_of_leaf(self):
        """У листа F находятся зависимые."""
        graph = graph_module.build_reverse(
            "F", getter_from(CHAIN), 10
        )
        self.assertEqual(
            sorted(graph.children_of("F")), ["D", "E"]
        )

    def test_reverse_stops_at_root(self):
        """Цепочка доходит до корня графа."""
        graph = graph_module.build_reverse(
            "F", getter_from(CHAIN), 10
        )
        self.assertIn("A", graph.nodes)

    def test_reverse_depth_limit(self):
        """Глубина ограничивает поиск вверх."""
        graph = graph_module.build_reverse(
            "F", getter_from(CHAIN), 1
        )
        self.assertNotIn("A", graph.nodes)


class TestRenderTree(unittest.TestCase):
    """ASCII-дерево."""

    def test_root_is_first_line(self):
        """Первая строка — корень."""
        graph = graph_module.bfs_graph(
            "A", getter_from(CHAIN), 10
        )
        lines = render_module.render_tree(graph, 10)
        self.assertEqual(lines[0], "A")

    def test_cycle_marked(self):
        """Цикл помечается."""
        graph = graph_module.bfs_graph(
            "X", getter_from(CYCLE), 10
        )
        lines = render_module.render_tree(graph, 10)
        text = "\n".join(lines)
        self.assertIn("(цикл)", text)

    def test_depth_limits_tree(self):
        """Глубина ограничивает дерево."""
        graph = graph_module.bfs_graph(
            "A", getter_from(CHAIN), 10
        )
        lines = render_module.render_tree(graph, 1)
        self.assertEqual(len(lines), 3)


class TestRenderList(unittest.TestCase):
    """Список и сводка."""

    def test_list_contains_counts(self):
        """Последняя строка — сводка."""
        graph = graph_module.bfs_graph(
            "A", getter_from(CHAIN), 10
        )
        lines = render_module.render_list(graph)
        self.assertIn("Вершин: 6", lines[-1])

    def test_leaf_marked(self):
        """У листа видно отсутствие детей."""
        graph = graph_module.bfs_graph(
            "A", getter_from(CHAIN), 10
        )
        text = "\n".join(render_module.render_list(graph))
        self.assertIn("(нет зависимостей)", text)


class TestDot(unittest.TestCase):
    """Исходник Graphviz."""

    def test_dot_has_edges(self):
        """Рёбра попадают в .dot."""
        graph = graph_module.bfs_graph(
            "A", getter_from(CHAIN), 10
        )
        text = render_module.graph_to_dot(graph)
        self.assertIn('"A" -> "B";', text)
        self.assertTrue(text.startswith("digraph"))

    def test_dot_is_balanced(self):
        """Фигурные скобки сбалансированы."""
        graph = graph_module.bfs_graph(
            "A", getter_from(CHAIN), 10
        )
        text = render_module.graph_to_dot(graph)
        self.assertEqual(text.count("{"), text.count("}"))


class TestPng(unittest.TestCase):
    """Встроенный PNG-рендер."""

    def test_png_signature(self):
        """Результат начинается с сигнатуры PNG."""
        graph = graph_module.bfs_graph(
            "A", getter_from(CHAIN), 10
        )
        data = render_module.graph_to_png(graph)
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_png_has_size(self):
        """В заголовке есть ненулевые размеры."""
        graph = graph_module.bfs_graph(
            "A", getter_from(CHAIN), 10
        )
        data = render_module.graph_to_png(graph)
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)

    def test_write_png_creates_file(self):
        """Файл создаётся на диске."""
        graph = graph_module.bfs_graph(
            "A", getter_from(CHAIN), 10
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "g.png")
            render_module.write_png(graph, path)
            self.assertTrue(Path(path).exists())


class TestRepo(unittest.TestCase):
    """Чтение тестового репозитория."""

    def write(self, text):
        """Временный файл; путь к нему."""
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False,
            encoding="utf-8",
        )
        with handle as tmp:
            tmp.write(text)
        return handle.name

    def test_read_simple(self):
        """Простой файл читается."""
        path = self.write("A -> B, C\nB ->\n")
        repository = testrepo_module.read_repository(path)
        self.assertEqual(repository["A"], ["B", "C"])
        self.assertEqual(repository["B"], [])

    def test_comments_skipped(self):
        """Комментарии пропускаются."""
        path = self.write("# комментарий\nA -> B\n")
        repository = testrepo_module.read_repository(path)
        self.assertEqual(list(repository), ["A"])

    def test_bad_name(self):
        """Строчные буквы недопустимы."""
        path = self.write("a -> B\n")
        with self.assertRaises(testrepo_module.TestRepoError):
            testrepo_module.read_repository(path)

    def test_missing_arrow(self):
        """Строка без стрелки отвергается."""
        path = self.write("A B\n")
        with self.assertRaises(testrepo_module.TestRepoError):
            testrepo_module.read_repository(path)

    def test_duplicate_package(self):
        """Повтор пакета отвергается."""
        path = self.write("A -> B\nA -> C\n")
        with self.assertRaises(testrepo_module.TestRepoError):
            testrepo_module.read_repository(path)

    def test_getter_lists_names(self):
        """Геттер отдаёт список всех пакетов."""
        path = self.write("A -> B\nB ->\n")
        getter, repository = testrepo_module.make_test_getter(
            path
        )
        self.assertEqual(getter.all_names, ["A", "B"])
        self.assertEqual(len(repository), 2)


if __name__ == "__main__":
    unittest.main()
