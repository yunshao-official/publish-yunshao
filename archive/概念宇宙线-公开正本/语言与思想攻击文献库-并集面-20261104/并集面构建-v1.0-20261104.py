#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并集面构建 v1.0（2026-11-04）
把三套实现（补跑 180／子任务 v1.2 210／协调人独立复核 117）按 DOI 归一去重成一张待整读面。
规矩：只读三份主档，只写并集面与两个分卷；不改任何主档、不联网、不动判据。
"""
import json, os, re, collections, hashlib

D = os.path.dirname(os.path.abspath(__file__))                      # …/概念宇宙线-公开正本/语言与思想攻击文献库-并集面-20261104
ROOT = os.path.dirname(D)                                            # …/概念宇宙线-公开正本
SRC = [('补跑', '语言与思想攻击文献库-v1.2补跑-20261104/文献主档-v1.2补跑.json'),
       ('v1.2', '语言与思想攻击文献库-v1.2-20261103/文献主档-v1.2.json'),
       ('独立复核', '语言与思想攻击文献库-v1.2独立复核-20261103/文献主档-v1.2独立复核.json')]


def norm_title(t):
    return re.sub(r'[^a-z0-9\u4e00-\u9fff]+', ' ', (t or '').lower()).strip()[:70]


def key(r):
    d = str(r.get('doi') or r.get('DOI') or '').lower().strip()
    return d if d.startswith('10.') else 'T|' + norm_title(r.get('title') or r.get('标题'))


def T(year):
    y = int(year or 2000)
    return 40 if y >= 2021 else 90 if y >= 2016 else 160 if y >= 2010 else 250 if y >= 2000 else 400 if y >= 1990 else 600


def main():
    recs = {}
    for lbl, rel in SRC:
        for r in json.load(open(os.path.join(ROOT, rel), encoding='utf-8')):
            k = key(r)
            if k not in recs:
                recs[k] = {'并集号': '', 'doi': k if k.startswith('10.') else '',
                           '标题': r.get('title') or r.get('标题') or '',
                           '作者': r.get('authors') or r.get('作者') or '',
                           '年份': r.get('year') or r.get('年份'),
                           '刊物': r.get('venue') or r.get('刊物') or '', 'type': r.get('type') or '',
                           '模块号': r.get('模块号') or r.get('module') or '',
                           '摘要': r.get('abstract') or r.get('摘要') or '',
                           'oa_cites': r.get('oa_cites') or 0, 'cr_cites': r.get('cr_cites') or 0,
                           '质量门': r.get('质量门') or r.get('q_gates') or [],
                           '放宽项': r.get('放宽项') or [], '池级': r.get('池级'), '来源': []}
            e = recs[k]
            e['来源'].append(lbl)
            e['池级'] = min(e['池级'] or 9, r.get('池级') or 9)                       # 三家一致取最严（池1 优先）
            if max(r.get('oa_cites') or 0, r.get('cr_cites') or 0) > max(e['oa_cites'] or 0, e['cr_cites'] or 0):
                e['oa_cites'], e['cr_cites'] = r.get('oa_cites') or 0, r.get('cr_cites') or 0   # 被引取各家最大
            if not e['摘要'] and (r.get('abstract') or r.get('摘要')):
                e['摘要'] = r.get('abstract') or r.get('摘要')
            if not e['刊物'] and (r.get('venue') or r.get('刊物')):
                e['刊物'] = r.get('venue') or r.get('刊物')
    lst = sorted(recs.values(), key=lambda x: (str(x['模块号']), -max(x['oa_cites'] or 0, x['cr_cites'] or 0)))
    for i, r in enumerate(lst, 1):
        r['并集号'] = 'U%03d' % i
        r['被引取大'] = max(r['oa_cites'] or 0, r['cr_cites'] or 0)
        r['本档T'] = T(r['年份'])
    assert len(lst) == 249, '并集=%d ≠ 249（三实现面变了，须先查主档）' % len(lst)
    assert sum(1 for r in lst if r['并集号'].startswith('U')) == 249
    tgt = os.path.join(D, '并集面-249.json')
    json.dump(lst, open(tgt, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for nm, sub in (('甲卷-U001-U125.json', [r for r in lst if r['并集号'] <= 'U125']),
                    ('乙卷-U126-U249.json', [r for r in lst if r['并集号'] > 'U125'])):
        json.dump(sub, open(os.path.join(D, nm), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for f in ('并集面-249.json', '甲卷-U001-U125.json', '乙卷-U126-U249.json'):
        p = os.path.join(D, f)
        print(f, os.path.getsize(p), hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16])
    print('总数', len(lst), '无摘要', sum(1 for r in lst if not (r['摘要'] or '').strip()),
          '池1', sum(1 for r in lst if r['池级'] == 1), '池2', sum(1 for r in lst if r['池级'] == 2),
          '三方共有', sum(1 for r in lst if len(set(r['来源'])) == 3),
          '仅一方', sum(1 for r in lst if len(set(r['来源'])) == 1))


if __name__ == '__main__':
    main()
