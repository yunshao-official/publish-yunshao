# -*- coding: utf-8 -*-
# DblTau 奇偶普适纸面化（R30 主格二·判据书 D-Z 系实算）
# 判据书：代数册·d±2余项解析与奇偶不变量定理化预注册判据书-v1.0-20260924.md（冻结 2026-09-24 03:29:44）
# 口径：D-Z0 递推核回归（暴力逐位对照 Y<=2000+随机 1e5 点）+72 档 μ/Σ 对照 R29 JSON
#       D-Z1 奇偶不变量 M-X1 全域 4^12 逐态验证：chi(Y)=D(Y)+f(m(Y)) mod 2 == 0（整数零容差）
#       D-Z2 DblTau(c)⊆{mu(c)} 全 72 档机器断言+Σ 谱恒等+R29 dbltau_universality 复核（终裁合成）
#       D-Z3 m=0 无约束双向记录（存在 D 偶/奇 m=0 态各 >=1）
# 器口径复用 R29 mu_parity_theorem（build_D_table 逐层 numpy）。
import json, argparse
import numpy as np

K = 12
N4 = 4 ** K
G = [[0,0,0],[0,1,-1],[-1,2,-1],[0,2,-2]]
SIGN = [1,-1,-1,1]
R29_REG = "H:/理论存档/01-数学/02-实验与数据/results/mu_parity_theorem-reg-v1.0-20260924.json"
R29_EXT = "H:/理论存档/01-数学/02-实验与数据/results/mu_parity_theorem-ext8-v1.0-20260924.json"
R29_UNI = "H:/理论存档/01-数学/02-实验与数据/results/mu_parity_dbltau_universality-v1.0-20260924.json"
OUT = "H:/理论存档/01-数学/02-实验与数据/results/parity_invariant-%s-v1.0-20260924.json"

def s2(n): return bin(n).count("1")

def build_tables():
    """全域 D(Y), tau(Y), m(Y)（递推核逐层 numpy·R29 口径）"""
    g = np.array(G, dtype=np.int64)
    sr = np.array([s2(r) & 1 for r in range(4)], dtype=np.int64)
    rr = np.arange(4, dtype=np.int64)
    Darr = np.zeros(N4, dtype=np.int64)
    parr = np.zeros(N4, dtype=np.int8)
    marr = np.zeros(N4, dtype=np.int8)
    lo = 1
    while lo < N4:
        hi = min(lo*4, N4)
        Zs = np.arange(lo, hi, dtype=np.int64) >> 2
        rs = np.arange(lo, hi, dtype=np.int64) & 3
        Darr[lo:hi] = 3*Darr[Zs] + ((-1) ** parr[Zs].astype(np.int64)) * g[rs, marr[Zs]]
        parr[lo:hi] = parr[Zs] ^ sr[rs]
        marr[lo:hi] = (marr[Zs] + rr[rs]) % 3
        lo = hi
    return Darr, parr, marr

def brute_state(Y):
    """暴力逐位（独立实现·D-Z0 对照正本）：Y 的 4 进制位逐个应用 step"""
    d, sg, m = 0, 1, 0
    digits = []
    if Y == 0:
        return (0, 1, 0)
    while Y:
        digits.append(Y & 3)
        Y >>= 2
    for rho in reversed(digits):
        d, sg, m = 3*d + sg*G[rho][m], sg*SIGN[rho], (m + rho) % 3
    return (d, sg, m)

def mu_of(c):
    return 1 if c % 2 == 0 else 2

def sigma_from_tables(Darr, parr, marr, c):
    """Σ(c)={(τ,m): D(Y)=c}（全域 4^12 聚合·τ=+1 if parr==0 else -1）"""
    idx = np.nonzero(Darr == c)[0]
    if idx.size == 0:
        return set()
    taus = np.where(parr[idx] == 0, 1, -1)
    ms = marr[idx].astype(np.int64)
    return set(zip(taus.tolist(), ms.tolist()))

def dbltau_from_sigma(sig):
    return sorted({m for (t, m) in sig if m in (1, 2) and (1, m) in sig and (-1, m) in sig})

