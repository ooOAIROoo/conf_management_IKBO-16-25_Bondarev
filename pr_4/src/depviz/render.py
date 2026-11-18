"""Этап 5: вывод графа.

Модуль умеет три представления:

* список рёбер «пакет -> зависимости»;
* ASCII-дерево от корня;
* язык Graphviz (``.dot``) и PNG.

PNG рисуется утилитой ``dot`` из пакета
Graphviz, если она установлена. Иначе
включается встроенный рендер на
стандартной библиотеке (zlib + struct),
чтобы результат получался всегда.
"""

from __future__ import annotations

import shutil
import subprocess
import zlib

from . import font
from .graph import Graph

TEE = "├── "
CORNER = "└── "
PIPE = "│   "
BLANK = "    "
CYCLE_MARK = " (цикл)"
NO_CHILDREN = "(нет зависимостей)"
EMPTY_VERSION = ""

DOT_HEADER = (
    "digraph dependencies {\n"
    '    rankdir="LR";\n'
    '    node [shape=box, style="rounded", '
    'fontname="Helvetica"];\n'
    '    edge [color="#888888"];\n'
)
DOT_EDGE = '    "{}" -> "{}";\n'
DOT_FOOTER = "}\n"

DOT_COMMAND = "dot"
DOT_ARGS = ("-Tpng",)
MIN_WIDTH = 240
MIN_HEIGHT = 90
NODE_WIDTH = 150
NODE_HEIGHT = 44
H_GAP = 30
V_GAP = 30
MARGIN = 24
TITLE_HEIGHT = 26
TEXT_SCALE = 2
TITLE_SCALE = 3
TEXT_PAD = 6

BLACK = (30, 30, 30)
WHITE = (255, 255, 255)
NODE_FILL = (232, 240, 254)
NODE_EDGE = (63, 81, 181)
ROOT_FILL = (255, 241, 209)
ROOT_EDGE = (191, 118, 0)
EDGE_COLOR = (150, 150, 150)


def render_list(graph: Graph) -> list[str]:
    """Список вида «пакет -> зависимости»."""
    lines = []
    for name in graph.order:
        children = graph.children_of(name)
        text = ", ".join(children) if children else NO_CHILDREN
        lines.append(f"{name} -> {text}")
    lines.append(
        f"Вершин: {graph.vertex_count()}, "
        f"рёбер: {graph.edge_count()}"
    )
    return lines


def _children_marks(count: int) -> list[str]:
    """Метки веток: последняя — угол."""
    marks = [TEE] * count
    if marks:
        marks[-1] = CORNER
    return marks


def _push_children(stack: list, graph: Graph, name: str,
                   prefix: str, path: tuple) -> None:
    """Кладёт детей в стек наоборот."""
    children = graph.children_of(name)
    marks = _children_marks(len(children))
    pairs = list(zip(children, marks))
    for child, mark in reversed(pairs):
        stack.append((child, mark, prefix, path))


def render_tree(graph: Graph, max_depth: int) -> list[str]:
    """ASCII-дерево от корня графа.

    Узел, уже стоящий среди своих
    предков, помечается «(цикл)» и не
    раскрывается.
    """
    root = graph.root
    lines = [root]
    stack: list = []
    _push_children(stack, graph, root, "", (root,))
    while stack:
        name, mark, prefix, path = stack.pop()
        if name in path:
            lines.append(f"{prefix}{mark}{name}{CYCLE_MARK}")
            continue
        lines.append(f"{prefix}{mark}{name}")
        if len(path) < max_depth:
            shift = BLANK if mark == CORNER else PIPE
            _push_children(
                stack, graph, name,
                prefix + shift, path + (name,),
            )
    return lines


def _escape(text: str) -> str:
    """Экранирует кавычки для Graphviz."""
    return text.replace('"', '\\"')


def graph_to_dot(graph: Graph) -> str:
    """Строит текст на языке Graphviz."""
    parts = [DOT_HEADER]
    for name in graph.order:
        for child in graph.children_of(name):
            parts.append(
                DOT_EDGE.format(_escape(name), _escape(child))
            )
    parts.append(DOT_FOOTER)
    return "".join(parts)


