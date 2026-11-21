# -*- coding: utf-8 -*-
# 执行器层·主流软件工程·纯stdlib·禁API
"""
scan_deps.py — 过时令牌全库扫描 / "改常数→下游影响面"机械演示（工具2）
=====================================================================
原理：常数一旦改版（如公式a判负、f0 由 800THz 改 373THz），凡引用旧值的
正文文档即受影响。本工具把"影响面"变成机械可查的命中清单：每个过时令牌
给出 文件|行号|行内容（截断80字）。
范围：18 个域目录全部 .md，**含 09-归档**（命中标注"归档件"，归档件只
标注不要求改）；排除只读区（绝不扫描）与 工具/工具报告（自指豁免）。
参数化：过时令牌表 = 下方 TOKENS 顶部常量。未来加 [constants:vX] 锚点
扫描时，只需在 TOKENS 追加 ("[constants:v1]", "锚点...") 一类条目，或在
scan_line 挂新匹配器；报告节自动随表再生。
长/短令牌重叠处理：同一行内长令牌优先占区间，短令牌不重复计数
（如 "350/√(Λ+0.01)" 命中处不再给 "350/√(Λ" 记一条）。
输出：scan_deps报告-20260916.md
用法：python scan_deps.py   （只读扫描，不修改任何文档）
"""
import os
import re
import sys
import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"H:\理论存档"
TOOL_DIR = os.path.join(ROOT, "09-流程规范", "工具")
REPORT_DIR = os.path.join(ROOT, "09-流程规范", "工具报告")
REPORT_PATH = os.path.join(REPORT_DIR, "scan_deps报告-20260916.md")

# ===================== 过时令牌表（顶部常量·参数化入口） =====================
# 格式：(令牌, 口径说明)。顺序即优先级：长令牌在前，短令牌不重复计长命中。
# 未来扩展：在此追加条目即可（例：("[constants:v0]", "旧版锚点已废")）。
TOKENS = [
    ("350/√(Λ+0.01)", "公式a（Tc）已判负（P0-2·0913审计）；正本=公式b Tc=Θ_D×15/16×f_defect"),
    ("350/√(Λ", "公式a（Tc）已判负·短形式（覆盖变体写法）"),
    ("800THz", "频率过时（P0-7）；正本 f0=373THz"),
    ("2309K", "笔误：应为 2390K"),
    ("σ²=1/8", "σ误抄（P0-5）；正本 σ投影=1/√6（σ²=1/6）"),
    ("σ^2=1/8", "σ误抄·ASCII形式"),
    ("α²=σ²", "恒等式作废（P0-5：σ独立于α）"),
    ("α^2=σ^2", "恒等式作废·ASCII形式"),
]
# ============================================================================

READONLY_DIRS = {
    "_归档-已整合-20260726",
    "backup_20260725",
    "backup_20260726_pre-attack",
    "归档-旧常数体系-20260731",
    "云韶备份",
}
ARCHIVE_DIR_NAME = "09-归档"
LINE_CUT = 80


def domain_dirs():
    out = []
    for name in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, name)
        if re.match(r"^\d{2}-", name) and os.path.isdir(p):
            out.append(name)
    return out


def read_text_any(path):
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def scan_line(line, tokens):
    """区间占用法：长令牌优先，短令牌跳过已占区间。返回 [(idx, col)]。"""
    hits = []
    occupied = []  # [(start,end)]
    def taken(s, e):
        return any(s < oe and os_ < e for os_, oe in occupied)
    for idx, (tok, _why) in enumerate(tokens):
        start = 0
        while True:
            pos = line.find(tok, start)
            if pos < 0:
                break
            if not taken(pos, pos + len(tok)):
                hits.append((idx, pos))
                occupied.append((pos, pos + len(tok)))
            start = pos + 1
    hits.sort(key=lambda x: x[1])
    return hits