def run_part1():
    log = []
    print("building tables (4^12)...")
    Darr, parr, marr = build_tables()
    log.append("tables built")
    # D-Z0：递推核回归（暴力对照）
    bad = []
    for Y in range(2000):
        b = brute_state(Y)
        if b[0] != int(Darr[Y]) or b[1] != (1 if parr[Y] == 0 else -1) or b[2] != int(marr[Y]):
            bad.append(("seq", Y))
    rng = np.random.default_rng(20260924)
    for Y in rng.integers(0, N4, size=100000):
        Y = int(Y)
        b = brute_state(Y)
        if b[0] != int(Darr[Y]) or b[1] != (1 if parr[Y] == 0 else -1) or b[2] != int(marr[Y]):
            bad.append(("rnd", Y))
    log.append("D-Z0 brute-check bad=%d (2000 sequential + 100000 random)" % len(bad))
    # D-Z1：奇偶不变量全域验证（f(0)=0, f(1)=0, f(2)=1）
    farr = (marr == 2).astype(np.int64)
    chi = (Darr + farr) & 1
    bad_idx = np.nonzero(chi != 0)[0]
    n_bad = int(bad_idx.size)
    bad_sample = [int(x) for x in bad_idx[:10].tolist()]
    log.append("D-Z1 invariant violations=%d sample=%s" % (n_bad, bad_sample))
    # D-Z3：m=0 无约束双向记录
    m0 = (marr == 0)
    d_even_m0 = int(np.count_nonzero(m0 & (Darr % 2 == 0)))
    d_odd_m0 = int(np.count_nonzero(m0 & (Darr % 2 != 0)))
    log.append("D-Z3 m=0 states: D even=%d, D odd=%d" % (d_even_m0, d_odd_m0))
    # 覆盖统计（记录级）
    n_m1 = int(np.count_nonzero(marr == 1)); n_m2 = int(np.count_nonzero(marr == 2))
    log.append("coverage: |Y|=%d, m=1: %d, m=2: %d, m=0: %d" % (N4, n_m1, n_m2, N4 - n_m1 - n_m2))
    res = {"meta": {"script": "parity_invariant-v1.0-20260924.py", "frozen": "2026-09-24T03:29:44"},
           "DZ0": {"bad": bad[:20], "n_bad": len(bad)},
           "DZ1": {"n_violations": n_bad, "sample": bad_sample},
           "DZ3": {"d_even_m0": d_even_m0, "d_odd_m0": d_odd_m0},
           "coverage": {"m1": n_m1, "m2": n_m2, "m0": N4 - n_m1 - n_m2},
           "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

def run_part2():
    log = []
    print("building tables (4^12)...")
    Darr, parr, marr = build_tables()
    # 72 档 Σ 谱重算 + DblTau⊆{μ} 断言 + 对照 R29 JSON
    r29reg = json.load(open(R29_REG, encoding="utf-8"))
    r29ext = json.load(open(R29_EXT, encoding="utf-8"))
    r29uni = json.load(open(R29_UNI, encoding="utf-8"))
    sigma_bad = []; subset_bad = []; dbltau_tab = {}
    n_nonempty = 0
    for c in range(0, -72, -1):
        sig = sigma_from_tables(Darr, parr, marr, c)
        dt = dbltau_from_sigma(sig)
        dbltau_tab["c(%d)" % c] = dt
        if dt:
            n_nonempty += 1
        # DblTau ⊆ {μ(c)}（M-X1 推论机器面）
        if not set(dt).issubset({mu_of(c)}):
            subset_bad.append((c, dt))
        # Σ 谱对照（R29 64 档 reg + 8 档 ext）
        key = "c(%d)" % c
        ref = None
        if key in r29reg.get("entries", {}):
            ref = r29reg["entries"][key].get("sigma")
        elif key in r29ext.get("entries", {}):
            ref = r29ext["entries"][key].get("sigma")
        if ref is not None:
            got = sorted([[t, m] for (t, m) in sig])
            ref_s = sorted([list(x[0]) for x in ref])
            if got != ref_s:
                sigma_bad.append((c, got, ref_s))
    log.append("72-c nonempty DblTau=%d; subset violations=%d; sigma mismatch=%d"
               % (n_nonempty, len(subset_bad), len(sigma_bad)))
    # R29 dbltau_universality 直读复核
    uni_checked = r29uni.get("checked"); uni_bad = r29uni.get("bad")
    log.append("R29 universality JSON: checked=%s bad=%s" % (uni_checked, uni_bad))
    # 总裁决合成
    p1 = json.load(open(OUT % "part1", encoding="utf-8"))
    dz1_ok = p1["DZ1"]["n_violations"] == 0
    dz0_ok = p1["DZ0"]["n_bad"] == 0
    verdict = bool(dz0_ok and dz1_ok and not subset_bad and not sigma_bad
                   and uni_checked == 63 and uni_bad == [])
    log.append("D-Z2 VERDICT: M-X1 corollary DblTau⊆{mu(c)} theorem-ization = %s" % verdict)
    res = {"meta": {"script": "parity_invariant-v1.0-20260924.py", "frozen": "2026-09-24T03:29:44"},
           "dbltau_table": dbltau_tab, "n_nonempty": n_nonempty,
           "subset_bad": subset_bad, "sigma_bad": sigma_bad[:10],
           "r29_universality": {"checked": uni_checked, "bad": uni_bad},
           "verdict": verdict, "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    a = ap.parse_args()
    {1: run_part1, 2: run_part2}[a.part]()

if __name__ == "__main__":
    main()
