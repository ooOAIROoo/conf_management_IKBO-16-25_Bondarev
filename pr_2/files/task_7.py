#!/usr/bin/env python3
"""
Задача 7: задача о зависимостях пакетов в общей форме.

Действуем как настоящий пакетный менеджер: описание пакетов и их зависимостей
лежит в структуре данных (словарь METADATA — в реальности такой словарь
менеджер получает из реестра: PyPI JSON, npm registry и т.п.), а система
ограничений MiniZinc строится по этому словарю АВТОМАТИЧЕСКИ.

Формат словаря:
    METADATA[name][version] = {dep_name: (lo, hi)}   # lo <= v < hi, hi=None - без верха
    ROOT = {dep_name: (lo, hi)}                      # зависимости корневого пакета
В модели 0 означает "пакет не установлен", i >= 1 - индекс версии в списке версий.

Запуск:  python3 files/task_7.py [t6|t5]
Скрипт генерирует files/task_7.mzn и, если в системе есть MiniZinc,
запускает его; иначе решает перебором (для проверки/демо).
"""
import shutil
import subprocess
import sys
from itertools import product
from pathlib import Path

V = lambda s: tuple(int(x) for x in s.split("."))

# ---- метаданные из условия задачи 6 ----
META_T6 = {
    "foo":    {"1.0.0": {},
               "1.1.0": {"left": ("1.0.0", "2.0.0"), "right": ("1.0.0", "2.0.0")}},
    "left":   {"1.0.0": {"shared": ("1.0.0", None)}},
    "right":  {"1.0.0": {"shared": (None, "2.0.0")}},
    "shared": {"1.0.0": {"target": ("1.0.0", "2.0.0")}, "2.0.0": {}},
    "target": {"1.0.0": {}, "2.0.0": {}},
}
ROOT_T6 = {"foo": ("1.0.0", "2.0.0"), "target": ("2.0.0", "3.0.0")}

# ---- метаданные из задачи 5 (рисунок PubGrub), та же генерация ----
META_T5 = {
    "menu":     {"1.0.0": {"dropdown": ("1.0.0", "2.0.0")},
                 "1.1.0": {"dropdown": ("2.0.0", None)},
                 "1.2.0": {"dropdown": ("2.0.0", None)},
                 "1.3.0": {"dropdown": ("2.0.0", None)},
                 "1.4.0": {"dropdown": ("2.0.0", None)},
                 "1.5.0": {"dropdown": ("2.0.0", None)}},
    "dropdown": {"1.8.0": {"icons": ("1.0.0", "2.0.0")},
                 "2.0.0": {"icons": ("2.0.0", None)},
                 "2.1.0": {"icons": ("2.0.0", None)},
                 "2.2.0": {"icons": ("2.0.0", None)},
                 "2.3.0": {"icons": ("2.0.0", None)}},
    "icons":    {"1.0.0": {}, "2.0.0": {}},
}
ROOT_T5 = {"menu": ("1.0.0", "2.0.0"), "icons": ("1.0.0", "2.0.0")}


def versions(meta, name):
    return sorted(meta[name], key=V)


def idx_range(meta, name, rng):
    """индексы версий (1-based), попадающих в диапазон [lo, hi)"""
    lo, hi = rng
    lo = V(lo) if lo else None
    hi = V(hi) if hi else None
    return [i for i, v in enumerate(versions(meta, name), 1)
            if (lo is None or V(v) >= lo) and (hi is None or V(v) < hi)]


def build_mzn(meta, root):
    names = list(meta)
    L = ["% сгенерировано task_7.py по метаданным; 0 = пакет не установлен"]
    for p in names:
        L.append(f"var 0..{len(versions(meta, p))}: {p};")
    L.append("")
    # требования корневого пакета
    for dep, rng in root.items():
        r = idx_range(meta, dep, rng)
        L.append(f"constraint {dep} >= {r[0]} /\\ {dep} <= {r[-1]};  % root: {dep} {rng}")
    L.append("")
    # зависимости каждой версии каждого пакета
    for q in names:
        for i, ver in enumerate(versions(meta, q), 1):
            for dep, rng in meta[q][ver].items():
                r = idx_range(meta, dep, rng)
                L.append(f"constraint ({q} = {i}) -> ({dep} >= {r[0]} /\\ {dep} <= {r[-1]});"
                         f"  % {q} {ver} -> {dep} {rng}")
    L.append("")
    # ставим только то, что понадобилось (поддержанность решения)
    for p in names:
        if p in root:
            continue
        parents = [f"({q} = {i})"
                   for q in names
                   for i, ver in enumerate(versions(meta, q), 1)
                   if p in meta[q][ver] and idx_range(meta, p, meta[q][ver][p])]
        if parents:
            or_sep = " \\/ "
            L.append(f"constraint ({p} > 0) -> ({or_sep.join(parents)});")
        else:
            L.append(f"constraint {p} = 0;")
    L.append("")
    # вывод
    L.append("solve satisfy;")
    L.append("")
    for p in names:
        vs = ", ".join(f'"{v}"' for v in versions(meta, p))
        L.append(f"array[1..{len(versions(meta, p))}] of string: {p}V = [{vs}];")
    L.append("output [")
    body = []
    for p in names:
        body.append(f'  "{p} " ++ (if fix({p}) = 0 then "not installed" '
                    f'else {p}V[fix({p})] endif) ++ "\\n"')
    L.append(" ++\n".join(body))
    L.append("];")
    return "\n".join(L) + "\n"


def brute(meta, root):
    """перебор для самопроверки: все комбинации версий (0 = не ставим)"""
    names = list(meta)
    doms = [range(0, len(versions(meta, p)) + 1) for p in names]
    sols = []
    for combo in product(*doms):
        sel = dict(zip(names, combo))
        ok = all(sel[d] in idx_range(meta, d, r) for d, r in root.items())
        if ok:
            for q in names:
                if sel[q]:
                    ver = versions(meta, q)[sel[q] - 1]
                    for dep, rng in meta[q][ver].items():
                        if sel[dep] not in idx_range(meta, dep, rng):
                            ok = False
                            break
                if not ok:
                    break
        if ok:
            for p in names:
                if p in root or sel[p] == 0:
                    continue
                needed = any(
                    sel[q] and p in meta[q][versions(meta, q)[sel[q] - 1]]
                    and sel[p] in idx_range(meta, p, meta[q][versions(meta, q)[sel[q] - 1]][p])
                    for q in names)
                if not needed:
                    ok = False
                    break
        if ok:
            sols.append(sel)
    return sols


def show(meta, sel):
    return "\n".join(
        f"{p} " + ("not installed" if sel[p] == 0 else versions(meta, p)[sel[p] - 1])
        for p in meta)


if __name__ == "__main__":
    meta, root = (META_T5, ROOT_T5) if len(sys.argv) > 1 and sys.argv[1] == "t5" \
        else (META_T6, ROOT_T6)
    mzn = build_mzn(meta, root)
    out = Path(__file__).with_name("task_7.mzn")
    out.write_text(mzn)
    print(f"--- model written to {out} ---")
    print(mzn)
    if shutil.which("minizinc"):
        subprocess.run(["minizinc", "--solver", "Gecode", str(out)])
    else:
        print("--- minizinc not found, solving by brute force ---")
        sols = brute(meta, root)
        print(f"solutions: {len(sols)}")
        for s in sols:
            print(show(meta, s))
            print("----------")
