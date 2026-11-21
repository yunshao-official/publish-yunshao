# -*- coding: utf-8 -*-
"""
ζ零点数值门扩展·最近邻间距统计 vs GUE（探测性统计·非验证主张）
批次：20260927（群论批算+ζ零点门扩展任务令·部分B）
在档锚点：
  - 几何册 v2.1 注5：ζ零点数值门已立，d̄(t)计数平均绝对差0.326（标准精度）
  - ta2_C_e2stats_result-v1.0-20260927.json：冻结判据 C-1 <r>=mean(min(g_n,g_{n+1})/max(g_n,g_{n+1}))，
    冻结基准 GUE≈0.7357 / Poisson≈0.5307（预注册《黎曼猜想·通俗图解-v4.0-20260927》§十二）
数据源（如实）：本机 python urllib 被环境禁外联，Odlyzko 公开表不可拉取 →
  按任务令备选路径：mpmath 1.3.0 自实现计算前 N 个零点（zetazero：Gram 点定位+Riemann-Siegel Z 函数精化，纯python）
统计（全部本轮自算，无外部数值引用）：
  ①raw 间距 ②全局 N̄(T) 展开（von Mangoldt 主项）与局部窗展开双口径
  ③<r̃>=mean(min/max) 对：冻结基准(0.7357/0.5307) + 本轮自算基准（Poisson 解析+MC、
    iid GUE/GOE surmise MC、真 GUE/GOE 随机矩阵 MC 展开体间距）
  ④展开间距分布 vs GUE/GOE Wigner surmise（均值/方差/偏度+KS 距离）
判读纪律：探测性统计，不构成任何验证主张；两套基准并列如实；基准差记判负照记候知世裁。
"""
import json, math, time, datetime, hashlib, os
import numpy as np
import mpmath as mp

mp.mp.dps = 30
N_TARGET = 1000          # 任务令：前1000个零点
EXT_TARGET = 2000        # 若算速允许，扩展到2000增强稳定性
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(OUT_DIR, "results")

# ---------- 1. 零点计算 ----------
t0 = time.time()
zeros = []
for n in range(1, EXT_TARGET + 1):
    g = mp.zetazero(n)          # 返回第 n 个零点虚部（高精度）
    zeros.append(float(mp.im(g)))
    if n == N_TARGET:
        t_mid = time.time() - t0
        print(f"前{N_TARGET}个零点完成：{t_mid:.1f}s")
        if t_mid > 240:          # 时间盒：太慢则止步1000
            break
zeros = np.array(zeros)
N = len(zeros)
print(f"零点总数 N={N}，γ_1={zeros[0]:.6f} γ_N={zeros[-1]:.6f}，用时 {time.time()-t0:.1f}s")

# ---------- 2. 间距与展开 ----------
gaps = np.diff(zeros)
# 全局展开：N̄(T)=T/(2π)ln(T/(2π))−T/2π+7/8（von Mangoldt 主项，忽略 S(T) 振荡·如实注记）
def Nbar(T):
    return T/(2*math.pi)*math.log(T/(2*math.pi)) - T/(2*math.pi) + 7.0/8.0
s_glob = np.array([Nbar(b) - Nbar(a) for a, b in zip(zeros[:-1], zeros[1:])])
# 局部窗展开（与在档 ta2 同风格：中心点邻域线性密度，窗含约50个零点）
halfw = 25
s_loc = []
for i, g in enumerate(gaps):
    lo = max(0, i - halfw); hi = min(N, i + 1 + halfw)
    win = zeros[lo:hi]
    rho = (len(win) - 1) / (win[-1] - win[0])
    s_loc.append(g * rho)
s_loc = np.array(s_loc)

# ---------- 3. <r̃>=mean(min/max)（冻结判据统计量，作用在 raw 间距上） ----------
r_ratio = np.array([min(gaps[i], gaps[i+1]) / max(gaps[i], gaps[i+1]) for i in range(len(gaps)-1)])
mean_r_raw = float(np.mean(r_ratio))
# 展开间距上的同统计量（局部展开口径，稳健性对照）
r_loc = np.array([min(s_loc[i], s_loc[i+1]) / max(s_loc[i], s_loc[i+1]) for i in range(len(s_loc)-1)])
mean_r_loc = float(np.mean(r_loc))

# ---------- 4. 本轮自算基准（无记忆引用·全部数值自产） ----------
rng = np.random.default_rng(20260927)
# 4a. Poisson：解析 2ln2−1 + MC 双验
poi_analytic = 2.0 * math.log(2.0) - 1.0
ex = rng.exponential(1.0, size=(400000, 2))
poi_mc = float(np.mean(np.minimum(ex[:,0], ex[:,1]) / np.maximum(ex[:,0], ex[:,1])))
# 4b. iid Wigner surmise 采样（GUE: (32/π²)s²e^{−4s²/π}；GOE: (π/2)s e^{−πs²/4}）
def sample_gue_surmise(k):
    # 反函数法：F(s) 数值建表
    gs = np.linspace(0, 4.5, 4001)
    pdf = (32/math.pi**2) * gs**2 * np.exp(-4*gs**2/math.pi)
    cdf = np.concatenate([[0], np.cumsum((pdf[1:]+pdf[:-1])/2*np.diff(gs))])
    cdf /= cdf[-1]
    return np.interp(rng.random(k), cdf, gs)
