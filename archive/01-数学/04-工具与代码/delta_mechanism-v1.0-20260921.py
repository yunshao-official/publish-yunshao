# -*- coding: utf-8 -*-
# δ_k→0（8π/5 收敛）机理定理化（R25 主格二·判据书 D5 实算）
# 判据书：代数册·全谱32档推进与态数谱机理预注册判据书-v1.0-20260921.md（冻结 NTFS 09:20:14 在先）
# 口径：10|22 对（c,c′)=(3,7)，d=10 mod 3=1；mpmath 50 位；轨道折算 t̂∈(π/2,π)，δ=t̂−3π/5；
#       机理：主导块 m=3 / 次主导块 m=1 幅度比 ρ0=|A1(3π/5)|/|A3(3π/5)| 解析导出，
#       闭式 δ(k)=A·ρ0^k·sin(ωk+φ0) 三参数由 k=5,7,9 定，k=11 复核 ≤0.10，k=13,15 外推记录。
import json, time
import numpy as np
from mpmath import mp, mpf, exp, pi, cos, sin

mp.dps = 50
T0 = time.time()
LOG = []
def log(msg):
    LOG.append(msg); print(msg, flush=True)

Z8 = np.exp(2j * np.pi / 8)

def c_of(r):
    return (r - (r % 3)) // 3 % 8

def class_N(k):
    M = (3 ** k - 3) // 8
    return [M + 1 if c in (0, 1) else M for c in range(8)]

def build_S(k, tgrid):
    """S[c](t) 在网格上（numpy double 粗扫）"""
    p = (k + 1) // 2; q = k // 2
    x = np.exp(1j * tgrid)
    Am = [1 + x * (np.conj(Z8) ** m) + x * x * (np.conj(Z8) ** (2 * m)) for m in range(8)]
    S = {}
    for c in range(8):
        acc = np.zeros_like(x)
        for m in range(8):
            acc += np.exp(1j * np.pi / 4 * ((m * c) % 8)) * (Am[m] ** p) * (Am[(3 * m) % 8] ** q)
        S[c] = acc / 8
    return S

def dphi(k, r, rp, tgrid, S=None):
    c, cp = c_of(r), c_of(rp)
    d = r % 3
    if S is None: S = build_S(k, tgrid)
    Nc = class_N(k)
    return np.abs(np.exp(1j * d * tgrid) * (S[c] / Nc[c] - S[cp] / Nc[cp]))

def mp_dphi(k, r, rp, t):
    p = (k + 1) // 2; q = k // 2
    tt = mp.exp(1j * t)
    z = lambda n: mp.exp(1j * mp.pi / 4 * (n % 8))
    M = (3 ** k - 3) // 8
    def Scc(c):
        tot = mp.mpc(0)
        for m in range(8):
            zm = mp.exp(-1j * mp.pi / 4 * (m % 8))
            z3m = mp.exp(-1j * mp.pi / 4 * ((3 * m) % 8))
            tot += z(m * c) * (1 + zm * tt + zm ** 2 * tt ** 2) ** p * (1 + z3m * tt + z3m ** 2 * tt ** 2) ** q
        return tot / 8
    c, cp = c_of(r), c_of(rp)
    Nc = M + 1 if c in (0, 1) else M
    Ncp = M + 1 if cp in (0, 1) else M
    return abs(mp.exp(1j * (r % 3) * t) * (Scc(c) / Nc - Scc(cp) / Ncp))

def mp_dphi2(k, r, rp, t):
    """|Δφ|² 的 mpmath 值（细化用平方口径更稳）"""
    v = mp_dphi(k, r, rp, t)
    return v * v

def refine_peak(k, r, rp, rep, N, rounds=60):
    """三分法细化 rep 附近的峰（mpmath）"""
    lo = mpf(rep - 4 * 2 * np.pi / N); hi = mpf(rep + 4 * 2 * np.pi / N)
    f = lambda tt: mp_dphi(k, r, rp, tt)
    for _ in range(rounds):
        m1 = lo + (hi - lo) / 3; m2 = hi - (hi - lo) / 3
        if f(m1) < f(m2): lo = m1
        else: hi = m2
    return (lo + hi) / 2

def orbit_fold(tstar):
    """反射轨道四点中取 ∈(π/2,π) 的唯一点 t̂"""
    pi_ = np.pi
    cands = [tstar % (2*pi_), (pi_ - tstar) % (2*pi_), (tstar + pi_) % (2*pi_), (2*pi_ - tstar) % (2*pi_)]
    for t in cands:
        if pi_/2 < t < pi_:
            return t
    return None

EIGHTPI5 = 8 * mp.pi / 5
THREEPI5 = 3 * mp.pi / 5

