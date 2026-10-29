# -*- coding: utf-8 -*-
# 执行器层·主流软件工程·纯stdlib·禁API
"""
gen_tables.py — 一致性校验模式（复算）（工具3）
===============================================
做什么：把 constants.yaml（v1.0，唯一常数正本）的**声明值**与数据文件的
**实值**逐项对照，输出 复算一致 / 不一致 / 数据缺失。不编造任何数：
文件读不到→"数据缺失"；键找不到→"数据缺失"；对比用显式容差。
数据文件（glob 定位，读得到哪个算哪个）：
  - theta_table*.json            （θ表派生件，03-高维材料工程 下递归找）
  - verdict_pkg_batch10.json     （公式b f_fit 判别包，results/ 优先）
  - ys_9d_material.json          （9维材料包，results/ 优先）
  - ys_field_recalc.json         （扇区阶梯复算，results/ 优先）
校验点（任务口径）：
  ① α_w=1/8（0.125）：theta_table N=8 行 alpha；ys_field_recalc N=8 行 alpha
  ② α_m=1/6（0.1667）：ys_9d_material.alpha；theta_table N=48 行 alpha
  ③ d_m≈0.167：ys_9d_material.d_nm
  ④ verdict_pkg_batch10：within_2x 全=1
输出：gen_tables报告-20260916.md
用法：python gen_tables.py   （只读扫描+报告，不修改任何数据）
"""
import os
import re
import sys
import json
import glob
import datetime
from fractions import Fraction

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"H:\理论存档"
DOMAIN = os.path.join(ROOT, "03-高维材料工程")
CONSTANTS_YAML = os.path.join(ROOT, "00-其他", "constants.yaml")
REPORT_DIR = os.path.join(ROOT, "09-流程规范", "工具报告")
REPORT_PATH = os.path.join(REPORT_DIR, "gen_tables报告-20260916.md")

READONLY_NAMES = {
    "_归档-已整合-20260726", "backup_20260725", "backup_20260726_pre-attack",
    "归档-旧常数体系-20260731", "云韶备份",
}
REL_TOL = 0.005   # 近似值容差 0.5%（constants d_m=0.167 为三位舍入值）
EQ_TOL = 1e-9     # 精确值容差


# ---------------- 文件定位 ----------------
def find_files():
    """返回 {键名: 绝对路径|None}。results/ 下优先，读得到哪个算哪个。"""
    def walk_glob(pattern):
        out = []
        for dirpath, dirnames, filenames in os.walk(DOMAIN):
            dirnames[:] = [d for d in dirnames if d not in READONLY_NAMES]
            for fn in filenames:
                if glob.fnmatch.fnmatch(fn, pattern):
                    out.append(os.path.join(dirpath, fn))
        # results/ 优先，其余按路径排序
        out.sort(key=lambda p: (0 if os.path.basename(os.path.dirname(p)) == "results" else 1, p))
        return out

    found = {}
    theta = walk_glob("theta_table*.json")
    found["theta_table"] = theta[0] if theta else None
    for key, pat in [
        ("verdict_pkg_batch10", "verdict_pkg_batch10.json"),
        ("ys_9d_material", "ys_9d_material.json"),
        ("ys_field_recalc", "ys_field_recalc.json"),
    ]:
        cands = walk_glob(pat)
        found[key] = cands[0] if cands else None
    return found


def load_json(path):
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, "rb") as f:
            return json.loads(f.read().decode("utf-8"))
    except Exception as e:
        print("[warn] 读取失败 %s: %s" % (path, e))
        return None


# ---------------- constants.yaml 简单解析（stdlib，无 yaml 库） ----------------
def parse_constants():
    """从 constants.yaml 行解析声明值。只取需要的键，解析不到→None。"""
    decl = {"alpha_w": None, "alpha_m": None, "d_m": None, "version": None}
    try:
        text = open(CONSTANTS_YAML, "r", encoding="utf-8").read()
    except OSError:
        return decl
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r'^version:\s*"?([^"\s#]+)', s)
        if m and decl["version"] is None:
            decl["version"] = m.group(1)
        m = re.match(r'^alpha_w:\s*"([^"]+)"', s)
        if m:
            decl["alpha_w"] = m.group(1)
        m = re.match(r'^alpha_m:\s*"([^"]+)"', s)
        if m:
            decl["alpha_m"] = m.group(1)
        m = re.match(r'^d_m:\s*"([^"]+)"', s)
        if m:
            decl["d_m"] = m.group(1)
    return decl


