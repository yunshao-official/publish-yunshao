# -*- coding: utf-8 -*-
"""
全库口径体检工具 constants_audit v1.0（知世问"如何永久杜绝"·三层防线第一层）
==============================================================================
功能：扫描理论存档全部 md，按"已知坏口径模式库"检出前裁决时代遗留错误，产出分级体检清单。
性质：只读扫描（不改任何文件）；确定性可复跑。
模式库 v1.0（随 P0 裁决/勘误案例持续扩充）：
  红线-已判负Tc公式a族：832.7 / 952.7 / 952.6 / 350/√ / 490.098 / 公式a（无判负语境难判，整串计）
  红线-已作废频率：280THz / 800THz
  红线-未验证声称标"实测"：600K（实测 类
  黄线-旧推导层混：M=64乘 / M=64× / 放大倍数M=64 / 热频率
  黄线-基准频率语境待审：373THz（本身是 f₀ 当前值合法引用，需人工看语境是否误作写入源/THz频段）
  黄线-缺摘要头：md 前 12 行无 summary 且无 摘要
排除：目录名含 归档/backup/_bak/云韶备份 的只读区（单独计数不体检）。
输出：JSON（results）+ 本脚本 stdout 摘要。报告 MD 由主线程撰写。
"""
import os, json, hashlib
from pathlib import Path

BASE = Path(r"H:\理论存档").resolve()
OUT_DIR = Path(r"H:\理论存档\09-流程规范\工具报告").resolve()
OUT_NAME = "全库口径体检-raw-v1.0-20260919.json"

EXCLUDE_KEYS = ("归档", "backup", "_bak", "云韶备份")

PATTERNS = {
    "红线-Tc公式a族": ["832.7", "952.7", "952.6", "350/√", "Tc = 350", "490.098", "公式a"],
    "红线-已作废频率": ["280THz", "800THz"],
    "红线-声称标实测": ["600K（实测", "600K(实测", "600K实测"],
    "黄线-旧推导层混": ["M=64乘", "M=64×", "放大倍数M=64", "热频率"],
    "黄线-373THz语境": ["373THz"],
}


def is_excluded(p: Path) -> bool:
    return any(k in str(p) for k in EXCLUDE_KEYS)


def has_summary_head(text_lines):
    head = "\n".join(text_lines[:12])
    return ("summary" in head) or ("摘要" in head)


def main():
    files_scanned, excluded_cnt, no_head, hits = 0, 0, [], {}
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if "归档" not in d and "backup" not in d]
        for fn in files:
            if not fn.endswith(".md"):
                continue
            fp = Path(root) / fn
            if is_excluded(fp):
                excluded_cnt += 1
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            files_scanned += 1
            lines = text.splitlines()
            if not has_summary_head(lines):
                no_head.append(str(fp.relative_to(BASE)))
            file_hits = {}
            for cat, pats in PATTERNS.items():
                cnts = {}
                for pat in pats:
                    c = text.count(pat)
                    if c:
                        cnts[pat] = c
                if cnts:
                    file_hits[cat] = cnts
            if file_hits:
                hits[str(fp.relative_to(BASE))] = file_hits

    result = {
        "snapshot": "20260919",
        "base": str(BASE),
        "files_scanned": files_scanned,
        "excluded_readonly_cnt": excluded_cnt,
        "no_summary_head_cnt": len(no_head),
        "no_summary_head_sample": no_head[:40],
        "hit_files_cnt": len(hits),
        "hits": hits,
        "sha256": hashlib.sha256(json.dumps(hits, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16],
        "note": "只读扫描；红线=已判负口径数值（须逐份处置）；黄线=需语境人工审查；缺摘要头=文件纪律合规缺口",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = (OUT_DIR / OUT_NAME).resolve()
    out_path.relative_to(BASE)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print("扫描md:", files_scanned, "| 只读排除:", excluded_cnt)
    print("命中文件数:", len(hits), "| 缺摘要头:", len(no_head))
    print("结果已写:", str(out_path))


if __name__ == "__main__":
    main()
