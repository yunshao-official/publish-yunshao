# -*- coding: utf-8 -*-
"""
MZV数值库 v2 —— Hoffman 基全基元扫描（权重2..18，263基元，深度至9）+ PSLQ 识别
================================================================================
路线B扩展件（v2.0）脚本 ｜ 2026-09-27 ｜ 判据源：任务书《MZV数值库v2》
正本链：MZV基结构库与数值验证·卷六路线B主件-v1.0（深度≤2/dps=30 之上扩展）

方法（判据先行，任务书=判据）：
  1) 基元全枚举：权重2..18 的 {2,3}-有序组合 = 263 个（含深度1），逐一赋值；
  2) 数值：mpmath dps=50。深度1用 zeta 精确值；深度≥2 = 精确部分和（嵌套DP直算）
     + 解析尾项外推（Hurwitz zeta 渐近展开 = 全阶 Richardson；任务书双N
     N=40000/120000 Richardson 照算，作交叉验证，残差照记）；
  3) 代数闭环自检：stuffle 20对（阈值1e-10）；对偶关系（标准 0-1 词规则，
     全部263对数值验证，含任务书抽验5组）；全2指标 zeta({2}^r)=pi^(2r)/(2r+1)! r=2..9；
  4) PSLQ 识别：深度2字面对（w=4,5,6）+ 全权重单项式基（zeta(2)^a × 奇zeta幂）扫描；
  5) 判负照记：一切失败/超界如实入档。

输出：results/mzv_v2_20260927.json（锁箱）+ 分段检查点 mzv_v2_checkpoint_*.json
运行：python mzv_v2_fullscan-v1.0-20260927.py [all|unittest|production|closure|pslq|finalize]
"""
import sys, os, json, hashlib, time
from fractions import Fraction
from collections import OrderedDict

from mpmath import (mp, mpf, mpmathify, zeta, pi, bernoulli, binomial,
                    factorial, digamma, nstr)
try:
    from mpmath import pslq as mp_pslq
except ImportError:            # 老版本兜底：运行时再探测
    mp_pslq = None

mp.dps = 50
EULER_GAMMA = +mp.euler

# ---------------- 全局参数 ----------------
W_MAX = 18
N_PROD = 2000          # 生产直算截断（尾项解析精确，N 只影响直算部分长度）
N_CHECK = 4000         # 自洽残差用 2N
EMAX = 46              # 渐近展开最高阶（m^-46 @ N=2000 → ~1e-150，远低于 1e-45 需求）
NEGLIG = mpf(10) ** (-58)

RESULTS_DIR = os.path.dirname(os.path.abspath(__file__)) + "/results"
CKPT_VALUES = RESULTS_DIR + "/mzv_v2_checkpoint_values.json"
CKPT_CLOSURE = RESULTS_DIR + "/mzv_v2_checkpoint_closure.json"
CKPT_PSLQ = RESULTS_DIR + "/mzv_v2_checkpoint_pslq.json"
LOCKBOX = RESULTS_DIR + "/mzv_v2_20260927.json"
V1_JSON = RESULTS_DIR + "/mzv_routeB_final_20260927.json"

T_START = time.time()


def elapsed():
    return round(time.time() - T_START, 1)


def log(*a):
    print(f"[{elapsed():8.1f}s]", *a)
    sys.stdout.flush()


# ============================================================
# 第一部分：枚举与 0-1 词工具
# ============================================================

def compositions_23(w):
    """权重 w 的全部 {2,3}-有序组合（Hoffman 基元指标），返回 list[tuple]"""
    if w == 0:
        return [()]
    if w < 2:
        return []
    return [(2,) + c for c in compositions_23(w - 2)] + \
           [(3,) + c for c in compositions_23(w - 3)]


def word_of(S):
    """指标 -> 0-1 词：0^{s1-1} 1 0^{s2-1} 1 ...（标准 Brown/Le-Murakami 口径）"""
    w = []
    for s in S:
        w.extend([0] * (s - 1))
        w.append(1)
    return w


def parse_word(bits):
    """0-1词 -> 指标（须 0 开头、1 结尾）；非法返回 None"""
    if not bits or bits[-1] != 1:
        return None
    S, cnt = [], 0
    for b in bits:
        if b == 0:
            cnt += 1
        else:
            S.append(cnt + 1)
            cnt = 0
    return tuple(S)


def dual_index(S):
    """对偶指标 = swap(reverse(word))。"""
    w = word_of(S)
    return parse_word([1 - x for x in w[::-1]])


def idx_str(S):
    return "z(" + ",".join(map(str, S)) + ")"


def idx_disp(S):
    return "ζ(" + ",".join(map(str, S)) + ")"


# ============================================================
# 第二部分：渐近展开代数
#   字典键 (e, j)：项 = c * m^{-e} * (ln m)^j，j∈{0,1}；e=0,j=1 即 ln m 项
# ============================================================

def dd():
    from collections import defaultdict
    return defaultdict(mpf)