def main():
    hits_by_token = {i: [] for i in range(len(TOKENS))}
    files_scanned = 0
    domains = domain_dirs()
    for dom in domains:
        dom_path = os.path.join(ROOT, dom)
        for dirpath, dirnames, filenames in os.walk(dom_path):
            dirnames[:] = [d for d in dirnames if d not in READONLY_DIRS]
            rel_dp = os.path.relpath(dirpath, ROOT)
            if rel_dp.startswith(os.path.join("09-流程规范", "工具")):
                dirnames[:] = []
                continue
            for fn in filenames:
                if not fn.lower().endswith(".md"):
                    continue
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, ROOT).replace("\\", "/")
                files_scanned += 1
                is_archive = ("/%s/" % ARCHIVE_DIR_NAME) in rel
                text = read_text_any(path)
                for ln, line in enumerate(text.splitlines(), 1):
                    for idx, col in scan_line(line, TOKENS):
                        hits_by_token[idx].append(
                            (rel, ln, line.strip()[:LINE_CUT], is_archive, col))

    total_hits = sum(len(v) for v in hits_by_token.values())
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    L = []
    L.append("# scan_deps报告-20260916（工具2 scan_deps.py 首跑）")
    L.append("")
    L.append("> 执行器层·主流软件工程·纯stdlib·禁API  ")
    L.append("> 运行时间：%s ｜ 扫描 md 文件数：%d ｜ 命中总计：%d" % (
        now, files_scanned, total_hits))
    L.append("")
    L.append("## 0. 本报告是什么")
    L.append("")
    L.append("「改常数 → 下游影响面」的机械演示：constants.yaml v1.0 判负/正名")
    L.append("之后，下列每条命中即一处仍引用旧口径的正文位置。归档件（09-归档）")
    L.append("只标注不要求改；其余命中按 M2/M3 整治计划消化。")
    L.append("")
    L.append("口径提醒：命中≠必改。部分命中是「负例警示引用」（如 启动包-最新.md")
    L.append("常数速览中『已判负/过时/已作废』的对照标注、constants.yaml deprecated")
    L.append("字段类条目），消化时须区分『残留旧口径』与『负例标注』，只改前者。")
    L.append("")
    L.append("## 0.5 总览")
    L.append("")
    L.append("| 令牌 | 口径 | 命中数 | 其中归档件 |")
    L.append("|---|---|---|---|")
    for idx, (tok, why) in enumerate(TOKENS):
        rows = hits_by_token[idx]
        arc = sum(1 for r in rows if r[3])
        L.append("| `%s` | %s | %d | %d |" % (tok, why, len(rows), arc))
    L.append("| **合计** |  | **%d** | **%d** |" % (
        total_hits, sum(sum(1 for r in v if r[3]) for v in hits_by_token.values())))
    for idx, (tok, why) in enumerate(TOKENS):
        rows = hits_by_token[idx]
        L.append("")
        L.append("## %d. 令牌 `%s` — 命中 %d 处" % (idx + 1, tok, len(rows)))
        L.append("")
        L.append("口径：%s" % why)
        L.append("")
        if rows:
            L.append("| # | 文件 | 行号 | 归档件 | 行内容（≤80字） |")
            L.append("|---|---|---|---|---|")
            for i, (rel, ln, frag, arc, _col) in enumerate(rows, 1):
                frag_md = frag.replace("|", "\\|")
                L.append("| %d | %s | %d | %s | %s |" % (
                    i, rel, ln, "是" if arc else "", frag_md))
        else:
            L.append("（无命中）")
    L.append("")
    L.append("---")
    L.append("参数化说明：令牌表位于脚本顶部 `TOKENS` 常量（含口径注释），")
    L.append("未来加 [constants:vX] 锚点扫描只需追加条目，报告节随表自动再生。")
    L.append("标签：执行器层·主流软件工程（命中≠物理判断，仅引用面机械账）。")

    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")

    print("=== scan_deps.py 完成 ===")
    print("扫描 md: %d" % files_scanned)
    for idx, (tok, _why) in enumerate(TOKENS):
        arc = sum(1 for r in hits_by_token[idx] if r[3])
        print("  %-18s 命中 %3d（归档 %d）" % (tok, len(hits_by_token[idx]), arc))
    print("合计命中: %d" % total_hits)
    print("报告: %s" % REPORT_PATH)


if __name__ == "__main__":
    main()