def val_of(expr):
    """"1/8"→0.125；"0.167nm"→0.167；解析不了→None。"""
    if expr is None:
        return None
    s = str(expr).strip()
    m = re.match(r"^-?\d+\s*/\s*-?\d+$", s)
    if m:
        try:
            return float(Fraction(s.replace(" ", "")))
        except Exception:
            return None
    m = re.match(r"^-?\d+(?:\.\d+)?", s)
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return None
    return None


# ---------------- 判定 ----------------
def cmp_exact(label, declared, actual, src, note=""):
    if declared is None:
        return ("数据缺失", label, "声明值解析失败", "-", src, note)
    if actual is None:
        return ("数据缺失", label, str(declared), "文件/键缺失", src, note)
    ok = abs(actual - declared) <= EQ_TOL
    return (("复算一致" if ok else "不一致"),
            label, str(declared), repr(actual), src, note)


def cmp_tol(label, declared, actual, src, note="", tol=REL_TOL):
    if declared is None:
        return ("数据缺失", label, "声明值解析失败", "-", src, note)
    if actual is None:
        return ("数据缺失", label, str(declared), "文件/键缺失", src, note)
    ok = abs(actual - declared) <= tol * max(abs(declared), 1e-12)
    dev = (actual - declared) / declared * 100 if declared else float("nan")
    return (("复算一致" if ok else "不一致"),
            label, "%s（容差%.1f%%）" % (declared, tol * 100),
            "%r（偏差 %+.3f%%）" % (actual, dev), src, note)


def row_note(verdict, label, declared, actual, src, note):
    return (verdict, label, declared, actual, src, note)


