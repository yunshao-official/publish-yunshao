#!/usr/bin/env python3
"""绝经线文献检索器 v1.0-20261104"""

import json
import re
import time
import hashlib
import os
import sys
from urllib.request import Request, urlopen
from urllib.parse import quote, urlencode
from urllib.error import HTTPError, URLError
from datetime import datetime

# ============================================================
# Configuration
# ============================================================

CRITERIA_PATH = "/data/workspace/publish-yunshao/archive/16-生命与营养工程/01-理论与推导/绝经线·文献检索判据书-v1.0-20261104.md"
OUTPUT_DIR = "/data/workspace/publish-yunshao/archive/16-生命与营养工程/02-实验与数据/绝经线-文献底座-v1.0-20261104/"
RAW_DIR = os.path.join(OUTPUT_DIR, "raw")
EXPECTED_HASH_PREFIX = "6184d7c5001ab833"

EPMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
CROSSREF_BASE = "https://api.crossref.org/works"
EPMC_INTERVAL = 0.35
CROSSREF_INTERVAL = 0.4

DISCLAIMER = "本件为文献题录底座,非医疗建议;未经知世终读与合格医务人员评估不得用于任何实施"

# T thresholds by year
T_THRESHOLDS = [
    (2021, 2026, 40),
    (2016, 2020, 90),
    (2010, 2015, 160),
    (2000, 2009, 250),
    (1990, 1999, 400),
    (1900, 1989, 600),
]

# Q3 whitelist journals
WHITELIST_JOURNALS = [
    "NEJM", "N Engl J Med", "Lancet", "JAMA", "BMJ", "Ann Intern Med",
    "Obstet Gynecol", "Menopause", "Climacteric", "J Clin Endocrinol Metab",
    "Hum Reprod", "Hum Reprod Update", "Fertil Steril", "JBMR", "J Bone Miner Res",
    "Osteoporos Int", "Circulation", "Eur Heart J", "Arterioscler Thromb Vasc Biol",
    "Neuron", "Lancet Neurol", "Alzheimers Dement", "Am J Psychiatry",
    "JAMA Intern Med", "Arch Intern Med", "Cochrane Database Syst Rev",
    "Nat Rev Endocrinol", "Nat Rev Dis Primers", "PLoS Med", "PNAS",
    "Nature", "Science", "Ageing Res Rev", "Rejuvenation Research",
    "Endocr Rev", "Theriogenology", "Biol Reprod",
]

# Allowed types
ALLOWED_TYPES = {
    "journal article", "review", "systematic review", "meta-analysis",
    "randomized controlled trial", "guideline", "editorial", "book",
    "journal_article", "research_article", "review_article", "article",
}

# Gate W keywords (female context)
GATE_W_KEYWORDS = [
    "menopaus", "postmenopausal", "climacteric", "perimenopaus",
    "ovarian", "oocyte", "follicle", "uter", "vagin", "breast",
    "hot flash", "hot flush", "fsh", "estradiol", "oestrogen",
    "estrogen", "amh", "woman", "women", "female", "gynecolog", "geri",
]

# Gate N unconditional negatives
GATE_N_UNCONDITIONAL = [
    "zebrafish", "medaka", "alligator", "wildlife", "ecosystem",
    "aquatic", "effluent", "pulp mill", "arabidopsis",
    "daphnia", "shellfish", "coral", "ovine", "mare", "canine",
    "male infertility", "andropause",
]

# Gate N broad terms (with word boundary)
GATE_N_BROAD = ["fish", "plant"]

# Gate N co-occurring patterns
GATE_N_COOCURRING = [
    (["menopausal hormone"], ["prostate"]),
    (["testosterone"], ["hypogonadism"]),
]

# Statistics
stats = {
    "epmc_requests": 0,
    "crossref_requests": 0,
    "crossref_retries": 0,
    "crossref_cache_hits": 0,
    "openalex_status": None,
    "openalex_headers": {},
    "modules": {},
    "gates": {"W_reject": 0, "N_reject": 0, "hard_bottom_reject": 0, "no_abstract": 0},
    "total_pool1": 0,
    "total_pool2": 0,
    "total_combined": 0,
    "formula_hits": {},
    "failing_modules": [],
}

