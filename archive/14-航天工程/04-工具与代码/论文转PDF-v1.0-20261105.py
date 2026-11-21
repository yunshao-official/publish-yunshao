#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论文 Markdown 转 PDF（Chrome 无头打印）

用法：
    python 论文转PDF-v1.0-20261105.py <输入.md> [输出.pdf]

说明：
    - 只用标准库，不装任何包。
    - 数学公式交给 MathJax 3（jsdelivr CDN），打印前等待渲染完成。
    - 需要本机装有 Chrome（默认路径见 CHROME_CANDIDATES）。
"""

import html
import os
import re
import subprocess
import sys
import tempfile
import time

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script>
window.MathJax = {{
  tex: {{ inlineMath: [['$','$']], displayMath: [['$$','$$']] }},
  svg: {{ fontCache: 'global' }},
  startup: {{ typeset: true }}
}};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
<style>
  @page {{ size: A4; margin: 20mm 18mm 20mm 18mm; }}
  body {{ font-family: "Times New Roman", "SimSun", "Songti SC", serif;
         font-size: 10.5pt; line-height: 1.65; color: #111; }}
  h1 {{ font-size: 17pt; text-align: center; margin: 0 0 6mm 0; line-height: 1.4; }}
  h2 {{ font-size: 13pt; margin: 7mm 0 3mm 0; border-bottom: 0.6pt solid #999; padding-bottom: 1.2mm; }}
  h3 {{ font-size: 11.5pt; margin: 5mm 0 2mm 0; }}
  p {{ margin: 0 0 2.2mm 0; text-align: left; }}
  mjx-container {{ white-space: nowrap; }}
  blockquote {{ margin: 4mm 0; padding: 3mm 4mm; background: #f4f4f4;
                border-left: 3pt solid #666; font-size: 9.5pt; }}
  table {{ border-collapse: collapse; width: 100%; margin: 3mm 0; font-size: 9.5pt; }}
  th, td {{ border: 0.5pt solid #888; padding: 1.2mm 2mm; text-align: left; }}
  th {{ background: #eee; }}
  ul, ol {{ margin: 0 0 2.5mm 0; padding-left: 7mm; }}
  li {{ margin-bottom: 1.2mm; }}
  code {{ font-family: Consolas, monospace; font-size: 9pt; background: #f0f0f0; padding: 0 1pt; }}
  .refs p {{ text-indent: -6mm; padding-left: 6mm; font-size: 9.5pt; }}
  .footer {{ margin-top: 8mm; font-size: 8.5pt; color: #555; text-align: center; }}
  .math-display {{ text-align: center; margin: 3mm 0; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def convert(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out = []
    i = 0
    n = len(lines)
    title = "论文"

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # 代码块
        if stripped.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 1:
                title = re.sub(r"[*`]", "", text)
            out.append(f"<h{level}>{inline(text)}</h{level}>")
            i += 1
            continue

        # 分隔线
        if re.match(r"^-{3,}$", stripped):
            out.append("<hr>")
            i += 1
            continue

        # 独立公式
        if stripped.startswith("$$"):
            buf = [stripped[2:]]
            if stripped.endswith("$$") and len(stripped) > 4:
                buf = [stripped[2:-2]]
                i += 1
            else:
                i += 1
                while i < n and not lines[i].strip().endswith("$$"):
                    buf.append(lines[i])
                    i += 1
                if i < n:
                    buf.append(lines[i].strip()[:-2])
                    i += 1
            out.append('<div class="math-display">$$' + "\n".join(buf) + "$$</div>")
            continue

        # 引用块
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            joined = " ".join(buf)
            # 档案用的"摘要头（≤300字）"是内部标记，外发 PDF 不显示
            if re.match(r"^\*\*(摘要头|Header)\b", joined):
                continue
            out.append("<blockquote>" + inline(joined) + "</blockquote>")
            continue

        # 表格
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            header = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = ["<table><thead><tr>"]
            t += [f"<th>{inline(c)}</th>" for c in header]
            t.append("</tr></thead><tbody>")
            for r in rows:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue

        # 无序列表
        if re.match(r"^[-*+]\s+", stripped):
            items = []
            while i < n and re.match(r"^[-*+]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*+]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue

        # 有序列表
        if re.match(r"^\d+[.)]\s+", stripped):
            items = []
            while i < n and re.match(r"^\d+[.)]\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+[.)]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue

        # 段落（合并到空行）
        buf = [stripped]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith("#") or nxt.startswith("|")
                    or nxt.startswith("$$") or nxt.startswith(">")
                    or re.match(r"^[-*+]\s+", nxt) or re.match(r"^\d+[.)]\s+", nxt)):
                break
            buf.append(nxt)
            i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")

    return title, "\n".join(out)


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit("找不到 Chrome 或 Edge")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    src = os.path.abspath(sys.argv[1])
    dst = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.splitext(src)[0] + ".pdf"

    with open(src, "r", encoding="utf-8") as f:
        md = f.read()

    title, body = convert(md)
    page = TEMPLATE.format(title=html.escape(title), body=body)

    keep = os.environ.get("MDPDF_KEEP_HTML")
    if keep:
        html_path = os.path.abspath(keep)
    else:
        tmpdir = tempfile.mkdtemp(prefix="mdpdf_")
        html_path = os.path.join(tmpdir, "paper.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(page)

    chrome = find_chrome()
    url = "file:///" + html_path.replace("\\", "/")
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        "--virtual-time-budget=25000",
        f"--print-to-pdf={dst}",
        url,
    ]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(r.stderr[-2000:])
        raise SystemExit(f"Chrome 退出码 {r.returncode}")
    if not os.path.exists(dst):
        raise SystemExit("PDF 未生成")
    print(f"OK {dst}  {os.path.getsize(dst)/1024:.1f} KB  {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