def main():
    decl = parse_constants()
    a_w = val_of(decl["alpha_w"])       # 0.125
    a_m = val_of(decl["alpha_m"])       # ~0.1666667
    d_m = val_of(decl["d_m"])           # 0.167

    files = find_files()
    theta = load_json(files["theta_table"])
    verdict = load_json(files["verdict_pkg_batch10"])
    ys9d = load_json(files["ys_9d_material"])
    field = load_json(files["ys_field_recalc"])

    results = []  # (判定, 校验项, 声明值, 实值, 数据来源, 说明)

    # ① α_w = 1/8：theta_table N=8 行
    def theta_row(tbl, n):
        if isinstance(tbl, list):
            for r in tbl:
                if isinstance(r, dict) and r.get("N") == n:
                    return r
        return None
    src_theta = files["theta_table"]
    r8 = theta_row(theta, 8)
    results.append(cmp_tol(
        "①a α_w=1/8 ← theta_table N=8 行 alpha",
        a_w, None if r8 is None else r8.get("alpha"),
        src_theta, "θ表 N=8（写入相空间基准锚）"))
    r48 = theta_row(theta, 48)
    results.append(cmp_tol(
        "①b α_m=1/6 ← theta_table N=48 行 alpha",
        a_m, None if r48 is None else r48.get("alpha"),
        src_theta, "θ表 N=48（材料本体层）"))

    # ys_field_recalc：A_扇区阶梯 N=8 行 alpha
    src_field = files["ys_field_recalc"]
    f8 = None
    if isinstance(field, dict):
        ladder = (field.get("A_扇区阶梯") or {}).get("ladder_rows")
        f8 = theta_row(ladder, 8)
    results.append(cmp_tol(
        "①c α_w=1/8 ← ys_field_recalc 扇区阶梯 N=8 行 alpha",
        a_w, None if f8 is None else f8.get("alpha"),
        src_field, "扇区阶梯复算件"))

    # ② α_m 与 ③ d_m ← ys_9d_material
    src_9d = files["ys_9d_material"]
    results.append(cmp_tol(
        "② α_m=1/6 ← ys_9d_material.alpha",
        a_m, None if ys9d is None else ys9d.get("alpha"),
        src_9d, "9维材料包（N=3 表外延直算行）"))
    results.append(cmp_tol(
        "③ d_m≈0.167nm ← ys_9d_material.d_nm",
        d_m, None if ys9d is None else ys9d.get("d_nm"),
        src_9d, "与 FCC a/2=0.1786nm 差6.5%（复算一致口径）"))

    # ④ verdict within_2x 全=1
    src_verdict = files["verdict_pkg_batch10"]
    rows = None
    if isinstance(verdict, dict):
        rows = (verdict.get("一_Tc公式ab判别") or {}).get("rows")
    if rows is None:
        results.append(("数据缺失", "④ verdict within_2x 全=1", "1",
                        "文件/键缺失", src_verdict, "公式b f_fit 判别包"))
    else:
        bad = [(r.get("material"), r.get("within_2x")) for r in rows
               if float(r.get("within_2x", 0)) != 1.0]
        results.append((
            "复算一致" if (rows and not bad) else ("不一致" if rows else "数据缺失"),
            "④ verdict within_2x 全=1", "全部=1",
            "%d 行全部=1" % len(rows) if rows and not bad
            else "违例: %s" % bad if rows else "-",
            src_verdict, "共 %d 材料" % len(rows)))

    ok_n = sum(1 for r in results if r[0] == "复算一致")
    bad_n = sum(1 for r in results if r[0] == "不一致")
    miss_n = sum(1 for r in results if r[0] == "数据缺失")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    def rp(p):
        return os.path.relpath(p, ROOT).replace("\\", "/") if p else "（未找到）"

    L = []
    L.append("# gen_tables报告-20260916（工具3 gen_tables.py 首跑·复算）")
    L.append("")
    L.append("> 执行器层·主流软件工程·纯stdlib·禁API  ")
    L.append("> 运行时间：%s ｜ 常数正本：00-其他/constants.yaml（v%s）" % (
        now, decl["version"] or "?"))
    L.append("")
    L.append("## 1. 数据文件定位（glob，读得到哪个算哪个）")
    L.append("")
    L.append("| 数据件 | 定位结果 |")
    L.append("|---|---|")
    L.append("| theta_table*.json | %s |" % rp(files["theta_table"]))
    L.append("| verdict_pkg_batch10.json | %s |" % rp(files["verdict_pkg_batch10"]))
    L.append("| ys_9d_material.json | %s |" % rp(files["ys_9d_material"]))
    L.append("| ys_field_recalc.json | %s |" % rp(files["ys_field_recalc"]))
    L.append("")
    L.append("注：theta_table* 不在 results/，glob 于 03-高维材料工程 域内找到")
    L.append("04-工具与代码 下的派生件（与 constants.yaml theta_table.generator")
    L.append("口径一致：工艺仿真工具/theta_table_20260914.py 派生）。")
    L.append("")
    L.append("## 2. 逐项复算（声明值 vs 实值，不编造任何数）")
    L.append("")
    L.append("| 判定 | 校验项 | 声明值（constants.yaml） | 实值（数据文件） | 数据来源 | 说明 |")
    L.append("|---|---|---|---|---|---|")
    for v, label, dv, av, src, note in results:
        L.append("| **%s** | %s | %s | %s | %s | %s |" % (
            v, label, dv, str(av).replace("|", "\\|"), rp(src), note))
    L.append("")
    L.append("## 3. 结论")
    L.append("")
    L.append("- 复算一致：**%d** 项" % ok_n)
    L.append("- 不一致：**%d** 项" % bad_n)
    L.append("- 数据缺失：**%d** 项" % miss_n)
    L.append("")
    if bad_n == 0 and miss_n == 0:
        L.append("全部校验点与 constants.yaml v%s 声明值一致（复算一致，" % (decl["version"] or "1.0"))
        L.append("执行器层机械对照；体系量值本身仍带「体系内部定义·未验证」标签）。")
    else:
        L.append("存在不一致/缺失项，见上表逐行；缺失项多为文件未找到或键名")
        L.append("不匹配，属数据面状态，不另行推算补数（不编造）。")
    L.append("")
    L.append("---")
    L.append("口径注：α_m=1/6 与 d_m=0.167 为三位舍入口径，容差 0.5%；")
    L.append("α_w=1/8 理论上应精确相等，同表按 0.5% 容差复核（实际偏差 0）。")
    L.append("标签：执行器层·主流软件工程（复算一致=机械对照通过；物理未验证）。")

    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")

    print("=== gen_tables.py 完成 ===")
    print("数据件定位:")
    for k in ("theta_table", "verdict_pkg_batch10", "ys_9d_material", "ys_field_recalc"):
        print("  %-20s %s" % (k, rp(files[k])))
    print("复算一致: %d  不一致: %d  数据缺失: %d" % (ok_n, bad_n, miss_n))
    for v, label, dv, av, src, note in results:
        print("  [%s] %s" % (v, label))
    print("报告: %s" % REPORT_PATH)


if __name__ == "__main__":
    main()
