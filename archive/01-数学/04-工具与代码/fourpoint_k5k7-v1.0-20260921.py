# -*- coding: utf-8 -*-
"""R23 候补格·四点峰 k=5/7 推广定位 判据 Q0-Q5 实算（v1.0 正式版）
判据书：代数册·四点峰k5k7推广定位预注册判据书-v1.0-20260921.md（冻结 05:53:04 在先）
口径：2^20 double 网格+mpmath 三分细化 1e-12；对称性网格判定；判负照记。路径正斜杠。"""
import json, time
import numpy as np
from mpmath import mp, mpf, exp as mpexp, pi as mppi, cos as mpcos, sin as mpsin, mpc

mp.dps = 50
T0 = time.time()
LOG = []
def log(msg):
    LOG.append(msg)
    print(msg, flush=True)

res = {"meta": {"script": "fourpoint_k5k7-v1.0-20260921.py",
                 "frozen_at": "2026-09-21 05:53:04", "start": time.strftime("%H:%M:%S")}}

def build_Pi_coeffs(k):
    """Π_m 系数（复 float，长度 2k+1），m=0..7"""
    zeta = np.exp(2j*np.pi/8)
    p = (k+1)//2; q = k//2
    def polymul(a, b):
        c = np.zeros(len(a)+len(b)-1, dtype=complex)
        for i, va in enumerate(a):
            c[i:i+len(b)] += va*b
        return c
    def polypow(a, e):
        r = np.array([1.0+0j])
        b = a
        while e:
            if e & 1: r = polymul(r, b)
            b = polymul(b, b); e >>= 1
        return r
    Pis = []
    for m in range(8):
        Am = np.array([1.0, zeta**(-m), zeta**(-2*m)])
        A3 = np.array([1.0, zeta**(-3*m), zeta**(-6*m)])
        Pis.append(polymul(polypow(Am, p), polypow(A3, q)))
    return Pis

def S_from_Pi(Pis, k):
    zeta = np.exp(2j*np.pi/8)
    S = []
    for c in range(8):
        acc = np.zeros(2*k+1, dtype=complex)
        for m in range(8):
            acc += (zeta**(m*c)) * Pis[m][:2*k+1]
        S.append(acc/8)
    return S

def eval_poly(coeffs, t):
    x = np.exp(1j*np.asarray(t))
    r = np.zeros_like(x)
    for cf in coeffs[::-1]:
        r = r*x + cf
    return r

NGRID = 1 << 20
tgrid = np.linspace(0, 2*np.pi, NGRID, endpoint=False)

def refine_peak(fn_mp, t_lo, t_hi, iters=90):
    """三分细化（mpmath）"""
    for _ in range(iters):
        m1 = t_lo + (t_hi-t_lo)/3
        m2 = t_hi - (t_hi-t_lo)/3
        if fn_mp(m1) < fn_mp(m2):
            t_lo = m1
        else:
            t_hi = m2
    return (t_lo+t_hi)/2

# ---------- Q0：k=3 锚+四项约化自检 ----------
q0 = {}
for k in (3, 5, 7):
    Pis = build_Pi_coeffs(k)
    S = S_from_Pi(Pis, k)
    M = (3**k - 3)//8
    Nc = M
    # 直接 S3-S7 与四项约化（float 网格三点）
    d_direct = S[3] - S[7]
    zeta = np.exp(2j*np.pi/8)
    d_four = ((zeta**3 - zeta**7)*(Pis[1]-Pis[5]) + (zeta - zeta**5)*(Pis[3]-Pis[7]))/8
    coeff_diff = np.max(np.abs(d_direct - d_four))
    # mpmath 三点核对
    def S3S7_mp(t):
        z = mpexp(2j*mppi/8)
        p = (k+1)//2; q = k//2
        tt = mpexp(1j*t)
        Pis = []
        for m in range(8):
            Am = 1 + z**(-m)*tt + z**(-2*m)*tt**2
            A3 = 1 + z**(-3*m)*tt + z**(-6*m)*tt**2
            Pis.append(Am**p * A3**q)
        direct = sum((z**(3*m)-z**(7*m))*Pis[m] for m in range(8))/8
        four = ((z**3-z**7)*(Pis[1]-Pis[5]) + (z-z**5)*(Pis[3]-Pis[7]))/8
        return abs(direct-four)
    mp_diffs = [float(S3S7_mp(mpf(t))) for t in (mppi/4, mppi/2, mpf(1))]
    q0[f"k{k}"] = {"coeff_diff": float(coeff_diff), "mp_diffs": mp_diffs}
    if k == 3:
        # 锚：峰位 7π/4+峰值 2/3
        g = np.abs(eval_poly(d_direct, tgrid))*0  # placeholder
        A3 = eval_poly(S[3], tgrid)/M; A7 = eval_poly(S[7], tgrid)/M
        gphi = np.abs(np.exp(1j*tgrid)*(A3-A7))
        jmax = int(np.argmax(gphi))
        t_star = tgrid[jmax]
        fam = np.array([np.pi/4, 3*np.pi/4, 5*np.pi/4, 7*np.pi/4])
        dist = np.min(np.abs(np.abs(t_star-fam-2*np.pi*np.round((t_star-fam)/(2*np.pi)))))
        val_at = float(gphi[jmax])
        q0["k3_anchor"] = {"t_star": float(t_star), "family_dist": float(dist),
                           "peak_val": val_at, "val_err_vs_2_3": abs(val_at-2/3)}
