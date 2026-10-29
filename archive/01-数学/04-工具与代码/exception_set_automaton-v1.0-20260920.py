# -*- coding: utf-8 -*-
"""
代数册·例外集E的四自动机语言刻画预注册判据书-v1.0-20260920 实算脚本
判据: E0-E5 (判据书 §三, 冻结文本零改动)
核心: D(Y)=0 例外集的显式刻画 E=T+{0,1} (T=base-4 只含{0,3});
      计数定理 |E∩[0,4^k)|=2^{k+1}-1; 3 态最小 DFA + Nerode 类数=3
"""
import json, time
from pathlib import Path

RES = Path(r"H:/理论存档/01-数学/02-实验与数据/results")
TAG = "v1.0-20260920"

W = (1, -1, -1, 1)
# g 表 (判据书 §一.2 冻结值): g[rho][m]
G_TAB = {
    0: (0, 0, 0),
    1: (0, 1, -1),
    2: (-1, 2, -1),
    3: (0, 2, -2),
}


def s2(n):
    return bin(n).count("1")


def tau(n):
    return 1 if s2(n) % 2 == 0 else -1


def D_digit(Y):
    """R18 定理 Z-B: D 自治数字递推 (MSB 逐位)"""
    if Y == 0:
        return 0
    digits = []
    x = Y
    while x:
        digits.append(x % 4); x //= 4
    D = 0; t = 1; m = 0
    for d in reversed(digits):
        g = G_TAB[d][m]
        D = 3 * D + t * g
        t = t * W[d]
        m = (m + d) % 3
    return D


def D_array(Ymax):
    """O(Y) 正向递推数组: D[4Z+ρ]=3D[Z]+τ[Z]g_ρ(Z mod 3)"""
    tauA = [0] * (Ymax + 1)
    D = [0] * (Ymax + 1)
    tauA[0] = 1
    for Y in range(1, Ymax + 1):
        Z = Y >> 2
        rho = Y & 3
        t = tauA[Z]
        D[Y] = 3 * D[Z] + t * G_TAB[rho][Z % 3]
        tauA[Y] = t * W[rho]
    return D, tauA


def S_vec_enum(Y):
    """直接枚举 (整型精确)"""
    S = [0, 0, 0]
    for n in range(Y):
        S[n % 3] += (1 if s2(n) % 2 == 0 else -1)
    return S


def b4_digits(Y):
    ds = []
    x = Y
    while x:
        ds.append(x % 4); x //= 4
    return ds[::-1] if ds else [0]


def in_E_explicit(Y):
    """定理 E-C 显式刻画: E=T+{0,1}; 数字⊂{0,3}, 或恰一个 1 且其下(更低)全 0"""
    ds = b4_digits(Y)
    seen1 = False
    for d in ds:
        if d == 2:
            return False
        if d == 1:
            if seen1:
                return False
            seen1 = True
        else:  # d in {0,3}
            if seen1 and d == 3:
                return False  # 1 之后只容 0
    return True


def dfa_accept(digits):
    """3 态 DFA (定理 E-C(iii)): q0={0,3}* 接受; q1=见1后只0 接受; 死"""
    st = 0
    for d in digits:
        if st == 0:
            if d in (0, 3):
                st = 0
            elif d == 1:
                st = 1
            else:
                return False
        elif st == 1:
            if d == 0:
                st = 1
            else:
                return False
    return True


