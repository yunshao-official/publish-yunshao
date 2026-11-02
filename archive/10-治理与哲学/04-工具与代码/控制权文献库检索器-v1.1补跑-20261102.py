#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
控制权架构文献库检索器 v1.1 补跑（2026-11-02）
为什么要 v1.1（判负照记后的唯一合规补法）：
  v1.0 实到 467 条（84 查询），四个域未达配额——D03 否决权与保护性条款 18/42（缺 24）、
  D09 混合所有制与特殊管理股 33/42（缺 9）、D04 董事高管与指挥权 39/42（缺 3）、D11 域外对照 41/42（缺 1）。
  判据书 §三 写明"执行后不改写、不追加（追加须另立 v1.1）"，故本件：
  ① 只追加查询串，**不改动 v1.0 冻结的关键词表、打分规则、去重规则、档位口径**；
  ② 原始响应照 v1.0 规矩落盘 raw/，并单写 queries-v1.1.txt；
  ③ 合并 v1.0 候选池后按同一门槛重选（每域上限 42），输出 文献主档-v1.1.json 与统计-v1.1.json；
  ④ 十二卷条目件就地升版为 v1.1，并在卷首列出本域全部查询串（v1.0＋v1.1）与补跑理由。
复用：v1.0 脚本的解析与打分函数（同一实现，避免口径漂移）。
"""
import importlib.util
import json
import os
import re
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
V10_PATH = os.path.join(HERE, "控制权文献库检索器-v1.0-20261102.py")
spec = importlib.util.spec_from_file_location("lit10", V10_PATH)
lit10 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lit10)

OUT = lit10.OUT
RAW = lit10.RAW
DOMAINS = lit10.DOMAINS
RETRIEVED = lit10.RETRIEVED

# ------------------------------------------------ v1.1 追加查询串（只加查询，不改判据）
SUPP = {
    "D03": {
        "cr": ["shareholder consent rights agreement enumeration",
               "reserved matters supermajority articles of association",
               "negative control minority shareholders corporate law",
               "blocking minority voting thresholds corporate decisions",
               "venture capital term sheet investor protection rights",
               "veto power shareholder protection empirical study"],
        "oa": ["protective provisions preferred shareholders board seats",
               "minority shareholder veto deadlock corporate governance"],
    },
    "D04": {
        "cr": ["director nomination rights shareholder agreements board composition",
               "company seal apparent authority contract validity China",
               "managing director appointment removal shareholder control",
               "legal representative corporate liability China governance"],
        "oa": ["board interlocks shareholder control executive appointments",
               "chief executive officer dismissal board authority"],
    },
    "D09": {
        "cr": ["golden shares member states free movement of capital restrictions",
               "mixed ownership reform control rights state-owned enterprises China",
               "special management shares Chinese internet platforms",
               "state ownership pyramid control minority shareholders",
               "party organizations boards of directors China corporate governance"],
        "oa": ["soe governance minority investor protection mixed ownership",
               "golden share proportionality case law European Union"],
    },
    "D11": {
        "cr": ["dual class shares long term underperformance founder control",
               "weighted voting rights sunset clause listing rules comparison",
               "one share multiple votes Singapore listing reform",
               "controlled company conflicts of interest Delaware doctrine"],
        "oa": ["differential voting rights ownership structure performance meta analysis",
               "tech founder controlled firms innovation governance"],
    },
}

V11_QINFO = {}


def parse_crossref(items, dom, slug):
    out = []
    for it in items:
        doi = (it.get("DOI") or "").strip()
        title = lit10.strip_tags((it.get("title") or [""])[0])
        yr = lit10.get_year_cr(it)
        summ = lit10.strip_tags(it.get("abstract", ""))[:900]
        au = lit10.authors_cr(it)
        if doi and title and yr and au and 1950 <= yr <= 2026:
            rec = dict(q=slug, dom=dom["code"], channel="crossref", id=doi.lower(),
                       doi=doi.lower(), url="https://doi.org/" + doi.lower(), title=title,
                       date=yr, authors=au, venue=lit10.venue_cr(it),
                       cites=int(it.get("is-referenced-by-count") or 0), summary=summ, ver="v1.1")
            out.append(rec)
    return out


def parse_openalex(items, dom, slug):
    out = []
    for it in items:
        oid = (it.get("id") or "").rstrip().split("/")[-1]
        doi = (it.get("doi") or "").replace("https://doi.org/", "").strip().lower()
        title = lit10.strip_tags(it.get("title") or "")
        ytxt = it.get("publication_date") or ""
        yr = int(ytxt[:4]) if len(ytxt) >= 4 and ytxt[:4].isdigit() else None
        summ = lit10.oa_abstract(it.get("abstract_inverted_index"))
        au = lit10.authors_oa(it)
        ident = doi or oid
        if ident and title and yr and au and 1950 <= yr <= 2026:
            rec = dict(q=slug, dom=dom["code"], channel="openalex", id=ident or oid, doi=doi,
                       url=("https://doi.org/" + doi) if doi else (it.get("id") or ""), title=title,
                       date=yr, authors=au, venue=lit10.venue_oa(it),
                       cites=int(it.get("cited_by_count") or 0), summary=summ, ver="v1.1")
            out.append(rec)
    return out


def main():
    v10 = json.load(open(os.path.join(OUT, "文献主档-v1.0.json"), encoding="utf-8"))
    for r in v10:
        r["ver"] = "v1.0"
    pool = list(v10)
    qlog, stats = [], {}

    for code, groups in SUPP.items():
        dom = [d for d in DOMAINS if d["code"] == code][0]
        for ch, qs in (("crossref", groups["cr"]), ("openalex", groups["oa"])):
            for qi, q in enumerate(qs, 1):
                slug = "%s-%s-v11-%02d" % (code, ch[:2], qi)
                if ch == "crossref":
                    url = ("https://api.crossref.org/works?query.bibliographic=%s&rows=25"
                           "&select=DOI,title,author,issued,container-title,publisher,"
                           "is-referenced-by-count,abstract,type" % urllib.parse.quote(q))
                else:
                    url = ("https://api.openalex.org/works?search=%s&per-page=25&select="
                           "id,doi,title,publication_date,authorships,abstract_inverted_index,"
                           "cited_by_count,primary_location" % urllib.parse.quote(q))
                obj, err = lit10.fetch_json(url)
                qlog.append("%s|%s|%s|%s" % (slug, ch, q, "OK" if obj else "FAILED " + str(err)))
                if obj is None:
                    stats[slug] = {"err": err, "returned": 0, "scored": 0}
                    continue
                json.dump(obj, open(os.path.join(RAW, slug + ".json"), "w", encoding="utf-8"),
                          ensure_ascii=False)
                items = ((obj.get("message", {}) or {}).get("items", []) if ch == "crossref"
                         else obj.get("results", [])) or []
                recs = parse_crossref(items, dom, slug) if ch == "crossref" else parse_openalex(items, dom, slug)
                ns = 0
                for r in recs:
                    tl = (r["title"] + " " + r["summary"]).lower()
                    sc, hits = lit10.score_of(tl, dom["kw"])
                    r["score"], r["hits"], r["retrieved"] = sc, hits, RETRIEVED
                    pool.append(r)
                    if sc >= 1:
                        ns += 1
                stats[slug] = {"channel": ch, "q": q, "returned": len(items), "scored": ns}
                sys.stdout.write("%s %s ret=%d scored=%d\n" % (slug, ch, len(items), ns))
                sys.stdout.flush()
                time.sleep(0.6)

    json.dump(pool, open(os.path.join(OUT, "候选池-v1.1.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    open(os.path.join(RAW, "queries-v1.1.txt"), "w", encoding="utf-8").write("\n".join(qlog) + "\n")

    # -------- 同门槛重选（v1.0 判据书 §四，一字未改）
    seen_doi, seen_title, final, per = {}, {}, [], {}
    for dom in DOMAINS:
        cands = [c for c in pool if c["dom"] == dom["code"] and c["score"] >= 1]
        cands.sort(key=lambda c: (-c["score"], -c["cites"], c["id"]))
        picked = []
        for c in cands:
            if len(picked) >= 42:
                break
            d, t = c["doi"].lower(), lit10.norm_title(c["title"])
            if (d and d in seen_doi) or t in seen_title:
                continue
            if d:
                seen_doi[d] = 1
            seen_title[t] = 1
            c["level"] = "核" if c["summary"] else "待核"
            picked.append(c)
        final.extend(picked)
        per[dom["code"]] = len(picked)

    final.sort(key=lambda c: (c["dom"], -c["score"], -c["cites"], c["id"]))
    for c in final:
        c.pop("hits", None) if False else None
    json.dump(final, open(os.path.join(OUT, "文献主档-v1.1.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    st = {"retrieved": RETRIEVED, "version": "v1.1", "total_records": len(final),
          "v10_total": len(v10), "per_domain": per,
          "deficit_closed": {k: {"v10": v10c, "v11": per[k]} for k, v10c in
                             sorted(((d["code"], sum(1 for r in v10 if r["dom"] == d["code"])) for d in DOMAINS))},
          "supp_queries": {k: v["cr"] + v["oa"] for k, v in SUPP.items()},
          "per_query_v11": stats,
          "failed_v11": [l for l in qlog if "FAILED" in l],
          "level_counts": {lv: sum(1 for c in final if c["level"] == lv) for lv in ("核", "待核")},
          "channel_counts": {ch: sum(1 for c in final if c["channel"] == ch) for ch in ("crossref", "openalex")},
          "ver_counts": {v: sum(1 for c in final if c.get("ver") == v) for v in ("v1.0", "v1.1")}}
    json.dump(st, open(os.path.join(OUT, "统计-v1.1.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    write_volumes(final)
    print("TOTAL=%d PER=%s" % (len(final), per))


def write_volumes(final):
    for dom in DOMAINS:
        recs = [c for c in final if c["dom"] == dom["code"]]
        supp = SUPP.get(dom["code"])
        L = ["---",
             'title: "控制权架构文献库·%s·%s"' % (dom["num"], dom["name"]),
             "date: 2026-11-02", "version: 1.1",
             "status: 结果件（v1.1 合并版·实到条目%d/配额42；v1.0 为 42 配额制下的首轮，缺口见执行报告，判负照记）" % len(recs),
             "constants: 检索日2026-11-02 / 通道Crossref+OpenAlex / 判据书v1.0冻结未改 / v1.1仅追加查询串",
             'summary: "%s（%s）域文献条目，全部带 DOI 或 OpenAlex ID、被引数与检索日期，可用 04-工具与代码 的检索器脚本复算。档位：核＝元数据齐且有摘要；待核＝摘要缺失需人工补。"' % (dom["name"], dom["code"]),
             "---", "",
             "# 控制权架构文献库 · %s · %s（%s）" % (dom["num"], dom["name"], dom["code"]), "",
             "> 委托人：知世 ｜ 检索执行：Qoder ｜ 检索日：2026-11-02 ｜ 判据：`01-理论与推导/控制权架构文献库·检索判据书-v1.0-20261102.md`（关键词表、打分、去重、档位四项口径 v1.1 未改动）",
             "> v1.0 查询串（Crossref 4 ＋ OpenAlex 3，首轮冻结）："]
        for q in dom["cr"]:
            L.append(">   · crossref｜`%s`" % q)
        for q in dom["oa"]:
            L.append(">   · openalex｜`%s`" % q)
        if supp:
            L.append("> v1.1 追加查询串（本域首轮未达配额，按判据书 §三 另立版本补跑；补跑理由与实到数见 `控制权架构文献库·执行报告-v1.1-20261102.md`）：")
            for q in supp["cr"]:
                L.append(">   · crossref｜`%s`" % q)
            for q in supp["oa"]:
                L.append(">   · openalex｜`%s`" % q)
        L.append("> 本卷实到 **%d** 条（配额 42）｜档位：核 %d / 待核 %d｜通道：Crossref %d / OpenAlex %d" % (
            len(recs), sum(1 for r in recs if r["level"] == "核"),
            sum(1 for r in recs if r["level"] == "待核"),
            sum(1 for r in recs if r["channel"] == "crossref"),
            sum(1 for r in recs if r["channel"] == "openalex")))
        L.append("")
        for i, r in enumerate(recs, 1):
            au = "; ".join(r["authors"][:6]) + (" 等" if len(r["authors"]) > 6 else "")
            L.append("[%d] %s (%d). %s. %s — %s ｜ %s ｜ 被引%d ｜ score=%d ｜ %s ｜ 检索 %s" % (
                i, au, r["date"], r["title"], r["venue"] or "（载体未记）",
                r["doi"] or r["id"], r["channel"], r["cites"], r["score"], r["level"], r["url"]))
            if r["summary"]:
                L.append("    摘要：%s" % r["summary"][:420])
            L.append("    关联：%s" % lit10.rel_note(r, dom))
            L.append("")
        fn = os.path.join(OUT, "%s·%s-v1.0-20261102.md" % (dom["num"], dom["slug"]))
        newfn = fn.replace("-v1.0-20261102.md", "-v1.1-20261102.md")
        open(newfn, "w", encoding="utf-8").write("\n".join(L) + "\n")
        if os.path.exists(fn) and fn != newfn:
            os.remove(fn)


if __name__ == "__main__":
    main()