def _run_dot(dot_text: str) -> bytes:
    """Запускает Graphviz и возвращает PNG."""
    if shutil.which(DOT_COMMAND) is None:
        raise FileNotFoundError(DOT_COMMAND)
    process = subprocess.run(
        [DOT_COMMAND, *DOT_ARGS],
        input=dot_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        message = process.stderr.decode(
            "utf-8", errors="replace"
        ).strip()
        raise ValueError(f"{DOT_COMMAND} завершился "
                         f"с ошибкой: {message}")
    return process.stdout


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    """Собирает один блок PNG."""
    body = kind + data
    crc = zlib.crc32(body) & 0xFFFFFFFF
    return (
        len(data).to_bytes(4, "big")
        + body
        + crc.to_bytes(4, "big")
    )


class Canvas:
    """Растровый холст RGB для PNG."""

    def __init__(self, width: int, height: int):
        """Создаёт белый холст."""
        self.width = max(width, MIN_WIDTH)
        self.height = max(height, MIN_HEIGHT)
        self.pixels = bytearray(
            bytes(WHITE) * (self.width * self.height)
        )

    def set(self, x: int, y: int, color: tuple) -> None:
        """Ставит пиксель внутри холста."""
        if x < 0 or y < 0:
            return
        if x >= self.width or y >= self.height:
            return
        offset = (y * self.width + x) * 3
        self.pixels[offset:offset + 3] = bytes(color)

    def fill_rect(self, x: int, y: int,
                  wide: int, high: int, color: tuple) -> None:
        """Заливает прямоугольник цветом."""
        for row in range(y, y + high):
            for column in range(x, x + wide):
                self.set(column, row, color)

    def frame_rect(self, x: int, y: int,
                   wide: int, high: int, color: tuple) -> None:
        """Рисует рамку прямоугольника."""
        for column in range(x, x + wide):
            self.set(column, y, color)
            self.set(column, y + high - 1, color)
        for row in range(y, y + high):
            self.set(x, row, color)
            self.set(x + wide - 1, row, color)

    def line(self, x0: int, y0: int,
             x1: int, y1: int, color: tuple) -> None:
        """Отрезок по Брезенхему."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        error = dx - dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            doubled = error * 2
            if doubled > -dy:
                error -= dy
                x0 += sx
            if doubled < dx:
                error += dx
                y0 += sy

    def to_png(self) -> bytes:
        """Кодирует холст в PNG."""
        raw = bytearray()
        stride = self.width * 3
        for row in range(self.height):
            raw.append(0)
            start = row * stride
            raw.extend(self.pixels[start:start + stride])
        header = (
            b"\x89PNG\r\n\x1a\n"
            + _png_chunk(
                b"IHDR",
                self.width.to_bytes(4, "big")
                + self.height.to_bytes(4, "big")
                + bytes((8, 2, 0, 0, 0)),
            )
            + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _png_chunk(b"IEND", b"")
        )
        return header


class Box:
    """Прямоугольник вершины на холсте."""

    def __init__(self, name: str, x: int, y: int):
        """Создаёт рамку для вершины."""
        self.name = name
        self.x = x
        self.y = y

    @property
    def cx(self) -> int:
        """Центр по горизонтали."""
        return self.x + NODE_WIDTH // 2

    @property
    def cy(self) -> int:
        """Центр по вертикали."""
        return self.y + NODE_HEIGHT // 2


def graph_levels(graph: Graph) -> list[list[str]]:
    """Вершины по уровням от корня."""
    levels: list[list[str]] = []
    seen = {graph.root}
    current = [graph.root]
    while current:
        levels.append(current)
        following = []
        for name in current:
            for child in graph.children_of(name):
                if child in seen:
                    continue
                seen.add(child)
                following.append(child)
        current = following
    return levels


def layout_levels(levels: list[list[str]]) -> list[Box]:
    """Координаты вершин по уровням."""
    boxes = []
    for index, level in enumerate(levels):
        y = MARGIN + TITLE_HEIGHT + index * (
            NODE_HEIGHT + V_GAP
        )
        for position, name in enumerate(level):
            x = MARGIN + position * (NODE_WIDTH + H_GAP)
            boxes.append(Box(name, x, y))
    return boxes


def canvas_size(levels: list[list[str]]) -> tuple[int, int]:
    """Размер холста под раскладку."""
    widest = 1
    for level in levels:
        widest = max(widest, len(level))
    width = MARGIN * 2 + widest * NODE_WIDTH
    width += (widest - 1) * H_GAP
    height = MARGIN * 2 + TITLE_HEIGHT
    height += len(levels) * (NODE_HEIGHT + V_GAP)
    return width, height


def draw_text(canvas: Canvas, x: int, y: int,
              text: str, color: tuple, scale: int) -> None:
    """Рисует строку растровым шрифтом."""
    cursor = x
    step = font.advance(scale)
    for char in text:
        pattern = font.glyph(char)
        for row, line in enumerate(pattern):
            for column, symbol in enumerate(line):
                if symbol != "#":
                    continue
                left = cursor + column * scale
                top = y + row * scale
                canvas.fill_rect(
                    left, top, scale, scale, color
                )
        cursor += step


def label_of(name: str) -> str:
    """Короткая подпись вершины."""
    short = name.split(":")[-1]
    return font.fit(short, NODE_WIDTH - TEXT_PAD * 2, TEXT_SCALE)


def centered_x(text: str, box: Box) -> int:
    """X для центрирования подписи."""
    width = font.text_width(text, TEXT_SCALE)
    return box.x + (NODE_WIDTH - width) // 2


def centered_y(box: Box) -> int:
    """Y для центрирования подписи."""
    height = font.GLYPH_HEIGHT * TEXT_SCALE
    return box.y + (NODE_HEIGHT - height) // 2


def draw_graph(canvas: Canvas, graph: Graph,
               boxes: list[Box]) -> None:
    """Рисует рёбра и вершины графа."""
    positions = {box.name: box for box in boxes}
    for name in graph.order:
        source = positions.get(name)
        if source is None:
            continue
        for child in graph.children_of(name):
            target = positions.get(child)
            if target is None:
                continue
            canvas.line(
                source.cx, source.y + NODE_HEIGHT,
                target.cx, target.y, EDGE_COLOR,
            )
    for box in boxes:
        is_root = box.name == graph.root
        fill = ROOT_FILL if is_root else NODE_FILL
        border = ROOT_EDGE if is_root else NODE_EDGE
        canvas.fill_rect(
            box.x, box.y, NODE_WIDTH, NODE_HEIGHT, fill
        )
        canvas.frame_rect(
            box.x, box.y, NODE_WIDTH, NODE_HEIGHT, border
        )
        label = label_of(box.name)
        draw_text(
            canvas,
            centered_x(label, box),
            centered_y(box),
            label,
            BLACK,
            TEXT_SCALE,
        )


def graph_to_png(graph: Graph) -> bytes:
    """Рисует граф в PNG без Graphviz."""
    levels = graph_levels(graph)
    width, height = canvas_size(levels)
    canvas = Canvas(width, height)
    title = font.fit(
        f"Dependencies: {graph.root}",
        canvas.width - MARGIN * 2,
        TITLE_SCALE,
    )
    draw_text(
        canvas, MARGIN, MARGIN, title, BLACK, TITLE_SCALE
    )
    boxes = layout_levels(levels)
    draw_graph(canvas, graph, boxes)
    return canvas.to_png()


def write_png(graph: Graph, path: str) -> str:
    """Сохраняет PNG: dot либо свой рендер.

    Возвращает описание использованного
    способа, чтобы вызывающий код мог
    сообщить его пользователю.
    """
    dot_text = graph_to_dot(graph)
    try:
        data = _run_dot(dot_text)
        engine = "graphviz"
    except FileNotFoundError:
        data = graph_to_png(graph)
        engine = "builtin"
    except (OSError, ValueError):
        data = graph_to_png(graph)
        engine = "builtin"
    with open(path, "wb") as handle:
        handle.write(data)
    return engine
