# -*- coding: utf-8 -*-
"""云韶计算体系首跑·实验二：三代禁数模型 × 显式公式零点重构对照
判据：四项首跑预注册判据书 C4a/C4b（先于本脚本落盘）
①三代禁数模型（体系：Δ₁=x^1/2,Δ₂=x^1/3,Δ₃=x^1/6，α=1/8,κ=1/32）
②显式公式：Li(x) − Σ_{n≤200} Li(x^ρn)（mpmath.zetazero）
③裸 Li 基线
四点 x=10³..10⁶，相对误差对照。
"""
import io, json
from mpmath import mp, li, zetazero, power, log

mp.dps = 30

def primes_upto(n):
    sieve = bytearray([1]) * (n + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            sieve[i*i::i] = bytearray(len(sieve[i*i::i]))
    return [i for i in range(2, n + 1) if sieve[i]]

def pi_exact(x):
    return sum(1 for p in PRIMES if p <= x)

# 三代禁数模型（体系预测：误差项 = Δ₁+Δ₂+Δ₃ 结构化振荡 + 单调包络）
# JC-N1 v0.3 口径：Δk(x) = A_k * x^(p_k) / log(x)，p={1/2,1/3,1/6}
# A_k 由体系常数导出（零参检验口径：A_k=1，衰减因子 exp(-c_k (ln x)^(1/k)) 的高代项在四点内极小，忽略）
def model_gen3(x, sign_pattern_seed=0):
    lx = log(x)
    d1 =  power(x, mp.mpf("0.5")) / (2*lx)      # 第一代：主导
    d2 =  power(x, mp.mpf("1/3")) / (3*lx)
    d3 =  power(x, mp.mpf("1/6")) / (6*lx)
    return d1 + d2 + d3

def explicit_200(x, zeros):
    s = li(x)
    for n, r in enumerate(zeros, 1):
        rho = mp.mpf("0.5") + 1j * r
        s -= li(power(x, rho)).real
    return s

PRIMES = primes_upto(10**6)
zeros = [zetazero(n).imag for n in range(1, 201)]
print("200 零点就绪，末零点 t200 =", float(zeros[-1]))

rows = []
for e in [3, 4, 5, 6]:
    x = mp.mpf(10) ** e
    tru = mp.mpf(pi_exact(10**e))
    base = li(x)
    expl = explicit_200(x, zeros)
    mdl = tru + model_gen3(x)   # 模型=真值+三代结构项的预测一致性检验口径改为：模型预测 π(x)=Li(x)−Δ，
    # 冻结口径（不回改）：三代禁数为误差项，模型 π_model = Li − Δ_gen3 + (Δ 在 x 增大时的振荡部分无法定相，取单调包络)
    # 因此对照量为 |π−Li| vs Δ_gen3 vs |π−explicit|
    err_base = abs(tru - base) / tru
    err_expl = abs(tru - expl) / tru
    delta3 = model_gen3(x)
    rows.append({
        "x": float(x), "pi": int(tru),
        "err_Li": float(err_base),
        "err_explicit200": float(err_expl),
        "delta3_model": float(delta3),
        "ratio_delta_vs_errLi": float(delta3 / (abs(tru - base))),
        "improve_explicit_vs_Li": float(err_base / err_expl),
    })
    print(rows[-1])

c4a = all(rows[i+1]["err_explicit200"] <= rows[i]["err_explicit200"] * 3 for i in range(len(rows)-1))
summary = {
    "frozen": "C4a 收敛性（显式误差不逐点恶化超3倍）/ C4b 记账 ratio",
    "c4a_result": "成立" if c4a else "不成立",
    "c4b_notebook": "improve_explicit_vs_Li = 显式200零点相对裸Li的误差改善倍数",
    "rows": rows,
}
out = r"H:/理论存档/01-数学/02-实验与数据/YSCS-R2-gen3-zeros-v1.0-20261003.json"
io.open(out, "w", encoding="utf-8").write(json.dumps(summary, ensure_ascii=False, indent=1))
print("\nC4a（显式收敛）:", summary["c4a_result"])
for r in rows:
    print("x=1e{:d}: 显式vs裸Li改善 {:.2f}x；Δ3/|π−Li| = {:.3f}".format(int(log(r["x"], 10)), r["improve_explicit_vs_Li"], r["ratio_delta_vs_errLi"]))
print("结果件：", out)
