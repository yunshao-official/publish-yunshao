#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绝经线·整读合并与净面 v1.0｜2026-11-04（协调人口径）
输入：整读初判-卷A…G 的 JSON（7 份）＋整读卷-A…G（原始送审面）＋文献主档-v1.2-全量重算.json
规则（全部来自冻结判据书 §八 与灵魂文件，本脚本不自设门槛）：
 1) 每卷必须与源卷编号集合完全相等，缺一即整卷判废（当场停）。
 2) 剔除率一律由**逐条结论重算**：剔除率＝(删＋待核)/送审；>10% ⇒ 该模块检索式判不合格。
    子会话自己写在表头或尾巴上的百分比只作对照，不作依据；不一致处逐条登记（谁错谁照记）。
 3) 无摘要却判"留" → 改判"待核"（姊妹线乙卷刚犯过的错，本线判据 §八 已前置）。
 4) 判"留"但带 门W漏网／门N漏网 标签 → 改判"删"（语境门既然没过，主题判留也不能留）。改判只往回收，不往发放。
 5) 归一标题重复且多条同时判"留" → 只留被引最高的一条，其余标"删·重复题录"。
 6) 待裁决条目（判据书 §六 缺口那 166 条）主题照判，但净面里单列，不与池1／池2 混数。
输出：审计剔除表-绝经线净面-20261104.md／.json、净面池-20261104.json、疑问锚定表-绝经线-20261104.md
"""
import json, os, re, glob, collections, hashlib

BASE = os.path.dirname(os.path.abspath(__file__))
QDESC = {
 "Q01": "卵泡池到底是「用完」还是「关掉」", "Q02": "人类卵巢出生后能否新产生卵母细胞",
 "Q03": "闭锁率为何无人量化", "Q04": "PTEN/PI3K-AKT 为何随龄逃逸性激活",
 "Q05": "卵母细胞非整倍体检查点为何失效", "Q06": "潮热是否 KNDy/NKB 单因、为何只影响一部分女性",
 "Q07": "FSH 设定点在哪里、阈值如何随龄漂移", "Q08": "AMH 为何不能预测个体绝经时间",
 "Q09": "POI 病因约 90% 不明", "Q10": "同样激素水平为何症状差异巨大",
 "Q11": "阴道激光/射频有无超安慰剂效应", "Q12": "骨丢失里绝经效应与年龄效应如何分离",
 "Q13": "地舒单抗停药反跳机制与序贯方案", "Q14": "时机假说的窗口多长、由什么决定",
 "Q15": "向心性肥胖是雌激素缺失还是年龄驱动", "Q16": "AD 女性超额有多少能被寿命解释",
 "Q17": "脑雾的主观-客观落差是测量还是机制问题", "Q18": "围绝经期抑郁窗口的内外因各占多少",
 "Q19": "WHI 乳腺癌超额里孕激素成分贡献多少", "Q20": "针灸/草药与假刺激·安慰剂分不开",
 "Q21": "微粒化黄体酮与合成孕激素是否等价", "Q22": "口服 vs 经皮的绝对风险个体化预测",
 "Q23": "移植后功能寿命与卵泡丢失为何 80—90%", "Q24": "senolytics/NAD/重编程能否外推到人",
 "Q25": "有无标志物能提前 4 年给出绝经时刻表", "Q26": "为什么人类（和部分鲸类、象）会绝经",
 "Q27": "环境内分泌干扰物与绝经年龄提前的因果链", "Q28": "为何六至七成有症状女性不治疗",
 "Q29": "乳腺癌幸存者症状管理与复发风险", "Q30": "绝经是「事件」还是「可被重设的稳态」",
}

# ---- 0. 载入
main = json.load(open(os.path.join(BASE, "文献主档-v1.2-全量重算.json"), encoding="utf8"))
by_id_key = {}
def clip(t, n):
    t = (t or "").strip()
    return t if len(t) <= n else t[:t.rfind(" ", 0, n)].rstrip(",;:") + "…"

def rec_key(x):
    return (x.get("PMID") or "").strip() or "doi:" + (x.get("DOI") or "").strip().lower()
for x in main["文献"] + main["待裁决"]:
    by_id_key[rec_key(x)] = x

mods = collections.defaultdict(list)
verdicts = {}
vol_stat = {}
gateW_leak, gateN_leak = [], []
child_reported = {}
for p in sorted(glob.glob(os.path.join(BASE, "整读初判-卷*-20261104.json"))):
    d = json.load(open(p, encoding="utf8"))
    v = str(d.get("卷"))
    src = [f for f in glob.glob(os.path.join(BASE, "整读卷-*.json")) if "-{}-".format(v) in f]
    s = json.load(open(src[0], encoding="utf8"))["文献"]
    sid = {x["编号"]: x for x in s}
    got = d.get("文献", [])
    assert set(sid) == set(x["编号"] for x in got), "卷{} 覆盖不全".format(v)
    assert len(got) == len(s), "卷{} 条数不等".format(v)
    vol_stat[v] = {"源卷条数": len(s), "自报条数": d.get("条数"),
                   "留": sum(1 for x in got if x["结论"] == "留"),
                   "删": sum(1 for x in got if x["结论"] == "删"),
                   "待核": sum(1 for x in got if x["结论"] == "待核"),
                   "理由超40字": sum(1 for x in got if len(str(x.get("理由", ""))) > 40),
                   "文件": os.path.basename(p),
                   "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest()[:16],
                   "子报模块数": {m: vv.get("剔除率") for m, vv in (d.get("模块") or {}).items()}}
    child_reported[v] = {m: vv.get("剔除率") for m, vv in (d.get("模块") or {}).items()}
    for x in got:
        x["_卷"] = v
        x["_摘要空"] = not (sid.get(x["编号"], {}).get("摘要") or "").strip()
        x["_源"] = sid.get(x["编号"], {})
        tags = x.get("标签") or []
        x["_门W漏网"] = ("门W漏网" in tags) or any("门W" in str(t) for t in tags)
        x["_门N漏网"] = ("门N漏网" in tags) or any("门N" in str(t) for t in tags)
        verdicts[x["编号"]] = x
        mods[x["模块号"]].append(x)
assert len(verdicts) == 720, len(verdicts)

# ---- 1. 改判（只往回收）
rejudge = []
RETRACTED = []
for x in verdicts.values():
    ty = str(x["_源"].get("类型", ""))
    if re.search(r"retract", ty, re.I):
        RETRACTED.append(x)
        x["_改判"] = "改判零：撤稿文献，违硬底线②（未撤稿），判负照记"
        x["结论"] = "删"; rejudge.append(x)
    elif x["结论"] == "留" and x["_摘要空"]:
        x["_改判"] = "改判一：无摘要却凭标题判留（违判据书 §八）"
        x["结论"] = "待核"; rejudge.append(x)
    elif x["结论"] == "留" and (x["_门W漏网"] or x["_门N漏网"]):
        x["_改判"] = "改判二：语境门未过却判留（门{}漏网）".format("W" if x["_门W漏网"] else "N")
        x["结论"] = "删"; rejudge.append(x)
    else:
        x["_改判"] = ""

# ---- 2. 重复题录折叠
def nt(t): return re.sub(r"[^a-z0-9]", "", str(t).lower())[:80]
by_title = collections.defaultdict(list)
for x in verdicts.values():
    if x["结论"] == "留":
        by_title[nt(x["_源"].get("标题", x.get("标题", "")))].append(x)
folds = []
for k, g in by_title.items():
    if len(g) > 1:
        g.sort(key=lambda z: -(z["_源"].get("被引数") or 0))
        for x in g[1:]:
            x["_改判"] = "改判三：重复题录，保留同题被引最高者"
            x["结论"] = "删"; x["_折叠"] = True
            folds.append(x)
            rejudge.append(x)

# ---- 3. 每模块重算
MODNAME = {"M01": "定义·分期·流行病学", "M02": "卵巢衰老机制", "M03": "内分泌轴与神经回路",
           "M04": "血管舒缩症状", "M05": "GSM 与性功能", "M06": "骨骼与骨折",
           "M07": "心血管与代谢", "M08": "脑·认知·神经退行", "M09": "情绪·睡眠·精神症状",
           "M10": "MHT 疗效与制剂", "M11": "MHT 风险与长期随访", "M12": "非激素治疗",
           "M13": "指南·共识·立场声明", "M14": "特殊人群", "M15": "生物标志物·组学·衰老时钟",
           "M16": "再生·抗衰·前沿", "M17": "生活质量·社会·职业", "M18": "进化·文化·中医·环境"}
mod_tab = {}
for m in sorted(mods):
    g = mods[m]
    cnt = collections.Counter(x["结论"] for x in g)
    drop = cnt["删"] + cnt["待核"]
    rate = drop / len(g) * 100.0
    mod_tab[m] = {"名": MODNAME[m], "送审": len(g), "留": cnt["留"], "删": cnt["删"], "待核": cnt["待核"],
                  "剔除率": round(rate, 2), "检索式判定": "不合格(>10%)" if rate > 10 else "合格",
                  "子报剔除率": {v: child_reported.get(v, {}).get(m) for v in set(x["_卷"] for x in g)}}

keep = [x for x in verdicts.values() if x["结论"] == "留"]
gap_keep = [x for x in keep if x["_源"].get("待裁决标记")]
pool_keep = [x for x in keep if not x["_源"].get("待裁决标记")]
p1_keep = [x for x in pool_keep if x["_源"].get("池级") == 1]
p2_keep = [x for x in pool_keep if x["_源"].get("池级") == 2]

# ---- 4. 疑问锚定（只用判"留"的条目）
anchor = collections.defaultdict(list)
for x in keep:
    for q in (x.get("关联疑问") or []):
        q = str(q).strip().upper()
        if q in QDESC:
            anchor[q].append(x)
for q in anchor:
    anchor[q].sort(key=lambda z: -(z["_源"].get("被引数") or 0))

# ---- 5. 输出
OUTX = os.path.join(BASE, "审计剔除表-绝经线净面-20261104.md")
OUTJ = os.path.join(BASE, "审计剔除表-绝经线净面-20261104.json")
OUTP = os.path.join(BASE, "净面池-20261104.json")
OUTQ = os.path.join(BASE, "疑问锚定表-绝经线-20261104.md")

def clean(t): return re.sub(r"<[^>]+>", "", str(t))

net = []
for x in keep:
    s = x["_源"]
    net.append({"编号": x["编号"], "卷": x["_卷"], "模块号": x["模块号"], "结论": x["结论"],
                "理由": x.get("理由", ""), "关联疑问": x.get("关联疑问") or [],
                "池级": s.get("池级"), "待裁决": bool(s.get("待裁决标记")),
                "PMID": s.get("PMID"), "DOI": s.get("DOI"), "年份": s.get("年份"),
                "被引数": s.get("被引数"), "过门": s.get("过门"), "刊物": s.get("刊物"),
                "类型": s.get("类型"), "标题": clean(s.get("标题")), "摘要前600": (s.get("摘要") or "")[:600]})
json.dump({"声明": "本件为文献题录底座初判净面,非医疗建议;未经知世终读与合格医务人员评估不得用于任何实施",
           "版本": "净面 v1.0（协调人初判面，终读权在知世）", "日期": "2026-11-04",
           "送审": len(verdicts), "留": len(keep), "删": sum(1 for x in verdicts.values() if x["结论"] == "删"),
           "待核": sum(1 for x in verdicts.values() if x["结论"] == "待核"),
           "留_池1": len(p1_keep), "留_池2": len(p2_keep), "留_待裁决面": len(gap_keep),
           "改判条数": len(rejudge), "重复题录折叠": len(folds),
           "文献": sorted(net, key=lambda z: z["编号"])},
          open(OUTP, "w", encoding="utf8"), ensure_ascii=False, indent=1)

json.dump({"卷统计": vol_stat, "模块": mod_tab,
           "改判清单": [{"编号": x["编号"], "因": x["_改判"]} for x in rejudge],
           "门W漏网": [x["编号"] for x in verdicts.values() if x["_门W漏网"]],
           "门N漏网": [x["编号"] for x in verdicts.values() if x["_门N漏网"]],
           "汇总": {"送审": len(verdicts), "留": len(keep),
                  "删": sum(1 for x in verdicts.values() if x["结论"] == "删"),
                  "待核": sum(1 for x in verdicts.values() if x["结论"] == "待核")}},
          open(OUTJ, "w", encoding="utf8"), ensure_ascii=False, indent=1)

md = []
A = md.append
A("# 审计剔除表·绝经线文献底座（协调人初判净面）v1.0｜2026-11-04\n")
A("> 判据：`绝经线·文献检索判据书-v1.0-20261104.md` sha256 `6184d7c5001ab833`（冻结未改）；整读铁律：grep 到一行不算读。")
A("> 送审面＝720 条（v1.2 重算的池1 380＋池2 174＝554 入池，另 166 条属判据书 §六 缺口·待裁决）。")
A("> 状态：**初判净面**，不是净库。终读权在知世；本表里每一条都有逐条理由，可单条推翻。\n")
A("## 一、总数")
A("- 留 " + str(len(keep)) + "／删 " + str(sum(1 for x in verdicts.values() if x['结论'] == '删')) +
  "／待核 " + str(sum(1 for x in verdicts.values() if x['结论'] == '待核')) + "（合计 " + str(len(verdicts)) + "）")
A("- 留的构成：池1 " + str(len(p1_keep)) + " 条／池2 " + str(len(p2_keep)) + " 条／待裁决面 " + str(len(gap_keep)) + " 条")
A("- 协调人改判 " + str(len(rejudge)) + " 条（无摘要判留 " +
  str(sum(1 for x in rejudge if x['_改判'].startswith('改判一'))) + " 条、语境门未过判留 " +
  str(sum(1 for x in rejudge if x['_改判'].startswith('改判二'))) + " 条、重复题录折叠 " +
  str(sum(1 for x in rejudge if x['_改判'].startswith('改判三'))) + " 条）——改判只往回收，不往发放")
v10 = {str(x.get("PMID")): x for x in json.load(
    open(os.path.join(BASE, "文献主档-v1.0.json"), encoding="utf8"))["文献"]}
A("- **撤稿件 " + str(len(RETRACTED)) + " 条**（改判零·违硬底线②）：" +
  "；".join(x["编号"] + " PMID " + str(x["_源"].get("PMID")) + "「" + clip(clean(x["_源"].get("标题")), 48) +
            "」被引 " + str(x["_源"].get("被引数")) +
            "，v1.0 落池" + str((v10.get(str(x["_源"].get("PMID"))) or {}).get("池级")) +
            "（过门 " + str((v10.get(str(x["_源"].get("PMID"))) or {}).get("过门")) + "、无放宽）"
  for x in RETRACTED) +
  "。执行器把类型栏写空，撤稿标记直到 v1.1 离线回填后才看得见；v1.2 重算把它们挪进 §六 待裁决面，"
  "于是「撤稿」这件事在两个版本里都没被硬底线②拦住——**属执行缺陷的直接后果，不记在判据头上**。\n")
A("## 二、每模块判定（剔除率＝(删＋待核)/送审，>10% 判该模块检索式不合格）")
for m in sorted(mod_tab):
    t = mod_tab[m]
    A("- **" + m + " " + t["名"] + "**｜送审 " + str(t["送审"]) + "｜留 " + str(t["留"]) + "｜删 " + str(t["删"]) +
      "｜待核 " + str(t["待核"]) + "｜剔除率 " + str(t["剔除率"]) + "% ⇒ **" + t["检索式判定"] + "**" +
      ("（" + "、".join("执行卷" + v + "自报" + str(r) for v, r in sorted((t["子报剔除率"] or {}).items())) + "）" if t["子报剔除率"] else ""))
bad = [m for m in mod_tab if mod_tab[m]["检索式判定"].startswith("不合格")]
A("- 判不合格的模块 " + str(len(bad)) + " 个：" + "、".join(bad) + "；合格模块 " + str(18 - len(bad)) + " 个\n")
A("## 三、子会话与协调人的百分比不一致登记（谁错谁照记）")
A("> 依据一律以**逐条结论重算**为准；子会话写在表头/尾巴上的数只作对照。")
seen = set()
for v in sorted(vol_stat):
    for m, r in (child_reported.get(v) or {}).items():
        if m in mod_tab:
            A("- 卷" + v + "／" + m + "：子报 " + str(r) + "，重算 " + str(mod_tab[m]["剔除率"]) + "%")
            seen.add(m)
A("- 说明：同一模块的百分比可能被子会话写成两种（表头一种、尾巴自报另一种），故本表不采信子会话百分比。\n")
A("## 四、逐条剔除与待核（含理由）")
for x in sorted(verdicts.values(), key=lambda z: z["编号"]):
    if x["结论"] == "留" and not x["_改判"]:
        continue
    s = x["_源"]
    A("- " + x["编号"] + "｜" + x["结论"] + "｜" + x["模块号"] + "｜池" + str(s.get("池级")) + "｜" + str(s.get("年份")) +
      "｜被引 " + str(s.get("被引数")) + "｜" + clip(clean(s.get("标题")), 70) + "｜理由：" + str(x.get("理由", ""))[:40] +
      ("｜" + x["_改判"] if x["_改判"] else ""))
A("")
A("## 五、语境门漏网清单（回修检索式用，不是让你改门槛）")
A("- 门W 漏网 " + str(sum(1 for x in verdicts.values() if x['_门W漏网'])) + " 条：" +
  "、".join(x["编号"] for x in sorted(verdicts.values(), key=lambda z: z["编号"]) if x["_门W漏网"]))
A("- 门N 漏网 " + str(sum(1 for x in verdicts.values() if x['_门N漏网'])) + " 条：" +
  "、".join(x["编号"] for x in sorted(verdicts.values(), key=lambda z: z["编号"]) if x["_门N漏网"]))
A("- 归因：48 条式子全是 TITLE-only，动物与男性条目只要标题里带 ovarian／estrogen／FSH／hot flash 就会命中，"
  "语境门在**摘要**里找女性词才拦得住；漏网集中在 M02／M03／M16 三条式子族。下一版式子须把 TITLE 侧加 NOT TITLE:(rat OR mouse ...)，"
  "而不是调门槛。\n")
A("## 六、状态标签")
A("- 本表＝**在办·初判净面**；对外一律标「体系内部文献工作面」，不得称「净库」。")
A("- 被引数为 Europe PMC `citedByCount`「文献值」口径（对只有 PubMed 记录的付费刊系统性低估）。")
open(OUTX, "w", encoding="utf8").write("\n".join(md) + "\n")

q = []
q.append("# 旧科学 30 条疑问·文献锚定表（绝经线）v1.0｜2026-11-04\n")
q.append("> 依据：纲领 §二 的 30 条疑问；锚定只允许用整读判「留」的条目（判删／待核不得作锚）。")
q.append("> 被引数＝Europe PMC `citedByCount`「文献值」；未逐字回读原文者，纲领 §九 已标「经典值·待回读」。\n")
for i in range(1, 31):
    k = "Q{:02d}".format(i)
    g = anchor.get(k, [])
    q.append("## " + k + "｜" + QDESC[k])
    if not g:
        q.append("- **疑问无判留文献支撑·判负照记**（池内无该疑问的锚件，须另开检索式或待中文库）")
    for x in g[:4]:
        s = x["_源"]
        q.append("- " + clean(s.get("标题")) + "｜" + str(s.get("年份")) + "｜" + (s.get("刊物") or "") +
                 "｜被引 " + str(s.get("被引数")) + "｜" + (("池" + str(s.get("池级"))) if s.get("池级") else "待裁决面") +
                 "｜PMID " + (s.get("PMID") or "无") + "｜DOI " + (s.get("DOI") or "无"))
    q.append("")
noanchor = ["Q{:02d}".format(i) for i in range(1, 31) if not anchor.get("Q{:02d}".format(i))]
q.append("## 附：无锚疑问 " + str(len(noanchor)) + " 条：" + ("、".join(noanchor) if noanchor else "无"))
q.append("\n## 附：判留条目按疑问覆盖统计")
for i in range(1, 31):
    k = "Q{:02d}".format(i)
    q.append("- " + k + "：" + str(len(anchor.get(k, []))) + " 条判留文献")
open(OUTQ, "w", encoding="utf8").write("\n".join(q) + "\n")

print("留", len(keep), "删", sum(1 for x in verdicts.values() if x['结论'] == '删'),
      "待核", sum(1 for x in verdicts.values() if x['结论'] == '待核'),
      "| 留池1", len(p1_keep), "留池2", len(p2_keep), "留待裁决", len(gap_keep),
      "| 改判", len(rejudge), "| 不合格模块", len(bad), "| 无锚疑问", len(noanchor))
for m in sorted(mod_tab):
    print(" ", m, mod_tab[m]["送审"], "留", mod_tab[m]["留"], "剔除率", mod_tab[m]["剔除率"], mod_tab[m]["检索式判定"])
