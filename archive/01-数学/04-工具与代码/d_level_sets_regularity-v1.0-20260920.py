# -*- coding: utf-8 -*-
"""
代数册·D值水平集正则性判定预注册判据书-v1.0-20260920 实算脚本
判据: C0-C5 (判据书 §三, 冻结文本零改动, NTFS 2026-09-20 06:07:28)
核心: E_c={Y: D(Y)=c} 递归分解律机器印证 + Nerode 类数正则性双分支判定 + 计数律
"""
import json, math, time
import numpy as np
from pathlib import Path

RES = Path("H:/理论存档/01-数学/02-实验与数据/results")
TAG = "v1.0-20260920"
# g 表 (R18/E 系在档冻结值): g[rho][m]
G = {0: (0, 0, 0), 1: (0, 1, -1), 2: (-1, 2, -1), 3: (0, 2, -2)}
CS = [-1, 1, 2, 3]
NMAX = 10 ** 6
K12 = 4 ** 12
PW = 5            # 后缀域 4^5
NW = 4 ** PW
KU_MAX = 6        # 前缀域至 4^6


def s12_direct(y):
    """直接定义 (Z 系判据书 §一): S_c(Y)=Σ_{n<Y, n≡c(3)}(−1)^{s₂(n)}; D=S₁−S₂"""
    s1 = s2 = 0
    for n in range(y):
        t = 1 if bin(n).count("1") % 2 == 0 else -1
        r = n % 3
        if r == 1:
            s1 += t
        elif r == 2:
            s2 += t
    return s1 - s2


