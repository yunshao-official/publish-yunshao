#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绝经线·疑问→题录锚定 v0.9（协调人自用工作件，非交付件）
用途：把纲领 §二 的 30 条旧科学疑问，落到 v1.2 池内的**真实高被引条目**上；
落不到的照实写「疑问无文献支撑·判负照记」，禁止拿记忆里的题名充数。
输入：文献主档-v1.2-全量重算.json（零网络请求）
输出：疑问锚定候选-v0.9.json（待整读结论回来后与 关联疑问 标签合并定稿）
"""
import json, os, re, collections

BASE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(BASE, "文献主档-v1.2-全量重算.json"), encoding="utf8"))
recs = d["文献"] + d["待裁决"]

Q = {
 "Q01": (r"follicle reserve|primordial follicle|depletion|diminished ovarian", "卵泡池是用完还是关掉"),
 "Q02": (r"germline stem cell|oogonial stem|neogenesis|new oocytes|mitotic", "出生后能否新生卵母细胞"),
 "Q03": (r"activation of primordial|AMH.*recruit|per-unit|atresia|closure", "闭锁率为何无人量化"),
 "Q04": (r"PTEN|PI3K/Akt|Akt.*oocyte|mTOR.*dormanc", "PTEN/PI3K 逃逸性激活之因"),
 "Q05": (r"aneuploid|spindle|checkpoint|cohesin|sister chromatid", "非整倍体检查点为何随龄失效"),
 "Q06": (r"KNDy|neurokinin B|tacro?|NK3R|hot flash|vasomotor|temperature", "潮热是否 KNDy 单因、为何因人而异"),
 "Q07": (r"FSH|follicle-stimulating hormone|set point|gonadotropin", "FSH 设定点如何随龄漂移"),
 "Q08": (r"AMH|anti-mullerian|predict.*menopause|timing of menopause", "AMH 为何预测不了个体绝经时间"),
 "Q09": (r"premature ovarian|primary ovarian insufficiency|POI|FMR1|Turner|NOBOX|FOXL2|GDF9", "POI 病因 90% 不明"),
 "Q10": (r"severity|bother|race|ethnic|variation|individual differences|frequency", "症状个体差异为何巨大"),
 "Q11": (r"laser|radiofrequency|energy-based|microablat", "阴道激光/射频有无超安慰剂效应"),
 "Q12": (r"bone mineral density|bone loss|age.*menopause.*bone|longitudinal.*bone", "骨丢失里绝经效应与年龄效应如何分离"),
 "Q13": (r"denosumab|discontinu|rebound|romosozumab|sequential", "地舒单抗停药反跳机制"),
 "Q14": (r"timing hypothesis|window|years since menopause|early initiation|age at initiation", "时机假说的窗口由什么决定"),
 "Q15": (r"visceral|abdominal fat|body composition|insulin resistance|weight gain|obesity", "向心性肥胖是雌激素缺失还是年龄驱动"),
 "Q16": (r"Alzheimer|dementia|cognit.*women|sex difference.*dementia|brain aging", "AD 女性超额能否用寿命解释"),
 "Q17": (r"brain fog|subjective.*cognit|cognitive complaints|memory complaints", "脑雾的主观-客观落差"),
 "Q18": (r"depression|depressive|anxiety|mood", "围绝经期抑郁窗口的内外因占比"),
 "Q19": (r"breast cancer.*hormone|estrogen.*progestin.*breast|WHI.*breast|incidence.*breast", "WHI 乳腺癌超额里孕激素贡献"),
 "Q20": (r"acupuncture|sham|black cohosh|cimicifuga|isoflavone|red clover|placebo|yoga", "针灸/草药与假刺激安慰剂分不开"),
 "Q21": (r"micronized progesterone|progestogen|progestin.*breast|dydrogesterone", "微粒化黄体酮与合成孕激素是否等价"),
 "Q22": (r"oral.*transdermal|venous thromboembolism|thromboembolism|stroke.*estrogen", "口服 vs 经皮的个体化风险预测"),
 "Q23": (r"ovarian tissue.*(transplant|autotransplant)|graft|ischemia.*reperfus", "移植后功能寿命与卵泡丢失"),
 "Q24": (r"senolytic|senescence|NAD|reprogramming|parabiosis|rapamycin|quercetin.*dasatinib", "抗衰手段能否外推到人"),
 "Q25": (r"biomarker.*(menopause|ovarian)|predict.*final menstrual|proteomic.*menopause|4 years", "有无标志物能提前 4 年给出绝经时刻表"),
 "Q26": (r"grandmother|reproductive senescence|evolution.*menopause|whale|postreproductive", "为什么人类会绝经"),
 "Q27": (r"endocrine disrupt|bisphenol|BPA|phthalate|pesticide|exposure.*menopaus", "环境干扰物与绝经提前"),
 "Q28": (r"prevalence.*treatment|unmet need|discontinu|adherence|women.*not.*using|uptake", "为何六至七成有症状者不治疗"),
 "Q29": (r"breast cancer.*(surviv|hot flash|tamoxifen|aromatase)|endocrine therapy.*symptom", "乳腺癌幸存者症状管理与复发风险"),
 "Q30": (r"set point|stable state|reversib|resurgenc|spontaneous.*menstrual|reversal of menopause|recover", "绝经是事件还是可重设的稳态"),
}

out = {}
for q, (pat, desc) in Q.items():
    rx = re.compile(pat, re.I)
    hits = [x for x in recs if rx.search(x["标题"] + " " + x["摘要前400字"])]
    hits.sort(key=lambda x: -(x["被引数"] or 0))
    out[q] = {"疑问": desc, "候选条数": len(hits),
              "前十": [{"编号": "", "PMID": x["PMID"], "DOI": x["DOI"], "年份": x["年份"],
                       "被引": x["被引数"], "过门": x["过门"], "池级": x["池级"],
                       "模块": x["模块号"], "刊物": x["刊物"], "标题": x["标题"][:90]} for x in hits[:10]]}
    print(q, desc, "->", len(hits), "候选", (hits[0]["标题"][:50] if hits else "无"))
json.dump({"说明": "协调人工作件；关键词命中不等于主题支撑，最终锚定以整读结论＋人工回读为准",
           "池内条数": len(recs), "疑问": out},
          open(os.path.join(BASE, "疑问锚定候选-v0.9.json"), "w", encoding="utf8"),
          ensure_ascii=False, indent=1)
zero = [q for q, v in out.items() if v["候选条数"] == 0]
print("零候选疑问:", zero)