res["Q0"] = q0
q0_pass = (q0["k3_anchor"]["family_dist"] <= 1e-9 and q0["k3_anchor"]["val_err_vs_2_3"] <= 1e-10
           and all(q0[f"k{kk}"]["coeff_diff"] <= 1e-12 for kk in (3, 5, 7))
           and all(d <= 1e-30 for kk in (3, 5, 7) for d in q0[f"k{kk}"]["mp_diffs"]))
res["Q0"]["pass"] = bool(q0_pass)
log(f"Q0: pass={q0_pass} k3锚={q0['k3_anchor']} 约化系数差={[q0[f'k{kk}']['coeff_diff'] for kk in (3,5,7)]}")

# ---------- Q1/Q2/Q3：对称性+argmax ----------
def analyze(k, pair):
    """pair: '10|22' or '2|20'"""
    Pis = build_Pi_coeffs(k)
    S = S_from_Pi(Pis, k)
    M = (3**k - 3)//8
    zeta = np.exp(2j*np.pi/8)
    if pair == "10|22":
        c, cp, d = 3, 7, 1
    else:
        c, cp, d = 0, 6, 2
    Nc = M if c >= 2 else M+1
    Ncp = M if cp >= 2 else M+1
    Ac = eval_poly(S[c], tgrid)/Nc
    Acp = eval_poly(S[cp], tgrid)/Ncp
    g = np.abs(np.exp(1j*d*tgrid)*(Ac-Acp))
    jmax = int(np.argmax(g))
    peak = float(g[jmax])
    # 网格对称性
    sh2 = NGRID//2; sh4 = NGRID//4
    half = float(np.max(np.abs(g - np.roll(g, sh2))))
    quarter = float(np.max(np.abs(g - np.roll(g, sh4))))
    # 细化（mpmath）：直接用 Π 定义
    p = (k+1)//2; q = k//2
    z = mpexp(2j*mppi/8)
    Ncm = mpf(M) if c >= 2 else mpf(M+1)
    Ncpm = mpf(M) if cp >= 2 else mpf(M+1)
    def gfun(t):
        tt = mpexp(1j*t)
        Sc = sum(z**(m*c)  * (1+z**(-m)*tt+z**(-2*m)*tt**2)**p * (1+z**(-3*m)*tt+z**(-6*m)*tt**2)**q for m in range(8))/8
        Scp = sum(z**(m*cp) * (1+z**(-m)*tt+z**(-2*m)*tt**2)**p * (1+z**(-3*m)*tt+z**(-6*m)*tt**2)**q for m in range(8))/8
        return abs(mpexp(1j*d*t)*(Sc/Ncm-Scp/Ncpm))
    step = 2*np.pi/NGRID
    t_lo = mpf(tgrid[jmax]-step); t_hi = mpf(tgrid[jmax]+step)
    t_ref = float(refine_peak(gfun, t_lo, t_hi))
    val_ref = float(gfun(mpf(t_ref)))
    # 族点值
    fam_vals = [float(gfun(mpf(t_ref)+j*mppi/2)) for j in range(1, 4)]
    fam_ok = all(abs(v-val_ref) <= 1e-9 for v in fam_vals)
    # 局部极大清单（网格，≥50% 峰）
    loc = []
    for j in range(NGRID):
        if g[j] >= 0.5*peak and g[j] >= g[(j-1) % NGRID] and g[j] >= g[(j+1) % NGRID]:
            loc.append((float(tgrid[j]), float(g[j])))
    return {"t_star_grid": float(tgrid[jmax]), "t_star_refined": t_ref,
            "peak_val_grid": peak, "peak_val_refined": val_ref,
            "grid_maxdiff_half": half, "grid_maxdiff_quarter": quarter,
            "family_vals_quarter": fam_vals, "family_ok_quarter": fam_ok,
            "local_maxima_ge50": sorted(loc, key=lambda x: -x[1])[:8]}

