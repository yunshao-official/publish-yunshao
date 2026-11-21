#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
差值归因件（第二轮·对 v1.2）：把子任务 v1.2 主档（210 条）逐条喂进本代理的
v1.2 独立复核门，量出"同一批条目、两套实现"的差出在哪一道门上。
只读，不改任何主档；输出 差值归因-子任务v1.2.md 与 .json。

与 差值归因-20261103.py 的差别：输入换成子任务 v1.2 主档，
并额外标出两类结构性问题——
  ① 章／书折叠：子任务 parent_doi()（其脚本 197—206 行）不看文献类型，
     一律砍掉 DOI 最后一段，期刊文章会被折到期刊前缀；
  ② 跨域漏网：R 门只在标题里找政治-话语词，工程／公卫类条目可借
     frame／avoidance 一类单词锚混入。
"""
import importlib.util
import io
import json
import os
import collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 上一层＝公开正本目录
SPEC = importlib.util.spec_from_file_location(
    '_v12b', os.path.join(HERE, '语言攻击文献检索器-v1.2独立复核-20261103.py'))
V12 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V12)

SRC_PATH = os.path.join(HERE, '语言与思想攻击文献库-v1.2-20261103', '文献主档-v1.2.json')
SRC = json.load(io.open(SRC_PATH, encoding='utf-8'))


def to_rec(x):
    return dict(module=x['模块号'], channel=x.get('通道') or 'crossref',
                src_file='（子任务 v1.2 主档）', doi=(x.get('DOI') or '').lower(),
                title=x.get('标题') or '', authors=x.get('作者') or [],
                year=x.get('年份'), venue=x.get('刊物') or '', type=(x.get('type') or ''),
                oa_cites=int(x.get('oa_cites') or 0), cr_cites=int(x.get('cr_cites') or 0),
                is_retracted=False, abstract=x.get('摘要') or '', 池级=x.get('池级'),
                anchors=x.get('锚词命中') or [])


WHY_ORDER = ('N门出局', 'R门出局', '硬底线出局', 'Q门出局', '无摘要出局', 'Q0无被引数据')

rows = collections.Counter()
per_mod = {}
detail = []
for x in SRC:
    r = to_rec(x)
    lvl = r['池级']
    stage = collections.Counter()
    ok, _, _ = V12.evaluate(r, lvl == 1, stage)
    key = '池%d' % lvl
    if ok:
        rows[key + '·v1.2 门下仍合格'] += 1
        per_mod.setdefault(r['module'], collections.Counter())[key + '留'] += 1
        detail.append(dict(模块=r['module'], 池级=lvl, 判定='留', 标题=r['title'][:90],
                           DOI=r['doi'], type=r['type'], 质量门=x.get('质量门')))
    else:
        why = '其他'
        for k in WHY_ORDER:
            if stage.get(k):
                why = k
                break
        if not stage.get('过锚词'):
            why = '锚词门（标题不含该模块锁定锚词）'
        rows[key + '·v1.2 门下出局→' + why] += 1
        per_mod.setdefault(r['module'], collections.Counter())[key + '剔·' + why] += 1
        detail.append(dict(模块=r['module'], 池级=lvl, 判定='出局·' + why, 标题=r['title'][:90],
                           DOI=r['doi'], type=r['type'], 子任务质量门=x.get('质量门'),
                           锚词=r['anchors'], 刊物=r['venue']))

kept = sum(v for k, v in rows.items() if '仍合格' in k)
out_dir = os.path.join(HERE, '语言与思想攻击文献库-v1.2独立复核-20261103')
json.dump(detail, io.open(os.path.join(out_dir, '差值归因-子任务v1.2.json'), 'w',
                          encoding='utf-8'), ensure_ascii=False, indent=1)

# 折叠面：章／书类 DOI 被子任务折到容器级的风险，按 DOI 形状机检
fold_risk = [d for d in detail if (d.get('type') or '') in
             ('book-chapter', 'chapter', 'book', 'edited-book', 'archived-article')]
journal_fold = [d for d in detail
                if (d.get('type') or '') in ('journal-article', 'article')
                and d['DOI'].count('/') and d['DOI'].split('/', 1)[1].count('.') >= 1]

lines = ['# 差值归因：子任务 v1.2 主档 210 条 在本代理 v1.2 独立复核门下的逐条判定',
         '',
         '> 输入：`语言与思想攻击文献库-v1.2-20261103/文献主档-v1.2.json`（210 条，池1=86／池2=124）',
         '> 判据正本：`语言与思想攻击·文献检索判据书-v1.2-20261103.md`（sha256 前缀 0be27507，mtime 09:57:34）',
         '> 门实现：本代理 `语言攻击文献检索器-v1.2独立复核-20261103.py`（第二实现，与子任务脚本互为差值核对）',
         '> 方法：逐条按它自己声明的池级送进对应档位重判，不抽样、不合并取优、不改任何冻结门槛。', '',
         '## 计数']
for k in sorted(rows):
    lines.append('- %s：%d 条' % (k, rows[k]))
lines.append('- 合计送审：%d 条；v1.2 门下合格：%d 条；出局：%d 条' % (len(SRC), kept, len(SRC) - kept))
lines.append('')
lines.append('## 逐模块')
for m in sorted(per_mod):
    lines.append('- %s：%s' % (m, '；'.join('%s=%d' % kv for kv in sorted(per_mod[m].items()))))
lines.append('')
lines.append('## 两条实现的差，具体差在哪')
lines.append('- 本代理这一轮（同一批 322 个 raw 缓存、5,254 条候选）出口是 **池1=41／池2=76／合计=117**；'
             '子任务是 **池1=86／池2=124／合计=210**。两边都远未达 200／300，判负结论一致，'
             '差值只影响"净库到底多少条"这一口径。')
lines.append('- 差异集中在 R 门与 Q 门的松紧，不在门槛数值：子任务的 R 门（其脚本 107—128 行）'
             '只要标题里出现 polic／media／power 一类政治-话语词就放行 frame／avoidance 这类危险单词锚，'
             '于是"电力变换器锁相环"（frame）、"肥胖政策杂音"（frame）这类跨域条目进了池1；'
             '本代理的 R 门另需 N 表与主题一致，这类条目出局。')
lines.append('- 子任务 `parent_doi()`（其脚本 197—206 行）不看文献类型，一律砍掉 DOI 最后一段：'
             '期刊文章 `10.1073/pnas.0712334105` 会被折成 `10.1073/pnas`，整本期刊视为同一本书，'
             '跨不同论文的错误合并风险存在；本件按 v1.2 §二.5 只在章／书类型上折叠，并留痕。')
lines.append('- 本代理 v1.2 门自身在这一轮不是"一次定盘"：同一批候选两次跑出 124 与 117，'
             '差在门 Q0 的 Crossref 回查命中率（夜间共享 IP 限流，未命中即按"无被引数据"落发现清单）。'
             '**门 Q0 是当前口径下唯一不确定的门**，须在判据书 v1.3 里补"回查失败重试／缓存固化"条款。')
lines.append('')
lines.append('## 待整读面（未做，先记账）')
lines.append('- 两池并集去重后约 **%d** 条需要逐卷整读；上一巡只覆盖 101 条，本轮整读未做，'
             '"净库"数字在整读前不得对外说。' % len({(d.get('DOI') or '').lower() for d in detail}))
io.open(os.path.join(out_dir, '差值归因-子任务v1.2.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('\n'.join(lines[5:]))
print('章/书类型条数=%d 期刊文章条数=%d' % (len(fold_risk), len(journal_fold)))
