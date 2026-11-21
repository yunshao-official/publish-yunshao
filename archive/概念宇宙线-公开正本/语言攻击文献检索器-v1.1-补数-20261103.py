#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言与思想攻击·文献检索器 v1.1 补数版（2026-11-03）
按协调员指令：69锚词逐条发Crossref+DOAJ，锚词从判据书§五解析
"""
import json, os, re, sys, time, shutil
import urllib.error, urllib.parse, urllib.request
import importlib.util
from collections import defaultdict

# ---------- 路径（禁止硬编码绝对路径） ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
OUT_DIR = os.path.join(SCRIPT_DIR, '语言与思想攻击文献库-v1.1-20261103')
RAW_DIR = os.path.join(OUT_DIR, 'raw')
RETRIEVED = '2026-11-03'
UA = {'User-Agent': 'yunshao-langattack/1.1-bushu (%s)' % REPO}

# ---------- 复用既有轮子 ----------
_tool_rel = os.path.join('archive','10-治理与哲学','04-工具与代码','控制权文献库检索器-v1.0-20261102.py')
_tool_path = os.path.join(REPO, _tool_rel)
_spec = importlib.util.spec_from_file_location('_ctrl', _tool_path)
_tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tool)
oa_abstract = _tool.oa_abstract
strip_tags = _tool.strip_tags
norm_title = _tool.norm_title

# ---------- 从判据书§五解析锚词 ----------
def parse_anchors_from_criteria():
    criteria_path = os.path.join(SCRIPT_DIR, '语言与思想攻击·文献检索判据书-v1.1-20261103.md')
    with open(criteria_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'## 五、锁定锚词表.*?\n(.*?)\n【修改记录】', content, re.DOTALL)
    if not match:
        raise ValueError("无法解析判据书§五")
    section = match.group(1)
    modules = []
    total_anchors = 0
    for line in section.strip().split('\n'):
        line = line.strip()
        if not line.startswith('-'):
            continue
        m = re.match(r'^-\s+\**M(\d\d)\**：(.+)$', line)
        if m:
            mod_id = 'M%s' % m.group(1)
            anchors = [a.strip() for a in m.group(2).split('｜')]
            modules.append({'id': mod_id, 'anchors': anchors})
            total_anchors += len(anchors)
    assert len(modules) == 15, '模块数=%d，必须=15' % len(modules)
    assert total_anchors == 69, '锚词总数=%d，必须=69' % total_anchors
    return modules

# ---------- fetch ----------
def fetch_json(url, retries=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode('utf-8','replace')), None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                ra = e.headers.get('Retry-After','?')
                print('    429 Retry-After=%s, fast-fail' % ra); sys.stdout.flush()
                time.sleep(3)
                return None, '429 rate limited (Retry-After=%s)' % ra
            else:
                time.sleep(2)
        except Exception as e:
            time.sleep(2)
    return None, 'exhausted retries'

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

# ---------- R门/N门 ----------
DOMAIN_WORDS = ['language','linguistic','word','words','lexical','lexicon','vocabulary',
    'discourse','speech','speaking','tongue','naming','term','terminology',
    'semantic','semantics','pragmatics','rhetoric','meaning','concept','metaphor',
    'translation','narrative','dialect']

NEGATIVE_WORDS = ['dna','protein','amino acid','bacteria','antimicrobial','antibiotic',
    'insulin','diabetes','tumor','cancer','carcinoma','pcr','crispr','phylogenetic',
    'modeltest','partitionfinder','job shop','quadratic assignment','supply chain',
    'venture creation','customer loyalty','biomarker','surrogate endpoint','quantum',
    'internet of things','wetting','asset pricing','econometric','stock market',
    'pandemic patients','hospitalized','clinical characteristics','mortality']

def _norm(s):
    return s.replace('-', ' ')

def check_R_gate(title_low, matched_anchors):
    tn = _norm(title_low)
    has_multi = False
    has_single_with_domain = False
    for a in matched_anchors:
        if a == 'metaphor AND politics':
            if 'metaphor' in tn and 'politics' in tn:
                has_multi = True
        elif ' ' in a or '-' in a:
            has_multi = True
        else:
            if any(dw in tn for dw in DOMAIN_WORDS):
                has_single_with_domain = True
    return has_multi or has_single_with_domain

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
                if 'metaphor' in tn and 'politics' in tn:
                    hits.append(a)
            else:
                combined = tn + ' ' + an
                if 'metaphor' in combined and 'politics' in combined:
                    hits.append(a)
        else:
            if anorm in tn:
                hits.append(a)
            elif not title_only and anorm in an:
                hits.append(a)
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

# ---------- 解析函数 ----------
def parse_oa(w, mid, anchor):
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
                search_url='', anchor_used=anchor)

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
    # DOI may be in bibjson.identifier[] with type="doi"
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
# 主流程
# ====================================================================
def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    # 解析锚词
    modules = parse_anchors_from_criteria()
    total_anchors = sum(len(m['anchors']) for m in modules)
    print('锚词解析完成：%d模块 %d锚词 (断言=15/69)' % (len(modules), total_anchors))

    all_cands = []
    req_stats = {}
    for m in modules:
        req_stats[m['id']] = {'oa_cache':0,'oa_new':0,'oa_429':0,'oa_fail':0,
                              'cr_cache':0,'cr_new':0,'cr_fail':0,
                              'dj_cache':0,'dj_new':0,'dj_fail':0}
    qlog = []
    total_raw = 0
    oa_429_retry_after = None

    # ================================================================
    # STEP 1: 加载已有OA缓存（M01-M05）
    # ================================================================
    print('\n=== 加载OpenAlex缓存 ===')
    for mod in modules[:5]:
        mid = mod['id']
        for qi in range(1, 5):
            for page in range(1, 11):
                slug = '%s-oa-%02d-p%d' % (mid, qi, page)
                raw_path = os.path.join(RAW_DIR, slug + '.json')
                if os.path.exists(raw_path) and os.path.getsize(raw_path) > 100:
                    with open(raw_path, 'r', encoding='utf-8') as f:
                        obj = json.load(f)
                    works = obj.get('results', []) or []
                    if works:
                        req_stats[mid]['oa_cache'] += 1
                        total_raw += len(works)
                        for w in works:
                            all_cands.append(parse_oa(w, mid, 'cached'))

    # ================================================================
    # STEP 2: 逐锚词发Crossref + DOAJ（69×2=138 queries）
    # ================================================================
    print('\n=== Crossref + DOAJ 逐锚词检索（69锚词×2通道） ===')
    for mod in modules:
        mid = mod['id']
        print('\n--- %s (%d锚词) ---' % (mid, len(mod['anchors'])))

        for ai, anchor in enumerate(mod['anchors'], 1):
            # --- Crossref ---
            ct_slug = '%s-ct-%02d' % (mid, ai)
            ct_path = os.path.join(RAW_DIR, ct_slug + '.json')
            sel_cr = 'DOI,title,container-title,author,published,issued,created,is-referenced-by-count,abstract,type'
            ct_url = 'https://api.crossref.org/works?query.title=%s&rows=25&sort=is-referenced-by-count&order=desc&select=%s' % (urllib.parse.quote(anchor), sel_cr)

            if os.path.exists(ct_path) and os.path.getsize(ct_path) > 100:
                with open(ct_path, 'r', encoding='utf-8') as f:
                    obj = json.load(f)
                items = (obj.get('message', {}) or {}).get('items', []) or []
                req_stats[mid]['cr_cache'] += 1
                qlog.append('%s|crossref|CACHED|%s' % (ct_slug, ct_url))
                if items:
                    total_raw += len(items)
                    for it in items:
                        all_cands.append(parse_cr(it, mid, anchor))
            else:
                qlog.append('%s|crossref|%s' % (ct_slug, ct_url))
                req_stats[mid]['cr_new'] += 1
                obj, err = fetch_json(ct_url)
                if obj is None:
                    req_stats[mid]['cr_fail'] += 1
                    print('  %s FAIL: %s' % (ct_slug, err))
                else:
                    with open(ct_path, 'w', encoding='utf-8') as f:
                        json.dump(obj, f, ensure_ascii=False)
                    items = (obj.get('message', {}) or {}).get('items', []) or []
                    total_raw += len(items)
                    for it in items:
                        all_cands.append(parse_cr(it, mid, anchor))
                    print('  %s got %d' % (ct_slug, len(items)))
                time.sleep(1.0)

            # --- DOAJ ---
            dj_slug = '%s-dj-%02d' % (mid, ai)
            dj_path = os.path.join(RAW_DIR, dj_slug + '.json')
            dj_url = 'https://doaj.org/api/search/articles/%s' % urllib.parse.quote(anchor)

            if os.path.exists(dj_path) and os.path.getsize(dj_path) > 100:
                with open(dj_path, 'r', encoding='utf-8') as f:
                    obj = json.load(f)
                results = obj.get('results', []) or []
                req_stats[mid]['dj_cache'] += 1
                qlog.append('%s|doaj|CACHED|%s' % (dj_slug, dj_url))
                if results:
                    total_raw += len(results)
                    for art in results:
                        all_cands.append(parse_doaj(art, mid, anchor))
            else:
                qlog.append('%s|doaj|%s' % (dj_slug, dj_url))
                req_stats[mid]['dj_new'] += 1
                obj, err = fetch_json(dj_url)
                if obj is None:
                    req_stats[mid]['dj_fail'] += 1
                    print('  %s DOAJ FAIL: %s' % (dj_slug, err))
                else:
                    with open(dj_path, 'w', encoding='utf-8') as f:
                        json.dump(obj, f, ensure_ascii=False)
                    results = obj.get('results', []) or []
                    total_raw += len(results)
                    for art in results:
                        all_cands.append(parse_doaj(art, mid, anchor))
                    print('  %s DOAJ got %d' % (dj_slug, len(results)))
                time.sleep(1.0)

    # 保存queries.txt
    with open(os.path.join(RAW_DIR, 'queries.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(qlog) + '\n')
    print('\n[检索完成] 原始候选=%d' % total_raw)

    # ================================================================
    # STEP 3: 筛选 → 双池
    # ================================================================
    def process_pool(candidates, pool_level, seen_doi, seen_title):
        mod_cands = defaultdict(list)
        for rec in candidates:
            mod_cands[rec['module']].append(rec)

        # 总漏斗 + 按通道漏斗
        funnel = {}
        ch_funnel = {}
        for mod in modules:
            mid = mod['id']
            funnel[mid] = {'raw':0,'anchor':0,'R':0,'N':0,'hard':0,'Q':0,'score':0,'dedup':0,'final':0}
            ch_funnel[mid] = {
                'openalex': {'raw':0,'final':0},
                'crossref': {'raw':0,'final':0},
                'doaj': {'raw':0,'final':0},
            }

        result = []

        for mod in modules:
            mid = mod['id']
            cands = mod_cands.get(mid, [])
            f = funnel[mid]
            f['raw'] = len(cands)
            for c in cands:
                ch_funnel[mid][c['channel']]['raw'] += 1

            for rec in cands:
                ch = rec['channel']
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

                # DOAJ无被引 → 池1不过；池2特批过Q门
                if rec['channel'] == 'doaj' and rec['oa_cites'] == 0 and rec['cr_cites'] == 0:
                    if pool_level == 1:
                        continue
                    else:
                        q_gates.append('DOAJ无被引·池2特批')

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
                    if rec['channel'] == 'doaj' and mc == 0:
                        relaxed.append('DOAJ无被引数')
                rec['relaxed'] = relaxed
                rec['q_gates'] = q_gates
                rec['pool_level'] = pool_level

                # 去重
                d = rec['doi'].lower()
                t = norm_title(rec['title'])
                if d and d in seen_doi: continue
                if t and t in seen_title: continue
                if d: seen_doi[d] = mid
                if t: seen_title[t] = mid
                rec['cited_by_count'] = max(rec['oa_cites'], rec['cr_cites'])
                f['final'] += 1
                ch_funnel[mid][ch]['final'] += 1
                result.append(rec)

        return result, funnel, ch_funnel

    # 池1
    seen_doi_p1, seen_title_p1 = {}, {}
    pool1, funnel_p1, ch_funnel_p1 = process_pool(list(all_cands), 1, seen_doi_p1, seen_title_p1)
    # 池2
    pool2_cands = [c for c in all_cands
                   if not (c['doi'].lower() in seen_doi_p1 or norm_title(c['title']) in seen_title_p1)]
    pool2, funnel_p2, ch_funnel_p2 = process_pool(pool2_cands, 2, dict(seen_doi_p1), dict(seen_title_p1))

    final = pool1 + pool2
    final.sort(key=lambda r: (r['module'], r['pool_level'], -r['score'],
                              -r['cited_by_count'], r['doi']))

    p1_count = len(pool1)
    p2_count = len(pool2)
    grand = p1_count + p2_count
    print('\n[池1] %d 条  [池2] %d 条  [合计] %d 条' % (p1_count, p2_count, grand))

    # ================================================================
    # STEP 4: 落盘
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
    with open(os.path.join(OUT_DIR, '文献主档-v1.1.json'), 'w', encoding='utf-8') as f:
        json.dump(archive, f, ensure_ascii=False, indent=1)

    # 每模块统计
    per_mod_p1 = defaultdict(int)
    per_mod_p2 = defaultdict(int)
    for r in pool1: per_mod_p1[r['module']] += 1
    for r in pool2: per_mod_p2[r['module']] += 1
    per_mod_total = {m['id']: per_mod_p1[m['id']] + per_mod_p2[m['id']] for m in modules}

    # 统计
    stats = {
        '检索日期': RETRIEVED, '锚词断言值': 69, '锚词实数': total_anchors,
        '候选总数': total_raw,
        '池级1_入库': p1_count, '池级2_入库': p2_count, '合计入库': grand,
        '每模块实收_池1': dict(per_mod_p1),
        '每模块实收_池2': dict(per_mod_p2),
        '每模块实收_合计': per_mod_total,
        '漏斗_池1': {mid: dict(v) for mid, v in funnel_p1.items()},
        '漏斗_池2': {mid: dict(v) for mid, v in funnel_p2.items()},
        '通道漏斗_池1': {mid: dict(v) for mid, v in ch_funnel_p1.items()},
        '通道漏斗_池2': {mid: dict(v) for mid, v in ch_funnel_p2.items()},
        '每模块请求统计': req_stats,
        'OpenAlex_429_Retry-After': oa_429_retry_after,
        'OpenAlex_429_说明': 'M06-M15 OpenAlex通道因IP日预算耗尽(429)无数据',
    }
    with open(os.path.join(OUT_DIR, '统计-v1.1.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)

    # 卷文件
    mod_names = {
        'M01':'一','M02':'二','M03':'三','M04':'四','M05':'五',
        'M06':'六','M07':'七','M08':'八','M09':'九','M10':'十',
        'M11':'十一','M12':'十二','M13':'十三','M14':'十四','M15':'十五',
    }
    mod_fullnames = {
        'M01':'语言与思想的因果','M02':'新话、双重话语与语言工程',
        'M03':'概念隐喻与政治框架','M04':'宣传、灌输与终止性套语',
        'M05':'国家审查与自我审查','M06':'平台治理与内容审核',
        'M07':'算法规避与影子限制','M08':'谐音、禁忌与词汇替换',
        'M09':'政治正确、辱称与语义漂移','M10':'语言意识形态、符号权力与守门',
        'M11':'沉默、寒蝉与舆论气候','M12':'讽刺、迷因与地下话语',
        'M13':'编码、隐写与规避书写','M14':'语言剥夺与概念后果',
        'M15':'媒体效应与被说出的问题',
    }

    for mod in modules:
        mid = mod['id']
        num = mod_names[mid]
        name = mod_fullnames[mid]
        p1r = [r for r in pool1 if r['module'] == mid]
        p2r = [r for r in pool2 if r['module'] == mid]
        L = []
        L.append('---')
        L.append('title: "语言与思想攻击文献库·卷%s·%s"' % (num, name))
        L.append('date: %s' % RETRIEVED)
        L.append('version: 1.1')
        L.append('status: 池1=%d条 池2=%d条 合计=%d条' % (len(p1r), len(p2r), len(p1r)+len(p2r)))
        L.append('---')
        L.append('')
        L.append('# 卷%s · %s（%s）' % (num, name, mid))
        L.append('')
        L.append('> 判据：`v1.1-20261103.md`（已冻结）｜检索日：%s｜锚词=%d条（从判据书§五解析）' % (RETRIEVED, len(mod['anchors'])))
        L.append('> 锚词：' + ' / '.join(mod['anchors']))
        L.append('')

        # 通道漏斗
        cf1 = ch_funnel_p1.get(mid, {})
        cf2 = ch_funnel_p2.get(mid, {})
        L.append('## 通道漏斗')
        L.append('')
        L.append('| 通道 | 池1原始 | 池1入库 | 池2原始 | 池2入库 |')
        L.append('|------|---------|---------|---------|---------|')
        for ch_name in ['openalex', 'crossref', 'doaj']:
            r1 = cf1.get(ch_name, {}).get('raw', 0)
            f1 = cf1.get(ch_name, {}).get('final', 0)
            r2 = cf2.get(ch_name, {}).get('raw', 0)
            f2 = cf2.get(ch_name, {}).get('final', 0)
            L.append('| %s | %d | %d | %d | %d |' % (ch_name, r1, f1, r2, f2))
        L.append('')

        # 池1
        L.append('## 池级 1 · 严格池（%d 条）' % len(p1r))
        L.append('')
        if not p1r:
            L.append('*（无条目）*')
            L.append('')
        for i, r in enumerate(p1r, 1):
            _entry(L, i, r, mod)

        # 池2
        L.append('## 池级 2 · 次级池（%d 条）' % len(p2r))
        L.append('')
        if not p2r:
            L.append('*（无条目）*')
            L.append('')
        for i, r in enumerate(p2r, 1):
            _entry(L, i, r, mod)

        fn = os.path.join(OUT_DIR, '卷%s·%s-20261103.md' % (num, name))
        with open(fn, 'w', encoding='utf-8') as f:
            f.write('\n'.join(L) + '\n')

    # ================================================================
    # STEP 5: 控制台汇总（协调员要求的格式）
    # ================================================================
    print('\n' + '=' * 70)
    print('锚词断言值: %d (从判据书§五解析)' % total_anchors)
    print('池1=%d (目标≥200: %s)' % (p1_count, '达标' if p1_count >= 200 else '未达标'))
    print('池1+池2=%d (目标≥300: %s)' % (grand, '达标' if grand >= 300 else '未达标'))
    if oa_429_retry_after:
        print('OA 429 Retry-After=%s' % oa_429_retry_after)
    print()

    # 每模块×每通道×池级漏斗
    print('每模块×每通道×池级漏斗:')
    print('%-5s | %-20s | %-20s' % ('模块', '池1 (OA/CR/DJ→final)', '池2 (OA/CR/DJ→final)'))
    print('-' * 70)
    for mod in modules:
        mid = mod['id']
        f1 = funnel_p1[mid]
        f2 = funnel_p2[mid]
        cf1 = ch_funnel_p1.get(mid, {})
        cf2 = ch_funnel_p2.get(mid, {})
        oa1 = cf1.get('openalex', {}).get('final', 0)
        cr1 = cf1.get('crossref', {}).get('final', 0)
        dj1 = cf1.get('doaj', {}).get('final', 0)
        oa2 = cf2.get('openalex', {}).get('final', 0)
        cr2 = cf2.get('crossref', {}).get('final', 0)
        dj2 = cf2.get('doaj', {}).get('final', 0)
        print('%-5s | OA=%d CR=%d DJ=%d → %d | OA=%d CR=%d DJ=%d → %d' % (
            mid, oa1, cr1, dj1, f1['final'], oa2, cr2, dj2, f2['final']))

    print()
    # 池1前10条标题
    print('每模块池1前10条标题:')
    for mod in modules:
        mid = mod['id']
        p1r = [r for r in pool1 if r['module'] == mid]
        print('\n  %s (%d条):' % (mid, len(p1r)))
        for i, r in enumerate(p1r[:10], 1):
            print('    %2d. [%s] %s' % (i, r['channel'], r['title'][:90]))

    print('\n' + '=' * 70)

    # 清理 __pycache__
    for d in [SCRIPT_DIR, os.path.dirname(_tool_path)]:
        c = os.path.join(d, '__pycache__')
        if os.path.isdir(c): shutil.rmtree(c)
    print('[已清理 __pycache__]')


def _entry(L, i, r, mod):
    au = '; '.join(r['authors'][:6]) + (' 等' if len(r['authors']) > 6 else '')
    doi_s = r['doi'] or '(无DOI)'
    cited = max(r['oa_cites'], r['cr_cites'])
    gates = '/'.join(r['q_gates'])
    anch = ', '.join(r['anchor_hits'][:4])
    pool = '池%d' % r['pool_level']
    L.append('%d｜%s(%d).%s｜%s｜%s｜被引%d｜score=%d｜%s｜%s｜锚词[%s]' % (
        i, au, r['year'], r['title'][:100], r['venue'] or '（载体未记）',
        doi_s, cited, r['score'], r.get('anchor_used',''), gates, anch))
    if r.get('relaxed'):
        L.append('    放宽项：%s' % '; '.join(r['relaxed']))
    if r['abstract']:
        L.append('    摘要：%s' % r['abstract'][:500])
    L.append('')


if __name__ == '__main__':
    main()
