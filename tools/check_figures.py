#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验 book/figures/*.svg 的几何正确性。

为什么需要：
    图是脚本生成的，但"脚本没报错"不等于"图是对的"。
    真实会出的事故是：坐标算成了 NaN、点跑到画布外面、
    折线穿出绘图区、标注文字盖住曲线。这些肉眼在缩小状态下看不出来。

这里只做可机检的部分，审美问题仍然要人看。

用法:
    python tools/check_figures.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "book" / "figures"

# 与 make_figures.py 保持一致
W, H = 680, 380
PAD_L, PAD_R, PAD_T, PAD_B = 58, 22, 34, 46
X_MIN, X_MAX = PAD_L, PAD_L + (W - PAD_L - PAD_R)
Y_MIN, Y_MAX = PAD_T, PAD_T + (H - PAD_T - PAD_B)

NUM = r"-?\d+(?:\.\d+)?"


def main():
    files = sorted(FIG.glob("*.svg"))
    if not files:
        sys.exit("没有找到 SVG，先跑 tools/make_figures.py")

    total_problems = 0
    print(f"检查 {len(files)} 个 SVG（画布 {W}x{H}，绘图区 x[{X_MIN},{X_MAX}] y[{Y_MIN},{Y_MAX}]）")
    print()

    for f in files:
        s = f.read_text(encoding="utf-8")
        probs = []

        # 1. NaN / inf
        for bad in ("NaN", "nan", "inf", "Infinity"):
            if re.search(rf"[=\s]{bad}[\s\"]", s):
                probs.append(f"出现 {bad}")

        # 2. path 坐标范围
        pts = re.findall(rf"([ML])({NUM}),({NUM})", s)
        if not pts:
            probs.append("没有找到路径点")
        oob = []
        for _, px, py in pts:
            x, y = float(px), float(py)
            if not (X_MIN - 2 <= x <= X_MAX + 2) or not (Y_MIN - 2 <= y <= Y_MAX + 2):
                oob.append((x, y))
        if oob:
            probs.append(f"{len(oob)} 个点越界，例如 {oob[0]}")

        # 3. 点在画布内
        cbad = [
            (float(cx), float(cy))
            for cx, cy in re.findall(rf'<circle cx="({NUM})" cy="({NUM})"', s)
            if not (0 <= float(cx) <= W and 0 <= float(cy) <= H)
        ]
        if cbad:
            probs.append(f"{len(cbad)} 个圆点出画布")

        # 4. 文字估计越界（粗略：按字号 * 字数 * 0.55 估宽）
        for m in re.finditer(
            rf'<text x="({NUM})" y="({NUM})"([^>]*)>(.*?)</text>', s
        ):
            x, y, attrs, txt = float(m.group(1)), float(m.group(2)), m.group(3), m.group(4)
            # 旋转文字（轴标题）按旋转后的包围盒算，跳过横向估算
            if "rotate(" in attrs:
                continue
            fs_m = re.search(rf'font-size="({NUM})"', attrs)
            if not fs_m:
                continue
            fs = float(fs_m.group(1))
            txt = re.sub(r"<[^>]+>", "", txt)
            # 中文按 1.0 倍宽，ASCII 按 0.55 倍
            width = sum(1.0 if ord(ch) > 0x2E80 else 0.55 for ch in txt) * fs
            if 'text-anchor="end"' in attrs:
                left, right = x - width, x
            elif 'text-anchor="middle"' in attrs:
                left, right = x - width / 2, x + width / 2
            else:
                left, right = x, x + width
            if right > W + 4 or left < -4 or y > H + 4 or y < 6:
                probs.append(f"文字越界: {txt[:14]!r} x=[{left:.0f},{right:.0f}] y={y:.0f}")

        # 5. 必须有 data 系列（至少 2 个点）
        if len(pts) < 2:
            probs.append("路径点少于 2 个")

        status = "OK" if not probs else "!!"
        print(f"[{status}] {f.name}  点={len(pts)}")
        for p in probs:
            print(f"      - {p}")
        total_problems += len(probs)

    print()
    if total_problems:
        print(f"[!] 共 {total_problems} 个问题")
        return 1
    print("[OK] 所有图几何检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
