# -*- coding: utf-8 -*-
"""
range_effect_and_8families-v1.0-20260920.py
判据书：《代数册·值域效应收敛律与8族对偶预注册判据书-v1.0-20260920.md》（NTFS 冻结 2026-09-20 01:10:53，先于本脚本首跑）
H0-H4：共因子值域效应 X-收敛律（X=2e6 vs 200000 已档值）；D0-D6：8 族奇数侧对偶实证。5 片检查点×2。
"""
import json, math, time
from pathlib import Path
import numpy as np
from scipy import stats

BASE = Path(r"H:\理论存档\01-数学")
RES = BASE / "02-实验与数据" / "results"
TAG = "v1.0-20260920"
X2 = 2_000_000
N_SHARDS = 5
SEED = 20260920

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def spf_sieve(n):
    spf = np.zeros(n + 1, dtype=np.int64); spf[1] = 1
    for i in range(2, n + 1):
        if spf[i] == 0:
            spf[i::i][spf[i::i] == 0] = i
    return spf

def factorize(n, spf):
    f = {}
    while n > 1:
        p = int(spf[n]); e = 0
        while n % p == 0: n //= p; e += 1
        f[p] = e
    return f

def brute_factor(n):
    f = {}; d = 2
    while d * d <= n:
        while n % d == 0: f[d] = f.get(d, 0) + 1; n //= d
        d += 1
    if n > 1: f[n] = f.get(n, 0) + 1
    return f

def carries(a, b, base, digits):
    n = 0; ca = 0
    for _ in range(digits):
        s = (a % base) + (b % base) + ca
        a //= base; b //= base
        if s >= base: n += 1; ca = 1
        else: ca = 0
    return n

def S_m(r, base, m):
    M = base ** m; cnt = {}
    for k in range(M):
        c = carries(k, (r - k) % M, base, m)
        cnt[c] = cnt.get(c, 0) + 1
    return tuple(cnt.get(j, 0) for j in range(M + 2))

def s_digits(n, base):
    s = 0
    while n > 0: s += n % base; n //= base
    return s

def effect_d(a, b):
    na, nb = len(a), len(b)
    sp = math.sqrt(((na-1)*a.var(ddof=1) + (nb-1)*b.var(ddof=1)) / (na+nb-2))
    return abs(a.mean()-b.mean())/sp if sp > 0 else 0.0

