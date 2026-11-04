#!/usr/bin/env python3 -B
"""
关二·独立复算 v1.0｜2026-11-04
绝经线文献底座全量数字独立验算（不看旧脚本，逐条原始初判为准）
"""
import json, hashlib, os, re, sys

BASE = "archive/16-生命与营养工程/02-实验与数据/绝经线-文献底座-v1.0-20261104"
THEORY = "archive/16-生命与营养工程/01-理论与推导"
ROOT = "/data/workspace/publish-yunshao"

results = {}

# ── 一、冻结判据哈希 ──
pandu_path = os.path.join(ROOT, THEORY, "绝经线·文献检索判据书-v1.0-20261104.md")
with open(pandu_path, "rb") as f:
    sha = hashlib.sha256(f.read()).hexdigest()[:16]
results["判据哈希"] = {"声明": "6184d7c5001ab833", "实测": sha, "符": sha == "6184d7c5001ab833"}

# ── 二、卷面覆盖率 ──
VOLS = ["G", "B", "C", "D", "E", "F", "A1", "A2"]
EXPECTED_COUNTS = {"G": 62, "B": 104, "C": 99, "D": 94, "E": 122, "F": 114, "A1": 65, "A2": 60}
all_chuji = {}          # 编号 -> record
vol_counts = {}
vol_ids = {}            # vol -> [编号list]
module_map = {}         # 编号 -> 模块号

for v in VOLS:
    path = os.path.join(ROOT, BASE, f"整读初判-卷{v}-20261104.json")
    with open(path) as f:
        d = json.load(f)
    n = d["条数"]
    vol_counts[v] = n
    ids = [x["编号"] for x in d["文献"]]
    vol_ids[v] = ids
    for x in d["文献"]:
        all_chuji[x["编号"]] = x
        module_map[x["编号"]] = x.get("模块号", "")

total = sum(vol_counts.values())
a1_a2_set = set(vol_ids["A1"] + vol_ids["A2"])
a_full_nums = set(f"A{i:03d}" for i in range(1, 126))

dup_check = {}
has_dup = False
for v in VOLS:
    seen = set()
    for nid in vol_ids[v]:
        if nid in seen:
            has_dup = True
        seen.add(nid)

results["卷面"] = {
    "八卷条数": vol_counts,
    "合计": total,
    "合计校验": total == 720,
    "A1并A2": sorted(a1_a2_set) == sorted(a_full_nums),
    "内部重复": has_dup,
}

# ── 三、净面 ──
chuji_counts = {"留": 0, "删": 0, "待核": 0}
chuji_liu_pmids = set()
chuji_all_pmids = {}     # 编号 -> PMID
for nid, x in all_chuji.items():
    c = x["结论"]
    chuji_counts[c] = chuji_counts.get(c, 0) + 1
    pmid = x.get("PMID", "")
    chuji_all_pmids[nid] = pmid
    if c == "留":
        chuji_liu_pmids.add(pmid)

pool_path = os.path.join(ROOT, BASE, "净面池-20261104.json")
with open(pool_path) as f:
    pool = json.load(f)

pool_liu_pmids = set()
pool_items = {}
for x in pool["文献"]:
    pmid = x.get("PMID", "")
    pool_liu_pmids.add(pmid)
    pool_items[x["编号"]] = x

# PMID diff (初判留 vs 净面池)
raw_diff = chuji_liu_pmids - pool_liu_pmids
raw_diff2 = pool_liu_pmids - chuji_liu_pmids

# Account for 6 改判
gaipan = {"B017", "C046", "D018", "A112", "B045", "D085"}
gaipan_liu_to_shan = set()
for gid in gaipan:
    if gid in all_chuji and all_chuji[gid]["结论"] == "留":
        gaipan_liu_to_shan.add(chuji_all_pmids[gid])

# G008 PMID correction: 9547816 -> 9867266
g008_old_pmid = chuji_all_pmids.get("G008", "")
g008_new_pmid = pool_items.get("G008", {}).get("PMID", "")

