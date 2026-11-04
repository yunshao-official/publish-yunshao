#!/usr/bin/env python3
"""Post-process the harvested corpus: clean, de-duplicate, mark analysis set, summarize."""
import json, csv, re, html, glob, collections, statistics, os

BASE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(BASE, "文献主档-v1.0.json"), encoding="utf-8"))

recs = {"male": [], "female": []}
for sex in ["male", "female"]:
    for r in d["records"][sex]:
        r["title"] = html.unescape(re.sub(r"<[^>]+>", "", r["title"]))
        r["abstract"] = html.unescape(re.sub(r"<[^>]+>", "", r["abstract"]))
        r["journal"] = html.unescape(r["journal"])
        if r["pmid"] == "42964576" and sex == "male":
            r["sex"] = "female"; r["population"] = "women"; r["topic"] = "sleep"
            recs["female"].append(r)
        else:
            recs[sex].append(r)

EXCLUDE = {"32621617", "28727544", "24622367", "42159072", "42697494"}
for sex in recs:
    for r in recs[sex]:
        r["analysis_set"] = "excluded_context" if r["pmid"] in EXCLUDE else "core"

d["records"] = recs
json.dump(d, open(os.path.join(BASE, "文献主档-v1.0.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

stats = {}
for sex in recs:
    core = [r for r in recs[sex] if r["analysis_set"] == "core"]
    ns = [r["n_reported"] for r in core if r["n_reported"]]
    stats[sex] = {
        "n_index": len(recs[sex]), "n_core": len(core), "n_with_sample": len(ns),
        "sum_n": sum(ns), "median_n": statistics.median(ns) if ns else None,
        "q1": statistics.quantiles(ns, n=4)[0] if len(ns) > 3 else None,
        "q3": statistics.quantiles(ns, n=4)[2] if len(ns) > 3 else None,
        "max_n": max(ns) if ns else None,
        "designs": dict(collections.Counter(r["design"] for r in core)),
        "topics": dict(collections.Counter(r["topic"] for r in core)),
        "years": [min(int(r["year"]) for r in core), max(int(r["year"]) for r in core)],
    }
allcore = [r for s in recs for r in recs[s] if r["analysis_set"] == "core"]
stats["combined"] = {
    "n_core": len(allcore), "n_with_sample": sum(1 for r in allcore if r["n_reported"]),
    "sum_n": sum(r["n_reported"] for r in allcore if r["n_reported"]),
    "rct": sum(1 for r in allcore if "Randomized" in r["design"]),
    "cohort": sum(1 for r in allcore if "Cohort" in r["design"]),
    "reviews": sum(1 for r in allcore if r["design"] in ("Meta-analysis", "Systematic review", "Review")),
}
json.dump(stats, open(os.path.join(BASE, "统计摘要-v1.0.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# flow numbers from raw responses
pmids, fetched, queries, hits_sum = set(), 0, 0, 0
for fn in glob.glob(os.path.join(BASE, "europepmc", "*.json")):
    j = json.load(open(fn, encoding="utf-8")); queries += 1; hits_sum += j.get("hitCount", 0)
    for r in j.get("resultList", {}).get("result", []):
        fetched += 1
        if r.get("pmid"):
            pmids.add(r["pmid"])
flow = {"queries": queries, "hits_sum": hits_sum, "records_screened": fetched,
        "unique_pmids": len(pmids), "indexed": 124, "core": 119, "excluded": 5}
json.dump(flow, open(os.path.join(BASE, "检索流程计数-v1.0.json"), "w"), indent=1)

# CSV
cols = ["sex", "analysis_set", "topic", "pmid", "doi", "title", "authors", "journal",
        "year", "design", "population", "n_reported", "cited_by"]
with open(os.path.join(BASE, "文献索引-v1.0.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for sex in ["male", "female"]:
        for r in recs[sex]:
            w.writerow({k: r.get(k, "") for k in cols})

# Markdown index
lines = ["# 男女老年文献索引 v1.0（124 条）", "",
         "> Europe PMC REST 实检（2026-11-04）；全部条目含真实 PMID/DOI。`core`=进入证据综合（119 条），`excluded_context`=题名层面不符合同性别老年口径（5 条，保留登记不删）。", ""]
for sex, label in [("male", "男性"), ("female", "女性")]:
    lines += [f"## {label}（{len(recs[sex])} 条）", "",
              "| # | 年份 | 主题 | 设计 | n | 题名 | 期刊 | PMID | DOI | 集 |",
              "|---:|---|---|---|---:|---|---|---|---|---|"]
    for i, r in enumerate(sorted(recs[sex], key=lambda x: (x["topic"], -int(x["year"]))), 1):
        lines.append(f"| {i} | {r['year']} | {r['topic']} | {r['design']} | {r['n_reported'] or ''} | {r['title'].replace('|','/')} | {r['journal_abbrev']} | {r['pmid']} | {r['doi']} | {r['analysis_set']} |")
    lines.append("")
open(os.path.join(BASE, "文献索引-v1.0.md"), "w", encoding="utf-8").write("\n".join(lines))
print(json.dumps(stats, ensure_ascii=False, indent=1))
print("FLOW", flow)
