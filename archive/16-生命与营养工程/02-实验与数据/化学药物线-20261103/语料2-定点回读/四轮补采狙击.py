# -*- coding: utf-8 -*-
# 第四轮·补采狙击（判据未改·只补未闭合项与工具自检）
# 目的：(1) 复测 A1 零命中＝真零 or 我方语法残留
#      (2) 试闭 CC-8（丙类·年龄依赖）、CC-10（犬类）、CC-9（乙类·自噬遗传必要性）
# 通道说明：沙箱内 python urllib 出现间歇 DNS 失败（gaierror -2），
#          本机改走 curl 子进程＋重试；重试只针对传输层，不改检索式、不改判据。
import json, re, subprocess, time, pathlib, datetime

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
OUT = pathlib.Path(__file__).resolve().parent
RAWD = OUT / "四轮原始"
RAWD.mkdir(exist_ok=True)

def fetch(q, size=25):
    last = ""
    for attempt in range(3):          # 沙箱 DNS 间歇失败（rc=6），重试只针对传输层
        p = subprocess.run(
            ["curl", "-s", "--max-time", "30", "-G", BASE,
             "--data-urlencode", "query=" + q,
             "--data-urlencode", "format=json",
             "--data-urlencode", "pageSize=%d" % size,
             "--data-urlencode", "resultType=core"],
            capture_output=True, text=True)
        if p.stdout.strip():
            try:
                return json.loads(p.stdout)
            except Exception as e:
                last = "JSON解析失败 " + str(e)[:60]
        else:
            last = "空响应/传输失败 rc=%d" % p.returncode
        time.sleep([3, 6, 12][attempt])
    raise RuntimeError(last)

def sents(txt):
    txt = re.sub(r"<[^>]+>", " ", txt or "")
    return [s.strip() for s in re.split(r"(?<=[.;])\s+", txt) if s.strip() and re.search(r"\d", s)]

QUERIES = [
    ("Q01", "A1复测·PUBTYPE字段", 'digoxin AND heart failure AND PUBTYPE:"Clinical Trial"', None),
    ("Q02", "A1复测·PUBTYPE裸式", 'PUBTYPE:"Clinical Trial"', None),
    ("Q03", "A1复测·MESH替代", 'digoxin AND heart failure AND MESH:"Clinical Trial"', r"mortality|death"),
    ("Q04", "A1复测·不加类型词", 'digoxin AND heart failure', None),
    ("Q05", "CC-10犬类", 'rapamycin AND dog AND aging AND healthspan', r"\d"),
    ("Q06", "CC-10犬类TRIAD", '"TRIAD" AND rapamycin AND dog', r"\d"),
    ("Q07", "CC-8丙类年龄依赖", '"senescent cells" AND clearance AND "life span" AND old', r"life span|lifespan|%"),
    ("Q08", "CC-8丙类DQ/FT-4392", '(dasatinib AND quercetin) AND (senolytic OR "senescent") AND aged', r"%|aged|old"),
    ("Q09", "CC-9乙类必要性", 'autophagy AND longevity AND ("Atg5" OR "Atg7" OR "autophagy-deficient")', r"autophag"),
    ("Q10", "CC-7甲类基线", 'rapamycin AND mice AND lifespan AND ("600 days" OR "late in life")', r"%|lifespan"),
    ("Q11", "CC-1丙候选", 'cytochrome c oxidase AND mitochondrial AND ("960" OR "980") AND action spectrum', r"\b\d{3}\s?nm"),
]

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
# 连通性闸门：轻探测（不走 fetch 的重试栈），通道不通就等
def probe():
    p = subprocess.run(["curl", "-s", "--max-time", "20", BASE +
                        "?query=digoxin&format=json&pageSize=1"],
                       capture_output=True, text=True)
    return p.returncode == 0 and len(p.stdout) > 50
for g in range(6):
    if probe():
        print("gate OK after %d waits" % g)
        break
    print("gate wait %d" % g)
    time.sleep(8)
log = []
md = ["# 第四轮·补采狙击读数", "",
      "性质：判据未改，仅补未闭合项与工具自检。执行 UTC " + stamp + "。",
      "通道：curl 子进程（python urllib 本批出现间歇 DNS 失败，如实登记）。", ""]
for qid, cc, q, pat in QUERIES:
    try:
        d = fetch(q)
    except Exception as e:
        log.append([qid, cc, q, "传输失败", str(e)[:80], "", ""])
        md.append("## %s (%s)\n- 检索式 `%s`｜**传输层失败** %s\n" % (qid, cc, q, e))
        continue
    hit = d.get("hitCount")
    (RAWD / ("%s_%s.json" % (qid, re.sub(r"[^\w\u4e00-\u9fff-]", "_", cc)))).write_text(
        json.dumps(d, ensure_ascii=False), encoding="utf-8")
    picked = []
    if pat:
        rx = re.compile(pat, re.I)
        for r in d.get("resultList", {}).get("result", []):
            for s in [x for x in sents(r.get("abstractText") or "") if rx.search(x)][:4]:
                picked.append((r.get("pubYear"), r.get("doi") or "NA",
                               (r.get("title") or "")[:90], s[:340]))
    log.append([qid, cc, q, hit, len(d.get("resultList", {}).get("result", [])), len(picked), ""])
    md.append("## %s (%s)\n- 检索式 `%s` hitCount=%s" % (qid, cc, q, hit))
    if picked:
        for y, doi, ti, s in picked[:8]:
            md.append("  - **%s** (%s | DOI=%s)\n    - 「%s」" % (ti, y, doi, s))
    elif pat:
        md.append("  - **NOT_FOUND**（本批未取到含该正则的逐字句）")
    md.append("")
    (OUT / "四轮读数.md").write_text("\n".join(md), encoding="utf-8")
    with open(OUT / "四轮日志.tsv", "w", encoding="utf-8") as f:
        f.write("id\t判据\t检索式\thitCount\t取回\t目标句数\t备注\n")
        for row in log:
            f.write("\t".join(str(x) for x in row) + "\n")
    time.sleep(1.5)                     # 降突发：沙箱 DNS 在高并发下会间歇失效

(OUT / "四轮读数.md").write_text("\n".join(md), encoding="utf-8")
with open(OUT / "四轮日志.tsv", "w", encoding="utf-8") as f:
    f.write("id\t判据\t检索式\thitCount\t取回\t目标句数\t备注\n")
    for row in log:
        f.write("\t".join(str(x) for x in row) + "\n")
print("stamp", stamp)
for row in log:
    print(row[0], row[1], "hit=", row[3], "sents=", row[5])
