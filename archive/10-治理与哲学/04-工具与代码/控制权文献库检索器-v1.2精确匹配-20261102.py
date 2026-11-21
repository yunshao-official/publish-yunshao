#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
控制权架构文献库检索器 v1.2 精确匹配补跑（2026-11-02）
版本账（每一步都记，不改已冻结的判据口径）：
  v1.0 首轮 84 查询 → 467 条 条（D03 18/42 等四域缺额，判负照记）
  v1.1 追加 27 查询（只加查询串，关键词表/打分/去重/档位未动）→ 487 条（D03 25/42）
  v1.2 本件：D03（否决权与保护性条款）单域补跑，把检索方式从"模糊书目/全文相关"换成
      OpenAlex 的 `filter=title_and_abstract.search:` **布尔精确匹配**（AND/OR/引号短语），
      因为前两轮该域返回大量生物学"negative control（阴性对照）"一类同名异物噪声，score=0 被门槛挡掉。
      —— 只换检索式，**不换关键词表、不换打分规则、不换去重规则、不换档位口径**（判据书 §四 原文有效）。
  缺额成因如实记：D03 的部分候选被 D02/D10 先行占用（判据书 §四 第 4 条"首见域保留"），
      该规则本件不改动，只用新检索式扩大 D03 的独立候选面。
