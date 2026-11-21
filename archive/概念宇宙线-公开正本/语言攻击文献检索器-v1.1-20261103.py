#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言与思想攻击·文献检索器 v1.1（2026-11-03）
判据：语言与思想攻击·文献检索判据书-v1.1-20261103.md（已冻结）
通道：OpenAlex + Crossref(query.title) + DOAJ
双池：池级1=严格；池级2=Q降半档或摘要级强锚
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
UA = {'User-Agent': 'yunshao-langattack/1.1 (%s)' % REPO}

# ---------- 复用既有轮子 ----------
_tool_rel = os.path.join('archive','10-治理与哲学','04-工具与代码','控制权文献库检索器-v1.0-20261102.py')
_tool_path = os.path.join(REPO, _tool_rel)
_spec = importlib.util.spec_from_file_location('_ctrl', _tool_path)
_tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tool)
oa_abstract = _tool.oa_abstract
strip_tags = _tool.strip_tags
norm_title = _tool.norm_title

# ---------- 带 429 退避的 fetch（快速失败） ----------
def fetch_json(url, retries=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode('utf-8','replace')), None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                ra = e.headers.get('Retry-After','?')
                # 429 预算耗尽 → 短等后快速放弃，不浪费数小时
                wait = 5
                print('    429 Retry-After=%s, wait %ds then give up'%(ra,wait)); sys.stdout.flush()
                time.sleep(wait)
                return None, '429 rate limited (Retry-After=%s)'%ra
            elif e.code == 405:
                return None, 'HTTP 405 (check https vs http)'
            else:
                time.sleep(2)
        except Exception as e:
            time.sleep(2)
    return None, 'exhausted retries'

# ---------- 质量门阈值（v1.0 §三 冻结，v1.1 不改） ----------
def get_T(year):
    if year >= 2021: return 40
    if year >= 2016: return 90
    if year >= 2010: return 160
    if year >= 2000: return 250
    if year >= 1990: return 400
    return 600

ALLOWED_TYPES = {'journal-article','journal article','book','book-chapter','book chapter',
    'conference-paper','conference paper','review','preprint','proceedings-article'}

# ---------- R 门：语言/话语域词 ----------
DOMAIN_WORDS = ['language','linguistic','word','words','lexical','lexicon','vocabulary',
    'discourse','speech','speaking','tongue','naming','term','terminology',
    'semantic','semantics','pragmatics','rhetoric','meaning','concept','metaphor',
    'translation','narrative','dialect']

# ---------- N 门：跨域负面词 ----------
NEGATIVE_WORDS = ['dna','protein','amino acid','bacteria','antimicrobial','antibiotic',
    'insulin','diabetes','tumor','cancer','carcinoma','pcr','crispr','phylogenetic',
    'modeltest','partitionfinder','job shop','quadratic assignment','supply chain',
    'venture creation','customer loyalty','biomarker','surrogate endpoint','quantum',
    'internet of things','wetting','asset pricing','econometric','stock market',
    'pandemic patients','hospitalized','clinical characteristics','mortality']

# ---------- 白名单（v1.0 §五 冻结） ----------
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

