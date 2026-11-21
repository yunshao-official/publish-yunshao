#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云韶体系·化学与药物线 - 文献语料批量抓取脚本
使用 Europe PMC REST API 和 Crossref API
仅使用 Python 标准库
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import time
import os
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

# 配置
BASE_DIR = Path(__file__).parent
LITE_DIR = BASE_DIR / "lite"
CORE_DIR = BASE_DIR / "core"
LITE_DIR.mkdir(exist_ok=True)
CORE_DIR.mkdir(exist_ok=True)

EUROPE_PMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
CROSSREF_WORKS_URL = "https://api.crossref.org/works"

REQUEST_DELAY = 0.6
MAX_RETRIES = 2
TIMEOUT = 30

# 36条检索式
QUERIES = [
    ("A", "A1", 'digoxin AND heart failure AND PUBTYPE:"Clinical Trial"'),
    ("A", "A2", "dobutamine AND randomized"),
    ("A", "A3", "milrinone AND heart failure AND mortality"),
    ("A", "A4", "levosimendan AND trial"),
    ("A", "A5", "pimobendan"),
    ("A", "A6", "omecamtiv mecarbil AND GALACTIC"),
    ("A", "A7", "cardiac myosin activator"),
    ("A", "A8", "beta blocker AND heart failure AND mortality AND randomized"),
    ("A", "A9", "ivabradine AND SHIFT"),
    ("A", "A10", "(SERCA2a OR phospholamban) AND contractility"),
    ("B", "B1", "rapamycin AND lifespan AND mouse"),
    ("B", "B2", "metformin AND aging AND trial"),
    ("B", "B3", "(nicotinamide riboside OR NMN) AND human trial"),
    ("B", "B4", "(dasatinib AND quercetin) AND senolytic"),
    ("B", "B5", "fisetin AND senolytic"),
    ("B", "B6", "spermidine AND autophagy AND longevity"),
    ("B", "B7", "urolithin A AND mitophagy"),
    ("B", "B8", "(glycine AND N-acetylcysteine) OR GlyNAC"),
    ("B", "B9", "partial reprogramming AND aging"),
    ("B", "B10", "senescence AND intervention AND aged"),
    ("B", "B11", "caloric restriction AND primate"),
    ("B", "B12", "(torpor OR hypometabolism) AND organ protection"),
    ("C", "C1", "aducanumab AND withdrawal"),
    ("C", "C2", "rapamycin AND dog AND trial"),
    ("C", "C3", '(NMN OR nicotinamide riboside) AND randomized AND (no effect OR null OR unchanged)'),
    ("C", "C4", "senolytic AND (failure OR did not)"),
    ("C", "C5", "metformin AND cancer AND mortality"),
    ("C", "C6", 'NAD+ AND trial AND (no benefit OR futile)'),
    ("C", "C7", '"dietary supplement" AND "adjunctive cancer therapy" AND adverse'),
    ("C", "C8", "positive inotrope AND increased mortality"),
    ("D", "D1", '"cytochrome c oxidase" AND near-infrared AND absorption spectrum'),
    ("D", "D2", "photobiomodulation AND (720 OR 730 OR 960 OR 980) AND mitochondria"),
    ("D", "D3", "tissue optical window AND (hemoglobin OR water) absorption"),
    ("D", "D4", "myocardial efficiency AND oxygen consumption"),
    ("D", "D5", "cardiomyocyte renewal AND turnover AND age"),
    ("D", "D6", "cardiac power output AND cardiac index"),
]

CORE_QUERY_IDS = {"A3", "A8", "A9", "C2", "C8", "B1", "B11", "B3", "B9", "D1", "D2", "D4", "D5", "D6"}

log_entries = []
all_records = []  # lite records
core_records = []  # core records (with abstracts)


def safe_filename(group, qid, suffix=""):
    return f"{group}_{qid}{suffix}.json"


