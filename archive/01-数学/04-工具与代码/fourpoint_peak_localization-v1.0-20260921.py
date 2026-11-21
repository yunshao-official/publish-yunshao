# -*- coding: utf-8 -*-
"""R22 候补格·奇档四点峰解析定位 判据 P0-P4 实算
判据书：代数册·奇档四点峰解析定位预注册判据书-v1.0-20260921.md（冻结在先）
口径：mpmath 50 位闭式评估；2^20 网格+峰细化 1e-12；预测值判负照记。
"""
import json, time
import numpy as np
from mpmath import mp, mpf, exp, pi, sin, cos, log as mplog

mp.dps = 50
T0 = time.time()
LOG = []
def log(msg):
    LOG.append(msg)
    print(msg, flush=True)

def zeta8():
    return exp(2j * mp.pi / 8)

def A_m(t, m):
    z = zeta8()
    return 1 + exp(1j * t) * (z ** (-m)) + exp(2j * t) * (z ** (-2 * m))

def S_c(t, k, c):
    p = (k + 1) // 2; q = k // 2
    s = 0j
    for m in range(8):
        s += (zeta8() ** (m * c)) * (A_m(t, m) ** p) * (A_m(t, (3 * m) % 8) ** q)
    return s / 8

def N_c(k, c):
    """干净档 X=3^k-1 的类计数：k 偶 N0=M+1 其余 M；k 奇 N0=N1=M+1 其余 M"""
    r = (3 ** k) % 8
    M = (3 ** k - r) // 8
    if k % 2 == 1 and c in (0, 1):
        return M + 1
    if k % 2 == 0 and c == 0:
        return M + 1
    return M

def dphi(t, k, c, cp):
    """|Delta_phi_{r|r'}(t)| = |S_c/N_c - S_cp/N_cp|（d 相位因子模为 1）"""
    return abs(S_c(t, k, c) / N_c(k, c) - S_c(t, k, cp) / N_c(k, cp))

res = {}

# ---------- P0：k=3 闭式 vs 枚举 ----------
def s3(n):
    s = 0
    while n:
        s += n % 3
        n //= 3
    return s
def enum_S(k, c, t):
    X = 3 ** k - 1
    s = 0j
    for Q in range(X + 1):
        if Q % 8 == c:
            s += exp(1j * t * s3(Q))
    return s
p0_max = 0.0
for t in [mp.pi / 4, mp.pi / 2, mpf(1)]:
    for c in range(8):
        d = abs(S_c(t, 3, c) - enum_S(3, c, t))
        p0_max = max(p0_max, float(d))
res['P0'] = {'max_diff': p0_max, 'pass': bool(p0_max <= 1e-12)}
log(f"P0: max diff = {p0_max:.3e}")

# ---------- P1：k=3 四点峰预测（预测值·判负照记）----------
# 高精度网格：float 先粗扫 + mpmath 细化
k = 3
Ngrid = 2 ** 20
ts = np.linspace(0, 2 * np.pi, Ngrid, endpoint=False)
# 向量化 double 粗扫（|S3-S7|/3，N3=N7=M=3）
Z8 = np.exp(2j * np.pi / 8)
def A_vec(t, m):
    return 1 + np.exp(1j * t) * np.conj(Z8) ** m + np.exp(2j * t) * np.conj(Z8) ** (2 * m)
p_, q_ = 2, 1
S3v = np.zeros(Ngrid, dtype=complex); S7v = np.zeros(Ngrid, dtype=complex)
for m in range(8):
    Am = A_vec(ts, m); Am3 = A_vec(ts, (3 * m) % 8)
    Pm = (Am ** p_) * (Am3 ** q_)
    S3v += (Z8 ** (3 * m)) * Pm
    S7v += (Z8 ** (7 * m)) * Pm
S3v /= 8; S7v /= 8
mag = np.abs(S3v - S7v) / 3.0
mx = float(mag.max())
peaks = ts[np.where(mag > mx - 1e-12)[0]]
# 聚类峰位
peak_set = sorted(set(float(np.round(x, 6)) for x in peaks))
targets = [mp.pi / 4, 3 * mp.pi / 4, 5 * mp.pi / 4, 7 * mp.pi / 4]
# 细化：在粗网格最大点邻域 mpmath 三分
def refine(t0, iters=80):
    lo, hi = t0 - 2 * np.pi / Ngrid, t0 + 2 * np.pi / Ngrid
    flo, fhi = float(mag[0]), float(mag[0])
    for _ in range(iters):
        m1 = lo + (hi - lo) / 3; m2 = hi - (hi - lo) / 3
        f1 = float(dphi(mp.mpf(m1), 3, 3, 7)); f2 = float(dphi(mp.mpf(m2), 3, 3, 7))
        if f1 < f2: lo = m1
        else: hi = m2
    tm = (lo + hi) / 2
    return tm, float(dphi(mp.mpf(tm), 3, 3, 7))
tbest = float(ts[int(np.argmax(mag))])
tm, vm = refine(tbest)
peak_pos_dist = min(abs(tm - float(T)) for T in map(float, targets))
peak_val = vm
res['P1'] = {'grid_argmax_t': tbest, 'refined_t': tm, 'refined_val': vm,
             'dist_to_fourpoint_family': peak_pos_dist,
             'val_vs_2div3_diff': abs(peak_val - 2 / 3),
             'n_grid_peaks': len(peak_set), 'grid_peaks': peak_set[:8],
             'pass': bool(peak_pos_dist <= 1e-6 and abs(peak_val - 2 / 3) <= 1e-10)}