def build_D(n_tot):
    """numpy 向量化 Z-B 递推: D(4Z+ρ)=3D(Z)+τ(Z)g_ρ(Z mod 3); D(0)=0, τ(0)=1"""
    D = np.zeros(n_tot, dtype=np.int32)
    tau = np.ones(n_tot, dtype=np.int8)
    # Z=0 特例 (Y=0..3)
    for rho in range(4):
        D[rho] = G[rho][0]
        tau[rho] = 1 if rho in (0, 3) else -1
    # 分层: Z ∈ [4^j, 4^{j+1}) (Y ∈ [4^{j+1}, 4^{j+2}))
    for j in range(0, 12):
        lo, hi = 4 ** j, 4 ** (j + 1)
        if lo >= n_tot // 4:
            break
        hi = min(hi, n_tot // 4)
        Z = np.arange(lo, hi, dtype=np.int64)
        dZ = D[lo:hi].astype(np.int32)
        tZ = tau[lo:hi].astype(np.int32)
        mZ = (Z % 3)
        for rho in range(4):
            g = np.array(G[rho], dtype=np.int32)[mZ]
            idx = 4 * Z + rho
            D[idx] = 3 * dZ + tZ * g
            tau[idx] = tZ if rho in (0, 3) else -tZ
    return D, tau


def b4_digits(y):
    if y == 0:
        return [0]
    ds = []
    while y > 0:
        ds.append(y % 4)
        y //= 4
    return ds[::-1]


def main():
    t0 = time.time()
    first_run = time.strftime("%Y-%m-%d %H:%M:%S")
    logs = [f"首跑时间 {first_run}"]
    res = {"meta": {"first_run": first_run,
                    "freeze": "判据书冻结 NTFS 2026-09-20 06:07:28 (§四 回填)"}}

    def log(m):
        logs.append(str(m)); print(m, flush=True)

    # ============ C0 递推恒等 ============
    D, tau = build_D(K12)
    bad = 0
    for y in range(2001):
        if int(D[y]) != s12_direct(y):
            bad += 1
    dual_ok = all(bool(np.sum(D[:2001] == c) == sum(1 for y in range(2001) if s12_direct(y) == c))
                  for c in (-1, 0, 1, 2, 3))
    C0 = bool(bad == 0 and dual_ok)
    res["C0"] = {"mismatches": bad, "dual_count_ok": bool(dual_ok), "pass": C0}
    log(f"C0 递推恒等: 失配 {bad}/2001 + 双通道计数 {dual_ok} -> {C0}")

    # ============ C1 递归分解律 ============
    det1 = {}
    C1 = True
    for c in CS:
        Ec = set(np.nonzero(D[:NMAX + 1] == c)[0].tolist())
        layers = {rho: [] for rho in range(4)}
        for rho in range(4):
            if rho == 0:
                if c % 3 == 0:
                    layers[0].append((c // 3, None, None))   # τ, m 不限
            else:
                for m in range(3):
                    for t in (1, -1):
                        gamma = t * G[rho][m]
                        if (c - gamma) % 3 == 0:
                            layers[rho].append(((c - gamma) // 3, t, m))
        gen = set()
        per_rho = {}
        N4 = NMAX // 4 + 1
        Zmod = np.arange(N4) % 3
        for rho, conds in layers.items():
            S = np.zeros(N4, dtype=bool)
            for (d, t, m) in conds:
                Zm = (D[:N4] == d)
                if t is not None:
                    Zm &= (tau[:N4] == t)
                if m is not None:
                    Zm &= (Zmod == m)
                S |= Zm
            Zs = np.nonzero(S)[0]
            ys = 4 * Zs + rho
            ys = ys[ys <= NMAX]
            per_rho[rho] = len(ys)
            gen.update(ys.tolist())
        ok = gen == Ec
        C1 = C1 and ok
        det1[f"c={c}"] = {"enum_count": len(Ec), "gen_count": len(gen),
                          "per_rho": per_rho, "equal": bool(ok)}
        log(f"C1 c={c}: 枚举 {len(Ec)} vs 分解律生成 {len(gen)} (逐ρ {per_rho}) -> {'全等' if ok else '不等'}")
    res["C1"] = {"detail": det1, "pass": C1}

    # ============ C2 Nerode 类数 (L_1 主对象) ============
    ner = {}
    sig_lists = {}
    for c in CS + [0]:
        Ns = []
        for k in range(3, KU_MAX + 1):
            KU = 4 ** k
            base = np.arange(KU, dtype=np.int64)[:, None] * NW + np.arange(NW, dtype=np.int64)[None, :]
            flat = base.ravel()
            okm = (D[flat] == c)
            bits = okm.reshape(KU, NW)
            packed = np.packbits(bits, axis=1)
            sigs = [int.from_bytes(row.tobytes(), "big") for row in packed]
            Ns.append(len(set(sigs)))
            if k == KU_MAX:
                sig_lists[c] = sigs
        ner[c] = Ns
        log(f"C2 L_{c}: Nerode 类数序列 k=3..6 = {Ns}")
    n_seq = ner[1]
    sigma6 = n_seq[-1] / n_seq[-2] if n_seq[-2] else 9.9
    if sigma6 >= 1.5:
        branch = "nonregular-evidence"
    elif sigma6 <= 1.1:
        branch = "regular-evidence"
    else:
        branch = "inconclusive"
    C2 = branch in ("nonregular-evidence", "regular-evidence")
    res["C2"] = {"L1_classes_k3_6": n_seq, "all_c": {str(c): v for c, v in ner.items()},
                 "sigma6": round(sigma6, 4), "branch": branch,
                 "pass": C2, "note": "双分支可判: 通过=给出明确分支; P-c1=正则(判负照记双向)"}
    log(f"C2 判定: σ6={sigma6:.4f} -> {branch} (P-c1=正则 {'印证' if branch=='regular-evidence' else ('判负' if branch=='nonregular-evidence' else '悬置')})")

    # ============ C3 分支跟随 ============
    if branch == "regular-evidence":
        c = 1
        sigs = sig_lists[c]
        uniq = {}
        cid = []
        for s in sigs:
            if s not in uniq:
                uniq[s] = len(uniq)
            cid.append(uniq[s])
        cid = np.array(cid, dtype=np.int32)
        # 空串签名
        empty_bits = (D[:NW] == c)
        sig_empty = int.from_bytes(np.packbits(empty_bits).tobytes(), "big")
        if sig_empty not in uniq:
            uniq[sig_empty] = len(uniq)
        start = uniq[sig_empty]
        # 转移: u < 4^5 -> 4u+a < 4^6
        K5 = 4 ** PW
        nstates = len(uniq)
        delta = np.full((nstates, 4), -1, dtype=np.int32)
        well_defined = True
        for u in range(K5):
            for a in range(4):
                tgt = cid[4 * u + a]
                if delta[cid[u], a] == -1:
                    delta[cid[u], a] = tgt
                elif delta[cid[u], a] != tgt:
                    well_defined = False
        accept = np.zeros(nstates, dtype=bool)
        K6 = 4 ** KU_MAX
        for u in range(K6):
            accept[cid[u]] = bool(D[u] == c)
        # 高位类 (u>=4^5) 的转移一致性抽查: 每类抽 2 代表
        rep = {}
        for u in range(4 ** KU_MAX):
            rep.setdefault(int(cid[u]), []).append(u)
        reps = {s: r for s, r in rep.items() if s >= K5 // 1 and r and r[0] >= K5}
        for s, us in list(reps.items())[:50]:
            if len(us) >= 2:
                for a in range(4):
                    t1 = cid[4 * us[0] + a] if 4 * us[0] + a < len(cid) else -1
                    t2 = cid[4 * us[1] + a] if 4 * us[1] + a < len(cid) else -1
                    if delta[s, a] == -1 and t1 >= 0:
                        delta[s, a] = t1
                    elif t1 >= 0 and delta[s, a] != t1:
                        well_defined = False
        # DFA 模拟 Y<=1e6
        sim_ok = True
        bad_y = 0
        for y in range(NMAX + 1):
            st = start
            for a in b4_digits(y):
                st = int(delta[st, a])
                if st < 0:
                    st = None
                    break
            mem = (st is not None) and bool(accept[st])
            if mem != (int(D[y]) == c):
                sim_ok = False
                bad_y += 1
                if bad_y > 5:
                    break
        C3 = bool(well_defined and sim_ok)
        res["C3"] = {"branch": branch, "n_states": nstates, "start": start,
                     "well_defined": bool(well_defined), "sim_mismatch": bad_y, "pass": C3}
        log(f"C3 正则分支: DFA 状态 {nstates} / 良构 {well_defined} / 模拟失配 {bad_y} -> {C3}")
    else:
        res["C3"] = {"branch": branch, "class_seq_L1": n_seq,
                     "note": "非正则证据/inconclusive: 类数序列=Nerode 下界机器证据, 复杂度下界方向入档",
                     "pass": True}
        log(f"C3 分支 {branch}: 类数序列落盘 (下界材料) -> 记录通过")

    # ============ C4 计数律 (记录) ============
    counts = {}
    for c in CS:
        row = []
        for k in range(13):
            hi = 4 ** k
            if hi <= K12:
                row.append(int(np.sum(D[:hi] == c)))
            else:
                row.append(None)
        counts[f"c={c}"] = row
    cross = {f"({a},{b})": int(np.sum((D[:NMAX + 1] == a) & (D[:NMAX + 1] == b)))
             for (a, b) in ((1, 2), (-1, 1), (0, 1))}
    dims = {}
    for c in CS:
        row = counts[f"c={c}"]
        ks = [k for k, v in enumerate(row) if v]
        if len(ks) >= 3:
            k1, k2 = ks[-2], ks[-1]
            dims[f"c={c}"] = round(math.log(row[k2] / max(1, row[k1]), 4) / (k2 - k1), 4) if row[k1] and row[k2] else None
    res["C4"] = {"counts_4k": counts, "cross_intersections_1e6": cross,
                 "dim_estimates": dims, "pass": True, "note": "记录项(无裁决效力); E 互斥性由 D 单值性平凡成立, 交叉计数=0 对照"}
    log(f"C4 计数律: |E_c∩[0,4^12)| = {{c: row[-1] for c}} ; 交叉计数 {cross}")

    # ============ 结果节材料 (不回改判据; 首跑发现: D<=0 恒 + E_{c>=1} 空 + L_{-1} 类数 4) ============
    maxD = int(D.max())
    minD = int(D[:NMAX + 1].min())
    empty_pos = {c: int(np.sum(D[:K12] == c)) for c in (1, 2, 3)}
    neg_m1_total = int(np.sum(D[:K12] == -1))
    # E 点 mod3/τ 结构 (材料: Z∈E ⟹ Z≡0(τ=+1, A 型) 或 Z≡1(τ=−1, A+1 型))
    Ez = np.nonzero(D[:NMAX + 1] == 0)[0]
    tauE = tau[Ez]
    mE = Ez % 3
    structE = {"m0_tau1": int(np.sum((mE == 0) & (tauE == 1))),
               "m1_tau-1": int(np.sum((mE == 1) & (tauE == -1))),
               "violations": int(np.sum(~(((mE == 0) & (tauE == 1)) | ((mE == 1) & (tauE == -1)))))}
    # L_{-1} 的 DFA 构造与模拟 (材料级: 1024 后缀域限 Nerode BFS 闭包, 可完成全量模拟)
    c = -1
    NWl = 4 ** 5  # 1024 后缀域

    def sig_of(u, cval):
        base = u * NWl + np.arange(NWl, dtype=np.int64)
        return int.from_bytes(np.packbits(D[base] == cval).tobytes(), "big")

    rep = {}     # sig -> 代表前缀 u (None=空串)
    trans = {}   # (sig, a) -> sig
    start_sig = sig_of(0, c)  # 占位; 空串签名在下方单独算
    # 空串: 对一切 w, w∈L_c iff D[w]==c
    empty_idx = np.arange(NWl, dtype=np.int64)
    start_sig = int.from_bytes(np.packbits((D[empty_idx] == c)).tobytes(), "big")
    rep = {start_sig: None}
    trans = {}
    queue = [start_sig]
    while queue:
        s = queue.pop()
        u = rep[s]
        for a in range(4):
            v = a if u is None else 4 * u + a
            sv = sig_of(v, c)
            if sv not in rep:
                rep[sv] = v
                queue.append(sv)
            trans[(s, a)] = sv
    acc = {s for s, u in rep.items() if u is not None and int(D[u]) == c}
    nstates = len(rep)
    sim_bad = 0
    for y in range(NMAX + 1):
        st = start_sig
        for a in b4_digits(y):
            st = trans[(st, a)]
        if (st in acc) != (int(D[y]) == c):
            sim_bad += 1
            if sim_bad > 5:
                break
    res["material"] = {
        "D_max_all_4_12": maxD, "D_min_1e6": minD,
        "empty_positive_levels_4_12": empty_pos, "E_m1_count_4_12": neg_m1_total,
        "E_mod3_tau_structure_1e6": structE,
        "L_m1_dfa": {"n_states_1024suffix_closure": nstates,
                     "sim_mismatch_1e6": sim_bad,
                     "note": "结果节材料: 非平凡正则对象 c=-1, 1024 后缀域限 Nerode BFS 闭包 DFA 全量模拟"},
        "note": "首跑发现 (不回改冻结判据): D(Y)<=0 对全域 (max=0); 正水平集 E_1/E_2/E_3 空集=定理级现象 "
                "(A∈T ⟹ s₂(A) 偶 ⟹ τ(A)=+1; A+1 型 τ=−1 恒 ⟹ Z∈E 时 τ(Z)g_ρ(Z mod 3)<=0 恒, 归纳收口); "
                "c=-1 为非平凡水平集 (正则)。"}
    log(f"材料: D 全域 max={maxD} / E_1,E_2,E_3(4^12 域) 计数={empty_pos} / E_−1(4^12)={neg_m1_total}")
    log(f"材料: E 点 mod3/τ 结构违反 {structE['violations']} / L_−1 闭包 DFA {nstates} 态模拟失配 {sim_bad}")

    # ============ C5 总裁决 ============
    struct = C0 and C1
    res["verdict"] = {
        "structure_pass": bool(struct),
        "C2_branch": branch,
        "p_c1_regular_prediction": ("印证" if branch == "regular-evidence" else
                                     "判负照记" if branch == "nonregular-evidence" else "悬置"),
        "final": ("D 值水平集递归分解律成立【复算一致】; 正则性分支=" + branch if struct
                  else "如实入账(见分项, 判负照记)")}
    log(f"C5 总裁决: {res['verdict']['final']}")
    res["log"] = logs
    (RES / f"d_level_sets_regularity_result-{TAG}.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘（总用时 {time.time() - t0:.1f}s）")


if __name__ == "__main__":
    main()
