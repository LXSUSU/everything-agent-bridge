# -*- coding: utf-8 -*-
"""
导出「索引侧」与「递归遍历侧」的同一类文件路径列表，供 diff_analysis.py 比对。

用法：
    python collect_lists.py --es es.exe --volume <volume>/ --pattern "*.md" \\
        --es-out list_es_md.txt --walk-out list_walk_md.txt

说明：输出文件包含本机真实路径，仅用于本地复核，不要提交到仓库。
"""
import argparse
import os
import subprocess

ap = argparse.ArgumentParser(description="Dump indexed vs traversed path lists.")
ap.add_argument("--es", default=os.environ.get("ES_EXE", "es.exe"),
                help="Path to es.exe (default: env ES_EXE or 'es.exe' on PATH)")
ap.add_argument("--volume", required=True, help="Volume root, e.g. <volume>/")
ap.add_argument("--pattern", default="*.md", help="Filename pattern (default: *.md)")
ap.add_argument("--es-out", default="list_es.txt", help="Indexed-side output")
ap.add_argument("--walk-out", default="list_walk.txt", help="Traversal-side output")
ap.add_argument("--n", type=int, default=0,
                help="Result cap passed to es.exe (0 = no cap, default)")
args = ap.parse_args()


def es_paths():
    argv = [args.es, args.pattern, "-path", args.volume]
    if args.n > 0:
        argv[1:1] = ["-n", str(args.n)]
    r = subprocess.run(argv, capture_output=True)
    if r.returncode != 0:
        raise SystemExit("es.exe failed: exit=%d stderr=%s"
                         % (r.returncode, r.stderr.decode("gbk", "ignore").strip()))
    # ES 默认以系统代码页输出，中文环境为 GBK
    text = r.stdout.decode("gbk", "ignore")
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def walk_paths():
    out = []
    for root, dirs, files in os.walk(args.volume):
        for name in files:
            out.append(os.path.join(root, name))
    return out


def matches(path, pattern):
    if pattern == "*":
        return True
    if pattern.startswith("*."):
        return path.lower().endswith(pattern[1:].lower())
    return pattern.lower() in path.lower()


es_list = [p for p in es_paths() if matches(p, args.pattern)]
walk_list = [p for p in walk_paths() if matches(p, args.pattern)]

with open(args.es_out, "w", encoding="utf-8") as f:
    f.write("\n".join(es_list) + "\n")
with open(args.walk_out, "w", encoding="utf-8") as f:
    f.write("\n".join(walk_list) + "\n")

print("indexed  : %d -> %s" % (len(es_list), args.es_out))
print("traversed: %d -> %s" % (len(walk_list), args.walk_out))
print("NOTE: these files contain local absolute paths; do not commit them.")
