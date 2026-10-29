# -*- coding: utf-8 -*-
"""
omega_factorization_negbound-v1.0-20260920.py
判据书：《代数册·因子分解签名族负边界预注册判据书-v1.0-20260920.md》（NTFS 冻结 2026-09-20 00:31:05，先于本脚本首跑）
判据 F0-F5：因子分解签名族（Ω/ω/v5/v7/ln(φ/N)/ln P(N)）× 12 组·偶数侧（N mod 24）
定理 K1 数值印证。5 片分片+检查点。纯标准库+numpy/scipy（KS 与置换双通道）。
"""
import json, math, sys, time
from pathlib import Path
import numpy as np
from scipy import stats

BASE = Path(r"H:\理论存档\01-数学")
RES = BASE / "02-实验与数据" / "results"
RES.mkdir(parents=True, exist_ok=True)
TAG = "v1.0-20260920"
X_MAX = 200000
N_SHARDS = 5
SEED = 20260920

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

# ---------- 因子分解工具 ----------
def spf_sieve(n):
    """最小素因子筛 [0..n]"""
    spf = np.zeros(n + 1, dtype=np.int64)
    spf[1] = 1
    for i in range(2, n + 1):
        if spf[i] == 0:
            for j in range(i, n + 1, i):
                if spf[j] == 0:
                    spf[j] = i
    return spf

def factorize(n, spf):
    """SPF 链分解 → {prime: exponent}"""
    f = {}
    while n > 1:
        p = int(spf[n])
        e = 0
        while n % p == 0:
            n //= p
            e += 1
        f[p] = e
    return f

def brute_factor(n):
    """暴力试除（F0 对照基准）"""
    f = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        f[n] = f.get(n, 0) + 1
    return f

def phi_brute(n):
    return sum(1 for k in range(1, n + 1) if math.gcd(k, n) == 1)

# ---------- 签名计算 ----------
def signatures(fact):
    """输入因子分解 dict → 7 元签名"""
    Omega = sum(fact.values())
    omega = len(fact)
    v2 = fact.get(2, 0)
    v3 = fact.get(3, 0)
    v5 = fact.get(5, 0)
    v7 = fact.get(7, 0)
    lnphi_over_n = sum(e * math.log(1.0 - 1.0 / p) for p, e in fact.items())
    lnpmax = math.log(max(fact.keys()))
    return Omega, omega, v2, v3, v5, v7, lnphi_over_n, lnpmax

# ---------- F0 自检锚 ----------
def f0_selfcheck(spf):
    for n in range(2, 1001, 2):
        bf = brute_factor(n)
        sf = factorize(n, spf)
        assert bf == sf, f"F0 因子分解不符 N={n}: {bf} vs {sf}"
        # φ 对照：φ(N)/N = ∏(1-1/p)
        phib = phi_brute(n)
        phis = n
        for p in sf:
            phis = phis // p * (p - 1)
        assert phib == phis, f"F0 φ 不符 N={n}"
        # P(N) 对照
        assert max(bf.keys()) == max(sf.keys()), f"F0 P(N) 不符 N={n}"
    log("F0 自检锚：N<=1000 全部偶数因子分解/φ/P(N) 与暴力对照全对 → 继续")

# ---------- 统计工具 ----------
def ks_test(a, b):
    return stats.ks_2samp(a, b, alternative="two-sided")

def perm_test(a, b, n_perm=10000, seed=SEED):
    rng = np.random.default_rng(seed)
    pooled = np.concatenate([a, b]).astype(np.float64)
    na = len(a)
    obs = abs(a.mean() - b.mean())
    count = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        d = abs(pooled[:na].mean() - pooled[na:].mean())
        if d >= obs:
            count += 1
    return (count + 1) / (n_perm + 1)

def effect_d(a, b):
    ma, mb = a.mean(), b.mean()
    sa2, sb2 = a.var(ddof=1), b.var(ddof=1)
    na, nb = len(a), len(b)
    sp = math.sqrt(((na - 1) * sa2 + (nb - 1) * sb2) / (na + nb - 2))
    return abs(ma - mb) / sp if sp > 0 else 0.0

GROUPS = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]