"""
import importlib.util
import json
import os
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, fn):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


lit11 = _load("lit11", "控制权文献库检索器-v1.1补跑-20261102.py")
lit10 = lit11.lit10
OUT, RAW, DOMAINS, RETRIEVED = lit11.OUT, lit11.RAW, lit11.DOMAINS, lit11.RETRIEVED

V12 = {
    "D03": [
        'veto AND shareholder',
        '"protective provisions" AND investor',
        'supermajority AND corporate AND voting',
        '"blocking minority" OR "minority veto"',
        'deadlock AND "board of directors"',
        'shareholder AND ("consent right" OR "approval right")',
        '"term sheet" AND (veto OR "protective provision")',
        'minority AND protection AND (veto OR "special majority")',
    ],
}


def main():
    pool = json.load(open(os.path.join(OUT, "候选池-v1.1.json"), encoding="utf-8"))
    qlog, stats = [], {}
    for code, exprs in V12.items():
        dom = [d for d in DOMAINS if d["code"] == code][0]
        for qi, expr in enumerate(exprs, 1):
            slug = "%s-op-v12-%02d" % (code, qi)
            url = ("https://api.openalex.org/works?filter=title_and_abstract.search:%s"
                   "&per-page=25&select=id,doi,title,publication_date,authorships,"
                   "abstract_inverted_index,cited_by_count,primary_location"
                   % urllib.parse.quote(expr))
            obj, err = lit10.fetch_json(url)
            qlog.append("%s|%s|%s|%s" % (slug, "openalex", expr, "OK" if obj else "FAILED " + str(err)))
            if obj is None:
                stats[slug] = {"err": err, "returned": 0, "scored": 0}
                continue
            json.dump(obj, open(os.path.join(RAW, slug + ".json"), "w", encoding="utf-8"),
                      ensure_ascii=False)
            recs = lit11.parse_openalex(obj.get("results", []) or [], dom, slug)
            ns = 0
            for r in recs:
                r["ver"] = "v1.2"
                tl = (r["title"] + " " + r["summary"]).lower()
                sc, hits = lit10.score_of(tl, dom["kw"])
                r["score"], r["hits"], r["retrieved"] = sc, hits, RETRIEVED
                pool.append(r)
                if sc >= 1:
                    ns += 1
            stats[slug] = {"channel": "openalex", "expr": expr,
                           "returned": len(obj.get("results", []) or []), "scored": ns}
            sys.stdout.write("%s ret=%s scored=%d\n" % (slug, stats[slug]["returned"], ns))
            sys.stdout.flush()
            time.sleep(0.6)

    json.dump(pool, open(os.path.join(OUT, "候选池-v1.2.json"), "w", encoding="utf-8"), ensure_ascii=False)
    open(os.path.join(RAW, "queries-v1.2.txt"), "w", encoding="utf-8").write("\n".join(qlog) + "\n")

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
    json.dump(final, open(os.path.join(OUT, "文献主档-v1.2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    st = {"retrieved": RETRIEVED, "version": "v1.2", "total_records": len(final),
          "history": {"v1.0": 467, "v1.1": 487, "v1.2": len(final)},
          "per_domain": per,
          "method_change": "仅 D03 域改用 OpenAlex title_and_abstract.search 布尔精确匹配；关键词表/打分/去重/档位口径未改",
          "v12_queries": V12, "per_query_v12": stats,
          "failed_v12": [l for l in qlog if "FAILED" in l],
          "level_counts": {lv: sum(1 for c in final if c["level"] == lv) for lv in ("核", "待核")},
          "channel_counts": {ch: sum(1 for c in final if c["channel"] == ch) for ch in ("crossref", "openalex")},
          "ver_counts": {v: sum(1 for c in final if c.get("ver") == v) for v in ("v1.0", "v1.1", "v1.2")}}
    json.dump(st, open(os.path.join(OUT, "统计-v1.2.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    write_volumes(final)
    print("TOTAL=%d PER=%s" % (len(final), per))


def write_volumes(final):
    for dom in DOMAINS:
        recs = [c for c in final if c["dom"] == dom["code"]]
        supp = lit11.SUPP.get(dom["code"])
        v12 = V12.get(dom["code"])
        L = ["---",
             'title: "控制权架构文献库·%s·%s"' % (dom["num"], dom["name"]),
             "date: 2026-11-02", "version: 1.2",
             "status: 结果件（v1.2 合并版·实到条目%d/配额42；v1.0 首轮 467 条、v1.1 补至 487 条、v1.2 终至见统计-v1.2.json，全过程判负照记）" % len(recs),
             "constants: 检索日2026-11-02 / 通道Crossref+OpenAlex / 判据书v1.0四项口径全程未改 / v1.1只加查询串 / v1.2仅D03改布尔精确匹配",
             'summary: "%s（%s）域文献条目，全部带 DOI 或 OpenAlex ID、被引数与检索日期，可用 04-工具与代码 三份检索器脚本复算。档位：核＝元数据齐且有摘要；待核＝摘要缺失需人工补。"' % (dom["name"], dom["code"]),
             "---", "",
             "# 控制权架构文献库 · %s · %s（%s）" % (dom["num"], dom["name"], dom["code"]), "",
             "> 委托人：知世 ｜ 检索执行：Qoder ｜ 检索日：2026-11-02 ｜ 判据：`01-理论与推导/控制权架构文献库·检索判据书-v1.0-20261102.md`",
             "> 查询串与补跑账：v1.0 首轮 7 串（冻结）；v1.1 追加串只加查询、不动口径；v1.2 仅否决权域改布尔精确匹配。全部原样列出，便于复算。",
             "> 【v1.0 冻结查询串】Crossref 4 ＋ OpenAlex 3："]
        for q in dom["cr"]:
            L.append(">   · crossref｜`%s`" % q)
        for q in dom["oa"]:
            L.append(">   · openalex｜`%s`" % q)
        if supp:
            L.append("> 【v1.1 追加查询串】（本域首轮未达配额）：")
            for q in supp["cr"]:
                L.append(">   · crossref｜`%s`" % q)
            for q in supp["oa"]:
                L.append(">   · openalex｜`%s`" % q)
        if v12:
            L.append("> 【v1.2 布尔精确匹配式】（OpenAlex `title_and_abstract.search`，AND/OR/引号短语；改的是检索式不是判据）：")
            for e in v12:
                L.append(">   · openalex-精确｜`%s`" % e)
        L.append("> 本卷实到 **%d** 条（配额 42）｜档位：核 %d / 待核 %d｜通道：Crossref %d / OpenAlex %d" % (
            len(recs), sum(1 for r in recs if r["level"] == "核"),
            sum(1 for r in recs if r["level"] == "待核"),
            sum(1 for r in recs if r["channel"] == "crossref"),
            sum(1 for r in recs if r["channel"] == "openalex")))
        L.append("")
        for i, r in enumerate(recs, 1):
            au = "; ".join(r["authors"][:6]) + (" 等" if len(r["authors"]) > 6 else "")
            L.append("[%d] %s (%d). %s. %s — %s ｜ %s ｜ 被引%d ｜ score=%d ｜ %s ｜ 入库轮次%s ｜ 检索 %s" % (
                i, au, r["date"], r["title"], r["venue"] or "（载体未记）",
                r["doi"] or r["id"], r["channel"], r["cites"], r["score"], r["level"],
                r.get("ver", "v1.0"), r["url"]))
            if r["summary"]:
                L.append("    摘要：%s" % r["summary"][:420])
            L.append("    关联：%s" % lit10.rel_note(r, dom))
            L.append("")
        old = os.path.join(OUT, "%s·%s-v1.1-20261102.md" % (dom["num"], dom["slug"]))
        new = os.path.join(OUT, "%s·%s-v1.2-20261102.md" % (dom["num"], dom["slug"]))
        open(new, "w", encoding="utf-8").write("\n".join(L) + "\n")
        if os.path.exists(old):
            os.remove(old)


if __name__ == "__main__":
    main()
