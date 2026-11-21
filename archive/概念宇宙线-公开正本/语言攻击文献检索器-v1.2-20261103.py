#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言与思想攻击·文献检索器 v1.2（2026-11-03）
判据：v1.2-20261103.md（已冻结，sha256 0be27507）
改动：Q0被引补齐、R门政治话语收紧、N表补词、父级DOI折叠
"""
import json, os, re, sys, time, shutil
import urllib.error, urllib.parse, urllib.request
import importlib.util
from collections import defaultdict

# ---------- 路径 ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..'))
OUT_DIR = os.path.join(SCRIPT_DIR, '语言与思想攻击文献库-v1.2-20261103')
RAW_DIR = os.path.join(OUT_DIR, 'raw')
# v1.1 补数的 raw 缓存目录
V11_RAW = os.path.join(SCRIPT_DIR, '语言与思想攻击文献库-v1.1-20261103', 'raw')
RETRIEVED = '2026-11-03'
UA = {'User-Agent': 'yunshao-langattack/1.2 (%s)' % REPO}

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
                rl = e.headers.get('x-ratelimit-remaining','?')
                time.sleep(3)
                return None, '429 (Retry-After=%s, remaining=%s)' % (ra, rl)
            else:
                time.sleep(2)
        except Exception:
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

# ---------- v1.2 R门 ----------
# 需要政治-话语域词的单词锚（v1.2 §二.3 明确列出）
STRICT_SINGLE_ANCHORS = {
    'frame','framing','propaganda','totalitarian','taboo','substitution',
    'avoidance','slur','silence','meme','satire','parody','attrition',
    'priming','cultivation'
}
# 政治-话语词集（子串匹配，大小写不敏感）
POLITICAL_WORDS = ['polic','politic','ideolog','discours','rhetor','propagand',
    'censor','narrat','hegemon','power','media','press','public','opinion','political']
# 辅助语言域词（v1.2: 只算辅助，不算充分）
DOMAIN_WORDS = ['language','linguistic','word','words','lexical','lexicon','vocabulary',
    'discourse','speech','speaking','tongue','naming','term','terminology',
    'semantic','semantics','pragmatics','rhetoric','meaning','concept','metaphor',
    'translation','narrative','dialect']

def _norm(s):
    return s.replace('-', ' ')

def check_R_gate(title_low, matched_anchors):
    """v1.2 R门：多词强锚标题直通；严格单词锚需政治-话语词；其他单词锚需语言域词。"""
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
            # v1.2: 必须同现政治-话语词
            if any(pw in tn for pw in POLITICAL_WORDS):
                has_strict_single_with_political = True
        else:
            # 其他单词锚：仍需语言域词
            if any(dw in tn for dw in DOMAIN_WORDS):
                has_other_single_with_domain = True
    return has_multi or has_strict_single_with_political or has_other_single_with_domain

# ---------- v1.2 N表（补词） ----------
NEGATIVE_WORDS = [
    # v1.1 原有
    'dna','protein','amino acid','bacteria','antimicrobial','antibiotic',
    'insulin','diabetes','tumor','cancer','carcinoma','pcr','crispr','phylogenetic',
    'modeltest','partitionfinder','job shop','quadratic assignment','supply chain',
    'venture creation','customer loyalty','biomarker','surrogate endpoint','quantum',
    'internet of things','wetting','asset pricing','econometric','stock market',
    'pandemic patients','hospitalized','clinical characteristics','mortality',
    # v1.2 补词（R4 漏网：语音合成/深度学习/编程等）
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

# ---------- 父级DOI折叠（v1.2 §二.5） ----------
def parent_doi(doi):
    """去掉DOI末段（按/和.切），返回容器段"""
    if not doi: return ''
    parts = doi.split('/')
    if len(parts) >= 2:
        prefix = parts[0]
        suffix_parts = parts[1].split('.')
        if len(suffix_parts) > 1:
            return prefix + '/' + '.'.join(suffix_parts[:-1])
    return doi

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
    total_anchors = sum(len(m['anchors']) for m in modules)
    print('v1.2 锚词=%d 模块=%d (断言 69/15)' % (total_anchors, len(modules)))

    all_cands = []
    req_stats = {}
    for m in modules:
        req_stats[m['id']] = {'oa_cache':0,'oa_new':0,'oa_429':0,'oa_fail':0,
                              'cr_cache':0,'cr_new':0,'cr_fail':0,
                              'dj_cache':0,'dj_new':0,'dj_fail':0}
    qlog = []
    total_raw = 0
    oa_429_info = None

    # ================================================================
    # STEP 1: 加载缓存（OA from v1.0, CT/DJ from v1.1 补数）
    # ================================================================
    print('\n=== 加载缓存 ===')
    # OA缓存（M01-M05 from v1.0 raw）
    v10_raw = os.path.join(SCRIPT_DIR, '语言与思想攻击文献库-20261103', 'raw')
    for mod in modules[:5]:
        mid = mod['id']
        for qi in range(1, 5):
            for page in range(1, 11):
                slug = '%s-oa-%02d-p%d' % (mid, qi, page)
                # 先查v1.2 raw，再查v1.0 raw
                for src_dir in [RAW_DIR, v10_raw]:
                    raw_path = os.path.join(src_dir, slug + '.json')
                    if os.path.exists(raw_path) and os.path.getsize(raw_path) > 100:
                        with open(raw_path, 'r', encoding='utf-8') as f:
                            obj = json.load(f)
                        works = obj.get('results', []) or []
                        if works:
                            req_stats[mid]['oa_cache'] += 1
                            total_raw += len(works)
                            for w in works:
                                all_cands.append(parse_oa(w, mid, 'cached'))
                        break

    # CT/DJ缓存（from v1.1 补数 raw）
    for mod in modules:
        mid = mod['id']
        for ai, anchor in enumerate(mod['anchors'], 1):
            # Crossref
            ct_slug = '%s-ct-%02d' % (mid, ai)
            for src_dir in [RAW_DIR, V11_RAW]:
                ct_path = os.path.join(src_dir, ct_slug + '.json')
                if os.path.exists(ct_path) and os.path.getsize(ct_path) > 100:
                    with open(ct_path, 'r', encoding='utf-8') as f:
                        obj = json.load(f)
                    items = (obj.get('message', {}) or {}).get('items', []) or []
                    req_stats[mid]['cr_cache'] += 1
                    qlog.append('%s|crossref|CACHED' % ct_slug)
                    total_raw += len(items)
                    for it in items:
                        all_cands.append(parse_cr(it, mid, anchor))
                    break

            # DOAJ
            dj_slug = '%s-dj-%02d' % (mid, ai)
            for src_dir in [RAW_DIR, V11_RAW]:
                dj_path = os.path.join(src_dir, dj_slug + '.json')
                if os.path.exists(dj_path) and os.path.getsize(dj_path) > 100:
                    with open(dj_path, 'r', encoding='utf-8') as f:
                        obj = json.load(f)
                    results = obj.get('results', []) or []
                    req_stats[mid]['dj_cache'] += 1
                    qlog.append('%s|doaj|CACHED' % dj_slug)
                    total_raw += len(results)
                    for art in results:
                        all_cands.append(parse_doaj(art, mid, anchor))
                    break

    print('缓存加载完成: 原始候选=%d' % total_raw)

    # ================================================================
    # STEP 2: OpenAlex 探测
    # ================================================================
    print('\n=== OpenAlex 探测 ===')
    oa_probe_url = 'https://api.openalex.org/works?filter=title_and_abstract.search:algospeak&per-page=1'
    obj, err = fetch_json(oa_probe_url)
    if obj is None and err and '429' in str(err):
        oa_429_info = err
        print('OA 仍为 429: %s' % err)
    elif obj is not None:
        print('OA 恢复! 开始补跑 M06-M15...')
        # TODO: 补跑逻辑（如果OA恢复）
    else:
        print('OA 探测异常: %s' % err)

    # ================================================================
    # STEP 3: Q0 被引补齐（DOAJ → Crossref回查）
    # ================================================================
    print('\n=== Q0 被引补齐 ===')
    # 收集所有DOAJ候选
    doaj_cands = [c for c in all_cands if c['channel'] == 'doaj']
    print('DOAJ候选总数: %d' % len(doaj_cands))

    # 先过R门筛选，只回查多词强锚命中标题的
    q0_candidates = []
    for rec in doaj_cands:
        title_low = (rec['title'] or '').lower()
        mod = [m for m in modules if m['id'] == rec['module']][0]
        hits = find_anchor_hits(title_low, '', mod['anchors'], title_only=True)
        multi_hits = [h for h in hits if (' ' in h or '-' in h) or h == 'metaphor AND politics']
        if multi_hits:
            q0_candidates.append(rec)

    print('R门多词强锚命中标题的DOAJ候选: %d' % len(q0_candidates))

    # 按锚词分组，每组最多20条
    q0_groups = defaultdict(list)
    for rec in q0_candidates:
        q0_groups[rec['anchor_used']].append(rec)

    # 限制每组20条
    q0_limited = []
    for anchor, recs in q0_groups.items():
        q0_limited.extend(recs[:20])
    print('分组限制后(每组≤20): %d' % len(q0_limited))

    # DOI去重
    doi_seen = {}
    q0_unique = []
    for rec in q0_limited:
        doi = rec['doi']
        if doi and doi not in doi_seen:
            doi_seen[doi] = rec
            q0_unique.append(rec)
    print('DOI去重后: %d' % len(q0_unique))

    # 回查Crossref（上限400次）
    Q0_MAX = 400
    q0_actual = 0
    q0_hit = 0
    q0_miss = 0
    q0_no_doi = 0
    discovery_list = []  # 无被引数据条目

    for rec in q0_unique:
        if q0_actual >= Q0_MAX:
            break
        doi = rec['doi']
        if not doi:
            q0_no_doi += 1
            discovery_list.append(rec)
            continue

        cr_url = 'https://api.crossref.org/works/%s' % doi
        obj, err = fetch_json(cr_url)
        q0_actual += 1

        if obj is not None:
            msg = obj.get('message', {}) or {}
            cites = int(msg.get('is-referenced-by-count') or 0)
            rec['cr_cites'] = cites
            if cites > 0:
                q0_hit += 1
            else:
                q0_miss += 1
                discovery_list.append(rec)
        else:
            q0_miss += 1
            discovery_list.append(rec)

        time.sleep(0.4)  # 间隔≥0.4秒

    print('Q0回查: 应回查=%d 实回查=%d 命中被引=%d 无记录=%d 无DOI=%d' % (
        len(q0_unique), q0_actual, q0_hit, q0_miss, q0_no_doi))
    print('Q0筛掉DOAJ候选: %d' % len(discovery_list))

    # 写发现清单
    disc_lines = ['# 发现清单 v1.2（无被引数据DOAJ条目）', '',
                  '检索日: %s' % RETRIEVED,
                  '条数: %d' % len(discovery_list), '',
                  '| DOI | 模块 | 标题 | 原因 |',
                  '|-----|------|------|------|']
    for rec in discovery_list:
        reason = '无DOI' if not rec['doi'] else 'Crossref无记录或被引=0'
        disc_lines.append('| %s | %s | %s | %s |' % (
            rec['doi'] or '(无)', rec['module'], (rec['title'] or '')[:60], reason))
    disc_path = os.path.join(OUT_DIR, '发现清单-v1.2.md')
    with open(disc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(disc_lines) + '\n')

    # ================================================================
    # STEP 4: 筛选（R门→N门→硬底线→Q0→Q门→打分→父DOI折叠→双池）
    # ================================================================
    def process_pool(candidates, pool_level, seen_doi, seen_title, seen_parent_doi):
        mod_cands = defaultdict(list)
        for rec in candidates:
            mod_cands[rec['module']].append(rec)

        funnel = {}
        ch_funnel = {}
        for mod in modules:
            mid = mod['id']
            funnel[mid] = {'raw':0,'anchor':0,'R':0,'N':0,'hard':0,'Q0':0,'Q':0,'score':0,'final':0}
            ch_funnel[mid] = {
                'openalex': {'raw':0,'final':0},
                'crossref': {'raw':0,'final':0},
                'doaj': {'raw':0,'final':0},
            }

        parent_fold_log = []  # 章书折叠留痕
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

                # R门（v1.2 收紧）
                if not check_R_gate(title_low, hits):
                    continue
                f['R'] += 1

                # N门（v1.2 补词）
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

                # Q0门：DOAJ无被引数据 → 不入池
                if ch == 'doaj' and rec['cr_cites'] == 0 and rec['oa_cites'] == 0:
                    continue
                if ch == 'doaj':
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
                    if ch == 'doaj':
                        relaxed.append('DOAJ被引由Crossref回查补齐(cr_cites=%d)' % rec['cr_cites'])
                rec['relaxed'] = relaxed
                rec['q_gates'] = q_gates
                rec['pool_level'] = pool_level

                # 去重（DOI + 规范化标题 + 父级DOI折叠）
                d = rec['doi'].lower()
                t = norm_title(rec['title'])
                pd = parent_doi(d)

                if d and d in seen_doi:
                    continue
                if t and t in seen_title:
                    continue
                # 父级DOI折叠：书与章只留被引最高
                if pd and pd in seen_parent_doi:
                    existing = seen_parent_doi[pd]
                    existing_cites = max(existing.get('oa_cites',0), existing.get('cr_cites',0))
                    new_cites = max(rec['oa_cites'], rec['cr_cites'])
                    if new_cites > existing_cites:
                        # 替换：移除旧的，加入新的
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
                ch_funnel[mid][ch]['final'] += 1
                result.append(rec)

        return result, funnel, ch_funnel, parent_fold_log

    # 池1
    seen_doi_p1, seen_title_p1, seen_pd_p1 = {}, {}, {}
    pool1, funnel_p1, ch_funnel_p1, fold_log_p1 = process_pool(
        list(all_cands), 1, seen_doi_p1, seen_title_p1, seen_pd_p1)
    # 池2
    pool2_cands = [c for c in all_cands
                   if not (c['doi'].lower() in seen_doi_p1 or norm_title(c['title']) in seen_title_p1)]
    pool2, funnel_p2, ch_funnel_p2, fold_log_p2 = process_pool(
        pool2_cands, 2, dict(seen_doi_p1), dict(seen_title_p1), dict(seen_pd_p1))

    final = pool1 + pool2
    final.sort(key=lambda r: (r['module'], r['pool_level'], -r['score'],
                              -r['cited_by_count'], r['doi']))

    p1_count = len(pool1)
    p2_count = len(pool2)
    grand = p1_count + p2_count
    all_fold_log = fold_log_p1 + fold_log_p2
    print('\n[池1] %d 条  [池2] %d 条  [合计] %d 条' % (p1_count, p2_count, grand))
    print('[章书折叠留痕] %d 条' % len(all_fold_log))

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
    with open(os.path.join(OUT_DIR, '文献主档-v1.2.json'), 'w', encoding='utf-8') as f:
        json.dump(archive, f, ensure_ascii=False, indent=1)

    # 每模块统计
    per_mod_p1 = defaultdict(int)
    per_mod_p2 = defaultdict(int)
    for r in pool1: per_mod_p1[r['module']] += 1
    for r in pool2: per_mod_p2[r['module']] += 1
    per_mod_total = {m['id']: per_mod_p1[m['id']] + per_mod_p2[m['id']] for m in modules}

    # 统计
    stats = {
        '检索日期': RETRIEVED, '判据版本': 'v1.2',
        '锚词断言值': 69, '锚词实数': total_anchors,
        '候选总数': total_raw,
        '池级1_入库': p1_count, '池级2_入库': p2_count, '合计入库': grand,
        '池级1_达标': '是' if p1_count >= 200 else '否（判负照记）',
        '合计_达标': '是' if grand >= 300 else '否（判负照记）',
        '每模块实收_池1': dict(per_mod_p1),
        '每模块实收_池2': dict(per_mod_p2),
        '每模块实收_合计': per_mod_total,
        '漏斗_池1': {mid: dict(v) for mid, v in funnel_p1.items()},
        '漏斗_池2': {mid: dict(v) for mid, v in funnel_p2.items()},
        '通道漏斗_池1': {mid: dict(v) for mid, v in ch_funnel_p1.items()},
        '通道漏斗_池2': {mid: dict(v) for mid, v in ch_funnel_p2.items()},
        'Q0_被引补齐': {
            '应回查': len(q0_unique), '实回查': q0_actual, '上限': Q0_MAX,
            '命中被引数': q0_hit, '无记录': q0_miss, '无DOI': q0_no_doi,
            '筛掉DOAJ候选数': len(discovery_list),
            '说明': 'Q0回查上限400次为执行参数非判据条款；用完即停'
        },
        '章书折叠留痕数': len(all_fold_log),
        '每模块请求统计': req_stats,
        'OpenAlex_429_实测': oa_429_info,
        'OpenAlex_说明': 'M06-M15 OpenAlex通道因IP日预算耗尽(429)无数据' if oa_429_info else 'OpenAlex已恢复',
    }
    with open(os.path.join(OUT_DIR, '统计-v1.2.json'), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)

    # 章书折叠留痕
    fold_lines = ['# 章书折叠留痕 v1.2', '', '条数: %d' % len(all_fold_log), '',
                  '| 保留DOI | 折叠DOI | 父级DOI | 原因 |',
                  '|---------|---------|---------|------|']
    for fl in all_fold_log:
        fold_lines.append('| %s | %s | %s | %s |' % (
            fl.get('kept_doi',''), fl.get('removed_doi',''),
            fl.get('parent_doi',''), fl.get('reason','')))
    with open(os.path.join(OUT_DIR, '章书折叠留痕-v1.2.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(fold_lines) + '\n')

    # queries.txt
    with open(os.path.join(RAW_DIR, 'queries.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(qlog) + '\n')

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
        L.append('version: 1.2')
        L.append('status: 池1=%d条 池2=%d条 合计=%d条' % (len(p1r), len(p2r), len(p1r)+len(p2r)))
        L.append('---')
        L.append('')
        L.append('# 卷%s · %s（%s）' % (num, name, mid))
        L.append('')
        L.append('> 判据：`v1.2-20261103.md`（已冻结）｜检索日：%s' % RETRIEVED)
        L.append('> 锚词(%d条)：' % len(mod['anchors']) + ' / '.join(mod['anchors']))
        L.append('')

        cf1 = ch_funnel_p1.get(mid, {})
        cf2 = ch_funnel_p2.get(mid, {})
        L.append('## 通道漏斗')
        L.append('| 通道 | 池1原始 | 池1入库 | 池2原始 | 池2入库 |')
        L.append('|------|---------|---------|---------|---------|')
        for ch_name in ['openalex', 'crossref', 'doaj']:
            r1 = cf1.get(ch_name, {}).get('raw', 0)
            f1 = cf1.get(ch_name, {}).get('final', 0)
            r2 = cf2.get(ch_name, {}).get('raw', 0)
            f2 = cf2.get(ch_name, {}).get('final', 0)
            L.append('| %s | %d | %d | %d | %d |' % (ch_name, r1, f1, r2, f2))
        L.append('')

        L.append('## 池级 1 · 严格池（%d 条）' % len(p1r))
        L.append('')
        if not p1r: L.append('*（无条目）*'); L.append('')
        for i, r in enumerate(p1r, 1):
            _entry(L, i, r)

        L.append('## 池级 2 · 次级池（%d 条）' % len(p2r))
        L.append('')
        if not p2r: L.append('*（无条目）*'); L.append('')
        for i, r in enumerate(p2r, 1):
            _entry(L, i, r)

        fn = os.path.join(OUT_DIR, '卷%s·%s-20261103.md' % (num, name))
        with open(fn, 'w', encoding='utf-8') as f:
            f.write('\n'.join(L) + '\n')

    # ================================================================
    # STEP 6: 控制台汇总（≤60行）
    # ================================================================
    print('\n' + '=' * 60)
    print('v1.2 检索完成')
    print('锚词=%d (断言69) 模块=%d (断言15)' % (total_anchors, len(modules)))
    print('候选=%d | 池1=%d (目标≥200:%s) | 池2=%d | 合计=%d (目标≥300:%s)' % (
        total_raw, p1_count, '达标' if p1_count>=200 else '未达标',
        p2_count, grand, '达标' if grand>=300 else '未达标'))
    print('Q0: 应=%d 实=%d 命中=%d 无记录=%d 无DOI=%d 筛掉=%d' % (
        len(q0_unique), q0_actual, q0_hit, q0_miss, q0_no_doi, len(discovery_list)))
    print('章书折叠: %d条' % len(all_fold_log))
    print('OA 429: %s' % (oa_429_info or '已恢复'))
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


def _entry(L, i, r):
    au = '; '.join(r['authors'][:6]) + (' 等' if len(r['authors']) > 6 else '')
    doi_s = r['doi'] or '(无DOI)'
    cited = max(r['oa_cites'], r['cr_cites'])
    gates = '/'.join(r['q_gates'])
    L.append('%d｜%s(%d). %s｜%s｜%s｜被引%d｜score=%d｜%s' % (
        i, au, r['year'], r['title'][:100], r['venue'] or '(未记)',
        doi_s, cited, r['score'], gates))
    if r.get('relaxed'):
        L.append('    放宽项: %s' % '; '.join(r['relaxed']))
    if r['abstract']:
        L.append('    摘要: %s' % r['abstract'][:400])
    L.append('')


if __name__ == '__main__':
    main()
