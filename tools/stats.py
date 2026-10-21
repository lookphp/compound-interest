#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计并回填 README 里的结构性数字（字数、节数、算式数）。

为什么需要这个脚本：
    之前 README 里手写"约 1.25 万字"，实际只有 1.18 万，属于虚标。
    凡是能被计算出来的数字，都不应该手写。

用法:
    python tools/stats.py          # 只打印
    python tools/stats.py --write  # 回填到 README 的固定标记里
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "book" / "00-full.md"
README = ROOT / "README.md"

CN = re.compile(r"[\u4e00-\u9fa5]")


def count_cn(text: str) -> int:
    return len(CN.findall(text))


def calc_stats() -> dict:
    md = BOOK.read_text(encoding="utf-8")
    cn = count_cn(md)
    # 章节：## 1.1 形式
    sections = re.findall(r"^## (\d+\.\d+) ", md, re.M)
    # 部分：# 第X部分
    parts = re.findall(r"^# 第([一二三四五六七八九十]+)部分", md, re.M)
    # 算式卡
    formulas = re.findall(r"^> ### 算式 (\d+)", md, re.M)
    # 表格数
    tables = len(re.findall(r"^\|.*\|$", md, re.M))

    # 检查"节号属于哪个部分"：扫描时记录当前所在部分
    sec_pairs = []
    cur = None
    for line in md.split("\n"):
        mp = re.match(r"^# 第([一二三四五六七八九十]+)部分", line)
        if mp:
            cur = mp.group(1)
            continue
        ms = re.match(r"^## (\d+\.\d+) ", line)
        if ms and cur:
            sec_pairs.append((cur, ms.group(1)))

    # 算式卡"实际"位置：编号 -> 所在节
    # 这一步是为了抓我自己犯过的错：附录 B 的索引一度把算式 6 和算式 7
    # 的所在节写反（6 在 2.2、7 在 1.5），而编号检查根本发现不了。
    formula_sections = {}
    cur_sec = None
    for line in md.split("\n"):
        ms = re.match(r"^## (\d+\.\d+) ", line)
        if ms:
            cur_sec = ms.group(1)
            continue
        mf = re.match(r"^> ### 算式 (\d+) · (.+)$", line)
        if mf:
            formula_sections[int(mf.group(1))] = (cur_sec, mf.group(2).strip())

    # 附录 B 索引里写的"卡片位置"：| 算式 N | 名称 | [x.y](...) | ... |
    # 注意：表格可能被格式化工具对齐成 "| 算式 1  |"，所以要容忍多余空格，
    # 否则只会匹配到恰好没被补空格的那一行（曾经只匹配到"算式 10"，误报索引行数 1）。
    index_rows = re.findall(
        r"^\|\s*算式\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*\[(\d+\.\d+)\]", md, re.M
    )

    # 一级标题的顺序（用于校验"正文在前、附录在后"）
    # 真实踩过的坑：第六部分是后来补写的，被追加到了附录 C 之后，
    # 读者翻到一半先撞见附录。任何编号/锚点检查都发现不了这种错。
    h1_order = [(md[: m.start()].count("\n") + 1, m.group(1))
                for m in re.finditer(r"^# (.+)$", md, re.M)]

    # 图引用：![alt](figures/figX-*.svg) → [(文件名, alt, 所在节)]
    # 图和算式一样会有"索引写的位置 ≠ 实际位置"的错，所以照同一套办法比对。
    fig_refs = []
    cur_sec = None
    for line in md.split("\n"):
        ms = re.match(r"^## (\d+\.\d+) ", line)
        if ms:
            cur_sec = ms.group(1)
            continue
        mg = re.match(r"^!\[([^\]]*)\]\((figures/fig[^)]+\.svg)\)\s*$", line)
        if mg:
            fig_refs.append((mg.group(2).split("/", 1)[1], mg.group(1).strip(), cur_sec))

    # 附录 B 图表索引：| figX-*.svg | 标题 | [x.y](...) | ... |
    fig_index_rows = re.findall(
        r"^\|\s*(fig[\w-]+\.svg)\s*\|\s*([^|]+?)\s*\|\s*\[(\d+\.\d+)\]", md, re.M
    )

    return {
        "cn": cn,
        "md": md,
        "h1_order": h1_order,
        "wan": cn / 10000,
        "sections": len(sections),
        "parts": len(parts),
        "part_names": parts,
        "sec_pairs": sec_pairs,
        "formulas": len(formulas),
        "formula_list": [int(x) for x in formulas],
        "formula_sections": formula_sections,
        "index_rows": index_rows,
        "fig_refs": fig_refs,
        "fig_index_rows": fig_index_rows,
        "tables": tables,
        "figures": len(list((ROOT / "book" / "figures").glob("*.svg"))),
    }


