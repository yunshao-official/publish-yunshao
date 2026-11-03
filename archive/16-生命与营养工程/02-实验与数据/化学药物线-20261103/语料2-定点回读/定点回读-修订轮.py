#!/usr/bin/env python3
# 化学与药物线·定点回读第二批（语法修订轮）
# 修订原因：第一批 6 条 TITLE:"..." 精确题名式命中 0，经查系我方题名拼写/字段用法错，
# 不是文献不存在。按 §4.2「语法错＝工具错，就地修正并记 语法修订；真零命中＝如实记 0」处理。
import json, re, ssl, time, urllib.parse, urllib.request, datetime, os

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
CTX = ssl.create_default_context()
OUT = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(OUT, "定点回读日志-修订轮.tsv")
NUM = os.path.join(OUT, "定点读数-修订轮.md")
RAW = os.path.join(OUT, "定点原始json-修订轮")
os.makedirs(RAW, exist_ok=True)

TARGETS = [
 ("R01","CC-2","milrinone AND PROMISE AND mortality","PROMISE 试验（口服米力农·慢性心衰·死亡）"),
 ("R02","CC-2","TITLE:\"The Cardiac Insufficiency Bisoprolol Study II\"","CIBIS-II（比索洛尔·全因死亡）"),
 ("R03","CC-2","MERIT-HF AND metoprolol AND mortality","MERIT-HF（美托洛尔缓释·总死亡降低%）"),
 ("R04","CC-3","TITLE:\"Ivabradine for patients with heart failure\" OR (SHIFT AND ivabradine AND randomized)","SHIFT（伊伐布雷定·主复合终点）"),
 ("R05","CC-2","carvedilol AND COPERNICUS AND mortality","COPERNICUS 死亡率数值"),
 ("R06","CC-2","vesnarinone OR (PDE3 AND inhibitor AND heart failure AND mortality)","其他正性肌力口服药死亡信号"),
 ("R07","CC-1","\"cytochrome oxidase\" AND (action OR absorption) AND (760 OR 850 OR 905 OR 980) AND (nm)","CCO 吸收/动作光谱峰位"),
 ("R08","CC-1","photobiomodulation AND review AND (660 OR 810 OR 880) AND (nm OR wavelength)","PBM 常用波长综述表"),
 ("R09","CC-5","myocardial external efficiency AND (pet OR carbon-11 OR acetate)","心肌外部效率实测值%"),
 ("R10","CC-4","\"cardiomyocyte\" AND (\"1%\" OR \"0.45\") AND renewal AND age","人心肌细胞年更新率具体数"),
 ("R11","CC-10","Dog Aging Project AND rapamycin","犬 TRIAD 试验"),
 ("R12","CC-10","\"caloric restriction\" AND rhesus monkeys AND survival AND (NIA OR Wisconsin OR 2017 OR 2009)","灵长类 CR 存活结论"),
 ("R13","CC-7","therapeutic hypothermia OR torpor AND (\"metabolic rate\" OR hypometabolism) AND (longevity OR aging)","甲类·降写入证据"),
 ("R14","CC-12","nicotinamide riboside AND randomized AND (\"no effect\" OR \"did not improve\") AND (insulin OR muscle OR vascular)","NR/NMN 阴性人体试验"),
]

TAG = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
rows = [["编号","判据","修订后检索式","执行UTC","HTTP","hitCount","取回","修订前编号","保存文件"]]
md = ["# 定点回读·修订轮读数","",
      "性质：语法修订轮（修订前 T01/T03/T04/T06/T07/T08 六条命中 0，判定为**我方检索式书写错误**，非文献不存在）。",
      "判据与检索矩阵未改；执行时刻 UTC %s。" % TAG, ""]

PRE = {"R01":"T01","R02":"T03","R03":"T04","R04":"T06/T07/T08","R05":"T05","R06":"A3",
       "R07":"T16","R08":"T17/T18","R09":"T12","R10":"T14/T15","R11":"T20","R12":"T21/T22",
       "R13":"T26","R14":"T27"}

def fetch(q, size=5):
    url = BASE + "?" + urllib.parse.urlencode({"query":q,"format":"json","pageSize":size,"resultType":"core"})
    req = urllib.request.Request(url, headers={"User-Agent":"yunshao-lit-pipeline/1.0"})
    for k in range(2):
        try:
            with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
                return json.loads(r.read().decode("utf-8")), 200
        except Exception as e:
            if k == 1: return {"error":str(e)}, 0
            time.sleep(2.0)

def sents(txt):
    txt = re.sub(r"<[^>]+>", " ", txt or "")
    return [s.strip() for s in re.split(r"(?<=[.;])\s+", txt) if s.strip() and re.search(r"\d", s)]

for tid, cc, q, want in TARGETS:
    d, st = fetch(q)
    hits = d.get("hitCount", 0)
    res = (d.get("resultList") or {}).get("result") or []
    fn = "%s_%s.json" % (tid, cc)
    json.dump(d, open(os.path.join(RAW, fn), "w", encoding="utf-8"), ensure_ascii=False)
    rows.append([tid, cc, q, TAG, str(st), str(hits), str(len(res)), PRE.get(tid,"-"), fn])
    md.append("## %s (%s) — 想要：%s  ｜ 修订前=%s" % (tid, cc, want, PRE.get(tid,"-")))
    md.append("- 检索式：`%s`｜hitCount=%s｜HTTP=%s" % (q, hits, st))
    for r in res[:4]:
        md.append("- **%s** (%s, %s) DOI=%s PMID=%s" % (r.get("title",""), r.get("journalTitle",""),
                   r.get("pubYear",""), r.get("doi","NA"), r.get("pmid","NA")))
        ss = sents(r.get("abstractText",""))
        for s in ss[:6]: md.append("    - 「%s」" % s[:420])
        if not ss: md.append("    - 摘要无含数字句/无摘要")
    if not res: md.append("- **NOT_FOUND**")
    md.append("")
    print(tid, cc, "hit=", hits, "res=", len(res)); time.sleep(0.55)

open(LOG,"w",encoding="utf-8").write("\n".join("\t".join(x) for x in rows)+"\n")
open(NUM,"w",encoding="utf-8").write("\n".join(md)+"\n")
print("WROTE", LOG, NUM)
