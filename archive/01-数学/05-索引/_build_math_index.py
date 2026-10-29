# -*- coding: utf-8 -*-
"""生成 01-数学 文件总表 / 版本链 / 统计。只读扫描，不移动文件。"""
import csv, json, os, re, sys
from pathlib import Path

ROOT = Path(r"H:\理论存档\01-数学")
OUT = ROOT / "05-索引"

SKIP_DIRS = {".mimosa", ".git", "node_modules", ".venv", "venv", "site-packages",
             "__pycache__", "dist", "build", ".next", ".cache", "checkpoints"}
SCAN_AREAS = ["00-正本", "01-理论与推导", "02-实验与数据", "03-论文与对外",
              "04-工具与代码", "05-索引", "内部版", "哈工大版",
              "09-归档", "归档-旧常数体系", "理论极致-20260911-附件"]
KEEP_EXT = {".md", ".docx", ".py", ".yaml", ".yml", ".csv", ".json", ".txt", ".tex", ".pdf"}

DATE_RE = re.compile(r"(20\d{2})(\d{2})(\d{2})")
VER_RE = re.compile(r"[vV](\d+(?:\.\d+)*)")

TOPIC_RULES = [
    ("黎曼猜想/L函数", ["RH", "黎曼", "L函数", "L₂", "L₅", "零点", "Ribet", "塔"]),
    ("素数/χ覆盖", ["χ覆盖", "素数", "进位签名", "MZV", "振幅"]),
    ("代数", ["代数", "签名族", "Kummer", "商化"]),
    ("几何", ["几何", "H₁", "M³⁶", "环面管", "拓扑分类"]),
    ("拓扑学", ["拓扑"]),
    ("数论", ["数论", "哥德巴赫", "ζ"]),
    ("概率论", ["概率", "Haar", "Doeblin", "遍历"]),
    ("群论", ["群论", "PSL", "S₃", "S₄"]),
    ("范畴论", ["范畴", "Ore", "quantale"]),
    ("调和分析", ["调和"]),
    ("非交换几何", ["非交换"]),
    ("计算体系", ["计算体系", "Lean", "FTIR", "D1", "D2"]),
    ("概念宇宙/LLM", ["概念宇宙", "概念理论", "语义等价类", "全息零点", "trigram",
                      "J-CC", "J-H", "J-U", "universe", "语言观", "LLM", "投影折叠"]),
    ("哈密顿路径", ["哈密顿", "HP", "gpipe", "M1", "m4", "EXIT127"]),
    ("超导/Tc", ["超导", "Tc", "O_h"]),
    ("常数体系", ["常数", "α(N)", "f_defect", "N2", "N=0", "N=2"]),
    ("因果/生命", ["因果签名", "生命链"]),
    ("AI保密", ["AI保密", "保密"]),
    ("紫微斗数", ["紫微"]),
    ("材料/高维", ["高维", "材料", "缺陷", "写入"]),
]

KIND_RULES = [
    ("归档", ["归档", "备份", "bak", "旧常数"]),
    ("对外/论文", ["大论文", "论文", "对外", "哈工大版"]),
    ("正本/裁决", ["正本", "裁决", "定纲", "基准常数", "总表", "公式总表", "封存", "定案"]),
    ("预注册/判据", ["预注册", "判据", "冻结书"]),
    ("执行报告", ["执行报告", "执行记", "运行记录", "报告", "记录", "台账", "结果"]),
    ("立案/方案", ["立案", "方案", "纲领", "任务书", "计划", "路线", "架构", "图谱", "对接", "研究"]),
    ("内部版", ["内部版"]),
    ("工具/代码", ["脚本", "工具", "引擎", "求解器", "库"]),
    ("索引/目录", ["索引", "总索引", "目录"]),
]


def parse_name(stem):
    date = ""
    m = DATE_RE.search(stem)
    if m:
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    vers = VER_RE.findall(stem)
    ver = ""
    if vers:
        def key(v):
            return tuple(int(x) for x in v.split("."))
        ver = max(vers, key=key)
    base = DATE_RE.sub("", stem)
    base = re.sub(r"[-_ ]*[vV]\d+(?:\.\d+)*", "", base)
    base = re.sub(r"[-_ ]+", " ", base).strip(" -_")
    return base, ver, date


