#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验 book/00-full.md 里的内部锚点链接是否都能落到真实标题上。

为什么需要：
    markdown 渲染器（GitHub、本书的 build.py）生成锚点的规则不完全一样，
    而且大小写敏感、标点会被吞掉。手写链接几乎必然有错。
    "附录-A" 写成 "附录-a" 就是一个真实的例子：全文看起来对，点不动。

用法:
    python tools/check_anchors.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "book" / "00-full.md"
README = ROOT / "README.md"

# 与 build.py / GitHub 一致的 slug 规则：
# 保留中文、字母、数字、下划线、连字符、空格；空格转 -；标点全部丢弃
SLUG_KEEP = re.compile(r"[^\w\u4e00-\u9fa5\- ]", re.UNICODE)


def slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = SLUG_KEEP.sub("", text)
    return text.strip().replace(" ", "-")


def headings(md: str):
    out = {}
    for line in md.split("\n"):
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            out[slug(m.group(2).strip())] = m.group(2).strip()
    return out


def links(md: str):
    """返回 [(行号, 目标)]，只取页内锚点"""
    out = []
    for i, line in enumerate(md.split("\n"), 1):
        for m in re.finditer(r"\]\(#([^)]+)\)", line):
            out.append((i, m.group(1)))
    return out


def check(path: Path, anchors: dict, prefix: str = ""):
    md = path.read_text(encoding="utf-8")
    bad = []
    for ln, tgt in links(md):
        if prefix:
            if not tgt.startswith(prefix):
                continue
            tgt = tgt[len(prefix):]
        if tgt not in anchors:
            bad.append((ln, tgt))
    return bad, len(links(md))


def main():
    book_md = BOOK.read_text(encoding="utf-8")
    anchors = headings(book_md)

    print(f"书中标题数（可作锚点）: {len(anchors)}")

    bad, total = check(BOOK, anchors)
    print(f"book/00-full.md  页内链接 {total} 个，失效 {len(bad)} 个")
    for ln, tgt in bad:
        print(f"  L{ln}: #{tgt}")

    # README 里指向 book 的链接形如 book/00-full.md#xxx
    rd = README.read_text(encoding="utf-8")
    bad2 = []
    n2 = 0
    for i, line in enumerate(rd.split("\n"), 1):
        for m in re.finditer(r"\]\(book/00-full\.md#([^)]+)\)", line):
            n2 += 1
            if m.group(1) not in anchors:
                bad2.append((i, m.group(1)))
    print(f"README.md        指向书稿的链接 {n2} 个，失效 {len(bad2)} 个")
    for ln, tgt in bad2:
        print(f"  L{ln}: #{tgt}")

    if bad or bad2:
        print("\n[!] 有失效锚点，请修正")
        return 1
    print("\n[OK] 所有内部锚点均可到达")
    return 0


if __name__ == "__main__":
    sys.exit(main())