def main():
    res = {"anchors": {}, "delta_ext": {}, "mech": {}, "verdict": {}}
    N = 2 ** 20
    ts = np.linspace(0, 2 * np.pi, N, endpoint=False)

    # ---- D5① δ 序列 k=5..15（同口径重算+延伸） ----
    deltas = {}
    for k in (5, 7, 9, 11, 13, 15):
        S = build_S(k, ts)
        d = dphi(k, 10, 22, ts, S)
        i = int(np.argmax(d))
        that = orbit_fold(float(ts[i]))
        tref = refine_peak(k, 10, 22, mpf(that), N)
        # tref 是轨道上被粗扫选中的代表；轨道折算回 (π/2,π)
        tref_hat = orbit_fold(float(tref % (2*np.pi)))
        # 直接对 t̂ 型点细化：重新三分（在 t̂ 附近）
        tref2 = refine_peak(k, 10, 22, mpf(tref_hat), N)
        delta = float(mpf(tref2) - THREEPI5)
        deltas["k=%d" % k] = {"that": tref_hat, "tref": float(tref2), "delta_3pi5": delta}
        log("k=%d t̂=%.12f δ=%+.9e" % (k, tref_hat, delta))
    res["delta_ext"] = deltas

    # ---- 锚核对（B4 在档：k=5,7,9,11） ----
    arch = {"k=5": 5.180353708216 - float(8*mp.pi/5),
            "k=7": 5.111199773175 - float(8*mp.pi/5),
            "k=9": 0.03608609528455982,
            "k=11": None}
    # B4 k=11 代表 4.39633 的轨道折算锚=1.88685439209 折算：π−1.25473860792
    arch["k=11"] = float(mpf("1.88685439209") - THREEPI5)
    anchors = {}
    for k in (5, 7, 9, 11):
        d_new = deltas["k=%d" % k]["delta_3pi5"]
        d_ref = arch["k=%d" % k]
        # B4 锚 k=5/7 的代表是 2π−t̂（同一轨道、δ 相差 π/5 折算）；统一用轨道差值：
        # |δ_new − δ_ref| 对 k=5/7 需按同 t̂ 口径：B4 peak 5.1804 → t̂=2.0388=π−(2π−5.1804)？
        # 直接核：B4 peak_refined 折算到 (π/2,π) 后减 3π/5
        anchors["k=%d" % k] = {"new": d_new, "arch_ref": d_ref, "absdiff": abs(d_new - d_ref)}
    res["anchors"] = anchors
    log("anchors: %s" % json.dumps(anchors))

    # ---- ρ0 解析导出（主导块 m=3 / 次主导块 m=1 在 t̂0=3π/5 的幅度比） ----
    A1 = abs(2 * mp.cos(THREEPI5 - mp.pi/4) + 1)
    A3 = abs(2 * mp.cos(THREEPI5 - 3*mp.pi/4) + 1)
    rho0 = A1 / A3
    res["mech"]["rho0"] = {"A1_m1": float(A1), "A3_m3": float(A3), "rho0": float(rho0)}
    log("rho0 = %.9f (A1=%.6f A3=%.6f)" % (float(rho0), float(A1), float(A3)))

    # ---- 闭式拟合：B(k)=δ(k)/ρ0^k，k=5,7,9 定 A,ω,φ0；k=11 复核 ----
    ks = [5, 7, 9]
    B = [mpf(deltas["k=%d" % k]["delta_3pi5"]) / (rho0 ** k) for k in ks]
    d11 = mpf(deltas["k=11"]["delta_3pi5"])
    B11 = d11 / (rho0 ** 11)
    # 递推：B9 = 2 cos(2ω) B7 − B5 （步长 2，因 k 步进 2 ⟹ 相位步 2ω）
    denom = 2 * B[1]
    c2w = (B[2] + B[0]) / denom if denom != 0 else None
    mech_ok = False
    fit = {}
    if c2w is not None and abs(float(c2w)) <= 1:
        w = mp.acos(c2w) / 2
        # A sin(φ0+5w)=B5, A sin(φ0+7w)=B7 ⟹ 解 A,φ0
        # sin(φ0+7w)=sin(φ0+5w)cos2w+cos(φ0+5w)sin2w ⟹ cos(φ0+5w)=(B7−B5 c2w)/(A sin2w)
        s2w = mp.sin(2*w)
        if abs(float(s2w)) > 1e-30:
            # 先解 A：B7² + X² = A²，X=A cos(φ0+5w)=(B7−B5 c2w)/s2w
            X = (B[1] - B[0]*c2w) / s2w
            A2 = B[1]**2 + X**2
            if A2 > 0:
                Aa = mp.sqrt(A2)
                phi5 = mp.asin(B[0]/Aa)  # φ0+5w 的候选（分支待定）
                # 分支校正：cos(φ0+5w)=X/A
                c5 = X/Aa
                for cand in (phi5, mp.pi - phi5):
                    if mp.sign(mp.cos(cand)) == mp.sign(c5) or abs(mp.cos(cand) - c5) < mp.mpf('1e-30'):
                        phi0 = cand - 5*w
                        break
                else:
                    phi0 = None
                if phi0 is not None:
                    def dpred(k):
                        return float(Aa * (rho0 ** k) * mp.sin(phi0 + w*k))
                    pred11 = dpred(11)
                    err11 = abs(pred11 - float(d11)) / abs(float(d11))
                    fit = {"A": float(Aa), "omega": float(w), "phi0": float(phi0 % (2*mp.pi)),
                           "pred11": pred11, "actual11": float(d11), "relerr11": err11}
                    mech_ok = bool(err11 <= 0.10)
                    res["mech"]["fit"] = fit
                    # 外推预测 k=13,15
                    res["mech"]["extrap"] = {"pred13": dpred(13), "pred15": dpred(15),
                                             "actual13": deltas["k=13"]["delta_3pi5"],
                                             "actual15": deltas["k=15"]["delta_3pi5"]}
    res["mech"]["closed_form_ok"] = mech_ok
    log("mech fit: %s" % json.dumps(res["mech"], ensure_ascii=False))

    # ---- D5② 续降结构断言 ----
    a11 = abs(deltas["k=11"]["delta_3pi5"]); a13 = abs(deltas["k=13"]["delta_3pi5"]); a15 = abs(deltas["k=15"]["delta_3pi5"])
    res["verdict"] = {
        "D5_2_continued_decay": bool(a13 < a11 and a15 < a13),
        "D5_3_closed_form_ok": mech_ok,
        "delta_abs": {"11": a11, "13": a13, "15": a15},
    }
    log("verdict: %s" % json.dumps(res["verdict"]))

    outp = "H:/理论存档/01-数学/02-实验与数据/results/delta_mechanism_result-v1.0-20260921.json"
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    log("saved %s" % outp)

if __name__ == "__main__":
    main()