def prune(D, emax=EMAX):
    """截断到 e<=emax，剔除可忽略小项"""
    out = {}
    for (e, j), c in D.items():
        if e > emax or abs(c) < NEGLIG * 1e-6:
            continue
        out[(e, j)] = +c
    return out


_DQ_CACHE = {}


def dq_terms(w):
    """zeta(w, m+1) 的 (m+1) 幂渐近展开项 [(q, coef, d(coef)/dw)]：
       zeta(w,m+1) = (m+1)^{1-w}/(w-1) + (m+1)^{-w}/2 + Σ_i B_{2i}(w)_{2i-1}/(2i)! (m+1)^{-w-2i+1}
       （DLMF 25.2.4 口径；w>=2）"""
    if w in _DQ_CACHE:
        return _DQ_CACHE[w]
    terms = []
    if w >= 2:
        terms.append((w - 1, mpf(1) / (w - 1), -mpf(1) / (w - 1) ** 2))
    terms.append((w, mpf(1) / 2, mpf(0)))
    i = 1
    while w + 2 * i - 1 <= EMAX + 2:
        B = bernoulli(2 * i)
        r = mp.rf(w, 2 * i - 1)   # 上升阶乘 (w)_{2i-1}
        f = factorial(2 * i)
        terms.append((w + 2 * i - 1, B * r / f,
                      B * r * (digamma(w + 2 * i - 1) - digamma(w)) / f))
        i += 1
    _DQ_CACHE[w] = terms
    return terms


_G_CACHE = {}


def Gexp(w):
    """zeta(w, m+1) 的 m 幂展开字典（w>=2 纯幂；w==1 为 psi(m+1)=ln m+γ+幂）。"""
    key = ("G", w)
    if key in _G_CACHE:
        return _G_CACHE[key]
    D = dd()
    if w == 1:
        # psi(m+1) = ln m + gamma + 1/(2m) - sum_{k>=1} B_{2k}/(2k) m^{-2k}
        D[(0, 1)] += mpf(1)
        D[(0, 0)] += EULER_GAMMA
        D[(1, 0)] += mpf(1) / 2
        k = 1
        while 2 * k <= EMAX:
            D[(2 * k, 0)] += -bernoulli(2 * k) / (2 * k)
            k += 1
    else:
        for q, c, _dc in dq_terms(w):
            i = 0
            while q + i <= EMAX:
                D[(q + i, 0)] += c * (-1) ** i * binomial(q + i - 1, i)
                i += 1
    out = prune(D)
    _G_CACHE[key] = out
    return out


_DG_CACHE = {}


def DGexp(w):
    """-d/dw zeta(w, m+1) 的 m 展开字典（含 (e,1) 对数项）；w>=2。
       -d_w zeta = Σ_q [-coef'_q + coef_q·ln(m+1)]·(m+1)^{-q}
       (m+1)^{-q} = Σ_i (-1)^i C(q+i-1,i) m^{-q-i}
       ln(m+1)    = ln m + Σ_l (-1)^{l+1} m^{-l}/l"""
    key = ("DG", w)
    if key in _DG_CACHE:
        return _DG_CACHE[key]
    D = dd()
    for q, c, dc in dq_terms(w):
        i = 0
        while q + i <= EMAX:
            b = (-1) ** i * binomial(q + i - 1, i)
            D[(q + i, 0)] += -dc * b
            D[(q + i, 1)] += c * b
            l = 1
            while q + i + l <= EMAX:
                D[(q + i + l, 0)] += c * b * (-1) ** (l + 1) / l
                l += 1
            i += 1
    out = prune(D)
    _DG_CACHE[key] = out
    return out


def shift01(D):
    """(n-1) 基 → n 基：(n-1)^{-e}(ln(n-1))^j 展开
       (n-1)^{-e} = n^{-e} Σ_i C(e+i-1,i) n^{-i}
       ln(n-1)    = ln n - Σ_l n^{-l}/l"""
    out = dd()
    for (e, j), c in D.items():
        i = 0
        while e + i <= EMAX:
            b = c * binomial(e + i - 1, i)
            if j == 0:
                out[(e + i, 0)] += b
            else:
                out[(e + i, 1)] += b
                l = 1
                while e + i + l <= EMAX:
                    out[(e + i + l, 0)] -= b / l
                    l += 1
            i += 1
    return prune(out)


def tail_exp(s, ZD):
    """E 字典：Σ_{n≥m+1} n^{-s} Z(n-1) 的 m 渐近展开（s>=2）。
       = Σ_(e,j) c·[ zeta(s+e,m+1) (j=0) | -d_w zeta(s+e,m+1) (j=1) ]"""
    assert s >= 2, "tail_exp 需 s>=2"
    E = dd()
    for (e, j), c in shift01(ZD).items():
        w = s + e
        Gs = Gexp(w) if j == 0 else DGexp(w)
        for kk, cc in Gs.items():
            E[kk] += c * cc
    return prune(E)


