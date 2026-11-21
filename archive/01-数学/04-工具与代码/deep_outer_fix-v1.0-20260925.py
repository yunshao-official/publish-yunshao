# -*- coding: utf-8 -*-
# Fix 保持集结构刻画 + 深域外延伸与极值机理（R36 主格一+主格二·判据书 D-F 系/D-G 系实算）
# 判据书：代数册·深域外延伸与Fix保持集刻画预注册判据书-v1.0-20260925.md（冻结 2026-09-25 04:44:32）
# part1: D-F0 回归锚 / D-F1 档0保持完全闭式核 / D-F2 单非零位词闭式表 / D-F3 型剖分 / D-F4 型N子族谱
# part2: D-G0 深域外64档器产出 / D-G1 继承律21档 / D-G2 态数谱延拓与全谱回归 / D-G3 分解律归因 / D-G4 分带统计
import json
import numpy as np

OUT = "H:/理论存档/01-数学/02-实验与数据/results/deep_outer_fix-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T04:44:32"
N4 = 4 ** 12
N11 = 4 ** 11
G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]
FAC = [1, -1, -1, 1]
BINS = [0, 71, 200, 600, 1800, 5400, 16200, 48600, 177147]   # 8 几何带（R34/R35 冻结口径）
R35P1 = "H:/理论存档/01-数学/02-实验与数据/results/reverse_migration-part1-v1.0-20260925.json"
R35P2 = "H:/理论存档/01-数学/02-实验与数据/results/reverse_migration-part2-v1.0-20260925.json"
R34P2 = "H:/理论存档/01-数学/02-实验与数据/results/outlayer_catalog-part2-v1.0-20260925.json"

# ---------- 全域 DP（值索引口径·R34/R35 修正口径复用） ----------
def dp_full(L=12):
    Gtab = np.array(G, dtype=np.int64)
    fac = np.array(FAC, dtype=np.int64)
    ys = np.arange(1, dtype=np.int64)
    Ds = np.zeros(1, dtype=np.int64); ts = np.ones(1, dtype=np.int64); ms = np.zeros(1, dtype=np.int64)
    for lay in range(L):
        parts_D, parts_y, parts_t, parts_m = [], [], [], []
        for r in range(4):
            parts_D.append(Ds * 3 + ts * Gtab[r][ms])
            parts_y.append(ys * 4 + r)
            parts_t.append(ts * fac[r]); parts_m.append((ms + r) % 3)
        ys = np.concatenate(parts_y); Ds = np.concatenate(parts_D)
        ts = np.concatenate(parts_t); ms = np.concatenate(parts_m)
    perm = np.argsort(ys, kind="stable")
    return ys[perm], Ds[perm], ts[perm], ms[perm]

def rev_map():
    y = np.arange(N4, dtype=np.int64); rv = np.zeros(N4, dtype=np.int64)
    for _ in range(12):
        rv = rv * 4 + (y & 3); y >>= 2
    return rv

def digits_of(y, L):
    ds = np.zeros((y.size, L), dtype=np.int64)
    for i in range(L):
        ds[:, L - 1 - i] = y % 4; y = y // 4
    return ds

