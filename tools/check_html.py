#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验 index.html 的完整性：
    1. 页内链接（#xxx）是否都能落到真实 id 上
    2. 是否还有未嵌入的 <img>（应为 0，全部是内联 SVG）
    3. 算式卡数量与编号
    4. 有没有 "figure" 里套了空 svg

用法:
    python tools/check_html.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"


def main():
    if not HTML.exists():
        sys.exit("找不到 index.html，先跑 tools/build.py")
    h = HTML.read_text(encoding="utf-8")

    ids = set(re.findall(r'\sid="([^"]+)"', h))
    hrefs = re.findall(r'href="#([^"]+)"', h)
    bad = [x for x in hrefs if x not in ids]

    print(f"页面 id 数量      : {len(ids)}")
    print(f"页内链接数量      : {len(hrefs)}")
    print(f"失效链接          : {len(bad)}")
    for x in bad[:20]:
        print(f"  #{x}")

    imgs = re.findall(r"<img\s", h)
    svgs = re.findall(r"<svg", h)
    figs = re.findall(r'<figure class="fig"', h)
    print(f"内联 SVG          : {len(svgs)}")
    print(f"未内联 <img>      : {len(imgs)}  (应为 0)")
    print(f"figure 容器       : {len(figs)}")

    empty = re.findall(r'<figcaption></figcaption>', h)
    print(f"空图注            : {len(empty)}")

    cards = re.findall(r'<div class="formula" id="calc-(\d+)"', h)
    nums = [int(x) for x in cards]
    print(f"算式卡            : {len(nums)}  编号={nums}")

    verdicts = re.findall(r'<blockquote class="verdict">', h)
    print(f"本章结论块        : {len(verdicts)}")

    problems = []
    if bad:
        problems.append(f"{len(bad)} 个失效链接")
    if imgs:
        problems.append(f"{len(imgs)} 个未内联图片")
    if nums != list(range(1, len(nums) + 1)):
        problems.append("算式编号不连续")

    if problems:
        print("\n[!] " + "；".join(problems))
        return 1
    print("\n[OK] HTML 结构完整")
    return 0


if __name__ == "__main__":
    sys.exit(main())
