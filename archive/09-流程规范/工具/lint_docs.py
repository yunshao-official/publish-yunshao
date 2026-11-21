# -*- coding: utf-8 -*-
# 执行器层·主流软件工程·纯stdlib·禁API
"""
lint_docs.py — 全库文档 lint（工具1）
=====================================
范围：H:\\理论存档 下 18 个域目录（00-其他 … 17-物理预测）的全部 .md。
排除：
  1) 只读区（绝不扫描）：_归档-已整合-20260726 / backup_20260725 /
     backup_20260726_pre-attack / 归档-旧常数体系-20260731 / 云韶备份；
  2) 各域 09-归档 二级目录内容（归档件豁免，仅计数）；
  3) _归位清单*.md（归位过程件豁免，仅计数）；
  4) 本工具目录与工具报告目录（自指豁免，报告注明）。
检查项：
  ① 有 YAML front matter（文件以 --- 开头）且含 title / date / status 三键；
  ② status ∈ 白名单（主标签口径：完整值或其“·”前主标签在白名单即合规，
     扩展标签如实记录）；
  ③ 正文（去 front matter、去空白字符后）≤ 5000 字，超出仅 WARN 不算违规。
输出：lint报告-20260916.md（违规清单 路径|缺什么、豁免说明、统计）。
用法：python lint_docs.py   （只读扫描，不修改任何文档）
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
REPORT_PATH = os.path.join(REPORT_DIR, "lint报告-20260916.md")

READONLY_DIRS = {
    "_归档-已整合-20260726",
    "backup_20260725",
    "backup_20260726_pre-attack",
    "归档-旧常数体系-20260731",
    "云韶备份",
}
ARCHIVE_DIR_NAME = "09-归档"          # 域内归档二级目录：豁免
EXEMPT_FILE_RE = re.compile(r"^_归位清单")  # 域根归位清单：豁免
BODY_CHAR_LIMIT = 5000                 # 正文上限，超出仅 WARN

VALID_STATUS = [
    "定稿", "内部版", "对外版", "复算一致", "体系内部定义·未验证",
    "理论参照·非实测", "已判负", "已封存", "已作废", "草案",
]
VALID_STATUS_SET = set(VALID_STATUS)
STATUS_SPLIT_RE = re.compile(r"[·/／:：,，;；\s]")


def domain_dirs():
    """发现域目录：根下以两位数字- 开头的目录。"""
    out = []
    for name in sorted(os.listdir(ROOT)):
        p = os.path.join(ROOT, name)
        if re.match(r"^\d{2}-", name) and os.path.isdir(p):
            out.append(name)
    return out


def read_text_any(path):
    """utf-8 优先，退 gbk；不因编码崩。"""
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def parse_front_matter(text):
    """返回 (fm_dict|None, body_text, has_fm_block)。
    fm_dict 记录出现的 key -> 原始值串（简单行解析，不做完整 YAML）。"""
    t = text.lstrip("\ufeff")
    lines = t.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, t, False
    fm = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body = "\n".join(lines[i + 1:])
            return fm, body, True
        m = re.match(r"^([A-Za-z_][\w\-]*)\s*:", line)
        if m:
            fm.setdefault(m.group(1), line.split(":", 1)[1].strip().strip("'\""))
    # 只有开 --- 没有闭 ---：视作缺格
    return fm, t, False


def status_verdict(raw_status):
    """返回 (ok, main_label, full_value)。主标签口径见文件头。"""
    v = (raw_status or "").strip().strip("'\"").strip()
    if not v:
        return False, "", ""
    if v in VALID_STATUS_SET:
        return True, v, v
    main = STATUS_SPLIT_RE.split(v)[0].strip()
    if main in VALID_STATUS_SET:
        return True, main, v
    return False, main, v


def main():
    violations = []   # (relpath, problem)
    warns = []        # (relpath, msg)
    stats = {"total": 0, "ok": 0, "violation": 0, "warn": 0,
             "exempt_archive": 0, "exempt_guiwei": 0}
    status_ext_used = []   # 扩展标签记录

    domains = domain_dirs()
    for dom in domains:
        dom_path = os.path.join(ROOT, dom)
        for dirpath, dirnames, filenames in os.walk(dom_path):
            # prune：域内归档二级目录（内容豁免，含其子目录全部 md 递归计数）
            if os.path.basename(dirpath) == ARCHIVE_DIR_NAME:
                for adp, adns, afns in os.walk(dirpath):
                    stats["exempt_archive"] += sum(
                        1 for fn in afns if fn.lower().endswith(".md"))
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if d not in READONLY_DIRS]
            # 工具/工具报告自指豁免
            rel_dp = os.path.relpath(dirpath, ROOT)
            if rel_dp.startswith(os.path.join("09-流程规范", "工具")):
                dirnames[:] = []
                continue
            for fn in filenames:
                if not fn.lower().endswith(".md"):
                    continue
                if EXEMPT_FILE_RE.match(fn):
                    stats["exempt_guiwei"] += 1
                    continue
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, ROOT)
                stats["total"] += 1
                text = read_text_any(path)
                fm, body, has_fm = parse_front_matter(text)
                problems = []
                if not has_fm:
                    problems.append("缺YAML front matter（--- 开头块）")
                else:
                    missing = [k for k in ("title", "date", "status") if k not in fm]
                    if missing:
                        problems.append("front matter缺键: " + "+".join(missing))
                    ok, main_lb, full_v = status_verdict(fm.get("status", ""))
                    if "status" in fm and not ok:
                        problems.append(
                            "status不在白名单: %r" % fm.get("status"))
                    elif ok and full_v not in VALID_STATUS_SET:
                        status_ext_used.append((rel, full_v))
                if problems:
                    stats["violation"] += 1
                    violations.append((rel, "；".join(problems)))
                else:
                    stats["ok"] += 1
                chars = len(re.sub(r"\s+", "", body))
                if chars > BODY_CHAR_LIMIT:
                    stats["warn"] += 1
                    warns.append((rel, "正文 %d 字 > %d 字（WARN仅提示）"
                                  % (chars, BODY_CHAR_LIMIT)))

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    L = []
    L.append("# lint报告-20260916（工具1 lint_docs.py 首跑）")
    L.append("")
    L.append("> 执行器层·主流软件工程·纯stdlib·禁API  ")
    L.append("> 运行时间：%s ｜ 扫描根：%s" % (now, ROOT))
    L.append("")
    L.append("## 1. 统计")
    L.append("")
    L.append("| 指标 | 数值 |")
    L.append("|---|---|")
    L.append("| 扫描 md 总数（应检） | %d |" % stats["total"])
    L.append("| 合规 | %d |" % stats["ok"])
    L.append("| 违规 | %d |" % stats["violation"])
    L.append("| WARN（正文超5000字，仅提示） | %d |" % stats["warn"])
    L.append("| 豁免：09-归档 归档件 | %d |" % stats["exempt_archive"])
    L.append("| 豁免：_归位清单* | %d |" % stats["exempt_guiwei"])
    L.append("| 域目录数 | %d |" % len(domains))
    L.append("")
    L.append("## 2. 违规清单（路径 | 缺什么）")
    L.append("")
    if violations:
        L.append("| # | 路径 | 问题 |")
        L.append("|---|---|---|")
        for i, (rel, prob) in enumerate(violations, 1):
            L.append("| %d | %s | %s |" % (i, rel.replace("\\", "/"), prob))
    else:
        L.append("（无违规）")
    L.append("")
    L.append("## 3. WARN 清单（正文超 5000 字，不算违规）")
    L.append("")
    if warns:
        L.append("| # | 路径 | 正文有效字符数 |")
        L.append("|---|---|---|")
        for i, (rel, msg) in enumerate(warns, 1):
            L.append("| %d | %s | %s |" % (i, rel.replace("\\", "/"), msg))
    else:
        L.append("（无 WARN）")
    L.append("")
    L.append("## 4. 豁免说明")
    L.append("")
    L.append("1. 只读区五处（_归档-已整合-20260726、backup_20260725、")
    L.append("   backup_20260726_pre-attack、归档-旧常数体系-20260731、云韶备份）")
    L.append("   一律不扫描不修改。")
    L.append("2. 各域 09-归档 二级目录内容豁免（归档件不受新格式约束），")
    L.append("   本次豁免 %d 个 md，仅计数。" % stats["exempt_archive"])
    L.append("3. _归位清单*.md 豁免（归位过程件），本次豁免 %d 个。" % stats["exempt_guiwei"])
    L.append("4. 09-流程规范\\工具\\ 与 09-流程规范\\工具报告\\ 自指豁免")
    L.append("   （工具与本报告自身不受检）。")
    L.append("5. status 判定口径：完整值精确命中白名单为合规；形如")
    L.append("   「定稿·内洽版」按「·」前主标签命中亦判合规，扩展标签如实")
    L.append("   记录于第 5 节。")
    L.append("")
    L.append("## 5. 扩展标签记录（主标签合规·完整值超出白名单）")
    L.append("")
    if status_ext_used:
        L.append("| # | 路径 | status 完整值 |")
        L.append("|---|---|---|")
        for i, (rel, v) in enumerate(status_ext_used, 1):
            L.append("| %d | %s | %s |" % (i, rel.replace("\\", "/"), v))
    else:
        L.append("（无）")
    L.append("")
    L.append("---")
    L.append("标签：执行器层·主流软件工程（lint 规则与白名单以 constants.yaml")
    L.append("v1.0 status_labels 为准；文档内容物理未验证）。")

    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")

    print("=== lint_docs.py 完成 ===")
    print("扫描: %d  合规: %d  违规: %d  WARN: %d" % (
        stats["total"], stats["ok"], stats["violation"], stats["warn"]))
    print("豁免: 归档件 %d, 归位清单 %d" % (
        stats["exempt_archive"], stats["exempt_guiwei"]))
    print("报告: %s" % REPORT_PATH)


if __name__ == "__main__":
    main()
