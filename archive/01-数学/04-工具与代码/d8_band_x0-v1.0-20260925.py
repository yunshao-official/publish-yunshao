# -*- coding: utf-8 -*-
# d=8 带深域外验证 + X_0 显式闭式定理化 + 格级镜像破缺探查（R40 主格一+主格二+候补）
# 判据书：代数册·d8带验证与X0闭式定理化预注册判据书-v1.0-20260925.md（冻结 2026-09-25 08:13:45）
# 用法: python d8_band_x0-v1.0-20260925.py all | part1 | part2 | band CS CE | merge
# part1: D-B0 锚 / D-B1 64档器 / D-B2 继承22档 / D-B3 段max=29 三态 / D-B5 分解律+C2+归因
# band : D-B4 分段快扫 c=CS..CE（Moore 向量化单通道+词数+reach）
# merge: D-B4 全带统计（max 对表 29 三态+两抬升链四次验证+实质素数律+词数极值链第五点+直方图+分带统计+抽样3档枚举增信）
# part2: D-X1 定理X-1 / D-X2 X_0 厘清+三分律自洽 / D-X3 M-Dp1 / D-MB 镜像破缺探查
import json
import sys
import numpy as np

OUT = "H:/理论存档/01-数学/02-实验与数据/results/d8_band_x0-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T08:13:45"
N4 = 4 ** 12
N11 = 4 ** 11
G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]
FAC = [1, -1, -1, 1]
R39P1 = "H:/理论存档/01-数学/02-实验与数据/results/d7_band_tm-part1-v1.0-20260925.json"
R39MG = "H:/理论存档/01-数学/02-实验与数据/results/d7_band_tm-merge-v1.0-20260925.json"
SEG64 = list(range(-6561, -6625, -1))          # 本轮段 64 档
INH22 = [c for c in SEG64 if c % 3 == 0]       # 继承 22 档（3|c 全集）
SRCS = sorted(set(c // 3 for c in INH22), reverse=True)   # 源档 -2187..-2208（R39 在档段）
PURE_CAND = [c for c in INH22 if (c // 3) % 2 == 1]       # 纯继承候选 11 档 -3(2j+2187) 型
BAND_CHUNKS = [(-6625, -7127), (-7128, -7630), (-7631, -8133), (-8134, -8636),
               (-8637, -9139), (-9140, -9642), (-9643, -10145), (-10146, -10648),
               (-10649, -11151), (-11152, -11654), (-11655, -12157), (-12158, -12660),
               (-12661, -13163), (-13164, -13666), (-13667, -14169), (-14170, -14672),
               (-14673, -15175), (-15176, -15678), (-15679, -16181), (-16182, -16684),
               (-16685, -17187), (-17188, -17690), (-17691, -18193), (-18194, -18696),
               (-18697, -19199), (-19200, -19682)]
M39 = [[3059, 0, 0, 0], [182, 1574, 0, 0], [0, 3232, 1574, 0], [5718, 0, 183, 3064]]

# ---------- 全域 DP（值索引口径·R34-R39 修正口径复用） ----------
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

def dp_prefix(rho, L=11):
    """前缀 DP Dp_rho：初态 s_rho=(G[rho][0], fac[rho], rho%3) 起 L 位递推终 D（值索引）"""
    Gtab = np.array(G, dtype=np.int64)
    fac = np.array(FAC, dtype=np.int64)
    d0, t0, m0 = G[rho][0], FAC[rho], rho % 3
    ys = np.arange(1, dtype=np.int64)
    Ds = np.array([d0], dtype=np.int64); ts = np.array([t0], dtype=np.int64); ms = np.array([m0], dtype=np.int64)
    for lay in range(L):
        parts_D, parts_y, parts_t, parts_m = [], [], [], []
        for r in range(4):
            parts_D.append(Ds * 3 + ts * Gtab[r][ms])
            parts_y.append(ys * 4 + r)
            parts_t.append(ts * fac[r]); parts_m.append((ms + r) % 3)
        ys = np.concatenate(parts_y); Ds = np.concatenate(parts_D)
        ts = np.concatenate(parts_t); ms = np.concatenate(parts_m)
    perm = np.argsort(ys, kind="stable")
    return Ds[perm]

def rev_map():
    y = np.arange(N4, dtype=np.int64); rv = np.zeros(N4, dtype=np.int64)
    for _ in range(12):
        rv = rv * 4 + (y & 3); y >>= 2
    return rv

def rev11_map():
    z = np.arange(N11, dtype=np.int64); rv = np.zeros(N11, dtype=np.int64)
    for _ in range(11):
        rv = rv * 4 + (z & 3); z >>= 2
    return rv

def digits_mask(nbits, allowed=(0, 3)):
    """nbits 位词中逐位∈allowed 的掩码（值索引）"""
    v = np.arange(4 ** nbits, dtype=np.int64)
    m = np.ones(4 ** nbits, dtype=bool)
    for _ in range(nbits):
        m &= np.isin(v & 3, allowed)
        v >>= 2
    return m

def sigma_map():
    """位镜像 sigma: rho -> 3-rho（12 位）"""
    y = np.arange(N4, dtype=np.int64); sv = np.zeros(N4, dtype=np.int64)
    for _ in range(12):
        sv = sv * 4 + (3 - (y & 3)); y >>= 2
    return sv

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

def _is_prime(n):
    if n < 2: return False
    i = 2
    while i * i <= n:
        if n % i == 0: return False
        i += 1
    return True

# ---------- part1（㊶ d=8 带验证） ----------
def run_part1():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    assert (ys == np.arange(N4, dtype=np.int64)).all()
    del ys, ts
    aD = -Ds
    hist_all = np.bincount(aD)
    # D-B0 回归锚
    r39p1 = json.load(open(R39P1, encoding="utf-8"))
    r39mg = json.load(open(R39MG, encoding="utf-8"))
    anchor_bad = 0
    for c in (-2187, -2188, -2189, -2190):
        arch = r39p1["DM1"]["gear64"][str(c)]
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        if Rm != arch["R_moore"] or int(hist_all[-c]) != arch["n_words"]:
            anchor_bad += 1; log.append("DB0 mismatch @%d re=%d arch=%s" % (c, Rm, json.dumps(arch)))
    fb = r39mg["fullband"]
    if not (fb["n"] == 4374 and fb["max"] == 26 and fb["at"] == -4375 and fb["tri"] == "hit"):
        anchor_bad += 1; log.append("DB0 merge fullband mismatch %s" % json.dumps(fb))
    wm = r39mg["wordmax"]
    if not (wm["v"] == 7680 and wm["at"] == -4374):
        anchor_bad += 1; log.append("DB0 wordmax mismatch %s" % json.dumps(wm))
    log.append("DB0 anchor_bad=%d (fullband=%s wordmax=%s)" % (anchor_bad, json.dumps(fb), json.dumps(wm)))
    # D-B1 64 档器产出
    import time
    t0 = time.time()
    dm1 = {}
    for c in SEG64:
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        dm1[str(c)] = {"c": int(c), "n_words": int(hist_all[-c]), "R_moore": Rm}
    seg_dt = time.time() - t0
    mutex = len(set(dm1[k]["c"] for k in dm1)) == 64
    seg_R = [dm1[str(c)]["R_moore"] for c in SEG64]
    seg_max = max(seg_R); seg_max_at = SEG64[seg_R.index(seg_max)]
    seg_reach = {}
    for c in SEG64:
        ks, tr, q0, acc = build_dfa(c)
        seg_reach[str(c)] = len(ks)
    import random
    rng = random.Random(20260925)
    samp = [seg_max_at] + rng.sample([c for c in SEG64 if c != seg_max_at], 2)
    enum3 = {}
    for c in samp:
        ks, tr, q0, acc = build_dfa(c)
        wc = dfa_word_count(tr, q0, acc, 12)
        enum3[str(c)] = {"dfa_paths": wc, "n_words": dm1[str(c)]["n_words"],
                         "eq": bool(wc == dm1[str(c)]["n_words"])}
    enum_bad = sum(0 if v["eq"] else 1 for v in enum3.values())
    log.append("DB1 gear64 R=%s mutex=%s seg_max=%d@%d seg_dt=%.1fs enum3 bad=%d %s" %
               (str(seg_R), str(mutex), seg_max, seg_max_at, seg_dt, enum_bad, json.dumps(enum3)))
    # D-B2 继承律 22 档（源档重算+R39 在档双读）
    src_bad = 0
    src_re = {}
    for c in SRCS:
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        arch = int(r39p1["DM1"]["gear64"][str(c)]["R_moore"])
        if Rm != arch: src_bad += 1; log.append("DB2 src mismatch @%d re=%d arch=%d" % (c, Rm, arch))
        src_re[str(c)] = {"recompute": Rm, "archive": arch}
    recs, inh_bad, pure_list = inherit_check(INH22, Ds, ms)
    synth = {}; synth_ok = True
    for c in sorted(pure_list)[:3]:
        Rc = dm1[str(c)]["R_moore"]
        Rs = src_re[str(c // 3)]["recompute"]
        synth[str(c)] = {"R": Rc, "R_src_plus1": Rs + 1}
        if Rc != Rs + 1: synth_ok = False
    pure_match = sorted(pure_list) == sorted(PURE_CAND)
    log.append("DB2 inherit22 bad=%d pure=%s pure_match_cand=%s synth=%s ok=%s" %
               (inh_bad, str(pure_list), str(pure_match), json.dumps(synth), str(synth_ok)))
    # D-B3 段 max=29 三态
    tri = "hit" if seg_max == 29 else ("fail" if seg_max > 29 else "unsupported")
    log.append("DB3 seg_max=%d@%d vs 29 -> %s" % (seg_max, seg_max_at, tri))
    # D-B5 分解律+M_int C2+极值归因
    dm5 = {}; law_bad = 0; c2_bad = 0
    for c in SEG64:
        lw = law_four(c, R_from=dm1[str(c)]["R_moore"])
        if not lw["law_ok"]: law_bad += 1
        if lw["M_int"] != lw["C2"]: c2_bad += 1
        dm5[str(c)] = {"reach": lw["reach"], "acc": lw["acc"], "M_acc": lw["M_acc"],
                       "M_dead": lw["M_dead"], "M_int": lw["M_int"], "R": lw["R"],
                       "C2": lw["C2"], "law_ok": lw["law_ok"],
                       "prime": _is_prime(-c), "pure_inh": c in pure_list}
    reach_max_seg = max(seg_reach.values())
    seg_reach_at = [c for c in SEG64 if seg_reach[str(c)] == reach_max_seg]
    top = sorted(SEG64, key=lambda c: (-dm1[str(c)]["R_moore"], c))[:5]
    log.append("DB5 law_bad=%d c2_bad=%d reach_max_seg=%d@%s top5=%s" %
               (law_bad, c2_bad, reach_max_seg, str(seg_reach_at),
                json.dumps({str(c): dm5[str(c)] for c in top})))
    res = {"meta": {"script": "d8_band_x0-v1.0-20260925.py", "frozen": FROZEN, "part": "part1"},
           "DB0": {"anchor_bad": anchor_bad, "fullband": fb, "wordmax": wm},
           "DB1": {"gear64": dm1, "seg_max": int(seg_max), "seg_max_at": int(seg_max_at),
                    "mutex": mutex, "enum3": enum3, "enum_bad": enum_bad,
                    "seg_reach": seg_reach, "seg_dt_sec": round(seg_dt, 1)},
           "DB2": {"src_R": src_re, "src_bad": src_bad, "records": recs, "bad": inh_bad,
                    "pure_list": pure_list, "pure_cand": PURE_CAND, "pure_match": pure_match,
                    "synth": synth, "synth_ok": synth_ok},
           "DB3": {"seg_max": int(seg_max), "seg_max_at": int(seg_max_at), "tri": tri},
           "DB5": {"records": dm5, "law_bad": law_bad, "c2_bad": c2_bad,
                    "reach_max_seg": int(reach_max_seg), "reach_max_at": seg_reach_at,
                    "top5": {str(c): dm5[str(c)] for c in top}},
           "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- band（D-B4 分段快扫·含 reach 字段） ----------
def run_band(cstart, cend):
    log = []
    ys, Ds, ts, ms = dp_full(12)
    del ys, ts
    aD = -Ds
    hist_all = np.bincount(aD)
    gear = {}
    for c in range(cstart, cend - 1, -1):
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        gear[str(c)] = {"c": int(c), "n_words": int(hist_all[-c]), "R": Rm, "reach": len(ks)}
    Rs = [gear[str(c)]["R"] for c in range(cstart, cend - 1, -1)]
    mx = max(Rs); mx_at = range(cstart, cend - 1, -1)[Rs.index(mx)]
    log.append("BAND [%d..%d] n=%d max=%d@%d" % (cstart, cend, len(Rs), mx, mx_at))
    res = {"meta": {"script": "d8_band_x0-v1.0-20260925.py", "frozen": FROZEN,
                    "part": "band", "cstart": cstart, "cend": cend},
           "gear": gear, "max": {"R": int(mx), "at": int(mx_at)}, "log": log}
    json.dump(res, open(OUT % ("band%d" % abs(cstart)), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- merge（D-B4 全带统计+两抬升链四次验证+增信） ----------
def run_merge():
    log = []
    p1 = json.load(open(OUT % "part1", encoding="utf-8"))
    gear = dict(p1["DB1"]["gear64"])
    for k in list(gear):
        gear[k] = {"c": gear[k]["c"], "n_words": gear[k]["n_words"],
                   "R": gear[k]["R_moore"], "reach": p1["DB1"]["seg_reach"][k]}
    for cs, ce in BAND_CHUNKS:
        bd = json.load(open(OUT % ("band%d" % abs(cs)), encoding="utf-8"))
        for k, v in bd["gear"].items():
            gear[k] = {"c": v["c"], "n_words": v["n_words"], "R": v["R"], "reach": v["reach"]}
    allc = sorted((int(k) for k in gear), reverse=True)
    Rs = [gear[str(c)]["R"] for c in allc]
    mx = max(Rs); mx_at = allc[Rs.index(mx)]
    tri = "hit" if mx == 29 else ("fail" if mx > 29 else "unsupported")
    Rdist = {}
    for r in Rs: Rdist[str(r)] = Rdist.get(str(r), 0) + 1
    nw = [(gear[str(c)]["n_words"], c) for c in allc]
    wmax, wmax_at = max(nw)
    # 两抬升链四次验证+max 档归因
    lw = law_four(mx_at, R_from=gear[str(mx_at)]["R"])
    lw["prime"] = _is_prime(-mx_at)
    lw["div3"] = bool((-mx_at) % 3 == 0)
    reach_all = [(gear[str(c)]["reach"], c) for c in allc]
    reach_max, reach_max_at = max(reach_all)
    lw["reach_is_band_max"] = bool(gear[str(mx_at)]["reach"] == reach_max)
    lw["reach_band_max_at"] = reach_max_at
    # 继承压制
    inh_R = [gear[str(c)]["R"] for c in allc if c % 3 == 0]
    non_R = [gear[str(c)]["R"] for c in allc if c % 3 != 0]
    stat = {"n": len(allc), "all": {"min": min(Rs), "max": mx, "mean": round(sum(Rs) / len(Rs), 3)},
            "inherit": {"n": len(inh_R), "max": max(inh_R), "mean": round(sum(inh_R) / len(inh_R), 3)},
            "noninherit": {"n": len(non_R), "max": max(non_R), "mean": round(sum(non_R) / len(non_R), 3)}}
    # 抽样枚举增信
    import random
    rng = random.Random(20260925)
    samp = [mx_at] + rng.sample([c for c in allc if c != mx_at], 3)
    enum4 = {}
    for c in samp:
        ks, tr, q0, acc = build_dfa(c)
        wc = dfa_word_count(tr, q0, acc, 12)
        enum4[str(c)] = {"dfa_paths": wc, "n_words": gear[str(c)]["n_words"],
                         "eq": bool(wc == gear[str(c)]["n_words"])}
    enum_bad = sum(0 if v["eq"] else 1 for v in enum4.values())
    # 词数极值链第五点：档位链 −2·3^8=−13122·值链 2^6·112=7168
    chain = {"at_pred": -2 * (3 ** 8), "at_actual": int(wmax_at),
             "at_hit": bool(wmax_at == -2 * 3 ** 8),
             "v_pred": 2 ** 6 * 112, "v_actual": int(wmax), "v_hit": bool(wmax == 2 ** 6 * 112),
             "record_8128": bool(wmax > 8128)}
    log.append("MERGE fullband n=%d max=%d@%d tri=%s" % (len(allc), mx, mx_at, tri))
    log.append("MERGE wordmax=%d@%d chain5=%s (record 8128@-162)" % (wmax, wmax_at, json.dumps(chain)))
    log.append("MERGE Rdist=%s" % json.dumps(Rdist))
    log.append("MERGE bands d8 %s" % json.dumps(stat))
    log.append("MERGE maxlaw %s" % json.dumps(lw))
    log.append("MERGE enum4 bad=%d %s" % (enum_bad, json.dumps(enum4)))
    res = {"meta": {"script": "d8_band_x0-v1.0-20260925.py", "frozen": FROZEN, "part": "merge"},
           "fullband": {"n": len(allc), "max": int(mx), "at": int(mx_at), "tri": tri},
           "wordmax": {"v": int(wmax), "at": int(wmax_at), "chain5": chain},
           "Rdist": Rdist, "band_d8_stat": stat, "max_law": lw,
           "enum4": enum4, "enum_bad": enum_bad, "log": log}
    json.dump(res, open(OUT % "merge", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- part2（㊷ X_0 定理化+候补镜像探查） ----------
def w12(v):
    s = ""
    for _ in range(12):
        s = str(v & 3) + s; v >>= 2
    return s

def run_part2():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    assert (ys == np.arange(N4, dtype=np.int64)).all()
    aD = -Ds
    # D-X1 定理 X-1：{D=0∧μ=0}=={0,3}*^L 双向（L=11 与 L=12）
    r11 = rev11_map()
    x1_bad = 0
    cond11 = np.nonzero((Ds[:N11] == 0) & (ms[:N11] == 0))[0]
    m03_11 = np.nonzero(digits_mask(11))[0]
    eq11 = (cond11.shape == m03_11.shape) and bool((cond11 == m03_11).all())
    if not eq11: x1_bad += 1
    cond12 = np.nonzero((Ds == 0) & (ms == 0))[0]
    m03_12 = np.nonzero(digits_mask(12))[0]
    eq12 = (cond12.shape == m03_12.shape) and bool((cond12 == m03_12).all())
    if not eq12: x1_bad += 1
    log.append("DX1 X-1 lemma L11 n=%d eq=%s | L12 n=%d eq=%s bad=%d" %
               (len(cond11), str(eq11), len(cond12), str(eq12), x1_bad))
    # D-X2 ① X_0^str 结构集=={12位词: 高11位∈{0,3}*∧尾∈{1,3}}·计数 4096
    z03 = m03_11
    x0s = np.sort(np.concatenate([4 * z03 + 1, 4 * z03 + 3]))
    tailv = (np.arange(N4) % 4)
    hi03 = digits_mask(11)  # 高 11 位∈{0,3}（值=词>>2 之掩码不直用·独立构造）
    # 独立口径：全域 12 位词 mask = (Y>>2 ∈ {0,3}*^11) ∧ 尾∈{1,3}
    indep = np.nonzero(hi03[(np.arange(N4) >> 2)] & np.isin(tailv, (1, 3)))[0]
    eq_x0s = (x0s.shape == indep.shape) and bool((x0s == indep).all())
    n_x0s = int(len(x0s))
    log.append("DX2a X0_str n=%d (expect 4096) indep_eq=%s" % (n_x0s, str(eq_x0s)))
    # D-X2 ② Fix∩X_0^str == {4z+3: z∈{0,3}*^11} ∪ {1}·计数 2049
    rv = rev_map()
    fixm = (Ds == Ds[rv])
    fixX = x0s[fixm[x0s]]
    t3 = np.sort(4 * z03 + 3)
    closed = np.sort(np.concatenate([t3, [1]]))
    eq_fixx = (fixX.shape == closed.shape) and bool((fixX == closed).all())
    log.append("DX2b Fix∩X0 n=%d (expect 2049) closed_eq=%s (t3=%d t1=%d)" %
               (len(fixX), str(eq_fixx), len(t3), len(fixX) - len(t3)))
    # D-X2 ③ E_0 == 4E_0 ⊔ X_0^str + 尾 2 空 + 计数链
    E0 = np.nonzero(Ds == 0)[0]
    E0_11 = np.nonzero(Ds[:N11] == 0)[0]
    fourE0 = np.sort(4 * E0_11)
    predE0 = np.sort(np.concatenate([fourE0, x0s]))
    eq_E0 = (E0.shape == predE0.shape) and bool((E0 == predE0).all())
    tail2_E0 = int(np.isin(E0 % 4, (2,)).sum())
    chain_cnt = bool(len(E0) == len(fourE0) + 4096)
    log.append("DX2c E0 n=%d 4E0 n=%d E0_eq=%s tail2=%d (expect 0) count_chain=%s" %
               (len(E0), len(fourE0), str(eq_E0), tail2_E0, str(chain_cnt)))
    # D-X3 M-Dp1 引理机器核：Dp1(w)==0 于 {0,3}*^11 恰 {w=0}+Dp3==D11 全域恒等
    Dp1 = dp_prefix(1, 11)
    Dp3 = dp_prefix(3, 11)
    dsub = Ds[:N11]
    dp3_eq_D = bool((Dp3 == dsub).all())
    z03v = m03_11
    zeros1 = z03v[Dp1[z03v] == 0]
    dp1_ok = bool(len(zeros1) == 1 and zeros1[0] == 0)
    nz3 = np.setdiff1d(np.arange(N11, dtype=np.int64), z03v, assume_unique=False)
    dp1_nonzero_otherside = None  # 判据只核 {0,3}*^11 侧
    log.append("DX3 Dp1 zero-set on {0,3}*^11 n=%d (expect 1·w=0) ok=%s | Dp3==D11 all=%s" %
               (len(zeros1), str(dp1_ok), str(dp3_eq_D)))
    # D-MB 候补·镜像破缺机理探查（判定输出）
    sv = sigma_map()
    anti = bool((Ds[sv] == -Ds).all())
    n_anti_bad = int((Ds[sv] != -Ds).sum())
    sigma_preserve = {"D_anti_all": anti, "D_anti_badcount": n_anti_bad}
    if n_anti_bad:
        badidx = np.nonzero(Ds[sv] != -Ds)[0]
        sigma_preserve["bad_first20"] = [{"w": w12(int(v)), "D": int(Ds[v]), "D_sigma": int(Ds[sv[v]])}
                                         for v in badidx[:20]]
    # npalm（R39 口径复用）
    palmask = np.zeros(N4, dtype=bool)
    p6 = np.arange(4096, dtype=np.int64)
    dg6 = np.zeros((4096, 6), dtype=np.int64); yy = p6.copy()
    for i in range(6):
        dg6[:, 5 - i] = yy % 4; yy //= 4
    pal = (dg6 * (4 ** np.arange(5, -1, -1))).sum(axis=1) * 4096 + \
          (dg6[:, ::-1] * (4 ** np.arange(5, -1, -1))).sum(axis=1)
    palmask[pal] = True
    npalm = fixm & ~palmask & (aD != 0)
    npidx = np.nonzero(npalm)[0]
    reps = npidx[npidx < rv[npidx]]
    tY = (reps & 3).astype(np.int64); tR = (rv[reps] & 3).astype(np.int64)
    M = np.bincount(tY * 4 + tR, minlength=16).reshape(4, 4)
    m_match39 = M.tolist() == M39
    # 词级尾类对称核（npalm 尾 ρ vs 尾 3−ρ）
    tailcnt = {str(r): int((npalm & (tailv == r)).sum()) for r in range(4)}
    sym03 = tailcnt["0"] == tailcnt["3"]; sym12 = tailcnt["1"] == tailcnt["2"]
    # σ 在 rep 词级的保性核：σ(非回文) 非回文 + σ(Fix) Fix 已由 D_anti 蕴含（anti 全过时 Fix 保持）
    if anti:
        sig_fix = bool(fixm[sv[reps]].all())
    else:
        sig_fix = None
    # 破缺差集形态：M[0,0] vs M[3,3] 与 M[1,0] vs M[3,2]
    A00 = reps[(tY == 0) & (tR == 0)]
    A33 = reps[(tY == 3) & (tR == 3)]
    A10 = reps[(tY == 1) & (tR == 0)]
    A32 = reps[(tY == 3) & (tR == 2)]
    diff33 = {}
    if anti:
        sa00 = sv[A00]
        inA33 = np.isin(sa00, A33)
        miss = A00[~inA33]
        extra = A33[~np.isin(A33, sa00)]
        diff33 = {"sigma(A00)_not_in_A33": [w12(int(v)) for v in miss[:10]],
                  "A33_not_sigma(A00)": [w12(int(v)) for v in extra[:10]],
                  "n_miss": int(len(miss)), "n_extra": int(len(extra))}
    log.append("DMB sigma D_anti_all=%s badcount=%d | M_match39=%s M=%s" %
               (str(anti), n_anti_bad, str(m_match39), json.dumps(M.tolist())))
    log.append("DMB tail_cnt=%s sym03=%s sym12=%s sigma_fix_on_reps=%s" %
               (json.dumps(tailcnt), str(sym03), str(sym12), str(sig_fix)))
    log.append("DMB diff33=%s | M10=%d M32=%d | M11=%d M22=%d" %
               (json.dumps(diff33), int(M[1, 0]), int(M[3, 2]), int(M[1, 1]), int(M[2, 2])))
    res = {"meta": {"script": "d8_band_x0-v1.0-20260925.py", "frozen": FROZEN, "part": "part2"},
           "DX1": {"L11_n": int(len(cond11)), "L11_eq": bool(eq11),
                    "L12_n": int(len(cond12)), "L12_eq": bool(eq12), "bad": int(x1_bad)},
           "DX2": {"x0_str_n": n_x0s, "x0_str_indep_eq": bool(eq_x0s),
                    "fixX_n": int(len(fixX)), "fixX_closed_eq": bool(eq_fixx),
                    "E0_n": int(len(E0)), "fourE0_n": int(len(fourE0)),
                    "E0_eq": bool(eq_E0), "E0_tail2": tail2_E0, "count_chain": chain_cnt},
           "DX3": {"dp1_zero_n": int(len(zeros1)), "dp1_only_w0": dp1_ok, "dp3_eq_D11": dp3_eq_D},
           "DMB": {"sigma": sigma_preserve, "M_recompute": M.tolist(), "M_match39": m_match39,
                    "tail_cnt": tailcnt, "sym03": sym03, "sym12": sym12,
                    "sigma_fix_on_reps": sig_fix, "diff33": diff33},
           "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part == "part1":
        run_part1()
    elif part == "part2":
        run_part2()
    elif part == "band":
        run_band(int(sys.argv[2]), int(sys.argv[3]))
    elif part == "merge":
        run_merge()
    else:
        run_part1()
        for cs, ce in BAND_CHUNKS:
            run_band(cs, ce)
        run_merge()
        run_part2()
