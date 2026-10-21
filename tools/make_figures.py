#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成内联 SVG 图表，输出到 book/figures/*.svg

为什么要用脚本画图：
    手写的坐标一定会算错。图上的每个点都必须由公式生成，
    和 tools/calc.py 用同一套数字，避免"图跟正文打架"。

用法:
    python tools/make_figures.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "book" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 680, 380          # viewBox 尺寸
PAD_L, PAD_R, PAD_T, PAD_B = 58, 22, 34, 46
PLOT_W = W - PAD_L - PAD_R
PLOT_H = H - PAD_T - PAD_B

# 颜色（浅色主题，与 index.html 保持一致）
C_FG = "#1f2328"
C_MUTED = "#5b6570"
C_LINE = "#e3e0d8"
C_ACCENT = "#b45309"     # 橙：复利
C_BLUE = "#2563eb"       # 蓝：线性
C_GREEN = "#166534"
C_RED = "#b91c1c"
C_BG = "#ffffff"


def svg_open(title: str) -> list:
    return [
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="{title}" class="fig">',
        f'<rect width="{W}" height="{H}" fill="{C_BG}"/>',
    ]


def scale(v, vmin, vmax, px0, px1):
    """把数值 v 映射到像素区间"""
    if vmax == vmin:
        return px0
    return px0 + (v - vmin) / (vmax - vmin) * (px1 - px0)


def axis_labels(parts, xmin, xmax, ymin, ymax, xticks, yticks, xfmt, yfmt, xlabel, ylabel):
    """画坐标轴 + 刻度。y 轴向下翻转。"""
    out = []
    x0, x1 = PAD_L, PAD_L + PLOT_W
    y0, y1 = PAD_T + PLOT_H, PAD_T          # y0 底部, y1 顶部

    # 网格与刻度
    for t in yticks:
        py = scale(t, ymin, ymax, y0, y1)
        out.append(f'<line x1="{x0}" y1="{py:.1f}" x2="{x1}" y2="{py:.1f}" '
                   f'stroke="{C_LINE}" stroke-width="1"/>')
        out.append(f'<text x="{x0 - 8}" y="{py + 4:.1f}" text-anchor="end" '
                   f'font-size="11" fill="{C_MUTED}">{yfmt(t)}</text>')
    for t in xticks:
        px = scale(t, xmin, xmax, x0, x1)
        out.append(f'<line x1="{px:.1f}" y1="{y0}" x2="{px:.1f}" y2="{y0 + 4}" '
                   f'stroke="{C_MUTED}" stroke-width="1"/>')
        out.append(f'<text x="{px:.1f}" y="{y0 + 18}" text-anchor="middle" '
                   f'font-size="11" fill="{C_MUTED}">{xfmt(t)}</text>')

    # 轴
    out.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{C_FG}" stroke-width="1.4"/>')
    out.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="{C_FG}" stroke-width="1.4"/>')
    out.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{H - 8}" text-anchor="middle" '
               f'font-size="12" fill="{C_MUTED}">{xlabel}</text>')
    out.append(f'<text x="14" y="{(y0 + y1) / 2:.0f}" text-anchor="middle" font-size="12" '
               f'fill="{C_MUTED}" transform="rotate(-90 14 {(y0 + y1) / 2:.0f})">{ylabel}</text>')
    return out


def path_from(points, xmin, xmax, ymin, ymax, color, width=2.4, dash=None):
    x0, x1 = PAD_L, PAD_L + PLOT_W
    y0, y1 = PAD_T + PLOT_H, PAD_T
    d = " ".join(
        ("M" if i == 0 else "L") + f"{scale(x, xmin, xmax, x0, x1):.1f},{scale(y, ymin, ymax, y0, y1):.1f}"
        for i, (x, y) in enumerate(points)
    )
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" ' \
           f'stroke-linejoin="round" stroke-linecap="round"{da}/>'


def legend(items, x=None, y=20):
    """items: [(color, text, dash)]"""
    x = PAD_L + 8 if x is None else x
    out = []
    for i, (color, text, dash) in enumerate(items):
        yy = y + i * 18
        da = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<line x1="{x}" y1="{yy}" x2="{x + 22}" y2="{yy}" '
                   f'stroke="{color}" stroke-width="2.4"{da}/>')
        out.append(f'<text x="{x + 28}" y="{yy + 4}" font-size="11.5" fill="{C_FG}">{text}</text>')
    return out


