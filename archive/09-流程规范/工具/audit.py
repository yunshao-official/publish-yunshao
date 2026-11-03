#!/usr/bin/env python3
# 全库口径巡检：自洽度不是感觉，是可以数的
import os, re, collections
ROOT = '/tmp/ys/publish-yunshao'
files = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if f.endswith('.md'):
            files.append(os.path.join(dp, f))
txt = {}
for p in files:
    try:
        txt[p] = open(p, encoding='utf-8').read()
    except Exception:
        txt[p] = ''
rel = lambda p: p.replace(ROOT + '/', '')

print(f'文件数={len(files)}  总字数={sum(len(t) for t in txt.values()):,}')

# ---------- A. 状态标签收支 ----------
LABELS = ['正本', '已证', '机器验证', '实证', '条件成立', '在案', '在办',
          '判负照记', '判负', '冻结封存', '封存', '降级', '不可数值检验', '不可复核', '裁决']
print('\n[A] 状态标签出现次数（全库）')
cnt = {L: sum(t.count(L) for t in txt.values()) for L in LABELS}
print('  ' + '  '.join(f'{L}={c}' for L, c in cnt.items()))
pos = cnt['正本'] + cnt['已证'] + cnt['机器验证'] + cnt['实证'] + cnt['在案'] + cnt['条件成立']
neg = cnt['判负照记'] + cnt['判负'] + cnt['冻结封存'] + cnt['封存'] + cnt['不可数值检验'] + cnt['不可复核']
print(f'  肯定侧合计={pos}   否定侧合计={neg}   否定/肯定 = {neg/max(pos,1):.3f}')

# ---------- B. 4.5 的出生式有几条 ----------
print('\n[B] “4.5” 被生成出来的互不相同的公式路线')
routes = {
    '3空间+1时间+0.5缺陷': r'3空间\s*[+＋]\s*1时间|3空间.{0,6}1时间.{0,8}0\.5',
    '每三维配0.5缺陷(36维总账)': r'每三维.{0,12}0\.5|0\.5维缺陷',
    '1.5=3×0.5': r'1\.5\s*=\s*3\s*[×x]',
    '3层×3个×0.5bit=4.5bit': r'4\.5\s*bit|3\s*层\s*[×x]\s*3',
    'α=4.5/36=1/8': r'4\.5\s*/\s*36',
    '加权测度 4+θ, θ=1/2': r'x.?5\^?\{?\(?.{0,3}θ.?1.{0,12}Hausdorff|Hausdorff\s*=\s*4\.5',
    '4.414 四舍五入': r'4\.414.{0,20}4\.5|4\.5.{0,20}4\.414',
    '4+0.5': r'4\s*\+\s*0\.5',
    '4+0.125(笔误)': r'4\.414\s*=\s*4\s*\+\s*0\.125',
}
for name, pat in routes.items():
    hits = []
    for p, t in txt.items():
        for m in re.finditer(pat, t):
            ln = t[:m.start()].count('\n') + 1
            hits.append(f'{rel(p)}:{ln}')
    print(f'  {name:<28} {len(hits)} 处  ' + '; '.join(hits[:3]) + (' …' if len(hits) > 3 else ''))

# ---------- C. 4.414 / 4.375 / 公理IV 的生命周期 ----------
print('\n[C] 已降级概念的传播（封存后是否仍以活口径存在）')
DEADMARK = ('降级', '判负', '封存', '不严谨', '无独立证明力', '循环', '重言式', '不可复核', '未完成')
for term in ['4.414', '4.375', '公理IV', '1.44']:
    lives, negs = [], []
    for p, t in txt.items():
        for m in re.finditer(re.escape(term), t):
            ln = t[:m.start()].count('\n')
            line = t[m.start():t.find('\n', m.start())] if False else t.split('\n')[ln]
            w = t[max(0, m.start()-400):m.start()+400]
            (negs if any(k in w for k in DEADMARK) else lives).append(f'{rel(p)}:{ln+1}')
    print(f'  “{term}”：命中 {len(negs)+len(lives)} 处；带否定语境的 {len(negs)} 处；'
          f'周围无否定标记（=裸引用）的 {len(lives)} 处')
    if lives:
        print('      裸引用样本: ' + '; '.join(lives[:6]))

# ---------- D. 已封存的旗舰结论是否还被下游引用 ----------
print('\n[D] 自我销毁件的下游引用')
cases = {
    '泛弦“最大模/次大模=1.44”已证不可能': (r'不可能成立|推论1', '1\.44'),
    'RH线/公理IV 已降级为几何诠释': ('降级', r'4\.414|4\.375'),
    'RD-4 判负读数禁止入结论': ('禁止入结论', r'r=-?0\.6|正相关'),
}
for name, (deadpat, livepat) in cases.items():
    dead_files = [rel(p) for p, t in txt.items() if re.search(livepat, t) and re.search(deadpat, t)]
    live_files = [rel(p) for p, t in txt.items() if re.search(livepat, t)]
    only_live = [f for f in live_files if f not in dead_files]
    print(f'  {name}\n     含该量的文件 {len(live_files)} 个，其中同时带否定标记 {len(dead_files)} 个，'
          f'只搬运数字不带否定标记 {len(only_live)} 个')

# ---------- E. 体系内“可复算/不可复算”比例（抽查最硬的 20 个数值断言） ----------
print('\n[E] 数值断言的可复核性标签分布（含“4.414维历史断言”一类）')
rows = re.findall(r'([^\n|]{0,40}4\.414[^\n|]{0,60})', ''.join(t for t in txt.values()))
for r in sorted(set(x.strip() for x in rows))[:8]:
    print('   ·', r[:110])
