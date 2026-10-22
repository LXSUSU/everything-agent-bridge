# 补充实测 · 2026-10-22

> 背景：初稿方法节偏教科书式解释，缺少只有作者本人才掌握的事实。
> 本组补测不改文风，只把"只有作者算得出来"的事实测出来。
> 全部命令可复现，未编造任何参数；测不出来的明确标"未测"。

---

## 一、引号语义（论文表 2 数据来源）

`es.exe` 的双引号表示**整名精确匹配**，不是字符串定界；通配符与点号在引号内失去通配含义。

| 查询式 | 语义 | 命中数 |
|---|---|---:|
| `*.md` | 扩展名匹配 | 29,555 |
| `"*.md"` | 整名等于字面量 `*.md` | 0 |
| `README` | 名称含该串 | 1,914 |
| `"README"` | 整名等于 `README`（仅目录） | 6 |
| `README.md` | 名称含该串 | 1,474 |
| `"README.md"` | 整名等于该串 | 0 |

关键观察：`"README"` 的 6 条命中全部是**名为 README 的目录**（如 `README\.aar`、`README\ABOUT.MD`），
不含任何 `README.md`。说明引号匹配的是整名，而非"包含"。

复现：

```
es.exe -get-result-count "*.md"     -path "<test-volume>/"   # 29555
es.exe -get-result-count '"*.md"'   -path "<test-volume>/"   # 0
es.exe -get-result-count "README"   -path "<test-volume>/"   # 1914
es.exe -get-result-count '"README"' -path "<test-volume>/"   # 6
```

---

## 二、命名管道与进程会话（论文 3.3 节机制证据）

管道枚举：`.NET System.IO.Directory.GetFiles("\\.\pipe\")` 共 491 条，其中与本文相关两条：

| 管道 | 用途 |
|---|---|
| `\\.\pipe\Everything IPC` | CLI 连接此管道 |
| `\\.\pipe\Everything Service` | 服务提权代理，非索引服务 |

同一时刻的进程与会话：

| 进程 | SessionId | 说明 |
|---|---|---|
| 索引进程 A | **0**（服务会话） | Everything.exe 1.5.0.1423b |
| 索引进程 B | **1**（用户会话） | Everything.exe 1.5.0.1423b |

当前 shell 会话 = 1。两条管道并存，但由不同会话的进程持有；CLI 连的是 Session 1 那条。

---

## 三、错误码 8 复现（不必停索引进程）

```
es.exe -instance nosuchinstance -get-result-count "*"
→ stderr: Error 8: Everything IPC not found. Please make sure Everything is running.
→ exit code = 8
```

- 用不存在的实例名即可等价复现"IPC 不可达"，**无需停止正在运行的 Everything**。
- 因此可直接用作部署验收的连通性检查。
- 对照：正常查询 exit=0；无匹配结果同样 exit=0（默认不报错，需 `-no-result-error` 才设错误级别）。

---

## 四、`-timeout` 参数的实际行为

帮助中确有 `-timeout <milliseconds>`。但实测 `-timeout 1` 仍返回正常结果（4,190,702 条），
说明它**不是硬性中断**，更可能是连接等待上限。

本文未据此下任何结论，正文亦未引用该参数——测不准的东西不写。

---

## 五、1.32 倍命中差异的根因（论文 4.3 节第二点）

两侧路径列表逐条求差集：

| 项 | 数值 |
|---|---:|
| 索引侧 `*.md`（测试卷） | 29,555 |
| 递归遍历侧 `*.md`（测试卷） | 38,955 |
| 差集（仅遍历有） | **9,400** |
| 反向差集（仅 ES 有） | **0** |
| 差集中位于 `node_modules` 的比例 | **9,400 / 9,400 = 100%** |

配置证据（`<Everything install dir>\Everything.ini`，第 916、917、918、2895 行）：

```
exclude_list_enabled=1
exclude_hidden_files_and_folders=0
exclude_system_files_and_folders=0
exclude_folders=*\*\*\*\*\*\*\*\*\node_modules,*\*\*\*\*\*\*\*\node_modules,... ,*\node_modules
```

**结论**：差异不是"索引覆盖不全"，而是**配置层面有意排除 node_modules**；
且明确不排除隐藏文件与系统文件。

⚠️ 原稿写的"系统保留目录、部分隐藏项未建立索引"是**双重错误**，已按实测修正。

旁证：两次采集相隔约 24 小时，两侧各增加 39 条（38,916→38,955 / 29,516→29,555），
**差值恒为 9,400**。若差异源于索引滞后，差值应随索引增长而波动。

---

## 六、完整输出到文件的遍历耗时（口径补充）

| 执行方式 | 耗时 | 说明 |
|---|---:|---|
| 遍历 + 累加路径长度（不输出全文） | 67.851 s | 论文基线表采用此口径 |
| 遍历 + 完整写出全部路径到文件 | **207.46 s** | 更接近 Agent 实际获取全量结果 |

相差 3.06 倍。若以 207.46 s 计，延迟缩减为 1,080 倍（论文正文已注明）。

---

## 七、复现脚本与中间产物

| 文件 | 用途 |
|---|---|
| `code/es_bench.py` | 五类查询延迟（n=30） |
| `code/diff_analysis.py` | 两侧列表差集与目录聚合 |
| `list_es.txt` | 索引侧测试卷全部 `.md` 路径（29,555 条），由 `code/collect_lists.py` 生成，含本机路径，未随仓库发布 |
| `list_walk.txt` | 遍历侧测试卷全部 `.md` 路径（38,955 条），同上 |
| `code/draw_fig1.py` | 图 1 生成（300 dpi，含复用边界标注） |

---

## 八、未测与边界

- **未测**命名管道 vs 本地 HTTP 的延迟差异。论文已写明"本文未单独测量"，不补数字。
- **未测**常驻连接（长驻服务/库调用）能压到多少延迟。仅作为后续工作提出。
- 异常值 311.27 ms **未定位成因**（样本未记时间戳），论文按"推测为调度抖动，未验证"处理。
- 测试期间未关 Defender 实时扫描、未暂停索引自动更新——论文 4.2 节已如实声明。