q1 = {}; q2 = {}
for k in (3, 5, 7):
    for pair in ("10|22", "2|20"):
        r = analyze(k, pair)
        q1[f"k{k}_{pair}"] = {"half": r["grid_maxdiff_half"], "quarter": r["grid_maxdiff_quarter"],
                               "family_ok_quarter": r["family_ok_quarter"],
                               "n_local_ge50": len(r["local_maxima_ge50"])}
        q2[f"k{k}_{pair}"] = {"t_star": r["t_star_refined"], "val": r["peak_val_refined"],
                               "local_maxima_ge50": r["local_maxima_ge50"]}
        log(f"k={k} {pair}: t*={r['t_star_refined']:.12f} val={r['peak_val_refined']:.12f} "
            f"half={r['grid_maxdiff_half']:.2e} quarter={r['grid_maxdiff_quarter']:.2e} "
            f"fam_ok={r['family_ok_quarter']} loc>50%={len(r['local_maxima_ge50'])} [{time.time()-T0:.1f}s]")

# Q1 判定
half_ok = all(q1[key]["half"] <= 1e-12 for key in q1)
quarter_ok = {key: (q1[key]["quarter"] <= 1e-12 and q1[key]["family_ok_quarter"]) for key in q1}
res["Q1"] = {"details": q1, "half_pass": bool(half_ok), "quarter_pass_by_key": quarter_ok,
             "quarter_pass_all": bool(all(quarter_ok.values()))}
# Q3：k=5 的 2|20 峰位=π/2
t25 = q2["k5_2|20"]["t_star"]
res["Q3"] = {"t_star_k5_2|20": t25, "dist_to_pi_over_2": abs(t25-np.pi/2),
             "pass": bool(abs(t25-np.pi/2) <= 1e-9)}
# Q-D 偏移序列
res["QD_offset"] = {"8pi_over_5": 8*np.pi/5,
                     "delta_k5": q2["k5_10|22"]["t_star"]-8*np.pi/5,
                     "delta_k7": q2["k7_10|22"]["t_star"]-8*np.pi/5,
                     "delta_k3": q2["k3_10|22"]["t_star"]-8*np.pi/5}
log(f"Q1: half_pass={half_ok} quarter_all={res['Q1']['quarter_pass_all']}")
log(f"Q3: k5 2|20 t*={t25:.12f} |t*-π/2|={abs(t25-np.pi/2):.2e} pass={res['Q3']['pass']}")
log(f"Q-D: δ_k5={res['QD_offset']['delta_k5']:.6f} δ_k7={res['QD_offset']['delta_k7']:.6f}")

# Q5 总裁决
q5 = (q0_pass and half_ok
      and all(q1[k3]["half"] <= 1e-12 for k3 in q1))
res["Q5_total"] = {"structure_pass(Q0+Q1 half)": bool(q5),
                    "predictions(Q1 quarter / Q3)": {"Q1_quarter_all": res["Q1"]["quarter_pass_all"],
                                                      "Q3": res["Q3"]["pass"]}}
log(f"Q5: 结构主项={q5} 预测(Q1quarter={res['Q1']['quarter_pass_all']}, Q3={res['Q3']['pass']})")

outp = "H:/理论存档/01-数学/02-实验与数据/results/fourpoint_k5k7_result-v1.0-20260921.json"
with open(outp, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1, default=str)
log(f"结果落盘 {outp} [{time.time()-T0:.1f}s]")