# ---------------------------------------------------------------- 图 1
def fig1():
    """线性 vs 复利：分水岭在第 15~20 年"""
    years = list(range(0, 41))
    lin = [(y, 100 + 10 * y) for y in years]
    comp = [(y, 100 * 1.10 ** y) for y in years]

    ymax = 4600
    yticks = [0, 1000, 2000, 3000, 4000]
    xticks = [0, 5, 10, 15, 20, 25, 30, 35, 40]

    o = svg_open("线性与复利的分水岭")
    o.append(f'<text x="{PAD_L}" y="20" font-size="13.5" font-weight="700" fill="{C_FG}">'
             f'线性 vs 复利：起点都是 100</text>')
    o += axis_labels(None, 0, 40, 0, ymax, xticks, yticks,
                     lambda t: f"{t}", lambda t: f"{t}", "年", "倍数（起点=100）")
    o += legend([(C_BLUE, "线性：每年 +10", "6 4"), (C_ACCENT, "复利：每年 ×1.10", None)], y=44)
    o.append(path_from(lin, 0, 40, 0, ymax, C_BLUE, 2.2, dash="6 4"))
    o.append(path_from(comp, 0, 40, 0, ymax, C_ACCENT, 2.8))

    # 分水岭标注
    x0, x1 = PAD_L, PAD_L + PLOT_W
    y0, y1 = PAD_T + PLOT_H, PAD_T
    for yr, label in [(15, "第15年 1.67×"), (30, "第30年 4.36×")]:
        px = scale(yr, 0, 40, x0, x1)
        o.append(f'<line x1="{px:.1f}" y1="{scale(100, 0, ymax, y0, y1):.1f}" '
                 f'x2="{px:.1f}" y2="{y1 + 10}" stroke="{C_MUTED}" stroke-width="1" '
                 f'stroke-dasharray="3 3"/>')
        o.append(f'<circle cx="{px:.1f}" cy="{scale(100 * 1.1 ** yr, 0, ymax, y0, y1):.1f}" '
                 f'r="4" fill="{C_ACCENT}"/>')
        o.append(f'<text x="{px + 6:.1f}" y="{scale(100 * 1.1 ** yr, 0, ymax, y0, y1) - 8:.1f}" '
                 f'font-size="11" fill="{C_ACCENT}" font-weight="700">{label}</text>')
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- 图 2
def fig2():
    """亏损回本的非对称：需要的涨幅"""
    pts = []
    losses = [i / 100 for i in range(0, 91, 2)]
    for L in losses:
        need = (1 / (1 - L) - 1) * 100 if L < 1 else None
        if need is not None:
            pts.append((L * 100, min(need, 700)))
    return _generic(
        "亏损回本的非对称：跌多少，需要涨多少才回来",
        pts, 0, 90, 0, 700,
        [0, 15, 30, 45, 60, 75, 90], [0, 200, 400, 600],
        "累计跌幅（%）", "回本所需涨幅（%）",
        C_RED,
        annot=[(50, 100, "−50% → +100%"), (70, 233.3, "−70% → +233%"), (90, 700, "−90% → +900%")],
    )


# ---------------------------------------------------------------- 图 3
def fig3():
    """费率对三十年复利的侵蚀"""
    fees = [i / 10 for i in range(0, 31)]
    pts = [(f, (0.08 - f / 100) ** 30) for f in fees]
    return _generic(
        "费率对 30 年复利的侵蚀（毛年化 8%）",
        pts, 0, 3, 0, 11,
        [0, 0.5, 1, 1.5, 2, 2.5, 3], [0, 2, 4, 6, 8, 10],
        "年费率（%）", "30 年终值（倍）",
        C_ACCENT,
        annot=[(1.0, 7.61, "1% → 7.61倍（−24%）"), (3.0, 4.32, "3% → 4.32倍（−57%）")],
    )