# ---------- part1（㉜ Fix 保持集刻画） ----------
def run_part1():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    assert (ys == np.arange(N4, dtype=np.int64)).all()
    del ys, ts
    aD = -Ds
    rv = rev_map()
    Drev = Ds[rv]
    fixm = (Ds == Drev)
    palmask = np.zeros(N4, dtype=bool)
    p6 = np.arange(4096, dtype=np.int64)
    dg6 = digits_of(p6, 6)
    pal = (dg6 * (4 ** np.arange(5, -1, -1))).sum(axis=1) * 4096 + (dg6[:, ::-1] * (4 ** np.arange(5, -1, -1))).sum(axis=1)
    palmask[pal] = True
    # D-F0 回归锚（R35 DI4 七字段）
    r35 = json.load(open(R35P1, encoding="utf-8"))["DI4"]
    n_fix = int(fixm.sum())
    fix_pal = int((fixm & palmask).sum())
    fix_nonpal = n_fix - fix_pal
    b1 = np.clip(np.digitize(aD, BINS) - 1, 0, 7)
    fix_band = [int(((b1 == i) & fixm).sum()) for i in range(8)]
    fix_sub200 = np.bincount(aD[fixm & (aD <= 200)], minlength=201)
    nfix0 = int((fixm & (aD == 0)).sum()); pal0 = int((palmask & (aD == 0)).sum())
    anchor_bad = 0
    for name, got, exp in [("n_fix", n_fix, r35["n_fix"]), ("fix_pal", fix_pal, r35["fix_and_pal"]),
                           ("nonpal", fix_nonpal, r35["fix_nonpal"]), ("nfix0", nfix0, r35["nfix0"]),
                           ("pal0", pal0, r35["pal0"])]:
        if got != exp: anchor_bad += 1; log.append("DF0 MISMATCH %s got=%d exp=%d" % (name, got, exp))
    if fix_band != r35["fix_band"]: anchor_bad += 1; log.append("DF0 band mismatch")
    if [int(x) for x in fix_sub200[:4]] != r35["fix_sub200"][:4]: anchor_bad += 1; log.append("DF0 sub200 head mismatch")
    log.append("DF0 anchor_bad=%d (n_fix=%d pal=%d nonpal=%d nfix0=%d pal0=%d)" %
               (anchor_bad, n_fix, fix_pal, fix_nonpal, nfix0, pal0))
    # D-F1 档0保持完全闭式核：Fix∩E0 == {0,3}* ∪ {单1}
    arr = np.array([0], dtype=np.int64)
    for _ in range(12):
        arr = np.concatenate([arr * 4, arr * 4 + 3])
    pure3 = np.sort(arr)
    single1 = np.sort(np.array([4 ** j for j in range(11, -1, -1)], dtype=np.int64))
    S0 = np.sort(np.concatenate([pure3, single1]))
    fixE0 = np.sort(np.nonzero(fixm & (aD == 0))[0])
    set_eq = (fixE0.shape == S0.shape) and bool((fixE0 == S0).all())
    palE0 = np.sort(np.nonzero(palmask & (aD == 0))[0])
    pal_pure3 = np.intersect1d(pal, pure3)
    pal_eq = (palE0.shape == pal_pure3.shape) and bool((palE0 == pal_pure3).all())
    df1_bad = (0 if set_eq else 1) + (0 if (pal_eq and len(palE0) == 64) else 1)
    log.append("DF1 set_eq=%s n_fixE0=%d (pure3=%d+single1=%d) pal_eq=%s n_palE0=%d bad=%d" %
               (set_eq, len(fixE0), len(pure3), len(single1), pal_eq, len(palE0), df1_bad))
    # D-F2 单非零位词闭式表
    rows = []; df2_bad = 0
    for y in (1, 2, 3):
        for k in range(1, 13):
            val = y * (4 ** (12 - k))
            Dm = int(Ds[val]); Drm = int(Ds[rv[val]])
            g0 = G[y][0]
            cl = (3 ** (12 - k)) * g0; clr = (3 ** (k - 1)) * g0
            kp = bool(g0 == 0 or k == 7); kr = bool(Dm == Drm)
            bad = int(Dm != cl) + int(Drm != clr) + int(kp != kr)
            df2_bad += bad
            rows.append({"y": y, "k": k, "D": Dm, "Drev": Drm, "closed": int(cl),
                         "closed_rev": int(clr), "keep_pred": kp, "keep_real": kr, "bad": bad})
    n_keep = sum(1 for r in rows if r["keep_real"])
    log.append("DF2 48-word closed-form bad=%d keep=%d (pred 25)" % (df2_bad, n_keep))
    # D-F3 型剖分
    typeZ = nfix0; typeN = n_fix - typeZ
    typeN_pal = int((fixm & palmask & (aD != 0)).sum())
    typeN_nonpal = int((fixm & ~palmask & (aD != 0)).sum())
    df3_bad = int(typeZ != 4108) + int(typeN != 41204) + int(typeN_pal != 4032) + int(typeN_nonpal != 37172)
    log.append("DF3 typeZ=%d typeN=%d typeN_pal=%d typeN_nonpal=%d bad=%d" %
               (typeZ, typeN, typeN_pal, typeN_nonpal, df3_bad))
    # D-F4 型N子族谱+生成规则判定输出
    y32 = np.arange(N4, dtype=np.uint32)
    has2 = np.zeros(N4, dtype=bool); ones = np.zeros(N4, dtype=np.uint8); nzc = np.zeros(N4, dtype=np.uint8)
    for i in range(12):
        d = (y32 >> (2 * i)) & np.uint32(3)
        has2 |= (d == 2); ones += (d == 1).astype(np.uint8); nzc += (d != 0).astype(np.uint8)
    del y32
    grp = {}
    def jkey(j): return str(j) if j < 3 else "ge3"
    for h2 in (False, True):
        for j in (0, 1, 2, 3):
            jm = (ones == j) if j < 3 else (ones >= 3)
            gm = (has2 == h2) & jm
            cnt = int(gm.sum()); fx = int((gm & fixm).sum())
            grp["has2=%s,ones=%s" % (h2, jkey(j))] = {"n": cnt, "fix": fx,
                                                      "rate": round(fx / cnt, 6) if cnt else None}
    rate_no2 = grp["has2=False,ones=0"]["fix"] + grp["has2=False,ones=1"]["fix"] + \
               grp["has2=False,ones=2"]["fix"] + grp["has2=False,ones=ge3"]["fix"]
    n_no2 = grp["has2=False,ones=0"]["n"] + grp["has2=False,ones=1"]["n"] + \
            grp["has2=False,ones=2"]["n"] + grp["has2=False,ones=ge3"]["n"]
    rate_has2 = n_fix - rate_no2; n_has2 = N4 - n_no2
    cand_a = (rate_no2 / n_no2) > (rate_has2 / n_has2)
    r_1 = grp["has2=False,ones=1"]["rate"]; r_m = ((grp["has2=False,ones=2"]["fix"] + grp["has2=False,ones=ge3"]["fix"]) /
                                                   max(1, grp["has2=False,ones=2"]["n"] + grp["has2=False,ones=ge3"]["n"]))
    cand_b = r_1 > r_m
    log.append("DF4 rate(no2)=%.6f vs rate(has2)=%.6f candA=%s ; rate(1-once)=%s vs rate(multi1)=%.6f candB=%s" %
               (rate_no2 / n_no2, rate_has2 / n_has2, cand_a, r_1, r_m, cand_b))
    # 富集比：Fix 非零位计数分布 vs 全域
    nz_hist_fix = np.bincount(nzc[fixm].astype(np.int64), minlength=13)
    nz_hist_all = np.bincount(nzc.astype(np.int64), minlength=13)
    enrich = [round(float(nz_hist_fix[i] / max(n_fix, 1)) / max(nz_hist_all[i] / N4, 1e-12), 4)
              for i in range(1, 13)]
    # 逐带样本（每带 5 个 Fix 词：词值/D/revD/非零位序列·y1..y12 序）
    samples = {}
    fix_idx_pool = np.nonzero(fixm)[0]
    for bi in range(8):
        msk = (b1[fix_idx_pool] == bi)
        sel = fix_idx_pool[msk][:5]
        lst = []
        for w in sel:
            dg = digits_of(np.array([int(w)], dtype=np.int64), 12)[0]
            nzseq = "".join(str(x) for x in dg if x != 0)
            lst.append([int(w), int(Ds[w]), int(Drev[w]), nzseq])
        samples[str(bi)] = lst
    res = {"meta": {"script": "deep_outer_fix-v1.0-20260925.py", "frozen": FROZEN},
           "DF0": {"anchor_bad": anchor_bad, "n_fix": n_fix, "fix_pal": fix_pal, "nonpal": fix_nonpal,
                    "nfix0": nfix0, "pal0": pal0, "fix_band": fix_band},
           "DF1": {"set_eq": set_eq, "n_fixE0": int(len(fixE0)), "pal_eq": pal_eq, "n_palE0": int(len(palE0)),
                    "bad": df1_bad},
           "DF2": {"bad": df2_bad, "n_keep": n_keep, "rows": rows},
           "DF3": {"typeZ": typeZ, "typeN": typeN, "typeN_pal": typeN_pal, "typeN_nonpal": typeN_nonpal,
                    "bad": df3_bad},
           "DF4": {"groups": grp, "candA_no2_gt_has2": bool(cand_a), "candB_1once_gt_multi": bool(cand_b),
                    "enrich_nz_1_12": enrich, "samples_by_band": samples},
           "log": log}
    del Drev, fixm, palmask, b1, has2, ones, nzc, fix_sub200
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return Ds, ms