# ====================================================================
# 锁定锚词表（69 条，逐字抄自 v1.1 §五 = v1.0 §六"锚词"列）
# ====================================================================
MODULES = [
    {'id':'M01','num':'一','name':'语言与思想的因果',
     'anchors':['linguistic relativity','sapir-whorf','linguistic determinism','language and thought'],
     'oa':['"linguistic relativity" OR "Sapir-Whorf" OR "linguistic determinism"',
           '"language and thought" AND (categories OR perception OR color)',
           'whorfian OR ("language" AND "worldview")'],
     'cr':['linguistic relativity','sapir-whorf'],
     'dj':['linguistic relativity','language and thought'],
     'rel':{'linguistic relativity':'语言相对论','sapir-whorf':'Sapir-Whorf假说',
            'linguistic determinism':'语言决定论','language and thought':'语言与思维'}},
    {'id':'M02','num':'二','name':'新话、双重话语与语言工程',
     'anchors':['newspeak','doublespeak','language engineering','political language'],
     'oa':['newspeak OR doublespeak','"political language" OR "language of politics"',
           'orwell AND (language OR propaganda OR truth)'],
     'cr':['political language','newspeak'],
     'dj':['political language','newspeak'],
     'rel':{'newspeak':'新话','doublespeak':'双重话语','language engineering':'语言工程',
            'political language':'政治语言'}},
    {'id':'M03','num':'三','name':'概念隐喻与政治框架',
     'anchors':['conceptual metaphor','framing','frame','metaphor AND politics'],
     'oa':['"conceptual metaphor" AND (politics OR political OR ideology)',
           '"framing" AND (media OR politics OR public opinion)',
           'metaphor AND (ideology OR political discourse)'],
     'cr':['conceptual metaphor','framing politics'],
     'dj':['conceptual metaphor','framing'],
     'rel':{'conceptual metaphor':'概念隐喻','framing':'框架效应','frame':'框架',
            'metaphor AND politics':'隐喻与政治'}},
    {'id':'M04','num':'四','name':'宣传、灌输与终止性套语',
     'anchors':['propaganda','indoctrination','brainwashing','totalitarian','thought-terminating'],
     'oa':['propaganda AND (language OR rhetoric OR persuasion)','indoctrination OR brainwashing',
           'totalitarian AND (language OR thought OR memory)',
           '"thought-terminating" OR "thought stopping"'],
     'cr':['propaganda language','thought-terminating'],
     'dj':['propaganda','indoctrination'],
     'rel':{'propaganda':'宣传','indoctrination':'灌输','brainwashing':'洗脑',
            'totalitarian':'极权','thought-terminating':'终止性套语'}},
    {'id':'M05','num':'五','name':'国家审查与自我审查',
     'anchors':['censorship','self-censorship','sensitive words','keyword filtering'],
     'oa':['censorship AND (china OR weibo OR chinese)','"self-censorship"',
           '"sensitive words" OR "keyword filtering"',
           'censorship AND (internet OR social media)'],
     'cr':['censorship self-censorship','sensitive words'],
     'dj':['censorship','self-censorship'],
     'rel':{'censorship':'审查','self-censorship':'自我审查','sensitive words':'敏感词',
            'keyword filtering':'关键词过滤'}},
    {'id':'M06','num':'六','name':'平台治理与内容审核',
     'anchors':['content moderation','platform governance','community standards','deplatforming'],
     'oa':['"content moderation"','"platform governance"',
           '"community standards" AND (speech OR moderation OR global)',
           'deplatforming OR "account suspension"'],
     'cr':['content moderation','deplatforming'],
     'dj':['content moderation','platform governance'],
     'rel':{'content moderation':'内容审核','platform governance':'平台治理',
            'community standards':'社区标准','deplatforming':'去平台化'}},
    {'id':'M07','num':'七','name':'算法规避与影子限制',
     'anchors':['algospeak','shadowban','algorithmic censorship','algorithmic suppression'],
     'oa':['algospeak OR "algorithmic avoidance"',
           'shadowban OR "shadow banning" OR "search hiding"',
           '"algorithmic censorship" OR "algorithmic suppression" OR "algorithmic gatekeeping"'],
     'cr':['algospeak','shadowban'],
     'dj':['algospeak','shadowban'],
     'rel':{'algospeak':'算法语','shadowban':'影子禁令',
            'algorithmic censorship':'算法审查','algorithmic suppression':'算法压制'}},
    {'id':'M08','num':'八','name':'谐音、禁忌与词汇替换',
     'anchors':['homophone','taboo','euphemism','dysphemism','substitution','avoidance'],
     'oa':['homophone AND (censorship OR internet OR chinese OR politeness)',
           'euphemism OR dysphemism',
           '"word taboo" OR "lexical taboo" OR "phonological taboo"',
           '"graphemic" OR "character substitution" OR "leet"'],
     'cr':['euphemism','homophone censorship'],
     'dj':['euphemism','taboo'],
     'rel':{'homophone':'谐音','taboo':'禁忌','euphemism':'委婉语','dysphemism':'贬损语',
            'substitution':'替换','avoidance':'回避'}},
    {'id':'M09','num':'九','name':'政治正确、辱称与语义漂移',
     'anchors':['political correctness','slur','hate speech','pejoration','semantic change'],
     'oa':['"political correctness" AND (language OR cognition OR attitude)',
           'slur OR pejorative',
           '"hate speech" AND (regulation OR moderation OR platform)',
           '"euphemism treadmill" OR "semantic bleaching" OR "pejoration"'],
     'cr':['political correctness','pejoration'],
     'dj':['political correctness','hate speech'],
     'rel':{'political correctness':'政治正确','slur':'辱称','hate speech':'仇恨言论',
            'pejoration':'贬义化','semantic change':'语义变化'}},
    {'id':'M10','num':'十','name':'语言意识形态、符号权力与守门',
     'anchors':['language ideology','symbolic power','linguistic capital','prescriptivism','gatekeeping'],
     'oa':['"language ideology"','"symbolic power" OR "linguistic capital" OR "linguistic market"',
           'prescriptivism OR "language policing" OR "language policy"',
           'gatekeeping AND (news OR communication OR science)'],
     'cr':['language ideology','prescriptivism'],
     'dj':['language ideology','prescriptivism'],
     'rel':{'language ideology':'语言意识形态','symbolic power':'符号权力',
            'linguistic capital':'语言资本','prescriptivism':'规范主义','gatekeeping':'守门'}},
    {'id':'M11','num':'十一','name':'沉默、寒蝉与舆论气候',
     'anchors':['chilling effect','spiral of silence','silence','climate of opinion'],
     'oa':['"chilling effect" AND (speech OR expression OR online OR communication)',
           '"spiral of silence"',
           '"self-censorship" AND (survey OR online OR social media)'],
     'cr':['chilling effect','spiral of silence'],
     'dj':['chilling effect','spiral of silence'],
     'rel':{'chilling effect':'寒蝉效应','spiral of silence':'沉默螺旋',
            'silence':'沉默','climate of opinion':'舆论气候'}},
    {'id':'M12','num':'十二','name':'讽刺、迷因与地下话语',
     'anchors':['satire','parody','meme','hidden transcript','infrapolitics'],
     'oa':['satire OR parody AND (politics OR authoritarian OR censorship)',
           'memes AND (resistance OR political OR subversive)',
           '"hidden transcript" OR infrapolitics OR "weapons of the weak"'],
     'cr':['satire politics','hidden transcript'],
     'dj':['satire','hidden transcript'],
     'rel':{'satire':'讽刺','parody':'戏仿','meme':'迷因',
            'hidden transcript':'隐藏文本','infrapolitics':'底层政治'}},
    {'id':'M13','num':'十三','name':'编码、隐写与规避书写',
     'anchors':['steganography','coded language','cryptography','samizdat','euphemistic code'],
     'oa':['"textual steganography" OR (steganography AND language)',
           '"coded language" OR "covert communication" AND (social media OR censorship)',
           'samizdat OR "underground publishing" OR "clandestine"'],
     'cr':['coded language','samizdat'],
     'dj':['steganography','coded language'],
     'rel':{'steganography':'隐写术','coded language':'编码语言','cryptography':'密码学',
            'samizdat':'地下出版','euphemistic code':'委婉编码'}},
    {'id':'M14','num':'十四','name':'语言剥夺与概念后果',
     'anchors':['language deprivation','affect labeling','emotion granularity','alexithymia','attrition'],
     'oa':['"language deprivation" OR "verbal deprivation"',
           '"affect labeling" OR "emotion labeling" OR "granularity"',
           'alexithymia AND (language OR emotion)',
           '"first language attrition" AND (concept OR cognition)'],
     'cr':['alexithymia','language deprivation'],
     'dj':['alexithymia','language deprivation'],
     'rel':{'language deprivation':'语言剥夺','affect labeling':'情感标注',
            'emotion granularity':'情绪颗粒度','alexithymia':'述情障碍','attrition':'磨蚀'}},
    {'id':'M15','num':'十五','name':'媒体效应与被说出的问题',
     'anchors':['agenda setting','priming','media effects','cultivation','knowledge gap'],
     'oa':['"agenda-setting" AND (media OR political)','priming AND (political OR media)',
           '"media effects" AND (public opinion OR attitude)',
           '"knowledge gap" OR "cultivation analysis"'],
     'cr':['agenda setting','media effects'],
     'dj':['agenda setting','media effects'],
     'rel':{'agenda setting':'议程设置','priming':'启动效应','media effects':'媒体效果',
            'cultivation':'涵化','knowledge gap':'知识沟'}},
]