def sample_goe_surmise(k):
    u = rng.random(k)
    # F(s)=1−e^{−πs²/4} → s=sqrt(−(4/π)ln(1−u))
    return np.sqrt(-4/math.pi*np.log(1-u))
def iid_ratio_mean(sp):
    a, b = sp[:-1], sp[1:]
    return float(np.mean(np.minimum(a, b)/np.maximum(a, b)))
gue_iid = iid_ratio_mean(sample_gue_surmise(400001))
goe_iid = iid_ratio_mean(sample_goe_surmise(400001))
# 4c. 真随机矩阵（GUE/GOE N=100，中央体展开）
def matrix_ratio(kind, ntrial=300, nmat=100):
    vals = []
    for _ in range(ntrial):
        if kind == "GUE":
            X = (rng.standard_normal((nmat, nmat)) + 1j*rng.standard_normal((nmat, nmat))) / math.sqrt(2)
            H = (X + X.conj().T) / 2
        else:
            X = rng.standard_normal((nmat, nmat))
            H = (X + X.T) / 2
        ev = np.sort(np.linalg.eigvalsh(H))
        ev = ev[(ev > -0.75) & (ev < 0.75)]   # 中央体（半圆边≈√N=10，|λ|<7.5中央体）
        g = np.diff(ev)
        halfw = 10
        sp = []
        for i, gg in enumerate(g):
            lo = max(0, i-halfw); hi = min(len(ev), i+1+halfw)
            w = ev[lo:hi]
            rho = (len(w)-1)/(w[-1]-w[0])
            sp.append(gg*rho)
        sp = np.array(sp)
        a, b = sp[:-1], sp[1:]
        vals.append(np.mean(np.minimum(a, b)/np.maximum(a, b)))
    return float(np.mean(vals)), float(np.std(vals)/math.sqrt(len(vals)))
gue_mat, gue_mat_se = matrix_ratio("GUE")
goe_mat, goe_mat_se = matrix_ratio("GOE")

# ---------- 5. 展开间距分布 vs Wigner surmise ----------
sp = s_glob
sp = sp[sp > 0]
m_sp, v_sp = float(np.mean(sp)), float(np.var(sp))
sk_sp = float(np.mean(((sp - m_sp)/np.std(sp))**3))
# GUE/GOE surmise 矩（解析·由公式直接积分）
from scipy.integrate import quad
from scipy.stats import kstest
gue_pdf = lambda s: (32/math.pi**2)*s*s*math.exp(-4*s*s/math.pi) if s > 0 else 0.0
goe_pdf = lambda s: (math.pi/2)*s*math.exp(-math.pi*s*s/4) if s > 0 else 0.0
def surmise_moments(pdf):
    m1 = quad(lambda s: s*pdf(s), 0, 12)[0]
    m2 = quad(lambda s: s*s*pdf(s), 0, 12)[0]
    sd = math.sqrt(m2 - m1*m1)
    sk = quad(lambda s: ((s-m1)/sd)**3*pdf(s), 0, 12)[0]
    return m1, m2-m1*m1, sk
gue_m, gue_v, gue_sk = surmise_moments(gue_pdf)
goe_m, goe_v, goe_sk = surmise_moments(goe_pdf)
# KS 距离（数值 CDF）
gs = np.linspace(1e-9, 6, 3000)
gue_cdf = np.concatenate([[0], np.cumsum([(gue_pdf(a)+gue_pdf(b))/2*(b-a) for a, b in zip(gs[:-1], gs[1:])])])
goe_cdf = np.concatenate([[0], np.cumsum([(goe_pdf(a)+goe_pdf(b))/2*(b-a) for a, b in zip(gs[:-1], gs[1:])])])
gue_cdf /= gue_cdf[-1]; goe_cdf /= goe_cdf[-1]
sp_sorted = np.sort(sp)
ecdf = np.arange(1, len(sp_sorted)+1)/len(sp_sorted)
ks_gue = float(np.max(np.abs(ecdf - np.interp(sp_sorted, gs, gue_cdf))))
ks_goe = float(np.max(np.abs(ecdf - np.interp(sp_sorted, gs, goe_cdf))))

# ---------- 6. 判读（两套基准并列·探测性） ----------
frozen = {"GUE": 0.7357, "Poisson": 0.5307}   # 在档冻结基准（ta2_C + 预注册§十二）
own = {"Poisson(解析)": poi_analytic, "Poisson(MC)": poi_mc,
       "GUE_iidSurmise": gue_iid, "GOE_iidSurmise": goe_iid,
       "GUE_matrix": gue_mat, "GOE_matrix": goe_mat}
