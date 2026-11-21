# -*- coding: utf-8 -*-
# d=11 带深域外验证 + E_c 一般档 Fix 保持集谱定理化（G-1..G-4）（R43）
# 判据书：代数册·d11带验证与Ec一般档Fix保持集谱预注册判据书-v1.0-20260925.md（冻结 2026-09-25T10:23:07）
# 用法: python d11_band_gfix-v1.0-20260925.py all | part1 | part2 | bands | band CS CE | merge
# part1: D-B0 锚 / D-B1 64档器 / D-B2 继承22档 / D-B3 段max=38 三态 / D-B5 分解律+C2+归因
# bands: D-B4 全部 702 段分段快扫（单进程共享 dp·逐段 JSON 落盘）
# band : D-B4 单段快扫 c=CS..CE
# merge: D-B4 全带统计（max 对表 38 三态+两抬升链七次验证+实质素数律+词数极值链第八点+相邻结构+直方图+分带统计+抽样3档枚举增信）
# part2: D-T3 定理 G-1 回文核 / G-2 μ分层对称迁移 / G-3 σ∘rev交换+σ(Pal)=Pal / G-4 Fix轨道分解 / 判定输出谱
import json
import sys
import numpy as np

OUT = "H:/理论存档/01-数学/02-实验与数据/results/d11_band_gfix-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T10:23:07"
N4 = 4 ** 12
N11 = 4 ** 11
G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]
FAC = [1, -1, -1, 1]
R42P1 = "H:/理论存档/01-数学/02-实验与数据/results/d10_fix_track-part1-v1.0-20260925.json"
R42MG = "H:/理论存档/01-数学/02-实验与数据/results/d10_fix_track-merge-v1.0-20260925.json"
SEG64 = list(range(-177147, -177211, -1))      # 本轮段 64 档
INH22 = [c for c in SEG64 if c % 3 == 0]       # 继承 22 档（3|c 全集）
SRCS = sorted(set(c // 3 for c in INH22), reverse=True)   # 源档 -59049..-59070（R42 在档段）
PURE_CAND = [c for c in INH22 if (c // 3) % 2 == 1]       # 纯继承候选 11 档 -3(2j+59049) 型
# 快扫 702 段：段长 505·末段 225（i=0..700: cs=-177211-505i, ce=cs-504；i=701: cs=-531216, ce=-531440）
BAND_CHUNKS = [(-177211 - 505 * i, -177211 - 505 * i - 504) for i in range(701)] + [(-531216, -531440)]
PRED_MAX = 38                                  # 3*11+5

# ---------- 全域 DP（值索引口径·R34-R42 修正口径复用） ----------
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

def dp_layers(Lmax=12):
    """逐层 DP：返回 [(L, Ds_L, ms_L)]（值索引·每层独立落位）"""
    Gtab = np.array(G, dtype=np.int64)
    fac = np.array(FAC, dtype=np.int64)
    ys = np.arange(1, dtype=np.int64)
    Ds = np.zeros(1, dtype=np.int64); ts = np.ones(1, dtype=np.int64); ms = np.zeros(1, dtype=np.int64)
    layers = []
    for lay in range(1, Lmax + 1):
        parts_D, parts_y, parts_t, parts_m = [], [], [], []
        for r in range(4):
            parts_D.append(Ds * 3 + ts * Gtab[r][ms])
            parts_y.append(ys * 4 + r)
            parts_t.append(ts * fac[r]); parts_m.append((ms + r) % 3)
        ys = np.concatenate(parts_y); Ds = np.concatenate(parts_D)
        ts = np.concatenate(parts_t); ms = np.concatenate(parts_m)
        perm = np.argsort(ys, kind="stable")
        layers.append((lay, Ds[perm], ms[perm]))
    return layers

def rev_map():
    y = np.arange(N4, dtype=np.int64); rv = np.zeros(N4, dtype=np.int64)
    for _ in range(12):
        rv = rv * 4 + (y & 3); y >>= 2
    return rv

def rev_map_L(L):
    """L 位反转对合（每层独立·R42 微测拦截教训：12 位映射不可用于 L<12 层）"""
    y = np.arange(4 ** L, dtype=np.int64); r = np.zeros(4 ** L, dtype=np.int64)
    for _ in range(L):
        r = r * 4 + (y & 3); y >>= 2
    return r

def sigma_map_L(L):
    """L 位 σ 镜像 ρ→3−ρ（每层独立）"""
    y = np.arange(4 ** L, dtype=np.int64); s = np.zeros(4 ** L, dtype=np.int64)
    for _ in range(L):
        s = s * 4 + (3 - (y & 3)); y >>= 2
    return s

def z03_masks(nmax=12):
    """masks[n] = bool 数组（长 4^n）：n 位词逐位∈{0,3}；masks[0]=[True]（空词值 0）"""
    masks = [np.ones(1, dtype=bool)]
    for n in range(1, nmax + 1):
        v = np.arange(4 ** n, dtype=np.int64)
        m = masks[n - 1][v >> 2] & np.isin(v & 3, (0, 3))
        masks.append(m)
    return masks

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

def moore_min_vec(tr, accept_set):
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

def dfa_word_count(tr, q0, accept, L=12):
    n = tr.shape[0]; DEAD = n; N = n + 1
    TR = np.full((N, 4), DEAD, dtype=np.int64)
    TR[:n] = np.where(tr >= 0, tr, DEAD); TR[DEAD, :] = DEAD
    cnt = np.zeros(N, dtype=np.int64); cnt[q0] = 1
    for _ in range(L):
        new = np.zeros(N, dtype=np.int64)
        for s in range(N):
            c0 = int(cnt[s])
            if c0:
                for r in range(4):
                    new[int(TR[s, r])] += c0
        cnt = new
    return int(sum(int(cnt[a]) for a in accept))

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
    n = 0; L = 1
    while 3 ** L <= abs(c):
        if c % (3 ** L) == 0 and abs(c) // (3 ** L) >= 2:
            n += 1
        L += 1
    return n

def law_four(c, R_from=None):
    keep_states, tr, q0, acc = build_dfa(c)
    reach = len(keep_states); accn = len(acc)
    m_acc = accn - 1
    m_dead = active_dead(keep_states, tr, acc)
    Rm = int(moore_min_vec(tr, acc)) if R_from is None else int(R_from)
    m_int = reach + 1 - m_acc - m_dead - Rm
    return {"reach": reach, "acc": accn, "M_acc": m_acc, "M_dead": m_dead,
            "M_int": int(m_int), "R": int(Rm), "C2": mint_layers(c),
            "law_ok": bool(m_int >= 0 and Rm == reach + 1 - m_acc - m_dead - m_int)}

def inherit_check(cs, Ds, ms):
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

# ---------- part1（㊽ d=11 带验证） ----------
def run_part1():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    assert (ys == np.arange(N4, dtype=np.int64)).all()
    del ys, ts
    aD = -Ds
    hist_all = np.bincount(aD)
    # D-B0 回归锚（R42 在档只读）
    r42p1 = json.load(open(R42P1, encoding="utf-8"))
    r42mg = json.load(open(R42MG, encoding="utf-8"))
    anchor_bad = 0
    for c in (-59049, -59050, -59051, -59052):
        arch = r42p1["DB1"]["gear64"][str(c)]
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        if Rm != arch["R_moore"] or int(hist_all[-c]) != arch["n_words"]:
            anchor_bad += 1; log.append("DB0 mismatch @%d re=%d arch=%s" % (c, Rm, json.dumps(arch)))
    fb = r42mg["fullband"]
    if not (fb["n"] == 118098 and fb["max"] == 35 and fb["at"] == -118099 and fb["tri"] == "hit"):
        anchor_bad += 1; log.append("DB0 merge fullband mismatch %s" % json.dumps(fb))
    wm = r42mg["wordmax"]
    if not (wm["v"] == 4096 and wm["at"] == -118098):
        anchor_bad += 1; log.append("DB0 wordmax mismatch %s" % json.dumps(wm))
    log.append("DB0 anchor_bad=%d (fullband=%s wordmax=%s)" % (anchor_bad, json.dumps(fb), json.dumps(wm)))
    # D-B1 64 档器产出（实现层口径修正·如实披露：全域 4^12 词 D 值上界=177147=3^11（bincount 直读）
    # ⟹ d=11 带内 |c|>177147 档全为空档（词数 0·语言空·Moore 态数无定义记 None 跳过 DFA）
    import time
    def hist_get(c):
        return int(hist_all[-c]) if -c < hist_all.shape[0] else 0
    t0 = time.time()
    dm1 = {}
    for c in SEG64:
        nw = hist_get(c)
        if nw > 0:
            ks, tr, q0, acc = build_dfa(c)
            Rm = int(moore_min_vec(tr, acc))
        else:
            Rm = None          # 空档·语言空·最小 DFA=单死态·R 无意义
        dm1[str(c)] = {"c": int(c), "n_words": nw, "R_moore": Rm}
    seg_dt = time.time() - t0
    mutex = len(set(dm1[k]["c"] for k in dm1)) == 64
    nonempty = [c for c in SEG64 if dm1[str(c)]["n_words"] > 0]
    seg_R = [dm1[str(c)]["R_moore"] for c in nonempty]
    seg_max = max(seg_R) if seg_R else 0
    seg_max_at = nonempty[seg_R.index(seg_max)] if seg_R else 0
    seg_reach = {}
    for c in nonempty:
        ks, tr, q0, acc = build_dfa(c)
        seg_reach[str(c)] = len(ks)
    import random
    rng = random.Random(20260925)
    samp = [seg_max_at] + rng.sample([c for c in nonempty if c != seg_max_at], min(2, len(nonempty) - 1)) if len(nonempty) >= 2 else list(nonempty)
    enum3 = {}
    for c in samp:
        ks, tr, q0, acc = build_dfa(c)
        wc = dfa_word_count(tr, q0, acc, 12)
        enum3[str(c)] = {"dfa_paths": wc, "n_words": dm1[str(c)]["n_words"],
                         "eq": bool(wc == dm1[str(c)]["n_words"])}
    enum_bad = sum(0 if v["eq"] else 1 for v in enum3.values())
    log.append("DB1 gear64 nonempty_n=%d nonempty=%s seg_R=%s mutex=%s seg_max=%d@%d seg_dt=%.1fs enum3 bad=%d %s" %
               (len(nonempty), str(nonempty), str(seg_R), str(mutex), seg_max, seg_max_at, seg_dt, enum_bad, json.dumps(enum3)))
    # D-B2 继承律 22 档（源档重算+R42 在档双读）
    src_bad = 0
    src_re = {}
    for c in SRCS:
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        arch = int(r42p1["DB1"]["gear64"][str(c)]["R_moore"])
        if Rm != arch: src_bad += 1; log.append("DB2 src mismatch @%d re=%d arch=%d" % (c, Rm, arch))
        src_re[str(c)] = {"recompute": Rm, "archive": arch}
    recs, inh_bad, pure_list_raw = inherit_check(INH22, Ds, ms)
    # 实现层口径细化（如实披露）：空档（|c|>3^11·语言空）在 W11 词集级恒等中自动满足（空==空）
    # 且 X_c=∅ 被标 pure——纯继承判定取非空档口径（纯继承=无新词且档非空·空档超域单列）
    pure_list_ne = [c for c in pure_list_raw if dm1[str(c)]["n_words"] > 0]
    empty_inh = [c for c in pure_list_raw if dm1[str(c)]["n_words"] == 0]
    synth = {}; synth_ok = True
    for c in sorted(pure_list_ne)[:3]:
        Rc = dm1[str(c)]["R_moore"]
        Rs_ = src_re[str(c // 3)]["recompute"]
        synth[str(c)] = {"R": Rc, "R_src_plus1": Rs_ + 1}
        if Rc != Rs_ + 1: synth_ok = False
    pure_match = sorted(pure_list_ne) == sorted(PURE_CAND)
    log.append("DB2 inherit22 bad=%d pure_nonempty=%s empty_pure_n=%d pure_match_cand=%s synth=%s ok=%s" %
               (inh_bad, str(pure_list_ne), len(empty_inh), str(pure_match), json.dumps(synth), str(synth_ok)))
    # D-B3 段 max=38 三态
    tri = "hit" if seg_max == PRED_MAX else ("fail" if seg_max > PRED_MAX else "unsupported")
    log.append("DB3 seg_max=%d@%d vs %d -> %s" % (seg_max, seg_max_at, PRED_MAX, tri))
    # D-B5 分解律+M_int C2+极值归因（实现层口径修正：分解律/C2 仅对非空档·空档语言空无意义·如实落盘）
    dm5 = {}; law_bad = 0; c2_bad = 0
    for c in nonempty:
        lw = law_four(c, R_from=dm1[str(c)]["R_moore"])
        if not lw["law_ok"]: law_bad += 1
        if lw["M_int"] != lw["C2"]: c2_bad += 1
        dm5[str(c)] = {"reach": lw["reach"], "acc": lw["acc"], "M_acc": lw["M_acc"],
                       "M_dead": lw["M_dead"], "M_int": lw["M_int"], "R": lw["R"],
                       "C2": lw["C2"], "law_ok": lw["law_ok"], "pure_inh": c in pure_list_ne}
    reach_max_seg = max(seg_reach.values()) if seg_reach else 0
    seg_reach_at = [c for c in nonempty if seg_reach.get(str(c)) == reach_max_seg]
    top = sorted(nonempty, key=lambda c: (-dm1[str(c)]["R_moore"], c))[:5]
    log.append("DB5 law_bad=%d c2_bad=%d reach_max_seg=%d@%s top5=%s" %
               (law_bad, c2_bad, reach_max_seg, str(seg_reach_at),
                json.dumps({str(c): dm5[str(c)] for c in top})))
    res = {"meta": {"script": "d11_band_gfix-v1.0-20260925.py", "frozen": FROZEN, "part": "part1"},
           "DB0": {"anchor_bad": anchor_bad, "fullband": fb, "wordmax": wm},
           "DB1": {"gear64": dm1, "seg_max": int(seg_max), "seg_max_at": int(seg_max_at),
                    "mutex": mutex, "enum3": enum3, "enum_bad": enum_bad,
                    "seg_reach": seg_reach, "seg_dt_sec": round(seg_dt, 1)},
           "DB2": {"src_R": src_re, "src_bad": src_bad, "records": recs, "bad": inh_bad,
                    "pure_list_raw": pure_list_raw, "pure_list_nonempty": pure_list_ne,
                    "empty_pure_n": len(empty_inh), "pure_cand": PURE_CAND, "pure_match": pure_match,
                    "synth": synth, "synth_ok": synth_ok},
           "DB3": {"seg_max": int(seg_max), "seg_max_at": int(seg_max_at), "tri": tri},
           "DB5": {"records": dm5, "law_bad": law_bad, "c2_bad": c2_bad,
                    "reach_max_seg": int(reach_max_seg), "reach_max_at": seg_reach_at,
                    "top5": {str(c): dm5[str(c)] for c in top}},
           "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- band 快扫（共享 dp 口径·逐段 JSON 落盘） ----------
def _scan_chunk(cstart, cend, hist_all):
    log = []
    gear = {}
    for c in range(cstart, cend - 1, -1):
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        gear[str(c)] = {"c": int(c), "n_words": int(hist_all[-c]), "R": Rm, "reach": len(ks)}
    Rs = [gear[str(c)]["R"] for c in range(cstart, cend - 1, -1)]
    mx = max(Rs); mx_at = range(cstart, cend - 1, -1)[Rs.index(mx)]
    log.append("BAND [%d..%d] n=%d max=%d@%d" % (cstart, cend, len(Rs), mx, mx_at))
    res = {"meta": {"script": "d11_band_gfix-v1.0-20260925.py", "frozen": FROZEN,
                    "part": "band", "cstart": cstart, "cend": cend},
           "gear": gear, "max": {"R": int(mx), "at": int(mx_at)}, "log": log}
    json.dump(res, open(OUT % ("band%d" % abs(cstart)), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n".join(log))

def run_band(cstart, cend):
    ys, Ds, ts, ms = dp_full(12)
    del ys, ts, ms
    aD = -Ds
    del Ds
    hist_all = np.bincount(aD)
    _scan_chunk(cstart, cend, hist_all)

def run_bands():
    """D-B4 快扫·空域机器证明版（实现层口径修正如实披露）：全域 D 值上界 3^11 ⟹
    d=11 带内 |c|>177147 全空档·逐段机器断言段内全档词数 0·逐段 JSON 落盘（702 段）"""
    import time
    ys, Ds, ts, ms = dp_full(12)
    del ys, ts, ms
    aD = -Ds
    del Ds
    hist_all = np.bincount(aD)
    del aD
    maxaD = int(hist_all.shape[0] - 1)
    t0 = time.time()
    for i, (cs, ce) in enumerate(BAND_CHUNKS):
        log = []
        empty_ok = True
        for c in range(cs, ce - 1, -1):
            if -c < hist_all.shape[0] and int(hist_all[-c]) > 0:
                empty_ok = False
        Rs = []
        mx = 0; mx_at = 0
        log.append("BAND [%d..%d] n=%d empty_ok=%s max=%d@%d" % (cs, ce, cs - ce + 1, str(empty_ok), mx, mx_at))
        res = {"meta": {"script": "d11_band_gfix-v1.0-20260925.py", "frozen": FROZEN,
                        "part": "band", "cstart": cs, "cend": ce, "mode": "emptydomain-proof"},
               "gear": {}, "empty_ok": empty_ok, "max": {"R": mx, "at": mx_at}, "log": log}
        json.dump(res, open(OUT % ("band%d" % abs(cs)), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("\n".join(log))
        print("CHUNK %d/%d done elapsed=%.1fs" % (i + 1, len(BAND_CHUNKS), time.time() - t0), flush=True)
    print("MAXAD=%d (3^11=%d) cap_ok=%s" % (maxaD, 3 ** 11, maxaD == 3 ** 11), flush=True)

# ---------- merge（D-B4 全带统计·空域版+两抬升链七次验证+封顶律核验） ----------
def run_merge():
    log = []
    p1 = json.load(open(OUT % "part1", encoding="utf-8"))
    gear = dict(p1["DB1"]["gear64"])
    for cs, ce in BAND_CHUNKS:
        bd = json.load(open(OUT % ("band%d" % abs(cs)), encoding="utf-8"))
        assert bd["empty_ok"], "band %d not empty" % cs
    ys, Ds, ts, ms = dp_full(12)
    del ys, ts
    aD = -Ds
    del Ds, ms
    hist_all = np.bincount(aD)
    maxaD = int(hist_all.shape[0] - 1)
    del aD
    # 全带档集（−177147..−531440）词数直读·非空档=gear 内 R 非空档
    allc = list(range(-177147, -531441, -1))
    nw_all = [(int(hist_all[-c]) if -c < hist_all.shape[0] else 0) for c in allc]
    nonempty = [c for c, n in zip(allc, nw_all) if n > 0]
    gear_ne = {k: v for k, v in gear.items() if v["n_words"] > 0}
    assert sorted(int(k) for k in gear_ne) == sorted(nonempty), "nonempty mismatch part1 vs hist"
    Rs = [gear[str(c)]["R_moore"] for c in nonempty]
    mx = max(Rs); mx_at = nonempty[Rs.index(mx)]
    tri = "hit" if mx == PRED_MAX else ("fail" if mx > PRED_MAX else "unsupported")
    Rdist = {}
    for r in Rs: Rdist[str(r)] = Rdist.get(str(r), 0) + 1
    nw = [(gear[str(c)]["n_words"], c) for c in nonempty]
    wmax, wmax_at = max(nw)
    # 两抬升链七次验证+max 档归因（链核验在唯一非空档上·如实对表）
    lw = law_four(mx_at, R_from=gear[str(mx_at)]["R_moore"])
    lw["div3"] = bool((-mx_at) % 3 == 0)
    reach_all = [(lw["reach"], mx_at)]
    lw["reach_is_band_max"] = True
    lw["reach_band_max_at"] = int(mx_at)
    # 相邻结构第六度候选：R 极值档与词数极值档（全带仅一非空档·相邻=自身差 0·如实证）
    adjacent = bool(abs(mx_at - wmax_at) == 1)
    # 继承压制（全带唯一非空档 vs 继承属性）
    inh_R = [gear[str(c)]["R_moore"] for c in nonempty if c % 3 == 0]
    non_R = [gear[str(c)]["R_moore"] for c in nonempty if c % 3 != 0]
    stat = {"n_total": len(allc), "n_nonempty": len(nonempty), "n_empty": len(allc) - len(nonempty),
            "nonempty_c": nonempty,
            "all": {"min": min(Rs), "max": mx, "mean": round(sum(Rs) / len(Rs), 3)},
            "inherit": {"n": len(inh_R), "max": max(inh_R) if inh_R else None,
                        "mean": round(sum(inh_R) / len(inh_R), 3) if inh_R else None},
            "noninherit": {"n": len(non_R), "max": max(non_R) if non_R else None,
                           "mean": round(sum(non_R) / len(non_R), 3) if non_R else None}}
    # 抽样枚举增信（唯一非空档+max 档）
    enum4 = {}
    for c in sorted(set([mx_at] + nonempty[:1])):
        ks, tr, q0, acc = build_dfa(c)
        wc = dfa_word_count(tr, q0, acc, 12)
        enum4[str(c)] = {"dfa_paths": wc, "n_words": gear[str(c)]["n_words"],
                         "eq": bool(wc == gear[str(c)]["n_words"])}
    enum_bad = sum(0 if v["eq"] else 1 for v in enum4.values())
    # 词数极值链第八点：档位链 −2·3^11=−354294·值链 2^6·32=2048（差分 −64 延拓·首猜）
    chain = {"at_pred": -2 * (3 ** 11), "at_actual": int(wmax_at),
             "at_hit": bool(wmax_at == -2 * 3 ** 11),
             "v_pred": 2 ** 6 * 32, "v_actual": int(wmax), "v_hit": bool(wmax == 2 ** 6 * 32),
             "record_8128": bool(wmax > 8128), "prev_d10_4096": bool(wmax > 4096),
             "note": "d=11 带空域结构下链第八点按冻结字面对表·唯一非空档如实落盘"}
    # 封顶律核验（判据外补充探查·如实声明）：L 位词全域 |D|max == 3^(L−1) 候选 L=1..12
    cap = {}
    Gtab = np.array(G, dtype=np.int64); fac = np.array(FAC, dtype=np.int64)
    ys = np.arange(1, dtype=np.int64)
    Ds_l = np.zeros(1, dtype=np.int64); ts_l = np.ones(1, dtype=np.int64); ms_l = np.zeros(1, dtype=np.int64)
    for lay in range(1, 13):
        parts_D, parts_y, parts_t, parts_m = [], [], [], []
        for r in range(4):
            parts_D.append(Ds_l * 3 + ts_l * Gtab[r][ms_l])
            parts_y.append(ys * 4 + r)
            parts_t.append(ts_l * fac[r]); parts_m.append((ms_l + r) % 3)
        ys = np.concatenate(parts_y); Ds_l = np.concatenate(parts_D)
        ts_l = np.concatenate(parts_t); ms_l = np.concatenate(parts_m)
        mn = int(Ds_l.min()); mxv = int(Ds_l.max())
        cap[str(lay)] = {"min_D": mn, "max_D": mxv, "abs_max": max(-mn, mxv),
                         "cap_3pow_Lm1": 3 ** (lay - 1),
                         "hit": bool(max(-mn, mxv) == 3 ** (lay - 1) and mxv <= 0)}
    cap_all = bool(all(v["hit"] for v in cap.values()))
    log.append("MERGE fullband n=%d nonempty=%d empty=%d max=%d@%d tri=%s maxaD=%d(3^11)" %
               (len(allc), len(nonempty), len(allc) - len(nonempty), mx, mx_at, tri, maxaD))
    log.append("MERGE wordmax=%d@%d chain8=%s adjacent=%s" % (wmax, wmax_at, json.dumps(chain), str(adjacent)))
    log.append("MERGE Rdist=%s" % json.dumps(Rdist))
    log.append("MERGE bands d11 %s" % json.dumps(stat))
    log.append("MERGE maxlaw %s" % json.dumps(lw))
    log.append("MERGE enum4 bad=%d %s" % (enum_bad, json.dumps(enum4)))
    log.append("MERGE cap=%s cap_all=%s" % (json.dumps(cap), str(cap_all)))
    res = {"meta": {"script": "d11_band_gfix-v1.0-20260925.py", "frozen": FROZEN, "part": "merge"},
           "fullband": {"n": len(allc), "n_nonempty": len(nonempty), "n_empty": len(allc) - len(nonempty),
                        "nonempty_c": nonempty, "max": int(mx), "at": int(mx_at), "tri": tri,
                        "maxaD": maxaD, "cap_3pow11": bool(maxaD == 3 ** 11)},
           "wordmax": {"v": int(wmax), "at": int(wmax_at), "chain8": chain, "adjacent": adjacent},
           "Rdist": Rdist, "band_d11_stat": stat, "max_law": lw,
           "enum4": enum4, "enum_bad": enum_bad,
           "cap_check": cap, "cap_all": cap_all, "log": log}
    json.dump(res, open(OUT % "merge", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- part2（㊾ E_c 一般档 Fix 保持集谱：G-1..G-4+判定输出） ----------
def run_part2():
    log = []
    layers = dp_layers(12)
    z03vals = [np.nonzero(m)[0].astype(np.int64) for m in z03_masks(12)]
    per_L = {}
    mig_small = {}          # L=1..8 μ 分层迁移非零三元组谱（判定输出落盘）
    g1_bad = 0; g2_bad = 0; g3_bad = 0; g4_bad = 0; e0_bad = 0
    for (L, Ds, ms) in layers:
        N = 4 ** L
        rv = rev_map_L(L); sv = sigma_map_L(L)
        # G-3a：σ∘rev==rev∘σ 全域逐词（向量化）
        exch_ok = bool((sv[rv] == rv[sv]).all())
        # 回文词 Pal + G-1（回文核·平凡真机器确认）
        pal_mask = (rv == np.arange(N, dtype=np.int64))
        pals = np.nonzero(pal_mask)[0].astype(np.int64)
        g1_core_ok = bool((Ds[pals] == Ds[rv[pals]]).all())
        # Fix 全域（D==D∘rev）与逐档谱
        dr = Ds[rv]
        fix_mask = (Ds == dr)
        fixw = np.nonzero(fix_mask)[0].astype(np.int64)
        nfix_by_c = np.bincount(Ds[fixw] - int(Ds.min()), minlength=int(Ds.max()) - int(Ds.min()) + 1)
        npal_by_c = np.bincount(Ds[pals] - int(Ds.min()), minlength=nfix_by_c.shape[0])
        # G-1 逐档下界 pal_c <= n_fix_c（仅在 E_c 非空档核）
        hist_c = np.bincount(Ds - int(Ds.min()), minlength=nfix_by_c.shape[0])
        nz = np.nonzero(hist_c)[0]
        g1_pal_ok = bool((npal_by_c[nz] <= nfix_by_c[nz]).all())
        # G-4：Fix 轨道分解 n_fix==pal+2*pair·pair>=0（逐档全域核）
        pair_by_c = (nfix_by_c[nz] - npal_by_c[nz])
        g4_ok = bool((pair_by_c >= 0).all() and ((pair_by_c % 2) == 0).all())
        # G-3b：σ(Pal)==Pal 词集级
        sigpal_ok = bool((np.sort(sv[pals]) == pals).all())
        if not (g1_core_ok and g1_pal_ok): g1_bad += 1
        if not g4_ok: g4_bad += 1
        if not (exch_ok and sigpal_ok): g3_bad += 1
        # E_0 回归（R42 F-1：E_0^L∩Fix=={0,3}*^L⊔{0^j·1·0^{L−1−j}} 计数 2^L+L）
        z = z03vals[L]
        unit = np.array([4 ** (L - 1 - j) for j in range(L)], dtype=np.int64)
        pred1 = np.unique(np.concatenate([z, unit]))
        fixE0 = np.sort(fixw[Ds[fixw] == 0])
        eq0 = bool(fixE0.shape == pred1.shape and (fixE0 == pred1).all())
        cnt0 = bool(len(fixE0) == 2 ** L + L)
        if not (eq0 and cnt0): e0_bad += 1
        # G-2：μ 分层对称迁移（L=1..8 全谱+L=12 全域核·向量化 searchsorted 反查）
        k3 = ms.astype(np.int64)
        dmin = int(Ds.min()); span = int(Ds.max()) - dmin + 1
        key = (Ds - dmin).astype(np.int64) * (span * 3) + (dr - dmin).astype(np.int64) * 3 + k3
        uni, cnt = np.unique(key, return_counts=True)
        # 对称核：kr=反打打包 (b,a,k)·searchsorted 查表比对
        a_arr = uni // (span * 3); rem = uni % (span * 3); b_arr = rem // 3; k_arr = rem % 3
        kr = b_arr * (span * 3) + a_arr * 3 + k_arr
        pos = np.searchsorted(uni, kr)
        pos_clipped = np.minimum(pos, uni.shape[0] - 1)
        found = (uni[pos_clipped] == kr)
        sym_ok = bool(found.all() and (cnt[pos_clipped] == cnt).all())
        # 行和核：Σ_{c',k'} 覆盖 (c,k) 行 == |E_c ∩ μ=k|（列和按 cnt 加权·首跑未加权滑误修正照记）
        pack_ck = (Ds - dmin).astype(np.int64) * 3 + k3
        row_uni, row_cnt = np.unique(pack_ck, return_counts=True)
        row_tr = np.bincount((b_arr * 3 + k_arr)[found],
                             weights=cnt[found].astype(np.float64), minlength=span * 3)
        row_ok = bool((np.rint(row_tr[row_uni]).astype(np.int64) == row_cnt).all())
        if not (sym_ok and row_ok): g2_bad += 1
        if L <= 8:
            mig = {}
            for kk, cc in zip(uni.tolist(), cnt.tolist()):
                a, r2 = divmod(int(kk), span * 3); b, k = divmod(r2, 3)
                mig["%d,%d,%d" % (a + dmin, b + dmin, k)] = int(cc)
            mig_small[str(L)] = {"n_triples": len(mig), "sym_ok": sym_ok, "row_ok": row_ok,
                                 "mig": mig}
        per_L[L] = {"exch_ok": exch_ok, "n_pal": int(len(pals)), "g1_core": g1_core_ok,
                    "g1_pal_le": g1_pal_ok, "g4_pair_int": g4_ok, "sigpal": sigpal_ok,
                    "n_fix": int(len(fixw)), "E0_eq": eq0, "E0_cnt": cnt0, "n_E0_fix": int(len(fixE0)),
                    "g2_sym_ok": sym_ok, "g2_row_ok": row_ok, "g2_triples": int(uni.shape[0])}
        log.append("DT3 L=%d exch=%s pal=%d g1=%s/%s g4=%s sigpal=%s nfix=%d E0fix=%d(exp %d)" %
                   (L, str(exch_ok), len(pals), str(g1_core_ok), str(g1_pal_ok), str(g4_ok),
                    str(sigpal_ok), len(fixw), per_L[L]["n_E0_fix"], 2 ** L + L))
    # 判定输出：L=12 全域谱（Fix 总数/pal 谱/代表档/σ 回文 D 像谱/小档闭式）
    (L12, Ds12, ms12) = layers[-1]
    rv12 = rev_map_L(12); sv12 = sigma_map_L(12)
    dr12 = Ds12[rv12]
    fixw12 = np.nonzero(Ds12 == dr12)[0].astype(np.int64)
    fix_total = int(len(fixw12))
    r35_reg = bool(fix_total == 45312)     # R35 全域口径回归
    pal12 = np.nonzero(rv12 == np.arange(N4, dtype=np.int64))[0].astype(np.int64)
    pal_spec = {}
    for w in pal12.tolist():
        c = int(Ds12[w]); pal_spec[str(c)] = pal_spec.get(str(c), 0) + 1
    # σ 回文 D 像谱（记录项·σ 不保 D）
    sig_d = Ds12[sv12[pal12]]
    pal_d = Ds12[pal12]
    sigma_preserve_cnt = int((sig_d == pal_d).sum())
    # 小档闭式：E_{−1}^L（L=1..6）与 E_{−5}^2
    small = {}
    for (L, Ds, ms) in layers:
        if L > 6: break
        rv = rev_map_L(L)
        dr = Ds[rv]
        fixw = np.nonzero(Ds == dr)[0].astype(np.int64)
        em1 = np.sort(fixw[Ds[fixw] == -1])
        small["E-1_L%d" % L] = [int(x) for x in em1.tolist()]
    (L2, Ds2, ms2) = layers[1]
    rv2 = rev_map_L(2); dr2 = Ds2[rv2]
    fw2 = np.nonzero(Ds2 == dr2)[0].astype(np.int64)
    em5 = np.sort(fw2[Ds2[fw2] == -5])
    small["E-5_L2"] = [int(x) for x in em5.tolist()]
    small["E-1_L1_expect"] = [2]; small["E-1_L2_expect"] = [22]; small["E-5_L2_expect"] = []
    # 手算闭式核（冻结 M-G6）
    m_g6 = bool(small["E-1_L1"] == [2] and small["E-1_L2"] == [22] and small["E-5_L2"] == [])
    # 代表档 Fix 词集大小（全域）
    repw = fixw12[np.isin(Ds12[fixw12], (-1, -2, -118099, -177147, -354295))]
    vals, cts = np.unique(Ds12[repw], return_counts=True)
    rep = {str(int(v)): int(ct) for v, ct in zip(vals.tolist(), cts.tolist())}
    log.append("DT3out fix_total=%d r35_reg(45312)=%s sigma_pal_preserve=%d/4096 m_g6=%s rep=%s" %
               (fix_total, str(r35_reg), sigma_preserve_cnt, str(m_g6), json.dumps(rep)))
    log.append("DT3bad g1_bad=%d g2_bad=%d g3_bad=%d g4_bad=%d e0_bad=%d" %
               (g1_bad, g2_bad, g3_bad, g4_bad, e0_bad))
    res = {"meta": {"script": "d11_band_gfix-v1.0-20260925.py", "frozen": FROZEN, "part": "part2"},
           "DT3": {"per_L": per_L, "g1_bad": g1_bad, "g2_bad": g2_bad, "g3_bad": g3_bad,
                    "g4_bad": g4_bad, "e0_bad": e0_bad},
           "out": {"fix_total": fix_total, "r35_reg_45312": r35_reg,
                    "pal_spec_L12": pal_spec, "sigma_pal_preserve": sigma_preserve_cnt,
                    "small_closed": small, "m_g6_ok": m_g6, "rep_fix": rep},
           "mig_small": mig_small,
           "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part == "part1":
        run_part1()
    elif part == "part2":
        run_part2()
    elif part == "bands":
        run_bands()
    elif part == "band":
        run_band(int(sys.argv[2]), int(sys.argv[3]))
    elif part == "merge":
        run_merge()
    else:
        run_part1()
        run_bands()
        run_merge()
        run_part2()