# ---------------------------------------------------------------- 图 4
def fig4():
    """定投：25 岁 vs 35 岁开始"""
    r = 0.08

    def fv(months):
        return 2000 * (((1 + r / 12) ** months - 1) / (r / 12))

    pts_a = [(m / 12 + 25, fv(m) / 10000) for m in range(0, 421, 6)]
    pts_b = [(m / 12 + 35, fv(m) / 10000) for m in range(0, 301, 6)]
    return _generic_multi(
        "每月投 2,000 元，年化 8%：晚十年开始的差距",
        [(pts_a, C_ACCENT, "25 岁开始"), (pts_b, C_BLUE, "35 岁开始")],
        25, 60, 0, 500,
        list(range(25, 61, 5)), [0, 100, 200, 300, 400, 500],
        "年龄", "终值（万元）",
        annot=[(60, 458.8, "458.8 万"), (60, 190.2, "190.2 万")],
    )


def _generic(title, pts, xmin, xmax, ymin, ymax, xt, yt, xl, yl, color, annot=None):
    return _generic_multi(title, [(pts, color, None)], xmin, xmax, ymin, ymax,
                          xt, yt, xl, yl, annot)


def _generic_multi(title, series, xmin, xmax, ymin, ymax, xt, yt, xl, yl, annot=None):
    o = svg_open(title)
    o.append(f'<text x="{PAD_L}" y="20" font-size="13.5" font-weight="700" fill="{C_FG}">{title}</text>')
    o += axis_labels(None, xmin, xmax, ymin, ymax, xt, yt,
                     lambda t: f"{t:g}", lambda t: f"{t:g}", xl, yl)

    named = [(s, c, n) for s, c, n in series if n]
    if named:
        o += legend([(c, n, None) for _, c, n in named], y=44)

    x0, x1 = PAD_L, PAD_L + PLOT_W
    y0, y1 = PAD_T + PLOT_H, PAD_T
    for pts, color, _ in series:
        o.append(path_from(pts, xmin, xmax, ymin, ymax, color, 2.8))

    if annot:
        for ax, ay, txt in annot:
            px = scale(ax, xmin, xmax, x0, x1)
            py = scale(ay, ymin, ymax, y0, y1)
            o.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{C_ACCENT}"/>')
            o.append(f'<text x="{px - 8:.1f}" y="{py - 10:.1f}" text-anchor="end" '
                     f'font-size="11" font-weight="700" fill="{C_ACCENT}">{txt}</text>')
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- 图 5
def fig5():
    """信用卡最低还款：余额几乎不降"""
    bal, apr = 10000.0, 0.18
    pts = [(0, bal / 1000)]
    for m in range(1, 61):
        bal = bal * (1 + apr / 12)
        pay = max(bal * 0.02, 50)
        bal -= pay
        if m % 2 == 0:
            pts.append((m / 12, bal / 1000))
    return _generic(
        "欠 1 万元、年化 18%、只还最低 2%：五年余额曲线",
        pts, 0, 5, 0, 12,
        [0, 1, 2, 3, 4, 5], [0, 3, 6, 9, 12],
        "年", "剩余欠款（千元）",
        C_RED,
        annot=[(5, 7.27, "5年后仍欠 7,270 元")],
    )


