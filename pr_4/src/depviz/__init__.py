"""depviz — визуализатор графа
зависимостей для Maven.

Практика №4, вариант №3. Реализованы
все пять этапов:

1. конфигурация из командной строки;
2. загрузка Maven POM (parent, BOM);
3. обход графа в ширину с фильтром;
4. обратные зависимости;
5. ASCII-дерево, Graphviz и PNG.
"""

from .version import APP_VERSION, STAGE_DESCRIPTION

__all__ = ["APP_VERSION", "STAGE_DESCRIPTION"]
__version__ = APP_VERSION
