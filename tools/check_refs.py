#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验正文里的"指涉"：所有说"见算式 N / X.Y 节 / 第X部分 / 第②条"的地方，
被指涉的对象必须真实存在。

为什么需要：
    算式有编号检查、锚点有失效检查，但正文里的**文字指涉**一直靠人眼维护。
    真实会出的事故：正文写"用算式 6 的语言说"，后来算式重排了，6 变成别的卡；
    或者写"这一点在 3.1 节会再讲一次"，3.1 后来被删了。读者照着翻，翻不到。

    人负责想法和纠错；对照关系交给机器。

检查五类指涉：
    1. "算式 N"          → 卡片必须存在
    2. "X.Y 节"          → 节必须存在
    3. "第X部分"          → 部分必须存在
    4. "第 ① 条 / 条件 ②" → 必须落在真实条件数之内（从"## 2.N 条件X"标题提取，
       并要求序数与节号一致；不能用"2.x 节数"当条件数——2.6 是检验表）
    5. 提示性输出：正文（附录前）对每张卡的显式指涉分布。
       "每张卡至少被指涉一次"曾想做成败文检查，但附录索引必然提到每张卡、
       排除后又过严（卡片嵌在正文流里，不强制需要"见算式 N"），
       所以降级为提示，供人在编号重排后核对指涉有没有迁移。

用法:
    python tools/check_refs.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "book" / "00-full.md"

CN_NUM = "一二三四五六七八九十"


def main():
    md = BOOK.read_text(encoding="utf-8")
    problems = []

    # ---- 基准对象 ----
    cards = set(int(n) for n in re.findall(r"^> ### 算式 (\d+)", md, re.M))
    sections = set(re.findall(r"^## (\d+\.\d+) ", md, re.M))
    parts = set(re.findall(r"^# 第([一二三四五六七八九十]+)部分", md, re.M))

    # 条件表：从标题本身提取「## 2.N 条件X」。
    # 不能用"2.x 节数"当条件数——2.6 是检验表，不是第六个条件（首轮就踩了这个坑）。
    seq_cn = "一二三四五六七八九十"
    cond_by_ord = {}   # 序数(1-based) -> 节号
    for m in re.finditer(rf"^## (2\.\d+) 条件([{seq_cn}])", md, re.M):
        sec, c = m.group(1), m.group(2)
        ord1 = seq_cn.index(c) + 1
        cond_by_ord[ord1] = sec
        # 条件的中文序数必须与节号一致：条件二 ↔ 2.2
        if sec != f"2.{ord1}":
            problems.append(f"「条件{c}」放在 {sec} 节，序数与节号不一致")

    # ---- 1. 算式指涉 ----
    for n in set(re.findall(r"算式\s*(\d+)", md)):
        n = int(n)
        if n not in cards:
            # 找一处上下文，方便定位
            ctx = re.search(rf".{{20}}算式\s*{n}.{{20}}", md, re.S)
            where = ctx.group(0).replace("\n", " ") if ctx else ""
            problems.append(f"正文指涉「算式 {n}」，但没有这张卡（共 {len(cards)} 张）…{where}…")

    # ---- 2. 节指涉 ----
    for sec in set(re.findall(rf"(\d+\.\d+)\s*节", md)):
        if sec not in sections:
            problems.append(f"正文指涉「{sec} 节」，但没有这一节")

    # ---- 3. 部分指涉 ----
    for p in set(re.findall(rf"第([{CN_NUM}]+)部分", md)):
        if p not in parts:
            problems.append(f"正文指涉「第{p}部分」，但没有这个部分")

    # ---- 4. 条件指涉 ----
    circ = "①②③④⑤⑥⑦⑧⑨⑩"
    for pat in (r"第\s*([{}])\s*条", r"条件\s*([{}])"):
        for c in set(re.findall(pat.format(circ), md)):
            idx = circ.index(c) + 1
            if idx not in cond_by_ord:
                problems.append(f"正文指涉「{c}」号条件，但书中只有 "
                                f"{len(cond_by_ord)} 个条件")
    # "条件X"（中文数字写法）
    for c in set(re.findall(rf"条件([{seq_cn}])", md)):
        idx = seq_cn.index(c) + 1
        if idx not in cond_by_ord:
            problems.append(f"正文指涉「条件{c}」，但书中只有 "
                            f"{len(cond_by_ord)} 个条件")

    # ---- 5. 指涉分布（提示，不判失败）----
    # 原本想做成"孤儿卡检查"：每张卡至少被正文指涉一次。
    # 但附录 B 索引本身就会提到每张卡，不排除的话检查形同虚设；
    # 排除后又过严——卡片嵌在正文流里，读者顺着读就会遇到，
    # 不强制需要"见算式 N"这种显式指涉。
    # 所以降级为提示：只报告附录之前正文里的显式指涉分布，
    # 供人判断"编号重排后指涉有没有迁移"。
    appx_start = md.find("# 附录 A")
    body = md[: appx_start] if appx_start > 0 else md
    body = re.sub(r"^> ### 算式 \d+.*$", "", body, flags=re.M)  # 卡头不算指涉
    mentions = {n: len(re.findall(rf"算式\s*{n}\b", body))
                for n in sorted(cards)}
    print()
    print("  正文（附录前）显式指涉分布（卡头不计）：" +
          ", ".join(f"算式{n}×{c}" for n, c in mentions.items()))
    zero = [n for n, c in mentions.items() if c == 0]
    if zero:
        print(f"  提示：算式 {zero} 在正文里没有被显式指涉过——"
              f"卡片嵌在正文流里，这不一定是问题，但编号重排时值得看一眼这里。")

    print(f"算式卡 {len(cards)} 张 / 节 {len(sections)} 个 / 部分 {len(parts)} 个 / "
          f"条件 {len(cond_by_ord)} 条")
    print(f"指涉检查：算式 {len(set(re.findall(r'算式\s*(\d+)', md)))} 处、"
          f"节 {len(set(re.findall(r'(\d+\.\d+)\s*节', md)))} 处、"
          f"部分 {len(set(re.findall(rf'第([{CN_NUM}]+)部分', md)))} 处、"
          f"条件若干处")

    if problems:
        print()
        print("[!] 指涉问题:")
        for p in problems:
            print(f"      - {p}")
        return 1
    print()
    print("[OK] 所有指涉都能落到真实对象")
    return 0


if __name__ == "__main__":
    sys.exit(main())