def zeta_deriv(w, a):
    """d/dw zeta(w, a)"""
    try:
        return zeta(w, a, derivative=1)
    except TypeError:
        return diff(lambda x: zeta(x, a), w)


def evaluate_tail(t, ZD, N):
    """数值 Σ_{n=N+1}^∞ n^{-t} Z(n-1)，Z 以 (n-1) 基展开字典给定。
       逐项要求权 w=t+e>=2（否则 Hurwitz 发散）。"""
    total = mpf(0)
    for (e, j), c in shift01(ZD).items():
        w = t + e
        assert w >= 2, f"evaluate_tail 权 w={w}<2 发散"
        if abs(c) * mpf(N + 1) ** (-w) < NEGLIG:
            continue
        if j == 0:
            total += c * zeta(w, N + 1)
        else:
            total -= c * zeta_deriv(w, N + 1)
    return +total


# ============================================================
# 第三部分：引擎（值 / E / ZE 记忆化 + DP 数组 LRU）
# ============================================================

class MZVEngine:
    def __init__(self, N, N2):
        self.N = N
        self.N2 = N2
        self.memo = {}        # S -> dict(value, ZE, E?, kind)
        self._pws = {}        # 幂表 m^-k

    def pws(self, k, M):
        """n^{-k} 幂表，下标 0 为占位 0（n>=1 才使用）"""
        arr = self._pws.get(k)
        if arr is None:
            arr = [mpf(0)] + [mpf(n) ** (-k) for n in range(1, M + 1)]
            self._pws[k] = arr
        elif len(arr) < M + 1:
            arr = arr + [mpf(n) ** (-k) for n in range(len(arr), M + 1)]
            self._pws[k] = arr
        return arr

    _ARR_CAP = 110

    def get_array(self, S, M):
        """Z_m(S), m=0..M 的列表（LRU 缓存）"""
        cache = getattr(self, "_arr_cache", None)
        if cache is None:
            cache = self._arr_cache = OrderedDict()
        key = (S, M)
        if key in cache:
            cache.move_to_end(key)
            return cache[key]
        if S == ():
            arr = [mpf(1)] * (M + 1)
        else:
            prev = self.get_array(S[1:], M)
            s1 = S[0]
            pw = self.pws(s1, M)
            arr = [mpf(0)] * (M + 1)
            run = mpf(0)
            for m in range(1, M + 1):
                run += prev[m - 1] * pw[m]
                arr[m] = run
        cache[key] = arr
        while len(cache) > self._ARR_CAP:
            cache.popitem(last=False)
        return arr

    def direct_sum(self, S, M):
        """Σ_{n≤M} n^{-s1} Z_{n-1}(suffix) —— 精确部分和"""
        s1 = S[0]
        arr = self.get_array(S[1:], M)
        pw = self.pws(s1, M)
        tot = mpf(0)
        for n in range(1, M + 1):
            t = arr[n - 1]
            if t:
                tot += pw[n] * t
        return tot

    def ensure(self, S):
        """计算并记忆 index S：value（收敛时）、ZE（Z_m 渐近字典）。"""
        if S in self.memo:
            return self.memo[S]
        if len(S) == 0:
            r = {"value": mpf(1), "ZE": {(0, 0): mpf(1)}, "E": {}, "kind": "base"}
            self.memo[S] = r
            return r
        s1, rest = S[0], S[1:]
        r_rest = self.ensure(rest)
        if s1 >= 2:
            # E 只对纯类（s1>=2）需要
            E_S = tail_exp(s1, r_rest["ZE"])
            val = self.direct_sum(S, self.N2) + evaluate_tail(s1, r_rest["ZE"], self.N2)
            val_N = self.direct_sum(S, self.N) + evaluate_tail(s1, r_rest["ZE"], self.N)
            resid = abs(val - val_N)
            ZE_S = {(0, 0): +val}
            for kk, cc in E_S.items():
                ZE_S[kk] = ZE_S.get(kk, mpf(0)) - cc
            ZE_S = prune(ZE_S)
            r = {"value": val, "value_N": val_N, "resid": resid,
                 "ZE": ZE_S, "E": E_S, "kind": "pure"}
        else:
            assert s1 == 1, "指标首项须>=1"
            # 对数类：Z_m(1,S'') = value(S'')·H_m - Σ_{j≤m} j^{-1} τ_{S''}(j-1)
            # 后缀须纯（无连1；{2,3}词的对偶指标自动满足）
            # 常数 S_inf = Σ_{j>=1} j^{-1}τ(j-1) 不用渐近系数求和（二项式移位在 j=1
            # 发散，交换非法——v2 首跑判负已修正）：直算 j≤J + 解析尾（τ 数值=
            # ζ(rest)−Z 数组，精确）
            assert r_rest["kind"] in ("pure", "base"), "对数类要求后缀纯（无连1）"
            E_rest = r_rest.get("E", {})
            val_rest = r_rest["value"]
            J = 400
            S_inf = (val_rest if rest else mpf(0))   # j=1 项：τ(0)=ζ(rest)（base 后缀 τ≡0）
            if rest:
                arr_r = self.get_array(rest, J)
                for j in range(2, J + 1):
                    S_inf += (val_rest - arr_r[j - 1]) / j
                if E_rest:
                    S_inf += evaluate_tail(1, E_rest, J)
            ZE_S = dd()
            for kk, cc in Gexp(1).items():
                ZE_S[kk] += val_rest * cc
            ZE_S[(0, 0)] -= S_inf
            if E_rest:
                for (e, j), c in shift01(E_rest).items():
                    w = 1 + e
                    assert w >= 2
                    Sp = Gexp(w) if j == 0 else DGexp(w)
                    for kk, cc in Sp.items():
                        ZE_S[kk] += c * cc
            # 首项 s1=1 的外层和 Σ n^{-1}·Z(n-1) 对数发散——对数类只作后缀使用，
            # 不定义收敛 value（收敛值只出现在 s1>=2 的指标）
            r = {"value": None, "ZE": prune(ZE_S), "kind": "log"}
        self.memo[S] = r
        return r

    def value(self, S):
        r = self.ensure(S)
        assert r["value"] is not None, f"{idx_disp(S)} 不收敛（首项=1）"
        return r["value"]


