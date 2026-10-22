# -*- coding: utf-8 -*-
"""
基线实测：传统递归目录遍历 vs ES 索引查询
同时测 es.exe 进程启动固定开销

用法：
    python baseline_bench.py --es es.exe --out baseline_bench.json <volume>/
    python baseline_bench.py <volume1>/ <volume2>/     # 多个卷依次测
"""
import argparse
import json
import os
import statistics
import subprocess
import time

ap = argparse.ArgumentParser(description="Recursive traversal baseline vs ES startup cost.")
ap.add_argument("--es", default=os.environ.get("ES_EXE", "es.exe"),
                help="Path to es.exe (default: env ES_EXE or 'es.exe' on PATH)")
ap.add_argument("--out", default="baseline_bench.json", help="Output JSON path")
ap.add_argument("drive", nargs="*", help="Volume root(s) to scan, e.g. <volume>/")
args = ap.parse_args()

ES = args.es
OUT = args.out
drives = args.drive
if not drives:
    ap.error("请至少指定一个卷根，例如 <volume>/")
result = {}


# ---------- 1. 进程启动固定开销 ----------
print("=== [1] es.exe 进程启动固定开销 (N=20, 空查询 -version) ===")
lat = []
for _ in range(20):
    t0 = time.perf_counter()
    subprocess.run([ES, "-version"], capture_output=True)
    t1 = time.perf_counter()
    lat.append((t1 - t0) * 1000)
result["startup"] = {
    "n": len(lat),
    "mean_ms": round(statistics.mean(lat), 2),
    "stdev_ms": round(statistics.stdev(lat), 2),
    "min_ms": round(min(lat), 2),
    "max_ms": round(max(lat), 2),
}
print("  mean=%.2f ms  sd=%.2f  min=%.2f  max=%.2f"
      % (result["startup"]["mean_ms"], result["startup"]["stdev_ms"],
         result["startup"]["min_ms"], result["startup"]["max_ms"]))


# ---------- 2. 递归遍历基线 ----------
def scan_drive(root):
    """模拟 Agent 传统做法：递归遍历目录树，收集全部文件路径"""
    t0 = time.perf_counter()
    n_files = 0
    n_dirs = 0
    chars = 0
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    try:
                        if e.is_symlink():
                            continue
                        if e.is_dir(follow_symlinks=False):
                            n_dirs += 1
                            stack.append(e.path)
                        else:
                            n_files += 1
                            chars += len(e.path) + 1
                    except OSError:
                        continue
        except OSError:
            continue
    elapsed = time.perf_counter() - t0
    return elapsed, n_files, n_dirs, chars


result["baseline"] = {}

for drv in drives:
    print("\n=== [2] 递归遍历基线 %s ===" % drv)
    try:
        elapsed, nf, nd, chars = scan_drive(drv)
        rec = {
            "drive": drv,
            "elapsed_s": round(elapsed, 3),
            "files": nf,
            "dirs": nd,
            "path_chars": chars,
            "est_tokens_3_5cpt": int(chars / 3.5),
        }
        result["baseline"][drv] = rec
        print("  耗时=%.3f s  文件=%d  目录=%d  路径字符=%d  估算token=%d"
              % (elapsed, nf, nd, chars, int(chars / 3.5)))
    except Exception as ex:
        print("  FAILED: %r" % ex)
        result["baseline"][drv] = {"error": repr(ex)}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("\n[saved] %s" % OUT)