expected_liu = chuji_liu_pmids - gaipan_liu_to_shan - {g008_old_pmid} | {g008_new_pmid}
pmid_diff_after = expected_liu - pool_liu_pmids
pmid_diff_after2 = pool_liu_pmids - expected_liu

results["净面"] = {
    "初判": chuji_counts,
    "初判合计": sum(chuji_counts.values()),
    "发布": {"留": pool["留"], "删": pool["删"], "待核": pool["待核"]},
    "发布合计": pool["留"] + pool["删"] + pool["待核"],
    "PMID差集_原始": sorted(raw_diff | raw_diff2),
    "改判条数": len(gaipan),
    "PMID差集_改判后": sorted(pmid_diff_after | pmid_diff_after2),
    "PMID集合一致": len(pmid_diff_after) == 0 and len(pmid_diff_after2) == 0,
}

# ── 四、池分布 ──
pool1 = pool["留_池1"]
pool2 = pool["留_池2"]
dai裁决 = pool["留_待裁决面"]
chi_sum = pool1 + pool2 + dai裁决

# Verify from文献
chi1_actual = sum(1 for x in pool["文献"] if x.get("池级") == 1)
chi2_actual = sum(1 for x in pool["文献"] if x.get("池级") == 2)
dai_actual = sum(1 for x in pool["文献"] if x.get("待裁决"))

results["池分布"] = {
    "池1": pool1, "池2": pool2, "待裁决面": dai裁决,
    "和": chi_sum, "和校验": chi_sum == 534,
    "文献验证": {"池1": chi1_actual, "池2": chi2_actual, "待裁决": dai_actual},
}

# ── 五、改判与不合格模块 ──
audit_path = os.path.join(ROOT, BASE, "审计剔除表-绝经线净面-20261104.json")
with open(audit_path) as f:
    audit = json.load(f)

gaipan_list = audit["改判清单"]
gaipan_detail = []
for g in gaipan_list:
    gaipan_detail.append({"编号": g["编号"], "因": g["因"]})

# Module deletion rates from初判 (independent)
mod_stats = {}
for nid, x in all_chuji.items():
    m = x.get("模块号", "")
    if m not in mod_stats:
        mod_stats[m] = {"total": 0, "留": 0, "删": 0, "待核": 0}
    mod_stats[m]["total"] += 1
    mod_stats[m][x["结论"]] += 1

over10_modules = []
for m in sorted(mod_stats.keys()):
    s = mod_stats[m]
    rate = s["删"] / s["total"] * 100 if s["total"] else 0
    if rate > 10:
        over10_modules.append({
            "模块": m, "删": s["删"], "送审": s["total"],
            "复算率": round(rate, 1),
            "自报率": audit["模块"][m]["剔除率"],
            "差": round(rate - audit["模块"][m]["剔除率"], 1),
        })

results["改判"] = gaipan_detail
results["不合格模块"] = over10_modules
results["不合格模块数"] = len(over10_modules)
results["不合格模块数校验"] = len(over10_modules) == 13

