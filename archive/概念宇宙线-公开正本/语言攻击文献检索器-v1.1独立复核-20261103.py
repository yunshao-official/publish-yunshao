#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言与思想攻击·文献检索器 v1.1 独立复核件（不联网，只重评缓存）

判据正本：语言与思想攻击·文献检索判据书-v1.1-20261103.md
          sha256 前缀 f683e13a，mtime 2026-11-03 09:22:41（早于本件生成）

本件由档案主代理亲手写，与子任务的 语言攻击文献检索器-v1.1-20261103.py 互为独立复核：
两者用同一批 v1.0 缓存候选（raw/*.json，2705 条原始返回），各自实现 v1.1 五道门，
出口数字若不一致，以逐条整读为准，不以任一脚本为准。

只做五件事，不联网、不发新请求：
  ① 锚词集锁死：逐字读判据书 §五 的 69 条，运行时硬断言，不等即中止
  ② R 主题共现门：多词强锚标题命中即过；单词锚须与语言／话语域词在标题共现
  ③ N 跨域负面表：标题命中负面词即出局（除非命中≥2 个多词强锚）
  ④ 硬底线 + Q1/Q2/Q3：数值口径与 v1.0 §三 相同，未放松；池级2 仅 Q 降半档
  ⑤ 两池分层 + DOI/标题去重 + 每模块漏斗 + 淘汰留痕 + 待整读标题清单

产出目录：语言与思想攻击文献库-v1.1独立复核-20261103/
"""
import glob
import importlib.util
import io
import json
import os
import re
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
CRIT = os.path.join(HERE, '语言与思想攻击·文献检索判据书-v1.1-20261103.md')
# 可用命令行换候选源与出口：argv[1]=raw 目录  argv[2]=输出目录
RAW = (sys.argv[1] if len(sys.argv) > 1
       else os.path.join(HERE, '语言与思想攻击文献库-20261103', 'raw'))
OUT = (sys.argv[2] if len(sys.argv) > 2
       else os.path.join(HERE, '语言与思想攻击文献库-v1.1独立复核-20261103'))
RETRIEVED = '2026-11-03'

# 复用既有轮子：摘要重建／去标签／标题规范化
_tool_path = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                          'archive', '10-治理与哲学', '04-工具与代码',
                          '控制权文献库检索器-v1.0-20261102.py')
_spec = importlib.util.spec_from_file_location('_ctrl_tool_v11x', _tool_path)
_tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tool)
oa_abstract = _tool.oa_abstract
strip_tags = _tool.strip_tags
norm_title = _tool.norm_title

MODULE_NAMES = {
    'M01': '语言与思想的因果', 'M02': '新话、双重话语与语言工程', 'M03': '概念隐喻与政治框架',
    'M04': '宣传、灌输与终止性套语', 'M05': '国家审查与自我审查', 'M06': '平台治理与内容审核',
    'M07': '算法规避与影子限制', 'M08': '谐音、禁忌与词汇替换', 'M09': '政治正确、辱称与语义漂移',
    'M10': '语言意识形态、符号权力与守门', 'M11': '沉默、寒蝉与舆论气候',
    'M12': '讽刺、迷因与地下话语', 'M13': '编码、隐写与规避书写', 'M14': '语言剥夺与概念后果',
    'M15': '媒体效应与被说出的问题'}


# ---------- ① 锚词集：逐字取自判据书 §五 ----------
def load_anchors(path):
    doc = io.open(path, encoding='utf-8').read()
    block = doc.split('## 五、锁定锚词表', 1)[1].split('【修改记录】', 1)[0]
    mods = {}
    for line in block.split('\n'):
        m = re.match(r'^-\s+\**M(\d\d)\**：(.+)$', line.strip())
        if m:
            mods['M' + m.group(1)] = [a.strip() for a in m.group(2).split('｜') if a.strip()]
    return mods


ANCHORS = load_anchors(CRIT)
TOTAL_ANCHORS = sum(len(v) for v in ANCHORS.values())
assert len(ANCHORS) == 15, '模块数应为 15，实为 %d' % len(ANCHORS)
assert TOTAL_ANCHORS == 69, '锚词数必须等于 69，实为 %d（判据书 v1.1 §二.1 硬断言）' % TOTAL_ANCHORS
print('[锚词锁定] 模块=15 锚词=%d' % TOTAL_ANCHORS)

# ---------- ② R 门域词 ----------
DOMAIN_WORDS = ['language', 'languages', 'linguistic', 'linguistics', 'word', 'words', 'lexical',
                'lexicon', 'vocabulary', 'discourse', 'speech', 'speaking', 'tongue', 'naming',
                'term', 'terms', 'terminology', 'semantic', 'semantics', 'pragmatic', 'pragmatics',
                'rhetoric', 'rhetorical', 'meaning', 'concept', 'concepts', 'conception',
                'metaphor', 'metaphors', 'metaphorical', 'translation', 'translate', 'narrative',
                'dialect', 'phrasing', 'wording', 'censorship', 'censored', 'propaganda',
                'newspeak', 'slur', 'slurs', 'algospeak', 'terminological', 'vocabulary']
DOMAIN_RE = re.compile(r'\b(' + '|'.join(sorted(set(DOMAIN_WORDS), key=len, reverse=True)) + r')\b')

# ---------- ③ N 跨域负面表 ----------
NEGATIVE = ['dna', 'protein', 'proteins', 'amino acid', 'amino acids', 'bacteria', 'bacterial',
            'antimicrobial', 'antibiotic', 'antibiotics', 'insulin', 'diabetes', 'tumor', 'tumour',
            'cancer', 'carcinoma', 'pcr', 'crispr', 'phylogenetic', 'phylogeny', 'modeltest',
            'partitionfinder', 'job shop', 'quadratic assignment', 'supply chain', 'venture',
            'customer loyalty', 'customer satisfaction', 'biomarker', 'surrogate endpoint',
            'quantum', 'internet of things', 'wetting', 'asset pricing', 'asset prices',
            'econometric', 'stock market', 'hiv', 'clinical characteristic', 'hospitalized',
            'mortality', 'coronavirus', 'covid', 'gene expression', 'sequence', 'rainfall',
            'concrete', 'titanium', 'alloy', 'catalyzed', 'catalysis', 'microbial', 'probiotic',
            'epidemiolog', 'inpatient', 'manikin', 'emotion regulation', 'basic emotions',
            'affective priming', 'self-assessment', 'resistance gene', 'drug resistance']

ALLOWED_TYPES = {'journal article', 'book', 'book chapter', 'conference paper',
                 'proceedings article', 'review', 'preprint', 'edited book', 'component'}


def get_T(year):
    if year >= 2021: return 40
    if year >= 2016: return 90
    if year >= 2010: return 160
    if year >= 2000: return 250
    if year >= 1990: return 400
    return 600


WHITELIST = ['nature', 'science', 'pnas', 'american political science review', 'american journal of sociology',
             'comparative political studies', 'political communication', 'public opinion quarterly',
             'new media & society', 'new media and society', 'information communication & society',
             'social media + society', 'social media society', 'journal of computer-mediated communication',
             'journal of computer mediated communication', 'media culture & society', 'media culture and society',
             'international journal of communication', 'discourse & society', 'discourse and society',
             'language in society', 'language & communication', 'language and communication', 'discourse studies',
             'journal of pragmatics', 'text & talk', 'text and talk', 'applied linguistics',
             'journal of language and social psychology', 'journal of sociolinguistics',
             'critical discourse studies', 'discourse, cognitive and language', 'cognition',
             'cognitive science', 'psychological science', 'annual review of linguistics',
             'journal of memory and language', 'memory & cognition', 'memory and cognition',
             'communication research', 'communication monographs', 'journal of communication',
             'discourse', 'journal of language and thought', 'research on language',
             'mit press', 'cambridge', 'oxford', 'routledge', 'chi', 'cscw', 'acl', 'emnlp', 'www']


def in_whitelist(venue):
    return bool(venue) and any(w in venue.lower() for w in WHITELIST)


def norm(s):
    return re.sub(r'\s+', ' ', (s or '').lower().replace('-', ' ')
                  .replace('\u2013', ' ').replace('\u2014', ' ').replace('\u2019', "'"))


def anchor_regex(a):
    """返回 (是否多词强锚, 编译后的匹配式)。单词锚允许常见词尾变化。"""
    if a == 'metaphor AND politics':
        return True, re.compile(r'\bmetaphor\w*\b')          # 共现另判
    n = norm(a)
    if ' ' in n:
        return False, re.compile(r'\b' + r'\s+'.join(re.escape(w) for w in n.split()) + r'\b')
    return False, re.compile(r'\b' + re.escape(n) + r'(es|s|ing|ed|al|ic|ism|ist)?\b')


ANCHOR_RX = {mid: [(a,) + anchor_regex(a) for a in lst] for mid, lst in ANCHORS.items()}


def hits(text, mid, other_text=None):
    """返回 [(锚, 是否多词强锚, 命中位置)]；metaphor AND politics 需两词共现。"""
    out = []
    for a, multi, rx in ANCHOR_RX[mid]:
        if a == 'metaphor AND politics':
            joined = text + ' ' + (other_text or '')
            if re.search(r'\bmetaphor\w*\b', joined) and re.search(r'\bpolitic', joined):
                out.append((a, True, 'title' if rx.search(text) or 'politic' in text else 'abstract'))
            continue
        if rx.search(text):
            out.append((a, multi or (' ' in norm(a)), 'title'))
        elif other_text is not None and rx.search(other_text):
            out.append((a, multi or (' ' in norm(a)), 'abstract'))
    return out


def r_gate(title, hh):
    """R 门：多词强锚标题命中即过；单词锚标题须与域词共现。"""
    for a, multi, where in hh:
        if multi and where == 'title':
            return True
    if any(a == 'metaphor AND politics' and where == 'title' for a, multi, where in hh):
        return True
    return bool(DOMAIN_RE.search(title))


def n_gate(title, hh):
    """N 门：标题含负面词即出局，除非标题命中≥2 个多词强锚。"""
    strong = sum(1 for a, multi, where in hh if (multi or ' ' in norm(a)) and where == 'title')
    if strong >= 2:
        return True, strong
    t = norm(title)
    bad = [w for w in NEGATIVE if w in t]
    return (False, bad[0]) if bad else (True, strong)


# ---------- 候选装载（v1.0 已落盘的 raw/*.json，不联网） ----------
def load_candidates():
    cands, files = [], sorted(glob.glob(os.path.join(RAW, '*.json')))
    for fp in files:
        base = os.path.basename(fp)[:-5]
        m = re.match(r'^(M\d\d)-(oa|cr|dj)-\d+(-p\d+)?$', base)
        if not m:
            continue
        mid, ch = m.group(1), m.group(2)
        try:
            d = json.load(io.open(fp, encoding='utf-8'))
        except Exception:
            continue
        if ch == 'oa':
            items = d.get('results')
        elif ch == 'cr':
            items = (d.get('message') or {}).get('items')
        else:
            items = None
        dj_items = None
        if ch == 'dj':
            dj_items = d.get('results')
            items = None
        for w in (items or []):
            if ch == 'oa':
                doi = (w.get('doi') or '').replace('https://doi.org/', '').strip().lower()
                title = strip_tags(w.get('title') or '')
                pl = (w.get('primary_location') or {})
                venue = strip_tags(((pl.get('source') or {}).get('display_name')) or '')
                cands.append(dict(module=mid, channel='openalex', src_file=base, doi=doi, title=title,
                                  authors=[(a.get('author') or {}).get('display_name', '')
                                           for a in (w.get('authorships') or [])],
                                  year=w.get('publication_year'), venue=venue,
                                  type=(w.get('type') or '').lower(),
                                  oa_cites=int(w.get('cited_by_count') or 0), cr_cites=0,
                                  is_retracted=bool(w.get('is_retracted')),
                                  abstract=oa_abstract(w.get('abstract_inverted_index'))))
            elif ch == 'cr':
                doi = (w.get('DOI') or '').strip().lower()
                title = strip_tags((w.get('title') or [''])[0])
                yr = None
                for df in ('published', 'issued', 'published-print', 'published-online', 'created'):
                    dp = w.get(df)
                    if dp and dp.get('date-parts') and dp['date-parts'][0]:
                        p = dp['date-parts'][0]
                        if p and isinstance(p[0], int) and p[0] > 1000:
                            yr = p[0]
                            break
                ct = w.get('container-title') or []
                cands.append(dict(module=mid, channel='crossref', src_file=base, doi=doi, title=title,
                                  authors=[', '.join(x for x in (a.get('family', ''), a.get('given', '')) if x)
                                           for a in (w.get('author') or [])],
                                  year=yr, venue=strip_tags(ct[0]) if ct else '',
                                  type=(w.get('type') or '').lower(),
                                  oa_cites=0, cr_cites=int(w.get('is-referenced-by-count') or 0),
                                  is_retracted=False, abstract=strip_tags(w.get('abstract') or '')))
        for w in (dj_items or []):
            b = w.get('bibjson') or {}
            doi = ''
            for ident in (b.get('identifier') or []):
                if (ident.get('type') or '').lower() == 'doi':
                    doi = (ident.get('id') or '').strip().lower()
                    break
            j = b.get('journal') or {}
            yr = b.get('year')
            try:
                yr = int(yr)
            except Exception:
                yr = None
            cands.append(dict(module=mid, channel='doaj', src_file=base, doi=doi,
                              title=strip_tags(b.get('title') or ''),
                              authors=[a.get('name', '') for a in (b.get('author') or []) if a.get('name')],
                              year=yr, venue=strip_tags(j.get('title') or ''),
                              type='journal article',
                              oa_cites=0, cr_cites=0, is_retracted=False,
                              abstract=strip_tags(b.get('abstract') or '')))
    return cands, files


def evaluate(rec, strict, stage):
    """五道门顺序：锚词 → 硬底线 → R → N → Q。返回 (是否入池, 记录, 放宽项)"""
    mid = rec['module']
    if mid not in ANCHORS:
        return False, None, None
    t = norm(rec['title'])
    ab = norm(rec['abstract'])
    hh = hits(t, mid, None if strict else ab)
    if strict:
        hh = [h for h in hh if h[2] == 'title']
    if not hh:
        return False, None, None
    stage['过锚词'] += 1
    ok, why = n_gate(rec['title'], hh)
    if not ok:
        stage['N门出局'] += 1
        return False, None, None
    if not r_gate(t, hh):
        stage['R门出局'] += 1
        return False, None, None
    stage['过RN'] += 1
    if not rec['doi'] or rec['is_retracted']:
        stage['硬底线出局'] += 1
        return False, None, None
    if rec['year'] is None or not (1900 <= int(rec['year']) <= 2026):
        stage['硬底线出局'] += 1
        return False, None, None
    tn = rec['type'].replace('-', ' ').replace('_', ' ').lower()
    if tn and tn not in ALLOWED_TYPES:
        stage['硬底线出局'] += 1
        return False, None, None
    T = get_T(int(rec['year']))
    scale = 1.0 if strict else 0.5
    q = []
    if rec['oa_cites'] >= int(T * scale):
        q.append('Q1')
    if rec['cr_cites'] >= int(0.6 * T * scale):
        q.append('Q2')
    mc = max(rec['oa_cites'], rec['cr_cites'])
    q3_floor = int(0.25 * T) if strict else int(0.15 * T)
    if in_whitelist(rec['venue']) and mc >= q3_floor:
        q.append('Q3')
    if not q:
        stage['Q门出局'] += 1
        return False, None, None
    score = 0
    for a, multi, where in hh:
        score += 2 if where == 'title' else 1
    if score < 1:
        return False, None, None
    has_abs = bool(rec['abstract'] and rec['abstract'].strip())
    if not has_abs and 'Q3' not in q and int(rec['year']) >= 1980:
        stage['无摘要出局'] += 1
        return False, None, None
    stage['过全门'] += 1
    relax = [] if strict else []
    if not strict:
        if len([h for h in hh if h[2] == 'title']) != len(hh):
            relax.append('强锚仅在摘要命中')
        if 'Q降级' not in relax:
            relax.append('Q门取半档')
    out = dict(rec)
    out.update(anchors=[h[0] for h in hh], anchor_where={h[0]: h[2] for h in hh},
               q_gates=q, score=score, T=T, cites=mc,
               level='核' if has_abs else '待核')
    return True, out, relax or None


def main():
    cands, files = load_candidates()
    print('[候选源] %s' % RAW)
    print('[缓存候选] raw 文件=%d 候选=%d' % (len(files), len(cands)))
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    funnel = {mid: collections.Counter() for mid in ANCHORS}
    for mid in ANCHORS:
        funnel[mid]['候选'] = sum(1 for c in cands if c['module'] == mid)

    seen = set()
    pool = {}
    stages = {}
    for level, strict in ((1, True), (2, False)):
        kept = []
        for c in cands:
            mid = c['module']
            f = funnel[mid]
            stage = stages.setdefault((level, mid), collections.Counter())
            ok, rec, relax = evaluate(c, strict, stage)
            if not ok:
                continue
            key = (c['doi'] or norm_title(c['title']))
            if key in seen:
                f['重复剔除'] += 1
                continue
            seen.add(key)
            f['入池%d' % level] += 1
            rec['池级'] = level
            if relax:
                rec['放宽项'] = relax
            kept.append(rec)
        pool[level] = kept

    # 排序（确定性）：模块 → 分数 → 被引 → DOI
    for level in pool:
        pool[level].sort(key=lambda r: (r['module'], -r['score'], -r['cites'], r['doi']))
        for i, r in enumerate(pool[level], 1):
            r['编号'] = 'P%d-%s-%02d' % (level, r['module'], i)

    p1, p2 = pool[1], pool[2]
    total = len(p1) + len(p2)
    done = (len(p1) >= 200 and total >= 300)
    for level in pool:
        for r in pool[level]:
            r['检索URL'] = '见 %s（v1.0 缓存）' % r['src_file']

    stats = {
        '判据': '语言与思想攻击·文献检索判据书-v1.1-20261103.md',
        '判据sha256前缀': 'f683e13a',
        '生成方式': '独立复核件——直接重评 v1.0 缓存 raw/*.json，未发任何新请求',
        '抓取日期': RETRIEVED,
        '锚词模块数': len(ANCHORS),
        '锚词总数': TOTAL_ANCHORS,
        '候选总数': len(cands),
        '池级1': len(p1),
        '池级2': len(p2),
        '合计': total,
        '达标': done,
        '数量口径': '池级1≥200 且 合计≥300；任一不满足即判负照记',
        '每模块漏斗': {mid: dict(funnel[mid]) for mid in sorted(ANCHORS)},
        '逐级漏斗': {'池%d|%s' % (lv, mid): dict(c) for (lv, mid), c in sorted(stages.items())},
        '通道分布': {('池%d' % lv): dict(collections.Counter(r['channel'] for r in pool[lv]))
                     for lv in pool},
        '核/待核': {('池%d' % lv): dict(collections.Counter(r['level'] for r in pool[lv]))
                    for lv in pool},
        '已知缺口': [
            '本件只重评缓存：M06–M15 在 v1.0 抓取时 OpenAlex 全量 429（预算约 15 小时后恢复），'
            '故这些模块的候选只有 Crossref 词袋结果，缺 OpenAlex 高被引池。',
            'Crossref 词袋（query.bibliographic）与 DOAJ 新通道的数据本件未取，需另跑 v1.1 联网件。',
            '入池条目未经逐条人工整读；整读审计与剔除表由档案主代理另出，剔除率>10%% 的模块判检索式不合格。',
        ],
    }
    io.open(os.path.join(OUT, '统计-v1.1独立复核.json'), 'w', encoding='utf-8').write(
        json.dumps(stats, ensure_ascii=False, indent=1))
    io.open(os.path.join(OUT, '文献主档-v1.1独立复核.json'), 'w', encoding='utf-8').write(
        json.dumps(p1 + p2, ensure_ascii=False, indent=1))

    # 待整读标题清单（给我逐条读，出审计剔除表）
    lines = ['# 语言与思想攻击文献库 v1.1 独立复核 · 待整读标题清单（2026-11-03）',
             '',
             '> 本件由 `语言攻击文献检索器-v1.1独立复核-20261103.py` 生成，只重评 v1.0 缓存候选，未联网。',
             '> 池级1=%d 池级2=%d 合计=%d；判据 v1.1 §二.5 口径：池1≥200 且 合计≥300 → %s' % (
                 len(p1), len(p2), total, '达标' if done else '**未达（判负照记）**'),
             '']
    for mid in sorted(ANCHORS):
        a = [r for r in p1 if r['module'] == mid]
        b = [r for r in p2 if r['module'] == mid]
        lines.append('## %s %s（池1=%d 池2=%d）' % (mid, MODULE_NAMES[mid], len(a), len(b)))
        lines.append('')
        for lv, L in (('1', a), ('2', b)):
            lines.append('- 池级%s' % lv)
            if not L:
                lines.append('  （空）')
            for i, r in enumerate(L, 1):
                lines.append('  %d. %s（%s）｜%s｜%s｜被引 %d/%d｜%s｜门 %s｜锚 %s｜%s' % (
                    i, (r['title'] or '（无题）')[:120], r['year'], r['venue'][:40] or '—',
                    r['doi'] or '无DOI', r['oa_cites'], r['cr_cites'], r['level'],
                    '+'.join(r['q_gates']), '、'.join(r['anchors'][:3]), r['channel']))
            lines.append('')
        lines.append('')
    io.open(os.path.join(OUT, '待整读清单-v1.1独立复核.md'), 'w', encoding='utf-8').write('\n'.join(lines))

    print('[结果] 池1=%d 池2=%d 合计=%d 达标=%s' % (len(p1), len(p2), total, done))
    print('[每模块] ')
    for mid in sorted(ANCHORS):
        print('  %s %-16s 候选=%-5d 池1=%-4d 池2=%-4d' % (
            mid, MODULE_NAMES[mid][:8], funnel[mid]['候选'], funnel[mid]['入池1'], funnel[mid]['入池2']))


if __name__ == '__main__':
    main()