def main():
    t0 = time.time()
    log(f"首跑时间 {time.strftime('%Y-%m-%d %H:%M:%S')}（判据书冻结 2026-09-20 00:31:05 NTFS 在先）")
    spf = spf_sieve(X_MAX)
    f0_selfcheck(spf)

    # 分片计算
    evens_all = np.arange(2, X_MAX + 1, 2)
    shards = np.array_split(evens_all, N_SHARDS)
    data = {}  # N -> 8 元 (r, Omega, omega, v2, v3, v5, v7, lnphi/n, lnpmax)
    for si, shard in enumerate(shards, 1):
        rows = []
        for N in shard:
            f = factorize(int(N), spf)
            sig = signatures(f)
            rows.append([int(N), int(N) % 24] + [float(x) if i >= 6 else int(x) for i, x in enumerate(sig)])
        data[si] = rows
        ck = RES / f"omega_negbound_checkpoint_{si}-{TAG}.json"
        ck.write_text(json.dumps({"shard": si, "n": len(rows), "rows": rows}, ensure_ascii=False), encoding="utf-8")
        log(f"片 {si}/{N_SHARDS} 完成（{len(rows)} 偶数），检查点落盘 {ck.name}")

    allrows = [r for si in range(1, N_SHARDS + 1) for r in data[si]]
    Ns = np.array([r[0] for r in allrows])
    rs = np.array([r[1] for r in allrows])
    sig = np.array([r[2:] for r in allrows])  # Ω,ω,v2,v3,v5,v7,lnφ/n,lnP
    names = ["Omega", "omega", "v2", "v3", "v5", "v7", "ln_phi_over_n", "ln_P"]
    log(f"总样本 {len(Ns)} 偶数，用时 {time.time()-t0:.1f}s")

    res = {"meta": {"script": "omega_factorization_negbound-v1.0-20260920.py",
                    "criterion_freeze_ntfs": "2026-09-20 00:31:05",
                    "first_run": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "X": X_MAX, "n_even": int(len(Ns)),
                    "signatures": names}}

    # ---------- F1：54 检验 ----------
    merge6 = {  # K1(a) 六类合并分拆
        (1, 0): [2, 10, 14, 22], (1, 1): [6, 18], (2, 0): [4, 20],
        (2, 1): [12], (3, 0): [8, 16], (3, 1): [0],
    }
    pair_list = []
    for cls, gs in merge6.items():
        for i in range(len(gs)):
            for j in range(i + 1, len(gs)):
                pair_list.append((gs[i], gs[j], cls))
    assert len(pair_list) == 9, len(pair_list)
    sig_idx = {"Omega": 0, "omega": 1, "v5": 4, "v7": 5, "ln_phi_over_n": 6, "ln_P": 7}
    f1 = []
    any_violation = False
    for sname, si_ in sig_idx.items():
        vals = sig[:, si_]
        for ga, gb, cls in pair_list:
            a = vals[rs == ga]; b = vals[rs == gb]
            ks = ks_test(a, b)
            pp = perm_test(a, b)
            d = effect_d(a, b)
            ok = (ks.pvalue > 0.01) and (pp > 0.01) and (d <= 0.05)
            if not ok:
                any_violation = True
            f1.append({"sig": sname, "pair": f"{ga}|{gb}", "class": f"{cls[0]},{cls[1]}",
                       "n_a": int(len(a)), "n_b": int(len(b)),
                       "mean_a": float(a.mean()), "mean_b": float(b.mean()),
                       "ks_D": float(ks.statistic), "ks_p": float(ks.pvalue),
                       "perm_p": float(pp), "d": float(d), "pass": bool(ok)})
    npass = sum(1 for t in f1 if t["pass"])
    pmin = min(t["ks_p"] for t in f1); pmin2 = min(t["perm_p"] for t in f1)
    dmax = max(t["d"] for t in f1)
    log(f"F1: {npass}/54 通过；min KS p={pmin:.4g} min perm p={pmin2:.4g} max d={dmax:.4g}")
    res["F1"] = {"n_tests": len(f1), "n_pass": npass, "min_ks_p": float(pmin),
                 "min_perm_p": float(pmin2), "max_d": float(dmax),
                 "any_violation": bool(any_violation), "tests": f1}

    # ---------- F2：三重锚 ----------
    v2v = sig[:, 2]; om = sig[:, 0]
    grp = lambda gs, v: np.concatenate([v[rs == g] for g in gs])
    a1 = {}
    g_v2_1 = [2, 10, 14, 22, 6, 18]; g_v2_2 = [4, 20, 12]; g_v2_3 = [0, 8, 16]
    a1["v2_eq1_exact"] = bool(np.all(v2v[np.isin(rs, g_v2_1)] == 1))
    a1["v2_eq2_exact"] = bool(np.all(v2v[np.isin(rs, g_v2_2)] == 2))
    v3g = grp(g_v2_3, v2v)
    a1["P_v2_3"] = float((v3g == 3).mean()); a1["P_v2_4"] = float((v3g == 4).mean())
    a1["mean_v2_ge3"] = float(v3g.mean())
    a1["pass"] = bool(a1["v2_eq1_exact"] and a1["v2_eq2_exact"]
                      and 0.48 <= a1["P_v2_3"] <= 0.52 and 0.23 <= a1["P_v2_4"] <= 0.27
                      and 3.9 <= a1["mean_v2_ge3"] <= 4.1)
    shifts = [
        ("{6,18}-{2,10,14,22}", [6, 18], [2, 10, 14, 22]),
        ("{12}-{4,20}", [12], [4, 20]),
        ("{0}-{8,16}", [0], [8, 16]),
    ]
    a2 = []
    for nm, g3, g1 in shifts:
        diff = float(grp(g3, om).mean() - grp(g1, om).mean())
        a2.append({"anchor": nm, "mean_diff": diff, "pass": bool(1.35 <= diff <= 1.65)})
    res["F2"] = {"v2_anchor": a1, "omega_shift": a2,
                 "pass": bool(a1["pass"] and all(x["pass"] for x in a2))}
    log(f"F2: v2锚={a1['pass']} Ω移位={[x['mean_diff'] for x in a2]}")

    # ---------- F3：可达性 ----------
    k2 = np.minimum(v2v, 3); k3 = (sig[:, 3] >= 1).astype(int)
    s0 = list(zip(k2.tolist(), k3.tolist()))
    well_defined = True
    grp_vals = {}
    for g in GROUPS:
        vs = set(s0[i] for i in np.where(rs == g)[0])
        if len(vs) != 1:
            well_defined = False
        grp_vals[g] = vs.pop() if len(vs) == 1 else None
    k1_table = {0: (3, 1), 8: (3, 0), 16: (3, 0), 12: (2, 1), 4: (2, 0), 20: (2, 0),
                6: (1, 1), 18: (1, 1), 2: (1, 0), 10: (1, 0), 14: (1, 0), 22: (1, 0)}
    match = all(grp_vals[g] == k1_table[g] for g in GROUPS)
    # 144 组对一致性
    pair_ok = 0
    for ga in GROUPS:
        for gb in GROUPS:
            same_cls = k1_table[ga] == k1_table[gb]
            same_sig = grp_vals[ga] == grp_vals[gb]
            if same_cls == same_sig:
                pair_ok += 1
    res["F3"] = {"well_defined": bool(well_defined), "matches_K1a": bool(match),
                 "pairwise_144": pair_ok, "pass": bool(well_defined and match and pair_ok == 144)}
    log(f"F3: 良定义={well_defined} 与K1(a)一致={match} 144对={pair_ok}")

    # ---------- F4：记录 ----------
    v5v = sig[:, 4]; v7v = sig[:, 5]
    f4 = {"v5_ge6_per_group": {str(g): int((v5v[rs == g] >= 6).sum()) for g in GROUPS},
          "v7_ge5_per_group": {str(g): int((v7v[rs == g] >= 5).sum()) for g in GROUPS}}
    res["F4"] = f4

    # ---------- F5 ----------
    f5 = bool(res["F1"]["n_pass"] == 54 and res["F2"]["pass"] and res["F3"]["pass"])
    res["F5_verdict"] = {"direction_sealed": f5,
                         "verdict": "方向封死（6/12 上界）" if f5 else "存在违背项→升级待判别"}
    log(f"F5 总裁决: {res['F5_verdict']}")

    out = RES / f"omega_factorization_negbound_result-{TAG}.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘 {out}")
    print(json.dumps({"F1": f"{res['F1']['n_pass']}/54", "F2": res["F2"]["pass"],
                      "F3": res["F3"]["pass"], "F5": res["F5_verdict"]["verdict"]},
                     ensure_ascii=False))

if __name__ == "__main__":
    main()
