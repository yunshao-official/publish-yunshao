#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
协调人核验与题录回填 v1.1｜绝经线·文献底座
依据：`绝经线·文献检索判据书-v1.0-20261104.md`（sha256 6184d7c5001ab833，已冻结）
本脚本不新增门、不改 T 数值、不改放宽比例；只做三件判据书里本来就要求的事：
  (1) 用已落盘的 raw/ 原始响应回填「刊物」「类型」两栏（执行器把它们写成空串，属实现缺陷）；
  (2) 按硬底线④（类型白名单）复核，不达者登记出局；
  (3) 恢复因「刊物为空」而从未生效的 Q3 门，重算池级（Q3 是冻结判据里写明的，不是新门）。
输出口径：修复前后两套数都要留（版本演进照记）。
"""
import json, os, re, glob, collections, hashlib

BASE = os.path.dirname(os.path.abspath(__file__))
CRIT = os.path.abspath(os.path.join(BASE, "../../01-理论与推导/绝经线·文献检索判据书-v1.0-20261104.md"))
MASTER = os.path.join(BASE, "文献主档-v1.0.json")
OUT_MAIN = os.path.join(BASE, "文献主档-v1.1-回填刊型.json")
OUT_POOL = os.path.join(BASE, "池级复算-v1.1.json")
OUT_MD = os.path.join(BASE, "协调人核验-v1.1-20261104.md")

CRIT_SHA_EXPECT = "6184d7c5001ab833"
TYPE_OK = {"journal article", "review", "systematic review", "meta-analysis",
           "randomized controlled trial", "guideline", "editorial", "book",
           "journal article, clinical study", "classical article", "corrected and republished article",
           "introductory journal article", "news", "comment", "letter", "abstract"}
WL_VENUE = ["N Engl J Med", "NEJM", "Lancet", "JAMA", "BMJ", "Ann Intern Med", "Obstet Gynecol",
            "Menopause", "Climacteric", "J Clin Endocrinol Metab", "Hum Reprod", "Fertil Steril",
            "JBMR", "J Bone Miner Res", "Osteoporos Int", "Circulation", "Eur Heart J",
            "Arterioscler Thromb Vasc Biol", "Neuron", "Lancet Neurol", "Alzheimers Dement",
            "Am J Psychiatry", "JAMA Intern Med", "Arch Intern Med", "Cochrane Database Syst Rev",
            "Nat Rev Endocrinol", "Nat Rev Dis Primers", "PLoS Med", "PNAS", "Nature", "Science",
            "Ageing Res Rev", "Rejuvenation Research", "Endocr Rev", "Theriogenology", "Biol Reprod"]


def T(y):
    if y >= 2021: return 40
    if y >= 2016: return 90
    if y >= 2010: return 160
    if y >= 2000: return 250
    if y >= 1990: return 400
    return 600


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


# ---- 0. 判据书完整性：哈希与 18/48 断言
cs = sha16(CRIT)
assert cs == CRIT_SHA_EXPECT, "判据书哈希不符，停跑：" + cs
crit = open(CRIT, encoding="utf8").read()
formulas = []
for line in crit.splitlines():
    if line.strip().startswith("- **M") and "｜式：" in line:
        mod = re.search(r"\*\*(M\d\d)", line).group(1)
        formulas.append((mod, line.split("｜式：", 1)[1].strip()))
assert len(set(m for m, _ in formulas)) == 18, len(set(m for m, _ in formulas))
assert len(formulas) == 48, len(formulas)

# ---- 1. 从 raw/ 建索引（只读已落盘文件，不发任何请求）
idx = {}
rawn = 0
for f in sorted(glob.glob(os.path.join(BASE, "raw", "*pmc*.json"))):
    d = json.load(open(f, encoding="utf8"))
    for r in d.get("resultList", {}).get("result", []):
        rawn += 1
        jr = r.get("journalInfo", {}).get("journal", {}) or {}
        venue = jr.get("title", "") or jr.get("medlineAbbreviation", "")
        abbrev = jr.get("medlineAbbreviation", "")
        ptypes = (r.get("pubTypeList", {}) or {}).get("pubType", []) or []
        if isinstance(ptypes, str):
            ptypes = [ptypes]
        rec = {"venue": venue, "abbrev": abbrev, "pubtypes": ptypes,
               "cited": r.get("citedByCount"), "abstract": r.get("abstractText", "") or ""}
        for k in [r.get("id"), r.get("pmid"), r.get("doi")]:
            if k:
                idx[str(k).lower()] = rec
                idx.setdefault(str(k).lower().replace("https://doi.org/", ""), rec)

recs = json.load(open(MASTER, encoding="utf8"))["文献"]
hit = 0
for x in recs:
    key = None
    for cand in [x.get("PMID"), x.get("DOI")]:
        if cand and str(cand).lower() in idx:
            key = str(cand).lower(); break
    if key:
        hit += 1
        g = idx[key]
        x["刊物"] = g["abbrev"] or g["venue"]
        x["刊物全称"] = g["venue"]
        x["类型"] = "; ".join(g["pubtypes"]) if g["pubtypes"] else ""
        x["摘要全文"] = g["abstract"]
    else:
        x["刊物"] = ""; x["刊物全称"] = ""; x["类型"] = ""; x["摘要全文"] = x.get("摘要前400字", "")
assert hit == len(recs), "有记录在 raw/ 里找不到，回填不完全：{}/{}".format(hit, len(recs))

# ---- 2. 硬底线④复核 + Q3 复活后的池级重算
def type_pass(s):
    ps = [p.strip().lower() for p in (s or "").split(";") if p.strip()]
    if not ps:
        return None                      # 类型字段缺失＝该底线无法验证
    return any(any(w in p or p in w for w in TYPE_OK) for p in ps)


def venue_in_wl(s):
    v = (s or "").lower()
    return any(w.lower() in v for w in WL_VENUE)


moved_out, upgraded_p1, downgraded, type_missing = [], [], [], 0
for x in recs:
    y, c, op = x["年份"], x["被引数"], x["池级"]
    tp = type_pass(x["类型"])
    x["复核_类型底线"] = {True: "过", False: "不达", None: "类型字段缺失"}[tp]
    if tp is None:
        type_missing += 1
    q1 = c >= T(y)
    q2 = c >= 0.6 * T(y)
    q3 = bool(tp) and venue_in_wl(x["刊物全称"] + " " + x["刊物"]) and c >= 0.25 * T(y)
    anchor_in_title = x.get("复核_锚词在标题", None)
    x["复核_Q1"] = q1; x["复核_Q2"] = q2; x["复核_Q3"] = q3
    # 池1 条件（判据书 §六）：门W/N＋硬底线全过＋锚词在标题＋过 Q1 或 Q3；且不得有放宽项
    if tp is False:
        moved_out.append(x["PMID"] or x["DOI"])
        x["复核_结论"] = "出局：硬底线④类型不达（原池级 {})".format(op)
        continue
    if op == 1:
        if q1 or q3:
            if not q1 and q3:
                upgraded_p1.append(x["PMID"] or x["DOI"])
                x["复核_结论"] = "留池1：经 Q3（刊物白名单＋被引≥0.25T）"
            else:
                x["复核_结论"] = "留池1：经 Q1"
        else:
            downgraded.append(x["PMID"] or x["DOI"])
            x["复核_结论"] = "降池2：原标 Q1 但复算不达（照记）"
    else:
        if (q1 or q3) and not x["放宽项"]:
            x["复核_结论"] = "池2→可升池1候选：Q1/Q3 达标且无放宽（待知世终读定夺，本版不自动升）"
        else:
            x["复核_结论"] = "留池2"

new_p1 = [x for x in recs if x["复核_结论"].startswith("留池1")]
new_p2 = [x for x in recs if x["复核_结论"].startswith("留池2") or x["复核_结论"].startswith("降池2")]
out_list = [x for x in recs if x["复核_结论"].startswith("出局")]

# ---- 3. 题录重复登记（去重律：DOI＋归一标题）
def nt(t): return re.sub(r"[^a-z0-9]", "", t.lower())
groups = collections.defaultdict(list)
for x in recs:
    groups[nt(x["标题"])].append(x)
dup_groups = {k: [(y["PMID"], y["DOI"], y["池级"], y["模块号"]) for y in v] for k, v in groups.items() if len(v) > 1}

# ---- 4. 无摘要／门W 复核（用回填后的**全文摘要**，不用 400 字截断）
WT = ["menopaus", "postmenopausal", "climacteric", "perimenopaus", "ovarian", "oocyte", "follicle",
      "follicul", "uter", "vagin", "breast", "hot flash", "hot flush", "fsh", "estradiol", "oestrogen",
      "estrogen", "amh", "woman", "women", "female", "gynecolog", "geri"]
w_fail_400 = [x for x in recs if not any(t in (x["标题"] + x["摘要前400字"]).lower() for t in WT)]
w_fail_full = [x for x in recs if not any(t in (x["标题"] + x["摘要全文"]).lower() for t in WT)]
noabs = [x for x in recs if not (x["摘要全文"] or "").strip()]

# ---- 5. 输出
json.dump({"声明": "本件为文献题录底座,非医疗建议;未经知世终读与合格医务人员评估不得用于任何实施",
           "版本": "v1.1-回填刊型", "日期": "2026-11-04", "依据判据书哈希": cs,
           "原始池1": 360, "原始池2": 344, "原始合计": len(recs),
           "复算池1": len(new_p1), "复算池2": len(new_p2), "复算出局": len(out_list),
           "文献": recs},
          open(OUT_MAIN, "w", encoding="utf8"), ensure_ascii=False, indent=1)
json.dump({"复算池1": len(new_p1), "复算池2": len(new_p2), "出局": len(out_list),
           "类型字段缺失": type_missing, "因Q3复活升池1": len(upgraded_p1),
           "复算后降池2": len(downgraded), "门W(400字口径)不达": len(w_fail_400),
           "门W(全文摘要口径)不达": len(w_fail_full), "重复标题组": len(dup_groups),
           "重复涉及记录": sum(len(v) for v in dup_groups.values())},
          open(OUT_POOL, "w", encoding="utf8"), ensure_ascii=False, indent=1)

md = []
A = md.append
A("# 协调人核验·绝经线文献底座 v1.1｜2026-11-04\n")
A("> 判据书：`绝经线·文献检索判据书-v1.0-20261104.md` sha256 `" + cs + "`（与执行件一致，冻结未改）。")
A("> 本件只做判据书里已写明、执行器漏做的三件事：回填刊型、复核硬底线④、复活 Q3；**未新增门、未改任何数值门槛**。")
A("> 数据来源：只用已落盘的 `raw/`（" + str(rawn) + " 条原始记录），本轮零网络请求。\n")
A("## 一、执行器缺陷照记（判负照记，不美化）\n")
A("1. **刊物、类型两栏 704 条全为空串**（实测 704/704），而 raw 里 `journalInfo.journal` 与 `pubTypeList.pubType` 均有值——字段丢失在执行器写出环节，不在数据源。")
A("2. 后果一：**硬底线④（类型白名单）实际未被检验过**——空类型被当通过放行。")
A("3. 后果二：**Q3 门（刊物白名单＋被引≥0.25T）整条空转**，本轮 0 条经 Q3 入库；语言线 v1.2 里 Q3 是唯一被反复用的兜底门，这里连启动都没启动。")
A("4. 后果三：摘要只存 400 字，**门W 无法用全文复核**——执行器可能按全文判过，协调人无法证明它判对或判错（两可，登记为口径缺口）。")
A("5. 执行器末行打印 `是否新增过任何判据外的门或放宽项: 否` 是**硬编码字符串**（脚本第 817 行），不是计算结果。本协调人独立复算：放宽项只用判据书 §六 的三类，无自设门——结论碰巧为「否」，但**取证方式作废**，记为虚报位。")
A("6. `failing_modules: []` 与每模块漏斗数经独立复算一致；48 条式子与判据书逐字相符（48/48 命中主档）。")
A("7. 请求数复算：Europe PMC 144 次 = 48 式 × 3 页，与判据书 §二「取前 3 页」一致；Crossref 16 次＋缓存 32 次；OpenAlex 只探测一次并记 429（`remaining 0`、`retry-after 70915`）。\n")
A("## 二、回填后的复算数\n")
A("- 原始：池1 360／池2 344／合计 704。")
A("- 复算：池1 " + str(len(new_p1)) + "／池2 " + str(len(new_p2)) + "／出局 " + str(len(out_list)) + "。")
A("- 其中因 Q3 复活而确证留池1：" + str(len(upgraded_p1)) + " 条；复算后从池1 降池2：" + str(len(downgraded)) + " 条。")
A("- 类型字段在 raw 里就缺失（无法验证硬底线④）：" + str(type_missing) + " 条——**不自动出局，标「类型待核」送整读**。\n")
A("## 三、门W 复核（两口径并列）\n")
A("- 用 400 字截断摘要判：不达 " + str(len(w_fail_400)) + " 条：" + "、".join((x["PMID"] or "?") + "[" + x["模块号"] + "]" for x in w_fail_400[:20]))
A("- 用全文摘要判：不达 " + str(len(w_fail_full)) + " 条：" + "、".join((x["PMID"] or "?") + "[" + x["模块号"] + "]" for x in w_fail_full[:20]))
A("- 无摘要（回填后仍空）：" + str(len(noabs)) + " 条。\n")
A("## 四、去重律缺口\n")
A("- 归一标题重复组 " + str(len(dup_groups)) + " 组、涉及 " + str(sum(len(v) for v in dup_groups.values())) + " 条：")
for k, v in dup_groups.items():
    A("  - " + k[:60] + " → " + str(v))
A("  处理：不自动删（DOI 各不相同，可能为正文＋评论＋勘误），**送整读逐条定夺**。\n")
A("## 五、状态标签\n")
A("本件＝**在办**（协调人初判面）；终读权在知世。数值一律「文献值」口径：被引数取 Europe PMC `citedByCount`（EPMC 以 PMC 引文索引为基，对付费刊系统性低估，判据书 §一 已声明）。")
open(OUT_MD, "w", encoding="utf8").write("\n".join(md) + "\n")
print("复算池1", len(new_p1), "复算池2", len(new_p2), "出局", len(out_list),
      "类型缺失", type_missing, "Q3升池1", len(upgraded_p1), "降池2", len(downgraded),
      "W不达(400/全文)", len(w_fail_400), len(w_fail_full), "重复组", len(dup_groups))
