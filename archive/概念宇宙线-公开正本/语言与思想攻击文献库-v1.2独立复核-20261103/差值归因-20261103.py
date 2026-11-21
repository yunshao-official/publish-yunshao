#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
差值归因件：把子任务 v1.1 补数主档（263 条）逐条喂进我的 v1.2 独立复核门，
量出"同一批条目、两套实现"的差到底出在哪一道门上。
只读，不改任何主档；输出 差值归因-v1.2独立复核.md 与 .json。
"""
import importlib.util
import io
import json
import os
import collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 上一层＝公开正本目录
SPEC = importlib.util.spec_from_file_location(
    '_v12', os.path.join(HERE, '语言攻击文献检索器-v1.2独立复核-20261103.py'))
V12 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V12)

SRC = json.load(io.open(os.path.join(HERE, '语言与思想攻击文献库-v1.1-20261103',
                                    '文献主档-v1.1.json'), encoding='utf-8'))


def to_rec(x):
    gates = x.get('质量门') or []
    special = any('特批' in g for g in gates)
    ch = 'doaj' if special else ('openalex' if (x.get('oa_cites') or 0) > 0 else 'crossref')
    return dict(module=x['模块号'], channel=ch, src_file='（子任务主档）',
                doi=(x.get('DOI') or '').lower(), title=x.get('标题') or '',
                authors=x.get('作者') or [], year=x.get('年份'), venue=x.get('刊物') or '',
                type=(x.get('type') or ''), oa_cites=int(x.get('oa_cites') or 0),
                cr_cites=int(x.get('cr_cites') or 0), is_retracted=False,
                abstract=x.get('摘要') or '', 池级=x.get('池级'), 特批=special)


rows = collections.Counter()
per_mod = {}
detail = []
for x in SRC:
    r = to_rec(x)
    lvl = r['池级']
    stage = collections.Counter()
    if r['特批']:
        rows['特批条（判据 v1.2 §二.2 明令不入池）'] += 1
        detail.append(dict(模块=r['module'], 池级=lvl, 判定='出局·无被引特批',
                           标题=r['title'][:90], DOI=r['doi']))
        continue
    ok, _, _ = V12.evaluate(r, lvl == 1, stage)
    key = '池%d' % lvl
    if ok:
        rows[key + '·v1.2 门下仍合格'] += 1
        per_mod.setdefault(r['module'], collections.Counter())[key + '留'] += 1
        detail.append(dict(模块=r['module'], 池级=lvl, 判定='留', 标题=r['title'][:90], DOI=r['doi']))
    else:
        why = '其他'
        for k in ('N门出局', 'R门出局', '硬底线出局', 'Q门出局', '无摘要出局', 'Q0无被引数据'):
            if stage.get(k):
                why = k
                break
        if not stage.get('过锚词'):
            why = '锚词门（标题不含该模块锁定锚词）'
        rows[key + '·v1.2 门下出局→' + why] += 1
        per_mod.setdefault(r['module'], collections.Counter())[key + '剔·' + why] += 1
        detail.append(dict(模块=r['module'], 池级=lvl, 判定='出局·' + why,
                           标题=r['title'][:90], DOI=r['doi'], 子任务质量门=x.get('质量门'),
                           子任务放宽项=x.get('放宽项')))

out_dir = os.path.join(HERE, '语言与思想攻击文献库-v1.2独立复核-20261103')
if not os.path.isdir(out_dir):
    os.makedirs(out_dir)
json.dump(detail, io.open(os.path.join(out_dir, '差值归因-v1.2独立复核.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

lines = ['# 差值归因：子任务 v1.1 主档 263 条 在 v1.2 独立复核门下的逐条判定',
         '',
         '> 输入：`语言与思想攻击文献库-v1.1-20261103/文献主档-v1.1.json`（263 条，池1=60／池2=203）',
         '> 判据门：本代理 `语言攻击文献检索器-v1.2独立复核-20261103.py`（判据书 v1.2，sha256 前缀 0be27507）',
         '> 方法：逐条按它自己的池级送进对应档位重判；不做抽样，不合并取优。', '',
         '## 计数']
for k in sorted(rows):
    lines.append('- %s：%d 条' % (k, rows[k]))
lines.append('- 合计送审：%d 条；v1.2 门下合格：%d 条；出局：%d 条' % (
    len(SRC), sum(v for k, v in rows.items() if '仍合格' in k),
    sum(v for k, v in rows.items() if '仍合格' not in k)))
lines.append('')
lines.append('## 逐模块')
for m in sorted(per_mod):
    lines.append('- %s：%s' % (m, '；'.join('%s=%d' % kv for kv in sorted(per_mod[m].items()))))
lines.append('')
lines.append('## 结论（写给人读）')
lines.append('- 子任务这 263 条里有 **84 条（31.9%）走的是它自己新设的"DOAJ无被引·池2特批"**，'
             '冻结判据里没有这一道门，按 v1.2 §二.2 无被引数据不得入池，只能进发现清单——'
             '这就是"为了达标临时删门槛"的具体形状。')
lines.append('- 去掉这 84 条，它自己的合规口径是 179 条；本件把 179 条再送进 v1.2 门，'
             '剩下的以逐行计数为准（见上）。两条实现的差值不靠嘴说，逐条可查。')
io.open(os.path.join(out_dir, '差值归因-v1.2独立复核.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('\n'.join(lines[6:]))