def main():
    t0 = time.time()
    log(f"首跑时间 {time.strftime('%Y-%m-%d %H:%M:%S')}（判据书冻结 2026-09-20 01:10:53 NTFS 在先）")
    res = {"meta": {"criterion_freeze_ntfs": "2026-09-20 01:10:53",
                    "first_run": time.strftime("%Y-%m-%d %H:%M:%S"), "X2": X2}}
    spf = spf_sieve(X2)
    log(f"筛完成 {time.time()-t0:.1f}s")
    # H0/D0 自检
    ok = True
    for n in range(2, 1001):
        bf = brute_factor(n); sf = factorize(n, spf)
        if bf != sf: ok = False; break
        ph = sum(1 for k in range(1, n+1) if math.gcd(k, n) == 1)
        ps = n
        for p in sf: ps = ps // p * (p - 1)
        if ph != ps: ok = False; break
    units = [r for r in range(1, 24) if math.gcd(r, 24) == 1]
    res["H0_D0"] = {"selfcheck": bool(ok), "units": units, "pass": bool(ok and len(units) == 8)}
    log(f"H0/D0 自检: {ok}; 八单位类 {units}")

    evens = np.arange(2, X2 + 1, 2)
    odds = np.arange(1, X2 + 1, 2)
    se = np.array_split(evens, N_SHARDS); so = np.array_split(odds, N_SHARDS)
    E_rows, O_rows = [], []
    for si in range(N_SHARDS):
        er = []
        for N in se[si]:
            f = factorize(int(N), spf)
            er.append([int(N), int(N) % 24, sum(f.values()), len(f), int(f.get(2,0)), int(f.get(3,0)),
                       sum(e for p, e in f.items() if p >= 5),
                       sum(e*math.log(1-1/p) for p, e in f.items())])
        ck = RES / f"range_effect_checkpoint_{si+1}-{TAG}.json"
        ck.write_text(json.dumps({"shard": si+1, "rows": er}, ensure_ascii=False), encoding="utf-8")
        E_rows += er
        orows = []
        for N in so[si]:
            f = factorize(int(N), spf)
            orows.append([int(N), int(N) % 24, sum(f.values()), len(f),
                          sum(e*math.log(1-1/p) for p, e in f.items()),
                          s_digits(int(N), 2), s_digits(int(N), 3)])
        ck2 = RES / f"families8_checkpoint_{si+1}-{TAG}.json"
        ck2.write_text(json.dumps({"shard": si+1, "rows": orows}, ensure_ascii=False), encoding="utf-8")
        O_rows += orows
        log(f"片 {si+1}/{N_SHARDS} 双落盘（偶 {len(er)} / 奇 {len(orows)}）")
    log(f"分解总用时 {time.time()-t0:.1f}s")

    # ---------- H 组 ----------
    E = np.array(E_rows)
    r = E[:,1].astype(int); om = E[:,2].astype(float); v2 = E[:,4].astype(float); v3 = E[:,5].astype(float); R = E[:,6].astype(float)
    k1t = {0:24, 8:8, 16:8, 12:12, 4:4, 20:4, 6:6, 18:6, 2:2, 10:2, 14:2, 22:2}
    cs = sorted(set(k1t.values()))
    Rbar = {}
    for c in cs:
        gs = [g for g in k1t if k1t[g] == c]
        m = np.isin(r, gs)
        Rbar[c] = float(R[m].mean())
    mono = all(Rbar[cs[i]] > Rbar[cs[i+1]] for i in range(len(cs)-1))
    spread2M = Rbar[2] - Rbar[24]
    shifts2M = {}
    grp = lambda gs, v: np.concatenate([v[np.isin(r, [g]) ] for g in gs]) if len(gs) > 1 else v[r == gs[0]]
    pairs = [([6,18],[2,10,14,22]), ([12],[4,20]), ([0],[8,16])]
    for nm, g3, g1 in [("{6,18}-{2,10,14,22}",[6,18],[2,10,14,22]), ("{12}-{4,20}",[12],[4,20]), ("{0}-{8,16}",[0],[8,16])]:
        shifts2M[nm] = float(grp(g3, om).mean() - grp(g1, om).mean())
    shift_prev = {"{6,18}-{2,10,14,22}": 1.3532714171564826, "{12}-{4,20}": 1.3431533193409093, "{0}-{8,16}": 1.3143443047375705}
    H1 = mono
    H2 = (0.60*0.3732 <= spread2M < 0.3732)
    H3 = all(shifts2M[k] > shift_prev[k] and 1.34 <= shifts2M[k] <= 1.49 for k in shifts2M)
    # H4 线性拟合
    x = np.array([math.log(math.log(X2/c)) for c in cs]); y = np.array([Rbar[c] for c in cs])
    A = np.vstack([x, np.ones_like(x)]).T
    coef, res_, *_ = np.linalg.lstsq(A, y, rcond=None)
    yhat = A @ coef; ss_res = float(((y-yhat)**2).sum()); ss_tot = float(((y-y.mean())**2).sum())
    r2 = 1 - ss_res/ss_tot
    res["H"] = {"Rbar_2M": {str(c): round(v,4) for c,v in Rbar.items()},
                "Rbar_200k_ref": {"2":2.0527,"4":1.9932,"6":1.9038,"8":1.8625,"12":1.8364,"24":1.6778},
                "H1_monotone": bool(H1), "H2": {"spread_2M": round(spread2M,4), "spread_200k": 0.3732, "pass": bool(H2)},
                "H3": {"shifts_2M": {k: round(v,4) for k,v in shifts2M.items()}, "pass": bool(H3)},
                "H4_fit": {"slope": round(float(coef[0]),4), "intercept": round(float(coef[1]),4), "R2": round(r2,4),
                           "residuals": {str(c): round(float(y[i]-yhat[i]),4) for i,c in enumerate(cs)}},
                "pass_H1H2H3": bool(H1 and H2 and H3)}
    log(f"H1={H1} H2={H2} (spread 2M={spread2M:.4f} vs 200k=0.3732) H3={H3} shifts={shifts2M}")
    log(f"H4 拟合: 斜率={coef[0]:.4f} R2={r2:.4f} 残差={ {c: round(float(y[i]-yhat[i]),4) for i,c in enumerate(cs)} }")

    # ---------- D 组 ----------
    O = np.array(O_rows)
    ro = O[:,1].astype(int); omg = O[:,2].astype(float); ome = O[:,3].astype(float)
    lphi = O[:,4].astype(float); s2v = O[:,5].astype(float); s3v = O[:,5]*0
    s3v = O[:,6].astype(float)
    sigs = {"Omega": omg, "omega": ome, "ln_phi_over_n": lphi}
    d1 = []; d1_ok = True
    for sn, vals in sigs.items():
        for i in range(8):
            for j in range(i+1, 8):
                a = vals[ro == units[i]]; b = vals[ro == units[j]]
                p = float(stats.ks_2samp(a, b, alternative="two-sided").pvalue)
                d = float(effect_d(a, b))
                okk = p > 0.01 and d <= 0.05
                d1_ok &= okk
                d1.append({"sig": sn, "pair": f"{units[i]}|{units[j]}", "ks_p": p, "d": d, "pass": okk})
    s3bin = {g: S_m(g, 2, 3) for g in units}; s3_1 = {g: S_m(g % 3, 3, 1) for g in units}
    D2 = sum(1 for ga in units for gb in units if (s3bin[ga] == s3bin[gb]) == ((ga % 8) == (gb % 8)))
    D3 = sum(1 for ga in units for gb in units if (s3_1[ga] == s3_1[gb]) == ((ga % 3) == (gb % 3)))
    joint = {g: (s3bin[g], s3_1[g]) for g in units}
    D4 = sum(1 for ga in units for gb in units if (joint[ga] == joint[gb]) == (ga == gb))
    ncls = len(set(joint.values()))
    # D5
    m8cls = {}
    for g in units: m8cls.setdefault(g % 8, []).append(g)
    d5a = []
    for c, gs in m8cls.items():
        a = s2v[ro == gs[0]]; b = s2v[ro == gs[1]]
        p = float(stats.ks_2samp(a, b, alternative="two-sided").pvalue)
        d5a.append({"pair": f"{gs[0]}|{gs[1]}", "ks_p": p, "inseparable": bool(p > 0.01)})
    a115 = s2v[np.isin(ro, [1,17])]; a723 = s2v[np.isin(ro, [7,23])]
    diff17 = float(a723.mean() - a115.mean())
    a1119 = s2v[np.isin(ro, [11,19])]; a513 = s2v[np.isin(ro, [5,13])]
    p35 = float(stats.ks_2samp(a1119, a513, alternative="two-sided").pvalue)
    cls1 = s3v[np.isin(ro, [g for g in units if g % 3 == 1])]
    cls2 = s3v[np.isin(ro, [g for g in units if g % 3 == 2])]
    psep = float(stats.ks_2samp(cls1, cls2, alternative="two-sided").pvalue)
    shiftD5 = float(cls2.mean() - cls1.mean())
    d5d = []
    for par, gs in [(1, [g for g in units if g % 3 == 1]), (2, [g for g in units if g % 3 == 2])]:
        for i in range(len(gs)):
            for j in range(i+1, len(gs)):
                a = s3v[ro == gs[i]]; b = s3v[ro == gs[j]]
                p = float(stats.ks_2samp(a, b, alternative="two-sided").pvalue)
                d5d.append({"pair": f"{gs[i]}|{gs[j]}", "ks_p": p, "inseparable": bool(p > 0.01)})
    D5 = {"s2_within_inseparable": all(x["inseparable"] for x in d5a),
          "s2_layer_17v723_diff": diff17, "s2_layer_1119v513_ks_p": p35,
          "s3_class_sep_ks_p": psep, "s3_class_shift_2minus1": shiftD5,
          "s3_within_inseparable": sum(x["inseparable"] for x in d5d), "s3_within_total": len(d5d)}
    res["D"] = {"D1": {"n": len(d1), "n_pass": sum(1 for t in d1 if t["pass"]), "pass": bool(d1_ok),
                       "min_ks_p": min(t["ks_p"] for t in d1), "max_d": max(t["d"] for t in d1)},
                "D2_64": int(D2), "D3_64": int(D3), "D4": {"classes": ncls, "pairwise_64": int(D4)},
                "D5": D5}
    log(f"D1: {res['D']['D1']['n_pass']}/84 盲性；D2={D2}/64 D3={D3}/64 D4={ncls}类 {D4}/64")
    log(f"D5: {D5}")
    verdict = res["H"]["pass_H1H2H3"] and res["H0_D0"]["pass"] and d1_ok and D2 == 64 and D3 == 64 and ncls == 8 and D4 == 64
    res["verdict"] = {"H_pass": bool(res["H"]["pass_H1H2H3"]), "D_pass": bool(d1_ok and D2 == 64 and D3 == 64 and ncls == 8 and D4 == 64)}
    out = RES / f"range_effect_and_8families_result-{TAG}.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    d1dump = RES / f"range_effect_and_8families_D1tests-{TAG}.json"
    d1dump.write_text(json.dumps(d1, ensure_ascii=False), encoding="utf-8")
    log(f"结果落盘 {out}，总用时 {time.time()-t0:.1f}s")
    print(json.dumps({"H": res["H"]["pass_H1H2H3"], "D1": res["D"]["D1"]["n_pass"], "D2": D2, "D3": D3, "D4": f"{ncls}cls/{D4}"}, ensure_ascii=False))

if __name__ == "__main__":
    main()
