# -*- coding: utf-8 -*-
# 峰位轨迹族一般化（R28 主格二·判据书 D-G 系实算）
# 判据书：代数册·Mint降层链完全性与峰位轨迹族一般化预注册判据书-v1.0-20260921.md（冻结 12:01:04）
# 口径：四对组 (10,22)基线/(2,20)/(8,14)/(4,10)；k 奇 {3,5,7,9,11,13}；mpmath 50 位；
#       D-G0 基线复现+锚 / D-G1 系数结构 / D-G2 σρ 驻点普适 / D-G3 新对轨迹+√律拟合+P-G 记账。
import json
import numpy as np
from mpmath import mp, mpf, exp, pi, cos, sin, sqrt

mp.dps = 50
PI = pi

PAIRS = [(10, 22), (2, 20), (8, 14), (4, 10)]
KS = [3, 5, 7, 9, 11, 13]

def c_of(r): return (r - (r % 3)) // 3 % 8

def build_S(k, t):
    p = (k + 1) // 2; q = k // 2
    tt = exp(1j * t)
    out = []
    for c in range(8):
        tot = mp.mpc(0)
        for m in range(8):
            zm = exp(-1j * pi / 4 * (m % 8))
            z3m = exp(-1j * pi / 4 * ((3 * m) % 8))
            tot += exp(1j * pi / 4 * ((m * c) % 8)) * (1 + zm*tt + zm**2*tt**2)**p \
                   * (1 + z3m*tt + z3m**2*tt**2)**q
        out.append(tot / 8)
    return out

def dphi_val(k, r, rp, t, Sc=None, Mc=None):
    c, cp = c_of(r), c_of(rp)
    M = (3**k - 3) // 8
    if Sc is None:
        Sc = build_S(k, t); Mc = [c2 for c2 in range(8)]
    Nc = M + 1 if c in (0, 1) else M
    Ncp = M + 1 if cp in (0, 1) else M
    return abs(exp(1j * (r % 3) * t) * (Sc[c]/Nc - Sc[cp]/Ncp))

def grid_peak(k, r, rp, N=2**18):
    ts = np.linspace(0, 2*np.pi, N, endpoint=False)
    x = np.exp(1j*ts)
    p = (k+1)//2; q = k//2
    w = np.conj(np.exp(2j*np.pi/8))
    Am = [1 + x*(w**m) + x*x*(w**(2*m)) for m in range(8)]
    M = (3**k - 3)//8
    Sc = {}
    for c in range(8):
        acc = np.zeros_like(x)
        for m in range(8):
            acc += np.exp(1j*np.pi/4*((m*c) % 8)) * (Am[m]**p) * (Am[(3*m) % 8]**q)
        Sc[c] = acc/8
    c, cp = c_of(r), c_of(rp)
    Nc = M+1 if c in (0,1) else M; Ncp = M+1 if cp in (0,1) else M
    d = np.abs(np.exp(1j*(r % 3)*ts) * (Sc[c]/Nc - Sc[cp]/Ncp))
    return float(ts[int(np.argmax(d))])

def refine(k, r, rp, rep, rounds=80):
    lo = mpf(rep) - mpf('1e-3'); hi = mpf(rep) + mpf('1e-3')
    f = lambda tt: dphi_val(k, r, rp, tt)
    for _ in range(rounds):
        m1 = lo + (hi-lo)/3; m2 = hi - (hi-lo)/3
        if f(m1) < f(m2): lo = m1
        else: hi = m2
    return (lo+hi)/2

def orbit_fold(t):
    p = float(pi)
    cands = [t % (2*p), (p-t) % (2*p), (t+p) % (2*p), (2*p-t) % (2*p)]
    for x in cands:
        if p/2 < x < p: return x
    return None

def deriv_check(k, r, rp, h=mpf('1e-6')):
    """|dphi|'(pi/2) 中心差分 + sigma-rho 对称偏差"""
    t0 = pi/2
    fp = dphi_val(k, r, rp, t0+h); fm = dphi_val(k, r, rp, t0-h)
    f0 = dphi_val(k, r, rp, t0)
    return float((fp-fm)/(2*h)), float(abs(fp-fm)), float(f0)

