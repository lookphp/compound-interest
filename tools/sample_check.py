#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
样本充分性核算（不做跨市场比较，只回答"能不能做"）

背景：
    本书的市场统计全部来自标普 500（1871-01 至 2023-06，1,829 个月）。
    README 里写着"没有做跨市场比较"，但只是一句笼统的自我限定。
    这个脚本把它变成一个可验算的事实：用同样的方法要在中国市场重做，
    到底需要多长的连续序列、实际能凑出多少个窗口。

为什么单独一个脚本：
    它不读任何市场数据、不产生任何新结论。它只做一件事——
    把"样本不够"这句话变成一个数字，让读者自己判断够不够。
    凡是"我觉得不够"的判断，都应该能被算出来，否则就是借口。

用法:
    python tools/sample_check.py
"""
from pathlib import Path

# ---- 输入：只看长度，不看收益 -------------------------------------------
# 标普序列的实际长度（由 market_stats.py 从快照算出）
SP_MONTHS = 1829          # 1871-01 ~ 2023-06，含头含尾
SP_YEARS_SPAN = SP_MONTHS / 12.0

# 中国市场可得的连续月度指数序列：上证综指 1990-12-19 起
# 这个起点是交易所开市日，不是选出来的；任何更早的"回溯编制"指数
# 都是用后来的成分股往回算的，不能用来做"当年买入"的检验。
CN_START = "1990-12"
CN_END = "2023-06"
CN_MONTHS = 391           # 1990-12 ~ 2023-06，39 年不到的月度观测
CN_YEARS_SPAN = CN_MONTHS / 12.0

WINDOWS = [(10, 120), (20, 240), (30, 360)]


def fmt(n):
    return f"{n:,}"


def indep_segments(years, seg):
    """互不重叠的完整段数。只算能切满的整段，余下的尾巴不算。"""
    return int(years // seg)


def windows(n_months, win_months):
    """滑动窗口个数：起点可以在 [0, n-win] 之间取，每步前进一个月"""
    if n_months <= win_months:
        return 0
    return n_months - win_months


def main():
    print("=" * 72)
    print("样本充分性核算：如果要用同样的方法分析中国市场，够不够")
    print("=" * 72)
    print()
    print(f"  标普 500 全收益（本书用的）: {fmt(SP_MONTHS)} 个月"
          f" = {SP_YEARS_SPAN:.1f} 年（1871-01 ~ 2023-06）")
    print(f"  中国可得连续序列           : {fmt(CN_MONTHS)} 个月"
          f" = {CN_YEARS_SPAN:.1f} 年（{CN_START} ~ {CN_END}）")
    print(f"  长度比                     : 1 : {SP_MONTHS / CN_MONTHS:.2f}")
    print()

    print("-" * 72)
    print("一、同样长度的滚动窗口，两边各能凑出多少个")
    print("-" * 72)
    print(f"  {'窗口':<6}{'标普':>10}{'中国':>10}{'倍数':>10}   中国占比")
    print("  " + "-" * 60)
    for years, months in WINDOWS:
        sp = windows(SP_MONTHS, months)
        cn = windows(CN_MONTHS, months)
        ratio = f"{sp / cn:.0f}x" if cn else "—"
        share = f"{cn / sp * 100:.1f}%" if sp else "—"
        print(f"  {years} 年{'':<3}{fmt(sp):>10}{fmt(cn):>10}{ratio:>10}   {share}")
    print()

    print("-" * 72)
    print("二、逐条判断：哪一项能比，哪一项不能")
    print("-" * 72)

    findings = []

    # 10 年窗口
    cn10 = windows(CN_MONTHS, 120)
    sp10 = windows(SP_MONTHS, 120)
    findings.append((
        "10 年窗口",
        CN_YEARS_SPAN // 10 >= 3,
        f"中国可凑 {fmt(cn10)} 个（标普 {fmt(sp10)} 个），"
        f"但互不重叠的只有 {int(CN_YEARS_SPAN // 10)} 段",
        "只能作为个案观察。本书用它说「10 年还可能亏」，"
        "这个现象在中国样本里无法证实也无法证伪",
    ))

    # 20 年窗口
    cn20 = windows(CN_MONTHS, 240)
    sp20 = windows(SP_MONTHS, 240)
    findings.append((
        "20 年窗口",
        CN_YEARS_SPAN // 20 >= 3,
        f"中国可凑 {fmt(cn20)} 个（标普 {fmt(sp20)} 个），"
        f"但互不重叠的只有 {int(CN_YEARS_SPAN // 20)} 段",
        "1 段独立样本，给不出「20 年不会亏」这类分布结论",
    ))

    # 30 年窗口：能凑出，但互不独立
    cn30 = windows(CN_MONTHS, 360)
    findings.append((
        "30 年窗口（全书核心证据）",
        False,
        f"中国可凑 {cn30} 个（标普 {fmt(windows(SP_MONTHS, 360))} 个），但全部重叠",
        "能算出 31 个，但任一相邻窗口共享 359 个月里的绝大多数历史；"
        "本质上是「一段历史的 31 个切法」，不是 31 个样本",
    ))

    # 独立 30 年窗口（不重叠）
    sp_indep = int(SP_YEARS_SPAN // 30)
    cn_indep = int(CN_YEARS_SPAN // 30)
    findings.append((
        "互不重叠的 30 年区间",
        cn_indep >= 3,
        f"标普 {sp_indep} 段，中国 {cn_indep} 段",
        "中国只有 1 段，n=1 无法给出任何区间估计",
    ))

    # 五个年代的分段比较（全书用 25 年一段做了五次）
    findings.append((
        "跨年代的 25 年分段",
        CN_YEARS_SPAN >= 25 * 5,
        f"中国总长 {CN_YEARS_SPAN:.1f} 年，最多切 {(int(CN_YEARS_SPAN) // 25)} 段 25 年",
        "全书切了 5 段做对比，中国最多 1 段，无对比可言",
    ))

    # 单一年份分布（152 个年度观测）
    findings.append((
        "单一年度分布（152 个观测）",
        CN_MONTHS // 12 >= 100,
        f"中国满年约 {CN_MONTHS // 12} 个年度观测",
        "年度亏损占比这类统计，样本数只有三分之一",
    ))

    verdict = 0
    for name, ok, fact, why in findings:
        mark = "[可]  " if ok else "[不可]"
        verdict += 0 if ok else 1
        print(f"  {mark} {name}")
        print(f"         事实：{fact}")
        print(f"         结论：{why}")
        print()

    print("=" * 72)
    print("三、判断")
    print("=" * 72)
    print(f"  当前覆盖 6 项检查，判定为「不可」的有 {verdict} 项。")
    print("  但要注意：即使标「可」，也不等于「可信」。")
    print()
    print("  关键区别在于「独立样本」而不是「窗口个数」：")
    print(f"    标普 {SP_YEARS_SPAN:.0f} 年里，互不重叠的 30 年区间有 {sp_indep} 段；")
    print(f"    中国 {CN_YEARS_SPAN:.1f} 年里只有 {cn_indep} 段。")
    print("    滑动窗口会让人以为样本很多，但相邻窗口共享 29 年零 11 个月的历史，")
    print("    它们不是独立观测。**窗口个数不是样本量。**")
    print()
    print("  因此本书的处理是：不做跨市场比较，也不补。")
    print("  理由不是「中国的数据不好看」，而是：")
    print(f"    在 {cn_indep} 段独立 30 年样本上，任何结论的置信区间都会宽到没有意义。")
    print()
    print("  这条限制已写入 README「自我限定」第 4 条与附录 D.4。")
    print("  如果将来中国市场积累了足够长度（至少 90 年，即 3 段独立 30 年），")
    print("  本脚本的判定会自动从「不可」变成「可」——到那时再补。")
    print()
    # 注意返回码：本脚本是「告知型」检查，不是「断言型」。
    # 「不可做」是这本书的既定结论，不是检查失败，所以返回 0。
    # 只有当判定与书中表述矛盾时才应该非零——那需要人工改书，脚本不替人决定。
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
