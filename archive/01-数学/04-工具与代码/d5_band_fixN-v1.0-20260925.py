# -*- coding: utf-8 -*-
# d5 带深域外验证 + 型 N 完全刻画（R37 主格一+主格二·判据书 D-K 系/D-N 系实算）
# 判据书：代数册·d5带验证与型N完全刻画预注册判据书-v1.0-20260925.md（冻结 2026-09-25 05:19:45）
# 用法: python d5_band_fixN-v1.0-20260925.py all | part1 | part2 | band START END | merge
# part1: D-K0 锚+双实现对照 / D-K1 64档器 / D-K2 继承21档 / D-K3 段max=20 三态 / D-K5 分解律+C2+归因
# part2: D-N0 锚 / D-N1 回文保持 / D-N2 对合配对 / D-N3 继承切片闭式 102 档 / D-N4 逐档谱四分量
# band : D-K4 全带快扫 c=START..END（Moore 向量化单通道+词数）
# merge: 全带统计（max 对表 20 三态）+全带 max 档 Nerode/law_four+seed 抽样 5 档 Nerode 增信+分带统计
import json
import sys
import numpy as np

OUT = "H:/理论存档/01-数学/02-实验与数据/results/d5_band_fixN-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T05:19:45"
N4 = 4 ** 12
N11 = 4 ** 11
G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]
FAC = [1, -1, -1, 1]
R36P1 = "H:/理论存档/01-数学/02-实验与数据/results/deep_outer_fix-part1-v1.0-20260925.json"
R36P2 = "H:/理论存档/01-数学/02-实验与数据/results/deep_outer_fix-part2-v1.0-20260925.json"
R35P2 = "H:/理论存档/01-数学/02-实验与数据/results/reverse_migration-part2-v1.0-20260925.json"
SEG64 = list(range(-243, -307, -1))          # 本轮段 64 档
INH21 = [c for c in SEG64 if c % 3 == 0]     # 继承 21 档
SRCS = sorted(set(c // 3 for c in INH21), reverse=True)   # 源档 -81..-102
SLICE102 = list(range(-3, -307, -3))         # 在档 3|c 档全集 102 档（D-N3）

# ---------- 全域 DP（值索引口径·R34/R35/R36 修正口径复用） ----------
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

def step(state, rho):
    d, sg, mu = state
    return (3 * d + sg * G[rho][mu], sg * FAC[rho], (mu + rho) % 3)

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
    """R36 逐点循环版（锚对照用）"""
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

def moore_min_vec(tr, accept_set):
    """向量化标签细化（本轮新实现·与循环版同一不动点迭代·锚档双实现对照预注册）"""
    n = tr.shape[0]; DEAD = n; N = n + 1
    TR = np.full((N, 4), DEAD, dtype=np.int64)
    TR[:n] = np.where(tr >= 0, tr, DEAD); TR[DEAD, :] = DEAD
    lab = np.zeros(N, dtype=np.int64)
    for a in accept_set: lab[a] = 1
    while True:
        key = np.concatenate([lab[:, None], lab[TR]], axis=1)
        uni, newlab = np.unique(key, axis=0, return_inverse=True)
        if int(uni.shape[0]) == int(np.unique(lab).size):
            return int(uni.shape[0])
        lab = newlab.astype(np.int64)

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

def mint_layers(c):
    """C2 正本：满足 3^L|c 且 |c/3^L|>=2 的层数（R36 机器裁决）"""
    n = 0; L = 1
    while 3 ** L <= abs(c):
        if c % (3 ** L) == 0 and abs(c) // (3 ** L) >= 2:
            n += 1
        L += 1
    return n

def law_four(c, Ds, ms, R_from=None):
    """分解律四件套（R26 修正轨口径·R36 修正版 M_int 反解）"""
    keep_states, tr, q0, acc = build_dfa(c)
    reach = len(keep_states); accn = len(acc)
    m_acc = accn - 1
    m_dead = active_dead(keep_states, tr, acc)
    Rm = int(moore_min_vec(tr, acc)) if R_from is None else int(R_from)
    m_int = reach + 1 - m_acc - m_dead - Rm
    return {"reach": reach, "acc": accn, "M_acc": m_acc, "M_dead": m_dead,
            "M_int": int(m_int), "R": int(Rm), "C2": mint_layers(c),
            "law_ok": bool(m_int >= 0 and Rm == reach + 1 - m_acc - m_dead - m_int)}

def inherit_check(cs, Ds, ms, R_of_src=None):
    """继承律 W11 口径词集级恒等核（R34/R35/R36 正本口径）"""
    dsub = Ds[:N11]; mu0 = (ms[:N11] == 0)
    recs = {}; bad = 0; pure_list = []
    for c in cs:
        s = c // 3
        zs = np.nonzero(dsub == s)[0]
        xsrc = zs[mu0[zs]]
        inherit = 4 * zs
        Xw = np.concatenate([4 * xsrc + 1, 4 * xsrc + 3])
        pred = np.sort(np.concatenate([inherit, Xw]))
        Ec = np.sort(np.nonzero(Ds == c)[0])
        eq = (pred.shape == Ec.shape) and bool((pred == Ec).all())
        tail_ok = bool(((Xw % 4 == 1).sum() + (Xw % 4 == 3).sum()) == len(Xw))
        src_ok = True
        if len(Xw):
            zback = Xw >> 2
            src_ok = bool((dsub[zback] == s).all() and mu0[zback].all())
        contain = True
        if zs.size:
            contain = bool((Ds[4 * zs] == c).all())
        pure = (len(Xw) == 0)
        if pure: pure_list.append(c)
        ok = bool(eq and tail_ok and src_ok and contain)
        if not ok: bad += 1
        recs[str(c)] = {"src": int(s), "n_Ec": int(len(Ec)), "n_4E": int(len(inherit)),
                        "n_X": int(len(Xw)), "pure": pure, "eq": eq, "tail_ok": tail_ok,
                        "src_ok": src_ok, "contain": contain, "ok": ok}
    return recs, bad, pure_list

# ---------- part1（㉞ d=5 带） ----------
def run_part1(Ds=None, ms=None):
    log = []
    if Ds is None:
        ys, Ds, ts, ms = dp_full(12)
        assert (ys == np.arange(N4, dtype=np.int64)).all()
        del ys, ts
    aD = -Ds
    hist_all = np.bincount(aD, minlength=177148)
    # D-K0 回归锚+双实现对照
    r36 = json.load(open(R36P2, encoding="utf-8"))
    anchor_bad = 0
    dual = {}
    for c in (-11, -29, -35, -55, -128, -129, -130, -131):
        ks, tr, q0, acc = build_dfa(c)
        R_loop = int(moore_min(tr, acc))
        R_vec = int(moore_min_vec(tr, acc))
        dual[str(c)] = {"loop": R_loop, "vec": R_vec}
        if R_loop != R_vec: anchor_bad += 1; log.append("DK0 dual mismatch @%d" % c)
    dom_anchor = {"-55": 14, "-35": 13, "-29": 12, "-11": 10}
    for k, v in dom_anchor.items():
        if dual[k]["vec"] != v: anchor_bad += 1; log.append("DK0 dom anchor mismatch @%s" % k)
    head4_bad = 0
    for c in (-128, -129, -130, -131):
        arch = r36["DG0"]["gear64"][str(c)]
        if dual[str(c)]["vec"] != arch["R_moore"] or hist_all[-c] != arch["n_words"]:
            head4_bad += 1; log.append("DK0 head4 mismatch @%d" % c)
    anchor_bad += head4_bad
    log.append("DK0 anchor_bad=%d dual=%s" % (anchor_bad, json.dumps(dual)))
    # D-K1 64 档器产出
    dg1 = {}; dfa_bad = 0
    for c in SEG64:
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        Nn = int(nerode_sig(c, Ds))
        rec = {"c": int(c), "n_words": int(hist_all[-c]), "R_moore": Rm, "R_nerode": Nn,
               "moore_eq_nerode": bool(Rm == Nn)}
        dfa_bad += 0 if rec["moore_eq_nerode"] else 1
        dg1[str(c)] = rec
    mutex = len(set(dg1[k]["c"] for k in dg1)) == 64
    log.append("DK1 gear64 dfa_bad=%d R=%s mutex=%s" %
               (dfa_bad, str([dg1[str(c)]["R_moore"] for c in SEG64]), str(mutex)))
    # D-K2 继承律 21 档（源档重算+R35 在档双读）
    r35p2 = json.load(open(R35P2, encoding="utf-8"))
    src_R = {}; src_bad = 0
    for c in SRCS:
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        arch = int(r35p2["DJ0"]["gear48"][str(c)]["R_moore"])
        if Rm != arch: src_bad += 1; log.append("DK2 src mismatch @%d re=%d arch=%d" % (c, Rm, arch))
        src_R[str(c)] = {"recompute": Rm, "archive": arch}
    log.append("DK2 src21 dual-read bad=%d %s" % (src_bad, json.dumps(src_R)))
    recs, inh_bad, pure_list = inherit_check(INH21, Ds, ms)
    synth = {}; synth_ok = True
    for c in sorted(pure_list)[:3]:
        Rc = dg1[str(c)]["R_moore"]
        Rs = src_R[str(c // 3)]["recompute"]
        synth[str(c)] = {"R": Rc, "R_src_plus1": Rs + 1}
        if Rc != Rs + 1: synth_ok = False
    log.append("DK2 inherit21 bad=%d pure=%s synth=%s ok=%s" %
               (inh_bad, str(pure_list), json.dumps(synth), str(synth_ok)))
    # D-K3 段 max=20 三态
    seg_R = [dg1[str(c)]["R_moore"] for c in SEG64]
    seg_max = max(seg_R); seg_max_at = SEG64[seg_R.index(seg_max)]
    tri = "hit" if seg_max == 20 else ("fail" if seg_max > 20 else "unsupported")
    log.append("DK3 seg_max=%d@%d vs 20 -> %s" % (seg_max, seg_max_at, tri))
    # D-K5 分解律+M_int C2+极值归因
    dg5 = {}; law_bad = 0; c2_bad = 0
    for c in SEG64:
        lw = law_four(c, Ds, ms, R_from=dg1[str(c)]["R_moore"])
        if not lw["law_ok"]: law_bad += 1
        if lw["M_int"] != lw["C2"]: c2_bad += 1
        dg5[str(c)] = {"reach": lw["reach"], "acc": lw["acc"], "M_acc": lw["M_acc"],
                       "M_dead": lw["M_dead"], "M_int": lw["M_int"], "R": lw["R"],
                       "C2": lw["C2"], "law_ok": lw["law_ok"],
                       "prime": _is_prime(-c), "pure_inh": c in pure_list}
    top = sorted(SEG64, key=lambda c: (-dg1[str(c)]["R_moore"], c))[:5]
    log.append("DK5 law_bad=%d c2_bad=%d top5=%s" %
               (law_bad, c2_bad, json.dumps({str(c): dg5[str(c)] for c in top})))
    res = {"meta": {"script": "d5_band_fixN-v1.0-20260925.py", "frozen": FROZEN, "part": "part1"},
           "DK0": {"anchor_bad": anchor_bad, "dual": dual, "head4_bad": head4_bad},
           "DK1": {"gear64": dg1, "dfa_bad": dfa_bad, "mutex": mutex},
           "DK2": {"src_R": src_R, "src_bad": src_bad, "records": recs, "bad": inh_bad,
                    "pure_list": pure_list, "synth": synth, "synth_ok": synth_ok},
           "DK3": {"seg_max": int(seg_max), "seg_max_at": int(seg_max_at), "tri": tri},
           "DK5": {"records": dg5, "law_bad": law_bad, "c2_bad": c2_bad,
                    "top5": {str(c): dg5[str(c)] for c in top}},
           "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return Ds, ms

def _is_prime(n):
    if n < 2: return False
    i = 2
    while i * i <= n:
        if n % i == 0: return False
        i += 1
    return True

# ---------- band（D-K4 快扫） ----------
def run_band(cstart, cend):
    """c 从 cstart 到 cend 递减（负档）"""
    log = []
    ys, Ds, ts, ms = dp_full(12)
    del ys, ts
    aD = -Ds
    hist_all = np.bincount(aD, minlength=177148)
    gear = {}
    for c in range(cstart, cend - 1, -1):
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        gear[str(c)] = {"c": int(c), "n_words": int(hist_all[-c]), "R": Rm}
    Rs = [gear[str(c)]["R"] for c in range(cstart, cend - 1, -1)]
    mx = max(Rs); mx_at = range(cstart, cend - 1, -1)[Rs.index(mx)]
    log.append("BAND [%d..%d] n=%d max=%d@%d" % (cstart, cend, len(Rs), mx, mx_at))
    res = {"meta": {"script": "d5_band_fixN-v1.0-20260925.py", "frozen": FROZEN,
                    "part": "band", "cstart": cstart, "cend": cend},
           "gear": gear, "max": {"R": int(mx), "at": int(mx_at)}, "log": log}
    json.dump(res, open(OUT % ("band%d" % abs(cstart)), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- merge（D-K4 全带统计+增信） ----------
def run_merge():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    del ys, ts
    p1 = json.load(open(OUT % "part1", encoding="utf-8"))
    bd = json.load(open(OUT % "band307", encoding="utf-8"))
    gear = dict(p1["DK1"]["gear64"])
    for k, v in bd["gear"].items():
        gear[k] = {"c": v["c"], "n_words": v["n_words"], "R_moore": v["R"]}
    allc = sorted((int(k) for k in gear), reverse=True)
    Rs = [gear[str(c)]["R_moore"] for c in allc]
    mx = max(Rs); mx_at = allc[Rs.index(mx)]
    tri = "hit" if mx == 20 else ("fail" if mx > 20 else "unsupported")
    # 全带 max 档 Nerode+law_four；seed 抽样 5 档 Nerode
    import random
    rng = random.Random(20260925)
    samp = [mx_at] + rng.sample([c for c in allc if c != mx_at], 5)
    nerd = {}
    for c in samp:
        Nn = int(nerode_sig(c, Ds))
        nerd[str(c)] = {"nerode": Nn, "moore": gear[str(c)]["R_moore"],
                        "eq": bool(Nn == gear[str(c)]["R_moore"])}
    nerd_bad = sum(0 if v["eq"] else 1 for v in nerd.values())
    lw = law_four(mx_at, Ds, ms, R_from=gear[str(mx_at)]["R_moore"])
    # d=5 带分带统计（继承/非继承）
    inh_R = [gear[str(c)]["R_moore"] for c in allc if c % 3 == 0]
    non_R = [gear[str(c)]["R_moore"] for c in allc if c % 3 != 0]
    stat = {"n": len(allc), "all": {"min": min(Rs), "max": mx,
                                    "mean": round(sum(Rs) / len(Rs), 3)},
            "inherit": {"n": len(inh_R), "max": max(inh_R), "mean": round(sum(inh_R) / len(inh_R), 3)},
            "noninherit": {"n": len(non_R), "max": max(non_R), "mean": round(sum(non_R) / len(non_R), 3)}}
    log.append("MERGE fullband n=%d max=%d@%d tri=%s" % (len(allc), mx, mx_at, tri))
    log.append("MERGE bands d5 %s" % json.dumps(stat))
    log.append("MERGE nerode %s bad=%d" % (json.dumps(nerd), nerd_bad))
    log.append("MERGE maxlaw %s" % json.dumps(lw))
    res = {"meta": {"script": "d5_band_fixN-v1.0-20260925.py", "frozen": FROZEN, "part": "merge"},
           "fullband": {"n": len(allc), "max": int(mx), "at": int(mx_at), "tri": tri},
           "band_d5_stat": stat, "nerode_check": nerd, "nerod_bad": nerd_bad,
           "max_law": lw, "log": log}
    json.dump(res, open(OUT % "merge", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- part2（㉝ 型 N 完全刻画） ----------
def run_part2(Ds=None, ms=None):
    log = []
    if Ds is None:
        ys, Ds, ts, ms = dp_full(12)
        assert (ys == np.arange(N4, dtype=np.int64)).all()
        del ys, ts
    aD = -Ds
    rv = rev_map()
    Drev = Ds[rv]
    fixm = (Ds == Drev)
    # 回文掩码（R36 口径）
    palmask = np.zeros(N4, dtype=bool)
    p6 = np.arange(4096, dtype=np.int64)
    dg6 = np.zeros((4096, 6), dtype=np.int64); yy = p6.copy()
    for i in range(6):
        dg6[:, 5 - i] = yy % 4; yy //= 4
    pal = (dg6 * (4 ** np.arange(5, -1, -1))).sum(axis=1) * 4096 + \
          (dg6[:, ::-1] * (4 ** np.arange(5, -1, -1))).sum(axis=1)
    palmask[pal] = True
    # D-N0 回归锚
    r36 = json.load(open(R36P1, encoding="utf-8"))
    n_fix = int(fixm.sum())
    nfix0 = int((fixm & (aD == 0)).sum())
    typeN = n_fix - nfix0
    typeN_pal = int((fixm & palmask & (aD != 0)).sum())
    typeN_nonpal = int((fixm & ~palmask & (aD != 0)).sum())
    anchor_bad = 0
    for name, got, exp in [("n_fix", n_fix, r36["DF0"]["n_fix"]),
                           ("typeZ", nfix0, r36["DF0"]["nfix0"]),
                           ("typeN", typeN, r36["DF3"]["typeN"]),
                           ("typeN_pal", typeN_pal, r36["DF3"]["typeN_pal"]),
                           ("typeN_nonpal", typeN_nonpal, r36["DF3"]["typeN_nonpal"])]:
        if got != exp: anchor_bad += 1; log.append("DN0 MISMATCH %s got=%d exp=%d" % (name, got, exp))
    log.append("DN0 anchor_bad=%d (n_fix=%d typeZ=%d typeN=%d pal=%d nonpal=%d)" %
               (anchor_bad, n_fix, nfix0, typeN, typeN_pal, typeN_nonpal))
    # D-N1 回文保持定理
    pal_idx = np.nonzero(palmask)[0]
    pal_all_fix = bool(fixm[pal_idx].all())
    palE0 = np.sort(np.nonzero(palmask & (aD == 0))[0])
    # Pal∩E0 == Pal∩{0,3}*（前 6 位∈{0,3} 的回文=2^6·hi*4096+rev6(hi)）
    arr6 = np.array([0], dtype=np.int64)
    for _ in range(6):
        arr6 = np.concatenate([arr6 * 4, arr6 * 4 + 3])
    d6 = np.zeros((arr6.size, 6), dtype=np.int64); y6 = arr6.copy()
    for i in range(6):
        d6[:, 5 - i] = y6 % 4; y6 //= 4
    r6 = (d6[:, ::-1] * (4 ** np.arange(5, -1, -1))).sum(axis=1)
    pal_pure3 = np.sort(arr6 * 4096 + r6)   # 回文由前 6 位决定：hi*4096+rev(hi)
    pal0_eq = (palE0.shape == pal_pure3.shape) and bool((palE0 == pal_pure3).all())
    n_pal0 = int(len(palE0))
    typeN_pal_idx = np.sort(np.nonzero(fixm & palmask & (aD != 0))[0])
    palN_eq_cnt = (len(typeN_pal_idx) == 4096 - n_pal0)
    dn1_bad = (0 if pal_all_fix else 1) + (0 if (pal0_eq and n_pal0 == 64) else 1) + \
              (0 if palN_eq_cnt else 1)
    log.append("DN1 pal_all_fix=%s n_pal0=%d pal0_eq=%s typeN_pal=%d pred=%d bad=%d" %
               (pal_all_fix, n_pal0, pal0_eq, len(typeN_pal_idx), 4096 - n_pal0, dn1_bad))
    # D-N2 对合配对（判据语境=型 N 非回文·aD!=0；附带全非回文 Fix 轨道数判定输出）
    np_idx = np.nonzero(fixm & ~palmask & (aD != 0))[0]
    closed = bool(fixm[rv[np_idx]].all() and (~palmask[rv[np_idx]]).all())
    nofix = bool((rv[np_idx] != np_idx).all())
    orbits = int((np_idx < rv[np_idx]).sum())
    np_all = np.nonzero(fixm & ~palmask)[0]
    orbits_all = int((np_all < rv[np_all]).sum())
    dn2_bad = (0 if closed else 1) + (0 if nofix else 1) + (0 if orbits == 18586 else 1)
    log.append("DN2 closed=%s nofix=%s orbits=%d (pred 18586) bad=%d orbits_allN=%d" %
               (closed, nofix, orbits, dn2_bad, orbits_all))
    # D-N3 继承切片闭式（102 档）
    dsub = Ds[:N11]; drevsub = Drev[:N11]
    tail0mask = (np.arange(N4) % 4 == 0)
    slice_rec = {}; dn3_bad = 0
    a_s_counts = {}
    for c in SLICE102:
        s = c // 3
        As = np.nonzero((dsub == s) & (drevsub == 9 * s))[0]
        fourA = np.sort(4 * As)
        fixc_tail0 = np.sort(np.nonzero(fixm & (Ds == c) & tail0mask)[0])
        eq = (fourA.shape == fixc_tail0.shape) and bool((fourA == fixc_tail0).all())
        contain = bool((dsub[As] == s).all()) if len(As) else True
        if not (eq and contain): dn3_bad += 1
        a_s_counts[str(c)] = int(len(As))
        slice_rec[str(c)] = {"s": int(s), "n_A": int(len(As)), "n_fix_tail0": int(len(fixc_tail0)),
                             "eq": eq, "contain": contain}
    log.append("DN3 slice102 bad=%d nonzeroA=%d/%d Acounts_head=%s" %
               (dn3_bad, sum(1 for v in a_s_counts.values() if v > 0), len(SLICE102),
                json.dumps(dict(list(a_s_counts.items())[:12]))))
    # D-N4 逐档谱+四分量（|c|<=306 主域）
    tail = (np.arange(N4) % 4).astype(np.int8)
    fixidx = np.nonzero(fixm)[0]
    spec = {}
    fixcnt = np.bincount(aD[fixidx], minlength=307)
    hist_all = np.bincount(aD, minlength=307)
    for t in range(4):
        m_t = fixm & (tail == t)
        spec["tail%d" % t] = np.bincount(aD[np.nonzero(m_t)[0]], minlength=307)
    palcnt = np.bincount(aD[np.nonzero(fixm & palmask)[0]], minlength=307)
    # 继承切片计数（3|c）
    slice_cnt = np.zeros(307, dtype=np.int64)
    for c in SLICE102:
        slice_cnt[-c] = a_s_counts[str(c)]
    inh_c = [c for c in range(0, 307) if c % 3 == 0]
    non_c = [c for c in range(0, 307) if c % 3 != 0]
    frate_inh = round(float(fixcnt[inh_c].sum()) / float(hist_all[inh_c].sum()), 6)
    frate_non = round(float(fixcnt[non_c].sum()) / float(hist_all[non_c].sum()), 6)
    candC = bool(frate_non > frate_inh)
    # 分带统计（Fix 率按 d）
    band_stat = {}
    for c in range(1, 307):
        d = 0; m = c
        while m >= 3: m //= 3; d += 1
        band_stat.setdefault(d, [0, 0, 0])
        band_stat[d][0] += int(fixcnt[c]); band_stat[d][1] += int(hist_all[c]); band_stat[d][2] += 1
    band_out = {str(d): {"fix": v[0], "words": v[1], "n_c": v[2],
                         "rate": round(v[0] / max(v[1], 1), 8)} for d, v in sorted(band_stat.items())}
    log.append("DN4 frate_inh=%.6f frate_non=%.6f candC(non>inh)=%s" % (frate_inh, frate_non, candC))
    log.append("DN4 bands %s" % json.dumps(band_out))
    res = {"meta": {"script": "d5_band_fixN-v1.0-20260925.py", "frozen": FROZEN, "part": "part2"},
           "DN0": {"anchor_bad": anchor_bad, "n_fix": n_fix, "typeZ": nfix0, "typeN": typeN,
                    "typeN_pal": typeN_pal, "typeN_nonpal": typeN_nonpal},
           "DN1": {"pal_all_fix": pal_all_fix, "n_pal0": n_pal0, "pal0_eq": pal0_eq,
                    "typeN_pal": int(len(typeN_pal_idx)), "bad": dn1_bad},
           "DN2": {"closed": closed, "no_fixpoint": nofix, "orbits": orbits, "bad": dn2_bad,
                    "orbits_all_nonpal_fix": orbits_all},
           "DN3": {"records": slice_rec, "bad": dn3_bad, "A_counts": a_s_counts},
           "DN4": {"fixcnt_0_306": [int(x) for x in fixcnt],
                    "hist_0_306": [int(x) for x in hist_all],
                    "tail_split": {("tail%d" % t): [int(x) for x in spec["tail%d" % t]] for t in range(4)},
                    "palcnt_0_306": [int(x) for x in palcnt],
                    "slice_cnt_0_306": [int(x) for x in slice_cnt],
                    "frate_inherit": frate_inh, "frate_noninherit": frate_non,
                    "candC_non_gt_inh": candC, "band_stat": band_out},
           "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return Ds, ms

if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part == "all":
        Ds1, ms1 = run_part1(None, None)
        run_part2(Ds1, ms1)
    elif part == "part1":
        run_part1(None, None)
    elif part == "part2":
        run_part2(None, None)
    elif part == "band":
        run_band(int(sys.argv[2]), int(sys.argv[3]))
    elif part == "merge":
        run_merge()