def read_head(p, limit=20000):
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")[:limit]
    except Exception:
        return "", {}, ""
    title = ""
    m = re.search(r"^#\s+(.+)$", txt, re.M)
    if m:
        title = m.group(1).strip()
    fm = {}
    if txt.startswith("---"):
        parts = txt.split("---", 2)
        if len(parts) >= 3:
            block = parts[1]
            for line in block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip().lower()] = v.strip().strip('"\'')
            body = parts[2]
        else:
            body = txt
    else:
        body = txt
    status = fm.get("status", "")
    if not status:
        m = re.search(r"状态[=：:]\s*([^｜|\n]{2,60})", body)
        if m:
            status = m.group(1).strip()
    summary = fm.get("summary", "") or fm.get("描述", "") or fm.get("description", "")
    if not summary:
        m = re.search(r"摘\s*要[=：:]\s*([^｜|\n]{10,300})", body)
        if m:
            summary = m.group(1).strip()
    return title, {"summary": summary, "status": status, "tags": fm.get("tags", "")}, body


def classify_topic(path, title, body):
    hay = f"{path} {title} {body[:3000]}"
    hits = []
    for topic, kws in TOPIC_RULES:
        score = sum(hay.count(k) for k in kws)
        if score:
            hits.append((score, topic))
    hits.sort(reverse=True)
    return hits[0][1] if hits else "其他"


def classify_kind(path, stem):
    hay = f"{path} {stem}"
    for kind, kws in KIND_RULES:
        if any(k in hay for k in kws):
            return kind
    return "其他"


def should_scan(p: Path):
    parts = set(p.parts)
    if parts & SKIP_DIRS:
        return False
    if p.suffix.lower() not in KEEP_EXT:
        return False
    rel = p.relative_to(ROOT).as_posix()
    if rel.startswith("04-工具与代码/"):
        depth = len(p.relative_to(ROOT).parts)
        if depth > 4:
            return False
        if p.suffix.lower() in {".json", ".csv", ".txt"} and "results" not in rel:
            return False
    return True


def main():
    rows = []
    for area in SCAN_AREAS:
        adir = ROOT / area
        if not adir.exists():
            continue
        for p in adir.rglob("*"):
            if not p.is_file() or not should_scan(p):
                continue
            rel = p.relative_to(ROOT).as_posix()
            stem = p.stem
            title, meta, body = ("", {}, "") if p.suffix.lower() not in {".md", ".txt"} else read_head(p)
            base, ver, date = parse_name(stem)
            st = p.stat()
            if not date:
                import datetime
                date = datetime.date.fromtimestamp(st.st_mtime).isoformat()
            topic = classify_topic(rel, title or stem, body)
            kind = classify_kind(rel, stem)
            rows.append({
                "path": rel, "area": area, "ext": p.suffix.lower().lstrip("."),
                "family": base, "version": ver, "date": date,
                "title": title or stem, "kind": kind, "topic": topic,
                "status": meta.get("status", ""), "summary": meta.get("summary", ""),
                "size": st.st_size,
            })

    # 版本链：同 area+family 内，按 version/date 选最新
    groups = {}
    for r in rows:
        if r["ext"] != "md":
            continue
        groups.setdefault((r["area"], r["family"]), []).append(r)
    latest = set()
    for k, g in groups.items():
        def vkey(r):
            v = r["version"]
            vt = tuple(int(x) for x in v.split(".")) if v else (-1,)
            return (vt, r["date"])
        best = max(g, key=vkey)
        latest.add(best["path"])
    for r in rows:
        r["is_latest"] = (r["ext"] != "md") or (r["path"] in latest)

    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "数学文件总表-v1.0-20261027.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (OUT / "数学文件总表-v1.0-20261027.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    # 版本链报告
    multi = {k: v for k, v in groups.items() if len(v) > 1}
    lines = ["# 数学文件版本链（自动归并）", "",
             f"> 生成 2026-10-27｜扫描 {len(rows)} 件｜md 族 {len(groups)} 个｜多版本族 {len(multi)} 个", "",
             "| 目录 | 文件族 | 件数 | 最新件 |", "|---|---|---|---|"]
    for (area, fam), g in sorted(multi.items(), key=lambda x: -len(x[1])):
        best = max(g, key=lambda r: ((tuple(int(x) for x in r["version"].split(".")) if r["version"] else (-1,)), r["date"]))
        lines.append(f"| {area} | {fam} | {len(g)} | {best['path']} |")
    (OUT / "数学版本链-v1.0-20261027.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 控制台统计
    from collections import Counter
    print("files:", len(rows))
    print("by area:", Counter(r["area"] for r in rows).most_common())
    print("by kind:", Counter(r["kind"] for r in rows).most_common())
    print("by topic:", Counter(r["topic"] for r in rows).most_common())
    print("md families:", len(groups), "multi-version:", len(multi))
    print("latest md:", sum(1 for r in rows if r["ext"] == "md" and r["is_latest"]))


if __name__ == "__main__":
    main()
