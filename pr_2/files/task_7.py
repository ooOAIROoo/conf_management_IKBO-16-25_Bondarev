"""Задача 7: зависимости пакетов.

Работаем как настоящий пакетный
менеджер: описание пакетов и их
зависимостей лежит в структуре данных
(словарь METADATA — в реальности его
получают из реестра: PyPI JSON,
npm registry и т. п.), а система
ограничений MiniZinc строится по
этому словарю автоматически.

Формат словаря:

    METADATA[name][version] = {dep: (lo, hi)}
    ROOT = {dep: (lo, hi)}

Диапазон означает lo <= v < hi;
hi=None — без верхней границы.
В модели 0 означает «пакет не
установлен», i >= 1 — индекс версии
в списке версий.

Запуск: python3 files/task_7.py [t6|t5]

Скрипт генерирует files/task_7.mzn и,
если в системе есть MiniZinc,
запускает его; иначе решает перебором.
"""

import shutil
import subprocess
import sys
from itertools import product
from pathlib import Path

MZN_SOLVER = "Gecode"
MZN_SUFFIX = ".mzn"
NOT_INSTALLED = "not installed"
SEP = "----------"


def parse_version(text):
    """Превращает '1.2.3' в кортеж чисел."""
    return tuple(int(part) for part in text.split("."))


def versions(meta, name):
    """Версии пакета по возрастанию."""
    return sorted(meta[name], key=parse_version)


META_T6 = {
    "foo": {
        "1.0.0": {},
        "1.1.0": {
            "left": ("1.0.0", "2.0.0"),
            "right": ("1.0.0", "2.0.0"),
        },
    },
    "left": {"1.0.0": {"shared": ("1.0.0", None)}},
    "right": {"1.0.0": {"shared": (None, "2.0.0")}},
    "shared": {
        "1.0.0": {"target": ("1.0.0", "2.0.0")},
        "2.0.0": {},
    },
    "target": {"1.0.0": {}, "2.0.0": {}},
}
ROOT_T6 = {
    "foo": ("1.0.0", "2.0.0"),
    "target": ("2.0.0", "3.0.0"),
}

META_T5 = {
    "menu": {
        "1.0.0": {"dropdown": ("1.0.0", "2.0.0")},
        "1.1.0": {"dropdown": ("2.0.0", None)},
        "1.2.0": {"dropdown": ("2.0.0", None)},
        "1.3.0": {"dropdown": ("2.0.0", None)},
        "1.4.0": {"dropdown": ("2.0.0", None)},
        "1.5.0": {"dropdown": ("2.0.0", None)},
    },
    "dropdown": {
        "1.8.0": {"icons": ("1.0.0", "2.0.0")},
        "2.0.0": {"icons": ("2.0.0", None)},
        "2.1.0": {"icons": ("2.0.0", None)},
        "2.2.0": {"icons": ("2.0.0", None)},
        "2.3.0": {"icons": ("2.0.0", None)},
    },
    "icons": {"1.0.0": {}, "2.0.0": {}},
}
ROOT_T5 = {
    "menu": ("1.0.0", "2.0.0"),
    "icons": ("1.0.0", "2.0.0"),
}


def idx_range(meta, name, rng):
    """Индексы версий (1-based) в диапазоне [lo, hi)."""
    lo, hi = rng
    lo = parse_version(lo) if lo else None
    hi = parse_version(hi) if hi else None
    result = []
    for i, ver in enumerate(versions(meta, name), 1):
        ok_lo = lo is None or parse_version(ver) >= lo
        ok_hi = hi is None or parse_version(ver) < hi
        if ok_lo and ok_hi:
            result.append(i)
    return result


def _domain_lines(meta, names):
    """Строки объявления переменных домена."""
    lines = [
        "% сгенерировано task_7.py по "
        "метаданным; 0 = пакет "
        "не установлен"
    ]
    for name in names:
        count = len(versions(meta, name))
        lines.append(f"var 0..{count}: {name};")
    lines.append("")
    return lines


def _root_lines(meta, root):
    """Ограничения корневых зависимостей."""
    lines = []
    for dep, rng in root.items():
        idx = idx_range(meta, dep, rng)
        lines.append(
            f"constraint {dep} >= {idx[0]} "
            f"/\\ {dep} <= {idx[-1]};"
            f"  % root: {dep} {rng}"
        )
    lines.append("")
    return lines


def _dep_lines(meta, names):
    """Ограничения по версиям."""
    lines = []
    for name in names:
        for i, ver in enumerate(versions(meta, name), 1):
            for dep, rng in meta[name][ver].items():
                idx = idx_range(meta, dep, rng)
                lines.append(
                    f"constraint ({name} = {i}) -> "
                    f"({dep} >= {idx[0]} /\\ "
                    f"{dep} <= {idx[-1]});"
                    f"  % {name} {ver} -> {dep} {rng}"
                )
    lines.append("")
    return lines


