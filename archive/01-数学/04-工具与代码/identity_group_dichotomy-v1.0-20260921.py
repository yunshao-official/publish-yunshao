# -*- coding: utf-8 -*-
"""R22 主格二·全 t 恒等群二分定理 判据 O0-O5 实算
判据书：代数册·全t恒等群二分定理预注册判据书-v1.0-20260921.md（冻结在先）
口径：I-D 闭式多项式（干净档）；4096 t 网格恒等判定 max<=1e-10 / 两两不同 max>=1e-3；
非整齐档直方图口径；小档例外枚举；判负照记。
"""
import json, time
import numpy as np

T0 = time.time()
LOG = []
def log(msg):
    LOG.append(msg)
    print(msg, flush=True)

Z8 = np.exp(2j * np.pi / 8)  # zeta

def A_poly(m):
    """A_m(x) = 1 + z^-m x + z^-2m x^2 系数（升幂）"""
    return np.array([1.0 + 0j, np.conj(Z8) ** m, np.conj(Z8) ** (2 * m)])

def F_poly(p, q):
    """F(y) = (1+y+y^2)^p (1+y^3+y^6)^q 升幂系数"""
    f = np.array([1.0 + 0j])
    g1 = np.array([1.0 + 0j, 1, 1])
    for _ in range(p):
        f = np.convolve(f, g1)
    g2 = np.zeros(7, dtype=complex); g2[0] = 1; g2[3] = 1; g2[6] = 1
    for _ in range(q):
        f = np.convolve(f, g2)
    return f

def Pi_m(p, q, m):
    """Pi_m = A_m^p A_{3m mod 8}^q 多项式（卷积幂）"""
    a = A_poly(m)
    pa = np.array([1.0 + 0j])
    for _ in range(p):
        pa = np.convolve(pa, a)
    b = A_poly((3 * m) % 8)
    for _ in range(q):
        pa = np.convolve(pa, b)
    return pa

def S_polys(k):
    """返回 8 个 S_c 多项式系数数组 + (p,q)"""
    p = (k + 1) // 2; q = k // 2
    S = []
    for c in range(8):
        s = np.zeros(2 * k + 1, dtype=complex)
        for m in range(8):
            pm = Pi_m(p, q, m)
            s[:len(pm)] += (Z8 ** (m * c)) * pm
        S.append(s / 8)
    return S, p, q

def eval_poly(coeffs, ts):
    """在 t 数组评估多项式 sum a_j e^{ijt}"""
    x = np.exp(1j * ts)
    pw = np.vstack([x ** j for j in range(len(coeffs))])
    return pw.T @ coeffs

def max_diff_grid(f, g, n=4096):
    ts = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return float(np.max(np.abs(eval_poly(f, ts) - eval_poly(g, ts))))

res = {}

# ---------- O0：F 旋转表示 ----------
o0_max = 0.0
for k in [5, 6]:
    p = (k + 1) // 2; q = k // 2
    Fc = F_poly(p, q)
    for m in range(8):
        pm = Pi_m(p, q, m)
        rot = np.zeros(len(Fc), dtype=complex)
        for j, fj in enumerate(Fc):
            if j < len(rot):
                rot[j] = fj * (np.conj(Z8) ** (m * j))
        L = max(len(pm), len(rot))
        d = float(np.max(np.abs(np.pad(pm, (0, L - len(pm))) - np.pad(rot, (0, L - len(rot))))))
        o0_max = max(o0_max, d)
res['O0'] = {'max_coeff_diff': o0_max, 'pass': bool(o0_max <= 1e-12)}
log(f"O0: max coeff diff = {o0_max:.3e}")

# ---------- O1：偶 k 恒等群 = sigma 循环 ----------
def identity_pairs(S, thr_eq=1e-10, thr_ne=1e-3):
    pairs = []
    clean = True
    for c in range(8):
        for cp in range(c + 1, 8):
            md = max_diff_grid(S[c], S[cp])
            if md <= thr_eq:
                pairs.append((c, cp))
            elif md < thr_ne:
                clean = False
    return pairs, clean