# ============================================================
# 第四部分：单元测试电池
# ============================================================

def unit_tests(eng):
    results = {"pass": True, "items": []}

    def T(name, ok, detail=""):
        results["items"].append({"name": name, "pass": bool(ok), "detail": detail})
        if not ok:
            results["pass"] = False
        log(f"  [{'PASS' if ok else 'FAIL'}] {name} {detail}")

    # T1: G 表
    m = mpf(5000)
    lnm = mp.log(m)

    def ev(D):   # 展开字典数值化：Σ c·m^{-e}·(ln m)^j
        return sum(c * m ** (-e) * lnm ** j for (e, j), c in D.items())

    for w in (2, 3, 5, 7):
        err = abs(ev(Gexp(w)) - zeta(w, m + 1))
        T(f"G表 zeta({w},m+1) m=5000", err < mpf(10) ** -45, f"err={nstr(err,3)}")
    # T1b: DG 表（对 w 导数，含 ln 项）
    w = 3
    err = abs(ev(DGexp(w)) - (-zeta_deriv(mpf(w), m + 1)))
    T("DG表 -d_w zeta(3,m+1) m=5000", err < mpf(10) ** -40, f"err={nstr(err,3)}")
    # T1c: psi 表——Gexp(1) 表示 H_m = ψ(m+1)+γ（对数路径 Z_m=ζ(rest)·H_m 用）
    err = abs(ev(Gexp(1)) - (digamma(m + 1) + EULER_GAMMA))
    T("G表 H_m=psi(m+1)+gamma m=5000", err < mpf(10) ** -45, f"err={nstr(err,3)}")

    # T2: 深度1 精确
    T("ζ(2)=pi^2/6", abs(eng.value((2,)) - pi ** 2 / 6) < mpf(10) ** -45)
    T("ζ(3)=zeta(3)", abs(eng.value((3,)) - zeta(3)) < mpf(10) ** -45)

    # T3: 已知闭式（纯路径）
    T("ζ(2,2)=pi^4/120", abs(eng.value((2, 2)) - pi ** 4 / 120) < mpf(10) ** -40,
      f"val={nstr(eng.value((2,2)),20)}")
    T("ζ(2,2,2)=pi^6/7!", abs(eng.value((2, 2, 2)) - pi ** 6 / factorial(7)) < mpf(10) ** -40)
    T("ζ(3,3)=ζ3²/2-ζ6/2",
      abs(eng.value((3, 3)) - (zeta(3) ** 2 / 2 - zeta(6) / 2)) < mpf(10) ** -40)

    # T4: 对数路径（含 1 的指标，Euler 闭式）
    T("ζ(2,1)=ζ(3)", abs(eng.value((2, 1)) - zeta(3)) < mpf(10) ** -35,
      f"val={nstr(eng.value((2,1)),20)}")
    T("ζ(3,1)=ζ4/4", abs(eng.value((3, 1)) - zeta(4) / 4) < mpf(10) ** -35)
    T("ζ(4,1)=2ζ5-ζ2ζ3",
      abs(eng.value((4, 1)) - (2 * zeta(5) - zeta(2) * zeta(3))) < mpf(10) ** -35)
    eu51 = mpf(5) / 2 * zeta(6) - (zeta(4) * zeta(2) + zeta(3) ** 2 + zeta(2) * zeta(4)) / 2
    T("ζ(5,1)=Euler闭式", abs(eng.value((5, 1)) - eu51) < mpf(10) ** -35)

    # T5: v1.0 交叉（12 个深度2值；v1.0 自身方法精度 ~1e-10（其报告自报
    # 外推残差 2e-20~2.3e-11），故阈值 5e-10，最坏偏差照记）
    try:
        v1 = json.load(open(V1_JSON, encoding="utf-8"))
        n_ok, n_tot, worst = 0, 0, mpf(0)
        for k, v in v1["values"].items():
            S = tuple(int(x) for x in k[2:-1].split(","))
            diff = abs(eng.value(S) - mpmathify(v))
            worst = max(worst, diff)
            n_tot += 1
            if diff < mpf(10) ** -9.3:
                n_ok += 1
        T(f"v1.0深度2值交叉({n_ok}/{n_tot})", n_ok == n_tot,
          f"worst={nstr(worst,3)}（v1.0字面法精度内）")
    except Exception as ex:
        T("v1.0交叉", False, f"异常 {ex}")

    # T6: 对偶样例（任务书5组+自对偶）
    for S in [(2, 3), (3, 3), (2, 2, 3), (2, 3, 3), (3, 2, 2)]:
        D = dual_index(S)
        err = abs(eng.value(S) - eng.value(D))
        T(f"对偶 ζ{S} = ζ{D}", err < mpf(10) ** -30, f"err={nstr(err,3)}")
    T("自对偶 ζ(2,2,2)", dual_index((2, 2, 2)) == (2, 2, 2))

    # T7: N/2N 自洽残差抽样
    worst = mpf(0)
    for S in [(2, 3), (3, 3, 2), (2, 2, 2, 3)]:
        worst = max(worst, eng.ensure(S)["resid"])
    T("N/2N自洽残差抽样", worst < mpf(10) ** -40, f"worst={nstr(worst,3)}")

    return results


