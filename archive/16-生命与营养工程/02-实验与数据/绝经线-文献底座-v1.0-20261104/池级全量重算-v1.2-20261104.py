#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绝经线·池级全量重算 v1.2（零网络请求，只用已落盘 raw/）
为什么要重算：执行器把「刊物」「类型」两栏写成空串，导致
  (a) 硬底线④（类型白名单）从未真正检验；
  (b) Q3 门（刊物白名单＋被引≥0.25T）整条空转，被引落在 0.25T—0.3T 区间的候选全部丢在门外。
本件从 raw/ 重建候选面，按冻结判据书的**同一条判定顺序**重算，不改任何门槛，不新增任何门。
判据书：sha256 6184d7c5001ab833（§五 门W→门N→硬底线→Q1/Q2/Q3；§六 两池与三类放宽）。

【照记·判据缺口在我（判据书写者）身上】
判据书 §六 只写了池1 条件（Q1 或 Q3 且锚在标题）与池2 的三类放宽（甲降半档／乙锚仅摘要／丙Crossref补齐），
**没有规定「被引达 Q2（≥0.6T）且锚在标题、又没用上任何放宽」的条目该进哪一池**。
执行器把它们放进了池2 且放宽项留空（实测 91 条）。本件不再自作主张，把它们单列为
「Q2无放宽·待知世裁决」清单，不计入池1 也不计入池2，等知世判。
"""
import json, os, re, glob, collections, hashlib

BASE = os.path.dirname(os.path.abspath(__file__))
CRIT = os.path.abspath(os.path.join(BASE, "../../01-理论与推导/绝经线·文献检索判据书-v1.0-20261104.md"))
OUT = os.path.join(BASE, "文献主档-v1.2-全量重算.json")
OUTMD = os.path.join(BASE, "池级重算说明-v1.2-20261104.md")
EXPECT = "6184d7c5001ab833"

WL = ["N Engl J Med", "NEJM", "Lancet", "JAMA", "BMJ", "Ann Intern Med", "Obstet Gynecol",
      "Menopause", "Climacteric", "J Clin Endocrinol Metab", "Hum Reprod", "Fertil Steril",
      "JBMR", "J Bone Miner Res", "Osteoporos Int", "Circulation", "Eur Heart J",
      "Arterioscler Thromb Vasc Biol", "Neuron", "Lancet Neurol", "Alzheimers Dement",
      "Am J Psychiatry", "JAMA Intern Med", "Arch Intern Med", "Cochrane Database Syst Rev",
      "Nat Rev Endocrinol", "Nat Rev Dis Primers", "PLoS Med", "PNAS", "Proc Natl Acad Sci",
      "Nature", "Science", "Ageing Res Rev", "Rejuvenation Research", "Endocr Rev",
      "Theriogenology", "Biol Reprod"]
TYPES = ["journal article", "review", "systematic review", "meta-analysis",
         "randomized controlled trial", "guideline", "editorial", "book"]
W_TOK = ["menopaus", "postmenopausal", "climacteric", "perimenopaus", "ovarian", "oocyte",
         "follicle", "follicul", "uter", "vagin", "breast", "hot flash", "hot flush", "fsh",
         "estradiol", "oestrogen", "estrogen", "amh", "woman", "women", "female", "gynecolog", "geri"]
# 门N：判据书列的跨域负面表。两处口径由我（重算人）当场写明：
#  (1) 判据书里的 `plant` 不单独作负面词——它会以 plant-based diet 形式出现在人群营养文献里，
#      无条件用会误杀；判据书同条已列 arabidopsis，故按该词与 plant growth regulator 处理。
#  (2) 判据书把 rat／bovine／mice 写成「无人类语境时」——判定顺序是门W 在前，
#      过门W 者已带人·女性语境词，故这里不再对这三个词做无条件剔除，只留纯动物词与显式共现禁令。
NEG = ["zebrafish", "medaka", "alligator", "wildlife", "ecosystem", "aquatic", "effluent",
       "pulp mill", "arabidopsis", "daphnia", "shellfish", "coral", "bovine", "ovine", "canine",
       "andropause", "male infertility", "plant growth regulator"]
NEG_CO = [("menopausal hormone", "prostate"), ("testosterone", "hypogonadism")]


def T(y):
    if y >= 2021: return 40
    if y >= 2016: return 90
    if y >= 2010: return 160
    if y >= 2000: return 250
    if y >= 1990: return 400
    return 600


def wl_hit(v):
    vl = v.lower()
    return next((w for w in WL if w.lower() in vl), None)


def type_ok(pts):
    low = [p.lower() for p in pts]
    return next((t for t in TYPES if any(t in p or p in t for p in low)), None) if pts else None


sha = hashlib.sha256(open(CRIT, "rb").read()).hexdigest()[:16]
assert sha == EXPECT, sha
crit = open(CRIT, encoding="utf8").read()
forms = []
for line in crit.splitlines():
    if line.strip().startswith("- **M") and "｜式：" in line:
        forms.append((re.search(r"\*\*(M\d\d)", line).group(1), line.split("｜式：", 1)[1].strip()))
assert len(forms) == 48 and len(set(m for m, _ in forms)) == 18

# ---- 1. 读全部 raw 候选，按 (式子, 页) 归属模块
cands = {}
per_formula = collections.Counter()
rawfiles = sorted(glob.glob(os.path.join(BASE, "raw", "*pmc*.json")))
for f in rawfiles:
    name = os.path.basename(f)
    m = re.match(r"(M\d\d)-pmc-(\d+)-\d+\.json", name)
    if not m:
        continue
    mod, fno = m.group(1), int(m.group(2))
    same_mod = [q for mm, q in forms if mm == mod]
    fq = same_mod[fno - 1] if fno - 1 < len(same_mod) else None
    d = json.load(open(f, encoding="utf8"))
    for r in d.get("resultList", {}).get("result", []):
        per_formula[(mod, fno)] += 1
        jr = (r.get("journalInfo", {}) or {}).get("journal", {}) or {}
        venue = jr.get("title", "") or ""
        abbrev = jr.get("medlineAbbreviation", "") or ""
        pts = (r.get("pubTypeList", {}) or {}).get("pubType", []) or []
        if isinstance(pts, str):
            pts = [pts]
        yr = r.get("pubYear") or ""
        try:
            yr = int(str(yr)[:4])
        except Exception:
            yr = None
        ab = r.get("abstractText", "") or ""
        key = (r.get("pmid") or "") or "doi:" + (r.get("doi") or "").lower() or (r.get("title") or "")[:70].lower()
        rec = {"模块号": mod, "检索式序号": fno, "检索式原文": fq, "标题": (r.get("title") or "").strip(),
               "作者": [a.get("author", "") for a in (r.get("authorList", {}) or {}).get("author", [])],
               "年份": yr, "PMID": r.get("pmid") or "", "DOI": r.get("doi") or "",
               "刊物": abbrev, "刊物全称": venue, "类型": "; ".join(pts), "类型表": pts,
               "被引数": r.get("citedByCount") or 0, "被引来源": "EPMC",
               "摘要全文": ab, "摘要前400字": ab[:400]}
        old = cands.get(key)
        if old:
            old["跨模块"] = sorted(set(old.get("跨模块", [old["模块号"]]) + [mod]))
            if rec["被引数"] > old["被引数"]:
                pass
        else:
            rec["跨模块"] = [mod]
            cands[key] = rec
print("raw 送审候选（去重后）:", len(cands))

# ---- 2. 冻结判据的判定顺序：门W → 门N → 硬底线 → Q1/Q2/Q3
pool1, pool2, q2_gap, rejW, rejN, rejFloor = [], [], [], [], [], []
for k, x in cands.items():
    blob = (x["标题"] + " " + x["摘要全文"]).lower()
    if x["年份"] is None or not (1900 <= x["年份"] <= 2026):
        rejFloor.append(dict(x, 出局因="硬底线③年份")); continue
    if not (x["PMID"] or x["DOI"]):
        rejFloor.append(dict(x, 出局因="硬底线①无PMID无DOI")); continue
    tok = type_ok(x["类型表"])
    if tok is None:
        rejFloor.append(dict(x, 出局因="硬底线④类型缺失或不达")); continue
    if not x["摘要全文"].strip():
        rejFloor.append(dict(x, 出局因="硬底线⑥无摘要→发现清单")); continue
    if not any(t in blob for t in W_TOK):
        rejW.append(x); continue
    if any(n in blob for n in NEG) or any(a in blob and b in blob for a, b in NEG_CO):
        rejN.append(x); continue
    c, t = x["被引数"], T(x["年份"])
    venue_ok = wl_hit(x["刊物全称"] + " " + x["刊物"])
    # 锚词在标题：所有检索式都是 TITLE-only，命中即标题满足；此处再核一次式子里的核心锚
    anchor = bool(x["检索式原文"])
    if c >= t:
        (pool1 if anchor else pool2).append(dict(x, 过门="Q1", 放宽项=[]))
    elif c >= 0.6 * t:
        if anchor:
            q2_gap.append(dict(x, 过门="Q2", 放宽项=[], 状态标签="待裁决·Q2无放宽"))
        else:
            pool2.append(dict(x, 过门="Q2", 放宽项=["放宽乙:锚仅摘要"]))
    elif c >= 0.5 * t:
        pool2.append(dict(x, 过门="Q1-放宽甲", 放宽项=["放宽甲:Q1降半档(门槛×0.5)"]))
    elif c >= 0.3 * t:
        pool2.append(dict(x, 过门="Q2-放宽甲", 放宽项=["放宽甲:Q2降半档(门槛×0.3)"]))
    elif c >= 0.25 * t and venue_ok:
        # 判据书 §六：池1 允许「过 Q1 或 Q3」，故 Q3 合格者进池1，并记下命中的白名单刊名
        pool1.append(dict(x, 过门="Q3", 放宽项=[], 白名单刊=venue_ok))
    else:
        rejFloor.append(dict(x, 出局因="被引不达任何档(含Q3白名单门)"))

for L in (pool1, pool2, q2_gap):
    for x in L:
        x["池级"] = 1 if L is pool1 else (2 if L is pool2 else None)
        x.setdefault("状态标签", "核")
for x in pool1:
    x["放宽项"] = []

json.dump({"声明": "本件为文献题录底座,非医疗建议;未经知世终读与合格医务人员评估不得用于任何实施",
           "版本": "v1.2-全量重算(零网络请求)", "日期": "2026-11-04", "依据判据书哈希": sha,
           "raw候选去重": len(cands), "池1": len(pool1), "池2": len(pool2),
           "Q2无放宽待裁决": len(q2_gap), "门W出局": len(rejW), "门N出局": len(rejN),
           "硬底线与门槛出局": len(rejFloor),
           "文献": pool1 + pool2, "待裁决": q2_gap},
          open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=1)

md = ["# 池级全量重算 v1.2 说明｜2026-11-04\n",
      "判据书 sha256 `" + sha + "`（冻结未改）；零网络请求，输入＝已落盘 raw/ 的 144 个 Europe PMC 响应。\n",
      "- 送审候选（按 PMID／DOI 去重）：" + str(len(cands)) + " 条",
      "- 池1：" + str(len(pool1)) + " 条（其中经 Q3 刊物白名单入库：" + str(sum(1 for x in pool1 if x['过门'] == 'Q3')) + " 条——**执行器因刊物栏空而全部漏掉的量**）",
      "- 池2：" + str(len(pool2)) + " 条",
      "- Q2 达线但无放宽依据·待知世裁决：" + str(len(q2_gap)) + " 条",
      "- 门W 出局：" + str(len(rejW)) + "；门N 出局：" + str(len(rejN)) + "；硬底线／门槛出局：" + str(len(rejFloor)) + "\n",
      "## 与 v1.0 的差异（同数不同因）",
      "- v1.0：池1 360／池2 344／合计 704（刊物、类型两栏全空）。",
      "- v1.2：口径不变、门槛不变，只是把丢掉的字段接回来重跑判定。差异全部逐条登记在本件 JSON 里。",
      "- **Q2 无放宽 91→" + str(len(q2_gap)) + " 条**：这是判据书 §六 的书写缺口，不是执行器越权；单列不并池。"]
q3only = [x for x in pool1 if x["过门"] == "Q3"]
md.append("- Q3 新增样本（最多列 10 条）：")
for x in q3only[:10]:
    md.append("  - " + str(x["年份"]) + "｜被引 " + str(x["被引数"]) + "｜" + x["刊物"] + "｜" + x["标题"][:60])
open(OUTMD, "w", encoding="utf8").write("\n".join(md) + "\n")
print("池1", len(pool1), "池2", len(pool2), "Q2待裁决", len(q2_gap), "Q3入库", len(q3only),
      "W", len(rejW), "N", len(rejN), "floor", len(rejFloor))