# ---------------------------------------------------------------- 图 6
def fig6():
    """LTCM：四个好年份，第五年抹平。累计净值，起点=1。

    数字来源：正文 2.2 节表格（净回报 28.5 / 42.8 / 40.8 / 17.1），
    1998 年按"五周蒸发约 90%"记为 ×0.10。图中每年末的累计值由这里连乘算出。
    """
    rates = [0.285, 0.428, 0.408, 0.171]
    cum = []
    v = 1.0
    for r in rates:
        v *= 1 + r
        cum.append(v)
    cum_98 = cum[-1] * 0.10
    assert abs(cum[-1] - 3.0254) < 0.001, cum[-1]
    assert abs(cum_98 - 0.3025) < 0.001, cum_98

    years = ["1994", "1995", "1996", "1997", "1998"]
    vals = cum + [cum_98]
    ymax = 3.6
    xt = list(range(5))
    yt = [0, 1, 2, 3]

    o = svg_open("LTCM 累计净值")
    o.append(f'<text x="{PAD_L}" y="20" font-size="13.5" font-weight="700" fill="{C_FG}">'
             f"LTCM：四个好年份，第五年抹平（起点 = 1）</text>")
    o += axis_labels(None, -0.5, 4.5, 0, ymax, xt, yt,
                     lambda t: years[int(t)], lambda t: f"{t}",
                     "年份", "累计净值（倍）")

    x0, x1 = PAD_L, PAD_L + PLOT_W
    y0, y1 = PAD_T + PLOT_H, PAD_T
    bw = PLOT_W / 5 * 0.52

    # 起点 1.0 参考线
    py1 = scale(1.0, 0, ymax, y0, y1)
    o.append(f'<line x1="{x0}" y1="{py1:.1f}" x2="{x1}" y2="{py1:.1f}" '
             f'stroke="{C_MUTED}" stroke-width="1" stroke-dasharray="3 3"/>')

    for i, val in enumerate(vals):
        px = scale(i, -0.5, 4.5, x0, x1)
        pyv = scale(val, 0, ymax, y0, y1)
        color = C_RED if i == 4 else C_ACCENT
        o.append(f'<rect x="{px - bw / 2:.1f}" y="{pyv:.1f}" width="{bw:.1f}" '
                 f'height="{y0 - pyv:.1f}" fill="{color}" opacity="0.85"/>')

    # 连线（年初 1.0 → 各年末）
    pts = [(-0.5, 1.0)] + [(i, v) for i, v in enumerate(vals)]
    o.append(path_from(pts, -0.5, 4.5, 0, ymax, C_FG, 1.6, dash="4 3"))

    # 标注
    px3 = scale(3, -0.5, 4.5, x0, x1)
    py3 = scale(vals[3], 0, ymax, y0, y1)
    o.append(f'<text x="{px3:.1f}" y="{py3 - 10:.1f}" text-anchor="middle" '
             f'font-size="11.5" font-weight="700" fill="{C_ACCENT}">四年 3.03 倍</text>')
    px4 = scale(4, -0.5, 4.5, x0, x1)
    py4 = scale(vals[4], 0, ymax, y0, y1)
    o.append(f'<text x="{px4 - 6:.1f}" y="{py4 - 10:.1f}" text-anchor="end" '
             f'font-size="11.5" font-weight="700" fill="{C_RED}">1998：−90% → 0.30</text>')
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- 图 7
def fig7():
    """利弗莫尔一生的时间线（1877–1940）。

    只画书里有据可查的事件，不画编造的财富曲线：
    1907 / 1908 / 1929 / 1934 / 1940 的日期与数字都来自正文 4.5 节。
    """
    o = svg_open("利弗莫尔时间线")
    o.append(f'<text x="{PAD_L}" y="20" font-size="13.5" font-weight="700" fill="{C_FG}">'
             f"杰西·利弗莫尔（1877–1940）：同一个人，两次巅峰，四次破产</text>")

    x0, x1 = PAD_L, PAD_L + PLOT_W
    y_mid = PAD_T + PLOT_H / 2
    XA, XB = 1875, 1943

    # 主轴
    o.append(f'<path d="M{scale(1877, XA, XB, x0, x1):.1f},{y_mid:.1f} '
             f'L{scale(1940, XA, XB, x0, x1):.1f},{y_mid:.1f}" '
             f'stroke="{C_FG}" stroke-width="1.6" stroke-linecap="round"/>')

    # 年份刻度
    for yr in range(1880, 1941, 10):
        px = scale(yr, XA, XB, x0, x1)
        o.append(f'<line x1="{px:.1f}" y1="{y_mid:.1f}" x2="{px:.1f}" y2="{y_mid + 4:.1f}" '
                 f'stroke="{C_MUTED}" stroke-width="1"/>')
        o.append(f'<text x="{px:.1f}" y="{y_mid + 18:.1f}" text-anchor="middle" '
                 f'font-size="10.5" fill="{C_MUTED}">{yr}</text>')
    o.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{H - 8}" text-anchor="middle" '
             f'font-size="12" fill="{C_MUTED}">年份</text>')

    # 事件：(年, 颜色, 上/下, [行1, 行2])
    events = [
        (1877, C_FG,    "up",   ["出生"]),
        (1907, C_GREEN, "up",   ["做空：单日赚", "约 300 万美元"]),
        (1908, C_RED,   "down", ["第一次破产"]),
        (1929, C_GREEN, "up",   ["做空获利约 1 亿美元", "（此数有争议）"]),
        (1934, C_RED,   "down", ["第四次破产", "资产 18.49 万 / 负债 225.9 万"]),
        (1940, C_FG,    "up",   ["生命结束"]),
    ]
    for yr, color, side, lines in events:
        px = scale(yr, XA, XB, x0, x1)
        o.append(f'<circle cx="{px:.1f}" cy="{y_mid:.1f}" r="4.5" fill="{color}"/>')
        stem_top = y_mid - 58 if side == "up" else y_mid + 58
        o.append(f'<line x1="{px:.1f}" y1="{y_mid - 8 if side == "up" else y_mid + 8:.1f}" '
                 f'x2="{px:.1f}" y2="{stem_top:.1f}" stroke="{color}" stroke-width="1" '
                 f'stroke-dasharray="3 3"/>')
        # 文字锚点：靠右的事件向左展开，避免出画布
        anchor = "end" if yr >= 1929 else "start"
        tx = px + (6 if anchor == "start" else -6)
        for k, line in enumerate(lines):
            ty = (stem_top - 14 + k * 15) if side == "up" else (stem_top + 10 + k * 15)
            o.append(f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anchor}" '
                     f'font-size="11" font-weight="700" fill="{color}">{line}</text>')

    # 图例
    o += legend([(C_GREEN, "做对的年份", None), (C_RED, "归零的年份", None)],
                x=x1 - 150, y=PAD_T + 6)
    o.append("</svg>")
    return "\n".join(o)