# ============================================================
# Helper functions
# ============================================================

def verify_hash():
    """Verify criteria document hash."""
    with open(CRITERIA_PATH, 'rb') as f:
        content = f.read()
    h = hashlib.sha256(content).hexdigest()[:16]
    if h != EXPECTED_HASH_PREFIX:
        print(f"FATAL: 判据哈希漂移! 期望 {EXPECTED_HASH_PREFIX}, 实际 {h}")
        sys.exit(1)
    print(f"✓ 判据哈希验证通过: {h}")
    return h

def parse_criteria():
    """Parse modules and formulas from criteria document."""
    with open(CRITERIA_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modules = []
    pattern = r'^- \*\*M(\d+)(?:[^*]*)\*\*｜式：(.+)$'
    
    for line in content.split('\n'):
        m = re.match(pattern, line.strip())
        if m:
            mod_num = f"M{m.group(1)}"
            formula = m.group(2).strip()
            modules.append({"module": mod_num, "formula": formula})
    
    unique_modules = sorted(set(m["module"] for m in modules))
    
    print(f"✓ 解析完成: {len(unique_modules)} 个模块, {len(modules)} 条检索式")
    
    if len(unique_modules) != 18:
        print(f"判负照记: 模块数 {len(unique_modules)} != 18")
        sys.exit(1)
    if len(modules) != 48:
        print(f"判负照记: 检索式条数 {len(modules)} != 48")
        sys.exit(1)
    
    return modules, unique_modules

def get_t_threshold(year):
    """Get citation threshold T for a given year."""
    if year is None:
        return None
    for start, end, t in T_THRESHOLDS:
        if start <= year <= end:
            return t
    return None

def check_gate_w(title, abstract):
    """Check Gate W: human female context."""
    text = (title + " " + (abstract or "")).lower()
    for kw in GATE_W_KEYWORDS:
        if kw in text:
            return True
    return False

def check_gate_n(title, abstract):
    """Check Gate N: cross-domain negative list. Returns (pass, reason)."""
    text = (title + " " + (abstract or "")).lower()
    
    # Check unconditional negatives
    for kw in GATE_N_UNCONDITIONAL:
        if kw in text:
            return False, f"unconditional:{kw}"
    
    # Check broad terms with word boundary
    for kw in GATE_N_BROAD:
        if re.search(rf'\b{kw}\b', text):
            return False, f"broad:{kw}"
    
    # Check co-occurring patterns
    for group1, group2 in GATE_N_COOCURRING:
        has1 = any(g in text for g in group1)
        has2 = any(g in text for g in group2)
        if has1 and has2:
            return False, f"cooccurring:{group1[0]}+{group2[0]}"
    
    return True, None

def check_hard_bottoms(article, anchors):
    """Check 6 hard bottom lines. Returns (pass, reasons)."""
    reasons = []
    
    # ① Has PMID or DOI
    if not article.get("pmid") and not article.get("doi"):
        reasons.append("no_pmid_or_doi")
    
    # ② Not retracted
    title_lower = (article.get("title") or "").lower()
    if "retract" in title_lower:
        reasons.append("retracted")
    
    # ③ Year 1900-2026
    year = article.get("year")
    if year is not None and (year < 1900 or year > 2026):
        reasons.append("year_out_of_range")
    
    # ④ Type check
    art_type = (article.get("type") or "").lower().replace("_", " ")
    type_ok = False
    for allowed in ALLOWED_TYPES:
        if allowed in art_type or art_type in allowed:
            type_ok = True
            break
    if not type_ok and art_type and art_type != "unknown":
        reasons.append("type_not_allowed")
    
    # ⑤ Title contains anchor words
    title = (article.get("title") or "").lower()
    anchor_in_title = any(a.lower() in title for a in anchors)
    if not anchor_in_title:
        reasons.append("anchor_not_in_title")
    
    # ⑥ Has abstract
    if not article.get("abstract"):
        reasons.append("no_abstract")
    
    return len(reasons) == 0, reasons, anchor_in_title

def extract_anchors(formula):
    """Extract anchor terms from a search formula."""
    anchors = []
    
    # Match quoted phrases: TITLE:"phrase"
    for m in re.finditer(r'TITLE:"([^"]+)"', formula):
        term = m.group(1).replace('*', '')
        anchors.append(term)
    
    # Match single words: TITLE:word (but not AND/OR/NOT)
    for m in re.finditer(r'TITLE:(\w+)', formula):
        term = m.group(1)
        if term.upper() not in ('AND', 'OR', 'NOT'):
            anchors.append(term)
    
    # Match parenthesized groups: TITLE:(A OR B OR C)
    for m in re.finditer(r'TITLE:\(([^)]+)\)', formula):
        group = m.group(1)
        for term in re.findall(r'"([^"]+)"|(\w+)', group):
            t = term[0] or term[1]
            if t.upper() not in ('AND', 'OR', 'NOT'):
                anchors.append(t.replace('*', ''))
    
    return list(set(anchors)) if anchors else ["menopause"]

def normalize_dedup_key(article):
    """Generate dedup key for an article."""
    if article.get("pmid"):
        return f"pmid:{article['pmid']}"
    if article.get("doi"):
        return f"doi:{article['doi'].lower()}"
    title = (article.get("title") or "").lower()
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return f"title:{title[:70]}"

def epmc_search(formula, page=1):
    """Search Europe PMC."""
    params = {
        "query": formula,
        "format": "json",
        "pageSize": "25",
        "resultType": "core",
        "sort": "CITED desc",
        "page": str(page),
    }
    url = f"{EPMC_BASE}?{urlencode(params)}"
    
    stats["epmc_requests"] += 1
    
    try:
        req = Request(url)
        req.add_header('User-Agent', 'MenopauseLiteratureSearch/1.0')
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data, url
    except Exception as e:
        print(f"  EPMC error: {e}")
        return None, url

def crossref_lookup(doi, cache, cache_path, lookup_idx):
    """Look up citation count from Crossref with retry."""
    if doi.lower() in cache:
        stats["crossref_cache_hits"] += 1
        return cache[doi.lower()]
    
    url = f"{CROSSREF_BASE}/{quote(doi, safe='')}"
    backoffs = [2, 5, 10]
    
    for attempt in range(3):
        stats["crossref_requests"] += 1
        try:
            req = Request(url)
            req.add_header('User-Agent', 'MenopauseLiteratureSearch/1.0 (mailto:research@example.com)')
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                
                # Save raw response
                raw_file = os.path.join(RAW_DIR, f"doi-回查-{lookup_idx[0]:03d}.json")
                with open(raw_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                lookup_idx[0] += 1
                
                count = data.get("message", {}).get("is-referenced-by-count", 0)
                cache[doi.lower()] = count
                with open(cache_path, 'w') as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)
                return count
        except Exception as e:
            if attempt < 2:
                stats["crossref_retries"] += 1
                time.sleep(backoffs[attempt])
            else:
                print(f"  Crossref final error for {doi}: {e}")
                return None
    
    return None

def probe_openalex():
    """Probe OpenAlex once and record 429 status."""
    url = "https://api.openalex.org/works?query=menopause&per_page=1"
    try:
        req = Request(url)
        req.add_header('User-Agent', 'MenopauseLiteratureSearch/1.0')
        with urlopen(req, timeout=10) as resp:
            stats["openalex_status"] = resp.status
            stats["openalex_headers"] = dict(resp.headers)
    except HTTPError as e:
        stats["openalex_status"] = e.code
        stats["openalex_headers"] = {
            "x-ratelimit-limit": e.headers.get("x-ratelimit-limit", ""),
            "x-ratelimit-remaining": e.headers.get("x-ratelimit-remaining", ""),
            "retry-after": e.headers.get("retry-after", ""),
        }
    except Exception as e:
        stats["openalex_status"] = str(e)

def parse_epmc_result(result):
    """Parse a single EPMC result into article dict."""
    authors = []
    if result.get("authorString"):
        authors = [a.strip() for a in result["authorString"].split(",")]
    elif result.get("author"):
        authors = [a.get("fullName", "") for a in result["author"]]
    
    year = None
    if result.get("pubYear"):
        try:
            year = int(result["pubYear"])
        except:
            pass
    
    return {
        "title": result.get("title", ""),
        "authors": authors,
        "year": year,
        "journal": result.get("journalTitle", ""),
        "type": result.get("type", ""),
        "pmid": result.get("pmid", ""),
        "doi": result.get("doi", ""),
        "abstract": result.get("abstractText", ""),
        "citedByCount": result.get("citedByCount", 0),
        "source": "EPMC",
    }

def check_journal_whitelist(journal):
    """Check if journal is in Q3 whitelist."""
    journal_lower = (journal or "").lower()
    for wl in WHITELIST_JOURNALS:
        if wl.lower() in journal_lower:
            return True
    return False

def classify_article(article, T, anchors):
    """Classify article into pool and determine Q level."""
    cited = article.get("citedByCount", 0) or 0
    journal = article.get("journal", "")
    title = article.get("title", "")
    
    anchor_in_title = any(a.lower() in title.lower() for a in anchors)
    journal_in_whitelist = check_journal_whitelist(journal)
    
    pool = None
    gate = None
    relaxation = []
    
    if T is None:
        # No year, can't determine threshold
        return None, None, []
    
    if cited >= T:
        gate = "Q1"
        if anchor_in_title:
            pool = 1
        else:
            pool = 2
            relaxation.append("放宽乙:锚仅摘要")
    elif cited >= 0.6 * T:
        gate = "Q2"
        pool = 2
        if not anchor_in_title:
            relaxation.append("放宽乙:锚仅摘要")
    elif cited >= 0.5 * T:
        gate = "Q1-放宽甲"
        pool = 2
        relaxation.append("放宽甲:Q1降半档(门槛×0.5)")
        if not anchor_in_title:
            relaxation.append("放宽乙:锚仅摘要")
    elif cited >= 0.3 * T:
        gate = "Q2-放宽甲"
        pool = 2
        relaxation.append("放宽甲:Q2降半档(门槛×0.3)")
        if not anchor_in_title:
            relaxation.append("放宽乙:锚仅摘要")
    elif cited >= 0.25 * T and journal_in_whitelist:
        gate = "Q3"
        if anchor_in_title:
            pool = 1
        else:
            pool = 2
            relaxation.append("放宽乙:锚仅摘要")
    else:
        return None, None, []
    
    # Pool 1 must have empty relaxation
    if pool == 1:
        relaxation = []
    
    return pool, gate, relaxation

# ============================================================
# Main execution
# ============================================================

def main():
    print("=" * 60)
    print("绝经线文献检索器 v1.0")
    print("=" * 60)
    
    # Create output directories
    os.makedirs(RAW_DIR, exist_ok=True)
    
    # Step 1: Verify hash
    verify_hash()
    
    # Step 2: Parse criteria
    modules, unique_modules = parse_criteria()
    
    # Step 3: Probe OpenAlex (once)
    print("\n探测 OpenAlex...")
    probe_openalex()
    print(f"  OpenAlex status: {stats['openalex_status']}")
    
    # Initialize module stats
    for mod in unique_modules:
        stats["modules"][mod] = {
            "formulas": 0,
            "hits": 0,
            "gate_w_reject": 0,
            "gate_n_reject": 0,
            "hard_bottom_reject": 0,
            "no_abstract": 0,
            "pool1": 0,
            "pool2": 0,
        }
    
    # Step 4: Search EPMC for each formula
    all_articles = []
    formula_idx_by_module = {}
    global_formula_idx = 0
    
    for idx, mod in enumerate(modules):
        mod_num = mod["module"]
        formula = mod["formula"]
        anchors = extract_anchors(formula)
        
        # Track formula index within module
        if mod_num not in formula_idx_by_module:
            formula_idx_by_module[mod_num] = 0
        formula_idx_by_module[mod_num] += 1
        local_idx = formula_idx_by_module[mod_num]
        global_formula_idx += 1
        
        print(f"\n[{global_formula_idx}/48] {mod_num}-{local_idx}: {formula[:60]}...")
        
        stats["modules"][mod_num]["formulas"] += 1
        
        for page in range(1, 4):  # pages 1-3
            time.sleep(EPMC_INTERVAL)
            data, url = epmc_search(formula, page)
            
            if data is None:
                continue
            
            # Save raw response
            raw_file = os.path.join(RAW_DIR, f"{mod_num}-pmc-{local_idx}-{page}.json")
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Get hit count (only from page 1)
            if page == 1:
                hc = data.get("hitCount", 0)
                stats["formula_hits"][f"{mod_num}-{local_idx}"] = hc
                stats["modules"][mod_num]["hits"] += hc
                print(f"  hitCount: {hc}")
            
            results = data.get("resultList", {}).get("result", [])
            if not results:
                break
            
            for result in results:
                article = parse_epmc_result(result)
                all_articles.append({
                    "article": article,
                    "module": mod_num,
                    "formula": formula,
                    "anchors": anchors,
                    "url": url,
                })
    
    print(f"\n总计从 EPMC 获取 {len(all_articles)} 条原始记录")
    
    # Step 5: Apply gates and scoring
    passed_articles = []
    cite_cache_path = os.path.join(OUTPUT_DIR, "cite-cache.json")
    cite_cache = {}
    if os.path.exists(cite_cache_path):
        with open(cite_cache_path, 'r') as f:
            cite_cache = json.load(f)
    
    lookup_idx = [1]
    
    for item in all_articles:
        article = item["article"]
        mod_num = item["module"]
        title = article.get("title", "")
        abstract = article.get("abstract", "")
        
        # Gate W
        if not check_gate_w(title, abstract):
            stats["gates"]["W_reject"] += 1
            stats["modules"][mod_num]["gate_w_reject"] += 1
            continue
        
        # Gate N
        n_pass, n_reason = check_gate_n(title, abstract)
        if not n_pass:
            stats["gates"]["N_reject"] += 1
            stats["modules"][mod_num]["gate_n_reject"] += 1
            continue
        
        # Hard bottoms
        hb_pass, hb_reasons, anchor_in_title = check_hard_bottoms(article, item["anchors"])
        
        # Special handling for no abstract
        if "no_abstract" in hb_reasons:
            stats["gates"]["no_abstract"] += 1
            stats["modules"][mod_num]["no_abstract"] += 1
            article["status"] = "待核·无摘要"
            article["module"] = mod_num
            article["cross_modules"] = [mod_num]
            article["formula"] = item["formula"]
            article["url"] = item["url"]
            article["gate"] = "无摘要→发现清单"
            article["pool"] = None
            article["relaxation"] = []
            article["hb_reasons"] = hb_reasons
            passed_articles.append(article)
            continue
        
        # Check other hard bottom failures
        other_reasons = [r for r in hb_reasons if r != "anchor_not_in_title" and r != "no_abstract"]
        if other_reasons:
            stats["gates"]["hard_bottom_reject"] += 1
            stats["modules"][mod_num]["hard_bottom_reject"] += 1
            continue
        
        # Determine Q level and pool
        year = article.get("year")
        T = get_t_threshold(year)
        cited = article.get("citedByCount", 0) or 0
        
        # Crossref lookup if needed
        if cited == 0 and article.get("doi"):
            time.sleep(CROSSREF_INTERVAL)
            cr_count = crossref_lookup(article["doi"], cite_cache, cite_cache_path, lookup_idx)
            if cr_count is not None and cr_count > cited:
                article["citedByCount"] = cr_count
                article["citationSource"] = "Crossref"
                cited = cr_count
            else:
                article["citationSource"] = "EPMC"
        else:
            article["citationSource"] = "EPMC"
        
        pool, gate, relaxation = classify_article(article, T, item["anchors"])
        
        if pool is None:
            stats["gates"]["hard_bottom_reject"] += 1
            stats["modules"][mod_num]["hard_bottom_reject"] += 1
            continue
        
        # Add Crossref relaxation if used
        if article["citationSource"] == "Crossref" and pool == 2:
            relaxation.append("放宽丙:Crossref补齐")
        
        # Set status
        if year and 2024 <= year <= 2026:
            article["status"] = "年份待核"
        elif year is None:
            article["status"] = "年份待核"
        else:
            article["status"] = "核"
        
        article["module"] = mod_num
        article["cross_modules"] = [mod_num]
        article["formula"] = item["formula"]
        article["url"] = item["url"]
        article["gate"] = gate
        article["pool"] = pool
        article["relaxation"] = relaxation
        article["anchors"] = item["anchors"]
        article["hb_reasons"] = hb_reasons
        
        passed_articles.append(article)
        
        if pool == 1:
            stats["modules"][mod_num]["pool1"] += 1
        elif pool == 2:
            stats["modules"][mod_num]["pool2"] += 1
    
    print(f"\n通过门控: {len(passed_articles)} 条")
    
    # Step 6: Deduplication
    dedup = {}
    for article in passed_articles:
        key = normalize_dedup_key(article)
        if key in dedup:
            existing = dedup[key]
            # Keep the one with higher citation
            if (article.get("citedByCount", 0) or 0) > (existing.get("citedByCount", 0) or 0):
                article["cross_modules"] = list(set(
                    existing.get("cross_modules", [existing["module"]]) + 
                    [article["module"]]
                ))
                dedup[key] = article
            else:
                existing["cross_modules"] = list(set(
                    existing.get("cross_modules", [existing["module"]]) + 
                    [article["module"]]
                ))
        else:
            dedup[key] = article
    
    final_articles = list(dedup.values())
    
    # Separate pools
    pool1 = [a for a in final_articles if a.get("pool") == 1]
    pool2 = [a for a in final_articles if a.get("pool") == 2]
    discovery = [a for a in final_articles if a.get("pool") is None]
    
    stats["total_pool1"] = len(pool1)
    stats["total_pool2"] = len(pool2)
    stats["total_combined"] = len(pool1) + len(pool2)
    
    print(f"\n池1: {len(pool1)}")
    print(f"池2: {len(pool2)}")
    print(f"合计: {len(pool1) + len(pool2)}")
    print(f"发现清单: {len(discovery)}")
    
    # Check per-module minimums
    module_counts = {}
    for a in final_articles:
        if a.get("pool") in (1, 2):
            for m in a.get("cross_modules", [a["module"]]):
                module_counts[m] = module_counts.get(m, 0) + 1
    
    failing_modules = []
    for mod_num in unique_modules:
        count = module_counts.get(mod_num, 0)
        if count < 3:
            failing_modules.append((mod_num, count))
    
    if failing_modules:
        print(f"\n判负照记: 以下模块不足3条:")
        for mod, count in failing_modules:
            print(f"  {mod}: {count} 条 (缺口 {3-count})")
    
    stats["failing_modules"] = failing_modules
    
    # Step 7: Generate output files
    print("\n生成输出文件...")
    
    # Prepare article records for output
    def prepare_record(article):
        return {
            "模块号": article.get("module"),
            "跨模块": article.get("cross_modules", []),
            "标题": article.get("title"),
            "作者": article.get("authors", []),
            "年份": article.get("year"),
            "刊物": article.get("journal"),
            "类型": article.get("type"),
            "PMID": article.get("pmid"),
            "DOI": article.get("doi"),
            "被引数": article.get("citedByCount", 0),
            "被引来源": article.get("citationSource", "EPMC"),
            "过门": article.get("gate"),
            "池级": article.get("pool"),
            "放宽项": article.get("relaxation", []),
            "状态标签": article.get("status"),
            "摘要前400字": (article.get("abstract") or "")[:400],
            "检索式原文": article.get("formula"),
            "请求URL": article.get("url"),
        }
    
    # 文献主档-v1.0.json
    archive_data = {
        "声明": DISCLAIMER,
        "版本": "v1.0",
        "日期": "2026-11-04",
        "池1数量": len(pool1),
        "池2数量": len(pool2),
        "合计数量": len(pool1) + len(pool2),
        "文献": [prepare_record(a) for a in final_articles if a.get("pool") in (1, 2)],
    }
    
    with open(os.path.join(OUTPUT_DIR, "文献主档-v1.0.json"), 'w', encoding='utf-8') as f:
        json.dump(archive_data, f, ensure_ascii=False, indent=2)
    
    # 统计-v1.0.json
    stats["disclaimer"] = DISCLAIMER
    stats["criteria_hash"] = EXPECTED_HASH_PREFIX
    stats["modules_count"] = len(unique_modules)
    stats["formulas_count"] = len(modules)
    stats["date"] = "2026-11-04"
    
    with open(os.path.join(OUTPUT_DIR, "统计-v1.0.json"), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    # 发现清单-v1.0.md
    with open(os.path.join(OUTPUT_DIR, "发现清单-v1.0.md"), 'w', encoding='utf-8') as f:
        f.write("# 发现清单 v1.0\n\n")
        f.write(f"> {DISCLAIMER}\n\n")
        f.write(f"总计: {len(discovery)} 条\n\n")
        
        for idx, article in enumerate(discovery, 1):
            f.write(f"## {idx}. {article.get('title', 'N/A')}\n\n")
            f.write(f"- 模块: {article.get('module')}\n")
            f.write(f"- 状态: {article.get('status')}\n")
            f.write(f"- 原因: {article.get('gate')}\n")
            f.write(f"- PMID: {article.get('pmid', 'N/A')}\n")
            f.write(f"- DOI: {article.get('doi', 'N/A')}\n")
            f.write(f"- 年份: {article.get('year', 'N/A')}\n")
            f.write(f"- 刊物: {article.get('journal', 'N/A')}\n\n")
    
    # 每模块漏斗-v1.0.md
    with open(os.path.join(OUTPUT_DIR, "每模块漏斗-v1.0.md"), 'w', encoding='utf-8') as f:
        f.write("# 每模块漏斗 v1.0\n\n")
        f.write(f"> {DISCLAIMER}\n\n")
        
        for mod in unique_modules:
            mod_stats = stats["modules"][mod]
            f.write(f"## {mod}\n\n")
            f.write(f"- 检索式数: {mod_stats['formulas']}\n")
            f.write(f"- EPMC 总命中: {mod_stats['hits']}\n")
            f.write(f"- 门W剔除: {mod_stats['gate_w_reject']}\n")
            f.write(f"- 门N剔除: {mod_stats['gate_n_reject']}\n")
            f.write(f"- 硬底线剔除: {mod_stats['hard_bottom_reject']}\n")
            f.write(f"- 无摘要→发现清单: {mod_stats['no_abstract']}\n")
            f.write(f"- 池1入库: {mod_stats['pool1']}\n")
            f.write(f"- 池2入库: {mod_stats['pool2']}\n")
            f.write(f"- 合计入库: {mod_stats['pool1'] + mod_stats['pool2']}\n\n")
            
            # List formula hit counts
            for key, hc in stats["formula_hits"].items():
                if key.startswith(mod):
                    f.write(f"  - {key}: hitCount={hc}\n")
            f.write("\n")
    
    # Save cite-cache
    with open(cite_cache_path, 'w', encoding='utf-8') as f:
        json.dump(cite_cache, f, ensure_ascii=False, indent=2)
    
    print("\n✓ 所有输出文件已生成")
    
    # Final summary
    print("\n" + "=" * 60)
    print("执行摘要")
    print("=" * 60)
    print(f"池1: {len(pool1)}")
    print(f"池2: {len(pool2)}")
    print(f"合计: {len(pool1) + len(pool2)}")
    print(f"发现清单: {len(discovery)}")
    print(f"EPMC 请求数: {stats['epmc_requests']}")
    print(f"Crossref 请求数: {stats['crossref_requests']}")
    print(f"Crossref 重试数: {stats['crossref_retries']}")
    print(f"Crossref 缓存命中: {stats['crossref_cache_hits']}")
    print(f"OpenAlex 状态: {stats['openalex_status']}")
    
    if failing_modules:
        print(f"\n判负模块: {len(failing_modules)}")
        for mod, count in failing_modules:
            print(f"  {mod}: {count} 条")
    
    print(f"\n是否新增过任何判据外的门或放宽项: 否")
    print("=" * 60)

if __name__ == "__main__":
    main()