# ====================================================================
# 锚词断言：必须恰好 69 条
# ====================================================================
ALL_ANCHORS = []
for m in MODULES:
    ALL_ANCHORS.extend(m['anchors'])
assert len(ALL_ANCHORS) == 69, '锚词数=%d，必须=69，中止运行'%len(ALL_ANCHORS)
# 分类：多词强锚 vs 单词锚
MULTI_WORD_ANCHORS = set()
SINGLE_WORD_ANCHORS = set()
for a in ALL_ANCHORS:
    if ' ' in a or '-' in a:
        MULTI_WORD_ANCHORS.add(a)
    else:
        SINGLE_WORD_ANCHORS.add(a)

# ====================================================================
# R 门 & N 门
# ====================================================================
def check_R_gate(title_low, matched_anchors):
    """R门：多词强锚标题命中即过；单词锚须与域词共现。"""
    title_norm = title_low.replace('-', ' ')
    has_multi = False
    has_single_with_domain = False
    for a in matched_anchors:
        if a in MULTI_WORD_ANCHORS:
            has_multi = True
        elif a in SINGLE_WORD_ANCHORS:
            if any(dw in title_norm for dw in DOMAIN_WORDS):
                has_single_with_domain = True
        # 特殊处理 "metaphor AND politics"
        if a == 'metaphor AND politics':
            if 'metaphor' in title_norm and 'politics' in title_norm:
                has_multi = True  # 视为多词强锚
    return has_multi or has_single_with_domain

def check_N_gate(title_low, matched_multi_count):
    """N门：标题含负面词即出局，除非命中≥2个多词强锚。"""
    if matched_multi_count >= 2:
        return True  # 豁免
    title_norm = title_low.replace('-', ' ')
    for nw in NEGATIVE_WORDS:
        if nw in title_norm:
            return False
    return True

def find_anchor_hits(title_low, abstract_low, anchors, title_only=True):
    """查找命中的锚词。title_only=True 只查标题；False 也查摘要。
    连字符/空格归一化：'agenda-setting' 可匹配 'agenda setting'。"""
    # 归一化：连字符→空格
    title_norm = title_low.replace('-', ' ')
    abstract_norm = abstract_low.replace('-', ' ')
    hits = []
    for a in anchors:
        a_norm = a.replace('-', ' ')
        if a == 'metaphor AND politics':
            if title_only:
                if 'metaphor' in title_norm and 'politics' in title_norm:
                    hits.append(a)
            else:
                combined = title_norm + ' ' + abstract_norm
                if 'metaphor' in combined and 'politics' in combined:
                    hits.append(a)
        else:
            if a_norm in title_norm:
                hits.append(a)
            elif not title_only and a_norm in abstract_norm:
                hits.append(a)
    return hits

