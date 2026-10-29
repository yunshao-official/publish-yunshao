# -*- coding: utf-8 -*-
"""
砖8：悬崖地形"无坡"的严格定义与测量（否定性框架第8砖）
判据冻结（先于运行）：
  P1 分布：E_top 随机p串分布 与 Binomial(k,1/2) 的均值/方差吻合（χ²目测+矩对比）
  P2 无细粒度坡判据：median|ΔE(单点翻转)| / std(E) ≥ 0.3 → 邻域步长与全局同阶（坡不存在）
  P3 自相关：随机游走 r(1)=corr(E_t,E_{t+1}) ≈ 0（|r(1)|≤0.1）
  P4 局部极小密度：实测记录（对照解释用）
  对照组：one-hot 列残差地形（已知有坡），P2 指标应显著小于悬崖组
  对象：k=24，BA-free 直接随机素数对（与压缩N编码线同构造），5000 p串/组
"""
import random, math, json, statistics as st
import exp_encodings as E

K = 24
NS = 5000

def e_top(p, N, k):
    q = E.lsb_recover(p, N, k)
    return E.popcount(((p * q) ^ N) >> k)

def sample_p(rng, k):
    return rng.getrandbits(k) | 1 | (1 << (k - 1))

def cliff_terrain(k=K, n=NS, seed=2024):
    rng = random.Random(seed)
    # 固定一个 N
    p0, q0, N = E.gen_N(k, 42)
    Es = [e_top(sample_p(rng, k), N, k) for _ in range(n)]
    # 单点翻转 ΔE
    dEs = []
    for _ in range(n):
        p = sample_p(rng, k)
        e1 = e_top(p, N, k)
        j = rng.randrange(1, k - 1)
        p2 = p ^ (1 << j)
        if not (p2 >> (k-1)) & 1:
            p2 |= 1 << (k - 1)
        dEs.append(abs(e_top(p2, N, k) - e1))
    # 随机游走自相关 r(1)
    walk = []
    p = sample_p(rng, k)
    for _ in range(2000):
        walk.append(e_top(p, N, k))
        j = rng.randrange(1, k - 1)
        p = p ^ (1 << j)
        p |= 1 << (k - 1)
    r1 = st.correlation(walk[:-1], walk[1:]) if hasattr(st, "correlation") else (
        (sum((a-st.mean(walk[:-1]))*(b-st.mean(walk[1:])) for a,b in zip(walk[:-1],walk[1:]))) /
        math.sqrt(sum((a-st.mean(walk[:-1]))**2 for a in walk[:-1]) * sum((b-st.mean(walk[1:]))**2 for b in walk[1:])))
    # 局部极小密度
    n_min = 0
    trials = 400
    for _ in range(trials):
        p = sample_p(rng, k)
        e1 = e_top(p, N, k)
        is_min = True
        for j in range(1, k - 1):
            p2 = (p ^ (1 << j)) | (1 << (k - 1))
            if e_top(p2, N, k) < e1:
                is_min = False; break
        n_min += is_min
    med_dE = st.median(dEs)
    sd = st.pstdev(Es)
    return {"mean_E": round(st.mean(Es),2), "binom_mean": k/2,
            "std_E": round(sd,2), "binom_std": round(math.sqrt(k)/2,2),
            "median_abs_dE": med_dE, "P2_ratio": round(med_dE/sd, 3),
            "autocorr_r1": round(r1, 4),
            "local_min_density": round(n_min/trials, 4)}

def onehot_terrain(k=10, n=800, seed=2024):
    """对照组：one-hot 列残差地形（0905方法A能量）——已知有坡。"""
    rng = random.Random(seed)
    p0, q0, N = E.gen_N(k, 42)
    # 状态 = p 位（k-2），能量 = 列残差平方和（one-hot进位版简化：列和与N列差的平方）
    def enc_energy(p):
        q = E.lsb_recover(p, N, k)
        prod = p * q
        pb, nb, qb = E.bits_set(p, k), E.bits_set(N, 2*k), E.bits_set(q, k)
        e = 0
        for i in range(2*k):
            col = sum(pb[j]*qb[i-j] for j in range(max(0, i-k+1), min(i, k-1)+1) if 0 <= i-j < k)
            e += (col - nb[i]) ** 2
        return e
    Es = [enc_energy(sample_p(rng, k)) for _ in range(n)]
    dEs = []
    for _ in range(n):
        p = sample_p(rng, k)
        e1 = enc_energy(p)
        j = rng.randrange(1, k-1)
        p2 = (p ^ (1 << j)) | (1 << (k-1))
        dEs.append(abs(enc_energy(p2) - e1))
    med_dE = st.median(dEs)
    sd = st.pstdev(Es)
    return {"mean_E": round(st.mean(Es),1), "std_E": round(sd,1),
            "median_abs_dE": med_dE, "P2_ratio": round(med_dE/sd, 3) if sd else None}

if __name__ == "__main__":
    r1 = cliff_terrain()
    print("悬崖地形（LSB, k=24）:", json.dumps(r1, ensure_ascii=False))
    r2 = onehot_terrain()
    print("one-hot 对照（k=10）:", json.dumps(r2, ensure_ascii=False))
    verdict = {
        "P1_分布吻合": abs(r1["mean_E"] - r1["binom_mean"]) < 2 and abs(r1["std_E"] - r1["binom_std"]) < 1.5,
        "P2_无细粒度坡(≥0.3)": r1["P2_ratio"] >= 0.3,
        "P3_自相关零(|r1|≤0.1)": abs(r1["autocorr_r1"]) <= 0.1,
        "对照_有坡地形P2更小": (r2["P2_ratio"] or 9) < r1["P2_ratio"],
    }
    print("判决:", verdict)
    json.dump({"cliff": r1, "onehot": r2, "verdict": verdict},
              open("results/brick8.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