# ============================================================
# 第五部分：生产扫描（263 基元）
# ============================================================

def production(eng):
    per_weight = {}
    values = {}
    all_elems = []
    for w in range(2, W_MAX + 1):
        comps = compositions_23(w)
        per_weight[w] = len(comps)
        all_elems += [(S, w) for S in comps]
    total = len(all_elems)
    log(f"枚举完成：权重2..18 基元总数 = {total}（任务书口径 263）")
    dcheck = [1, 1, 1, 2, 2, 3, 4, 5, 7, 9, 12, 16, 21, 28, 37, 49, 65]
    cnt_ok = all(per_weight[w] == dcheck[w - 2] for w in range(2, 19))
    log("计数=Zagier维数 17/17：" + ("PASS" if cnt_ok else "FAIL"))
    if total != 263 or not cnt_ok:
        raise RuntimeError("枚举计数与任务书不符！")

    # 按权重升序处理（数组缓存友好）
    for i, (S, w) in enumerate(sorted(all_elems, key=lambda t: (t[1], len(t[0])))):
        eng.ensure(S)
        if (i + 1) % 40 == 0:
            log(f"  ...{i+1}/{total}")
    log("263 基元赋值完成")

    # 汇总（含 Richardson 交叉在 closure 阶段做，这里先存主表）
    for S, w in all_elems:
        r = eng.memo[S]
        values[idx_str(S)] = {
            "index": list(S), "depth": len(S), "weight": w,
            "value25": nstr(r["value"], 25),
            "value40": nstr(r["value"], 40),
            "N": eng.N2,
            "resid_N_vs_2N": nstr(r.get("resid", mpf(0)), 5),
        }
    return {"per_weight": per_weight, "count": total,
            "count_matches_dk_17of17": cnt_ok, "values": values}


# ============================================================
# 第六部分：代数闭环
# ============================================================

