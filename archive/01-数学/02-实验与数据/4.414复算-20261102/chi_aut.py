#!/usr/bin/env python3
# 复算 χ 覆盖不等式 + |Aut(Z4 x C2 x C2)|（高精度 Decimal 版，独立于体系脚本）
from decimal import Decimal as D, getcontext
import math
getcontext().prec = 60

def li(x):
    """li(x) = gamma + ln|ln x| + Σ_{k>=1} ln(x)^k / (k·k!)   (x>1)"""
    L = D(x).ln(); s = D('0.5772156649015328606065120900824024310421593359399263') + L.ln()
    num = D(1)
    for k in range(1, 1200):
        num = num*L/k
        term = num/k
        s += term
        if abs(term) < D(10)**-70: break
    return s
LI2 = li(2)
chi = lambda x: li(D(x)) - LI2

def sieve(n):
    sv = bytearray([1])*(n+1); sv[0]=sv[1]=0
    for i in range(2, int(n**0.5)+1):
        if sv[i]: sv[i*i::i] = bytearray(len(sv[i*i::i]))
    return [i for i in range(n+1) if sv[i]]
PR = sieve(400); PSET = set(PR)
CH = {n: chi(n) for n in range(2, 401)}

print('=== χ 覆盖不等式 ρ(p,q)=χ(p)+χ(q)−χ(N)，N 偶数 4..200 ===')
best = {}; worst = {}; neg_pairs = []
for N in range(4, 201, 2):
    cand = [(p, N-p) for p in PR if p <= N-p and (N-p) in PSET]
    vals = []
    for p, q in cand:
        r = CH[p] + CH[q] - CH[N]
        vals.append((r, p, q))
        if r < 0: neg_pairs.append((N, p, q, float(r)))
    r, p, q = max(vals)
    best[N] = (r, p, q, len(vals))
    r2, p2, q2 = min(vals)
    worst[N] = (r2, p2, q2)
uncov = [N for N, v in best.items() if v[0] < 0]
print('  每 N 的最大 ρ（前若干）:', ', '.join(f'N={N}:{v[0]:+.5f}({v[1]},{v[2]})' for N, v in list(best.items())[:10]))
print(f'  没有任何配对使 ρ≥0 的 N（不覆盖点）= {uncov}')
mn = min((v[0], N, v[1], v[2]) for N, v in worst.items() if N >= 18)
print(f'  「全配对都覆盖」最严口径：N≥18 时 min-ρ 的全局最小 = {mn[0]:.6f} @ N={mn[1]} 配对({mn[2]},{mn[3]})')
print(f'  例外配对(ρ<0) 且 N≥6 的条数 = {sum(1 for t in neg_pairs if t[0] >= 6)}（你档例外全表：5 条）')
print(f'  ρ<0 的配对总数 = {len(neg_pairs)}')
print('  逐条 ρ<0 配对:', ', '.join(f'{N}:({p},{q}){r:+.4f}' for N, p, q, r in neg_pairs))

print('\n=== |Aut(Z4 × C2 × C2)| 暴力枚举 ===')
G = [(a, b, c) for a in range(4) for b in range(2) for c in range(2)]
def order(x):
    k = 1; v = x
    while v != (0, 0, 0):
        v = ((v[0]+x[0]) % 4, (v[1]+x[1]) % 2, (v[2]+x[2]) % 2); k += 1
    return k
G4 = [x for x in G if x != (0, 0, 0) and 4 % order(x) == 0]
G2 = [x for x in G if x != (0, 0, 0) and 2 % order(x) == 0]
def add(u, v): return ((u[0]+v[0]) % 4, (u[1]+v[1]) % 2, (u[2]+v[2]) % 2)
cnt = 0
for a in G4:
    for b in G2:
        for c in G2:
            img = set()
            for i in range(4):
                for j in range(2):
                    for k in range(2):
                        img.add((i*a[0] % 4, (j*b[1] + k*c[1]) % 2, (j*b[2] + k*c[2]) % 2))
            if len(img) == 16: cnt += 1
print(f'  4阶生成元候选 {len(G4)} 个, 2阶 {len(G2)} 个, 满射三元组数 = {cnt}')
print(f'  |Aut(Z4 × C2 × C2)| = {cnt}')