log(f"P1: refined t={tm:.12f} val={vm:.12f} dist={peak_pos_dist:.3e} valdiff={abs(peak_val-2/3):.3e}")

# ---------- P2：镜像结构 ----------
o2 = {}
for kk in [3, 5, 7, 9, 11]:
    ts4096 = np.linspace(0, 2 * np.pi, 4096, endpoint=False)
    def dphi_vec(t_arr, c, cp, kkv):
        Zl = np.exp(2j * np.pi / 8)
        pp = (kkv + 1) // 2; qq = kkv // 2
        Sc = np.zeros(len(t_arr), dtype=complex); Scp = np.zeros(len(t_arr), dtype=complex)
        for m in range(8):
            Am = 1 + np.exp(1j * t_arr) * np.conj(Zl) ** m + np.exp(2j * t_arr) * np.conj(Zl) ** (2 * m)
            Am3 = 1 + np.exp(1j * t_arr) * np.conj(Zl) ** ((3 * m) % 8) + np.exp(2j * t_arr) * np.conj(Zl) ** (2 * ((3 * m) % 8))
            Pm = (Am ** pp) * (Am3 ** qq)
            Sc += (Zl ** (m * c)) * Pm
            Scp += (Zl ** (m * cp)) * Pm
        r = (3 ** kkv) % 8
        M = (3 ** kkv - r) // 8
        def Nc(cc):
            if kkv % 2 == 1: return M + 1 if cc in (0, 1) else M
            return M + 1 if cc == 0 else M
        return np.abs(Sc / Nc(c) - Scp / Nc(cp))
    d_mirror = float(np.max(np.abs(dphi_vec(ts4096, 0, 6, kk) - dphi_vec(ts4096, 2, 4, kk))))
    d_422_410 = float(np.max(np.abs(dphi_vec(ts4096, 1, 7, kk) - dphi_vec(ts4096, 1, 3, kk))))
    o2[kk] = {'mirror_max_diff': d_mirror, 'eq422_410_max_diff': d_422_410}
    log(f"P2 k={kk}: mirror={d_mirror:.3e}  4|22-4|10={d_422_410:.3e}")
res['P2'] = {'per_k': o2,
             'pass_422_410': bool(all(v['eq422_410_max_diff'] <= 1e-10 for v in o2.values())),
             'mirror_equation': bool(all(v['mirror_max_diff'] <= 1e-10 for v in o2.values()))}

# ---------- P3：k=5..11 峰位峰值精化（记录）----------
o3 = {}
for kk in [5, 7, 9, 11]:
    ts4096 = np.linspace(0, 2 * np.pi, 4096, endpoint=False)
    Zl = np.exp(2j * np.pi / 8)
    pp = (kk + 1) // 2; qq = kk // 2
    r = (3 ** kk) % 8
    M = (3 ** kk - r) // 8
    def Svec(t_arr, c):
        S = np.zeros(len(t_arr), dtype=complex)
        for m in range(8):
            Am = 1 + np.exp(1j * t_arr) * np.conj(Zl) ** m + np.exp(2j * t_arr) * np.conj(Zl) ** (2 * m)
            Am3 = 1 + np.exp(1j * t_arr) * np.conj(Zl) ** ((3 * m) % 8) + np.exp(2j * t_arr) * np.conj(Zl) ** (2 * ((3 * m) % 8))
            S += (Zl ** (m * c)) * (Am ** pp) * (Am3 ** qq)
        return S / 8
    def Nc(cc):
        if kk % 2 == 1: return M + 1 if cc in (0, 1) else M
        return M + 1 if cc == 0 else M
    d1022 = np.abs(Svec(ts4096, 3) / Nc(3) - Svec(ts4096, 7) / Nc(7))
    d0208 = np.abs(Svec(ts4096, 0) / Nc(0) - Svec(ts4096, 6) / Nc(6))
    i1 = int(np.argmax(d1022)); i2 = int(np.argmax(d0208))
    o3[kk] = {'peak_10_22_t': float(ts4096[i1]), 'peak_10_22_val': float(d1022[i1]),
              'peak_2_20_t': float(ts4096[i2]), 'peak_2_20_val': float(d0208[i2])}
    log(f"P3 k={kk}: 10|22 peak t={ts4096[i1]:.6f} val={d1022[i1]:.6f}; 2|20 t={ts4096[i2]:.6f} val={d0208[i2]:.6f}")
res['P3'] = {'per_k': o3}

# ---------- P4 总裁决 ----------
res['P4'] = {'P0': res['P0']['pass'], 'P1_prediction': res['P1']['pass'],
             'P2_eq422_410': res['P2']['pass_422_410'], 'P2_mirror': res['P2']['mirror_equation'],
             'pass': bool(res['P0']['pass'] and res['P2']['pass_422_410'])}
log(f"P4: {res['P4']}")

res['meta'] = {'elapsed_s': round(time.time() - T0, 1), 'log': LOG}
import io
out = r'H:\理论存档\01-数学\02-实验与数据\results\fourpoint_peak_localization_result-v1.0-20260921.json'
io.open(out, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1, default=str))
print('saved', out)