def closure(eng, prod):
    out = {}
    # 1) stuffle 20 对（v1.0 的 12 对 + 8 对新）
    pairs = [(2, 2), (2, 3), (3, 2), (2, 5), (5, 2), (3, 3), (3, 4), (4, 3),
             (2, 7), (7, 2), (5, 5), (2, 9),
             (4, 5), (5, 4), (6, 3), (3, 6), (4, 4), (5, 3), (6, 2), (2, 6)]
    rows, worst, npass = [], mpf(0), 0
    for a, b in pairs:
        lhs = zeta(a) * zeta(b)
        rhs = eng.value((a, b)) + eng.value((b, a)) + zeta(a + b)
        err = abs(lhs - rhs)
        worst = max(worst, err)
        npass += err < mpf(10) ** -10
        rows.append({"pair": [a, b], "err": nstr(err, 5)})
    out["stuffle"] = {"n": len(pairs), "pass": int(npass), "threshold": "1e-10",
                      "worst_err": nstr(worst, 5), "rows": rows}
    log(f"stuffle 闭环：{npass}/{len(pairs)} PASS，最坏残差 {nstr(worst,3)}")

    # 2) 对偶：全部 263 对
    rows, worst, npass = [], mpf(0), 0
    for w in range(2, W_MAX + 1):
        for S in compositions_23(w):
            D = dual_index(S)
            assert D is not None and D[0] >= 2
            err = abs(eng.value(S) - eng.value(D))
            worst = max(worst, err)
            ok = err < mpf(10) ** -10
            npass += ok
            if not ok or w <= 7:   # 低权重全记录，高权重只记失败
                rows.append({"S": list(S), "dual": list(D), "err": nstr(err, 5),
                             "pass": bool(ok)})
    out["duality"] = {"n": sum(per_weight_cache(w) for w in range(2, 19)),
                      "pass": int(npass), "threshold": "1e-10",
                      "worst_err": nstr(worst, 5), "rows": rows}
    log(f"对偶闭环：{npass}/{out['duality']['n']} PASS，最坏残差 {nstr(worst,3)}")

    # 3) 全2指标 ζ({2}^r)=π^{2r}/(2r+1)!  r=2..9
    rows, npass = [], 0
    for r in range(2, 10):
        S = tuple([2] * r)
        err = abs(eng.value(S) - pi ** (2 * r) / factorial(2 * r + 1))
        npass += err < mpf(10) ** -10
        rows.append({"r": r, "weight": 2 * r, "depth": r, "err": nstr(err, 5)})
    out["all2"] = {"n": 8, "pass": int(npass), "threshold": "1e-10", "rows": rows}
    log(f"全2指标 ζ({{2}}^r)：{npass}/8 PASS")

    # 4) 任务书两处猜测的数值判负照记
    g1 = abs(eng.value((2, 3)) - eng.value((3, 2)))
    g2 = abs(eng.value((2, 2, 2)) - eng.value((3, 3)))
    out["task_guesses_negated"] = {
        "guess_dual_23_32": {"err": nstr(g1, 5), "verdict": "判负：ζ(2,3)≠ζ(3,2)，"
                             "标准对偶 dual(2,3)=(2,1,2)，dual(3,2)=%s" % str(dual_index((3, 2)))},
        "guess_dual_222_33": {"err": nstr(g2, 5), "verdict": "判负：ζ(2,2,2)≠ζ(3,3)；"
                              "(2,2,2)自对偶；dual(3,3)=(2,1,2,1)"},
    }
    return out


def weight_of(S):
    return sum(S)


_PERW = {}


def per_weight_cache(w):
    if not _PERW:
        for ww in range(2, W_MAX + 1):
            _PERW[ww] = len(compositions_23(ww))
    return _PERW[w]


# ============================================================
# 第七部分：PSLQ 识别
# ============================================================

def do_pslq(vec, tol_exp=30, maxcoeff=10 ** 13, maxsteps=1500):
    """小规模 PSLQ：返回整数关系列表或 None（搜索界如实披露）"""
    if mp_pslq is None:
        return None
    try:
        return mp_pslq(vec, tol=mpf(10) ** (-tol_exp),
                       maxcoeff=maxcoeff, maxsteps=maxsteps)
    except Exception:
        return None


