# -*- coding: utf-8 -*-
"""
代数册·E₋₁完全定理化与最小DFA判定预注册判据书-v1.0-20260921 实算脚本
判据: P0-P5 (判据书 §三, 冻结文本零改动, NTFS 2026-09-21 03:07:04)
定理 J-A..J-E 机器印证: 语言刻画全等/计数闭式任意k/τ二型分解/最小DFA恰5态/R20伪合并定理
"""
import json, time
import numpy as np
from pathlib import Path

RES = Path("H:/理论存档/01-数学/02-实验与数据/results")
TAG = "v1.0-20260921"
G = {0: (0, 0, 0), 1: (0, 1, -1), 2: (-1, 2, -1), 3: (0, 2, -2)}
K12 = 4 ** 12
NMAX = 10 ** 6


def build_D(n_tot):
    D = np.zeros(n_tot, dtype=np.int32)
    tau = np.ones(n_tot, dtype=np.int8)
    for rho in range(4):
        D[rho] = G[rho][0]
        tau[rho] = 1 if rho in (0, 3) else -1
    for j in range(0, 11):
        lo, hi = 4 ** j, min(4 ** (j + 1), n_tot // 4)
        Z = np.arange(lo, hi, dtype=np.int64)
        dZ = D[lo:hi].astype(np.int32)
        tZ = tau[lo:hi].astype(np.int32)
        mZ = Z % 3
        for rho in range(4):
            g = np.array(G[rho], dtype=np.int32)[mZ]
            D[4 * Z + rho] = 3 * dZ + tZ * g
            tau[4 * Z + rho] = tZ if rho in (0, 3) else -tZ
    return D, tau


def s12_direct(y):
    s1 = s2 = 0
    for n in range(y):
        t = 1 if bin(n).count("1") % 2 == 0 else -1
        r = n % 3
        if r == 1:
            s1 += t
        elif r == 2:
            s2 += t
    return s1 - s2


def b4_digits(y):
    ds = []
    while y > 0:
        ds.append(y % 4)
        y //= 4
    return ds[::-1] or [0]


def main():
    t0 = time.time()
    logs = []
    res = {"meta": {"script_start": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "freeze": "判据书冻结 NTFS 2026-09-21 03:07:04"}}

    def log(m):
        logs.append(str(m))
        print(m, flush=True)

    # ============ P0 递推表自检 ============
    D, tau = build_D(K12)
    bad = sum(1 for y in range(2001) if int(D[y]) != s12_direct(y))
    direct_m1 = {y for y in range(2001) if s12_direct(y) == -1}
    rec_m1 = {int(y) for y in np.nonzero(D[:2001] == -1)[0]}
    P0 = bool(bad == 0 and direct_m1 == rec_m1)
    res["P0"] = {"mismatches": bad, "set_equal": direct_m1 == rec_m1, "pass": P0}
    log(f"P0: 递推 vs 直接定义 Y<=2000 失配 {bad}, E_m1 集合全等 {direct_m1 == rec_m1} -> {P0}")

    # ============ P1 语言刻画全等 ============
    # T 值集: {0,3}* 串基 BFS（值基 BFS 会 0→0 自循环，MemoryError 拦截后改此口径）
    T_vals = set()
    frontier = [""]
    while frontier:
        nxt = []
        for s in frontier:
            T_vals.add(int(s, 4) if s else 0)
            if len(s) < 12:
                for d in "03":
                    nxt.append(s + d)
        frontier = nxt
    T_vals = sorted(T_vals)
    # L_C 值集: A*4^{j+1} + 3*4^j - 1, A in T, j>=0, 值 < 4^12
    L_C = set()
    for A in T_vals:
        j = 0
        while True:
            v = A * 4 ** (j + 1) + 3 * 4 ** j - 1
            if v >= K12:
                break
            L_C.add(v)
            j += 1
    # L_B 值集: 4A+5
    L_B = {4 * A + 5 for A in T_vals if 4 * A + 5 < K12}
    L_vals = L_C | L_B
    Em1 = set(np.nonzero(D == -1)[0].tolist())
    eq = (L_vals == Em1)
    counts_ok = True
    c_counts, b_counts, e_counts = [], [], []
    for k in range(1, 13):
        e = sum(1 for v in Em1 if v < 4 ** k)
        c = sum(1 for v in Em1 if v < 4 ** k and tau[v] == -1)
        b = e - c
        c_counts.append(c)
        b_counts.append(b)
        e_counts.append(e)
        if e != 3 * 2 ** (k - 1) - 2 or c != 2 ** k - 1 or b != 2 ** (k - 1) - 1:
            counts_ok = False
    P1 = bool(eq and counts_ok)
    res["P1"] = {"set_equal": eq, "nL": len(L_vals), "nE": len(Em1),
                 "counts_ok": counts_ok, "e_counts": e_counts,
                 "c_counts": c_counts, "b_counts": b_counts, "pass": P1}
    log(f"P1: 语言刻画集全等 {eq} ({len(L_vals)} vs {len(Em1)}); 计数闭式 k=1..12 零容差 {counts_ok} -> {P1}")

    # ============ P2 结构零违反 ============
    mask = D == -1
    ys = np.nonzero(mask)[0]
    mod3_bad = int(np.sum(ys % 3 != 2))
    C_mask = mask & (tau == -1)
    B_mask = mask & (tau == 1)
    c_cnt = int(C_mask.sum())
    b_cnt = int(B_mask.sum())
    S1_cnt = int(np.sum((tau[ys] == 1) & (ys % 3 == 1)))
    P2 = bool(mod3_bad == 0 and c_cnt == 2 ** 12 - 1 and b_cnt == 2 ** 11 - 1 and S1_cnt == 0)
    res["P2"] = {"mod3_violations": mod3_bad, "C_count": c_cnt, "B_count": b_cnt,
                 "S1_selfref_count": S1_cnt, "pass": P2}
    log(f"P2: mod3!=2 违反 {mod3_bad}; C={c_cnt}(2^12-1), B={b_cnt}(2^11-1); S1 自引用计数 {S1_cnt} -> {P2}")

    # ============ P3 最小 DFA (ε-增广 Nerode + 显式 5 态模拟) ============
    delta = {("q0", 0): "q0", ("q0", 1): "qB", ("q0", 2): "qC", ("q0", 3): "q0",
             ("qC", 0): "qD", ("qC", 1): "qD", ("qC", 2): "qD", ("qC", 3): "qC",
             ("qB", 0): "qB", ("qB", 1): "qB2", ("qB", 2): "qD", ("qB", 3): "qD",
             ("qB2", 0): "qD", ("qB2", 1): "qD", ("qB2", 2): "qD", ("qB2", 3): "qD",
             ("qD", 0): "qD", ("qD", 1): "qD", ("qD", 2): "qD", ("qD", 3): "qD"}
    acc = {"qC", "qB2"}
    sim_bad = 0
    for y in range(3 * NMAX + 1):
        st = "q0"
        for a in b4_digits(y):
            st = delta[(st, a)]
        if (st in acc) != (int(D[y]) == -1):
            sim_bad += 1

    def nerode_classes(suffix_exp, prefix_exp, eps_bit):
        NW = 4 ** suffix_exp
        KU = 4 ** prefix_exp
        assert KU * NW <= K12
        base = (np.arange(KU, dtype=np.int64)[:, None] * NW
                + np.arange(NW, dtype=np.int64)[None, :]).ravel()
        bits = (D[base] == -1).reshape(KU, NW)
        sigs = set()
        for r in np.packbits(bits, axis=1):
            sigs.add(r.tobytes())
        if eps_bit:
            eps = (D[:KU] == -1)
            for i in range(KU):
                if eps[i]:
                    pass
            # ε 位并入: 前缀自身的接受性
            eps_sigs = set()
            for i in range(KU):
                row = bits[i].tobytes()
                key = (int(eps[i]), row)
                eps_sigs.add(key)
            return len(eps_sigs)
        return len(sigs)

    n_eps_65 = nerode_classes(5, 6, True)
    n_eps_57 = nerode_classes(5, 7, True)
    n_eps_66 = nerode_classes(6, 6, True)
    # 见证表: 10 对可分 (ε 或 1 位后缀)
    reps_str = {"q0": "0", "qC": "2", "qB": "1", "qB2": "11", "qD": "21"}
    suffixes = ["", "0", "1", "2", "3"]
    names = list(reps_str)

    def inL(uw):
        return int(D[uw]) == -1

    wit_ok = True
    wit_detail = []
    for i in range(5):
        for j in range(i + 1, 5):
            found = None
            for w in suffixes:
                si = reps_str[names[i]] + w
                sj = reps_str[names[j]] + w
                vi, vj = int(si, 4), int(sj, 4)
                if inL(vi) != inL(vj):
                    found = w if w else "ε"
                    break
            wit_detail.append((names[i], names[j], found))
            if found is None:
                wit_ok = False
    P3 = bool(sim_bad == 0 and n_eps_65 == 5 and n_eps_57 == 5 and n_eps_66 == 5 and wit_ok)
    res["P3"] = {"dfa5_sim_mismatch_3e6": sim_bad,
                 "nerode_eps_classes": {"s5_p6": n_eps_65, "s5_p7": n_eps_57, "s6_p6": n_eps_66},
                 "witness_all_found": wit_ok, "witness": wit_detail, "pass": P3}
    log(f"P3: 5态DFA模拟 Y<=3e6 失配 {sim_bad}; ε-增广 Nerode {n_eps_65}/{n_eps_57}/{n_eps_66}; 见证 {wit_ok} -> {P3}")

    # ============ P4 R20 伪合并解释 ============
    def sig_noeps(u, suffix_exp):
        NWl = 4 ** suffix_exp
        w = np.arange(NWl, dtype=np.int64)
        vals = u * NWl + w
        return np.packbits(D[vals] == -1).tobytes()

    merged_56 = sig_noeps(5, 6) == sig_noeps(9, 6)
    cls_nonoeps_s5p6 = len({sig_noeps(u, 5) for u in range(4 ** 6)})
    cls_nonoeps_s6p6 = len({sig_noeps(u, 6) for u in range(4 ** 6)})
    # R20 4态闭包 (BFS, ℓ=5) 全量模拟无截断
    NWl = 4 ** 5
    w_arr = np.arange(NWl, dtype=np.int64)

    def sig_l5(u):
        return np.packbits(D[u * NWl + w_arr] == -1).tobytes()

    start_sig = sig_l5(0)
    rep = {start_sig: 0}
    trans = {}
    queue = [start_sig]
    while queue:
        s = queue.pop()
        u = rep[s]
        for a in range(4):
            v = 4 * u + a
            sv = sig_l5(v)
            if sv not in rep:
                rep[sv] = v
                queue.append(sv)
            trans[(s, a)] = sv
    accs = {s for s, u in rep.items() if int(D[u]) == -1}
    n_states = len(rep)
    mism = set()
    for y in range(NMAX + 1):
        st = start_sig
        for a in b4_digits(y):
            st = trans[(st, a)]
        if (st in accs) != (int(D[y]) == -1):
            mism.add(y)
    L_B_dom = {v for v in L_B if v <= NMAX}
    P4 = bool(merged_56 and cls_nonoeps_s5p6 == 4 and cls_nonoeps_s6p6 == 4
              and mism == L_B_dom)
    res["P4"] = {"BC_vs_dead_signature_equal_suffix6": merged_56,
                 "classes_nonoeps": {"s5_p6": cls_nonoeps_s5p6, "s6_p6": cls_nonoeps_s6p6},
                 "closure_states_l5": n_states,
                 "mismatch_count_1e6": len(mism),
                 "LB_count_1e6": len(L_B_dom),
                 "mismatch_set_equals_LB": mism == L_B_dom, "pass": P4}
    log(f"P4: B成vs死签名全同(定宽6位) {merged_56}; 无ε类数 {cls_nonoeps_s5p6}/{cls_nonoeps_s6p6}; "
        f"闭包 {n_states} 态失配 {len(mism)} vs L_B {len(L_B_dom)} 集合相等 {mism == L_B_dom} -> {P4}")

    # ============ P5 总裁决 ============
    struct = P0 and P1 and P2 and P3 and P4
    res["verdict"] = {"structure_pass": bool(struct),
                      "final": ("E₋₁ 完全定理化成立【复算一致】: J-A 自引用空置 + J-B τ二型分解 + "
                                "J-C 显式语言刻画 {0,3}*2{3}* ∪ {0,3}*10*1 + J-D 计数闭式 3·2^{k-1}-2 任意k + "
                                "J-E 最小DFA恰5态 + J-E.1 伪合并定理" if struct else "如实入账(见分项, 判负照记)")}
    log(f"P5 总裁决: {res['verdict']['final']}")
    res["log"] = logs
    res["elapsed_sec"] = round(time.time() - t0, 1)
    (RES / f"e_m1_complete_theorem_result-{TAG}.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    log(f"结果落盘（总用时 {time.time() - t0:.1f}s）")


if __name__ == "__main__":
    main()
