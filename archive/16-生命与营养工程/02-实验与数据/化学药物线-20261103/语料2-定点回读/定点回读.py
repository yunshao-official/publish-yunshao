#!/usr/bin/env python3
# 化学与药物线·第二批定点回读脚本（判据读数专用·零第三方依赖）
# 性质：冻结件 §4.2 批量扫描之后的「定点回读」——只取读数，不改判据、不改检索式矩阵
# 纪律：只打印 API 返回的 abstractText 里含数字的句子；查不到打印 NOT_FOUND，不补全
import json, re, ssl, time, urllib.parse, urllib.request, datetime, os, sys

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
CTX = ssl.create_default_context()
OUT = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(OUT, "定点回读日志.tsv")
RAW = os.path.join(OUT, "定点原始json")
NUM = os.path.join(OUT, "定点读数.md")
os.makedirs(RAW, exist_ok=True)

# (编号, 判据, 回读题名短语/检索式, 想要的读数)
TARGETS = [
 ("T01","CC-2","TITLE:\"Effects of oral milrinone on mortality in severe chronic heart failure\"","PROMISE：口服米力农对死亡率"),
 ("T02","CC-2","TITLE:\"The effect of digoxin on mortality and morbidity in patients with heart failure\"","DIG：地高辛死亡/住院"),
 ("T03","CC-2","TITLE:\"A trial of the beta-blocker bisoprolol in patients with chronic cardiac failure\"","CIBIS：比索洛尔死亡"),
 ("T04","CC-2","TITLE:\"Effect of metoprolol CR/XL in chronic heart failure: Randomised Intervention Assessment Study\"","MERIT-HF：美托洛尔死亡降低%"),
 ("T05","CC-2","TITLE:\"Effect of carvedilol on the morbidity of patients with severe chronic heart failure\"","COPERNICUS：卡维地洛"),
 ("T06","CC-2","TITLE:\"Ivabradine, heart rate, and heart failure\"","SHIFT/心率相关"),
 ("T07","CC-3","TITLE:\"Effects of ivabradine in patients with chronic systolic heart failure, in atrial fibrillation and with or without beta-blockers\"","SHIFT 主终点风险降低%"),
 ("T08","CC-3","TITLE:\"SHIFT Investigators\" AND ivabradine","SHIFT 试验"),
 ("T09","CC-2","TITLE:\"Xanamivir\" OR (TITLE:\"levosimendan\" AND TITLE:\"mortality\")","左西孟旦死亡信号"),
 ("T10","CC-2","TITLE:\"omecamtiv mecarbil\" AND TITLE:\"GALACTIC-HF\"","GALACTIC-HF 主终点/心血管死亡"),
 ("T11","CC-2","TITLE:\"Enoximone\" AND TITLE:\"mortality\" AND TITLE:\"heart failure\"","依诺昔酮死亡率"),
 ("T12","CC-5","(\"myocardial external efficiency\" OR \"myocardial efficiency\") AND (ABSTRACT:\"%\")","心肌外部效率实测%"),
 ("T13","CC-5","\"cardiac power output\" AND (ABSTRACT:\"W\" OR ABSTRACT:\"watts\")","心脏功率输出 W"),
 ("T14","CC-4","TITLE:\"Cardiomyocyte renewal in humans\"","人心肌细胞更新率%/年"),
 ("T15","CC-4","cardiomyocyte AND turnover AND (ABSTRACT:\"% per year\" OR ABSTRACT:\"annual\" OR ABSTRACT:\"age\")","心肌细胞年更新率随龄"),
 ("T16","CC-1","\"action spectrum\" AND \"cytochrome c oxidase\"","CCO 动作光谱峰位 nm"),
 ("T17","CC-1","(photobiomodulation OR \"near infrared\") AND (ABSTRACT:\"730\" OR ABSTRACT:\"740\" OR ABSTRACT:\"760\") AND mitochondria","PBM 725nm 附近实测"),
 ("T18","CC-1","(photobiomodulation OR \"laser irradiation\") AND (ABSTRACT:\"960\" OR ABSTRACT:\"970\" OR ABSTRACT:\"980\") AND (ABSTRACT:\"nm\")","PBM 966nm 附近实测"),
 ("T19","CC-1","\"optical window\" AND tissue AND (ABSTRACT:\"650\" OR ABSTRACT:\"900\" OR ABSTRACT:\"1350\") AND (ABSTRACT:\"nm\")","组织光学窗口边界 nm"),
 ("T20","CC-10","TITLE:\"The Effect of Rapamycin on Gait and Activity in the Dog Aging Project\" OR (rapamycin AND dogs AND randomized AND aging)","犬 TRIAD 结论"),
 ("T21","CC-10","(caloric restriction AND rhesus AND survival AND (ABSTRACT:\"no\") )","灵长类热量限制存活"),
 ("T22","CC-10","TITLE:\"Caloric restriction does not improve survival in rhesus monkeys\" OR (\"Rhesus monkey studies\" AND caloric restriction)","NIA/Wisconsin 两研究"),
 ("T23","CC-10","TITLE:\"Rapamycin fed late in life extends lifespan in genetically heterogeneous mice\"","ITP 小鼠寿命延长%"),
 ("T24","CC-9","(rapamycin OR \"tor1\" OR autophagy) AND lifespan AND (ABSTRACT:\"required\" OR ABSTRACT:\"blocked\") AND (ABSTRACT:\"autophagy\")","自噬必要性"),
 ("T25","CC-8","senolytic AND (ABSTRACT:\"aged\" OR ABSTRACT:\"old\") AND (ABSTRACT:\"young\") AND lifespan","丙类随龄效应差"),
 ("T26","CC-7","(hypometabolism OR torpor) AND (ABSTRACT:\"lifespan\" OR ABSTRACT:\"longevity\")","甲类降写入"),
 ("T27","CC-12","(NMN OR \"nicotinamide mononucleotide\") AND randomized AND (ABSTRACT:\"no significant\" OR ABSTRACT:\"did not\")","NMN 阴性 RCT"),
 ("T28","CC-12","aducanumab AND (ABSTRACT:\"withdrawn\" OR ABSTRACT:\"accelerated approval\")","aducanumab 撤市/代理终点"),
 ("T29","CC-3","\"resting heart rate\" AND (ABSTRACT:\"mortality\") AND (ABSTRACT:\"hazard\" OR ABSTRACT:\"risk\") AND general population","静息心率与全因死亡"),
 ("T30","CC-4","\"mitochondrial\" AND turnover AND (ABSTRACT:\"myocardium\" OR ABSTRACT:\"cardiac\") AND (ABSTRACT:\"half-life\" OR ABSTRACT:\"turnover rate\")","心肌线粒体周转"),
]

