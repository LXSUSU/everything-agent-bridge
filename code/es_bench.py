# -*- coding: utf-8 -*-
"""
ES 查询性能实测 —— 论文数据采集

输出：版本 / 索引规模 / 多类查询的延迟分布

用法：
    python es_bench.py --es es.exe --out es_bench.json --n 30
    也可用环境变量 ES_EXE 指定 es.exe 路径。
"""
import argparse
import json
import os
import statistics
import subprocess
import time

ap = argparse.ArgumentParser(description="Measure ES query latency distribution.")
ap.add_argument("--es", default=os.environ.get("ES_EXE", "es.exe"),
                help="Path to es.exe (default: env ES_EXE or 'es.exe' on PATH)")
ap.add_argument("--out", default="es_bench.json", help="Output JSON path")
ap.add_argument("--n", type=int, default=30, help="Repetitions per query (default: 30)")
args = ap.parse_args()

ES = args.es
N = args.n
OUT = args.out


def run_once(argv):
    t0 = time.perf_counter()
    r = subprocess.run([ES] + argv, capture_output=True)
    t1 = time.perf_counter()
    return (t1 - t0) * 1000.0, r.returncode, r.stdout


def decode(b):
    return b.decode("gbk", "ignore").strip()


print("=== VERSION ===")
_, rc, out = run_once(["-version"])
print("exit=%d  %s" % (rc, decode(out)))

print("\n=== INDEX SCALE ===")
for q in ["*", "*.md", "*.py", "*.txt", "*.gguf", "*.exe"]:
    _, rc, out = run_once(["-get-result-count", q])
    print("%-10s count=%s (exit=%d)" % (q, decode(out), rc))

print("\n=== LATENCY (N=%d per query) ===" % N)
queries = [
    ("ext_md_n20",     ["-n", "20", "*.md"]),
    ("ext_py_n20",     ["-n", "20", "*.py"]),
    ("keyword_n20",    ["-n", "20", "config"]),
    ("ext_md_n100",    ["-n", "100", "*.md"]),
    ("count_md",       ["-get-result-count", "*.md"]),
]

results = {}
for name, qargs in queries:
    lat = []
    outlen = 0
    for i in range(N):
        ms, rc, out = run_once(qargs)
        if rc == 0:
            lat.append(ms)
            if i == 0:
                outlen = len(out)
    lat_sorted = sorted(lat)
    stats = {
        "n": len(lat),
        "mean_ms": round(statistics.mean(lat), 2),
        "stdev_ms": round(statistics.stdev(lat), 2) if len(lat) > 1 else 0.0,
        "min_ms": round(min(lat), 2),
        "max_ms": round(max(lat), 2),
        "p50_ms": round(lat_sorted[len(lat_sorted) // 2], 2),
        "p95_ms": round(lat_sorted[int(len(lat_sorted) * 0.95) - 1], 2),
        "out_bytes": outlen,
    }
    results[name] = stats
    print("%-14s mean=%7.2f  sd=%6.2f  min=%6.2f  p50=%6.2f  p95=%6.2f  max=%7.2f  bytes=%d"
          % (name, stats["mean_ms"], stats["stdev_ms"], stats["min_ms"],
             stats["p50_ms"], stats["p95_ms"], stats["max_ms"], outlen))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\n[saved] %s" % OUT)