o1 = {}
vand = {}
for k in [4, 6, 8, 10, 12]:
    S, p, q = S_polys(k)
    pairs, clean = identity_pairs(S)
    ok = (sorted(pairs) == [(1, 3), (2, 6), (5, 7)]) and clean
    o1[k] = {'pairs': pairs, 'n_dist': 8 - len(pairs), 'binary_clean': clean, 'pass': bool(ok)}
    # Vandermonde 型行列式 {Pi1,Pi2,Pi5} 无关性（支撑 j=0,1,2 三方程）
    M = np.array([[np.conj(Z8) ** (m * 0), np.conj(Z8) ** (m * 1), np.conj(Z8) ** (m * 2)] for m in (1, 2, 5)])
    vand[k] = float(np.abs(np.linalg.det(M)))
    log(f"O1 k={k}: pairs={pairs} pass={ok}")
res['O1'] = {'per_k': o1, 'vandermonde_det_abs': vand,
             'pass': bool(all(v['pass'] for v in o1.values()))}

# ---------- O2：奇 k 恒等群平凡 ----------
o2 = {}
for k in [3, 5, 7, 9, 11]:
    S, p, q = S_polys(k)
    pairs, clean = identity_pairs(S)
    ok = (len(pairs) == 0) and clean
    o2[k] = {'pairs': pairs, 'binary_clean': clean, 'pass': bool(ok)}
    log(f"O2 k={k}: pairs={pairs} pass={ok}")
res['O2'] = {'per_k': o2, 'pass': bool(all(v['pass'] for v in o2.values()))}

# ---------- O3：非整齐档（预测值·判负照记）----------
def popcount3(n):
    s = 0
    while n:
        s += n % 3
        n //= 3
    return s
def hist_X(X):
    """H[c][s] = #{Q<=X: Q mod 8 == c, s3(Q)=s}（Q=0..X）"""
    Qs = np.arange(X + 1, dtype=np.int64)
    cmod = (Qs % 8).astype(np.int64)
    s3 = np.zeros(X + 1, dtype=np.int64)
    t = Qs.copy()
    while np.any(t):
        s3 += t % 3
        t //= 3
    smax = int(s3.max())
    H = np.zeros((8, smax + 1), dtype=np.int64)
    for c in range(8):
        H[c] = np.bincount(s3[cmod == c], minlength=smax + 1)
    return H
o3 = {}
for X in [666666, 1000000]:
    H = hist_X(X)
    ts = np.linspace(0, 2 * np.pi, 4096, endpoint=False)
    E = np.exp(1j * np.outer(ts, np.arange(H.shape[1])))  # 4096 x (smax+1)
    Tc = E @ H.T  # 4096 x 8
    pairs = []
    clean = True
    for c in range(8):
        for cp in range(c + 1, 8):
            md = float(np.max(np.abs(Tc[:, c] - Tc[:, cp])))
            if md <= 1e-10 * max(1, X):
                pairs.append((c, cp))
            elif md < 1e-3 * max(1, X):
                clean = False
    ok = (len(pairs) == 0) and clean
    o3[X] = {'pairs': pairs, 'binary_clean': clean, 'pass': bool(ok)}
    log(f"O3 X={X}: pairs={pairs} clean={clean} pass={ok}")
res['O3'] = {'per_X': o3, 'pass': bool(all(v['pass'] for v in o3.values()))}

# ---------- O4：小档例外枚举 ----------
o4 = {}
for k in [1, 2]:
    S, p, q = S_polys(k)
    pairs, _ = identity_pairs(S)
    sigma_cycles = {(1, 3), (2, 6), (5, 7)}
    extra = [pr for pr in pairs if tuple(sorted(pr)) not in sigma_cycles]
    o4[k] = {'identity_pairs': sorted(pairs), 'beyond_sigma': sorted(extra)}
    log(f"O4 k={k}: pairs={sorted(pairs)} beyond_sigma={sorted(extra)}")
res['O4'] = {'per_k': o4}

# ---------- O5 总裁决 ----------
res['O5'] = {'structure_pass': bool(res['O0']['pass'] and res['O1']['pass'] and res['O2']['pass']),
             'O3_prediction': res['O3']['pass']}
log(f"O5: {res['O5']}")

res['meta'] = {'elapsed_s': round(time.time() - T0, 1), 'log': LOG}
import io
out = r'H:\理论存档\01-数学\02-实验与数据\results\identity_group_dichotomy_result-v1.0-20260921.json'
io.open(out, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1, default=str))
print('saved', out)