TAG = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
rows = [["编号","判据","回读检索式","执行UTC","HTTP","hitCount","取回","保存文件"]]
md = ["# 第二批·定点回读读数（化学与药物线）","",
      "本批性质：§4.2 批量扫描之后的判据读数回读；判据未改，检索矩阵未改；执行时刻 UTC %s。" % TAG,
      "只摘录 API abstractText 中含数字的逐字句。无命中＝NOT_FOUND，不补全。",""]

def fetch(q, rtype="core", size=4):
    url = BASE + "?" + urllib.parse.urlencode({"query":q,"format":"json","pageSize":size,"resultType":rtype})
    req = urllib.request.Request(url, headers={"User-Agent":"yunshao-lit-pipeline/1.0"})
    for k in range(2):
        try:
            with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
                return json.loads(r.read().decode("utf-8")), 200
        except Exception as e:
            if k == 1:
                return {"error":str(e)}, 0
            time.sleep(2.0)

def sentences_with_numbers(txt):
    txt = re.sub(r"<[^>]+>", " ", txt or "")
    out = []
    for s in re.split(r"(?<=[.;])\s+", txt):
        s = s.strip()
        if s and re.search(r"\d", s):
            out.append(s)
    return out

for tid, cc, q, want in TARGETS:
    d, st = fetch(q)
    hits = d.get("hitCount", 0)
    res = (d.get("resultList") or {}).get("result") or []
    fn = "%s_%s.json" % (tid, cc)
    with open(os.path.join(RAW, fn), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    rows.append([tid, cc, q, TAG, str(st), str(hits), str(len(res)), fn])
    md.append("## %s (%s) — 想要：%s" % (tid, cc, want))
    md.append("- 检索式：`%s`｜hitCount=%s｜HTTP=%s" % (q, hits, st))
    if not res:
        md.append("- **NOT_FOUND**（本语料未见，零命中或接口错误）\n")
        print("%s %s hit=%s RES=0" % (tid, cc, hits)); time.sleep(0.5); continue
    for r in res[:3]:
        title = r.get("title","")
        doi = r.get("doi","NA"); pmid = r.get("pmid","NA")
        j = r.get("journalTitle",""); y = r.get("pubYear","")
        pt = r.get("pubType","")
        md.append("- **%s** (%s, %s) DOI=%s PMID=%s [%s]" % (title, j, y, doi, pmid, pt))
        sn = sentences_with_numbers(r.get("abstractText",""))
        if sn:
            for s in sn[:5]:
                md.append("    - 「%s」" % s[:400])
        else:
            md.append("    - 摘要无含数字句（或未返回摘要）")
    md.append("")
    print("%s %s hit=%s res=%d" % (tid, cc, hits, len(res)))
    time.sleep(0.55)

with open(LOG, "w", encoding="utf-8") as f:
    f.write("\n".join("\t".join(x) for x in rows) + "\n")
with open(NUM, "w", encoding="utf-8") as f:
    f.write("\n".join(md) + "\n")
print("WROTE", LOG, NUM)
