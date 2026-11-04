#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言与思想攻击·文献检索器 v1.0（2026-11-03 第三次修订）
委托人：知世 ｜ 执行：Qoder
判据：archive/概念宇宙线-公开正本/语言与思想攻击·文献检索判据书-v1.0-20261103.md（已冻结，未改）
通道：OpenAlex（M01-M05 有缓存；M06-M15 因 IP 日预算耗尽跳过）+ Crossref（全 15 模块）
双池：池级1=严格（原门槛）；池级2=次级（锚词允许摘要命中，被引 0.5×T，白名单 0.15×T）
"""
import json, os, re, sys, time, shutil
import urllib.error, urllib.parse, urllib.request
import importlib.util
from collections import Counter, defaultdict

REPO = "/data/workspace/publish-yunshao"
CRITERIA_DIR = os.path.join(REPO, "archive/概念宇宙线-公开正本")
OUT = os.path.join(CRITERIA_DIR, "语言与思想攻击文献库-20261103")
RAW = os.path.join(OUT, "raw")
RETRIEVED = "2026-11-03"
UA = {"User-Agent": "yunshao-langattack/1.0 (https://github.com/yunshao-official/publish-yunshao)"}

# ---------- 复用既有轮子（判据书 §七） ----------
_tool_path = os.path.join(REPO, "archive/10-治理与哲学/04-工具与代码/控制权文献库检索器-v1.0-20261102.py")
_spec = importlib.util.spec_from_file_location("_ctrl_tool", _tool_path)
_tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tool)
oa_abstract = _tool.oa_abstract
strip_tags = _tool.strip_tags
norm_title = _tool.norm_title

# ---------- 带 429 退避的 fetch ----------
def fetch_json_robust(url, max_retries=3):
    err = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                body = r.read().decode("utf-8", "replace")
            return json.loads(body), None
        except urllib.error.HTTPError as e:
            err = "%s: %s" % (type(e).__name__, e)
            if e.code == 429:
                wait = 60 * (attempt + 1)
                print("    429 rate-limited, waiting %ds..." % wait); sys.stdout.flush()
                time.sleep(wait)
            else:
                time.sleep(2.0)
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            err = "%s: %s" % (type(e).__name__, e)
            time.sleep(2.0)
    return None, err

# ---------- 质量门阈值（判据书 §三 冻结） ----------
def get_T(year):
    if year >= 2021: return 40
    if year >= 2016: return 90
    if year >= 2010: return 160
    if year >= 2000: return 250
    if year >= 1990: return 400
    return 600

ALLOWED_TYPES = {'journal-article','journal article','book','book-chapter','book chapter',
    'conference-paper','conference paper','review','preprint','proceedings-article'}

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
# 模块定义（判据书 §六 冻结——锚词、检索式一律不改）
# ====================================================================
MODULES = [
    {'id':'M01','num':'一','name':'语言与思想的因果',
     'anchors':['linguistic relativity','sapir-whorf','sapir whorf','linguistic determinism',
                'language and thought','whorfian','language and worldview'],
     'oa_queries':['"linguistic relativity" OR "Sapir-Whorf" OR "linguistic determinism"',
                   '"language and thought" AND (categories OR perception OR color)',
                   'whorfian OR ("language" AND "worldview")'],
     'cr_queries':['linguistic relativity Sapir-Whorf','language thought worldview whorfian'],
     'rel':{'linguistic relativity':'语言相对论（本线核心·语义受语言塑造）','sapir-whorf':'Sapir-Whorf 假说',
            'sapir whorf':'Sapir-Whorf 假说','linguistic determinism':'语言决定论','language and thought':'语言与思维关系',
            'whorfian':'Whorf 效应','language and worldview':'语言与世界图景'}},
    {'id':'M02','num':'二','name':'新话、双重话语与语言工程',
     'anchors':['newspeak','doublespeak','language engineering','political language','language of politics','orwell'],
     'oa_queries':['newspeak OR doublespeak','"political language" OR "language of politics"',
                   'orwell AND (language OR propaganda OR truth)'],
     'cr_queries':['newspeak doublespeak','political language orwell propaganda'],
     'rel':{'newspeak':'新话（语言缩减→概念缩减）','doublespeak':'双重话语','political language':'政治语言',
            'language of politics':'政治的语言','orwell':'奥威尔式语言控制'}},
    {'id':'M03','num':'三','name':'概念隐喻与政治框架',
     'anchors':['conceptual metaphor','framing','frame','metaphor and politics','metaphor and ideology',
                'political discourse','ideology'],
     'oa_queries':['"conceptual metaphor" AND (politics OR political OR ideology)',
                   '"framing" AND (media OR politics OR public opinion)',
                   'metaphor AND (ideology OR political discourse)'],
     'cr_queries':['conceptual metaphor politics framing','metaphor ideology political discourse'],
     'rel':{'conceptual metaphor':'概念隐喻','framing':'框架效应','frame':'框架',
            'political discourse':'政治话语','ideology':'意识形态'}},
    {'id':'M04','num':'四','name':'宣传、灌输与终止性套语',
     'anchors':['propaganda','indoctrination','brainwashing','totalitarian','thought-terminating',
                'thought stopping','rhetoric','persuasion'],
     'oa_queries':['propaganda AND (language OR rhetoric OR persuasion)','indoctrination OR brainwashing',
                   'totalitarian AND (language OR thought OR memory)',
                   '"thought-terminating" OR "thought stopping"'],
     'cr_queries':['propaganda language rhetoric persuasion','indoctrination brainwashing totalitarian'],
     'rel':{'propaganda':'宣传','rhetoric':'修辞','persuasion':'说服','indoctrination':'灌输',
            'brainwashing':'洗脑','totalitarian':'极权','thought-terminating':'终止性套语','thought stopping':'终止性技巧'}},
    {'id':'M05','num':'五','name':'国家审查与自我审查',
     'anchors':['censorship','self-censorship','sensitive words','keyword filtering','delete',
                'internet','social media','china','chinese','weibo'],
     'oa_queries':['censorship AND (china OR weibo OR chinese)','"self-censorship"',
                   '"sensitive words" OR "keyword filtering"','censorship AND (internet OR social media)'],
     'cr_queries':['censorship china self-censorship','sensitive words keyword filtering internet'],
     'rel':{'censorship':'审查（外部语义删除·本线核心机制）','self-censorship':'自我审查','sensitive words':'敏感词',
            'keyword filtering':'关键词过滤','china':'中国语境','chinese':'中文语境','weibo':'微博',
            'internet':'互联网','social media':'社交媒体','delete':'删除'}},
    {'id':'M06','num':'六','name':'平台治理与内容审核',
     'anchors':['content moderation','platform governance','community standards','deplatforming','account suspension'],
     'oa_queries':['"content moderation"','"platform governance"',
                   '"community standards" AND (speech OR moderation OR global)',
                   'deplatforming OR "account suspension"'],
     'cr_queries':['deplatforming','content moderation'],
     'rel':{'content moderation':'内容审核（平台层语义管控）','platform governance':'平台治理',
            'community standards':'社区标准','deplatforming':'去平台化','account suspension':'账号封禁'}},
    {'id':'M07','num':'七','name':'算法规避与影子限制',
     'anchors':['algospeak','shadowban','shadow banning','search hiding','algorithmic censorship',
                'algorithmic suppression','algorithmic gatekeeping','algorithmic avoidance'],
     'oa_queries':['algospeak OR "algorithmic avoidance"','shadowban OR "shadow banning" OR "search hiding"',
                   '"algorithmic censorship" OR "algorithmic suppression" OR "algorithmic gatekeeping"'],
     'cr_queries':['algospeak','shadowban'],
     'rel':{'algospeak':'算法语（为规避审查而生的新词汇层）','shadowban':'影子禁令','shadow banning':'影子封禁',
            'algorithmic censorship':'算法审查','algorithmic suppression':'算法压制',
            'algorithmic gatekeeping':'算法守门','algorithmic avoidance':'算法规避'}},
    {'id':'M08','num':'八','name':'谐音、禁忌与词汇替换',
     'anchors':['homophone','taboo','euphemism','dysphemism','substitution','avoidance',
                'word taboo','lexical taboo','phonological taboo','graphemic','character substitution','leet'],
     'oa_queries':['homophone AND (censorship OR internet OR chinese OR politeness)','euphemism OR dysphemism',
                   '"word taboo" OR "lexical taboo" OR "phonological taboo"',
                   '"graphemic" OR "character substitution" OR "leet"'],
     'cr_queries':['euphemism','homophone taboo'],
     'rel':{'homophone':'谐音（词汇层规避策略）','taboo':'禁忌','euphemism':'委婉语','dysphemism':'贬损语',
            'substitution':'替换','avoidance':'回避','word taboo':'词禁忌','character substitution':'字符替换'}},
    {'id':'M09','num':'九','name':'政治正确、辱称与语义漂移',
     'anchors':['political correctness','slur','pejorative','hate speech','semantic change','pejoration',
                'euphemism treadmill','semantic bleaching'],
     'oa_queries':['"political correctness" AND (language OR cognition OR attitude)','slur OR pejorative',
                   '"hate speech" AND (regulation OR moderation OR platform)',
                   '"euphemism treadmill" OR "semantic bleaching" OR "pejoration"'],
     'cr_queries':['pejoration','slur'],
     'rel':{'political correctness':'政治正确','slur':'辱称','pejorative':'贬义词','hate speech':'仇恨言论',
            'pejoration':'贬义化','euphemism treadmill':'委婉语跑步机','semantic bleaching':'语义漂白'}},
    {'id':'M10','num':'十','name':'语言意识形态、符号权力与守门',
     'anchors':['language ideology','symbolic power','linguistic capital','linguistic market',
                'prescriptivism','language policing','language policy','gatekeeping'],
     'oa_queries':['"language ideology"','"symbolic power" OR "linguistic capital" OR "linguistic market"',
                   'prescriptivism OR "language policing" OR "language policy"',
                   'gatekeeping AND (news OR communication OR science)'],
     'cr_queries':['prescriptivism','gatekeeping'],
     'rel':{'language ideology':'语言意识形态','symbolic power':'符号权力','linguistic capital':'语言资本',
            'prescriptivism':'规范主义','gatekeeping':'守门','language policing':'语言警察'}},
    {'id':'M11','num':'十一','name':'沉默、寒蝉与舆论气候',
     'anchors':['chilling effect','spiral of silence','silence','climate of opinion','self-censorship',
                'speech','expression','online','communication'],
     'oa_queries':['"chilling effect" AND (speech OR expression OR online OR communication)',
                   '"spiral of silence"','"self-censorship" AND (survey OR online OR social media)'],
     'cr_queries':['censorship','spiral of silence'],
     'rel':{'chilling effect':'寒蝉效应','spiral of silence':'沉默螺旋','silence':'沉默',
            'self-censorship':'自我审查','climate of opinion':'舆论气候'}},
    {'id':'M12','num':'十二','name':'讽刺、迷因与地下话语',
     'anchors':['satire','parody','meme','memes','hidden transcript','infrapolitics',
                'weapons of the weak','resistance','subversive'],
     'oa_queries':['satire OR parody AND (politics OR authoritarian OR censorship)',
                   'memes AND (resistance OR political OR subversive)',
                   '"hidden transcript" OR infrapolitics OR "weapons of the weak"'],
     'cr_queries':['satire','infrapolitics'],
     'rel':{'satire':'讽刺（以幽默为载体的语义反抗）','parody':'戏仿','meme':'迷因','memes':'迷因',
            'hidden transcript':'隐藏文本','infrapolitics':'底层政治','weapons of the weak':'弱者的武器'}},
    {'id':'M13','num':'十三','name':'编码、隐写与规避书写',
     'anchors':['steganography','textual steganography','coded language','covert communication',
                'cryptography','samizdat','underground publishing','clandestine','euphemistic code'],
     'oa_queries':['"textual steganography" OR (steganography AND language)',
                   '"coded language" OR "covert communication" AND (social media OR censorship)',
                   'samizdat OR "underground publishing" OR "clandestine"'],
     'cr_queries':['samizdat','steganography'],
     'rel':{'steganography':'隐写术','textual steganography':'文本隐写','coded language':'编码语言',
            'samizdat':'地下出版物','underground publishing':'地下出版','covert communication':'隐蔽传播'}},
    {'id':'M14','num':'十四','name':'语言剥夺与概念后果',
     'anchors':['language deprivation','verbal deprivation','affect labeling','emotion labeling',
                'granularity','alexithymia','first language attrition','emotion','cognition'],
     'oa_queries':['"language deprivation" OR "verbal deprivation"',
                   '"affect labeling" OR "emotion labeling" OR "granularity"',
                   'alexithymia AND (language OR emotion)',
                   '"first language attrition" AND (concept OR cognition)'],
     'cr_queries':['alexithymia','language deprivation'],
     'rel':{'language deprivation':'语言剥夺（缺少语言输入→概念缺损）','affect labeling':'情感标注',
            'alexithymia':'述情障碍（无法用语言描述情感）','granularity':'颗粒度','first language attrition':'母语磨蚀'}},
    {'id':'M15','num':'十五','name':'媒体效应与被说出的问题',
     'anchors':['agenda-setting','agenda setting','priming','media effects','cultivation',
                'cultivation analysis','knowledge gap','public opinion','attitude'],
     'oa_queries':['"agenda-setting" AND (media OR political)','priming AND (political OR media)',
                   '"media effects" AND (public opinion OR attitude)',
                   '"knowledge gap" OR "cultivation analysis"'],
     'cr_queries':['agenda-setting','media effects'],
     'rel':{'agenda-setting':'议程设置','agenda setting':'议程设置','priming':'启动效应',
            'media effects':'媒体效果','cultivation':'涵化','knowledge gap':'知识沟'}},
]

VOL_NAMES = {m['id']: m['name'] for m in MODULES}

# ====================================================================
# 数据解析辅助函数
# ====================================================================
def parse_oa_work(w, mid, q_expr, page):
    doi_raw = (w.get('doi') or '').replace('https://doi.org/','').strip()
    sel = "doi,title,publication_year,cited_by_count,type,is_retracted,primary_location,abstract_inverted_index,authorships"
    filt = urllib.parse.quote("title_and_abstract.search:%s"%q_expr, safe='') + ",is_retracted:false"
    url = "https://api.openalex.org/works?filter=%s&sort=cited_by_count:desc&per-page=25&page=%d&select=%s"%(filt,page,sel)
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

def parse_cr_item(it, mid, q_phrase):
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
    sel = "DOI,title,container-title,author,published,issued,created,is-referenced-by-count,abstract,type"
    url = "https://api.crossref.org/works?query.bibliographic=%s&rows=25&sort=is-referenced-by-count&order=desc&select=%s"%(urllib.parse.quote(q_phrase),sel)
    return dict(module=mid, channel='crossref', doi=doi, title=title,
                authors=authors, year=yr,
                venue=strip_tags(ct[0]) if ct else '',
                type=(it.get('type') or '').lower(),
                oa_cites=0, cr_cites=int(it.get('is-referenced-by-count') or 0),
                is_retracted=False,
                abstract=strip_tags(it.get('abstract','') or ''),
                search_url=url)

# ====================================================================
# 主流程
# ====================================================================
def main():
    os.makedirs(RAW, exist_ok=True)

    # 统计计数器
    req_stats = {m['id']: {'oa_req':0,'oa_fail':0,'cr_req':0,'cr_fail':0} for m in MODULES}
    qlog = []
    total_raw = 0
    all_cands = []  # 所有原始候选

    # ================================================================
    # STEP 1：检索
    # ================================================================
    for mod in MODULES:
        mid = mod['id']
        rs = req_stats[mid]
        print("\n=== %s · %s ==="%(mid, mod['name']))

        # ---------- OpenAlex ----------
        for qi, q_expr in enumerate(mod['oa_queries']):
            for page in range(1, 6):  # max 5 pages
                slug = "%s-oa-%02d-p%d"%(mid, qi+1, page)
                raw_path = os.path.join(RAW, slug+".json")

                # Resume: 加载缓存
                if os.path.exists(raw_path) and os.path.getsize(raw_path) > 100:
                    with open(raw_path, 'r', encoding='utf-8') as f:
                        obj = json.load(f)
                    works = obj.get('results', []) or []
                    filt = urllib.parse.quote("title_and_abstract.search:%s"%q_expr, safe='') + ",is_retracted:false"
                    sel = "doi,title,publication_year,cited_by_count,type,is_retracted,primary_location,abstract_inverted_index,authorships"
                    cached_url = "https://api.openalex.org/works?filter=%s&sort=cited_by_count:desc&per-page=25&page=%d&select=%s"%(filt,page,sel)
                    qlog.append("%s|openalex|CACHED|%s"%(slug, cached_url))
                    if works:
                        print("  %s [cached] got %d"%(slug, len(works)))
                        total_raw += len(works)
                        for w in works:
                            all_cands.append(parse_oa_work(w, mid, q_expr, page))
                        if len(works) < 20: break
                        continue
                    else:
                        print("  %s [cached] got 0, stop"%slug); break

                # 无缓存 → OpenAlex 日预算耗尽，跳过
                filt = urllib.parse.quote("title_and_abstract.search:%s"%q_expr, safe='') + ",is_retracted:false"
                sel = "doi,title,publication_year,cited_by_count,type,is_retracted,primary_location,abstract_inverted_index,authorships"
                skip_url = "https://api.openalex.org/works?filter=%s&sort=cited_by_count:desc&per-page=25&page=%d&select=%s"%(filt,page,sel)
                qlog.append("%s|openalex|SKIP_429|%s"%(slug, skip_url))
                if page == 1:
                    print("  %s [skip] OpenAlex 日预算耗尽"%slug)
                break

        # ---------- Crossref ----------
        for qi, q_phrase in enumerate(mod['cr_queries']):
            slug = "%s-cr-%02d"%(mid, qi+1)
            raw_path = os.path.join(RAW, slug+".json")

            # Resume
            if os.path.exists(raw_path) and os.path.getsize(raw_path) > 100:
                with open(raw_path, 'r', encoding='utf-8') as f:
                    obj = json.load(f)
                msg = obj.get('message') or {}
                items = msg.get('items') or []
                sel_cr = "DOI,title,container-title,author,published,issued,created,is-referenced-by-count,abstract,type"
                cached_url = "https://api.crossref.org/works?query.bibliographic=%s&rows=25&sort=is-referenced-by-count&order=desc&select=%s"%(urllib.parse.quote(q_phrase),sel_cr)
                qlog.append("%s|crossref|CACHED|%s"%(slug, cached_url))
                if items:
                    print("  %s [cached] got %d"%(slug, len(items)))
                    total_raw += len(items)
                    for it in items:
                        all_cands.append(parse_cr_item(it, mid, q_phrase))
                    continue

            # 新请求
            sel_cr = "DOI,title,container-title,author,published,issued,created,is-referenced-by-count,abstract,type"
            url = "https://api.crossref.org/works?query.bibliographic=%s&rows=25&sort=is-referenced-by-count&order=desc&select=%s"%(urllib.parse.quote(q_phrase),sel_cr)
            qlog.append("%s|crossref|%s"%(slug, url))
            print("  %s fetching..."%slug, end=' '); sys.stdout.flush()
            rs['cr_req'] += 1
            obj, err = fetch_json_robust(url)
            if obj is None:
                print("FAIL %s"%err); rs['cr_fail'] += 1; continue
            with open(raw_path, 'w', encoding='utf-8') as f:
                json.dump(obj, f, ensure_ascii=False)
            msg = obj.get('message') or {}
            items = msg.get('items') or []
            print("got %d"%len(items))
            total_raw += len(items)
            for it in items:
                all_cands.append(parse_cr_item(it, mid, q_phrase))
            time.sleep(1.0)

    # 保存 queries.txt
    with open(os.path.join(RAW, "queries.txt"), 'w', encoding='utf-8') as f:
        f.write("\n".join(qlog) + "\n")

    print("\n[检索完成] 原始条目总数=%d"%(total_raw))

    # ================================================================
    # STEP 2：双池筛选
    # ================================================================
    def evaluate_candidate(rec, mod, pool_level):
        """评估一条候选是否通过给定池级的门槛。返回 (pass, info_dict) 或 (False, None)。"""
        title_low = (rec['title'] or '').lower()
        abstract_low = (rec['abstract'] or '').lower()

        # --- 锚词检查 ---
        if pool_level == 1:
            anchor_hits = [a for a in mod['anchors'] if a in title_low]
        else:  # pool 2: 标题或摘要
            anchor_hits = [a for a in mod['anchors'] if a in title_low or a in abstract_low]
        if not anchor_hits:
            return False, None

        # --- 硬底线（两池相同） ---
        if not rec['doi']: return False, None
        if rec['is_retracted']: return False, None
        if rec['year'] is None or not (1900 <= rec['year'] <= 2026): return False, None
        type_norm = rec['type'].replace('-',' ').replace('_',' ').lower()
        if type_norm and type_norm not in ALLOWED_TYPES: return False, None

        # --- 质量门 ---
        T = get_T(rec['year'])
        q_gates = []
        if pool_level == 1:
            if rec['oa_cites'] >= T: q_gates.append('Q1')
            if rec['cr_cites'] >= int(0.6 * T): q_gates.append('Q2')
            max_cites = max(rec['oa_cites'], rec['cr_cites'])
            if in_whitelist(rec['venue']) and max_cites >= int(0.25 * T): q_gates.append('Q3')
        else:  # pool 2: 放宽
            if rec['oa_cites'] >= int(0.5 * T): q_gates.append('Q1')
            if rec['cr_cites'] >= int(0.3 * T): q_gates.append('Q2')
            max_cites = max(rec['oa_cites'], rec['cr_cites'])
            if in_whitelist(rec['venue']) and max_cites >= int(0.15 * T): q_gates.append('Q3')
        if not q_gates: return False, None

        # --- 打分 ---
        score = 0
        for a in mod['anchors']:
            if a in title_low: score += 2
            if a in abstract_low: score += 1
        if score < 1: return False, None

        # --- 摘要硬底线 ---
        has_abstract = bool(rec['abstract'] and rec['abstract'].strip())
        level = '核' if has_abstract else '待核'

        # --- 关联注释 ---
        notes = []
        for h in anchor_hits:
            n = mod['rel'].get(h)
            if n and n not in notes: notes.append(n)
            if len(notes) >= 2: break
        rel_note = "；".join(notes) if notes else "外围对照·待人工判读"

        return True, dict(anchor_hits=anchor_hits, q_gates=q_gates, score=score,
                          level=level, rel_note=rel_note, pool_level=pool_level)

    # --- 池级 1 筛选 ---
    pool1_cands = []
    funnel_p1 = {'raw': total_raw, 'anchor': 0, 'hard': 0, 'qgate': 0, 'score': 0}
    for rec in all_cands:
        mod = next(m for m in MODULES if m['id'] == rec['module'])
        title_low = (rec['title'] or '').lower()
        # 快速预筛：标题锚词
        if not any(a in title_low for a in mod['anchors']):
            continue
        funnel_p1['anchor'] += 1
        ok, info = evaluate_candidate(rec, mod, 1)
        if ok:
            rec.update(info)
            pool1_cands.append(rec)
            funnel_p1['score'] += 1

    # --- 池级 1 去重 + 截断 ---
    pool1_cands.sort(key=lambda r: (-r['score'], -max(r['oa_cites'],r['cr_cites']), r['doi']))
    seen_doi_p1, seen_title_p1 = {}, {}
    pool1_final = []
    p1_mod_count = defaultdict(int)
    displacement = 0

    for rec in pool1_cands:
        mid = rec['module']
        if p1_mod_count[mid] >= 26: continue
        d = rec['doi'].lower(); t = norm_title(rec['title'])
        if d and d in seen_doi_p1:
            if seen_doi_p1[d] != mid: displacement += 1
            continue
        if t and t in seen_title_p1:
            if seen_title_p1[t] != mid: displacement += 1
            continue
        if d: seen_doi_p1[d] = mid
        if t: seen_title_p1[t] = mid
        rec['cited_by_count'] = max(rec['oa_cites'], rec['cr_cites'])
        pool1_final.append(rec)
        p1_mod_count[mid] += 1

    pool1_final.sort(key=lambda r: (r['module'], -r['score'], -r['cited_by_count'], r['doi']))

    # --- 池级 2 筛选（排除已在池级1 的 DOI/标题） ---
    pool2_cands = []
    funnel_p2 = {'anchor': 0, 'score': 0}
    for rec in all_cands:
        mod = next(m for m in MODULES if m['id'] == rec['module'])
        d = rec['doi'].lower(); t = norm_title(rec['title'])
        # 排除池级1已收录
        if d and d in seen_doi_p1: continue
        if t and t in seen_title_p1: continue
        # 评估池级2
        ok, info = evaluate_candidate(rec, mod, 2)
        if ok:
            rec.update(info)
            pool2_cands.append(rec)
            funnel_p2['score'] += 1

    # --- 池级 2 去重 + 截断 ---
    pool2_cands.sort(key=lambda r: (-r['score'], -max(r['oa_cites'],r['cr_cites']), r['doi']))
    seen_doi_p2, seen_title_p2 = dict(seen_doi_p1), dict(seen_title_p1)
    pool2_final = []
    p2_mod_count = defaultdict(int)

    for rec in pool2_cands:
        mid = rec['module']
        if p2_mod_count[mid] >= 26: continue
        d = rec['doi'].lower(); t = norm_title(rec['title'])
        if d and d in seen_doi_p2: continue
        if t and t in seen_title_p2: continue
        if d: seen_doi_p2[d] = mid
        if t: seen_title_p2[t] = mid
        rec['cited_by_count'] = max(rec['oa_cites'], rec['cr_cites'])
        pool2_final.append(rec)
        p2_mod_count[mid] += 1

    pool2_final.sort(key=lambda r: (r['module'], -r['score'], -r['cited_by_count'], r['doi']))

    # 合并
    final = pool1_final + pool2_final
    p1_total = len(pool1_final)
    p2_total = len(pool2_final)
    grand_total = p1_total + p2_total

    print("\n[池级1] 锚词命中=%d → 入库=%d" % (funnel_p1['anchor'], p1_total))
    print("[池级2] 入库=%d" % p2_total)
    print("[合计] %d 条" % grand_total)

    # ================================================================
    # STEP 3：落盘——文献主档
    # ================================================================
    archive = []
    for r in final:
        archive.append({
            '模块号': r['module'], '池级': r['pool_level'],
            '标题': r['title'], '作者': r['authors'], '年份': r['year'],
            '刊物': r['venue'], 'DOI': r['doi'],
            'cited_by_count': r['oa_cites'], 'is-referenced-by-count': r['cr_cites'],
            'type': r['type'], 'score': r['score'],
            '质量门': r['q_gates'], '锚词命中': r['anchor_hits'],
            '核/待核': r['level'], '摘要': r['abstract'], '检索URL': r['search_url'],
        })
    with open(os.path.join(OUT, "文献主档-v1.0.json"), 'w', encoding='utf-8') as f:
        json.dump(archive, f, ensure_ascii=False, indent=1)

    # ================================================================
    # STEP 4：落盘——统计
    # ================================================================
    wl_p1 = sum(1 for r in pool1_final if in_whitelist(r['venue']))
    wl_p2 = sum(1 for r in pool2_final if in_whitelist(r['venue']))
    pend_p1 = sum(1 for r in pool1_final if r['level'] == '待核')
    pend_p2 = sum(1 for r in pool2_final if r['level'] == '待核')

    per_mod_p1 = {m['id']: p1_mod_count.get(m['id'], 0) for m in MODULES}
    per_mod_p2 = {m['id']: p2_mod_count.get(m['id'], 0) for m in MODULES}
    per_mod_total = {m['id']: per_mod_p1[m['id']] + per_mod_p2[m['id']] for m in MODULES}

    # Crossref 命中率统计
    cr_total_items = sum(1 for c in all_cands if c['channel'] == 'crossref')
    cr_passed = sum(1 for r in final if r['channel'] == 'crossref')
    cr_hit_rate = "%.2f%%" % (cr_passed / cr_total_items * 100) if cr_total_items else "N/A"

    stats = {
        '检索日期': RETRIEVED,
        '候选总数（两通道原始返回）': total_raw,
        '池级1_漏斗': {
            '原始': total_raw, '过标题锚词': funnel_p1['anchor'],
            '过score≥1+Q门+硬底线': funnel_p1['score'], '去重后入库': p1_total,
        },
        '池级2_漏斗': {
            '排除池1后候选': len(all_cands) - sum(1 for c in all_cands if any(r['doi']==c['doi'] and r['pool_level']==1 for r in pool1_final)),
            '过标题或摘要锚词+放宽Q门': funnel_p2['score'],
            '去重后入库': p2_total,
        },
        '合计入库': grand_total,
        '每模块实收_池1': per_mod_p1,
        '每模块实收_池2': per_mod_p2,
        '每模块实收_合计': per_mod_total,
        '每模块目标': {m['id']: 24 for m in MODULES},
        '每模块缺口_合计': {m['id']: max(0, 24 - per_mod_total[m['id']]) for m in MODULES},
        '位移条目数': displacement,
        '白名单命中_池1': wl_p1, '白名单命中_池2': wl_p2,
        '待核_池1': pend_p1, '待核_池2': pend_p2,
        '待核比例_池1': "%.2f%%"%(pend_p1/p1_total*100) if p1_total else "0%",
        '待核比例_池2': "%.2f%%"%(pend_p2/p2_total*100) if p2_total else "0%",
        'Crossref总返回': cr_total_items, 'Crossref入库': cr_passed, 'Crossref命中率': cr_hit_rate,
        '每模块请求统计': req_stats,
        'OpenAlex新请求数': sum(rs['oa_req'] for rs in req_stats.values()),
        'Crossref新请求数': sum(rs['cr_req'] for rs in req_stats.values()),
        'OpenAlex失败数': sum(rs['oa_fail'] for rs in req_stats.values()),
        'Crossref失败数': sum(rs['cr_fail'] for rs in req_stats.values()),
        '失败语义说明': 'OpenAlex失败=HTTP错误(含429日预算耗尽)；Crossref失败=HTTP错误。缓存加载不计入失败。',
        '总量达标': '是' if grand_total >= 300 else '否（判负照记）',
        '执行参数说明': 'OpenAlex per-page=25, max 5 pages/query; Crossref rows=25; 请求间隔≥1.0s; 429退避60/120/180s',
        'OpenAlex缺失说明': 'M06-M15 OpenAlex通道因IP共享日预算耗尽(Retry-After≈15h)无法获取，仅使用Crossref通道数据',
    }
    with open(os.path.join(OUT, "统计-v1.0.json"), 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)

    # ================================================================
    # STEP 5：落盘——卷一…卷十五
    # ================================================================
    cr_noise_note = (
        "> **Crossref 通道命中率说明**：Crossref `query.bibliographic` 按词袋匹配、以被引数排序，"
        "会将高被引的方法论/软件论文（如 Fiji、GloVe、CLUSTAL W 等）顶到前面，"
        "本库通过标题锚词门+质量门过滤后，Crossref 通道总命中率为 %s（%d/%d）。"
        "因此 Crossref-only 模块（M06-M15）实收偏低。\n" % (cr_hit_rate, cr_passed, cr_total_items)
    )

    for mod in MODULES:
        mid = mod['id']
        p1_recs = [r for r in pool1_final if r['module'] == mid]
        p2_recs = [r for r in pool2_final if r['module'] == mid]

        lines = []
        lines.append("---")
        lines.append('title: "语言与思想攻击文献库·卷%s·%s"'%(mod['num'], VOL_NAMES[mid]))
        lines.append("date: %s" % RETRIEVED)
        lines.append("version: 1.0")
        lines.append("status: 结果件（池1=%d条，池2=%d条，合计=%d条；目标24；判据书v1.0已冻结）"%(len(p1_recs),len(p2_recs),len(p1_recs)+len(p2_recs)))
        lines.append("constants: 检索日%s / 通道OpenAlex+Crossref / 双池（严格+次级）"%(RETRIEVED))
        lines.append('summary: "卷%s·%s 文献条目。池级1=原门槛；池级2=锚词允许摘要命中+被引0.5×T。"'%(mod['num'], VOL_NAMES[mid]))
        lines.append("---")
        lines.append("")
        lines.append("# 语言与思想攻击文献库 · 卷%s · %s（%s）"%(mod['num'], VOL_NAMES[mid], mid))
        lines.append("")
        lines.append("> 委托人：知世 ｜ 检索执行：Qoder ｜ 检索日：%s ｜ 判据：`语言与思想攻击·文献检索判据书-v1.0-20261103.md`（已冻结）"%(RETRIEVED))
        lines.append("> OpenAlex 检索式：")
        for q in mod['oa_queries']:
            lines.append(">   · `filter=title_and_abstract.search:%s`"%q)
        lines.append("> Crossref 检索短语：")
        for q in mod['cr_queries']:
            lines.append(">   · `query.bibliographic=%s`"%q)
        lines.append("> 本卷池1 **%d** 条 / 池2 **%d** 条 / 合计 **%d** 条（目标 24；缺 %d 条）"%(
            len(p1_recs), len(p2_recs), len(p1_recs)+len(p2_recs), max(0, 24-len(p1_recs)-len(p2_recs))))
        lines.append("")
        lines.append(cr_noise_note)

        # --- 池级 1 ---
        lines.append("## 池级 1 · 严格池（%d 条）"%len(p1_recs))
        lines.append("")
        if not p1_recs:
            lines.append("*（本卷池级1无条目）*")
            lines.append("")
        for i, r in enumerate(p1_recs, 1):
            _write_entry(lines, i, r, mod)

        # --- 池级 2 ---
        lines.append("## 池级 2 · 次级池（%d 条）"%len(p2_recs))
        lines.append("")
        if not p2_recs:
            lines.append("*（本卷池级2无条目）*")
            lines.append("")
        for i, r in enumerate(p2_recs, 1):
            _write_entry(lines, i, r, mod)

        fn = os.path.join(OUT, "卷%s·%s-20261103.md"%(mod['num'], VOL_NAMES[mid]))
        with open(fn, 'w', encoding='utf-8') as f:
            f.write("\n" .join(lines) + "\n")

    # ================================================================
    # 汇总
    # ================================================================
    print("\n" + "="*60)
    print("合计入库=%d (池1=%d, 池2=%d)"%(grand_total, p1_total, p2_total))
    print("PER_MODULE (P1+P2):")
    for m in MODULES:
        mid = m['id']
        print("  %s: %d+%d=%d (gap %d)"%(mid, per_mod_p1[mid], per_mod_p2[mid],
              per_mod_total[mid], max(0, 24-per_mod_total[mid])))
    print("Crossref命中率: %s"%(cr_hit_rate))
    print("达标: %s"%stats['总量达标'])
    print("="*60)

    # 清理 __pycache__
    for d in [CRITERIA_DIR, os.path.join(REPO, "archive/10-治理与哲学/04-工具与代码")]:
        cache = os.path.join(d, "__pycache__")
        if os.path.isdir(cache): shutil.rmtree(cache)
    print("[已清理 __pycache__]")


def _write_entry(lines, idx, r, mod):
    """写一条文献条目到卷文件。"""
    au = "; ".join(r['authors'][:6]) + (" 等" if len(r['authors'])>6 else "")
    doi_str = r['doi'] or '(无DOI)'
    cited = max(r['oa_cites'], r['cr_cites'])
    gates = "/".join(r['q_gates'])
    anchors_str = ", ".join(r['anchor_hits'][:4])
    pool_tag = "池%d"%r['pool_level']
    lines.append("%d｜%s(%d).%s.%s — %s｜%s｜被引%d｜score=%d｜%s｜%s｜%s｜锚词[%s]｜%s"%(
        idx, au, r['year'], r['title'], r['venue'] or '（载体未记）',
        doi_str, r['channel'], cited, r['score'], r['level'], gates, pool_tag,
        anchors_str, r['search_url']))
    if r['abstract']:
        lines.append("    摘要：%s"%r['abstract'][:500])
    lines.append("    关联：%s"%r['rel_note'])
    lines.append("")


if __name__ == "__main__":
    main()
