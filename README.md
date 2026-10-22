# 面向 AI Agent 的本地文件检索加速

**Accelerating Local File Retrieval for AI Agents via a Reused Desktop Index: Design and Measurement**

本仓库包含论文、实验代码与聚合结果。

方法不重写检索算法，而是把确定性的文件名检索下沉到常驻内存的桌面索引，命令行接口复用其官方 CLI；自研部分集中在接入层的编码转换、引号语义适配、默认限条，以及"索引召回 + 内容精排"两级检索策略。

## 关键结果

| 指标 | 递归遍历 | 索引接入 | 比值 |
|---|---:|---:|---:|
| 索引规模 | — | 4,170,958 条 | — |
| 返回 20 / 100 条延迟 | — | 213.78 / 218.06 ms | 差值 4.28 ms |
| 枚举全部 Markdown（931 GB 卷） | 67.851 s | 0.192 s | 353× |
| 输出规模 | 38,916 条 / 4,839,399 字符（约 138.3 万 token） | 20 条 / 1,440 字符（约 411 token） | 3,361× |

查询延迟与结果集规模无关：返回 20 条与 100 条的差值（4.28 ms）小于各自的单次测量标准差（11.80 ms 与 30.16 ms）。端到端时间主要由进程创建与 IPC 建立占据。

两项负面实测同样可复现：索引进程安装为系统服务后命令行接口不可用（错误码 8，命名管道按会话隔离）；查询语法中引号表示整名精确匹配，习惯性加引号会使数万条结果归零。

## 目录

```text
.
├─ README.md
├─ LICENSE
├─ requirements.txt
├─ paper/
│  ├─ paper.md                  # 论文全文（Markdown，匿名版，适配双盲评审）
│  └─ fig1_architecture.png     # 图 1：三层架构与复用边界
├─ code/
│  ├─ es_bench.py               # 五类查询延迟分布（n=30）
│  ├─ baseline_bench.py         # 递归遍历基线 + 进程启动固定开销
│  ├─ collect_lists.py          # 导出索引侧 / 遍历侧路径列表
│  ├─ diff_analysis.py          # 两侧差集与目录聚合
│  └─ draw_fig1.py              # 图 1 生成
├─ results/
│  ├─ es_bench.json             # 查询延迟原始聚合结果
│  └─ es_h_drive.json           # 测试卷限定路径查询结果
└─ docs/
   ├─ experiment-summary.md          # 测试环境、索引规模、内存、基线对比
   └─ supplementary-measurements.md  # 引号语义、命名管道、错误码 8、差集根因
```

## 复现

前置条件：

1. 安装 Everything 1.5.x，并确认索引进程正在运行（本机测试版本 1.5.0.1423b）；
2. 自行获取对应版本的 ES 命令行工具（本仓库不包含二进制；测试版本 1.1.0.38）；
3. 安装 Python 依赖：

```bash
pip install -r requirements.txt
```

4. 设置环境变量 `ES_EXE` 指向 `es.exe`（或用 `--es` 逐个脚本指定）。

查询延迟与索引规模：

```bash
python code/es_bench.py --es "$ES_EXE" --out results/es_bench.json --n 30
```

递归遍历基线（指定自己的卷根）：

```bash
python code/baseline_bench.py --es "$ES_EXE" --out results/baseline_bench.json <volume>/
```

两侧差集：

```bash
python code/collect_lists.py --es "$ES_EXE" --volume <volume>/ --pattern "*.md" \
    --es-out list_es.txt --walk-out list_walk.txt
python code/diff_analysis.py --es-list list_es.txt --walk-list list_walk.txt
```

图 1：

```bash
python code/draw_fig1.py --out fig1_architecture.png
# 非 Windows 平台请指定中文字体：--font-bold / --font-reg
```

说明：`collect_lists.py` 产出的路径列表包含本机绝对路径，**仅用于本地复核，不要提交到仓库**（已在 `.gitignore` 中排除）。读者若要复核差集结论，请用自己的卷重新生成。

## 已知边界

- 索引层与命令行接口均为第三方成熟工具，本文未修改其实现，工作集中在接入层与实测；
- 未测量命名管道与本地 HTTP 的延迟差异，也未测量常驻连接可压缩到的延迟下界；
- 100 条查询的最大值 311.27 ms 未定位成因（样本未记录时间戳），论文按"推测为调度抖动，未验证"处理；
- 测试期间未关闭杀毒实时扫描、未暂停索引自动更新，属常规桌面负载条件；
- token 数按 3.5 字符/token 折算，仅用于量级比较，非精确计量。

## 引用

论文投稿中。正式发表后补充 DOI 与 BibTeX。

## 许可

- 代码：MIT，见 `LICENSE`
- 论文文本：CC BY 4.0（如期刊版权协议另有要求，以期刊协议为准）

## 第三方

Everything 与 ES 为第三方工具，版权归其作者所有，本仓库不包含其二进制文件。测试版本：Everything 1.5.0.1423b、ES 1.1.0.38。