def fetch_json(url, params=None, retries=MAX_RETRIES):
    """通用HTTP GET → JSON，带重试"""
    if params:
        qs = urllib.parse.urlencode(params, doseq=True)
        full_url = f"{url}?{qs}"
    else:
        full_url = url

    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(full_url, headers={
                "User-Agent": "YunshaoChemCorpus/1.0 (mailto:research@example.org)"
            })
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data, resp.status
        except urllib.error.HTTPError as e:
            status = e.code
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")[:200]
            except Exception:
                pass
            if status == 400 and attempt < retries:
                # 语法错误不重试（400通常是查询语法问题）
                return {"error": body, "status": status}, status
            if attempt < retries:
                time.sleep(1.0)
                continue
            return {"error": body, "status": status}, status
        except Exception as e:
            if attempt < retries:
                time.sleep(1.0)
                continue
            return {"error": str(e), "status": 0}, 0
    return {"error": "unknown", "status": 0}, 0


def europe_pmc_search(query_str, result_type="lite", page_size=50, cursor_mark=None):
    """Europe PMC 搜索"""
    params = {
        "query": query_str,
        "format": "json",
        "pageSize": str(page_size),
        "resultType": result_type,
    }
    if cursor_mark:
        params["cursorMark"] = cursor_mark

    data, status = fetch_json(EUROPE_PMC_URL, params)
    if status != 200:
        return [], data.get("hitCount", 0), status

    hit_count = data.get("hitCount", 0)
    results = data.get("resultList", {}).get("result", [])
    return results, hit_count, status


def crossref_by_doi(doi):
    """通过DOI直接查Crossref"""
    url = f"{CROSSREF_WORKS_URL}/{urllib.parse.quote(doi, safe='')}"
    data, status = fetch_json(url)
    if status != 200:
        return None
    msg = data.get("message", {})
    if not msg or "title" not in msg:
        return None
    title = msg.get("title", [""])[0] if msg.get("title") else ""
    year_parts = msg.get("published", {}).get("date-parts", [[None]])
    year = year_parts[0][0] if year_parts and year_parts[0] else None
    return {"title": title, "year": year if year else "NA"}


def extract_pubtype(record):
    """提取pubType"""
    ptl = record.get("pubTypeList")
    if isinstance(ptl, list):
        return "; ".join(str(p.get("pubType", p) if isinstance(p, dict) else p) for p in ptl)
    if isinstance(ptl, dict):
        pts = ptl.get("pubType", [])
        if isinstance(pts, list):
            return "; ".join(str(p) for p in pts)
        return str(pts)
    return str(ptl) if ptl else "NA"