def count_multi_word_hits(hits):
    return sum(1 for h in hits if h in MULTI_WORD_ANCHORS or h == 'metaphor AND politics')

# ====================================================================
# 数据解析
# ====================================================================
def parse_oa(w, mid, q, page):
    doi_raw = (w.get('doi') or '').replace('https://doi.org/','').strip()
    filt = urllib.parse.quote('title_and_abstract.search:%s'%q, safe='') + ',is_retracted:false'
    sel = 'doi,title,publication_year,cited_by_count,type,is_retracted,primary_location,abstract_inverted_index,authorships'
    url = 'https://api.openalex.org/works?filter=%s&sort=cited_by_count:desc&per-page=25&page=%d&select=%s'%(filt,page,sel)
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
                search_url=url)

def parse_cr(it, mid, q):
    doi = (it.get('DOI') or '').strip().lower()
    title = strip_tags((it.get('title') or [''])[0])
    yr = None
    for df in ('published','issued','published-print','published-online','created'):
        dp = it.get(df)
        if dp and dp.get('date-parts'):
            for part in dp['date-parts']:
                if isinstance(part, list) and part and isinstance(part[0], int) and part[0]>1000:
                    yr = part[0]; break
        if yr: break
    authors = []
    for a in (it.get('author') or []):
        nm = ', '.join([x for x in (a.get('family',''),a.get('given','')) if x]) or a.get('name','')
        if nm: authors.append(nm)
    ct = it.get('container-title') or []
    url = 'https://api.crossref.org/works?query.title=%s&rows=25&sort=is-referenced-by-count&order=desc'%(urllib.parse.quote(q))
    return dict(module=mid, channel='crossref', doi=doi, title=title,
                authors=authors, year=yr, venue=strip_tags(ct[0]) if ct else '',
                type=(it.get('type') or '').lower(),
                oa_cites=0, cr_cites=int(it.get('is-referenced-by-count') or 0),
                is_retracted=False, abstract=strip_tags(it.get('abstract','') or ''),
                search_url=url)

def parse_doaj(article, mid, q):
    bib = article.get('bibjson') or {}
    doi = (bib.get('doi') or article.get('doi') or '').strip().lower()
    title = strip_tags(bib.get('title') or article.get('title') or '')
    if isinstance(title, list): title = strip_tags(title[0]) if title else ''
    yr = None
    # bibjson.year or top-level dates
    for df in ('year', 'publication_date', 'created_date'):
        d = str(bib.get(df) or article.get(df) or '')
        if len(d) >= 4 and d[:4].isdigit():
            y = int(d[:4])
            if y > 1000: yr = y; break
    journal = bib.get('journal') or article.get('journal') or {}
    venue = strip_tags(journal.get('title','') or '')
    authors = [strip_tags(a.get('name','')) for a in (bib.get('author') or []) if a.get('name')]
    url = 'https://doaj.org/api/search/articles/%s'%urllib.parse.quote(q)
    return dict(module=mid, channel='doaj', doi=doi, title=title,
                authors=authors,
                year=yr, venue=venue, type='journal-article',
                oa_cites=0, cr_cites=0,
                is_retracted=False,
                abstract=strip_tags(bib.get('abstract','') or ''),
                search_url=url)