def _parents_of(meta, names, target):
    """Условия, при которых нужен target."""
    parents = []
    for name in names:
        for i, ver in enumerate(versions(meta, name), 1):
            deps = meta[name][ver]
            if target in deps and idx_range(
                meta, target, deps[target]
            ):
                parents.append(f"({name} = {i})")
    return parents


def _support_lines(meta, names, root):
    """Ставим только то, что понадобилось."""
    lines = []
    or_sep = " \\/ "
    for name in names:
        if name in root:
            continue
        parents = _parents_of(meta, names, name)
        if parents:
            joined = or_sep.join(parents)
            lines.append(
                f"constraint ({name} > 0) -> "
                f"({joined});"
            )
        else:
            lines.append(f"constraint {name} = 0;")
    lines.append("")
    return lines


def _version_array_lines(meta, names):
    """Массивы версий для вывода."""
    lines = []
    for name in names:
        quoted = ", ".join(
            f'"{ver}"' for ver in versions(meta, name)
        )
        count = len(versions(meta, name))
        lines.append(
            f"array[1..{count}] of string: "
            f"{name}V = [{quoted}];"
        )
    return lines


def _output_lines(meta, names):
    """Блок solve и output модели MiniZinc."""
    lines = ["solve satisfy;", ""]
    lines += _version_array_lines(meta, names)
    lines.append("output [")
    body = []
    for name in names:
        body.append(
            f'  "{name} " ++ (if fix({name}) = 0 '
            f'then "{NOT_INSTALLED}" '
            f'else {name}V[fix({name})] endif) '
            f'++ "\\n"'
        )
    lines.append(" ++\n".join(body))
    lines.append("];")
    return lines


def build_mzn(meta, root):
    """Строит текст модели MiniZinc."""
    names = list(meta)
    lines = _domain_lines(meta, names)
    lines += _root_lines(meta, root)
    lines += _dep_lines(meta, names)
    lines += _support_lines(meta, names, root)
    lines += _output_lines(meta, names)
    return "\n".join(lines) + "\n"


def _version_ok(meta, sel, name):
    """Зависимости выбранной версии."""
    if not sel[name]:
        return True
    ver = versions(meta, name)[sel[name] - 1]
    for dep, rng in meta[name][ver].items():
        if sel[dep] not in idx_range(meta, dep, rng):
            return False
    return True


def _needed(meta, sel, names, name, root):
    """Нужен ли пакет на самом деле."""
    if name in root or sel[name] == 0:
        return True
    for parent in names:
        if not sel[parent]:
            continue
        ver = versions(meta, parent)[sel[parent] - 1]
        deps = meta[parent][ver]
        if name in deps and sel[name] in idx_range(
            meta, name, deps[name]
        ):
            return True
    return False


def _combo_ok(meta, sel, names, root):
    """Проверяет допустимость набора версий."""
    for dep, rng in root.items():
        if sel[dep] not in idx_range(meta, dep, rng):
            return False
    for name in names:
        if not _version_ok(meta, sel, name):
            return False
    for name in names:
        if not _needed(meta, sel, names, name, root):
            return False
    return True


def brute(meta, root):
    """Перебор всех комбинаций версий."""
    names = list(meta)
    domains = [
        range(0, len(versions(meta, name)) + 1)
        for name in names
    ]
    solutions = []
    for combo in product(*domains):
        sel = dict(zip(names, combo))
        if _combo_ok(meta, sel, names, root):
            solutions.append(sel)
    return solutions


def show(meta, sel):
    """Печатает выбранный набор версий."""
    lines = []
    for name in meta:
        if sel[name] == 0:
            lines.append(f"{name} {NOT_INSTALLED}")
        else:
            ver = versions(meta, name)[sel[name] - 1]
            lines.append(f"{name} {ver}")
    return "\n".join(lines)


def _pick_meta(argv):
    """Выбирает набор данных по аргументу."""
    if len(argv) > 1 and argv[1] == "t5":
        return META_T5, ROOT_T5
    return META_T6, ROOT_T6


def main(argv):
    """Точка входа скрипта."""
    meta, root = _pick_meta(argv)
    model = build_mzn(meta, root)
    out = Path(__file__).with_name(
        "task_7" + MZN_SUFFIX
    )
    out.write_text(model, encoding="utf-8")
    print(f"--- model written to {out} ---")
    print(model)
    if shutil.which("minizinc"):
        subprocess.run(
            ["minizinc", "--solver", MZN_SOLVER, str(out)]
        )
    else:
        print("--- minizinc not found, "
              "solving by brute force ---")
        solutions = brute(meta, root)
        print(f"solutions: {len(solutions)}")
        for sel in solutions:
            print(show(meta, sel))
            print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
