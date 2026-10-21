#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键跑完所有校验。

这本书的一个原则是：凡是能被机器检查的数字，都不应该靠人眼。
所以把 calc / stats / anchors / figures / html 串起来，一条命令全跑。

用法:
    python tools/verify.py
返回码 0 表示全部通过。
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

STEPS = [
    ("算式与互检", ["tools/calc.py"]),
    ("真实数据统计", ["tools/market_stats.py"]),
    ("样本充分性", ["tools/sample_check.py"]),
    ("结构与编号", ["tools/stats.py"]),
    ("正文指涉", ["tools/check_refs.py"]),
    ("Markdown 锚点", ["tools/check_anchors.py"]),
    ("图表几何", ["tools/check_figures.py"]),
    ("HTML 结构", ["tools/check_html.py"]),
]


def main():
    # build 必须先跑，保证 html 是最新的
    print("=" * 60)
    print("重建 index.html")
    print("=" * 60)
    r = subprocess.run([PY, "tools/build.py"], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0:
        print("[!] build 失败")
        return 1

    failed = []
    for name, cmd in STEPS:
        print()
        print("=" * 60)
        print(f"检查：{name}  ({' '.join(cmd)})")
        print("=" * 60)
        r = subprocess.run([PY] + cmd, cwd=ROOT, capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        # 只回显尾部，避免刷屏
        lines = out.strip().split("\n")
        print("\n".join(lines[-16:]))
        if r.returncode != 0:
            failed.append(name)

    print()
    print("=" * 60)
    if failed:
        print(f"[!] 未通过：{', '.join(failed)}")
        return 1
    print(f"[OK] 全部 {len(STEPS)} 项检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
