# -*- coding: utf-8 -*-
"""
生成论文图 1：三层架构、调用路径与复用边界
300 dpi，灰度可辨（适配期刊黑白印刷），输出 PNG

用法：
    python draw_fig1.py --out fig1_architecture.png
    python draw_fig1.py --font-bold /path/to/simhei.ttf --font-reg /path/to/simsun.ttc

默认字体指向 Windows 自带黑体/宋体；其他平台请用 --font-bold/--font-reg 指定中文字体，
否则中文会渲染成方块。
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser(description="Draw Figure 1 (three-layer architecture).")
ap.add_argument("--font-bold",
                default=os.environ.get("FIG_FONT_BOLD", r"C:\Windows\Fonts\simhei.ttf"))
ap.add_argument("--font-reg",
                default=os.environ.get("FIG_FONT_REG", r"C:\Windows\Fonts\simsun.ttc"))
ap.add_argument("--out", default="fig1_architecture.png", help="Output PNG path")
args = ap.parse_args()

DPI = 300
W_CM, H_CM = 14.0, 9.0
W = int(W_CM / 2.54 * DPI)
H = int(H_CM / 2.54 * DPI)

FONT_BOLD = args.font_bold
FONT_REG = args.font_reg
OUT = args.out


def f(path, pt):
    return ImageFont.truetype(path, int(pt / 72 * DPI))


f_title = f(FONT_BOLD, 9)
f_body = f(FONT_REG, 8)
f_note = f(FONT_BOLD, 7.5)

img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

BLACK = (0, 0, 0)
FILL = (242, 242, 242)
LW = 3


def box(x0, y0, x1, y1, fill=FILL):
    d.rectangle([x0, y0, x1, y1], fill=fill, outline=BLACK, width=LW)


def ctext(cx, y, s, font, fill=BLACK):
    bb = d.textbbox((0, 0), s, font=font)
    d.text((cx - (bb[2] - bb[0]) / 2, y), s, font=font, fill=fill)
    return bb[3] - bb[1]


def ltext(x, y, s, font, fill=BLACK):
    d.text((x, y), s, font=font, fill=fill)
    bb = d.textbbox((0, 0), s, font=font)
    return bb[3] - bb[1]


def arrow(cx, y0, y1, label):
    """向下箭头 + 右侧标注"""
    d.line([cx, y0, cx, y1 - 18], fill=BLACK, width=LW)
    d.polygon([(cx - 13, y1 - 20), (cx + 13, y1 - 20), (cx, y1)], fill=BLACK)
    bb = d.textbbox((0, 0), label, font=f_note)
    hh = bb[3] - bb[1]
    d.text((cx + 30, (y0 + y1) / 2 - hh / 2), label, font=f_note, fill=BLACK)


# ---------- 布局 ----------
CX = W // 2
BX0, BX1 = 200, W - 200
bw = BX1 - BX0
LX = BX0 + 56          # 框内文字左边界
GAP = 104              # 框间距（容纳箭头与标注）

# 框1 Agent
y1_0, y1_1 = 34, 224
box(BX0, y1_0, BX1, y1_1)
ctext(CX, y1_0 + 32, "Agent（大语言模型推理循环）", f_title)
ctext(CX, y1_0 + 32 + 54, '工具调用：es.exe -n 20 "<pattern>"', f_body)

# 箭头1
arrow(CX, y1_1, y1_1 + GAP, "① 进程创建 + 参数传递")

# 框2 接口层
y2_0 = y1_1 + GAP
y2_1 = y2_0 + 224
box(BX0, y2_0, BX1, y2_1)
ctext(CX, y2_0 + 26, "接口层：命令行封装（ES 1.1.0.38，262,312 B）", f_title)
ltext(LX, y2_0 + 26 + 56, "复用：参数解析、管道客户端、结果输出", f_body)
ltext(LX, y2_0 + 26 + 56 + 44, "自研：编码转换、引号语义适配、默认限条", f_body)

# 箭头2
arrow(CX, y2_1, y2_1 + GAP, "② 命名管道 \\Everything IPC")

# 框3 索引层
y3_0 = y2_1 + GAP
y3_1 = H - 24
box(BX0, y3_0, BX1, y3_1)
ctext(CX, y3_0 + 24, "索引层：常驻索引进程（Everything 1.5.0.1423b）", f_title)
rows = [
    "· 建索引：读取 NTFS MFT",
    "· 增量更新：订阅 USN Journal",
    "· 存放：常驻内存（私有内存 488.2 MB）",
    "· 查询：内存匹配 + 排序，O(1) 次磁盘访问",
    "—— 以上全部复用，本文未修改其实现",
]
yy = y3_0 + 24 + 54
for r in rows:
    ltext(LX, yy, r, f_body)
    yy += 44

img.save(OUT, dpi=(DPI, DPI))
print("saved:", OUT, img.size, "px =", W_CM, "x", H_CM, "cm @", DPI, "dpi")