def main():
    s = calc_stats()
    print(f"中文字数     : {s['cn']:,}")
    print(f"折合         : {s['wan']:.2f} 万字")
    print(f"节数         : {s['sections']}")
    print(f"部分数       : {s['parts']}")
    print(f"算式卡       : {s['formulas']}  编号={s['formula_list']}")
    print(f"图表         : {s['figures']} 张 SVG")
    print(f"表格行(粗计) : {s['tables']}")

    # 一致性检查
    problems = []
    if s["formula_list"] != list(range(1, s["formulas"] + 1)):
        problems.append("算式编号不连续")
    # 部分数不写死：只要各部分按"第一/第二/..."连续编号即可
    # （早期版本写死 5，加第六部分时会误报，属于检查器自己的 bug）
    seq = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    want = seq[: s["parts"]]
    if s["part_names"] != want:
        problems.append(f"部分编号不连续或跳号: {s['part_names']}")
    # 节号必须与所属部分一致
    for p, sec in s["sec_pairs"]:
        if sec.split(".")[0] != str(seq.index(p) + 1):
            problems.append(f"节号 {sec} 不属于第{p}部分")
            break

    # 附录 B 索引必须与卡片实际所在节一致（含名称）
    for num, name, idx_sec in s["index_rows"]:
        n = int(num)
        if n not in s["formula_sections"]:
            problems.append(f"索引里有算式 {n}，但正文找不到这张卡")
            continue
        real_sec, real_name = s["formula_sections"][n]
        if real_sec != idx_sec:
            problems.append(f"算式 {n} 索引写 {idx_sec}，卡片实际在 {real_sec}")
        if name.strip() != real_name:
            problems.append(f"算式 {n} 名称不一致：索引「{name.strip()}」/ 正文「{real_name}」")
    if len(s["index_rows"]) != s["formulas"]:
        problems.append(
            f"索引行数 {len(s['index_rows'])} ≠ 卡片数 {s['formulas']}"
        )

    # 图表索引与实际引用比对
    disk_figs = sorted(p.name for p in (ROOT / "book" / "figures").glob("*.svg"))
    ref_files = [f for f, _, _ in s["fig_refs"]]
    for f in disk_figs:
        n = ref_files.count(f)
        if n == 0:
            problems.append(f"图 {f} 在磁盘上存在但正文没有引用")
        elif n > 1:
            problems.append(f"图 {f} 被正文引用了 {n} 次（应为 1）")
    for f in ref_files:
        if f not in disk_figs:
            problems.append(f"正文引用了图 {f}，但磁盘上没有这个文件")
    alts = [a for _, a, _ in s["fig_refs"]]
    if len(alts) != len(set(alts)):
        problems.append("存在重复的图替代文本（alt）")
    # 索引行 vs 实际引用
    ref_map = {f: (a, sec) for f, a, sec in s["fig_refs"]}
    for f, name, idx_sec in s["fig_index_rows"]:
        if f not in ref_map:
            problems.append(f"图表索引里有 {f}，但正文找不到引用")
            continue
        real_alt, real_sec = ref_map[f]
        if real_sec != idx_sec:
            problems.append(f"图 {f} 索引写 {idx_sec}，实际插在 {real_sec}")
        if name.strip() != real_alt:
            problems.append(f"图 {f} 标题不一致：索引「{name.strip()}」/ 正文「{real_alt}」")
    if len(s["fig_index_rows"]) != len(s["fig_refs"]):
        problems.append(
            f"图表索引行数 {len(s['fig_index_rows'])} ≠ 正文引用数 {len(s['fig_refs'])}"
        )
    # 图表索引必须按正文出现顺序排（读者按这张表翻书）
    idx_order = [f for f, _, _ in s["fig_index_rows"]]
    appear_order = [f for f, _, _ in s["fig_refs"]]
    if idx_order and idx_order != appear_order:
        problems.append("图表索引没有按正文出现顺序排列")

    # 一级标题顺序：所有"第X部分"必须全部出现在第一个附录之前
    appx_pos = [ln for ln, title in s["h1_order"] if title.startswith("附录")]
    part_pos = [(ln, title) for ln, title in s["h1_order"]
                if re.match(r"^第[一二三四五六七八九十]+部分", title)]
    if appx_pos and part_pos:
        first_appx = min(appx_pos)
        late = [t for ln, t in part_pos if ln > first_appx]
        if late:
            problems.append(
                f"正文部分排在附录之后: {late}（第一个附录在第 {first_appx} 行）"
            )
    # 附录本身按 A/B/C… 顺序且不重复
    appx_letters = []
    for _, title in s["h1_order"]:
        m = re.match(r"^附录 ([A-Z])：", title)
        if m:
            appx_letters.append(m.group(1))
    want_letters = [chr(ord("A") + i) for i in range(len(appx_letters))]
    if appx_letters != want_letters:
        problems.append(f"附录编号不连续: {appx_letters}")

    # ---- 排版卫生：这两类问题在成品里是肉眼可见的乱码/硬伤 ----
    # 同一个问题在书稿和 README 里各犯过一次，所以两处都查。
    def typo_report(name, text):
        bad = []
        ents = re.findall(r"&#x?[0-9A-Fa-f]+;", text)
        if ents:
            bad.append(f"{name} 残留 HTML 实体 {len(ents)} 处（如 {ents[0]}）")
        prose, in_fence = [], False
        for line in text.split("\n"):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence:
                prose.append(re.sub(r"`[^`]*`", "", line))
        n = "".join(prose).count('"')
        if n:
            bad.append(f"{name} 有 {n} 个 ASCII 直引号（中文应作 “ ”）")
        if text.count("“") != text.count("”"):
            bad.append(f"{name} 弯引号不配平：左 {text.count('“')} / 右 {text.count('”')}")
        return bad

    problems.extend(typo_report("书稿", s["md"]))
    problems.extend(typo_report("README", README.read_text(encoding="utf-8")))

    if "--write" in sys.argv:
        rd = README.read_text(encoding="utf-8")
        # 替换固定格式的声明句（允许中间夹"5 张图"之类，避免加内容就匹配不上）
        pat = re.compile(
            r"全书约 [\d.]+ 万中文字，\d+ 节，\d+ 个部分，\d+ 个算式(?:，\d+ 张图)?。"
        )
        new = pat.sub(
            f"全书约 {s['wan']:.2f} 万中文字，{s['sections']} 节，"
            f"{s['parts']} 个部分，{s['formulas']} 个算式，{s['figures']} 张图。",
            rd,
        )
        if new == rd:
            # 一致性没问题但没替换，说明只是内容没变，这不算错误
            print("\n[OK] README 声明句已是最新")
        else:
            README.write_text(new, encoding="utf-8")
            print("\n[OK] README 已更新")

    if problems:
        print("\n[!] 一致性问题:", "；".join(problems))
        return 1
    print("\n[OK] 编号与结构一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