# ====================================================================
# 主流程
# ====================================================================
def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    print('锚词数=%d (断言=69)'%len(ALL_ANCHORS))
    print('多词强锚=%d, 单词锚=%d'%(len(MULTI_WORD_ANCHORS), len(SINGLE_WORD_ANCHORS)))

    req_stats = {m['id']: {'oa_new':0,'oa_cache':0,'oa_fail':0,'oa_429':0,
                            'cr_new':0,'cr_cache':0,'cr_fail':0,
                            'dj_new':0,'dj_cache':0,'dj_fail':0} for m in MODULES}
    qlog = []
    total_raw = 0
    all_cands = []
    oa_429_retry_after = None

    # ================================================================
    # STEP 1: 检索
    # ================================================================
    for mod in MODULES:
        mid = mod['id']
        rs = req_stats[mid]
        print('\n=== %s · %s ==='%(mid, mod['name']))

        # --- OpenAlex ---
        for qi, q in enumerate(mod['oa']):
            for page in range(1, 6):
                slug = '%s-oa-%02d-p%d'%(mid, qi+1, page)
                raw_path = os.path.join(RAW_DIR, slug+'.json')
                if os.path.exists(raw_path) and os.path.getsize(raw_path) > 100:
                    with open(raw_path, 'r', encoding='utf-8') as f:
                        obj = json.load(f)
                    works = obj.get('results',[]) or []
                    rs['oa_cache'] += 1
                    filt = urllib.parse.quote('title_and_abstract.search:%s'%q, safe='')+',is_retracted:false'
                    sel = 'doi,title,publication_year,cited_by_count,type,is_retracted,primary_location,abstract_inverted_index,authorships'
                    curl = 'https://api.openalex.org/works?filter=%s&sort=cited_by_count:desc&per-page=25&page=%d&select=%s'%(filt,page,sel)
                    qlog.append('%s|openalex|CACHED|%s'%(slug,curl))
                    if works:
                        total_raw += len(works)
                        for w in works: all_cands.append(parse_oa(w, mid, q, page))
                        if len(works) < 20: break
                        continue
                    else: break
                # 无缓存 → 尝试请求
                filt = urllib.parse.quote('title_and_abstract.search:%s'%q, safe='')+',is_retracted:false'
                sel = 'doi,title,publication_year,cited_by_count,type,is_retracted,primary_location,abstract_inverted_index,authorships'
                url = 'https://api.openalex.org/works?filter=%s&sort=cited_by_count:desc&per-page=25&page=%d&select=%s'%(filt,page,sel)
                qlog.append('%s|openalex|%s'%(slug,url))
                rs['oa_new'] += 1
                obj, err = fetch_json(url)
                if obj is None:
                    if err and '429' in str(err):
                        rs['oa_429'] += 1
                        # 提取 Retry-After from error string
                        import re as _re
                        _m = _re.search(r'Retry-After=(\d+)', str(err))
                        if _m:
                            oa_429_retry_after = _m.group(1)
                    else:
                        rs['oa_fail'] += 1
                    if page == 1: print('  %s [skip/fail] %s'%(slug, err))
                    break
                with open(raw_path, 'w', encoding='utf-8') as f:
                    json.dump(obj, f, ensure_ascii=False)
                works = obj.get('results',[]) or []
                if not works: break
                total_raw += len(works)
                for w in works: all_cands.append(parse_oa(w, mid, q, page))
                if len(works) < 20: break
                time.sleep(1.5)
            time.sleep(1.0)

        # --- Crossref (query.title) ---
        for qi, q in enumerate(mod['cr']):
            slug = '%s-cr-%02d'%(mid, qi+1)
            raw_path = os.path.join(RAW_DIR, slug+'.json')
            sel_cr = 'DOI,title,container-title,author,published,issued,created,is-referenced-by-count,abstract,type'
            url = 'https://api.crossref.org/works?query.title=%s&rows=25&sort=is-referenced-by-count&order=desc&select=%s'%(urllib.parse.quote(q),sel_cr)
            if os.path.exists(raw_path) and os.path.getsize(raw_path) > 100:
                with open(raw_path, 'r', encoding='utf-8') as f:
                    obj = json.load(f)
                items = (obj.get('message',{}) or {}).get('items',[]) or []
                rs['cr_cache'] += 1
                qlog.append('%s|crossref|CACHED|%s'%(slug,url))
                if items:
                    total_raw += len(items)
                    for it in items: all_cands.append(parse_cr(it, mid, q))
                    continue
            qlog.append('%s|crossref|%s'%(slug,url))
            rs['cr_new'] += 1
            obj, err = fetch_json(url)
            if obj is None:
                rs['cr_fail'] += 1; print('  %s FAIL %s'%(slug,err)); continue
            with open(raw_path, 'w', encoding='utf-8') as f:
                json.dump(obj, f, ensure_ascii=False)
            items = (obj.get('message',{}) or {}).get('items',[]) or []
            total_raw += len(items)
            for it in items: all_cands.append(parse_cr(it, mid, q))
            print('  %s got %d'%(slug, len(items)))
            time.sleep(1.0)

        # --- DOAJ ---
        for qi, q in enumerate(mod['dj']):
            slug = '%s-dj-%02d'%(mid, qi+1)
            raw_path = os.path.join(RAW_DIR, slug+'.json')
            url = 'https://doaj.org/api/search/articles/%s'%urllib.parse.quote(q)
            if os.path.exists(raw_path) and os.path.getsize(raw_path) > 100:
                with open(raw_path, 'r', encoding='utf-8') as f:
                    obj = json.load(f)
                results = obj.get('results',[]) or []
                rs['dj_cache'] += 1
                qlog.append('%s|doaj|CACHED|%s'%(slug,url))
                if results:
                    total_raw += len(results)
                    for art in results: all_cands.append(parse_doaj(art, mid, q))
                    continue
            qlog.append('%s|doaj|%s'%(slug,url))
            rs['dj_new'] += 1
            obj, err = fetch_json(url)
            if obj is None:
                rs['dj_fail'] += 1; print('  %s DOAJ FAIL %s'%(slug,err)); continue
            with open(raw_path, 'w', encoding='utf-8') as f:
                json.dump(obj, f, ensure_ascii=False)
            results = obj.get('results',[]) or []
            total_raw += len(results)
            for art in results: all_cands.append(parse_doaj(art, mid, q))
            print('  %s DOAJ got %d'%(slug, len(results)))
            time.sleep(1.0)

    # 保存 queries.txt
    with open(os.path.join(RAW_DIR, 'queries.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(qlog) + '\n')
    print('\n[检索完成] 原始=%d'%total_raw)

    # ================================================================
    # STEP 2: R门 → N门 → 硬底线 → Q门 → 打分 → 双池
    # ================================================================
    def process_pool(candidates, pool_level, seen_doi, seen_title):
        """处理一个池级的筛选。返回 (final_list, funnel_dict, audit_candidates)。"""
        mod_cands = defaultdict(list)
        for rec in candidates:
            mod_cands[rec['module']].append(rec)

        funnel = defaultdict(lambda: {'raw':0,'anchor':0,'R':0,'N':0,'hard':0,'Q':0,'score':0,'dedup':0,'final':0})
        result = []
        audit_list = []

        for mod in MODULES:
            mid = mod['id']
            cands = mod_cands.get(mid, [])
            f = funnel[mid]
            f['raw'] = len(cands)

            for rec in cands:
                title_low = (rec['title'] or '').lower()
                abstract_low = (rec['abstract'] or '').lower()

                # 锚词检查
                if pool_level == 1:
                    hits = find_anchor_hits(title_low, abstract_low, mod['anchors'], title_only=True)
                else:
                    hits = find_anchor_hits(title_low, abstract_low, mod['anchors'], title_only=False)
                if not hits:
                    continue
                f['anchor'] += 1
                rec['anchor_hits'] = hits

                # R 门
                if not check_R_gate(title_low, hits):
                    continue
                f['R'] += 1

                # N 门
                multi_count = count_multi_word_hits(hits)
                if not check_N_gate(title_low, multi_count):
                    audit_list.append(dict(DOI=rec['doi'], title=rec['title'][:80],
                                       reason='N门负面词命中', module=mid))
                    continue
                f['N'] += 1

                # 硬底线
                if not rec['doi']: continue
                if rec['is_retracted']: continue
                if rec['year'] is None or not (1900 <= rec['year'] <= 2026): continue
                tn = rec['type'].replace('-',' ').replace('_',' ').lower()
                if tn and tn not in ALLOWED_TYPES: continue
                f['hard'] += 1

                # Q 门
                T = get_T(rec['year'])
                q_gates = []
                if pool_level == 1:
                    if rec['oa_cites'] >= T: q_gates.append('Q1')
                    if rec['cr_cites'] >= int(0.6*T): q_gates.append('Q2')
                    mc = max(rec['oa_cites'], rec['cr_cites'])
                    if in_whitelist(rec['venue']) and mc >= int(0.25*T): q_gates.append('Q3')
                else:
                    if rec['oa_cites'] >= int(0.5*T): q_gates.append('Q1')
                    if rec['cr_cites'] >= int(0.3*T): q_gates.append('Q2')
                    mc = max(rec['oa_cites'], rec['cr_cites'])
                    if in_whitelist(rec['venue']) and mc >= int(0.15*T): q_gates.append('Q3')
                # DOAJ 无被引数 → 只能池级2 且标记放宽
                if rec['channel'] == 'doaj' and rec['oa_cites'] == 0 and rec['cr_cites'] == 0:
                    if pool_level == 1:
                        continue  # DOAJ无被引不过池1
                    # 池2: 标记放宽项
                if not q_gates:
                    continue
                f['Q'] += 1

                # 打分
                score = 0
                title_norm = title_low.replace('-', ' ')
                abstract_norm = abstract_low.replace('-', ' ')
                for a in mod['anchors']:
                    a_norm = a.replace('-', ' ')
                    if a == 'metaphor AND politics':
                        if 'metaphor' in title_norm and 'politics' in title_norm: score += 2
                        elif 'metaphor' in abstract_norm or 'politics' in abstract_norm: score += 1
                    else:
                        if a_norm in title_norm: score += 2
                        if a_norm in abstract_norm: score += 1
                if score < 1: continue
                f['score'] += 1
                rec['score'] = score

                # 摘要硬底线
                has_abs = bool(rec['abstract'] and rec['abstract'].strip())
                rec['level'] = '核' if has_abs else '待核'

                # 放宽项标记（池级2）
                relaxed = []
                if pool_level == 2:
                    title_hits = find_anchor_hits(title_low, '', mod['anchors'], title_only=True)
                    if not title_hits:
                        relaxed.append('强锚仅摘要命中')
                    if rec['oa_cites'] < T and rec['oa_cites'] >= int(0.5*T):
                        relaxed.append('Q1降半档(0.5×T)')
                    if rec['cr_cites'] < int(0.6*T) and rec['cr_cites'] >= int(0.3*T):
                        relaxed.append('Q2降半档(0.3×T)')
                    mc = max(rec['oa_cites'], rec['cr_cites'])
                    if mc < int(0.25*T) and mc >= int(0.15*T) and in_whitelist(rec['venue']):
                        relaxed.append('Q3降半档(0.15×T)')
                    if rec['channel'] == 'doaj' and mc == 0:
                        relaxed.append('DOAJ无被引数')
                rec['relaxed'] = relaxed

                # 关联注释
                notes = []
                for h in hits:
                    n = mod['rel'].get(h)
                    if n and n not in notes: notes.append(n)
                    if len(notes) >= 2: break
                rec['rel_note'] = '；'.join(notes) if notes else '外围对照·待人工判读'
                rec['q_gates'] = q_gates
                rec['pool_level'] = pool_level

                # 去重
                d = rec['doi'].lower(); t = norm_title(rec['title'])
                if d and d in seen_doi: continue
                if t and t in seen_title: continue
                if d: seen_doi[d] = mid
                if t: seen_title[t] = mid
                rec['cited_by_count'] = max(rec['oa_cites'], rec['cr_cites'])
                f['final'] += 1
                result.append(rec)

        return result, dict(funnel), audit_list

    # 池级1
    seen_doi_p1, seen_title_p1 = {}, {}
    pool1, funnel_p1, audit_p1 = process_pool(list(all_cands), 1, seen_doi_p1, seen_title_p1)
    # 池级2（排除池1已收录）
    pool2_cands = [c for c in all_cands
                   if not (c['doi'].lower() in seen_doi_p1 or norm_title(c['title']) in seen_title_p1)]
    pool2, funnel_p2, audit_p2 = process_pool(pool2_cands, 2, dict(seen_doi_p1), dict(seen_title_p1))

    final = pool1 + pool2
    final.sort(key=lambda r: (r['module'], r['pool_level'], -r['score'], -r['cited_by_count'], r['doi']))

    p1_count = len(pool1)
    p2_count = len(pool2)
    grand = p1_count + p2_count
    print('\n[池1] %d 条  [池2] %d 条  [合计] %d 条'%(p1_count, p2_count, grand))

    # ================================================================
    # STEP 3: 落盘
    # ================================================================
    # 文献主档
    archive = []
    for r in final:
        archive.append({
            '模块号':r['module'],'池级':r['pool_level'],'标题':r['title'],
            '作者':r['authors'],'年份':r['year'],'刊物':r['venue'],'DOI':r['doi'],
            'cited_by_count':r['oa_cites'],'is-referenced-by-count':r['cr_cites'],
            'type':r['type'],'score':r['score'],'质量门':r['q_gates'],
            '锚词命中':r['anchor_hits'],'核/待核':r['level'],'摘要':r['abstract'],
            '检索URL':r['search_url'],
            '放宽项':r.get('relaxed',[]),
        })
    with open(os.path.join(OUT_DIR,'文献主档-v1.1.json'),'w',encoding='utf-8') as f:
        json.dump(archive, f, ensure_ascii=False, indent=1)

    # 每模块统计
    per_mod_p1 = defaultdict(int)
    per_mod_p2 = defaultdict(int)
    for r in pool1: per_mod_p1[r['module']] += 1
    for r in pool2: per_mod_p2[r['module']] += 1
    per_mod_total = {m['id']: per_mod_p1[m['id']]+per_mod_p2[m['id']] for m in MODULES}

    # 统计
    wl_p1 = sum(1 for r in pool1 if in_whitelist(r['venue']))
    wl_p2 = sum(1 for r in pool2 if in_whitelist(r['venue']))
    pend_p1 = sum(1 for r in pool1 if r['level']=='待核')
    pend_p2 = sum(1 for r in pool2 if r['level']=='待核')

    stats = {
        '检索日期':RETRIEVED,'锚词断言值':69,'锚词实数':len(ALL_ANCHORS),
        '多词强锚数':len(MULTI_WORD_ANCHORS),'单词锚数':len(SINGLE_WORD_ANCHORS),
        '候选总数':total_raw,
        '池级1_入库':p1_count,'池级2_入库':p2_count,'合计入库':grand,
        '每模块实收_池1':dict(per_mod_p1),'每模块实收_池2':dict(per_mod_p2),
        '每模块实收_合计':per_mod_total,
        '每模块目标':{m['id']:24 for m in MODULES},
        '每模块缺口':{m['id']:max(0,24-per_mod_total[m['id']]) for m in MODULES},
        '池级1_达标':'是' if p1_count>=200 else '否（判负照记）',
        '合计_达标':'是' if grand>=300 else '否（判负照记）',
        '漏斗_池1':{mid:{k:v for k,v in funnel_p1[mid].items()} for mid in [m['id'] for m in MODULES]},
        '漏斗_池2':{mid:{k:v for k,v in funnel_p2[mid].items()} for mid in [m['id'] for m in MODULES]},
        '白名单命中_池1':wl_p1,'白名单命中_池2':wl_p2,
        '待核_池1':pend_p1,'待核_池2':pend_p2,
        '每模块请求统计':req_stats,
        'OpenAlex_429_Retry-After':oa_429_retry_after,
        'OpenAlex_429_说明':'M06-M15 OpenAlex通道因IP日预算耗尽(429)无数据，仅用Crossref+DOAJ',
        '请求数语义说明':'oa_new/cr_new/dj_new=本次新发起的HTTP请求数；oa_cache/cr_cache/dj_cache=从raw/加载的缓存页数；oa_fail/cr_fail/dj_fail=HTTP错误数',
        '审计剔除表条数':len(audit_p1)+len(audit_p2),
    }
    with open(os.path.join(OUT_DIR,'统计-v1.1.json'),'w',encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)

    # 卷文件
    cr_total = sum(1 for c in all_cands if c['channel']=='crossref')
    cr_in = sum(1 for r in final if r['channel']=='crossref')
    cr_rate = '%.1f%%'%(cr_in/cr_total*100) if cr_total else 'N/A'
    cr_note = ('> **Crossref 命中率**：`query.title` 按标题匹配，命中率 %s（%d/%d）。'
               'N 门负面词表已过滤跨域论文。\n'%(cr_rate, cr_in, cr_total))

    for mod in MODULES:
        mid = mod['id']
        p1r = [r for r in pool1 if r['module']==mid]
        p2r = [r for r in pool2 if r['module']==mid]
        L = []
        L.append('---')
        L.append('title: "语言与思想攻击文献库·卷%s·%s"'%(mod['num'],mod['name']))
        L.append('date: %s'%RETRIEVED); L.append('version: 1.1')
        L.append('status: 池1=%d条 池2=%d条 合计=%d条 目标24'%(len(p1r),len(p2r),len(p1r)+len(p2r)))
        L.append('---')
        L.append('')
        L.append('# 卷%s · %s（%s）'%(mod['num'],mod['name'],mid))
        L.append('')
        L.append('> 判据：`v1.1-20261103.md`（已冻结）｜检索日：%s｜锚词=%d条（锁死）'%(RETRIEVED,len(mod['anchors'])))
        L.append('> OpenAlex 式：')
        for q in mod['oa']: L.append('>   · `%s`'%q)
        L.append('> Crossref `query.title`：')
        for q in mod['cr']: L.append('>   · `%s`'%q)
        L.append('> DOAJ：')
        for q in mod['dj']: L.append('>   · `%s`'%q)
        L.append('> 池1 **%d** 条 / 池2 **%d** 条 / 合计 **%d** 条（缺 %d）'%(
            len(p1r),len(p2r),len(p1r)+len(p2r),max(0,24-len(p1r)-len(p2r))))
        L.append('')
        L.append(cr_note)
        L.append('## 池级 1 · 严格池（%d 条）'%len(p1r)); L.append('')
        if not p1r: L.append('*（无条目）*'); L.append('')
        for i,r in enumerate(p1r,1): _entry(L,i,r,mod)
        L.append('## 池级 2 · 次级池（%d 条）'%len(p2r)); L.append('')
        if not p2r: L.append('*（无条目）*'); L.append('')
        for i,r in enumerate(p2r,1): _entry(L,i,r,mod)
        fn = os.path.join(OUT_DIR,'卷%s·%s-20261103.md'%(mod['num'],mod['name']))
        with open(fn,'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')

    # 审计剔除表
    all_audit = audit_p1 + audit_p2
    audit_lines = ['# 审计剔除表 v1.1','','检索日：%s'%RETRIEVED,
                   '条数：%d'%len(all_audit),'',
                   '| DOI | 模块 | 标题 | 剔除理由 |',
                   '|-----|------|------|----------|']
    for a in all_audit:
        audit_lines.append('| %s | %s | %s | %s |'%(a['DOI'],a['module'],a['title'],a['reason']))
    with open(os.path.join(OUT_DIR,'审计剔除表-v1.1.md'),'w',encoding='utf-8') as f:
        f.write('\n'.join(audit_lines)+'\n')

    # 汇总
    print('\n'+'='*60)
    print('池1=%d (目标≥200: %s)'%(p1_count,'达标' if p1_count>=200 else '未达标'))
    print('池1+池2=%d (目标≥300: %s)'%(grand,'达标' if grand>=300 else '未达标'))
    for m in MODULES:
        mid=m['id']
        print('  %s: P1=%d P2=%d 合计=%d 缺=%d'%(mid,per_mod_p1[mid],per_mod_p2[mid],
              per_mod_total[mid],max(0,24-per_mod_total[mid])))
    print('审计剔除=%d'%len(all_audit))
    if oa_429_retry_after: print('OA 429 Retry-After=%s'%oa_429_retry_after)
    print('='*60)

    # 清理 __pycache__
    for d in [SCRIPT_DIR, os.path.dirname(_tool_path)]:
        c = os.path.join(d,'__pycache__')
        if os.path.isdir(c): shutil.rmtree(c)
    # 也清理 REPO 根的 __pycache__
    c = os.path.join(os.path.dirname(SCRIPT_DIR),'__pycache__')
    if os.path.isdir(c): shutil.rmtree(c)
    print('[已清理 __pycache__]')


def _entry(L, i, r, mod):
    au = '; '.join(r['authors'][:6]) + (' 等' if len(r['authors'])>6 else '')
    doi_s = r['doi'] or '(无DOI)'
    cited = max(r['oa_cites'], r['cr_cites'])
    gates = '/'.join(r['q_gates'])
    anch = ', '.join(r['anchor_hits'][:4])
    pool = '池%d'%r['pool_level']
    L.append('%d｜%s(%d).%s.%s — %s｜%s｜被引%d｜score=%d｜%s｜%s｜%s｜锚词[%s]｜%s'%(
        i, au, r['year'], r['title'], r['venue'] or '（载体未记）',
        doi_s, r['channel'], cited, r['score'], r['level'], gates, pool, anch, r['search_url']))
    if r.get('relaxed'):
        L.append('    放宽项：%s'%'; '.join(r['relaxed']))
    if r['abstract']:
        L.append('    摘要：%s'%r['abstract'][:500])
    L.append('    关联：%s'%r['rel_note'])
    L.append('')


if __name__ == '__main__':
    main()
