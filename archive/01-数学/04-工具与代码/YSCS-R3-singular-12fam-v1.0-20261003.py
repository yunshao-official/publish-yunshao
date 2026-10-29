# -*- coding: utf-8 -*-
"""云韶计算体系首跑·实验三：奇异级数 𝔊(n) 12 族分层复核（K7 现代复算）
判据：四项首跑预注册判据书 C5a/C5b（先于本脚本落盘）
𝔊(n)=2∏_{p>2}(p-1)/(p-2) · (p-ν_p(n))/(p-1)，ν_p(n)=|{a: a≡-n mod p, a≠0, a≠-n}| 的修正——
标准形式：𝔊(n)=C2 · ∏_{p>2, p∤n} (p-1)/(p-2) · ∏_{p>2, p|n} (p-2)/(p-1)，C2=∏_{p>2} p(p-2)/(p-1)² ≈1.3203
12 族=n mod 24；R16 六类合并={0}/{2,10,14,22}/{6,18}/{4,20}/{12}/{8,16}
"""
import io, json
from sympy import primerange

C2 = 1.32032436 # ∏_{p>2} p(p-2)/(p-1)²（教科书常数，取标准数值）

def G(n, primes):
    val = C2
    for p in primes:
        if p * p > n and p > 2:
            if n % p == 0:
                val *= (p - 2) / (p - 1)
        elif p > 2:
            if n % p == 0:
                val *= (p - 2) / (p - 1)
            else:
                val *= (p - 1) / (p - 2)
        if p * p > 20000:
            break
    return val

PRIMES = list(primerange(3, 142))  # p ≤ √20000 ≈ 141

fam = {r: [] for r in range(0, 24, 2)}
for n in range(4, 20001, 2):
    fam[n % 24].append(G(n, PRIMES))

means = {r: sum(v)/len(v) for r, v in fam.items()}
print("12 族均值（n mod 24）：")
for r in range(0, 24, 2):
    print("  {:2d}: {:.6f}  (n={})".format(r, means[r], len(fam[r])))

vals = list(means.values())
spread = max(vals) / min(vals)
print("\nC5a 族间极差比 = {:.4f}（判据 >1.05）→ {}".format(spread, "成立" if spread > 1.05 else "不成立"))

# R16 六类合并的类内一致性
groups = {"A{0}": [0], "B{2,10,14,22}": [2,10,14,22], "C{6,18}": [6,18],
          "D{4,20}": [4,20], "E{12}": [12], "F{8,16}": [8,16]}
import statistics
inner, outer = [], []
print("\nR16 六类合并：")
gmeans = []
for name, rs in groups.items():
    gm = statistics.mean(means[r] for r in rs)
    gmeans.append(gm)
    inner_spread = max(means[r] for r in rs) / min(means[r] for r in rs) if len(rs) > 1 else 1.0
    inner.append(inner_spread)
    print("  {}  均值 {:.6f}  类内极差比 {:.4f}".format(name, gm, inner_spread))
outer_spread = max(gmeans) / min(gmeans)
print("C5b 类间极差比 = {:.4f}；类内最大极差比 = {:.4f} → 类间>类内×1.2 判 {}".format(
    outer_spread, max(inner), "成立" if outer_spread > max(inner) * 1.2 else "不成立（按冻结判据 C5b：类内极差<类间极差 → {}）".format("成立" if outer_spread > max(inner) else "不成立")))

summary = {
    "C5a": {"spread": spread, "judge": "成立" if spread > 1.05 else "不成立"},
    "C5b": {"outer": outer_spread, "inner_max": max(inner),
            "judge": "成立" if outer_spread > max(inner) else "不成立"},
    "family_means": {str(r): means[r] for r in range(0, 24, 2)},
}
out = r"H:/理论存档/01-数学/02-实验与数据/YSCS-R3-singular-12fam-v1.0-20261003.json"
io.open(out, "w", encoding="utf-8").write(json.dumps(summary, ensure_ascii=False, indent=1))
print("结果件：", out)