def main():
    t0 = time.time()
    first_run = time.strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"首跑时间 {first_run}"]

    def log(m):
        log_lines.append(str(m)); print(m, flush=True)
    res = {"meta": {"first_run": first_run,
                    "freeze_note": "判据书创建 05:03:44 (NTFS), 首跑在其后 (§四 回填)"}}

    # ---------- E0 递推 vs 枚举 ----------
    ok = True
    for Y in range(0, 2001):
        S = S_vec_enum(Y)
        Dd = D_digit(Y)
        if Dd != S[1] - S[2]:
            ok = False; log(f"E0 失败 Y={Y}")
    E0 = bool(ok)
    res["E0"] = {"grid_0_2000": bool(ok), "pass": E0}
    log(f"E0 递推 vs 枚举 Y=0..2000 零容差: {ok} -> {E0}")

    # ---------- 数组法 (域=4^10, 覆盖 E2 冻结判据 k=0..10 的 4^k-1 上界) ----------
    YM = 4 ** 10  # 1048576 ≥ 1e6, k=10 的 4^10-1=1048575 在域内
    Darr, tauA = D_array(YM)
    zeros = [Y for Y in range(YM + 1) if Darr[Y] == 0]
    eset = set(zeros)
    res["meta"]["zeros_count_le1e6"] = len(zeros)
    log(f"数组递推完成: |{{Y≤1e6: D=0}}| = {len(zeros)}")

    # ---------- E1 结构律 ----------
    bad2 = [Y for Y in zeros if Y % 4 == 2]
    # E=T+{0,1} 全等: T={base-4 只含{0,3}}
    Tset = set()
    for Y in range(YM + 1):
        ds = b4_digits(Y)
        if all(d in (0, 3) for d in ds):
            Tset.add(Y)
    Tplus = set()
    for A in Tset:
        Tplus.add(A)
        if A + 1 <= YM:
            Tplus.add(A + 1)
    Tplus = {x for x in Tplus if x <= YM}
    eq_E = (Tplus == eset)
    eq_T = ({Y for Y in zeros if Y % 3 == 0} == Tset)
    E1 = bool(not bad2 and eq_E and eq_T)
    res["E1"] = {"lastdigit2_zeros": len(bad2), "E_eq_Tplus01": bool(eq_E),
                 "T_eq_Ecap3Z": bool(eq_T), "T_count_le1e6": len(Tset), "pass": E1}
    log(f"E1 结构律: 禁位2例外 {len(bad2)} / E=T+{{0,1}} 全等 {eq_E} / T=E∩3Z 全等 {eq_T} -> {E1}")

    # ---------- E2 计数定理 ----------
    cnt_ok = True; cnt_rows = {}
    for k in range(0, 11):
        p = 4 ** k
        a = sum(1 for Y in zeros if Y < p)
        b = sum(1 for Y in zeros if Y < p and Y % 3 == 0)
        pred_a, pred_b = 2 ** (k + 1) - 1, 2 ** k
        cnt_rows[str(k)] = {"a": a, "pred_a": pred_a, "b": b, "pred_b": pred_b}
        if a != pred_a or b != pred_b:
            cnt_ok = False; log(f"E2 失败 k={k}: {a}/{b} vs {pred_a}/{pred_b}")
    n_1e6 = sum(1 for Y in zeros if Y <= 1_000_000)
    n_262 = sum(1 for Y in zeros if 262144 <= Y <= 1_000_000)  # [4^9, 1e6]
    E2 = bool(cnt_ok and n_1e6 == 1792)
    res["E2"] = {"rows": cnt_rows, "count_1e6": n_1e6, "count_4p9_to_1e6": n_262,
                 "r18_ref": 1792, "pass": E2}
    log(f"E2 计数定理 k=0..10 全对: {cnt_ok}; ≤1e6 复现 {n_1e6}==1792; [262144,1e6)={n_262} -> {E2}")

    # ---------- E3 最小机 ----------
    dfa_ok = all(dfa_accept(b4_digits(Y)) == (Y in eset) for Y in range(YM + 1))
    # Nerode: 标准串域 u 长≤5 (含空串), 后缀域 w 标准 长≤4 (含空串)
    def std_strings(maxlen):
        out = [""]
        for L in range(1, maxlen + 1):
            for v in range(4 ** (L - 1) * 3):
                # 标准 base-4 串长 L: 首位 1..3
                ds = []
                x = (v // (4 ** (L - 1))) + 1
                rem = v % (4 ** (L - 1))
                ds.append(x)
                for i in range(L - 2, -1, -1):
                    ds.append((rem // (4 ** i)) % 4)
                out.append(tuple(ds))
        return out
    Us = std_strings(5)
    Ws = [()] + std_strings(4)
    def append_val(u, w):
        """uw 的值"""
        v = 0
        for d in u: v = v * 4 + d
        for d in w: v = v * 4 + d
        return v
    sigs = {}
    for u in Us:
        sig = tuple(append_val(u, w) in eset for w in Ws)
        sigs[u] = sig
    n_classes = len(set(sigs.values()))
    E3 = bool(dfa_ok and n_classes == 3)
    res["E3"] = {"dfa_vs_enum_1e6": bool(dfa_ok), "nerode_classes_le8domain": n_classes,
                 "n_prefixes": len(Us), "n_suffixes": len(Ws), "pass": E3}
    log(f"E3 最小机: DFA vs 枚举 Y≤1e6 全等 {dfa_ok}; Nerode 类数 {n_classes} (域 u≤5/w≤4) -> {E3}")

    # ---------- E4 记录项 ----------
    dens = {str(k): round(sum(1 for Y in zeros if Y < 4 ** k) / (4 ** k), 6) for k in range(1, 11)}
    adj_pairs = [str(4 ** k) for k in range(0, 11) if (4 ** k) in eset and (4 ** k - 1) in eset]
    res["E4"] = {"density_seq": dens, "dim_log4_2": round(__import__("math").log(2, 4), 6),
                 "adjacent_4k_4k-1_all_present": len(adj_pairs) == 11, "adjacent_pairs": adj_pairs,
                 "note": "记录项(无裁决效力)"}
    log(f"E4 记录: 密度序列+维数 {res['E4']['dim_log4_2']}; 4^k/4^k-1 相邻对 k=0..10 全在 {len(adj_pairs)==11}")

    # ---------- E5 总裁决 ----------
    struct = E0 and E1 and E2 and E3
    res["verdict"] = {"structure_pass": bool(struct),
                      "final": ("例外集四自动机语言刻画成立【复算一致】: E=T+{0,1} 正则语言(3态最小DFA)+计数定理 2^{k+1}-1+维数 1/2" if struct
                                else "如实入账(见分项, 判负照记)")}
    log(f"E5 总裁决: {res['verdict']['final']}")
    res["log"] = log_lines
    (RES / f"exception_set_automaton_result-{TAG}.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘（总用时 {time.time()-t0:.1f}s）")


if __name__ == "__main__":
    main()