# ---------- part2（㉛ 深域外延伸） ----------
SIGN = [1, -1, -1, 1]
DEEP64 = list(range(-128, -192, -1))
INH21 = [c for c in DEEP64 if c % 3 == 0]
DOM72 = list(range(0, -72, -1))
MID56 = list(range(-72, -128, -1))

def step(state, rho):
    d, sg, mu = state
    return (3 * d + sg * G[rho][mu], sg * SIGN[rho], (mu + rho) % 3)

def rev_closure(c):
    R = set((c, sg, m) for sg in (1, -1) for m in range(3))
    frontier = list(R)
    while frontier:
        cur = frontier.pop(); d = cur[0]
        if d == 0:
            continue
        for rho in range(4):
            for mu in range(3):
                for sg in (1, -1):
                    gamma = sg * G[rho][mu]
                    if (d - gamma) % 3 == 0:
                        p = ((d - gamma) // 3, sg, mu)
                        if p not in R:
                            R.add(p); frontier.append(p)
    return R

def build_dfa(c):
    START = (0, 1, 0)
    R = rev_closure(c); R.add(START)
    states = sorted(R); idx = {s: i for i, s in enumerate(states)}
    trans = np.full((len(states), 4), -1, dtype=np.int64)
    for i, s in enumerate(states):
        for rho in range(4):
            trans[i, rho] = idx.get(step(s, rho), -1)
    reach = {idx[START]}; stack = [idx[START]]
    while stack:
        u = stack.pop()
        for rho in range(4):
            v = int(trans[u, rho])
            if v >= 0 and v not in reach:
                reach.add(v); stack.append(v)
    keep = sorted(reach); kidx = {states[i]: i2 for i2, i in enumerate(keep)}
    tr2 = np.full((len(keep), 4), -1, dtype=np.int64)
    for i2, i in enumerate(keep):
        for rho in range(4):
            v = int(trans[i, rho])
            tr2[i2, rho] = kidx[states[v]] if v >= 0 else -1
    q0 = kidx[START]
    accept = [i2 for i2, i in enumerate(keep) if states[i][0] == c]
    return [states[i] for i in keep], tr2, q0, accept

def moore_min(tr, accept_set):
    n = tr.shape[0]; DEAD = n; N = n + 1
    TR = np.full((N, 4), DEAD, dtype=np.int64)
    TR[:n] = np.where(tr >= 0, tr, DEAD); TR[DEAD, :] = DEAD
    lab = np.zeros(N, dtype=np.int64)
    for a in accept_set: lab[a] = 1
    while True:
        sig = {}; newlab = np.zeros(N, dtype=np.int64)
        for i in range(N):
            key = (int(lab[i]),) + tuple(int(lab[int(TR[i, r])]) for r in range(4))
            if key not in sig: sig[key] = len(sig)
            newlab[i] = sig[key]
        if len(sig) == len(set(lab.tolist())):
            return len(sig)
        lab = newlab

def nerode_sig(c, Ds, pf_bits=6, sf_bits=6):
    import hashlib, struct
    okb = (Ds == c)
    sigs = set()
    for a in range(4 ** pf_bits):
        h = hashlib.md5()
        for l in range(sf_bits + 1):
            base = a * (4 ** l); cnt = 4 ** l
            if base >= N4: break
            if base + cnt > N4: cnt = N4 - base
            chb = np.packbits(okb[base:base + cnt]).tobytes()
            h.update(struct.pack("<I", len(chb))); h.update(chb)
        sigs.add(h.digest())
    return len(sigs)

def active_dead(keep_states, tr2, accept):
    n = len(keep_states)
    rev_adj = [[] for _ in range(n)]
    for u in range(n):
        for rho in range(4):
            v = int(tr2[u, rho])
            if v >= 0:
                rev_adj[v].append(u)
    act = set(int(a) for a in accept); st = list(act)
    while st:
        v = st.pop()
        for u in rev_adj[v]:
            if u not in act:
                act.add(u); st.append(u)
    return len(keep_states) - len(act)

def mobius(n):
    if n <= 0: return 0
    res = 1; m = n
    p = 2
    while p * p <= m:
        if m % p == 0:
            m //= p
            if m % p == 0: return 0
            res = -res
        p += 1
    if m > 1: res = -res
    return res

def mint_layers(c):
    """满足 3^L|c 且 |c/3^L|>=2 的层数（R28 IntPairs 闭式的层集）"""
    n = 0; L = 1
    while 3 ** L <= abs(c):
        if c % (3 ** L) == 0 and abs(c) // (3 ** L) >= 2:
            n += 1
        L += 1
    return n

def mint_closed_variants(c):
    """R28 闭式解读三候选（判定输出）：C1=R28 报告字面 2·#{L}；C2=#{L}（每降层对省 1 态·
    R28 结论行「2·」系数与「每对省 1」矛盾——机器裁决候选）；C3=判据书 μ̃ 加权版（冻结主口径）"""
    n = mint_layers(c)
    c3 = 0; L = 1
    while 3 ** L <= abs(c):
        if c % (3 ** L) == 0:
            d = abs(c) // (3 ** L)
            if d >= 2:
                mu = mobius(d)
                if mu == 1: c3 += 2
                elif mu == -1: c3 += 4
        L += 1
    return {"C1_2times_layers": 2 * n, "C2_layers": n, "C3_mu_tilde_weighted": c3}

def d_band(c):
    if c == 0: return 0
    m = abs(c); d = 0
    while m >= 3:
        m //= 3; d += 1
    return d

def law_four(c, Ds, ms, R_from=None, hist_all=None):
    """分解律四件套（R26 修正轨口径）：reach/acc/M_acc/M_dead/M_int 反解+R Moore
    （首跑拦截实现层修正：M_int 反解式 M_int=reach+1−M_acc−M_dead−R（前版符号反转滑误照记））"""
    keep_states, tr, q0, acc = build_dfa(c)
    reach = len(keep_states); accn = len(acc)
    m_acc = accn - 1
    m_dead = active_dead(keep_states, tr, acc)
    Rm = int(moore_min(tr, acc)) if R_from is None else int(R_from)
    m_int = reach + 1 - m_acc - m_dead - Rm
    return {"reach": reach, "acc": accn, "M_acc": m_acc, "M_dead": m_dead,
            "M_int": int(m_int), "R": int(Rm),
            "law_ok": bool(m_int >= 0 and Rm == reach + 1 - m_acc - m_dead - m_int),
            "mintC": mint_closed_variants(c)}

def run_part2(Ds=None, ms=None):
    log = []
    if Ds is None:
        ys, Ds, ts, ms = dp_full(12)
        assert (ys == np.arange(N4, dtype=np.int64)).all()
        del ys, ts
    aD = -Ds
    hist_all = np.bincount(aD, minlength=177148)
    # D-G0 深域外 64 档器产出
    dg0 = {}; dfa_bad = 0
    for c in DEEP64:
        cnt = int(hist_all[-c])
        keep_states, tr, q0, acc = build_dfa(c)
        Rm = moore_min(tr, acc)
        Nn = nerode_sig(c, Ds)
        rec = {"c": int(c), "n_words": cnt, "R_moore": int(Rm), "R_nerode": int(Nn),
               "moore_eq_nerode": bool(Rm == Nn)}
        dfa_bad += 0 if rec["moore_eq_nerode"] else 1
        dg0[str(c)] = rec
    mutex = len(set(dg0[k]["c"] for k in dg0)) == 64
    log.append("DG0 64-gear dfa_bad=%d R=%s mutex=%s" %
               (dfa_bad, str([dg0[str(c)]["R_moore"] for c in DEEP64]), str(mutex)))
    # D-G1 继承律 21 档
    dg1 = {}; dg1_bad = 0; pure_list = []
    for c in sorted(INH21, reverse=True):
        src = c // 3
        zmask11 = (Ds[:N11] == src)
        zs = np.nonzero(zmask11)[0]
        mu0 = (ms[:N11] == 0)
        xsrc = zs[mu0[zs]]
        inherit = 4 * zs
        Xw = np.concatenate([4 * xsrc + 1, 4 * xsrc + 3])
        pred = np.concatenate([inherit, Xw])
        Ec = np.nonzero(Ds == c)[0]
        ps = np.sort(pred); es = np.sort(Ec)
        eq = (ps.shape == es.shape) and bool((ps == es).all())
        tail_ok = bool((Xw % 4 == 1).sum() + (Xw % 4 == 3).sum() == len(Xw))
        src_ok = True
        if len(Xw):
            zback = Xw >> 2
            src_ok = bool(zmask11[zback].all() and mu0[zback].all())
        pure = (len(Xw) == 0)
        if pure: pure_list.append(c)
        if not (eq and tail_ok and src_ok): dg1_bad += 1
        dg1[str(c)] = {"c": int(c), "src": int(src), "n_Ec": int(len(Ec)), "n_4E": int(len(inherit)),
                       "n_X": int(len(Xw)), "pure": pure, "wordset_eq": eq,
                       "tail_ok": tail_ok, "src_ok": src_ok}
    log.append("DG1 inherit21 bad=%d pure=%s" % (dg1_bad, str(pure_list)))
    contain_bad = 0
    for c in INH21:
        zs = np.nonzero(Ds[:N11] == c // 3)[0]
        if zs.size and not (Ds[4 * zs] == c).all():
            contain_bad += 1
    log.append("DG1 contain4E bad=%d" % contain_bad)
    # D-G2 域内 72 档重算回归（含分解律四件套增信）+ −72..−127 对照 + 深域外谱
    dom = {}; dom_law = {}; mint_variant_ok = {"C1_2times_layers": 0, "C2_layers": 0, "C3_mu_tilde_weighted": 0}
    for c in DOM72:
        lw = law_four(c, Ds, ms)
        dom[str(c)] = lw["R"]; dom_law[str(c)] = lw
        if c % 3 != 0:
            pass
        for kk in mint_variant_ok:
            if lw["M_int"] == lw["mintC"][kk]:
                mint_variant_ok[kk] += 1
    anchor = {"-55": 14, "-35": 13, "-29": 12, "-11": 10}
    anchor_bad = sum(1 for k, v in anchor.items() if dom[k] != v)
    dom_max_c = max(dom, key=lambda k: dom[k])
    law_dom_bad = sum(1 for c in DOM72 if not dom_law[str(c)]["law_ok"])
    # M_int 闭式候选在域内的关键锚：E-45=2（R29 四件套在档）/E-9=2/E-18/E-27
    mint_anchor = {k: {"solved": dom_law[k]["M_int"],
                        "variants": dom_law[k]["mintC"]} for k in ("-9", "-18", "-27", "-45", "-54")}
    log.append("DG2 dom72 anchor_bad=%d dom_max=%s@%s law_dom_bad=%d mint_variant_ok(in72)=%s" %
               (anchor_bad, dom[dom_max_c], dom_max_c, law_dom_bad, json.dumps(mint_variant_ok)))
    log.append("DG2 mint anchors %s" % json.dumps(mint_anchor))
    # 锚四点 Nerode 增信
    nerd_anchor = {}
    for c in (-11, -29, -35, -55):
        nerd_anchor[str(c)] = int(nerode_sig(c, Ds))
    anchor_nerd_bad = sum(1 for c in (-11, -29, -35, -55) if nerd_anchor[str(c)] != dom[str(c)])
    log.append("DG2 anchor nerode=%s bad=%d" % (json.dumps(nerd_anchor), anchor_nerd_bad))
    # −72..−127 56 档重算 Moore 对照在档
    r35p2 = json.load(open(R35P2, encoding="utf-8"))
    r34p2 = json.load(open(R34P2, encoding="utf-8"))
    mid_cmp = {}; mid_bad = 0
    for c in MID56:
        keep_states, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min(tr, acc))
        if c >= -79:
            arch = r34p2["DH3"]["eight"][str(c)]["R_moore"]
        else:
            arch = r35p2["DJ0"]["gear48"][str(c)]["R_moore"]
        ok = (Rm == arch)
        if not ok: mid_bad += 1
        mid_cmp[str(c)] = {"recompute": Rm, "archive": int(arch), "eq": ok}
    log.append("DG2 mid56 vs archive bad=%d" % mid_bad)
    deep_R = [dg0[str(c)]["R_moore"] for c in DEEP64]
    all_R = list(dom.values()) + [mid_cmp[str(c)]["recompute"] for c in MID56] + deep_R
    all_c = DOM72 + MID56 + DEEP64
    gmax = max(all_R); gmax_at = all_c[all_R.index(gmax)]
    prev = r35p2["DJ2"]["max_R"]; prev_at = r35p2["DJ2"]["max_at"]
    log.append("DG2 full-spectrum(0..-191) max=%d@%d (R35 archive max=%d@%d refreshed=%s)" %
               (gmax, gmax_at, prev, prev_at, str((gmax, gmax_at) != (prev, prev_at))))
    # D-G3 分解律归因（深域外 64 档 + −105..−109 明细）
    dg3 = {}; law_bad = 0; mint_bad = 0
    mint_variant_ok_deep = {"C1_2times_layers": 0, "C2_layers": 0, "C3_mu_tilde_weighted": 0}
    for c in DEEP64:
        lw = law_four(c, Ds, ms, R_from=dg0[str(c)]["R_moore"])
        mc = lw["mintC"]
        ok_law = lw["law_ok"]
        ok_mint_C1 = (lw["M_int"] == mc["C1_2times_layers"])
        ok_mint_C3 = (lw["M_int"] == mc["C3_mu_tilde_weighted"])
        if not ok_law: law_bad += 1
        if not ok_mint_C3: mint_bad += 1
        for kk in mint_variant_ok_deep:
            if lw["M_int"] == mc[kk]:
                mint_variant_ok_deep[kk] += 1
        dg3[str(c)] = {"reach": lw["reach"], "acc": lw["acc"], "M_acc": lw["M_acc"],
                       "M_dead": lw["M_dead"], "M_int": lw["M_int"],
                       "M_int_closed": mc, "R": lw["R"],
                       "law_ok": ok_law, "mint_ok_C1": ok_mint_C1, "mint_ok_C3": ok_mint_C3,
                       "pure_inh": c in pure_list}
    detail = {}
    for c in list(range(-105, -110, -1)) + [-107]:
        if str(c) in dg3:
            detail[str(c)] = dg3[str(c)]
        else:
            lw = law_four(c, Ds, ms)
            lw["mint_ok_C1"] = (lw["M_int"] == lw["mintC"]["C1_2times_layers"])
            lw["mint_ok_C3"] = (lw["M_int"] == lw["mintC"]["C3_mu_tilde_weighted"])
            lw["pure_inh"] = False
            detail[str(c)] = lw
            if not lw["law_ok"]: law_bad += 1
    r107 = detail["-107"]
    log.append("DG3 law_bad=%d mintC3_bad=%d mint_variant_ok(deep64)=%s E-107 detail=%s" %
               (law_bad, mint_bad, json.dumps(mint_variant_ok_deep),
                json.dumps({"reach": r107["reach"], "M_acc": r107["M_acc"], "M_dead": r107["M_dead"],
                            "M_int": r107["M_int"], "R": r107["R"]})))
    # 合成律样本核（纯继承档前 3 档·R(c)==R(c/3)+1·域内重算谱为源）
    synth = {}
    for c in pure_list[:3]:
        synth[str(c)] = {"R": dg0[str(c)]["R_moore"], "R_src_plus1": dom[str(c // 3)] + 1}
    synth_ok = all(v["R"] == v["R_src_plus1"] for v in synth.values()) if synth else None
    log.append("DG1 synth %s ok=%s" % (json.dumps(synth), str(synth_ok)))
    # D-G4 分带统计（全谱 0..−191 192 档·d=⌊log₃|c|⌋；d=4 带覆盖 −81..−191 段·−192..−242 未测如实声明）
    bands = {}
    for c, R in zip(all_c, all_R):
        d = d_band(c)
        key = str(d)
        bands.setdefault(key, []).append((c, R, c % 3 == 0))
    stat = {}
    for d in sorted(bands):
        rows = bands[d]
        Rs = [r[1] for r in rows]
        inh = [r[1] for r in rows if r[2]]; non = [r[1] for r in rows if not r[2]]
        stat[d] = {"n": len(rows), "range_c": [min(abs(x[0]) for x in rows if x[0] != 0) * (1 if any(x[0] < 0 for x in rows) else 0), max(abs(x[0]) for x in rows)],
                   "all": {"min": min(Rs), "max": max(Rs), "mean": round(sum(Rs) / len(Rs), 3)},
                   "inherit": {"n": len(inh), "min": min(inh) if inh else None, "max": max(inh) if inh else None,
                               "mean": round(sum(inh) / len(inh), 3) if inh else None},
                   "noninherit": {"n": len(non), "min": min(non) if non else None, "max": max(non) if non else None,
                                  "mean": round(sum(non) / len(non), 3) if non else None}}
    # R35 报告句核查：域内 72 档 max
    in72max = dom[dom_max_c]
    r35_claim = 7
    claim_check = {"R35_report_claim_in72_max": r35_claim, "recompute_in72_max": int(in72max),
                   "recompute_in72_argmax": int(dom_max_c),
                   "contradiction": bool(in72max != r35_claim)}
    log.append("DG4 bands=%s" % json.dumps(stat))
    log.append("DG4 in72max check: %s" % json.dumps(claim_check))
    res = {"meta": {"script": "deep_outer_fix-v1.0-20260925.py", "frozen": FROZEN},
           "DG0": {"gear64": dg0, "dfa_bad": dfa_bad, "mutex": mutex},
           "DG1": {"records": dg1, "bad": dg1_bad, "pure_list": pure_list, "contain_bad": contain_bad,
                    "synth_check": synth, "synth_ok": synth_ok},
           "DG2": {"dom72": dom, "anchor_bad": anchor_bad, "anchor_nerode": nerd_anchor,
                    "anchor_nerd_bad": anchor_nerd_bad, "dom_max": {"c": int(dom_max_c), "R": int(dom[dom_max_c])},
                    "law_dom_bad": law_dom_bad, "mint_variant_ok_in72": mint_variant_ok,
                    "mint_anchors": mint_anchor,
                    "mid56_cmp": mid_cmp, "mid_bad": mid_bad,
                    "deep_R": deep_R, "full_max": {"R": int(gmax), "at": int(gmax_at)},
                    "archive_max": {"R": int(prev), "at": int(prev_at)}},
           "DG3": {"records": dg3, "law_bad": law_bad, "mintC3_bad": mint_bad,
                    "mint_variant_ok_deep64": mint_variant_ok_deep, "detail_105_109": detail},
           "DG4": {"bands": stat, "claim_check": claim_check},
           "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

if __name__ == "__main__":
    import sys
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part in ("all", "part1"):
        Ds1, ms1 = run_part1()
        if part == "all":
            run_part2(Ds1, ms1)
    elif part == "part2":
        run_part2(None, None)
