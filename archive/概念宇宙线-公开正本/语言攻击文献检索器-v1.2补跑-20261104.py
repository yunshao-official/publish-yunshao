#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言与思想攻击·文献检索器 v1.2补跑（2026-11-04）
判据：v1.2-20261103.md（已冻结，sha256 0be27507）
任务：补跑M06-M15 OpenAlex通道（M01-M05用v1.0缓存）
"""
import json, os, re, sys, time, shutil
import urllib.error, urllib.parse, urllib.request
import importlib.util
from collections import defaultdict

# ---------- 路径 ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
OUT_DIR = os.path.join(SCRIPT_DIR, '语言与思想攻击文献库-v1.2补跑-20261104')
RAW_DIR = os.path.join(OUT_DIR, 'raw')
V10_RAW = os.path.join(SCRIPT_DIR, '语言与思想攻击文献库-20261103', 'raw')
V11_RAW = os.path.join(SCRIPT_DIR, '语言与思想攻击文献库-v1.1-20261103', 'raw')
RETRIEVED = '2026-11-04'
UA = {'User-Agent': 'yunshao-langattack/1.2-bupao (%s)' % REPO}

# ---------- 复用工具 ----------
_tool_rel = os.path.join('archive','10-治理与哲学','04-工具与代码','控制权文献库检索器-v1.0-20261102.py')
_tool_path = os.path.join(REPO, _tool_rel)
_spec = importlib.util.spec_from_file_location('_ctrl', _tool_path)
_tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tool)
oa_abstract = _tool.oa_abstract
strip_tags = _tool.strip_tags
norm_title = _tool.norm_title

# ---------- 从判据书 v1.2 §五 解析锚词 ----------
def parse_anchors_from_criteria():
    criteria_path = os.path.join(SCRIPT_DIR, '语言与思想攻击·文献检索判据书-v1.2-20261103.md')
    with open(criteria_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'## 五、锁定锚词表.*?\n(.*?)\n【修改记录】', content, re.DOTALL)
    if not match:
        raise ValueError("无法解析判据书v1.2 §五")
    section = match.group(1)
    modules = []
    total = 0
    for line in section.strip().split('\n'):
        line = line.strip()
        if not line.startswith('-'): continue
        m = re.match(r'^-\s+\**M(\d\d)\**：(.+)$', line)
        if m:
            mod_id = 'M%s' % m.group(1)
            anchors = [a.strip() for a in m.group(2).split('｜')]
            modules.append({'id': mod_id, 'anchors': anchors})
            total += len(anchors)
    assert len(modules) == 15, '模块数=%d ≠ 15' % len(modules)
    assert total == 69, '锚词数=%d ≠ 69' % total
    return modules

# ---------- 从判据书 v1.0 §六 解析检索式 ----------
def parse_formulas_from_criteria():
    criteria_path = os.path.join(SCRIPT_DIR, '语言与思想攻击·文献检索判据书-v1.0-20261103.md')
    with open(criteria_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'## 六、模块表.*?## 七', content, re.DOTALL)
    if not match:
        raise ValueError("无法解析判据书v1.0 §六")
    section = match.group(0)
    formulas = {}
    # 逐行解析，每行一个模块
    for line in section.split('\n'):
        line = line.strip()
        if not line.startswith('- **M'):
            continue
        # 提取模块号
        m_mod = re.match(r'- \*\*(M\d\d)', line)
        if not m_mod:
            continue
        mid = m_mod.group(1)
        # 提取式：后面的内容
        m_style = re.search(r'｜式：(.+)$', line)
        if not m_style:
            continue
        style_text = m_style.group(1).strip()
        # 按；或;分割，去掉反引号
        f_list = [f.strip().strip('`') for f in re.split(r'[；;]', style_text) if f.strip()]
        formulas[mid] = f_list
    return formulas

# ---------- fetch ----------
def fetch_json(url, retries=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                headers = dict(r.headers)
                body = json.loads(r.read().decode('utf-8','replace'))
                return body, None, headers
        except urllib.error.HTTPError as e:
            # Extract headers from HTTPError
            resp_headers = {}
            if hasattr(e, 'headers'):
                for key in e.headers.keys():
                    resp_headers[key.lower()] = e.headers[key]
            if e.code == 429:
                ra = resp_headers.get('retry-after','?')
                rl = resp_headers.get('x-ratelimit-remaining','?')
                time.sleep(3)
                return None, '429 (Retry-After=%s, remaining=%s)' % (ra, rl), resp_headers
            else:
                time.sleep(2)
        except Exception:
            time.sleep(2)
    return None, 'exhausted retries', {}

# ---------- 质量门 ----------
def get_T(year):
    if year >= 2021: return 40
    if year >= 2016: return 90
    if year >= 2010: return 160
    if year >= 2000: return 250
    if year >= 1990: return 400
    return 600

ALLOWED_TYPES = {'journal-article','journal article','book','book-chapter','book chapter',
    'conference-paper','conference paper','review','preprint','proceedings-article'}

# ---------- v1.2 R门 ----------
STRICT_SINGLE_ANCHORS = {
    'frame','framing','propaganda','totalitarian','taboo','substitution',
    'avoidance','slur','silence','meme','satire','parody','attrition',
    'priming','cultivation'
}
POLITICAL_WORDS = ['polic','politic','ideolog','discours','rhetor','propagand',
    'censor','narrat','hegemon','power','media','press','public','opinion','political']
DOMAIN_WORDS = ['language','linguistic','word','words','lexical','lexicon','vocabulary',
    'discourse','speech','speaking','tongue','naming','term','terminology',
    'semantic','semantics','pragmatics','rhetoric','meaning','concept','metaphor',
    'translation','narrative','dialect']

def _norm(s):
    return s.replace('-', ' ')

def check_R_gate(title_low, matched_anchors):
    tn = _norm(title_low)
    has_multi = False
    has_strict_single_with_political = False
    has_other_single_with_domain = False
    for a in matched_anchors:
        if a == 'metaphor AND politics':
            if 'metaphor' in tn and 'politics' in tn:
                has_multi = True
        elif ' ' in a or '-' in a:
            has_multi = True
        elif a in STRICT_SINGLE_ANCHORS:
            if any(pw in tn for pw in POLITICAL_WORDS):
                has_strict_single_with_political = True
        else:
            if any(dw in tn for dw in DOMAIN_WORDS):
                has_other_single_with_domain = True
    return has_multi or has_strict_single_with_political or has_other_single_with_domain

# ---------- v1.2 N表 ----------
NEGATIVE_WORDS = [
    'dna','protein','amino acid','bacteria','antimicrobial','antibiotic',
    'insulin','diabetes','tumor','cancer','carcinoma','pcr','crispr','phylogenetic',
    'modeltest','partitionfinder','job shop','quadratic assignment','supply chain',
    'venture creation','customer loyalty','biomarker','surrogate endpoint','quantum',
    'internet of things','wetting','asset pricing','econometric','stock market',
    'pandemic patients','hospitalized','clinical characteristics','mortality',
    'speech synthesis','text to speech','tacotron','blstm','end-to-end speech',
    'voice conversion','speech quality','programming language','object module',
    'compiler','neural network','deep learning','lstm network',
    'corporate report','fossil fuel','public relations','journalism studies',
    'historiography','international management',
]

def check_N_gate(title_low, matched_multi_count):
    if matched_multi_count >= 2:
        return True
    tn = _norm(title_low)
    for nw in NEGATIVE_WORDS:
        if nw in tn:
            return False
    return True

def find_anchor_hits(title_low, abstract_low, anchors, title_only=True):
    tn = _norm(title_low)
    an = _norm(abstract_low)
    hits = []
    for a in anchors:
        anorm = _norm(a)
        if a == 'metaphor AND politics':
            if title_only:
                if 'metaphor' in tn and 'politics' in tn: hits.append(a)
            else:
                combined = tn + ' ' + an
                if 'metaphor' in combined and 'politics' in combined: hits.append(a)
        else:
            if anorm in tn: hits.append(a)
            elif not title_only and anorm in an: hits.append(a)
    return hits

def count_multi_word_hits(hits):
    return sum(1 for h in hits if (' ' in h or '-' in h) or h == 'metaphor AND politics')

# ---------- 白名单 ----------
WHITELIST = [
    'nature','science','pnas','american political science review','american journal of sociology',
    'comparative political studies','political communication','public opinion quarterly',
    'new media & society','new media and society','information communication & society',
    'social media + society','social media society','journal of computer-mediated communication',
    'journal of computer mediated communication','media culture & society','media culture and society',
    'international journal of communication','discourse & society','discourse and society',
    'language in society','language & communication','language and communication',
    'discourse studies','journal of pragmatics','text & talk','text and talk',
    'applied linguistics','journal of language and social psychology','journal of sociolinguistics',
    'critical discourse studies','cognition','cognitive science','psychological science',
    'annual review of linguistics','journal of memory and language','memory & cognition',
    'memory and cognition','communication research','communication monographs','journal of communication',
    'chi','cscw','www','emnlp','acl','mit press','cambridge','oxford','routledge',
]
def in_whitelist(venue):
    if not venue: return False
    vl = venue.lower()
    return any(w in vl for w in WHITELIST)

# ---------- 父级DOI折叠（v1.2 §二.5）----------
def parent_doi(doi):
    if not doi: return ''
    parts = doi.split('/')
    if len(parts) >= 2:
        prefix = parts[0]
        suffix_parts = parts[1].split('.')
        if len(suffix_parts) > 1:
            return prefix + '/' + '.'.join(suffix_parts[:-1])
    return doi

# ---------- 解析函数 ----------
def parse_oa(w, mid, formula):
    doi_raw = (w.get('doi') or '').replace('https://doi.org/','').strip()
    title = strip_tags(w.get('title') or '')
    authors = [(a.get('author') or {}).get('display_name','') for a in (w.get('authorships') or [])]
    authors = [a for a in authors if a]
    pl = w.get('primary_location') or {}; src = pl.get('source') or {}
    return dict(module=mid, channel='openalex', doi=doi_raw.lower(), title=title,
                authors=authors, year=w.get('publication_year'),
                venue=strip_tags(src.get('display_name','') or ''),
                type=(w.get('type') or '').lower(),
                oa_cites=int(w.get('cited_by_count') or 0), cr_cites=0,
                is_retracted=bool(w.get('is_retracted')),
                abstract=oa_abstract(w.get('abstract_inverted_index')),
                search_url='', anchor_used=formula)

def parse_cr(it, mid, anchor):
    doi = (it.get('DOI') or '').strip().lower()
    title = strip_tags((it.get('title') or [''])[0])
    yr = None
    for df in ('published','issued','published-print','published-online','created'):
        dp = it.get(df)
        if dp and dp.get('date-parts'):
            for part in dp['date-parts']:
                if isinstance(part, list) and part and isinstance(part[0], int) and part[0] > 1000:
                    yr = part[0]; break
        if yr: break
    authors = []
    for a in (it.get('author') or []):
        nm = ', '.join([x for x in (a.get('family',''), a.get('given','')) if x]) or a.get('name','')
        if nm: authors.append(nm)
    ct = it.get('container-title') or []
    url = 'https://api.crossref.org/works?query.title=%s&rows=25&sort=is-referenced-by-count&order=desc' % urllib.parse.quote(anchor)
    return dict(module=mid, channel='crossref', doi=doi, title=title,
                authors=authors, year=yr, venue=strip_tags(ct[0]) if ct else '',
                type=(it.get('type') or '').lower(),
                oa_cites=0, cr_cites=int(it.get('is-referenced-by-count') or 0),
                is_retracted=False, abstract=strip_tags(it.get('abstract','') or ''),
                search_url=url, anchor_used=anchor)

def parse_doaj(article, mid, anchor):
    bib = article.get('bibjson') or {}
    doi = ''
    for ident in (bib.get('identifier') or []):
        if ident.get('type') == 'doi':
            doi = (ident.get('id') or '').strip().lower()
            break
    if not doi:
        doi = (bib.get('doi') or article.get('doi') or '').strip().lower()
    title = strip_tags(bib.get('title') or article.get('title') or '')
    if isinstance(title, list): title = strip_tags(title[0]) if title else ''
    yr = None
    for df in ('year', 'publication_date', 'created_date'):
        d = str(bib.get(df) or article.get(df) or '')
        if len(d) >= 4 and d[:4].isdigit():
            y = int(d[:4])
            if y > 1000: yr = y; break
    journal = bib.get('journal') or article.get('journal') or {}
    venue = strip_tags(journal.get('title','') or '')
    authors = [strip_tags(a.get('name','')) for a in (bib.get('author') or []) if a.get('name')]
    url = 'https://doaj.org/api/search/articles/%s' % urllib.parse.quote(anchor)
    return dict(module=mid, channel='doaj', doi=doi, title=title,
                authors=authors, year=yr, venue=venue, type='journal-article',
                oa_cites=0, cr_cites=0, is_retracted=False,
                abstract=strip_tags(bib.get('abstract','') or ''),
                search_url=url, anchor_used=anchor)

# ====================================================================
def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    modules = parse_anchors_from_criteria()
    formulas = parse_formulas_from_criteria()
    total_anchors = sum(len(m['anchors']) for m in modules)
    print('v1.2补跑 锚词=%d 模块=%d (断言 69/15)' % (total_anchors, len(modules)))

    # ================================================================
    # STEP 1: OpenAlex 探测
    # ================================================================
    print('\n=== OpenAlex 探测 ===')
    oa_probe_url = 'https://api.openalex.org/works?filter=title_and_abstract.search:algospeak&per-page=1'
    obj, err, headers = fetch_json(oa_probe_url)
    oa_limit = headers.get('x-ratelimit-limit', '?')
    oa_remaining = headers.get('x-ratelimit-remaining', '?')
    oa_reset = headers.get('x-ratelimit-reset', '?')
    oa_429_info = None

    if obj is None and err and '429' in str(err):
        oa_429_info = err
        print('OA 为 429: %s' % err)
        print('limit=%s remaining=%s reset=%s' % (oa_limit, oa_remaining, oa_reset))
        print('M06-M15 OpenAlex 补跑无法执行，将使用已有缓存数据继续处理')
    elif obj is not None:
        print('OA 可用! limit=%s remaining=%s reset=%s' % (oa_limit, oa_remaining, oa_reset))
    else:
        print('OA 探测异常: %s' % err)
        print('将使用已有缓存数据继续处理')

    # ================================================================
    # STEP 2: OpenAlex 取数
    # ================================================================
    print('\n=== OpenAlex 取数 ===')
    all_cands = []
    oa_stats = {}
    qlog = []
    file_seq = 0

    for mod in modules:
        mid = mod['id']
        mod_formulas = formulas.get(mid, [])
        print('\n%s: formulas=%d' % (mid, len(mod_formulas)))

        oa_stats[mid] = {
            'formulas': len(mod_formulas),
            'requests': 0,
            'candidates': 0,
            '429_count': 0,
            '429_retry_after': None,
            'cache_hits': 0,
        }

        # M01-M05: 尝试加载v1.0缓存
        if mid in ['M01','M02','M03','M04','M05']:
            cache_loaded = 0
            for fi, formula in enumerate(mod_formulas, 1):
                for page in range(1, 6):
                    slug = '%s-oa-%02d-p%d' % (mid, fi, page)
                    cache_path = os.path.join(V10_RAW, slug + '.json')
                    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 100:
                        with open(cache_path, 'r', encoding='utf-8') as f:
                            obj = json.load(f)
                        works = obj.get('results', []) or []
                        if works:
                            cache_loaded += len(works)
                            oa_stats[mid]['cache_hits'] += 1
                            for w in works:
                                rec = parse_oa(w, mid, formula)
                                all_cands.append(rec)
            if cache_loaded > 0:
                oa_stats[mid]['candidates'] = cache_loaded
                print('  缓存加载: %d 条' % cache_loaded)
                continue

        # M06-M15 (或M01-M05缓存缺失): 从OA取
        if oa_429_info:
            print('  OA 429，跳过M06-M15取数')
            oa_stats[mid]['429_count'] = 1
            oa_stats[mid]['429_retry_after'] = oa_reset
            continue

        for fi, formula in enumerate(mod_formulas, 1):
            print('  公式 %d/%d: %s' % (fi, len(mod_formulas), formula[:50]))

            for page in range(1, 6):
                file_seq += 1
                fname = '%s-oa-%03d.json' % (mid, file_seq)
                fpath = os.path.join(RAW_DIR, fname)

                # 检查是否已存在（断点续传）
                if os.path.exists(fpath) and os.path.getsize(fpath) > 100:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        obj = json.load(f)
                    works = obj.get('results', []) or []
                    oa_stats[mid]['cache_hits'] += 1
                    qlog.append('%s|openalex|CACHED|%s' % (fname, formula))
                else:
                    # 发请求
                    oa_url = 'https://api.openalex.org/works?filter=title_and_abstract.search:%s,is_retracted:false&sort=cited_by_count:desc&per-page=25&page=%d' % (
                        urllib.parse.quote(formula), page)
                    obj, err, headers = fetch_json(oa_url)
                    oa_stats[mid]['requests'] += 1
                    qlog.append('%s|openalex|%s|%s' % (fname, 'OK' if obj else 'FAIL', formula))

                    if obj is None:
                        if err and '429' in str(err):
                            oa_stats[mid]['429_count'] += 1
                            ra = headers.get('Retry-After', '?')
                            oa_stats[mid]['429_retry_after'] = ra
                            print('    429! Retry-After=%s' % ra)
                        break

                    # 落盘
                    with open(fpath, 'w', encoding='utf-8') as f:
                        json.dump(obj, f, ensure_ascii=False)

                    works = obj.get('results', []) or []

                if not works:
                    break

                # 解析
                for w in works:
                    rec = parse_oa(w, mid, formula)
                    all_cands.append(rec)
                    oa_stats[mid]['candidates'] += 1

                if len(works) < 25:
                    break

                time.sleep(0.6)

        print('  累计: %d 条' % oa_stats[mid]['candidates'])

    print('\nOpenAlex取数完成: 总候选=%d' % len(all_cands))

    # ================================================================
    # STEP 3: 加载Crossref/DOAJ缓存（from v1.1）
    # ================================================================
    print('\n=== 加载Crossref/DOAJ缓存 ===')
    ct_count = 0
    dj_count = 0

    for mod in modules:
        mid = mod['id']
        for ai, anchor in enumerate(mod['anchors'], 1):
            # Crossref
            ct_slug = '%s-ct-%02d' % (mid, ai)
            ct_path = os.path.join(V11_RAW, ct_slug + '.json')
            if os.path.exists(ct_path) and os.path.getsize(ct_path) > 100:
                with open(ct_path, 'r', encoding='utf-8') as f:
                    obj = json.load(f)
                items = (obj.get('message', {}) or {}).get('items', []) or []
                ct_count += len(items)
                for it in items:
                    rec = parse_cr(it, mid, anchor)
                    all_cands.append(rec)

            # DOAJ
            dj_slug = '%s-dj-%02d' % (mid, ai)
            dj_path = os.path.join(V11_RAW, dj_slug + '.json')
            if os.path.exists(dj_path) and os.path.getsize(dj_path) > 100:
                with open(dj_path, 'r', encoding='utf-8') as f:
                    obj = json.load(f)
                results = obj.get('results', []) or []
                dj_count += len(results)
                for art in results:
                    rec = parse_doaj(art, mid, anchor)
                    all_cands.append(rec)

    print('Crossref缓存: %d 条' % ct_count)
    print('DOAJ缓存: %d 条' % dj_count)
    print('总候选: %d 条' % len(all_cands))

    # ================================================================
    # STEP 4: 判分门（R门→N门→硬底线→Q0→Q门→打分≥1→去重→双池）
    # ================================================================
    print('\n=== 判分门 ===')

    cr_cache = {}  # DOI → Crossref引用数

    def process_pool(candidates, pool_level, seen_doi, seen_title, seen_parent_doi):
        mod_cands = defaultdict(list)
        for rec in candidates:
            mod_cands[rec['module']].append(rec)

        funnel = {}
        for mod in modules:
            mid = mod['id']
            funnel[mid] = {'raw':0,'anchor':0,'R':0,'N':0,'hard':0,'Q0':0,'Q':0,'score':0,'final':0}

        parent_fold_log = []
        discovery_list = []
        result = []

        for mod in modules:
            mid = mod['id']
            cands = mod_cands.get(mid, [])
            f = funnel[mid]
            f['raw'] = len(cands)

            for rec in cands:
                title_low = (rec['title'] or '').lower()
                abstract_low = (rec['abstract'] or '').lower()

                # 锚词检查
                hits = find_anchor_hits(title_low, abstract_low, mod['anchors'],
                                        title_only=(pool_level == 1))
                if not hits:
                    continue
                f['anchor'] += 1
                rec['anchor_hits'] = hits

                # R门
                if not check_R_gate(title_low, hits):
                    continue
                f['R'] += 1

                # N门
                multi_count = count_multi_word_hits(hits)
                if not check_N_gate(title_low, multi_count):
                    continue
                f['N'] += 1

                # 硬底线
                if not rec['doi']: continue
                if rec.get('is_retracted'): continue
                if rec['year'] is None or not (1900 <= rec['year'] <= 2026): continue
                tn = rec['type'].replace('-',' ').replace('_',' ').lower()
                if tn and tn not in ALLOWED_TYPES: continue
                f['hard'] += 1

                # Q0门：DOAJ无被引数据 → Crossref回查
                if rec['channel'] == 'doaj' and rec['cr_cites'] == 0 and rec['oa_cites'] == 0:
                    doi = rec['doi']
                    if not doi:
                        discovery_list.append(rec)
                        continue
                    if doi in cr_cache:
                        rec['cr_cites'] = cr_cache[doi]
                    else:
                        cr_url = 'https://api.crossref.org/works/%s' % doi
                        obj, err, _ = fetch_json(cr_url)
                        if obj:
                            msg = obj.get('message', {}) or {}
                            cites = int(msg.get('is-referenced-by-count') or 0)
                            rec['cr_cites'] = cites
                            cr_cache[doi] = cites
                        else:
                            discovery_list.append(rec)
                            continue
                        time.sleep(0.4)
                    if rec['cr_cites'] == 0:
                        discovery_list.append(rec)
                        continue
                if rec['channel'] == 'doaj':
                    f['Q0'] += 1

                # Q门
                T = get_T(rec['year'])
                q_gates = []
                if pool_level == 1:
                    if rec['oa_cites'] >= T: q_gates.append('Q1')
                    if rec['cr_cites'] >= int(0.6 * T): q_gates.append('Q2')
                    mc = max(rec['oa_cites'], rec['cr_cites'])
                    if in_whitelist(rec['venue']) and mc >= int(0.25 * T): q_gates.append('Q3')
                else:
                    if rec['oa_cites'] >= int(0.5 * T): q_gates.append('Q1')
                    if rec['cr_cites'] >= int(0.3 * T): q_gates.append('Q2')
                    mc = max(rec['oa_cites'], rec['cr_cites'])
                    if in_whitelist(rec['venue']) and mc >= int(0.15 * T): q_gates.append('Q3')

                if not q_gates:
                    continue
                f['Q'] += 1

                # 打分
                score = 0
                tn2 = _norm(title_low)
                an2 = _norm(abstract_low)
                for a in mod['anchors']:
                    anorm = _norm(a)
                    if a == 'metaphor AND politics':
                        if 'metaphor' in tn2 and 'politics' in tn2: score += 2
                        elif 'metaphor' in an2 or 'politics' in an2: score += 1
                    else:
                        if anorm in tn2: score += 2
                        if anorm in an2: score += 1
                if score < 1: continue
                f['score'] += 1
                rec['score'] = score

                # 放宽项
                relaxed = []
                if pool_level == 2:
                    title_hits = find_anchor_hits(title_low, '', mod['anchors'], title_only=True)
                    if not title_hits:
                        relaxed.append('强锚仅摘要命中')
                    if rec['oa_cites'] < T and rec['oa_cites'] >= int(0.5 * T):
                        relaxed.append('Q1降半档(0.5×T)')
                    if rec['cr_cites'] < int(0.6 * T) and rec['cr_cites'] >= int(0.3 * T):
                        relaxed.append('Q2降半档(0.3×T)')
                    mc = max(rec['oa_cites'], rec['cr_cites'])
                    if mc < int(0.25 * T) and mc >= int(0.15 * T) and in_whitelist(rec['venue']):
                        relaxed.append('Q3降半档(0.15×T)')
                    if rec['channel'] == 'doaj':
                        relaxed.append('DOAJ被引由Crossref回查补齐(cr_cites=%d)' % rec['cr_cites'])
                rec['relaxed'] = relaxed
                rec['q_gates'] = q_gates
                rec['pool_level'] = pool_level

                # 去重（DOI + 规范化标题 + 父级DOI折叠）
                d = rec['doi'].lower()
                t = norm_title(rec['title'])

                if d and d in seen_doi:
                    continue
                if t and t in seen_title:
                    continue

                # 父级DOI折叠：仅对书/章，不对期刊DOI
                rec_type = rec.get('type', '').lower()
                if rec_type in ['book', 'book-chapter', 'book chapter']:
                    pd = parent_doi(d)
                    if pd and pd in seen_parent_doi:
                        existing = seen_parent_doi[pd]
                        existing_cites = max(existing.get('oa_cites',0), existing.get('cr_cites',0))
                        new_cites = max(rec['oa_cites'], rec['cr_cites'])
                        if new_cites > existing_cites:
                            if existing in result:
                                result.remove(existing)
                                parent_fold_log.append({
                                    'kept_doi': d, 'removed_doi': existing['doi'],
                                    'parent_doi': pd, 'reason': '章书折叠·保留被引更高'})
                            seen_parent_doi[pd] = rec
                        else:
                            parent_fold_log.append({
                                'kept_doi': existing['doi'], 'removed_doi': d,
                                'parent_doi': pd, 'reason': '章书折叠·保留被引更高'})
                            continue
                    else:
                        if pd:
                            seen_parent_doi[pd] = rec

                if d: seen_doi[d] = mid
                if t: seen_title[t] = mid
                rec['cited_by_count'] = max(rec['oa_cites'], rec['cr_cites'])
                f['final'] += 1
                result.append(rec)

        return result, funnel, parent_fold_log, discovery_list

    # 池1
    seen_doi_p1, seen_title_p1, seen_pd_p1 = {}, {}, {}
    pool1, funnel_p1, fold_log_p1, disc_p1 = process_pool(
        list(all_cands), 1, seen_doi_p1, seen_title_p1, seen_pd_p1)
    # 池2
    pool2_cands = [c for c in all_cands
                   if not (c['doi'].lower() in seen_doi_p1 or norm_title(c['title']) in seen_title_p1)]
    pool2, funnel_p2, fold_log_p2, disc_p2 = process_pool(
        pool2_cands, 2, dict(seen_doi_p1), dict(seen_title_p1), dict(seen_pd_p1))

    final = pool1 + pool2
    final.sort(key=lambda r: (r['module'], r['pool_level'], -r['score'],
                              -r['cited_by_count'], r['doi']))

    p1_count = len(pool1)
    p2_count = len(pool2)
    grand = p1_count + p2_count
    all_fold_log = fold_log_p1 + fold_log_p2
    all_discovery = disc_p1 + disc_p2
    print('\n[池1] %d 条  [池2] %d 条  [合计] %d 条' % (p1_count, p2_count, grand))
    print('[章书折叠留痕] %d 条' % len(all_fold_log))
    print('[发现清单] %d 条' % len(all_discovery))

    # ================================================================
    # STEP 5: 落盘
    # ================================================================
    # 文献主档
    archive = []
    for r in final:
        archive.append({
            '模块号': r['module'], '池级': r['pool_level'], '标题': r['title'],
            '作者': r['authors'], '年份': r['year'], '刊物': r['venue'], 'DOI': r['doi'],
            'oa_cites': r['oa_cites'], 'cr_cites': r['cr_cites'],
            'type': r['type'], 'score': r['score'], '质量门': r['q_gates'],
            '锚词命中': r['anchor_hits'], '摘要': r['abstract'],
            '检索URL': r['search_url'], '使用锚词': r.get('anchor_used', ''),
            '放宽项': r.get('relaxed', []),
        })
    with open(os.path.join(OUT_DIR, '文献主档-v1.2补跑.json'), 'w', encoding='utf-8') as f:
        json.dump(archive, f, ensure_ascii=False, indent=1)

    # 每模块统计
    per_mod_p1 = defaultdict(int)
    per_mod_p2 = defaultdict(int)
    for r in pool1: per_mod_p1[r['module']] += 1
    for r in pool2: per_mod_p2[r['module']] += 1
    per_mod_total = {m['id']: per_mod_p1[m['id']] + per_mod_p2[m['id']] for m in modules}

    # 统计
    stats = {
        '检索日期': RETRIEVED, '判据版本': 'v1.2补跑',
        '锚词断言值': 69, '锚词实数': total_anchors,
        '候选总数': len(all_cands),
        '池级1_入库': p1_count, '池级2_入库': p2_count, '合计入库': grand,
        '池级1_达标': '是' if p1_count >= 200 else '否（判负照记）',
        '合计_达标': '是' if grand >= 300 else '否（判负照记）',
        '每模块实收_池1': dict(per_mod_p1),
        '每模块实收_池2': dict(per_mod_p2),
        '每模块实收_合计': per_mod_total,
        '漏斗_池1': {mid: dict(v) for mid, v in funnel_p1.items()},
        '漏斗_池2': {mid: dict(v) for mid, v in funnel_p2.items()},
        'OpenAlex_每模块统计': oa_stats,
        'OpenAlex_限额实测': {
            'limit': oa_limit,
            'remaining': oa_remaining,
            'reset': oa_reset,
            '探测URL': oa_probe_url,
        },
        'Crossref_缓存命中': ct_count,
        'DOAJ_缓存命中': dj_count,
        'Q0_Crossref回查': {
            '缓存大小': len(cr_cache),
            '说明': 'DOAJ无被引数据条目用DOI回查Crossref取被引数'
        },
        '章书折叠留痕数': len(all_fold_log),
        '发现清单数': len(all_discovery),
    }
    with open(os.path.join(OUT_DIR, '统计-v1.2补跑.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)

    # 章书折叠留痕
    fold_lines = ['# 章书折叠留痕 v1.2补跑', '', '条数: %d' % len(all_fold_log), '',
                  '| 保留DOI | 折叠DOI | 父级DOI | 原因 |',
                  '|---------|---------|---------|------|']
    for fl in all_fold_log:
        fold_lines.append('| %s | %s | %s | %s |' % (
            fl.get('kept_doi',''), fl.get('removed_doi',''),
            fl.get('parent_doi',''), fl.get('reason','')))
    with open(os.path.join(OUT_DIR, '章书折叠留痕-v1.2补跑.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(fold_lines) + '\n')

    # 发现清单
    disc_lines = ['# 发现清单 v1.2补跑（无被引数据条目）', '',
                  '检索日: %s' % RETRIEVED,
                  '条数: %d' % len(all_discovery), '',
                  '| DOI | 模块 | 标题 | 原因 |',
                  '|-----|------|------|------|']
    for rec in all_discovery:
        reason = '无DOI' if not rec['doi'] else 'Crossref无记录或被引=0'
        disc_lines.append('| %s | %s | %s | %s |' % (
            rec['doi'] or '(无)', rec['module'], (rec['title'] or '')[:60], reason))
    with open(os.path.join(OUT_DIR, '发现清单-v1.2补跑.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(disc_lines) + '\n')

    # queries.txt
    with open(os.path.join(RAW_DIR, 'queries.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(qlog) + '\n')

    # ================================================================
    # STEP 6: 控制台汇总
    # ================================================================
    print('\n' + '=' * 60)
    print('v1.2补跑 检索完成')
    print('锚词=%d (断言69) 模块=%d (断言15)' % (total_anchors, len(modules)))
    print('候选=%d | 池1=%d (目标≥200:%s) | 池2=%d | 合计=%d (目标≥300:%s)' % (
        len(all_cands), p1_count, '达标' if p1_count>=200 else '未达标',
        p2_count, grand, '达标' if grand>=300 else '未达标'))
    print('OpenAlex限额: limit=%s remaining=%s reset=%s' % (oa_limit, oa_remaining, oa_reset))
    print('Crossref缓存=%d DOAJ缓存=%d' % (ct_count, dj_count))
    print('Q0 Crossref回查缓存=%d' % len(cr_cache))
    print('章书折叠=%d 发现清单=%d' % (len(all_fold_log), len(all_discovery)))
    print()
    for mod in modules:
        mid = mod['id']
        print('  %s: P1=%d P2=%d 合计=%d' % (mid, per_mod_p1[mid], per_mod_p2[mid], per_mod_total[mid]))
    print('=' * 60)
    print('输出目录: %s' % OUT_DIR)

    # 清理 __pycache__
    for d in [SCRIPT_DIR, os.path.dirname(_tool_path)]:
        c = os.path.join(d, '__pycache__')
        if os.path.isdir(c): shutil.rmtree(c)
    print('[已清理 __pycache__]')


if __name__ == '__main__':
    main()
