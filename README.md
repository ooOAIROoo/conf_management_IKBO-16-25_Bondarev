# conf_management_IKBO-16-25_Bondarev

Практические работы по курсу «Конфигурационное управление».

| Работа | Тема | Отчёт |
|--------|------|-------|
| 1 | Командная строка UNIX, bash-скрипты | [pr_1/Pr_1.md](pr_1/Pr_1.md) |
| 2 | Менеджеры пакетов, зависимости | [pr_2/Pr_2.md](pr_2/Pr_2.md) |
| 3 | Эмулятор командной строки ОС с виртуальной файловой системой (вариант №3) | [pr_3/Pr_3.md](pr_3/Pr_3.md) |
| 4 | Визуализация графа зависимостей для менеджера пакетов (вариант №3, этапы 1–5) | [pr_4/Pr_4.md](pr_4/Pr_4.md) |

## Практика 3

Эмулятор оболочки UNIX-подобной ОС на C++17 с VFS в оперативной памяти:
REPL, парсер аргументов с кавычками, параметры командной строки, стартовые
скрипты, загрузка VFS из CSV (с Base64 для двоичных данных), команды
`ls`, `cd`, `who`, `tree`, `uname`, `touch`, `rmdir`, `exit`.

Сборка и запуск:

```bash
cmake -S pr_3 -B pr_3/build -DCMAKE_BUILD_TYPE=Release
cmake --build pr_3/build -j
./pr_3/build/bin/emu --vfs pr_3/vfs/demo.csv
```

Полный прогон проверок: `pr_3/scripts/run_all.sh`.
Подробности — в [pr_3/README.md](pr_3/README.md).

## Практика 4

Инструмент визуализации графа зависимостей для менеджера пакетов
(Java/Maven, вариант №3). Выполнены все пять этапов: конфигурация
из командной строки, загрузка Maven POM (parent, dependencyManagement,
BOM), обход графа в ширину с фильтром и обрывом циклов, обратные
зависимости, вывод ASCII-деревом, в Graphviz `.dot` и PNG.

Своя реализация: только стандартная библиотека Python, без менеджеров
пакетов и сторонних библиотек. Graphviz используется через `dot`,
если установлен; иначе PNG рисуется встроенным рендером.

Запуск (скрипты в корне репозитория, поддерживают Windows и Linux/macOS):

```bash
./run.sh --package guava           # Linux/macOS
run.bat --package guava            # Windows
```

То же самое вручную:

```bash
# тестовый репозиторий (без сети)
PYTHONPATH=pr_4/src python3 -m depviz --package A \
    --repo pr_4/test_repo/sample.txt --test-repo --ascii-tree

# реальный Maven-репозиторий
PYTHONPATH=pr_4/src python3 -m depviz \
    --package com.google.guava:guava --package-version 32.1.2-jre
```

Тесты и проверки:

```bash
./run.sh test       # юнит-тесты (63 теста)
./run.sh style      # стиль по критериям отчёта
./run.sh check      # всё вместе
```

То же для Windows: `run.bat test`, `run.bat style`, `run.bat check`.

Полный прогон проверок: `pr_4/scripts/run_all.sh`.
Подробности — в [pr_4/README.md](pr_4/README.md).

## Коды возврата pr_4

| Код | Значение |
|-----|----------|
| `0` | Успех |
| `1` | Ошибка получения данных (сеть, POM, файл) |
| `2` | Ошибка в параметрах командной строки |
