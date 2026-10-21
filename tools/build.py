#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 book/00-full.md 渲染成单文件 HTML（零外部依赖、可离线、手机可读、可搜索）。

用法:
    python tools/build.py

输出:
    index.html
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "book" / "00-full.md"
OUT = ROOT / "index.html"


def slugify(text: str) -> str:
    """生成锚点 id：保留中文，去掉标点。"""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fa5\- ]", "", text)
    text = text.strip().replace(" ", "-")
    return text or "sec"


def inline_md(s: str) -> str:
    """处理行内 markdown：粗体、行内代码、链接。"""
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def table_to_html(rows):
    """把 markdown 表格行转成 HTML。"""
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    if not cells:
        return ""
    out = ['<div class="tbl-wrap"><table>']
    header = cells[0]
    out.append("<thead><tr>" + "".join(f"<th>{inline_md(c)}</th>" for c in header) + "</tr></thead>")
    body = cells[1:]
    # 去掉分隔行 |---|---|
    if body and all(re.fullmatch(r":?-{2,}:?", c) for c in body[0] if c):
        body = body[1:]
    out.append("<tbody>")
    for r in body:
        out.append("<tr>" + "".join(f"<td>{inline_md(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def convert(md: str):
    lines = md.split("\n")
    body, toc = [], []
    i = 0
    in_code = False
    code_buf = []
    list_stack = []  # 'ul' / 'ol'

    def close_lists():
        while list_stack:
            body.append(f"</{list_stack.pop()}>")

    while i < len(lines):
        line = lines[i]

        # 代码块
        if line.startswith("```"):
            if in_code:
                body.append('<pre><code>' + html.escape("\n".join(code_buf)) + "</code></pre>")
                code_buf, in_code = [], False
            else:
                close_lists()
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # 表格
        if line.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]):
            close_lists()
            tbl = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl.append(lines[i])
                i += 1
            body.append(table_to_html(tbl))
            continue

        # 图片：![alt](path) —— 单独一行时，内联 SVG 直接嵌入，保证单文件离线可读
        mi = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", line)
        if mi:
            close_lists()
            alt, src = mi.group(1), mi.group(2)
            fig_path = (ROOT / "book" / src).resolve()
            if fig_path.suffix == ".svg" and fig_path.exists():
                svg = fig_path.read_text(encoding="utf-8")
                # 去掉 XML 声明，保留 viewBox，宽度交给 CSS
                svg = re.sub(r"<\?xml[^>]*\?>", "", svg).strip()
                body.append(
                    f'<figure class="fig">'
                    f'{svg}'
                    f'<figcaption>{inline_md(alt)}</figcaption>'
                    f"</figure>"
                )
            else:
                body.append(
                    f'<figure class="fig">'
                    f'<img src="{html.escape(src)}" alt="{html.escape(alt)}" loading="lazy"/>'
                    f'<figcaption>{inline_md(alt)}</figcaption>'
                    f"</figure>"
                )
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            close_lists()
            lvl = len(m.group(1))
            text = m.group(2).strip()
            sid = slugify(text)
            if lvl in (1, 2):
                toc.append((lvl, text, sid))
            body.append(f'<h{lvl} id="{sid}">{inline_md(text)}</h{lvl}>')
            i += 1
            continue

        # 分割线
        if re.match(r"^\s*---+\s*$", line):
            close_lists()
            body.append("<hr/>")
            i += 1
            continue

        # 引用
        if line.strip().startswith(">"):
            close_lists()
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            # 算式卡：引用块内以 ### 算式 N 开头
            joined = "\n".join(buf)
            if re.match(r"^###\s*算式\s*\d+", joined):
                num = re.search(r"算式\s*(\d+)", joined)
                num = num.group(1) if num else "?"
                # 标题形如 "算式 1 · 每天 1% 的年度倍数"，拆出名称
                first_line = buf[0] if buf else ""
                title = re.sub(r"^#+\s*", "", first_line)
                title = re.sub(r"^算式\s*\d+\s*[·:：\-—]?\s*", "", title).strip()
                # 去掉标题行，避免与标签重复
                rest = "\n".join(buf[1:])
                inner_body, _ = convert(rest)
                body.append(
                    f'<div class="formula" id="calc-{num}">'
                    f'<div class="formula-tag">算式 {num}</div>'
                    f'<div class="formula-title">{inline_md(title)}</div>'
                    f'{inner_body}</div>'
                )
                continue
            inner = "<br/>".join(inline_md(b) for b in buf if b)
            # 本章结论：单独着色
            cls = "verdict" if "本章结论" in inner else ""
            body.append(f'<blockquote class="{cls}">{inner}</blockquote>')
            continue

        # 列表
        mu = re.match(r"^\s*[-*]\s+(.*)$", line)
        mo = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if mu or mo:
            want = "ul" if mu else "ol"
            if not list_stack or list_stack[-1] != want:
                close_lists()
                body.append(f"<{want}>")
                list_stack.append(want)
            body.append(f"<li>{inline_md((mu or mo).group(1))}</li>")
            i += 1
            continue

        if not line.strip():
            close_lists()
            i += 1
            continue

        close_lists()
        body.append(f"<p>{inline_md(line)}</p>")
        i += 1

    if in_code and code_buf:
        body.append('<pre><code>' + html.escape("\n".join(code_buf)) + "</code></pre>")
    close_lists()
    return "\n".join(body), toc


TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>没有一种复利叫坚持 · 别把线性当复利</title>
<style>
:root{{
  --bg:#fbfaf7; --fg:#1f2328; --muted:#5b6570; --line:#e3e0d8;
  --card:#ffffff; --accent:#b45309; --accent-bg:#fdf3e7;
  --code-bg:#f4f2ec; --ok:#166534; --warn:#a16207; --no:#b91c1c;
}}
html[data-theme="dark"]{{
  --bg:#14161a; --fg:#e6e8ea; --muted:#9aa4ae; --line:#2b3038;
  --card:#1b1e23; --accent:#f0b35e; --accent-bg:#2a2318;
  --code-bg:#23272e; --ok:#4ade80; --warn:#fbbf24; --no:#f87171;
}}
*{{box-sizing:border-box}}
body{{
  margin:0; background:var(--bg); color:var(--fg);
  font:16px/1.85 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  -webkit-text-size-adjust:100%;
}}
header{{
  position:sticky; top:0; z-index:20; background:var(--bg);
  border-bottom:1px solid var(--line); padding:10px 16px;
  display:flex; gap:12px; align-items:center; flex-wrap:wrap;
}}
header h1{{font-size:15px;margin:0;font-weight:700;letter-spacing:.02em}}
header .sub{{font-size:12px;color:var(--muted)}}
header .grow{{flex:1}}
#q{{
  padding:7px 12px;border:1px solid var(--line);border-radius:8px;
  background:var(--card);color:var(--fg);font-size:14px;width:220px;max-width:45vw;
}}
#q:focus{{outline:2px solid var(--accent);outline-offset:1px}}
button{{
  padding:7px 12px;border:1px solid var(--line);border-radius:8px;
  background:var(--card);color:var(--fg);font-size:13px;cursor:pointer;
}}
button:hover{{border-color:var(--accent);color:var(--accent)}}
button.on{{background:var(--accent-bg);border-color:var(--accent);color:var(--accent);font-weight:600}}
.layout{{display:flex;max-width:1180px;margin:0 auto;align-items:flex-start}}
nav{{
  width:250px;flex:0 0 250px;position:sticky;top:56px;max-height:calc(100vh - 70px);
  overflow:auto;padding:18px 12px 40px 16px;font-size:13.5px;
}}
nav a{{display:block;padding:5px 8px;color:var(--muted);text-decoration:none;border-radius:6px;line-height:1.5}}
nav a:hover{{background:var(--accent-bg);color:var(--accent)}}
nav a.lv2{{padding-left:20px;font-size:12.5px}}
nav a.active{{background:var(--accent-bg);color:var(--accent);font-weight:600}}
main{{flex:1;min-width:0;padding:28px 28px 90px}}
main h1{{font-size:30px;line-height:1.35;margin:.4em 0 .6em;letter-spacing:-.01em}}
main h2{{font-size:23px;margin:2.2em 0 .8em;padding-top:.5em;border-top:1px solid var(--line);letter-spacing:-.01em}}
main h3{{font-size:18px;margin:1.9em 0 .6em}}
main h4{{font-size:16px;margin:1.5em 0 .5em}}
main p{{margin:.9em 0}}
main ul,main ol{{margin:.8em 0;padding-left:1.5em}}
main li{{margin:.35em 0}}
blockquote{{
  margin:1.2em 0;padding:14px 18px;background:var(--accent-bg);
  border-left:4px solid var(--accent);border-radius:0 8px 8px 0;
  font-size:15.5px;
}}
blockquote p{{margin:0}}
code{{background:var(--code-bg);padding:1px 5px;border-radius:4px;font-size:.9em;
  font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
pre{{background:var(--code-bg);padding:14px 16px;border-radius:10px;overflow:auto;border:1px solid var(--line)}}
pre code{{background:none;padding:0;font-size:13.5px;line-height:1.7}}
.tbl-wrap{{overflow-x:auto;margin:1.2em 0;border:1px solid var(--line);border-radius:10px}}
table{{border-collapse:collapse;width:100%;font-size:14.5px;background:var(--card)}}
th,td{{padding:9px 13px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{background:var(--code-bg);font-weight:600;white-space:nowrap}}
tr:last-child td{{border-bottom:none}}
hr{{border:none;border-top:1px solid var(--line);margin:2.5em 0}}
a{{color:var(--accent)}}
mark{{background:#ffe58f;color:#1f2328;padding:0 2px;border-radius:3px}}
html[data-theme="dark"] mark{{background:#7a5c00;color:#fff}}
#top{{
  position:fixed;right:18px;bottom:18px;width:44px;height:44px;border-radius:50%;
  border:1px solid var(--line);background:var(--card);color:var(--fg);
  font-size:18px;cursor:pointer;display:none;box-shadow:0 2px 10px rgba(0,0,0,.12);
}}
#top.show{{display:block}}
.hint{{font-size:13px;color:var(--muted);margin-bottom:1em}}
/* 算式卡 */
.formula{{
  margin:1.6em 0;border:1px solid var(--accent);border-left-width:5px;
  border-radius:10px;background:var(--card);padding:4px 18px 12px;position:relative;
}}
.formula-tag{{
  display:inline-block;margin-top:-1px;transform:translateY(-50%);
  background:var(--accent);color:#fff;font-size:11.5px;font-weight:700;
  letter-spacing:.06em;padding:2px 10px;border-radius:99px;
}}
html[data-theme="dark"] .formula-tag{{color:#14161a}}
.formula h3{{margin:.2em 0 .5em;font-size:16px;border:none;padding:0}}
.formula .formula-title{{
  font-size:16.5px;font-weight:700;margin:.15em 0 .55em;line-height:1.45;
}}
.formula table{{font-size:13.5px}}
.formula th{{background:var(--accent-bg);color:var(--accent)}}
.formula .tbl-wrap{{margin:.6em 0 0;border-color:var(--line)}}
/* 结论块 */
blockquote.verdict{{
  border-left-color:var(--ok);background:linear-gradient(90deg,var(--accent-bg),transparent 85%);
}}
blockquote.verdict strong:first-child{{color:var(--ok)}}
/* 图 */
figure.fig{{margin:1.8em 0;padding:0}}
figure.fig svg,figure.fig img{{
  display:block;width:100%;height:auto;
  border:1px solid var(--line);border-radius:10px;background:#fff;
}}
html[data-theme="dark"] figure.fig svg,
html[data-theme="dark"] figure.fig img{{filter:invert(.92) hue-rotate(180deg)}}
figure.fig figcaption{{
  margin-top:.55em;font-size:13px;color:var(--muted);text-align:center;line-height:1.6;
}}
body.only-verdict main figure.fig{{display:none}}
/* 只看结论模式 */
body.only-verdict main p,body.only-verdict main ul,body.only-verdict main ol,
body.only-verdict main table,body.only-verdict main pre{{display:none}}
body.only-verdict main blockquote{{display:block}}
body.only-verdict main h2,body.only-verdict main h3{{display:block}}
@media(max-width:820px){{
  nav{{display:none}}
  main{{padding:20px 16px 90px}}
  main h1{{font-size:25px}}
  main h2{{font-size:20px}}
  header{{padding:8px 12px;gap:8px}}
  #q{{width:100%;max-width:none;order:10}}
}}
@media print{{
  header,nav,#top{{display:none}}
  body{{background:#fff}}
  main{{padding:0;max-width:none}}
  pre,.tbl-wrap{{page-break-inside:avoid}}
}}
</style>
</head>
<body>
<header>
  <div>
    <h1>没有一种复利叫坚持</h1>
    <div class="sub">别把线性当复利</div>
  </div>
  <div class="grow"></div>
  <button id="btn-verdict" title="只显示每章的结论块">只看结论</button>
  <button id="btn-theme" title="切换明暗">🌗</button>
  <input id="q" type="search" placeholder="搜索全书…" autocomplete="off"/>
</header>

<div class="layout">
  <nav id="toc">{toc}</nav>
  <main id="content">
{body}
  </main>
</div>
<button id="top" title="回到顶部">↑</button>

<script>
(function(){{
  var root=document.documentElement;
  var saved=localStorage.getItem('ci-theme');
  if(saved) root.setAttribute('data-theme',saved);

  document.getElementById('btn-theme').onclick=function(){{
    var now=root.getAttribute('data-theme')==='dark'?'light':'dark';
    root.setAttribute('data-theme',now);
    localStorage.setItem('ci-theme',now);
  }};

  document.getElementById('btn-verdict').onclick=function(){{
    document.body.classList.toggle('only-verdict');
    this.classList.toggle('on');
  }};

  var top=document.getElementById('top');
  window.addEventListener('scroll',function(){{
    top.classList.toggle('show',window.scrollY>600);
  }});
  top.onclick=function(){{window.scrollTo({{top:0,behavior:'smooth'}});}};

  // 滚动联动目录
  var links=[].slice.call(document.querySelectorAll('#toc a'));
  var targets=links.map(function(a){{return document.getElementById(a.getAttribute('href').slice(1));}});
  function sync(){{
    var pos=window.scrollY+120, idx=0;
    for(var i=0;i<targets.length;i++){{
      if(targets[i]&&targets[i].offsetTop<=pos) idx=i;
    }}
    links.forEach(function(a,i){{a.classList.toggle('active',i===idx);}});
  }}
  window.addEventListener('scroll',sync,{{passive:true}});
  sync();

  // 搜索高亮
  var q=document.getElementById('q');
  var content=document.getElementById('content');
  var original=content.innerHTML;
  var timer=null;
  q.addEventListener('input',function(){{
    clearTimeout(timer);
    var kw=q.value.trim();
    timer=setTimeout(function(){{
      if(!kw){{ content.innerHTML=original; return; }}
      if(content.innerHTML!==original) return;
      var esc=kw.replace(/[.*+?^${{}}()|[\\]\\\\]/g,'\\\\$&');
      var re=new RegExp(esc,'gi');
      // 只替换文本节点，避免破坏标签
      var walker=document.createTreeWalker(content,NodeFilter.SHOW_TEXT,null);
      var nodes=[],n;
      while((n=walker.nextNode())) nodes.push(n);
      nodes.forEach(function(node){{
        if(!re.test(node.nodeValue)) return;
        var span=document.createElement('span');
        span.innerHTML=node.nodeValue.replace(re,function(m){{return '<mark>'+m+'</mark>';}});
        node.parentNode.replaceChild(span,node);
      }});
      var first=content.querySelector('mark');
      if(first) first.scrollIntoView({{block:'center',behavior:'smooth'}});
    }},220);
  }});
}})();
</script>
</body>
</html>
"""


def main():
    if not SRC.exists():
        sys.exit(f"找不到 {SRC}")
    md = SRC.read_text(encoding="utf-8")
    body, toc = convert(md)

    toc_html = []
    for lvl, text, sid in toc:
        cls = "lv2" if lvl == 2 else "lv1"
        toc_html.append(f'<a class="{cls}" href="#{sid}">{html.escape(text)}</a>')

    out = TPL.format(toc="\n".join(toc_html), body=body)
    OUT.write_text(out, encoding="utf-8")
    print(f"已生成 {OUT}  ({len(out) / 1024:.1f} KB)")
    print(f"目录条目 {len(toc)} 个")


if __name__ == "__main__":
    main()