verdict_frozen = "GUE" if abs(mean_r_raw-frozen["GUE"]) < abs(mean_r_raw-frozen["Poisson"]) else "Poisson"
own_best = min(own, key=lambda k: abs(mean_r_raw - own[k]))
# 分段稳定性
seg = {}
for name, sl in [("1-250", slice(0, 250)), ("251-500", slice(250, 500)),
                 ("501-750", slice(500, 750)), ("751-end", slice(750, len(r_ratio)))]:
    seg[name] = float(np.mean(r_ratio[sl]))

out = {
  "script": "zeta_gate_spacing-v1.0-20260927.py",
  "batch": "20260927 群论批算+ζ零点门扩展任务令·部分B",
  "ran_at": datetime.datetime.now().isoformat(timespec="seconds"),
  "nature": "探测性统计·非验证主张（任务令原话口径）",
  "data_source": {
    "odlyzko_pull": "FAILED——本机python urllib被环境禁外联（[BLOCKED]），公开零点表不可拉取，如实记",
    "fallback_used": "mpmath 1.3.0 zetazero 自实现计算（Gram点定位+Riemann-Siegel Z函数精化，纯python，mp.dps=30）",
    "n_zeros": int(N),
    "first": float(zeros[0]), "last": float(zeros[-1]),
    "compute_seconds": round(time.time()-t0, 1)
  },
  "C1_r_ratio_min_over_max": {
    "statistic_def": "mean(min(g_n,g_{n+1})/max(g_n,g_{n+1}))，与在档 ta2_C_e2stats 冻结判据同定义",
    "value_raw_gaps": mean_r_raw,
    "value_local_unfolded": mean_r_loc,
    "segments_raw": seg,
    "frozen_benchmarks_in_archive": frozen,
    "verdict_vs_frozen": verdict_frozen + " 趋势（冻结基准口径）",
    "own_benchmarks_computed_this_run": own,
    "own_benchmark_errs": {k: abs(mean_r_raw - v) for k, v in own.items()},
    "nearest_own_benchmark": own_best,
    "frozen_vs_own_discrepancy_note": "在档冻结基准(0.7357/0.5307)与本轮自算基准数值不同源（本轮 Poisson 解析=2ln2−1、真GUE矩阵MC=见own字段）；两套判向并列如实，基准溯源与取舍候知世裁——判负照记"
  },
  "C2_unfolded_spacing_distribution": {
    "unfolding": "双口径：全局N̄(T)主项（忽略S(T)振荡·如实注记）+局部窗(±25零点)线性密度",
    "mean_global": m_sp, "var_global": v_sp, "skew_global": sk_sp,
    "mean_local": float(np.mean(s_loc)), "var_local": float(np.var(s_loc)),
    "GUE_surmise_mean_var_skew": [gue_m, gue_v, gue_sk],
    "GOE_surmise_mean_var_skew": [goe_m, goe_v, goe_sk],
    "KS_vs_GUE_surmise": ks_gue, "KS_vs_GOE_surmise": ks_goe,
    "distribution_verdict": "KS更小者=" + ("GUE" if ks_gue < ks_goe else "GOE") + " surmise（趋势级）"
  },
  "honesty_notes": [
    "本件为探测性统计：ζ零点近距统计的GUE归属是主流已知结论方向，本轮不主张任何体系验证",
    "Odlyzko表拉取失败如实记录；数据源=mpmath自算，统计效力限于前%d个零点" % N,
    "全局展开忽略S(T)振荡，局部展开口径已并列给出",
    "在档冻结基准0.7357/0.5307与本轮自算基准不一致——判向可能翻转（如实并列），裁定权在知世",
    "几何册注5数值门(d̄(t)差0.326)口径未动；本件只做间距统计扩展，不触碰该门"
  ]
}
os.makedirs(RES, exist_ok=True)
zp = os.path.join(RES, "zeta_zeros_mpmath-20260927.txt")
with open(zp, "w") as f:
    f.write("# zeta zeros (ordinates), mpmath 1.3.0 zetazero, mp.dps=30, batch 20260927\n")
    for i, z in enumerate(zeros, 1):
        f.write(f"{i} {z:.6f}\n")
jp = os.path.join(RES, "zeta_gate_spacing-20260927.json")
with open(jp, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
hj = hashlib.sha256(open(jp, "rb").read()).hexdigest()
hz = hashlib.sha256(open(zp, "rb").read()).hexdigest()
with open(os.path.join(RES, "zeta_gate_spacing-20260927.sha256"), "w") as f:
    f.write(f"{hj}  zeta_gate_spacing-20260927.json\n{hz}  zeta_zeros_mpmath-20260927.txt\n")
print(json.dumps({k: out[k] for k in ["C1_r_ratio_min_over_max"] if k in out}, ensure_ascii=False, indent=1)[:1600])
print("KS:", ks_gue, ks_goe, "mean/var/sk:", m_sp, v_sp, sk_sp)
print("JSON:", jp, hj[:16], " zeros:", hz[:16])