# ---------------------------------------------------------------- 图 8
def fig8():
    """标普 500 的 152 个年度收益率分布（真实数据直方图）。

    数据同 market_stats.py 第 4 节：直接 import 它的 load/total_return_series，
    保证图上的每一个柱子和正文表格是同一套数字。
    """
    import collections
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "tools"))
    from market_stats import END, START, load, total_return_series

    rows = [r for r in load() if START <= r["date"] <= END]
    yearly = []
    for y in range(int(rows[0]["date"][:4]), int(rows[-1]["date"][:4]) + 1):
        sub = [r for r in rows if r["date"][:4] == str(y)]
        if len(sub) < 12:
            continue
        si = total_return_series(sub)
        yearly.append(si[-1] / si[0] - 1)

    assert len(yearly) == 152, len(yearly)
    bins = collections.Counter()
    for v in yearly:
        lo = int(v * 100 // 5) * 5
        bins[max(-50, min(45, lo))] += 1
    n_neg = sum(c for lo, c in bins.items() if lo < 0)
    assert n_neg == 43, n_neg

    xmin, xmax, ymax = -50, 50, 25
    o = svg_open("标普 500 年度收益率分布")
    o.append(f'<text x="{PAD_L}" y="20" font-size="13.5" font-weight="700" fill="{C_FG}">'
             f"标普 500 的 152 个年度：收益率分布（1871–2023，含股息）</text>")
    o += axis_labels(None, xmin, xmax, 0, ymax,
                     [-50, -25, 0, 25, 50], [0, 5, 10, 15, 20],
                     lambda t: f"{t}", lambda t: f"{t}",
                     "年度收益率（%）", "年份数")

    x0, x1 = PAD_L, PAD_L + PLOT_W
    y0, y1 = PAD_T + PLOT_H, PAD_T

    # 柱：涨红跌绿（中国市场惯例）
    step = []
    for lo in range(-50, 50, 5):
        c = bins.get(lo, 0)
        px = scale(lo, xmin, xmax, x0, x1)
        pw = scale(lo + 5, xmin, xmax, x0, x1) - px
        pyv = scale(c, 0, ymax, y0, y1)
        color = C_GREEN if lo < 0 else C_RED
        if c:
            o.append(f'<rect x="{px:.1f}" y="{pyv:.1f}" width="{pw:.1f}" '
                     f'height="{y0 - pyv:.1f}" fill="{color}" opacity="0.8"/>')
        step.append((px, pyv if c else y0))
        step.append((px + pw, pyv if c else y0))
    # 阶梯轮廓
    d = "M" + f"{step[0][0]:.1f},{y0:.1f} " + " ".join(
        f"L{x:.1f},{y:.1f}" for x, y in step)
    o.append(f'<path d="{d}" fill="none" stroke="{C_MUTED}" stroke-width="1"/>')

    # 长期年化参考线
    cagr_v = 9.17
    pxc = scale(cagr_v, xmin, xmax, x0, x1)
    o.append(f'<line x1="{pxc:.1f}" y1="{y1}" x2="{pxc:.1f}" y2="{y0}" '
             f'stroke="{C_FG}" stroke-width="1.4" stroke-dasharray="5 4"/>')
    o.append(f'<text x="{pxc + 6:.1f}" y="{y1 + 14:.1f}" font-size="11" '
             f'font-weight="700" fill="{C_FG}">长期年化 9.17%</text>')

    # 标注
    top_lo = max(bins, key=lambda k: bins[k])
    pxm = scale(top_lo + 2.5, xmin, xmax, x0, x1)
    pym = scale(bins[top_lo], 0, ymax, y0, y1)
    o.append(f'<text x="{pxm:.1f}" y="{pym - 8:.1f}" text-anchor="middle" '
             f'font-size="11" font-weight="700" fill="{C_RED}">'
             f"{top_lo}%~{top_lo + 5}%：{bins[top_lo]} 年（最多）</text>")
    o.append(f'<text x="{x0 + 8:.1f}" y="{y1 + 26:.1f}" font-size="11" '
             f'font-weight="700" fill="{C_GREEN}">亏损年 {n_neg} 个（28.3%）；8%~12% 只有 14 年</text>')
    o.append("</svg>")
    return "\n".join(o)


def write_preview(figs: dict):
    """生成 book/figures/_preview.html。

    以前这个文件是手工维护的清单，加图后忘了更新（一直停在 5 张）——
    又一次"同一份清单两个出处"。改为从 figs 字典生成，单一出处。
    """
    items = "\n".join(
        f'  ["{name.removesuffix(".svg")}", "{name}"],' for name in figs
    )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>图表预览（由 make_figures.py 生成，勿手改）</title>
<style>
body{{margin:0;padding:24px;background:#fbfaf7;font:15px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:#1f2328}}
h2{{font-size:15px;margin:28px 0 8px;color:#5b6570;font-weight:600}}
.card{{background:#fff;border:1px solid #e3e0d8;border-radius:10px;padding:8px;max-width:720px}}
svg{{width:100%;height:auto;display:block}}
</style>
</head>
<body>
<div id="host"></div>
<script>
const figs = [
{items}
];
const host = document.getElementById('host');
figs.forEach(([title, file]) => {{
  const h = document.createElement('h2'); h.textContent = title; host.appendChild(h);
  const d = document.createElement('div'); d.className = 'card'; host.appendChild(d);
  fetch(file).then(r => r.text()).then(t => {{ d.innerHTML = t; }})
    .catch(e => {{ d.textContent = '加载失败: ' + e; }});
}});
</script>
</body>
</html>
"""
    p = OUT / "_preview.html"
    p.write_text(html, encoding="utf-8")
    print(f"生成 {p.relative_to(ROOT)}  ({len(html) / 1024:.1f} KB)")


def main():
    figs = {
        "fig1-linear-vs-compound.svg": fig1(),
        "fig2-loss-recovery.svg": fig2(),
        "fig3-fee-erosion.svg": fig3(),
        "fig4-start-early.svg": fig4(),
        "fig5-min-payment.svg": fig5(),
        "fig6-ltcm.svg": fig6(),
        "fig7-livermore.svg": fig7(),
        "fig8-annual-distribution.svg": fig8(),
    }
    for name, content in figs.items():
        p = OUT / name
        p.write_text(content, encoding="utf-8")
        print(f"生成 {p.relative_to(ROOT)}  ({len(content) / 1024:.1f} KB)")
    write_preview(figs)


if __name__ == "__main__":
    main()