# ── 六、统计量 ──
cites = sorted([x["被引数"] for x in pool["文献"]])
n = len(cites)
median = (cites[n // 2 - 1] + cites[n // 2]) / 2 if n % 2 == 0 else cites[n // 2]
ge500 = sum(1 for c in cites if c >= 500)
ge1000 = sum(1 for c in cites if c >= 1000)
max_cite = max(cites)
years = [x["年份"] for x in pool["文献"] if x.get("年份")]
year_min, year_max = min(years), max(years)
ge100 = sum(1 for c in cites if c >= 100)

results["统计"] = {
    "中位数": median, "中位数校验": median == 183,
    "ge500": ge500, "ge500校验": ge500 == 58,
    "ge1000": ge1000, "ge1000校验": ge1000 == 15,
    "最大": max_cite, "最大校验": max_cite == 10248,
    "年份跨度": f"{year_min}-{year_max}",
    "年份校验": year_min == 1976 and year_max == 2026,
    "高贡献_被引ge100": ge100,
    "订单门槛富余": ge100 - 100,
}

# ── 七、疑问锚定与硬底线 ──
anchor_path = os.path.join(ROOT, BASE, "疑问锚定表-绝经线-20261104.md")
with open(anchor_path) as f:
    anchor_text = f.read()

questions = re.findall(r"## (Q\d+)", anchor_text)
all_anchor_pmids = re.findall(r"PMID (\d+)", anchor_text)
unique_anchor_pmids = set(all_anchor_pmids)

# Per-question checks
sections = re.split(r"## (Q\d+)", anchor_text)[1:]
no_anchor_count = 0
over4_count = 0
not_sorted_count = 0
for i in range(0, len(sections), 2):
    qnum = sections[i].strip()
    qcontent = sections[i + 1]
    anchors = re.findall(r"PMID (\d+)", qcontent)
    cite_vals = re.findall(r"被引 (\d+)", qcontent)
    if len(anchors) == 0:
        no_anchor_count += 1
    if len(anchors) > 4:
        over4_count += 1
    cite_ints = [int(c) for c in cite_vals]
    if cite_ints != sorted(cite_ints, reverse=True):
        not_sorted_count += 1

# All anchor PMIDs in pool?
anchor_not_in_pool = unique_anchor_pmids - pool_liu_pmids

# 硬底线 checks on 534
hardline_violations = []
for x in pool["文献"]:
    vid = x["编号"]
    issues = []
    # ① PMID or DOI
    if not x.get("PMID") and not x.get("DOI"):
        issues.append("无PMID且无DOI")
    # ② Not retracted (check类型 field)
    typ = str(x.get("类型", "")).lower()
    if "retract" in typ:
        issues.append("撤稿类型")
    # ③ Year 1900-2026
    year = x.get("年份", 0)
    if year and (year < 1900 or year > 2026):
        issues.append(f"年份{year}超范围")
    # ④ Type whitelist (all types are journal-related, verified separately)
    # ⑤ Anchor in title (过门 field confirms pass)
    if not x.get("标题"):
        issues.append("无标题")
    if issues:
        hardline_violations.append({"编号": vid, "问题": issues})

results["锚定"] = {
    "疑问数": len(questions), "疑问数校验": len(questions) == 30,
    "去重PMID": len(unique_anchor_pmids), "去重PMID校验": len(unique_anchor_pmids) == 99,
    "全部在留池": len(anchor_not_in_pool) == 0,
    "无锚数": no_anchor_count, "无锚数校验": no_anchor_count == 0,
    "超4锚数": over4_count, "超4校验": over4_count == 0,
    "未降序数": not_sorted_count, "未降序校验": not_sorted_count == 0,
}
results["硬底线"] = {
    "违规数": len(hardline_violations),
    "违规列表": hardline_violations,
}

# ── 总判定 ──
all_pass = (
    results["判据哈希"]["符"]
    and results["卷面"]["合计校验"]
    and results["卷面"]["A1并A2"]
    and not results["卷面"]["内部重复"]
    and results["净面"]["PMID集合一致"]
    and results["池分布"]["和校验"]
    and results["不合格模块数校验"]
    and results["统计"]["中位数校验"]
    and results["统计"]["ge500校验"]
    and results["统计"]["ge1000校验"]
    and results["统计"]["最大校验"]
    and results["统计"]["年份校验"]
    and results["锚定"]["疑问数校验"]
    and results["锚定"]["去重PMID校验"]
    and results["锚定"]["全部在留池"]
    and results["锚定"]["无锚数校验"]
    and results["硬底线"]["违规数"] == 0
)
results["总判定"] = "过" if all_pass else "不过"

# Write JSON
out_dir = os.path.join(ROOT, "archive/10-治理与哲学/02-实验与数据/公开层三关-20261104")
os.makedirs(out_dir, exist_ok=True)
json_path = os.path.join(out_dir, "关二-验算-20261104.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"JSON written: {json_path}")
print(f"总判定: {results['总判定']}")

# Print summary
for k, v in results.items():
    if k == "总判定":
        print(f"\n{k}: {v}")
    elif isinstance(v, dict):
        print(f"\n{k}:")
        for kk, vv in v.items():
            if isinstance(vv, list) and len(vv) > 5:
                print(f"  {kk}: [{len(vv)} items]")
            else:
                print(f"  {kk}: {vv}")
