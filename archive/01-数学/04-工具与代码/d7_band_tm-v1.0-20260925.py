# -*- coding: utf-8 -*-
# d=7 带深域外验证 + 轨道尾类转移矩阵定理化 + X 型 Fix 词全域归档（R39 主格一+主格二+候补并入）
# 判据书：代数册·d7带验证与轨道尾类转移矩阵定理化预注册判据书-v1.0-20260925.md（冻结 2026-09-25 07:26:33）
# 用法: python d7_band_tm-v1.0-20260925.py all | part1 | part2 | band START END | merge
# part1: D-M0 锚 / D-M1 64档器 / D-M2 继承22档 / D-M3 段max=26 三态 / D-M5 分解律+C2+归因
# band : D-M4 分段快扫 c=START..END（Moore 向量化单通道+词数+reach）
# merge: D-M4 全带统计（max 对表 26 三态+两抬升链三次验证+素数律+词数纪录+直方图+分带统计+抽样3档枚举增信）
# part2: D-R0 锚 / D-R1 16格重算 / D-R2 TM-A 上三角零格 / D-R3 TM-B1 (2,0) / D-R4 (3,1)+分层 / D-R5 非零格谱 / D-R6 X型全域直读
import json
import sys
import numpy as np

OUT = "H:/理论存档/01-数学/02-实验与数据/results/d7_band_tm-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T07:26:33"
N4 = 4 ** 12
N11 = 4 ** 11
G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]
FAC = [1, -1, -1, 1]
R38P1 = "H:/理论存档/01-数学/02-实验与数据/results/d6_band_tailN-part1-v1.0-20260925.json"
R38P2 = "H:/理论存档/01-数学/02-实验与数据/results/d6_band_tailN-part2-v1.0-20260925.json"
R38MG = "H:/理论存档/01-数学/02-实验与数据/results/d6_band_tailN-merge-v1.0-20260925.json"
SEG64 = list(range(-2187, -2251, -1))          # 本轮段 64 档
INH22 = [c for c in SEG64 if c % 3 == 0]       # 继承 22 档（3|c 全集）
SRCS = sorted(set(c // 3 for c in INH22), reverse=True)   # 源档 -729..-750（R38 在档段）
PURE_CAND = [c for c in INH22 if (c // 3) % 2 == 1]       # 纯继承候选 11 档 -3(2j+729) 型
BAND_CHUNKS = [(-2251, -2700), (-2701, -3150), (-3151, -3600), (-3601, -4050),
               (-4051, -4500), (-4501, -4950), (-4951, -5400), (-5401, -5850),
               (-5851, -6300), (-6301, -6560)]

# ---------- 全域 DP（值索引口径·R34-R38 修正口径复用） ----------
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
    """最小 DFA 定长 L 接受路径计数（含死态全转移）== 词数增信通道（R37 口径）"""
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

# ---------- part1（㊳ d=7 带验证） ----------
def run_part1():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    assert (ys == np.arange(N4, dtype=np.int64)).all()
    del ys, ts
    aD = -Ds
    hist_all = np.bincount(aD)
    # D-M0 回归锚
    r38p1 = json.load(open(R38P1, encoding="utf-8"))
    r38mg = json.load(open(R38MG, encoding="utf-8"))
    r38p2 = json.load(open(R38P2, encoding="utf-8"))
    anchor_bad = 0
    for c in (-729, -730, -731, -732):
        arch = r38p1["DL1"]["gear64"][str(c)]
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        if Rm != arch["R_moore"] or int(hist_all[-c]) != arch["n_words"]:
            anchor_bad += 1; log.append("DM0 mismatch @%d re=%d arch=%s" % (c, Rm, json.dumps(arch)))
    fb = r38mg["fullband"]
    if not (fb["n"] == 1458 and fb["max"] == 23 and fb["at"] == -1459 and fb["tri"] == "hit"):
        anchor_bad += 1; log.append("DM0 merge fullband mismatch %s" % json.dumps(fb))
    wm = r38mg["wordmax"]
    if not (wm["v"] == 7936 and wm["at"] == -1458):
        anchor_bad += 1; log.append("DM0 wordmax mismatch %s" % json.dumps(wm))
    ot38 = r38p2["DT5"]["orbit_transfer"]
    if r38p2["DT5"]["orbits"] != 18586:
        anchor_bad += 1; log.append("DM0 orbits mismatch")
    log.append("DM0 anchor_bad=%d (fullband=%s wordmax=%s orbits=%d)" %
               (anchor_bad, json.dumps(fb), json.dumps(wm), r38p2["DT5"]["orbits"]))
    # D-M1 64 档器产出
    dm1 = {}
    for c in SEG64:
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        dm1[str(c)] = {"c": int(c), "n_words": int(hist_all[-c]), "R_moore": Rm}
    mutex = len(set(dm1[k]["c"] for k in dm1)) == 64
    seg_R = [dm1[str(c)]["R_moore"] for c in SEG64]
    seg_max = max(seg_R); seg_max_at = SEG64[seg_R.index(seg_max)]
    seg_reach = {}
    for c in SEG64:
        ks, tr, q0, acc = build_dfa(c)
        seg_reach[str(c)] = len(ks)
    # 段 max 档+2 抽样档 DFA 词集级枚举增信
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
    log.append("DM1 gear64 R=%s mutex=%s seg_max=%d@%d enum3 bad=%d %s" %
               (str(seg_R), str(mutex), seg_max, seg_max_at, enum_bad, json.dumps(enum3)))
    # D-M2 继承律 22 档（源档重算+R38 在档双读）
    src_R = {}; src_bad = 0
    for c in SRCS:
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        arch = int(r38p1["DL1"]["gear64"][str(c)]["R_moore"])
        if Rm != arch: src_bad += 1; log.append("DM2 src mismatch @%d re=%d arch=%d" % (c, Rm, arch))
        src_R[str(c)] = {"recompute": Rm, "archive": arch}
    log.append("DM2 src22 dual-read bad=%d %s" % (src_bad, json.dumps(src_R)))
    recs, inh_bad, pure_list = inherit_check(INH22, Ds, ms)
    synth = {}; synth_ok = True
    for c in sorted(pure_list)[:3]:
        Rc = dm1[str(c)]["R_moore"]
        Rs = src_R[str(c // 3)]["recompute"]
        synth[str(c)] = {"R": Rc, "R_src_plus1": Rs + 1}
        if Rc != Rs + 1: synth_ok = False
    pure_match = sorted(pure_list) == sorted(PURE_CAND)
    log.append("DM2 inherit22 bad=%d pure=%s pure_match_cand=%s synth=%s ok=%s" %
               (inh_bad, str(pure_list), str(pure_match), json.dumps(synth), str(synth_ok)))
    # D-M3 段 max=26 三态
    tri = "hit" if seg_max == 26 else ("fail" if seg_max > 26 else "unsupported")
    log.append("DM3 seg_max=%d@%d vs 26 -> %s" % (seg_max, seg_max_at, tri))
    # D-M5 分解律+M_int C2+极值归因
    dm5 = {}; law_bad = 0; c2_bad = 0
    for c in SEG64:
        lw = law_four(c, R_from=dm1[str(c)]["R_moore"])
        if not lw["law_ok"]: law_bad += 1
        if lw["M_int"] != lw["C2"]: c2_bad += 1
        dm5[str(c)] = {"reach": lw["reach"], "acc": lw["acc"], "M_acc": lw["M_acc"],
                       "M_dead": lw["M_dead"], "M_int": lw["M_int"], "R": lw["R"],
                       "C2": lw["C2"], "law_ok": lw["law_ok"],
                       "prime": _is_prime(-c), "pure_inh": c in pure_list}
    # 段内 reach 极大核对（M-K7 reach 带内极大的段级口径）
    reach_max_seg = max(seg_reach.values())
    seg_reach_at = [c for c in SEG64 if seg_reach[str(c)] == reach_max_seg]
    top = sorted(SEG64, key=lambda c: (-dm1[str(c)]["R_moore"], c))[:5]
    log.append("DM5 law_bad=%d c2_bad=%d reach_max_seg=%d@%s top5=%s" %
               (law_bad, c2_bad, reach_max_seg, str(seg_reach_at),
                json.dumps({str(c): dm5[str(c)] for c in top})))
    res = {"meta": {"script": "d7_band_tm-v1.0-20260925.py", "frozen": FROZEN, "part": "part1"},
           "DM0": {"anchor_bad": anchor_bad, "fullband": fb, "wordmax": wm,
                    "orbits": r38p2["DT5"]["orbits"], "orbit_transfer38": ot38},
           "DM1": {"gear64": dm1, "seg_max": int(seg_max), "seg_max_at": int(seg_max_at),
                    "mutex": mutex, "enum3": enum3, "enum_bad": enum_bad,
                    "seg_reach": seg_reach},
           "DM2": {"src_R": src_R, "src_bad": src_bad, "records": recs, "bad": inh_bad,
                    "pure_list": pure_list, "pure_cand": PURE_CAND, "pure_match": pure_match,
                    "synth": synth, "synth_ok": synth_ok},
           "DM3": {"seg_max": int(seg_max), "seg_max_at": int(seg_max_at), "tri": tri},
           "DM5": {"records": dm5, "law_bad": law_bad, "c2_bad": c2_bad,
                    "reach_max_seg": int(reach_max_seg), "reach_max_at": seg_reach_at,
                    "top5": {str(c): dm5[str(c)] for c in top}},
           "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- band（D-M4 分段快扫·含 reach 字段） ----------
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
    res = {"meta": {"script": "d7_band_tm-v1.0-20260925.py", "frozen": FROZEN,
                    "part": "band", "cstart": cstart, "cend": cend},
           "gear": gear, "max": {"R": int(mx), "at": int(mx_at)}, "log": log}
    json.dump(res, open(OUT % ("band%d" % abs(cstart)), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- merge（D-M4 全带统计+两抬升链三次验证+增信） ----------
def run_merge():
    log = []
    p1 = json.load(open(OUT % "part1", encoding="utf-8"))
    gear = dict(p1["DM1"]["gear64"])
    for k in list(gear):
        gear[k] = {"c": gear[k]["c"], "n_words": gear[k]["n_words"],
                   "R": gear[k]["R_moore"], "reach": p1["DM1"]["seg_reach"][k]}
    for cs, ce in BAND_CHUNKS:
        bd = json.load(open(OUT % ("band%d" % abs(cs)), encoding="utf-8"))
        for k, v in bd["gear"].items():
            gear[k] = {"c": v["c"], "n_words": v["n_words"], "R": v["R"], "reach": v["reach"]}
    allc = sorted((int(k) for k in gear), reverse=True)
    Rs = [gear[str(c)]["R"] for c in allc]
    mx = max(Rs); mx_at = allc[Rs.index(mx)]
    tri = "hit" if mx == 26 else ("fail" if mx > 26 else "unsupported")
    Rdist = {}
    for r in Rs: Rdist[str(r)] = Rdist.get(str(r), 0) + 1
    nw = [(gear[str(c)]["n_words"], c) for c in allc]
    wmax, wmax_at = max(nw)
    # 两抬升链三次验证+max 档归因
    lw = law_four(mx_at, R_from=gear[str(mx_at)]["R"])
    lw["prime"] = _is_prime(-mx_at)
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
    log.append("MERGE fullband n=%d max=%d@%d tri=%s" % (len(allc), mx, mx_at, tri))
    log.append("MERGE wordmax=%d@%d (record 8128@-162)" % (wmax, wmax_at))
    log.append("MERGE Rdist=%s" % json.dumps(Rdist))
    log.append("MERGE bands d7 %s" % json.dumps(stat))
    log.append("MERGE maxlaw %s" % json.dumps(lw))
    log.append("MERGE enum4 bad=%d %s" % (enum_bad, json.dumps(enum4)))
    res = {"meta": {"script": "d7_band_tm-v1.0-20260925.py", "frozen": FROZEN, "part": "merge"},
           "fullband": {"n": len(allc), "max": int(mx), "at": int(mx_at), "tri": tri},
           "wordmax": {"v": int(wmax), "at": int(wmax_at)},
           "Rdist": Rdist, "band_d7_stat": stat, "max_law": lw,
           "enum4": enum4, "enum_bad": enum_bad, "log": log}
    json.dump(res, open(OUT % "merge", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- part2（㊴ 转移矩阵定理化+候补 7aq X 型归档） ----------
def run_part2():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    assert (ys == np.arange(N4, dtype=np.int64)).all()
    del ys
    aD = -Ds
    rv = rev_map()
    fixm = (Ds == Ds[rv])
    palmask = np.zeros(N4, dtype=bool)
    p6 = np.arange(4096, dtype=np.int64)
    dg6 = np.zeros((4096, 6), dtype=np.int64); yy = p6.copy()
    for i in range(6):
        dg6[:, 5 - i] = yy % 4; yy //= 4
    pal = (dg6 * (4 ** np.arange(5, -1, -1))).sum(axis=1) * 4096 + \
          (dg6[:, ::-1] * (4 ** np.arange(5, -1, -1))).sum(axis=1)
    palmask[pal] = True
    npalm = fixm & ~palmask & (aD != 0)
    tail = (np.arange(N4) % 4).astype(np.int64)
    first = (np.arange(N4) >> 22).astype(np.int64)
    # D-R0 回归锚
    r38p2 = json.load(open(R38P2, encoding="utf-8"))
    ot38 = r38p2["DT5"]["orbit_transfer"]
    tc38 = r38p2["DT5"]["tail_counts"]
    anchor_bad = 0
    if r38p2["DT5"]["orbits"] != 18586: anchor_bad += 1
    tail_cnt = {}
    for rho in range(4):
        tail_cnt[str(rho)] = int((npalm & (tail == rho)).sum())
    if tail_cnt != tc38:
        anchor_bad += 1; log.append("DR0 tail_counts mismatch %s vs %s" % (json.dumps(tail_cnt), json.dumps(tc38)))
    log.append("DR0 anchor_bad=%d orbits38=%d tail_counts=%s" %
               (anchor_bad, r38p2["DT5"]["orbits"], json.dumps(tail_cnt)))
    # D-R1 16 格全域重算
    npidx = np.nonzero(npalm)[0]
    reps = npidx[npidx < rv[npidx]]
    tY = (reps & 3).astype(np.int64); tR = (rv[reps] & 3).astype(np.int64)
    M = np.bincount(tY * 4 + tR, minlength=16).reshape(4, 4)
    m_bad = 0 if M.tolist() == ot38 else 1
    log.append("DR1 M_recompute=%s sum=%d match38=%s" %
               (json.dumps(M.tolist()), int(M.sum()), str(bool(m_bad == 0))))
    # D-R2 TM-A 上三角 6 格恒零
    upper = [(a, b) for a in range(4) for b in range(4) if a < b]
    ut_zero = all(int(M[a, b]) == 0 for (a, b) in upper)
    ut_bad = 0 if ut_zero else 1
    log.append("DR2 upper-tri zeros=%s cells=%s" %
               (str(ut_zero), json.dumps({("(%d,%d)" % ab): int(M[ab]) for ab in upper})))
    # D-R3 TM-B1 (2,0) 恒零（mod 3 定理机器侧）
    c20 = int((npalm & (tail == 2) & (first == 0)).sum())
    # mod 3 机器侧证：尾 2 首 0 Fix 词的 D 分布非 3 倍数核（全域 Fix 词 aD mod 3 分布·尾2首0 层）
    sel20 = (tail == 2) & (first == 0)
    dmod3_fix20 = np.unique(aD[fixm & sel20] % 3).tolist() if int((fixm & sel20).sum()) else []
    log.append("DR3 cell(2,0) typeN_nonpal=%d (expect 0) fixword_dmod3_set=%s (expect [1,2]-only or empty)" %
               (c20, json.dumps(dmod3_fix20)))
    # D-R4 (3,1) 零格+μ 分层
    c31 = int((npalm & (tail == 3) & (first == 1)).sum())
    # μ_u 分层：μ(1w)=1+μ(w)·w=Y 中 10 位；对尾3首1 全体词分层落盘+对 Fix 词分层（预期全零）
    sel31_all = (tail == 3) & (first == 1)
    idx31_all = np.nonzero(sel31_all)[0]
    mu_all31 = np.zeros(3, dtype=np.int64)
    ww = idx31_all >> 2  # 11 位 1w
    # μ(11 位前缀)=μ(词去尾位)·从 11 位 ms 表直读（值索引口径·11 位词值=w）
    ys2, Ds2, ts2, ms2 = dp_full(11)
    mu_u = ms2[ww]
    for m in range(3):
        mu_all31[m] = int((mu_u == m).sum())
    idx31_fix = np.nonzero(npalm & sel31_all)[0]
    mu_fix31 = np.zeros(3, dtype=np.int64)
    if len(idx31_fix):
        muf = ms2[idx31_fix >> 2]
        for m in range(3):
            mu_fix31[m] = int((muf == m).sum())
    log.append("DR4 cell(3,1) typeN_nonpal=%d (expect 0) mu_layer_all(tail3first1)=%s mu_layer_fix=%s" %
               (c31, json.dumps([int(x) for x in mu_all31]), json.dumps([int(x) for x in mu_fix31])))
    # 和值相容引理机器核：G3[m]+G1[(m-1) mod 3] mod 3 表
    G1 = G[1]; G3 = G[3]
    compat = {m: (G3[m] - G1[(m - 1) % 3]) % 3 for m in range(3)}
    log.append("DR4 compat-table G3[m]-G1[m-1] mod3 = %s (m=2 -> 0 相容层)" % json.dumps(compat))
    # D-R5 非零格谱+对角镜像
    nonzero_cells = {("(%d,%d)" % (i, j)): int(M[i, j]) for i in range(4) for j in range(4) if M[i, j] > 0}
    mirror = {"(1,1)-(2,2)": [int(M[1, 1]), int(M[2, 2])],
              "(0,0)-(3,3)": [int(M[0, 0]), int(M[3, 3])],
              "(1,0)-(3,2)": [int(M[1, 0]), int(M[3, 2])]}
    log.append("DR5 nonzero_cells=%s mirror=%s" % (json.dumps(nonzero_cells), json.dumps(mirror)))
    # D-R6 X 型全域闭式直读逐档归档
    r11 = rev11_map()
    dsub = Ds[:N11]; msub = ms[:N11]
    mu0 = (msub == 0)
    d11rev = dsub[r11]
    Dp1 = dp_prefix(1, 11)
    z_all = np.arange(N11, dtype=np.int64)
    # 拆尾 1/尾 3（词 4z+1 条件 Dp1(rev11(z))==c；词 4z+3 条件 Dp3==D11==d11rev==c；c=3D(z) 自动入档）
    m1 = mu0 & (Dp1[r11] == 3 * dsub)
    m3 = mu0 & (d11rev == 3 * dsub)
    zc = np.arange(N11, dtype=np.int64)
    w1 = 4 * zc[m1] + 1
    w3 = 4 * zc[m3] + 3
    allx = np.concatenate([w1, w3])
    total = int(len(allx))
    # 双口径+三层归因（首跑失配 14258≠11558 归因修正：判负照记+修正读法；aD=|c|≥0·层判据用正数 |c|）
    # 层A=c0 层（|c|==0）；层B=|c|>306 回文层；层C=npalm 口径（R38 11558 对表口径）
    xD = aD[allx]
    ispal = palmask[allx]
    layer_c0 = xD == 0
    layer_pal_big = ispal & (xD > 306)
    layer_npalm = npalm[allx]
    t1_np = int(layer_npalm[:len(w1)].sum()); t3_np = int(layer_npalm[len(w1):].sum())
    c0_1 = int((layer_c0[:len(w1)]).sum()); c0_3 = int((layer_c0[len(w1):]).sum())
    pal_big_1 = int((layer_pal_big[:len(w1)]).sum()); pal_big_3 = int((layer_pal_big[len(w1):]).sum())
    # 主域非零档核（|c|∈[3,306] 应全零）
    md_nonzero = int(((xD >= 3) & (xD <= 306)).sum())
    # 逐档谱（npalm 口径为主谱）
    cc = xD[layer_npalm]
    uq, cnt = np.unique(cc, return_counts=True)
    spec_npalm = {str(int(a)): int(b) for a, b in zip(uq, cnt)}
    n_distinct_c = len(np.unique(xD[layer_npalm]))
    log.append("DR6 X-type closed-form total=%d | layers: c0=%d(t1 %d+t3 %d) pal_big(|c|>306)=%d(t1 %d+t3 %d) npalm=%d(t1 %d expect 432 / t3 %d expect 11126) | md_nonzero(|c| 3..306)=%d (expect 0) ndistinct_c_npalm=%d" %
               (total, int(layer_c0.sum()), c0_1, c0_3, int(layer_pal_big.sum()), pal_big_1, pal_big_3,
                int(layer_npalm.sum()), t1_np, t3_np, md_nonzero, n_distinct_c))
    res = {"meta": {"script": "d7_band_tm-v1.0-20260925.py", "frozen": FROZEN, "part": "part2"},
           "DR0": {"anchor_bad": anchor_bad, "tail_counts": tail_cnt},
           "DR1": {"M": M.tolist(), "sum": int(M.sum()), "bad": m_bad},
           "DR2": {"upper_zero": bool(ut_zero), "bad": ut_bad, "upper_cells": {("(%d,%d)" % ab): int(M[ab]) for ab in upper}},
           "DR3": {"c20": c20, "fix_dmod3_set": dmod3_fix20},
           "DR4": {"c31": c31, "mu_layer_all31": [int(x) for x in mu_all31],
                    "mu_layer_fix31": [int(x) for x in mu_fix31], "compat_table": {str(k): int(v) for k, v in compat.items()}},
           "DR5": {"nonzero_cells": nonzero_cells, "mirror": mirror},
           "DR6": {"total_closedform": total,
                    "layer_c0": {"t1": c0_1, "t3": c0_3, "sum": c0_1 + c0_3},
                    "layer_pal_big": {"t1": pal_big_1, "t3": pal_big_3, "sum": pal_big_1 + pal_big_3},
                    "layer_npalm": {"t1": t1_np, "t3": t3_np, "sum": t1_np + t3_np},
                    "md_nonzero_count": md_nonzero,
                    "spec_npalm": spec_npalm},
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
