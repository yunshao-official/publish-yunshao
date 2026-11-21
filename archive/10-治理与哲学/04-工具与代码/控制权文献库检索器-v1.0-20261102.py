#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
控制权架构文献库检索器 v1.0（2026-11-02）
委托人：知世 ｜ 执行：Qoder
判据：archive/10-治理与哲学/01-理论与推导/控制权架构文献库·检索判据书-v1.0-20261102.md（已先冻结）
现货对照（第零律）：库内既有检索先例为 预想科技文献库-20260930（arXiv API，39 查询 173 篇），
  其抓取脚本未入库（轮子重造账 +1），故本件新写；schema 沿用其 文献主档-v1.0.json 六字段，另加通道与核验档位字段。
通道：Crossref REST（https://api.crossref.org/works）、OpenAlex（https://api.openalex.org/works）
输出：02-实验与数据/控制权架构文献库-20261102/{raw/*.json, raw/queries.txt, 文献主档-v1.0.json, 统计-v1.0.json, 卷*.md}
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REPO = "/data/workspace/publish-yunshao"
OUT = os.path.join(REPO, "archive/10-治理与哲学/02-实验与数据/控制权架构文献库-20261102")
RAW = os.path.join(OUT, "raw")
RETRIEVED = "2026-11-02"
UA = {"User-Agent": "yunshao-litfetch/1.0 (https://github.com/yunshao-official/publish-yunshao)"}

# ---------------------------------------------------------------- 域定义（判据书 §三、§四 冻结内容）
# kw: 相关性关键词（小写子串匹配）；rel: 命中后的中文关联注释（甲一·逢压缩词必注释）
DOMAINS = [
    dict(
        code="D01", num="卷一", name="公司法与利润分配", slug="gongsi-fa-yu-li-run-fenpei",
        cr=["minority shareholder dividend rights", "profit distribution company law",
            "legal capital maintenance creditor protection", "dividend policy shareholder wealth"],
        oa=["shareholder pre-emptive rights dilution", "mandatory dividend judicial intervention",
            "公司 股利 分配 少数股东"],
        kw=["dividend", "profit distribution", "minority shareholder", "capital maintenance",
            "pre-emptive", "payout", "retained earnings", "creditor protection", "distribution"],
        rel={"dividend": "分红请求权与利润分配（利益账主战场）",
             "profit distribution": "利润分配决议程序（利益账·公司机关权限）",
             "minority shareholder": "少数股东压制与救济（否决账补强）",
             "capital maintenance": "资本维持原则（利益外流闸门）",
             "pre-emptive": "优先认购权（防稀释=防指挥权被摊薄）",
             "payout": "派现政策（利益账兑现路径）",
             "creditor protection": "债权人保护（限制分红合法性边界）"},
    ),
    dict(
        code="D02", num="卷二", name="表决权与控制权工具", slug="biao-quan-yu-kong-zhi-quan-gong-ju",
        cr=["dual-class shares voting rights", "shareholder voting agreements control",
            "proxy voting shareholder control", "multiple voting shares"],
        oa=["concert party agreement voting control", "一致行动人 协议 表决权",
            "voting trust founder control"],
        kw=["dual-class", "dual class", "voting right", "multiple voting", "voting agreement",
            "proxy", "shareholder voting", "super-voting", "supermajority", "concert party",
            "differential voting"],
        rel={"dual-class": "同股不同权（AB 股·指挥账核心工具）",
             "voting right": "表决权配置（指挥账）", "multiple voting": "复数表决权",
             "voting agreement": "表决权拘束/委托协议", "proxy": "投票权委托",
             "super-voting": "超高倍率表决权", "supermajority": "特别多数门槛",
             "concert party": "一致行动人协议", "differential voting": "差别表决权（域外口径）"},
    ),
    dict(
        code="D03", num="卷三", name="否决权与保护性条款", slug="fou-jue-quan-yu-bao-hu-xing-tiao-kuan",
        cr=["protective provisions venture capital board", "veto rights shareholders contract",
            "supermajority voting corporate charter", "casting vote board deadlock"],
        oa=["shareholder agreement negative control", "minority blocking rights",
            "否决权 公司章程 条款"],
        kw=["veto", "protective provision", "blocking", "negative control", "casting vote",
            "deadlock", "consent right", "approval right", "supermajority", "reserved matter"],
        rel={"veto": "否决权条款本体（否决账）", "protective provision": "保护性条款清单",
             "blocking": "阻断门槛（blocking minority）", "negative control": "消极控制权",
             "casting vote": "主持决定票（僵局破局权）", "deadlock": "公司僵局处置",
             "consent right": "同意权（重大事项前置审批）", "reserved matter": "保留事项清单"},
    ),
    dict(
        code="D04", num="卷四", name="董事高管与指挥权（法定代表人·印章·授权）", slug="dong-shi-gao-guan-yu-zhi-hui-quan",
        cr=["board representation shareholder rights", "executive appointment removal control",
            "corporate seal authority China", "legal representative company China"],
        oa=["chief executive power board dismissal", "法定代表人 董事 控制",
            "chairman appointment control"],
        kw=["board of directors", "board seat", "director appointment", "executive",
            "legal representative", "corporate seal", "agency", "delegation", "chairman",
            "management control", "chief executive"],
        rel={"board of directors": "董事会构成（指挥账第一层）", "board seat": "董事席位提名权",
             "director appointment": "董事任免权", "legal representative": "法定代表人控制",
             "corporate seal": "印章控制（对外行为权）", "delegation": "授权与代理边界",
             "chairman": "董事长职权", "chief executive": "经理层权限划分"},
    ),
    dict(
        code="D05", num="卷五", name="婚姻与继承风险", slug="hun-yin-yu-ji-cheng-feng-xian",
        cr=["marital property division closely held business", "divorce corporate control family firm",
            "prenuptial agreement business ownership", "inheritance family business succession"],
        oa=["spousal property rights corporate control", "夫妻 共同财产 股权分割",
            "marital dissolution voting power"],
        kw=["marital", "divorce", "spouse", "prenuptial", "matrimonial", "inheritance",
            "succession", "family firm", "family business", "widow"],
        rel={"marital": "婚姻财产分割（股权折价风险）", "divorce": "离异导致控制权外流",
             "prenuptial": "婚内/婚前财产协议（默认项改写工具）", "matrimonial": "夫妻财产制",
             "inheritance": "继承引发的股权分散", "succession": "代际传承安排",
             "family firm": "家族企业治理对照"},
    ),
    dict(
        code="D06", num="卷六", name="代持·信托·SPV 与风险隔离", slug="dai-chi-xin-tuo-spv-yu-ge-li",
        cr=["nominee shareholding trust China", "voting trust corporate control",
            "family limited partnership control", "holding company pyramid ownership control"],
        oa=["equity nominee agreement enforceability", "trust beneficiary control rights",
            "股权 代持 信托 效力"],
        kw=["nominee", "trust", "holding company", "limited partnership", "pyramid",
            "separation of ownership", "SPV", "special purpose", "asset protection",
            "beneficial owner"],
        rel={"nominee": "股权代持效力与风险", "trust": "家族信托/表决权信托",
             "holding company": "控股公司层级（隔离+分红免税通道）",
             "limited partnership": "有限合伙持股平台（GP 小出资控大权）",
             "pyramid": "金字塔控制（现金流权与控制权分离）", "SPV": "特殊目的载体隔离",
             "asset protection": "债务隔离", "beneficial owner": "受益所有权认定"},
    ),
    dict(
        code="D07", num="卷七", name="IP 持有与许可·特许权使用费", slug="IP-chi-you-yu-xu-ke",
        cr=["royalty licensing intellectual property valuation",
            "work for hire invention assignment employee", "patent holding company licensing",
            "exclusive license bankruptcy licensee"],
        oa=["technology transfer royalty pricing", "inventor ownership university",
            "职务发明 权利 归属"],
        kw=["intellectual property", "patent", "licens", "royalt", "copyright",
            "work for hire", "invention assignment", "trade secret", "technology transfer",
            "workplace invention"],
        rel={"intellectual property": "IP 归属架构本体", "licens": "许可结构（独占/排他/普通）",
             "royalt": "特许权使用费（税负与利益账接口）", "patent": "专利权属",
             "work for hire": "职务创作归属", "invention assignment": "发明转让协议",
             "workplace invention": "职务发明奖励与归属", "trade secret": "商业秘密保护（体系文本）",
             "technology transfer": "技术转移定价"},
    ),
    dict(
        code="D08", num="卷八", name="税务与分红税负", slug="shui-wu-yu-fen-hong-shui-fu",
        cr=["double taxation of dividends corporate income tax", "dividend tax incidence shareholder",
            "tax treaty royalty withholding", "pass-through taxation small business"],
        oa=["imputation system dividend taxation", "股息 红利 个人所得税",
            "corporate tax burden dividend payout"],
        kw=["tax", "taxation", "dividend", "withholding", "imputation", "double taxation",
            "income tax", "tax planning", "effective tax", "evasion", "avoidance"],
        rel={"double taxation": "公司—股东两层税负（利益账核心）",
             "withholding": "代扣代缴（现金流摩擦）", "imputation": "归集抵免制（域外对照）",
             "tax planning": "税负筹划边界", "income tax": "所得税率结构",
             "tax avoidance": "合理筹划与反避税界线", "dividend": "分红课税"},
    ),
    dict(
        code="D09", num="卷九", name="混合所有制·特殊管理股·公共域控制", slug="hun-gai-yu-te-shu-guan-li-gu",
        cr=["golden share state ownership control", "mixed ownership reform China state-owned enterprise",
            "special management shares China media", "state ownership corporate governance performance"],
        oa=["party building corporate governance China", "golden share proportionality EU",
            "国有企业 治理 控制权"],
        kw=["golden share", "state-owned", "state owned", "mixed ownership", "privatisation",
            "soe", "government ownership", "party", "special management", "platinum share"],
        rel={"golden share": "黄金股（国家保留否决权·否决账制度先例）",
             "mixed ownership": "混改中的控制权安排", "state-owned": "国有控股治理结构",
             "special management": "特殊管理股（内容域否决权实践）",
             "party": "党建入章对指挥账的影响", "privatisation": "私有化保留特权条款"},
    ),
    dict(
        code="D10", num="卷十", name="争议与执行（对赌·僵局·解散·知情权）", slug="zheng-yi-yu-zhi-xing",
        cr=["valuation adjustment mechanism investor China", "corporate deadlock judicial dissolution",
            "shareholder inspection rights", "minority shareholder oppression remedy"],
        oa=["performance betting dispute enforcement", "corporate gridlock buyout remedy",
            "股东 知情权 诉讼"],
        kw=["deadlock", "dissolution", "buyout", "buy-back", "repurchase", "arbitration",
            "litigation", "oppression", "inspection", "unfair prejudice", "valuation adjustment",
            "gambling", "dispute"],
        rel={"deadlock": "僵局解决（否决权设计副作用必修项）", "dissolution": "司法解散风险",
             "buyout": "回购退出通道", "repurchase": "对赌回购条款",
             "valuation adjustment": "估值调整机制（对赌）效力", "oppression": "压迫救济",
             "inspection": "股东知情权（监督利益账）", "unfair prejudice": "不公正损害救济",
             "arbitration": "仲裁条款选择"},
    ),
    dict(
        code="D11", num="卷十一", name="域外对照（Delaware·港股 WVR·合伙人制）", slug="yu-wai-dui-zhao",
        cr=["Delaware dual class stock founder control", "one share ten votes Hong Kong listing",
            "Alibaba partnership structure control", "UK golden share privatisation control"],
        oa=["differential voting rights IPO underperformance", "founder control technology firms",
            "合伙人 制度 控制权"],
        kw=["dual class", "dual-class", "one share ten votes", "WVR", "weighted voting",
            "Delaware", "Hong Kong", "Alibaba", "partnership", "founder", "Snap", "IPO"],
        rel={"dual class": "双层股权境外经验与代价", "one share ten votes": "港股 18C 同股不同权",
             "weighted voting": "加权表决权制度", "Delaware": "特拉华判例（信义义务边界）",
             "Alibaba": "合伙人制（董事提名权与股权解绑）", "founder": "创始人控制存续研究",
             "Hong Kong": "港交所规则对照"},
    ),
    dict(
        code="D12", num="卷十二", name="控制权理论（所有权与控制分离·控制权私人收益）", slug="kong-zhi-quan-li-lun",
        cr=["separation of ownership and control Berle Means", "private benefits of control",
            "agency costs corporate governance", "wedge between ownership and voting rights"],
        oa=["director primacy corporate control", "managerial entrenchment takeover defense",
            "incomplete contracts control rights property rights"],
        kw=["control rights", "ownership control", "agency", "private benefit", "entrenchment",
            "corporate governance", "primacy", "incomplete contract", "property rights",
            "takeover", "wedge", "cash flow rights"],
        rel={"control rights": "控制权理论基准（Grossman-Hart 系）", "private benefit": "控制权私人收益",
             "agency": "代理成本", "entrenchment": "管理层 entrenched 与防线",
             "primacy": "董事会中心主义", "incomplete contract": "不完全合同与控制权配置",
             "wedge": "现金流权—控制权楔子（本规划核心指标）", "cash flow rights": "现金流权度量"},
    ),
]

CN = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"]


def fetch_json(url):
    """GET 一次，失败重试 1 次（判据书 §二）。返回 (obj, err)。"""
    err = None
    for attempt in (0, 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                body = r.read().decode("utf-8", "replace")
            return json.loads(body), None
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as e:
            err = "%s: %s" % (type(e).__name__, e)
            time.sleep(2.0)
    return None, err


def strip_tags(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def oa_abstract(inv):
    if not inv:
        return ""
    pos = {}
    for w, idxs in inv.items():
        for i in idxs:
            pos[i] = w
    return " ".join(pos[i] for i in sorted(pos))[:900]


def year_of(parts):
    for key in ("date-parts",):
        for dp in parts or []:
            for v in dp:
                if isinstance(v, int) and v > 1000:
                    return v
    return None


def get_year_cr(it):
    for f in ("issued", "published-print", "published-online", "created"):
        if it.get(f):
            y = year_of(it[f].get("date-parts"))
            if y:
                return y
    return None


def authors_cr(it):
    out = []
    for a in it.get("author", []) or []:
        nm = ", ".join([x for x in (a.get("family", ""), a.get("given", "")) if x]) or a.get("name", "")
        if nm:
            out.append(nm)
    if not out:
        for a in it.get("editor", []) or []:
            nm = ", ".join([x for x in (a.get("family", ""), a.get("given", "")) if x])
            if nm:
                out.append(nm)
    return out


def authors_oa(it):
    out = []
    for a in it.get("authorships", []) or []:
        nm = (a.get("author") or {}).get("display_name")
        if nm:
            out.append(nm)
    return out


def venue_cr(it):
    ct = it.get("container-title") or []
    if ct:
        return strip_tags(ct[0])
    return strip_tags(it.get("publisher", "") or "")


def venue_oa(it):
    pl = it.get("primary_location") or {}
    src = pl.get("source") or {}
    return strip_tags(src.get("display_name", "") or "")


def norm_title(t):
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", (t or "").lower())


def score_of(text_low, kws):
    s = 0
    hits = []
    for k in kws:
        if k in text_low:
            s += 1
            hits.append(k)
    return s, hits


def main():
    os.makedirs(RAW, exist_ok=True)
    qlog, stats, cands = [], {}, []
    per_q = {}
    for dom in DOMAINS:
        for ch, qs in (("crossref", dom["cr"]), ("openalex", dom["oa"])):
            for qi, q in enumerate(qs):
                slug = "%s-%s-%02d" % (dom["code"], ch[:2], qi + 1)
                if ch == "crossref":
                    url = ("https://api.crossref.org/works?query.bibliographic=%s&rows=20"
                           "&select=DOI,title,author,issued,container-title,publisher,"
                           "is-referenced-by-count,abstract,type" % urllib.parse.quote(q))
                else:
                    url = ("https://api.openalex.org/works?search=%s&per-page=20&select="
                           "id,doi,title,publication_date,authorships,abstract_inverted_index,"
                           "cited_by_count,primary_location" % urllib.parse.quote(q))
                obj, err = fetch_json(url)
                qlog.append("%s|%s|%s|%s" % (slug, ch, q, "OK" if obj else "FAILED " + str(err)))
                if obj is None:
                    stats[slug] = {"err": err, "n": 0}
                    continue
                with open(os.path.join(RAW, slug + ".json"), "w", encoding="utf-8") as f:
                    json.dump(obj, f, ensure_ascii=False)
                items = (obj.get("message", {}) or {}).get("items", []) if ch == "crossref" \
                    else obj.get("results", [])
                items = items or []
                per_q[slug] = len(items)
                n_ok = 0
                for it in items:
                    rec = None
                    if ch == "crossref":
                        doi = (it.get("DOI") or "").strip()
                        title = strip_tags((it.get("title") or [""])[0])
                        yr = get_year_cr(it)
                        summ = strip_tags(it.get("abstract", ""))[:900]
                        if doi and title and yr and authors_cr(it) and 1950 <= yr <= 2026:
                            rec = dict(q=slug, dom=dom["code"], channel="crossref",
                                       id=doi.lower(), doi=doi.lower(),
                                       url="https://doi.org/" + doi.lower(),
                                       title=title, date=yr, authors=authors_cr(it),
                                       venue=venue_cr(it), cites=int(it.get("is-referenced-by-count") or 0),
                                       summary=summ)
                    else:
                        oid = (it.get("id") or "").rstrip().split("/")[-1]
                        doi = (it.get("doi") or "").replace("https://doi.org/", "").strip().lower()
                        title = strip_tags(it.get("title") or "")
                        ytxt = it.get("publication_date") or ""
                        yr = int(ytxt[:4]) if len(ytxt) >= 4 and ytxt[:4].isdigit() else None
                        summ = oa_abstract(it.get("abstract_inverted_index"))
                        ident = doi or oid
                        if ident and title and yr and authors_oa(it) and 1950 <= yr <= 2026:
                            rec = dict(q=slug, dom=dom["code"], channel="openalex",
                                       id=ident or oid, doi=doi,
                                       url=("https://doi.org/" + doi) if doi else (it.get("id") or ""),
                                       title=title, date=yr, authors=authors_oa(it),
                                       venue=venue_oa(it), cites=int(it.get("cited_by_count") or 0),
                                       summary=summ)
                    if rec:
                        tl = (rec["title"] + " " + rec["summary"]).lower()
                        sc, hits = score_of(tl, dom["kw"])
                        rec["score"] = sc
                        rec["hits"] = hits
                        rec["retrieved"] = RETRIEVED
                        cands.append(rec)
                        if sc >= 1:
                            n_ok += 1
                stats[slug] = {"channel": ch, "q": q, "returned": len(items), "kept_scored": n_ok}
                sys.stdout.write("%s %s ret=%d scored=%d\n" % (slug, ch, len(items), n_ok))
                sys.stdout.flush()
                time.sleep(0.6)

    # -------- 选择与跨域去重（判据书 §四）
    seen_doi, seen_title, final, short = {}, {}, [], {}
    for dom in DOMAINS:
        pool = [c for c in cands if c["dom"] == dom["code"] and c["score"] >= 1]
        pool.sort(key=lambda c: (-c["score"], -c["cites"], c["id"]))
        picked = []
        for c in pool:
            if len(picked) >= 42:
                break
            d, t = c["doi"].lower(), norm_title(c["title"])
            if d and d in seen_doi:
                continue
            if t in seen_title:
                continue
            if d:
                seen_doi[d] = c["dom"]
            seen_title[t] = c["dom"]
            c["level"] = "核" if c["summary"] else "待核"
            picked.append(c)
        final.extend(picked)
        short[dom["code"]] = len(picked)

    final.sort(key=lambda c: (c["dom"], -c["score"], -c["cites"], c["id"]))
    with open(os.path.join(OUT, "文献主档-v1.0.json"), "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=1)
    with open(os.path.join(RAW, "queries.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(qlog) + "\n")
    summary_stats = {
        "retrieved": RETRIEVED, "total_records": len(final),
        "candidates_raw": len(cands), "per_domain": short,
        "per_query": stats, "returned_per_query": per_q,
        "level_counts": {lv: sum(1 for c in final if c["level"] == lv) for lv in ("核", "待核")},
        "channel_counts": {ch: sum(1 for c in final if c["channel"] == ch)
                           for ch in ("crossref", "openalex")},
        "failed_queries": [l for l in qlog if "FAILED" in l],
    }
    with open(os.path.join(OUT, "统计-v1.0.json"), "w", encoding="utf-8") as f:
        json.dump(summary_stats, f, ensure_ascii=False, indent=1)
    write_volumes(final, short)
    print("TOTAL=%d" % len(final), "PER_DOMAIN=%s" % short)


def rel_note(rec, dom):
    notes = []
    for k in rec["hits"]:
        n = dom["rel"].get(k)
        if n and n not in notes:
            notes.append(n)
        if len(notes) >= 2:
            break
    return "；".join(notes) if notes else "外围对照·待人工判读（关键词命中但无专注映射）"


def write_volumes(final, short):
    for dom in DOMAINS:
        recs = [c for c in final if c["dom"] == dom["code"]]
        lines = []
        lines.append("---")
        lines.append('title: "控制权架构文献库·%s·%s"' % (dom["num"], dom["name"]))
        lines.append("date: 2026-11-02")
        lines.append("version: 1.0")
        lines.append('status: 结果件（实拉入库·条目%d/%d；未达配额部分见统计-v1.0.json 与执行报告，判负照记）' % (len(recs), 42))
        lines.append("constants: 检索日2026-11-02 / 通道Crossref+OpenAlex / 判据书v1.0已先冻结")
        lines.append('summary: "%s（%s）域文献条目，全部带 DOI 或 OpenAlex ID + 检索日期，可机器复算。档位：核=元数据齐且有摘要；待核=摘要缺失需人工补。"' % (dom["name"], dom["code"]))
        lines.append("---")
        lines.append("")
        lines.append("# 控制权架构文献库 · %s · %s（%s）" % (dom["num"], dom["name"], dom["code"]))
        lines.append("")
        lines.append("> 委托人：知世 ｜ 检索执行：Qoder ｜ 检索日：2026-11-02 ｜ 判据：`01-理论与推导/控制权架构文献库·检索判据书-v1.0-20261102.md`")
        lines.append("> 查询串（Crossref 4 + OpenAlex 3，冻结未改）：")
        for q in dom["cr"]:
            lines.append(">   · crossref｜`%s`" % q)
        for q in dom["oa"]:
            lines.append(">   · openalex｜`%s`" % q)
        lines.append("> 本卷实到 **%d** 条（配额 42；缺 %d 条）｜档位统计：核 %d / 待核 %d" % (
            len(recs), 42 - len(recs),
            sum(1 for r in recs if r["level"] == "核"),
            sum(1 for r in recs if r["level"] == "待核")))
        lines.append("")
        for i, r in enumerate(recs, 1):
            au = "; ".join(r["authors"][:6]) + (" 等" if len(r["authors"]) > 6 else "")
            lines.append("[%d] %s (%d). %s. %s — %s ｜ %s ｜ 被引%d ｜ score=%d ｜ %s ｜ 检索 %s" % (
                i, au, r["date"], r["title"], r["venue"] or "（载体未记）",
                r["doi"] or r["id"], r["channel"], r["cites"], r["score"], r["level"], r["url"]))
            if r["summary"]:
                lines.append("    摘要：%s" % r["summary"][:420])
            lines.append("    关联：%s" % rel_note(r, dom))
            lines.append("")
        fn = os.path.join(OUT, "%s·%s-v1.0-20261102.md" % (dom["num"], dom["slug"]))
        with open(fn, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
