# -*- coding: utf-8 -*-
"""
对比「索引侧」与「递归遍历侧」的同一类文件列表，定位差集目录分布。

用法：
    python diff_analysis.py --es-list list_es.txt --walk-list list_walk.txt
    （列表可用 collect_lists.py 生成）

论文结论：两侧差集 9,400 条全部位于 node_modules，反向差集为 0。
原因是索引工具配置显式排除了 node_modules，而非索引覆盖不全。
"""
import argparse
import collections

ap = argparse.ArgumentParser(description="Diff indexed vs traversed path lists.")
ap.add_argument("--es-list", required=True, help="Path list from the index side")
ap.add_argument("--walk-list", required=True, help="Path list from the traversal side")
ap.add_argument("--top", type=int, default=20, help="Show top N directories")
args = ap.parse_args()


def load(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return [ln.strip() for ln in f if ln.strip()]


es = load(args.es_list)
walk = load(args.walk_list)

es_set = {p.lower() for p in es}
walk_set = {p.lower() for p in walk}

only_walk = walk_set - es_set
only_es = es_set - walk_set

print("indexed side    : %d" % len(es_set))
print("traversed side  : %d" % len(walk_set))
print("only traversed  : %d" % len(only_walk))
print("only indexed    : %d" % len(only_es))
print()


def top_dirs(paths, depth=2, n=20):
    """按路径前 depth 段聚合计数"""
    c = collections.Counter()
    for p in paths:
        parts = p.split("\\")
        # parts[0] = 卷标, parts[1..] 是目录
        key = "\\".join(parts[: depth + 1])
        c[key] += 1
    return c.most_common(n)


print("=== only traversed: top %d dirs (depth=2) ===" % args.top)
for k, v in top_dirs(only_walk, depth=2, n=args.top):
    print("%6d  %s" % (v, k))
print()

print("=== only traversed: by first-level dir ===")
for k, v in top_dirs(only_walk, depth=1, n=args.top):
    print("%6d  %s" % (v, k))
print()

print("=== only indexed: by first-level dir ===")
for k, v in top_dirs(only_es, depth=1, n=args.top):
    print("%6d  %s" % (v, k))
print()

# 特殊目录归类
SPECIAL = [
    ("$RECYCLE.BIN", "$RECYCLE.BIN"),
    ("node_modules", "node_modules"),
    (".git\\", ".git"),
    ("__pycache__", "__pycache__"),
    ("site-packages", "site-packages"),
    ("AppData", "AppData"),
    ("$Recycle", "$Recycle"),
    (".venv", ".venv"),
    ("venv\\", "venv"),
    ("dist\\", "dist"),
    ("build\\", "build"),
    (".cache", ".cache"),
    ("\\Temp\\", "Temp"),
    ("\\tmp\\", "tmp"),
]

print("=== only traversed: classified by special dir (overlapping) ===")
for pat, label in SPECIAL:
    n = sum(1 for p in only_walk if pat.lower() in p)
    if n:
        print("%6d  %s" % (n, label))