def record_to_row(rec, group, qid):
    """将API记录转为索引行"""
    return {
        "PMID": rec.get("pmid", "NA") or "NA",
        "DOI": rec.get("doi", "NA") or "NA",
        "年份": rec.get("pubYear", "NA") or "NA",
        "期刊": rec.get("journalTitle", "NA") or "NA",
        "标题": (rec.get("title", "NA") or "NA").replace("\n", " ").replace("\t", " "),
        "PUBTYPE": extract_pubtype(rec),
        "组编号": f"{group}{qid}",
        "abstractText": rec.get("abstractText", "") or "",
    }


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    t0 = time.time()
    print("=" * 60)
    print("云韶体系·化学与药物线 - 文献语料抓取")
    print(f"开始时间: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # ========== 第一遍 lite ==========
    print("\n[1/7] 第一遍 lite (36条) ...")
    for group, qid, query_str in QUERIES:
        print(f"  {qid} ...", end=" ", flush=True)
        ts = datetime.now(timezone.utc)
        results, hit_count, status = europe_pmc_search(query_str, result_type="lite", page_size=50)
        print(f"hit={hit_count}, got={len(results)}, status={status}")

        fname = safe_filename(group, qid)
        fpath = LITE_DIR / fname
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump({
                "query_id": qid, "group": group, "query": query_str,
                "hitCount": hit_count, "resultType": "lite",
                "timestamp": ts.isoformat(), "results": results
            }, f, ensure_ascii=False, indent=2)

        log_entries.append({
            "检索式编号": qid, "数据库": "Europe PMC",
            "检索式原文": query_str,
            "执行UTC时间": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "HTTP状态": status, "hitCount": hit_count,
            "取回条数": len(results), "语法修订": "-",
            "保存文件名": fname
        })

        for rec in results:
            all_records.append(record_to_row(rec, group, qid))

        time.sleep(REQUEST_DELAY)

    # ========== 第二遍 core ==========
    print(f"\n[2/7] 第二遍 core ({len(CORE_QUERY_IDS)}条) ...")
    for group, qid, query_str in QUERIES:
        if qid not in CORE_QUERY_IDS:
            continue
        print(f"  {qid}-core ...", end=" ", flush=True)
        ts = datetime.now(timezone.utc)
        results, hit_count, status = europe_pmc_search(query_str, result_type="core", page_size=25)
        print(f"hit={hit_count}, got={len(results)}, status={status}")

        fname = safe_filename(group, qid, "_core")
        fpath = CORE_DIR / fname
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump({
                "query_id": qid, "group": group, "query": query_str,
                "hitCount": hit_count, "resultType": "core",
                "timestamp": ts.isoformat(), "results": results
            }, f, ensure_ascii=False, indent=2)

        log_entries.append({
            "检索式编号": f"{qid}-core", "数据库": "Europe PMC",
            "检索式原文": query_str,
            "执行UTC时间": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "HTTP状态": status, "hitCount": hit_count,
            "取回条数": len(results), "语法修订": "-",
            "保存文件名": fname
        })

        for rec in results:
            row = record_to_row(rec, group, qid)
            core_records.append(row)
            # 更新all_records中匹配PMID的abstract
            for existing in all_records:
                if existing["PMID"] == row["PMID"] and row["abstractText"]:
                    existing["abstractText"] = row["abstractText"]
                    break

        time.sleep(REQUEST_DELAY)

    # ========== 检索日志 ==========
    print("\n[3/7] 写入检索日志 ...")
    log_path = BASE_DIR / "检索日志.tsv"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("检索式编号\t数据库\t检索式原文\t执行UTC时间\tHTTP状态\thitCount\t取回条数\t语法修订\t保存文件名\n")
        for e in log_entries:
            f.write(f"{e['检索式编号']}\t{e['数据库']}\t{e['检索式原文']}\t{e['执行UTC时间']}\t{e['HTTP状态']}\t{e['hitCount']}\t{e['取回条数']}\t{e['语法修订']}\t{e['保存文件名']}\n")

    # ========== 条目索引 ==========
    print("[4/7] 写入条目索引 ...")
    idx_path = BASE_DIR / "条目索引.tsv"
    with open(idx_path, "w", encoding="utf-8") as f:
        f.write("PMID\tDOI\t年份\t期刊\t标题\tPUBTYPE\t组编号\n")
        for r in all_records:
            title_safe = r["标题"].replace("\t", " ").replace("\n", " ")
            journal_safe = (r["期刊"] or "NA").replace("\t", " ").replace("\n", " ")
            pubtype_safe = (r["PUBTYPE"] or "NA").replace("\t", " ").replace("\n", " ")
            f.write(f"{r['PMID']}\t{r['DOI']}\t{r['年份']}\t{journal_safe}\t{title_safe}\t{pubtype_safe}\t{r['组编号']}\n")

    # 计数
    cnt_path = BASE_DIR / "条目索引-计数.txt"
    unique_pmids = set()
    group_pmids = {"A": set(), "B": set(), "C": set(), "D": set()}
    for r in all_records:
        pmid = r["PMID"]
        if pmid != "NA":
            unique_pmids.add(pmid)
            g = r["组编号"][0]
            if g in group_pmids:
                group_pmids[g].add(pmid)

    with open(cnt_path, "w", encoding="utf-8") as f:
        f.write(f"总条目数（含重复）: {len(all_records)}\n")
        f.write(f"去重PMID数: {len(unique_pmids)}\n\n")
        f.write("各组分档去重条数:\n")
        for g in ["A", "B", "C", "D"]:
            f.write(f"  {g}组: {len(group_pmids[g])} 条\n")
        f.write(f"\n各检索式命中详情:\n")
        for e in log_entries:
            f.write(f"  {e['检索式编号']}: hitCount={e['hitCount']}, 取回={e['取回条数']}, HTTP={e['HTTP状态']}\n")

    # ========== adopted candidates ==========
    print("[5/7] 筛选 adopted candidates ...")

    # 合并所有有abstract的记录用于筛选
    all_with_abstract = []
    seen_pmids = set()
    for r in core_records:
        key = r["PMID"]
        if key not in seen_pmids:
            seen_pmids.add(key)
            all_with_abstract.append(r)
    for r in all_records:
        key = r["PMID"]
        if key not in seen_pmids:
            seen_pmids.add(key)
            all_with_abstract.append(r)

    trial_kw = ["randomized", "randomised", "clinical trial", "rct", "trial"]
    review_kw = ["review", "meta-analysis", "systematic review", "meta analysis"]
    spectral_kw = ["spectrum", "absorption", "spectral", "wavelength", "nm", "nanometer", "optical"]
    quant_kw = ["efficiency", "cardiac output", "oxygen consumption", "turnover", "power output", "cardiac index", "ml/min", "vo2"]

    candidates = []
    for r in all_with_abstract:
        title = (r.get("标题") or "").lower()
        abstract = (r.get("abstractText") or "").lower()
        pubtype = (r.get("PUBTYPE") or "").lower()
        combined = f"{title} {abstract} {pubtype}"

        reasons = []
        if any(k in combined for k in trial_kw):
            reasons.append("随机试验")
        if any(k in combined for k in review_kw):
            reasons.append("综述")
        if any(k in combined for k in spectral_kw):
            reasons.append("光谱实测")
        if any(k in combined for k in quant_kw):
            reasons.append("定量生理")

        if not reasons:
            continue

        # 生成说明
        abs_text = r.get("abstractText", "") or ""
        if abs_text:
            first_sent = abs_text.split(".")[0].strip()
            desc = first_sent[:200]
        else:
            desc = (r.get("标题") or "")[:200]

        candidates.append({**r, "筛选理由": "/".join(reasons), "说明": desc})

    # 限制40-60
    if len(candidates) > 60:
        candidates = candidates[:60]

    adopted_path = BASE_DIR / "adopted-candidates.tsv"
    with open(adopted_path, "w", encoding="utf-8") as f:
        f.write("PMID\tDOI\t年份\t期刊\t标题\tPUBTYPE\t组编号\t筛选理由\t它究竟说什么\n")
        for c in candidates:
            title_safe = c["标题"].replace("\t", " ").replace("\n", " ")
            desc_safe = c["说明"].replace("\t", " ").replace("\n", " ")
            f.write(f"{c['PMID']}\t{c['DOI']}\t{c['年份']}\t{c['期刊']}\t{title_safe}\t{c['PUBTYPE']}\t{c['组编号']}\t{c['筛选理由']}\t{desc_safe}\n")

    print(f"  adopted candidates: {len(candidates)}")

    # ========== Crossref 核验 ==========
    print("[6/7] Crossref 核验 ...")
    crossref_results = []
    doi_candidates = [c for c in candidates if c.get("DOI") and c["DOI"] != "NA"]
    
    for i, c in enumerate(doi_candidates):
        doi = c["DOI"]
        local_title = c["标题"]
        print(f"  [{i+1}/{len(doi_candidates)}] {doi} ...", end=" ", flush=True)
        
        cr = crossref_by_doi(doi)
        if cr:
            cr_title = cr["title"]
            cr_year = cr["year"]
            # 比较：规范化后比较
            norm_local = re.sub(r'[^a-z0-9]', '', local_title.lower())[:40]
            norm_cr = re.sub(r'[^a-z0-9]', '', cr_title.lower())[:40]
            match = norm_local == norm_cr or norm_local in norm_cr or norm_cr in norm_local
            crossref_results.append({
                "DOI": doi,
                "Crossref返回题名": cr_title.replace("\t", " ").replace("\n", " "),
                "年份": cr_year,
                "是否与本地题名一致": "是" if match else "否",
                "一致判据": "规范化前40字符匹配" if match else "不匹配"
            })
            print(f"{'OK' if match else 'MISMATCH'}")
        else:
            crossref_results.append({
                "DOI": doi,
                "Crossref返回题名": "查询失败",
                "年份": "NA",
                "是否与本地题名一致": "未能核验",
                "一致判据": "Crossref无返回"
            })
            print("FAIL")
        
        time.sleep(REQUEST_DELAY)

    cr_path = BASE_DIR / "核验-Crossref.tsv"
    with open(cr_path, "w", encoding="utf-8") as f:
        f.write("DOI\tCrossref返回题名\t年份\t是否与本地题名一致\t一致判据\n")
        for r in crossref_results:
            f.write(f"{r['DOI']}\t{r['Crossref返回题名']}\t{r['年份']}\t{r['是否与本地题名一致']}\t{r['一致判据']}\n")

    # ========== 重要数值摘句 ==========
    print("\n[7/7] 提取重要数值摘句 ...")

    # 从所有有abstract的记录中提取
    quote_items = {
        "a": {
            "desc": "(a) 正性肌力药在心衰随机试验中的死亡率/有害信号",
            "kw": ["mortality", "death rate", "fatal", "harm", "adverse event", "increased mortality",
                    "inotrope", "milrinone", "dobutamine", "digoxin", "digitalis"],
            "numeric_kw": ["%", "percent", "hazard", "risk ratio", "RR ", "HR ", "odds"]
        },
        "b": {
            "desc": "(b) β受体阻滞剂在心衰中的死亡率降低百分比",
            "kw": ["beta blocker", "β-blocker", "beta-blocker", "metoprolol", "carvedilol", "bisoprolol"],
            "numeric_kw": ["%", "percent", "reduction", "mortality", "risk"]
        },
        "c": {
            "desc": "(c) ivabradine（SHIFT或同类）主要终点风险降低百分比",
            "kw": ["ivabradine", "SHIFT"],
            "numeric_kw": ["%", "percent", "reduction", "endpoint", "risk", "hazard"]
        },
        "d": {
            "desc": "(d) CCO或光生物调节的动作光谱/吸收峰的具体nm数值",
            "kw": ["nm", "nanometer", "wavelength", "absorption peak", "action spectrum",
                    "cytochrome c oxidase", "complex iv", "photobiomodulation", "near-infrared", "nir"],
            "numeric_kw": ["nm", "nanometer", "wavelength", "peak", "absorption"]
        },
        "e": {
            "desc": "(e) 心肌机械效率（%）或心脏功率输出（W）的具体数值",
            "kw": ["mechanical efficiency", "cardiac efficiency", "power output", "cardiac power",
                    "oxygen consumption", "vo2", "mvo2", "work efficiency"],
            "numeric_kw": ["%", "percent", "watt", " W ", "ml/min", "watts"]
        },
        "f": {
            "desc": "(f) 心肌细胞年更新率（%）及其随年龄变化",
            "kw": ["cardiomyocyte", "turnover", "renewal", "replacement rate", "cell cycle"],
            "numeric_kw": ["%", "percent", "per year", "annual", "age"]
        },
        "g": {
            "desc": "(g) 犬类（TRIAD或同类）雷帕霉素试验的结论",
            "kw": ["rapamycin", "dog", "canine", "TRIAD", "tripaid"],
            "numeric_kw": ["survival", "lifespan", "healthspan", "cardiac", "function"]
        },
        "h": {
            "desc": "(h) 灵长类热量限制试验的存活结论",
            "kw": ["caloric restriction", "dietary restriction", "primate", "monkey", "rhesus", "wisconsin", "nia"],
            "numeric_kw": ["survival", "lifespan", "mortality", "median", "maximum"]
        },
    }

    extracted_quotes = {}
    for key, cfg in quote_items.items():
        extracted_quotes[key] = []
        for r in all_with_abstract:
            abstract = r.get("abstractText", "") or ""
            if not abstract:
                continue
            abs_lower = abstract.lower()
            # 必须同时匹配主题关键词和数值关键词
            has_topic = any(kw.lower() in abs_lower for kw in cfg["kw"])
            has_numeric = any(kw.lower() in abs_lower for kw in cfg["numeric_kw"])
            if not (has_topic and has_numeric):
                continue
            # 提取含关键词的句子
            sentences = re.split(r'(?<=[.!?])\s+', abstract)
            for sent in sentences:
                sent_lower = sent.lower()
                if any(kw.lower() in sent_lower for kw in cfg["kw"]) and \
                   any(kw.lower() in sent_lower for kw in cfg["numeric_kw"]):
                    extracted_quotes[key].append({
                        "原句": sent.strip(),
                        "DOI": r.get("DOI", "NA"),
                        "PMID": r.get("PMID", "NA"),
                    })
                    break  # 每篇只取一句

    quotes_path = BASE_DIR / "重要数值摘句.md"
    with open(quotes_path, "w", encoding="utf-8") as f:
        f.write("# 重要数值摘句\n\n")
        f.write("> 以下摘录均来自 Europe PMC API 返回的 abstractText 原文，逐字摘录。\n")
        f.write("> 查不到的项标记「本语料未见」，禁止编造。\n\n")

        for key, cfg in quote_items.items():
            f.write(f"## {cfg['desc']}\n\n")
            quotes = extracted_quotes[key]
            if quotes:
                for i, q in enumerate(quotes[:5], 1):
                    f.write(f"{i}. **原句**: \"{q['原句']}\"\n")
                    f.write(f"   **来源**: DOI={q['DOI']}, PMID={q['PMID']}\n\n")
            else:
                f.write("**本语料未见**\n\n")

    # ========== SHA256 ==========
    print("\n计算 SHA256 ...")
    sha_path = BASE_DIR / "sha256.txt"
    all_files = [
        log_path, idx_path, cnt_path, adopted_path, cr_path, quotes_path
    ]
    all_files.extend(sorted(LITE_DIR.glob("*.json")))
    all_files.extend(sorted(CORE_DIR.glob("*.json")))

    with open(sha_path, "w", encoding="utf-8") as f:
        f.write("# SHA256 清单\n")
        f.write(f"# 生成时间: {datetime.now(timezone.utc).isoformat()}\n\n")
        for fp in all_files:
            if fp.exists():
                h = sha256_file(fp)
                rel = fp.relative_to(BASE_DIR)
                f.write(f"{h}  {rel}\n")

    # ========== 总结 ==========
    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"完成！耗时 {elapsed:.1f}s")
    print(f"  lite 条目总数: {len(all_records)}")
    print(f"  去重 PMID: {len(unique_pmids)}")
    print(f"  core 条目: {len(core_records)}")
    print(f"  各组分档: A={len(group_pmids['A'])}, B={len(group_pmids['B'])}, C={len(group_pmids['C'])}, D={len(group_pmids['D'])}")
    print(f"  adopted candidates: {len(candidates)}")
    cr_ok = sum(1 for r in crossref_results if r["是否与本地题名一致"] == "是")
    cr_no = sum(1 for r in crossref_results if r["是否与本地题名一致"] == "否")
    cr_fail = sum(1 for r in crossref_results if r["是否与本地题名一致"] == "未能核验")
    print(f"  Crossref: 一致={cr_ok}, 不一致={cr_no}, 未核验={cr_fail}")
    print(f"  重要数值摘句:")
    for key, cfg in quote_items.items():
        n = len(extracted_quotes[key])
        print(f"    {cfg['desc'][:30]}... → {n} 条摘录")
    print(f"  sha256.txt: {sha_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