def monomials_of_weight(w):
    """权重 w 的单ζ幂单项式指数列表 [{2:a, p:c_p,...}]（2a+Σp·c_p=w，奇p≥3）"""
    odds = [3, 5, 7, 9, 11, 13, 15, 17]
    out = []

    def rec(rem, idx, cur):
        if idx >= len(odds):
            if rem % 2 == 0:
                e = dict(cur)
                a = rem // 2
                if a:
                    e[2] = e.get(2, 0) + a
                if e:
                    out.append(e)
            return
        p = odds[idx]
        for c in range(rem // p + 1):
            d = dict(cur)
            if c:
                d[p] = c
            rec(rem - c * p, idx + 1, d)

    rec(w, 0, {})
    return out


def monval(expd):
    v = mpf(1)
    for p, c in expd.items():
        v *= zeta(p) ** c
    return v


def fmt_rat(fr):
    fr = Fraction(fr).limit_denominator(10 ** 14)
    return f"{fr.numerator}/{fr.denominator}" if fr.denominator != 1 else str(fr.numerator)


def pslq_stage(eng, prod_values):
    """PSLQ 识别（发现性产出）。
    【v2 首跑判负照记】dps=50 + tol=1e-30 下假阳性淹没：任意系数<=1e13 的整数
    向量 c 都有 |c·舍入噪声| <= 1e13*26*1e-49 ≈ 2.6e-35 < tol（无判别力），
    权重18 出现 65/65 全部"单项式化简成功"的不可能结果（Hoffman 基元线性
    无关，最多 #单项式 个可约）——全部作废。
    【修复】dps=110 重算基元值：噪声底 1e-109，对非关系向量组
    |c·v| >= 10^-109*maxcoeff^-1 ≈ 1e-63 >> tol=1e-88，假阳性被精度排除；
    tol/maxcoeff/验证阈值三方挂钩，如实披露搜索界。"""
    global NEGLIG
    mp.dps = 110
    NEGLIG = mpf(10) ** (-118)
    eng = MZVEngine(N_PROD, N_CHECK)
    all_elems = []
    for w in range(2, W_MAX + 1):
        all_elems += compositions_23(w)
    for i, S in enumerate(sorted(all_elems, key=lambda t: (weight_of(t), len(t)))):
        eng.ensure(S)
        if (i + 1) % 60 == 0:
            log(f"  [dps110 重算] ...{i+1}/{len(all_elems)}")
    log("[dps110] 263 基元重算完成（PSLQ 专用）")

    out = {"precision_note": "PSLQ 在 dps=110 下执行（首跑 dps=50 假阳性判负作废）",
           "tol": "1e-88", "maxcoeff": int(1e14), "maxsteps": 1000,
           "literal": [], "monomial_reductions": {}, "failures": [],
           "summary": {}}
    n_found, n_fail = 0, 0

    # --- 字面扫描（任务书：深度2基元对 + 奇ζ）---
    lit = [
        (4, [(2, 2)], [ {2: 2} ]),                        # ζ(2,2) vs ζ(2)^2（ζ4=2/5·ζ2²同族）
        (5, [(2, 3), (3, 2)], [ {5: 1} ]),                # vs ζ(5)
        (6, [(3, 3)], [ {3: 2}, {2: 3} ]),                # vs ζ(3)^2, ζ(2)^3
    ]
    for w, elems, mons in lit:
        vec = [eng.value(S) for S in elems] + [monval(mm) for mm in mons]
        rel = do_pslq(vec, tol_exp=88, maxcoeff=10 ** 14, maxsteps=1000)
        ok = False
        if rel and any(x != 0 for x in rel):
            err = abs(sum(rel[i] * vec[i] for i in range(len(vec))))
            if err < mpf(10) ** -28:
                nz = next(i for i, x in enumerate(rel) if x != 0)
                denom = rel[nz]

                def fm(x):
                    return fmt_rat(Fraction(-x, denom)) if x else "0"

                expr = {idx_str(elems[i]): fm(rel[i]) for i in range(len(elems))}
                mexpr = {str(sorted(mm.items())): fm(rel[len(elems) + i])
                         for i, mm in enumerate(mons)}
                out["literal"].append({"weight": w,
                                       "elements": [list(S) for S in elems],
                                       "relation": [int(x) for x in rel],
                                       "solved": expr, "monomials": mexpr,
                                       "residual": nstr(err, 5), "pass": True})
                n_found += 1
                ok = True
        if not ok:
            out["literal"].append({"weight": w, "elements": [list(S) for S in elems],
                                   "relation": None, "pass": False})
            n_fail += 1
    log(f"PSLQ 字面扫描：{n_found} 关系，{n_fail} 失败")

    # --- 全权重单项式基扫描（每个 Hoffman 基元 vs 单ζ幂单项式）---
    per_w_summary = {}
    for w in range(2, W_MAX + 1):
        mons = monomials_of_weight(w)
        found_w, fail_w = [], []
        for S in compositions_23(w):
            vec = [eng.value(S)] + [monval(mm) for mm in mons]
            rel = do_pslq(vec, tol_exp=88, maxcoeff=10 ** 14, maxsteps=1000)
            if rel and rel[0] != 0:
                err = abs(sum(rel[i] * vec[i] for i in range(len(vec))))
                if err < mpf(10) ** -88:
                    coeff = {str(sorted(mm.items())): fmt_rat(Fraction(-rel[i + 1], rel[0]))
                             for i, mm in enumerate(mons) if rel[i + 1]}
                    found_w.append({"index": list(S),
                                    "expr": coeff, "residual": nstr(err, 5)})
                    continue
            fail_w.append(list(S))
        per_w_summary[w] = {"n_hoffman": len(compositions_23(w)), "n_monomials": len(mons),
                            "n_reduced": len(found_w), "n_not_reduced": len(fail_w)}
        out["monomial_reductions"][str(w)] = found_w
        if fail_w:
            out["failures"].append({"weight": w, "not_reduced": fail_w})
        log(f"  权重{w}: 基元{len(compositions_23(w))} 单项式{len(mons)} "
            f"化简成功{len(found_w)} 未化简{len(fail_w)}")
    out["summary"] = per_w_summary
    return out


# ============================================================
# 第八部分：Richardson 交叉验证（任务书字面：N=40000/120000）
# ============================================================

def richardson_cross(eng):
    """深度2：任务书字面双N Richardson 交叉验证"""
    out = {"note": "任务书字面法：N=40000/120000 双N Richardson（p=s1-1）；"
                   "生产值=解析尾项法，此处验证两法一致性",
           "rows": []}
    worst = mpf(0)
    for S in [(2, 2), (2, 3), (3, 2), (2, 5), (5, 2), (3, 3), (3, 5), (5, 3)]:
        a, b = S
        N1, N2_ = 40000, 120000
        arr = eng.get_array((b,), N2_)
        pw = eng.pws(a, N2_)
        s1 = mpf(0)
        for n in range(1, N1 + 1):
            s1 += pw[n] * arr[n - 1]
        s2 = s1
        for n in range(N1 + 1, N2_ + 1):
            s2 += pw[n] * arr[n - 1]
        p = a - 1
        # Richardson（比率3，消 O(N^{-p}) leading 尾项）：
        #   S* = (3^p·S(3N) − S(N))/(3^p − 1)
        # 【判负照记】首跑曾把方向写成 (3^p·S(N) − S(3N))/(3^p−1)，不消 leading
        # 项，残留 (4/3)c1/N1≈5.5e-5（与 v1.0 的 a/b 互换 bug 同族）——已修正
        rich = (mpf(3) ** p * s2 - s1) / (mpf(3) ** p - 1)
        exact = eng.value(S)
        err = abs(rich - exact)
        worst = max(worst, err)
        out["rows"].append({"index": list(S), "richardson_err_vs_engine": nstr(err, 5)})
    out["worst_err"] = nstr(worst, 5)
    log(f"Richardson(N=40000/120000) vs 解析尾项：最坏偏差 {nstr(worst,3)}（预期~1e-10级=字面法精度上限）")
    return out


# ============================================================
# 主流程
# ============================================================

def save_ckpt(path, obj):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    log(f"检查点已存：{path}")


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    eng = MZVEngine(N_PROD, N_CHECK)
    log(f"MZV v2 引擎启动 stage={stage} dps={mp.dps} N={N_PROD}/{N_CHECK} Emax={EMAX}")

    if stage in ("all", "unittest"):
        log("== 单元测试电池 ==")
        ut = unit_tests(eng)
        if not ut["pass"]:
            log("!! 单元测试未全过——中止生产扫描（判负照记）")
            save_ckpt(RESULTS_DIR + "/mzv_v2_checkpoint_unittest_FAIL.json", ut)
            return
        save_ckpt(RESULTS_DIR + "/mzv_v2_checkpoint_unittest.json", ut)

    if stage in ("all", "production"):
        log("== 生产扫描 263 基元 ==")
        prod = production(eng)
        save_ckpt(CKPT_VALUES, prod)

    if stage in ("all", "closure"):
        log("== 代数闭环 ==")
        prod = json.load(open(CKPT_VALUES, encoding="utf-8"))
        clo = closure(eng, prod)
        clo["richardson_cross"] = richardson_cross(eng)
        save_ckpt(CKPT_CLOSURE, clo)

    if stage in ("all", "pslq"):
        log("== PSLQ 识别 ==")
        ps = pslq_stage(eng, None)
        save_ckpt(CKPT_PSLQ, ps)

    if stage in ("all", "finalize"):
        log("== 锁箱合成 ==")
        script_path = os.path.abspath(__file__)
        sha_script = hashlib.sha256(open(script_path, "rb").read()).hexdigest()
        box = {
            "meta": {
                "task": "MZV数值库v2（路线B扩展：权重≤18全基元263个+dps50+闭环+PSLQ）",
                "date": "2026-09-27",
                "dps": mp.dps, "N_prod": N_PROD, "N_check": N_CHECK, "Emax": EMAX,
                "method": "嵌套和精确部分和 + 解析尾项外推（Hurwitz zeta 全阶渐近=全阶Richardson）；"
                          "任务书字面双N Richardson(N=40000/120000)作交叉验证照记",
                "mpmath": __import__("mpmath").__version__,
                "script": script_path, "script_sha256": sha_script,
                "runtime_s": elapsed(),
            },
        }
        for name, path in [("unittest", RESULTS_DIR + "/mzv_v2_checkpoint_unittest.json"),
                           ("production", CKPT_VALUES),
                           ("closure", CKPT_CLOSURE),
                           ("pslq", CKPT_PSLQ)]:
            if os.path.exists(path):
                box[name] = json.load(open(path, encoding="utf-8"))
        import copy
        box["meta"]["lockbox_sha256"] = "PENDING"
        with open(LOCKBOX, "w", encoding="utf-8") as f:
            json.dump(box, f, ensure_ascii=False, indent=1)
        # 自引用 sha 处理（判负照记：首版直接"写入后算 sha 再写回"导致文件实际
        # sha≠记录值——16字符字段数学上不可能包含自身 sha 的不动点）：
        # lockbox_sha256 = 排除 meta.lockbox_sha256 字段后的 canonical JSON 的 sha256
        b2 = copy.deepcopy(box)
        del b2["meta"]["lockbox_sha256"]
        canon = json.dumps(b2, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"))
        sha_box = hashlib.sha256(canon.encode("utf-8")).hexdigest()
        box["meta"]["lockbox_sha256"] = sha_box
        with open(LOCKBOX, "w", encoding="utf-8") as f:
            json.dump(box, f, ensure_ascii=False, indent=1)
        log(f"锁箱已写：{LOCKBOX}")
        log(f"script sha256[:16] = {sha_script[:16]}")
        log(f"lockbox 内容 sha256[:16]（排除自身字段口径） = {sha_box[:16]}")

    log("完成。")


if __name__ == "__main__":
    main()