def main():
    res = {"meta": {}, "DG0": {}, "DG1": {}, "DG2": {}, "DG3": {}, "notes": {}}
    def L(m):
        print(m, flush=True)

    L("== D-G1 系数结构 ==")
    zeta = exp(2j*pi/8)
    dg1 = {}
    for (r, rp) in PAIRS:
        c, cp = c_of(r), c_of(rp)
        d = (cp - c) % 8
        coefs = {}
        ok = True
        for m in range(8):
            v = abs(1 - zeta**(m*d))
            target = 0.0 if (d == 4 and m % 2 == 0) else (2.0 if (d == 4) else
                     (2.0 if (d % 4 == 2 and m in (2, 6)) else
                     (0.0 if (d % 4 == 2 and m in (0, 4)) else sqrt(2) if d % 4 == 2 else None)))
            if target is None:
                ok = False
            else:
                err = abs(v - mpf(target))
                if err > mpf('1e-30'): ok = False
            coefs[m] = float(v)
        dg1["%d|%d" % (r, rp)] = {"c": c, "cp": cp, "d": d, "coefs_abs": coefs, "pass": ok}
        L("%d|%d d=%d coefs=%s pass=%s" % (r, rp, d, {m: round(v,6) for m,v in coefs.items()}, ok))
    res["DG1"] = dg1

    L("== D-G0 基线复现 + 全对峰位 ==")
    peaks = {}
    for (r, rp) in PAIRS:
        key = "%d|%d" % (r, rp)
        peaks[key] = {}
        for k in KS:
            g = grid_peak(k, r, rp)
            tref = refine(k, r, rp, mpf(g))
            fold = orbit_fold(float(tref % (2*float(pi))))
            entry = {"t_star": float(tref)}
            if fold is not None:
                t2 = refine(k, r, rp, mpf(fold))
                f2 = orbit_fold(float(t2 % (2*float(pi))))
                if f2 is not None:
                    entry["t_hat"] = float(f2)
            else:
                entry["t_hat"] = None
                entry["fold_cands"] = [float(x) for x in
                    [tref % (2*float(pi)), (float(pi)-tref) % (2*float(pi)),
                     (tref+float(pi)) % (2*float(pi)), (2*float(pi)-tref) % (2*float(pi))]]
            peaks[key][str(k)] = entry
            L("%s k=%d t*=%.12f t_hat=%s" % (key, k, entry["t_star"], entry.get("t_hat")))
    res["meta"]["peaks"] = peaks

    base = peaks["10|22"]
    dg0 = {}
    ref6 = {"5": 2.038761, "7": 1.969607, "9": 1.921042, "11": 1.886854, "13": 1.861055, "15": 1.840694}
    # 六点中 k=13 在本轮 KS；k=5..11 复现；k=15 另算（补）
    g15 = grid_peak(15, 10, 22); t15 = refine(15, 10, 22, mpf(g15))
    f15 = orbit_fold(float(t15 % (2*float(pi)))); f15 = orbit_fold(float(refine(15,10,22,mpf(f15)) % (2*float(pi))))
    dg0["t15_recompute"] = float(f15)
    for k, v in ref6.items():
        got = base["13"]["t_hat"] if k == "13" else (float(f15) if k == "15" else base[k]["t_hat"])
        if got is not None:
            dg0["rep_k%s" % k] = {"ref": v, "got": got, "absdiff": abs(got - v), "pass": abs(got-v) <= 1e-6}
    dg0["anchor_k3"] = {"ref": 2.356194490192345, "got": base["3"]["t_hat"],
                        "absdiff": abs(base["3"]["t_hat"] - 2.356194490192345),
                        "pass": abs(base["3"]["t_hat"] - 2.356194490192345) <= 1e-4}
    # k=21,23 锚（修正重跑：初值=R26/R27 口径 2^18 全域 argmax，不用候选点把戏）
    for k, anch in [(21, 1.798407861079), (23, 1.788185124572)]:
        g = grid_peak(k, 10, 22)
        t = refine(k, 10, 22, mpf(g), rounds=90)
        f = orbit_fold(float(t % (2*float(pi))))
        dg0["anchor_k%d" % k] = {"ref": anch, "got": float(f),
                                 "absdiff": abs(float(f)-anch), "pass": abs(float(f)-anch) <= 1e-9}
    res["DG0"] = dg0
    L("DG0: %s" % json.dumps({k2: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk != 'got'}) for k2, v in dg0.items()}))

    L("== D-G2 sigma-rho 驻点普适 ==")
    dg2 = {}
    allpass = True
    for (r, rp) in PAIRS:
        key = "%d|%d" % (r, rp)
        dg2[key] = {}
        for k in KS:
            dv, sym, f0 = deriv_check(k, r, rp)
            ok = abs(dv) <= 1e-8
            allpass = allpass and ok
            dg2[key][str(k)] = {"deriv": dv, "sym_dev": sym, "f_pi2": f0, "pass": ok}
        L("%s derivs=%s" % (key, {k2: round(v["deriv"], 12) for k2, v in dg2[key].items()}))
    res["DG2"] = dg2
    res["notes"]["DG2_all_pass"] = allpass

    L("== D-G3 新对轨迹 + sqrt 律拟合 ==")
    dg3 = {}
    # 基线 sqrt 拟合对照（k=5..13 五点，q=(k-1)/2）
    def sqrt_fit(ks, that_map):
        qs = [mpf((k-1)//2) for k in ks]
        ys = [mpf(that_map[k]) for k in ks]
        n = len(ks)
        b1 = [1/sqrt(q) for q in qs]; b2 = [1/q for q in qs]
        # 最小二乘 2x2 正规方程
        S11 = sum(x*x for x in b1); S12 = sum(x*y for x, y in zip(b1, b2)); S22 = sum(y*y for y in b2)
        T1 = sum(x*y2 for x, y2 in zip(b1, ys)); T2 = sum(y*y2 for y, y2 in zip(b2, ys))
        det = S11*S22 - S12*S12
        A = (T1*S22 - T2*S12)/det; B = (S11*T2 - S12*T1)/det
        mx = max(abs(A*x + B*y - y2)/abs(y2) for x, y, y2 in zip(b1, b2, ys))
        return float(A), float(B), float(mx)
    base_map = {k: base[str(k)]["t_hat"] for k in KS if base[str(k)]["t_hat"] is not None}
    if 15 in base_map or True:
        pass
    base_map[15] = float(f15)
    ks5 = [5, 7, 9, 11, 13]
    A, B, mx = sqrt_fit(ks5, {k: base_map[k] for k in ks5})
    dg3["baseline_10|22_sqrtfit"] = {"A": A, "B": B, "max_rel": mx,
                                     "pass_band": mx <= 0.05}
    L("baseline sqrtfit A=%.6f B=%.6f max_rel=%.6f" % (A, B, mx))
    pg_hits = {"PG1": None, "PG2_count": 0}
    for key in ["2|20", "8|14", "4|10"]:
        pk = peaks[key]
        tmap = {k: pk[str(k)]["t_hat"] for k in KS if pk[str(k)]["t_hat"] is not None}
        rec = {"t_hat_map": tmap, "raw_k3": pk["3"]["t_star"], "raw_k5": pk["5"]["t_star"]}
        if 5 in tmap:
            rec["PG1_t5_vs_pi2"] = abs(tmap[5] - float(pi/2))
            if key == "2|20":
                pg_hits["PG1"] = bool(abs(tmap[5] - float(pi/2)) <= 1e-6)
        if all(k in tmap for k in ks5):
            A2, B2, mx2 = sqrt_fit(ks5, {k: tmap[k] for k in ks5})
            rec["sqrtfit"] = {"A": A2, "B": B2, "max_rel": mx2}
            if mx2 > 0.20: pg_hits["PG2_count"] += 1
        dg3[key] = rec
        L("%s t_hat=%s" % (key, {k: round(v, 9) for k, v in tmap.items()}))
    dg3["P_G"] = pg_hits
    res["DG3"] = dg3

    outp = "H:/理论存档/01-数学/02-实验与数据/results/peak_family_general-v1.0-20260921.json"
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    L("saved %s" % outp)

if __name__ == "__main__":
    main()
