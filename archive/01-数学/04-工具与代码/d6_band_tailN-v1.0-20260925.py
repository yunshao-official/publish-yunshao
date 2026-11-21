# -*- coding: utf-8 -*-
# d=6 带深域外验证 + 型 N 尾族完全刻画 + Nerode 全量等价类计算器（R38 主格一+主格二+候补）
# 判据书：代数册·d6带验证与型N尾族刻画预注册判据书-v1.0-20260925.md（冻结 2026-09-25 05:59:25）
# 用法: python d6_band_tailN-v1.0-20260925.py all | part1 | part2 | band START END | merge | nero
# part1: D-L0 锚 / D-L1 64档器 / D-L2 继承21档 / D-L3 段max=23 三态 / D-L5 分解律+C2+归因
# part2: D-T0 锚 / D-T1 尾位保持条件 / D-T2 领头位恒等 / D-T3 Fix全重建 / D-T4 X_c闭式 / D-T5 回文尾分+分层谱
# band : D-L4 分段快扫 c=START..END（Moore 向量化单通道+词数）
# merge: D-L4 全带统计（max 对表 23 三态+词数纪录+直方图+分带统计+max档law_four+抽样3档枚举增信）
# nero : D-Nr 全量签名器（13 档逐深度签名分区==Moore 行为分区双向包含）
import json
import sys
import numpy as np

OUT = "H:/理论存档/01-数学/02-实验与数据/results/d6_band_tailN-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T05:59:25"
N4 = 4 ** 12
N11 = 4 ** 11
G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]
FAC = [1, -1, -1, 1]
R37P1 = "H:/理论存档/01-数学/02-实验与数据/results/d5_band_fixN-part1-v1.0-20260925.json"
R37P2 = "H:/理论存档/01-数学/02-实验与数据/results/d5_band_fixN-part2-v1.0-20260925.json"
R37MG = "H:/理论存档/01-数学/02-实验与数据/results/d5_band_fixN-merge-v1.0-20260925.json"
SEG64 = list(range(-729, -793, -1))          # 本轮段 64 档
INH21 = [c for c in SEG64 if c % 3 == 0]     # 继承 21 档
SRCS = sorted(set(c // 3 for c in INH21), reverse=True)   # 源档 -244..-264（R37 在档段）
SLICE102 = list(range(-3, -307, -3))         # 在档 3|c 档全集 102 档（D-T4）
BAND_CHUNKS = [(-793, -1000), (-1001, -1200), (-1201, -1400), (-1401, -1600),
               (-1601, -1800), (-1801, -2000), (-2001, -2186)]

# ---------- 全域 DP（值索引口径·R34-R37 修正口径复用） ----------
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

def moore_labels(tr, accept_set):
    """Moore 最小化并返回行为分区标签（含显式死态）——D-Nr 用"""
    n = tr.shape[0]; DEAD = n; N = n + 1
    TR = np.full((N, 4), DEAD, dtype=np.int64)
    TR[:n] = np.where(tr >= 0, tr, DEAD); TR[DEAD, :] = DEAD
    lab = np.zeros(N, dtype=np.int64)
    for a in accept_set: lab[a] = 1
    while True:
        key = np.concatenate([lab[:, None], lab[TR]], axis=1)
        uni, newlab = np.unique(key, axis=0, return_inverse=True)
        if int(uni.shape[0]) == int(np.unique(lab).size):
            return int(uni.shape[0]), lab.astype(np.int64), TR, DEAD
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

# ---------- part1（㊱ d=6 带验证） ----------
def run_part1():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    assert (ys == np.arange(N4, dtype=np.int64)).all()
    del ys, ts
    aD = -Ds
    hist_all = np.bincount(aD, minlength=2187)
    # D-L0 回归锚
    r37p1 = json.load(open(R37P1, encoding="utf-8"))
    r37mg = json.load(open(R37MG, encoding="utf-8"))
    anchor_bad = 0
    for c in (-243, -244, -245, -246):
        arch = r37p1["DK1"]["gear64"][str(c)]
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        if Rm != arch["R_moore"] or int(hist_all[-c]) != arch["n_words"]:
            anchor_bad += 1; log.append("DL0 mismatch @%d re=%d arch=%s" % (c, Rm, json.dumps(arch)))
    fb = r37mg["fullband"]
    if not (fb["max"] == 20 and fb["at"] == -487 and fb["tri"] == "hit"):
        anchor_bad += 1; log.append("DL0 merge field mismatch %s" % json.dumps(fb))
    log.append("DL0 anchor_bad=%d (merge fullband=%s)" % (anchor_bad, json.dumps(fb)))
    # D-L1 64 档器产出
    dl1 = {}; dfa_bad = 0
    for c in SEG64:
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        Nn = int(nerode_sig(c, Ds))
        rec = {"c": int(c), "n_words": int(hist_all[-c]), "R_moore": Rm, "R_nerode": Nn,
               "moore_eq_nerode": bool(Rm == Nn)}
        dfa_bad += 0 if rec["moore_eq_nerode"] else 1
        dl1[str(c)] = rec
    mutex = len(set(dl1[k]["c"] for k in dl1)) == 64
    seg_R = [dl1[str(c)]["R_moore"] for c in SEG64]
    seg_max = max(seg_R); seg_max_at = SEG64[seg_R.index(seg_max)]
    # 段 max 档+2 抽样档 DFA 词集级枚举增信
    import random
    rng = random.Random(20260925)
    samp = [seg_max_at] + rng.sample([c for c in SEG64 if c != seg_max_at], 2)
    enum3 = {}
    for c in samp:
        ks, tr, q0, acc = build_dfa(c)
        wc = dfa_word_count(tr, q0, acc, 12)
        enum3[str(c)] = {"dfa_paths": wc, "n_words": dl1[str(c)]["n_words"],
                         "eq": bool(wc == dl1[str(c)]["n_words"])}
    enum_bad = sum(0 if v["eq"] else 1 for v in enum3.values())
    log.append("DL1 gear64 dfa_bad(采样≠Moore 档数·记录)=%d R=%s mutex=%s enum3 bad=%d %s" %
               (dfa_bad, str(seg_R), str(mutex), enum_bad, json.dumps(enum3)))
    # D-L2 继承律 21 档（源档重算+R37 在档双读）
    src_R = {}; src_bad = 0
    for c in SRCS:
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        arch = int(r37p1["DK1"]["gear64"][str(c)]["R_moore"])
        if Rm != arch: src_bad += 1; log.append("DL2 src mismatch @%d re=%d arch=%d" % (c, Rm, arch))
        src_R[str(c)] = {"recompute": Rm, "archive": arch}
    log.append("DL2 src21 dual-read bad=%d %s" % (src_bad, json.dumps(src_R)))
    recs, inh_bad, pure_list = inherit_check(INH21, Ds, ms)
    synth = {}; synth_ok = True
    for c in sorted(pure_list)[:3]:
        Rc = dl1[str(c)]["R_moore"]
        Rs = src_R[str(c // 3)]["recompute"]
        synth[str(c)] = {"R": Rc, "R_src_plus1": Rs + 1}
        if Rc != Rs + 1: synth_ok = False
    log.append("DL2 inherit21 bad=%d pure=%s synth=%s ok=%s" %
               (inh_bad, str(pure_list), json.dumps(synth), str(synth_ok)))
    # D-L3 段 max=23 三态
    tri = "hit" if seg_max == 23 else ("fail" if seg_max > 23 else "unsupported")
    log.append("DL3 seg_max=%d@%d vs 23 -> %s" % (seg_max, seg_max_at, tri))
    # D-L5 分解律+M_int C2+极值归因
    dl5 = {}; law_bad = 0; c2_bad = 0
    for c in SEG64:
        lw = law_four(c, R_from=dl1[str(c)]["R_moore"])
        if not lw["law_ok"]: law_bad += 1
        if lw["M_int"] != lw["C2"]: c2_bad += 1
        dl5[str(c)] = {"reach": lw["reach"], "acc": lw["acc"], "M_acc": lw["M_acc"],
                       "M_dead": lw["M_dead"], "M_int": lw["M_int"], "R": lw["R"],
                       "C2": lw["C2"], "law_ok": lw["law_ok"],
                       "prime": _is_prime(-c), "pure_inh": c in pure_list}
    top = sorted(SEG64, key=lambda c: (-dl1[str(c)]["R_moore"], c))[:5]
    log.append("DL5 law_bad=%d c2_bad=%d top5=%s" %
               (law_bad, c2_bad, json.dumps({str(c): dl5[str(c)] for c in top})))
    res = {"meta": {"script": "d6_band_tailN-v1.0-20260925.py", "frozen": FROZEN, "part": "part1"},
           "DL0": {"anchor_bad": anchor_bad, "merge_fullband": fb},
           "DL1": {"gear64": dl1, "seg_max": int(seg_max), "seg_max_at": int(seg_max_at),
                    "nerode_gap_files": dfa_bad, "mutex": mutex, "enum3": enum3, "enum_bad": enum_bad},
           "DL2": {"src_R": src_R, "src_bad": src_bad, "records": recs, "bad": inh_bad,
                    "pure_list": pure_list, "synth": synth, "synth_ok": synth_ok},
           "DL3": {"seg_max": int(seg_max), "seg_max_at": int(seg_max_at), "tri": tri},
           "DL5": {"records": dl5, "law_bad": law_bad, "c2_bad": c2_bad,
                    "top5": {str(c): dl5[str(c)] for c in top}},
           "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- band（D-L4 分段快扫） ----------
def run_band(cstart, cend):
    log = []
    ys, Ds, ts, ms = dp_full(12)
    del ys, ts
    aD = -Ds
    hist_all = np.bincount(aD, minlength=2187)
    gear = {}
    for c in range(cstart, cend - 1, -1):
        ks, tr, q0, acc = build_dfa(c)
        Rm = int(moore_min_vec(tr, acc))
        gear[str(c)] = {"c": int(c), "n_words": int(hist_all[-c]), "R": Rm}
    Rs = [gear[str(c)]["R"] for c in range(cstart, cend - 1, -1)]
    mx = max(Rs); mx_at = range(cstart, cend - 1, -1)[Rs.index(mx)]
    log.append("BAND [%d..%d] n=%d max=%d@%d" % (cstart, cend, len(Rs), mx, mx_at))
    res = {"meta": {"script": "d6_band_tailN-v1.0-20260925.py", "frozen": FROZEN,
                    "part": "band", "cstart": cstart, "cend": cend},
           "gear": gear, "max": {"R": int(mx), "at": int(mx_at)}, "log": log}
    json.dump(res, open(OUT % ("band%d" % abs(cstart)), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- merge（D-L4 全带统计+增信） ----------
def run_merge():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    del ys, ts
    aD = -Ds
    hist_all = np.bincount(aD, minlength=2187)
    p1 = json.load(open(OUT % "part1", encoding="utf-8"))
    gear = dict(p1["DL1"]["gear64"])
    for cs, ce in BAND_CHUNKS:
        bd = json.load(open(OUT % ("band%d" % abs(cs)), encoding="utf-8"))
        for k, v in bd["gear"].items():
            gear[k] = {"c": v["c"], "n_words": v["n_words"], "R_moore": v["R"]}
    allc = sorted((int(k) for k in gear), reverse=True)
    Rs = [gear[str(c)]["R_moore"] for c in allc]
    mx = max(Rs); mx_at = allc[Rs.index(mx)]
    tri = "hit" if mx == 23 else ("fail" if mx > 23 else "unsupported")
    Rdist = {}
    for r in Rs: Rdist[str(r)] = Rdist.get(str(r), 0) + 1
    nw = [(gear[str(c)]["n_words"], c) for c in allc]
    wmax, wmax_at = max(nw)
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
    lw = law_four(mx_at, R_from=gear[str(mx_at)]["R_moore"])
    lw["prime"] = _is_prime(-mx_at)
    inh_R = [gear[str(c)]["R_moore"] for c in allc if c % 3 == 0]
    non_R = [gear[str(c)]["R_moore"] for c in allc if c % 3 != 0]
    stat = {"n": len(allc), "all": {"min": min(Rs), "max": mx, "mean": round(sum(Rs) / len(Rs), 3)},
            "inherit": {"n": len(inh_R), "max": max(inh_R), "mean": round(sum(inh_R) / len(inh_R), 3)},
            "noninherit": {"n": len(non_R), "max": max(non_R), "mean": round(sum(non_R) / len(non_R), 3)}}
    log.append("MERGE fullband n=%d max=%d@%d tri=%s" % (len(allc), mx, mx_at, tri))
    log.append("MERGE wordmax=%d@%d (record 8128@-162)" % (wmax, wmax_at))
    log.append("MERGE Rdist=%s" % json.dumps(Rdist))
    log.append("MERGE bands d6 %s" % json.dumps(stat))
    log.append("MERGE enum4 bad=%d %s" % (enum_bad, json.dumps(enum4)))
    log.append("MERGE maxlaw %s" % json.dumps(lw))
    res = {"meta": {"script": "d6_band_tailN-v1.0-20260925.py", "frozen": FROZEN, "part": "merge"},
           "fullband": {"n": len(allc), "max": int(mx), "at": int(mx_at), "tri": tri},
           "wordmax": {"v": int(wmax), "at": int(wmax_at)},
           "Rdist": Rdist, "band_d6_stat": stat, "enum4": enum4, "enum_bad": enum_bad,
           "max_law": lw, "log": log}
    json.dump(res, open(OUT % "merge", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- part2（㉝ 尾部收口·型 N 尾族刻画） ----------
def run_part2():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    assert (ys == np.arange(N4, dtype=np.int64)).all()
    del ys
    aD = -Ds
    rv = rev_map()
    Drev = Ds[rv]
    fixm = (Ds == Drev)
    r11 = rev11_map()
    dsub = Ds[:N11]; tsub = ts[:N11]; msub = ms[:N11]
    d11rev = dsub[r11]
    # 前缀 DP 四件
    Dp = {rho: dp_prefix(rho, 11) for rho in range(4)}
    # D-T2 领头位恒等特例
    t2_bad = int(not bool((Dp[0] == dsub).all())) + int(not bool((Dp[3] == dsub).all()))
    log.append("DT2 lead-prefix identity bad=%d (Dp0==D11: %s, Dp3==D11: %s)" %
               (t2_bad, str(bool((Dp[0] == dsub).all())), str(bool((Dp[3] == dsub).all()))))
    tail = (np.arange(N4) % 4).astype(np.int8)
    # D-T0 回归锚
    r37p2 = json.load(open(R37P2, encoding="utf-8"))
    n_fix = int(fixm.sum()); nfix0 = int((fixm & (aD == 0)).sum())
    typeN = n_fix - nfix0
    palmask = np.zeros(N4, dtype=bool)
    p6 = np.arange(4096, dtype=np.int64)
    dg6 = np.zeros((4096, 6), dtype=np.int64); yy = p6.copy()
    for i in range(6):
        dg6[:, 5 - i] = yy % 4; yy //= 4
    pal = (dg6 * (4 ** np.arange(5, -1, -1))).sum(axis=1) * 4096 + \
          (dg6[:, ::-1] * (4 ** np.arange(5, -1, -1))).sum(axis=1)
    palmask[pal] = True
    typeN_pal = int((fixm & palmask & (aD != 0)).sum())
    typeN_nonpal = int((fixm & ~palmask & (aD != 0)).sum())
    anchor_bad = 0
    for name, got, exp in [("n_fix", n_fix, r37p2["DN0"]["n_fix"]),
                           ("typeZ", nfix0, r37p2["DN0"]["typeZ"]),
                           ("typeN", typeN, r37p2["DN0"]["typeN"]),
                           ("typeN_pal", typeN_pal, r37p2["DN0"]["typeN_pal"]),
                           ("typeN_nonpal", typeN_nonpal, r37p2["DN0"]["typeN_nonpal"])]:
        if got != exp: anchor_bad += 1; log.append("DT0 MISMATCH %s got=%d exp=%d" % (name, got, exp))
    # 主域尾 0==2215 对照（R37 DN4 tail_split：前 307 bin=主域 |c|<=306；全数组=全域尾 0）
    md_tail0 = int((fixm & (tail == 0) & (aD <= 306)).sum())
    arch_arr = r37p2["DN4"]["tail_split"]["tail0"]
    arch_md = int(sum(arch_arr[:307])); arch_glob = int(sum(arch_arr))
    glob_tail0 = int((fixm & (tail == 0)).sum())
    if md_tail0 != arch_md:
        anchor_bad += 1; log.append("DT0 md tail0 mismatch %d vs %d" % (md_tail0, arch_md))
    if glob_tail0 != arch_glob:
        anchor_bad += 1; log.append("DT0 glob tail0 mismatch %d vs %d" % (glob_tail0, arch_glob))
    log.append("DT0 anchor_bad=%d md_tail0=%d(arch_md %d) glob_tail0=%d(arch_glob %d)" %
               (anchor_bad, md_tail0, arch_md, glob_tail0, arch_glob))
    # D-T1 尾位保持条件（ρ=0/1/2/3 四类词集级）
    z_all = np.arange(N11, dtype=np.int64)
    conds = {}
    conds[0] = (3 * dsub == d11rev)
    conds[1] = (3 * dsub + tsub * np.array(G[1], dtype=np.int64)[msub] == Dp[1][r11])
    conds[2] = (3 * dsub + tsub * np.array(G[2], dtype=np.int64)[msub] == Dp[2][r11])
    conds[3] = (3 * dsub + tsub * np.array(G[3], dtype=np.int64)[msub] == d11rev)
    dt1_bad = 0; tail_recs = {}
    for rho in range(4):
        pred = np.sort(4 * z_all[conds[rho]] + rho)
        fact = np.sort(np.nonzero(fixm & (tail == rho))[0])
        eq = (pred.shape == fact.shape) and bool((pred == fact).all())
        if not eq: dt1_bad += 1
        tail_recs[str(rho)] = {"n_pred": int(pred.size), "n_fact": int(fact.size), "eq": eq}
    log.append("DT1 tail-condition identity bad=%d %s" % (dt1_bad, json.dumps(tail_recs)))
    # D-T3 Fix 全重建
    recon = np.zeros(N4, dtype=bool)
    for rho in range(4):
        recon[4 * z_all[conds[rho]] + rho] = True
    eq_fix = (int(recon.sum()) == n_fix) and bool((recon == fixm).all())
    npalm = fixm & ~palmask & (aD != 0)
    recon_np = recon & ~palmask & (aD != 0)
    eq_np = bool((recon_np == npalm).all()) and int(npalm.sum()) == 37172
    dt3_bad = (0 if eq_fix else 1) + (0 if eq_np else 1)
    log.append("DT3 recon==Fix: %s (%d) ; recon_np==typeN_nonpal: %s (%d vs 37172) bad=%d" %
               (str(eq_fix), int(recon.sum()), str(eq_np), int(npalm.sum()), dt3_bad))
    # D-T4 X_c 闭式条件 102 档
    mu0 = (msub == 0)
    dt4_bad = 0; x_recs = {}; xt_tot = 0
    for c in SLICE102:
        s = c // 3
        zs = np.nonzero(dsub == s)[0]
        xsrc = zs[mu0[zs]]
        if len(xsrc):
            back = r11[xsrc]
            keep1 = (Dp[1][back] == c)
            keep3 = (d11rev[back] == c)
            pred = np.sort(np.concatenate([4 * xsrc[keep1] + 1, 4 * xsrc[keep3] + 3]))
            xs_all = np.sort(np.concatenate([4 * xsrc + 1, 4 * xsrc + 3]))
            fact = np.sort(xs_all[fixm[xs_all]])
        else:
            pred = np.zeros(0, dtype=np.int64); fact = np.zeros(0, dtype=np.int64)
        eq = (pred.shape == fact.shape) and bool((pred == fact).all())
        if not eq: dt4_bad += 1
        xt_tot += int(len(fact))
        x_recs[str(c)] = {"n_fixX": int(len(fact)), "eq": eq}
    log.append("DT4 Xc closed-form bad=%d (total Fix∩X=%d) %s" %
               (dt4_bad, xt_tot, json.dumps({k: x_recs[k] for k in list(x_recs)[:6]})))
    # 全域 X_c 交叉核：npalm 尾 1/3 且 μ(z)=0 词数（=全域 Fix∩X 总量·全部 |c|>306 则主域计数 0）
    md_mu0_t13 = int((npalm & ((tail == 1) | (tail == 3)) & mu0[np.arange(N4) >> 2] & (aD <= 306)).sum())
    glob_mu0_t13 = int((npalm & ((tail == 1) | (tail == 3)) & mu0[np.arange(N4) >> 2]).sum())
    log.append("DT4 glob Fix∩X crosscheck: md(mu0,tail13)=%d glob=%d (strat 432+543=975)" %
               (md_mu0_t13, glob_mu0_t13))
    # D-T5 回文尾分+分层谱
    hi_all = np.arange(4096, dtype=np.int64)
    pal_words = hi_all * 4096 + (dg6[:, ::-1] * (4 ** np.arange(5, -1, -1))).sum(axis=1)
    pal_tail_bad = 0; pal_tail = {}
    for rho in range(4):
        sel = ((hi_all >> 10) == rho)   # hi 首位（bit10-11）
        pw = np.sort(pal_words[sel])
        pf = np.sort(np.nonzero(palmask & (tail == rho))[0])
        eq = (pw.shape == pf.shape) and bool((pw == pf).all())
        if not eq: pal_tail_bad += 1
        pal_tail[str(rho)] = int(pw.size)
    # Pal⊆各尾类条件集：pal∩tailρ 词全部满足 conds[rho]（词值直查）
    pal_sub_bad = 0
    for rho in range(4):
        pw = 4 * (pal_words >> 2) + rho  # 仅为对齐形状的占位，不用
        pidx = np.nonzero(palmask & (tail == rho))[0]
        zz = pidx >> 2
        ok = bool(conds[rho][zz].all())
        if not ok: pal_sub_bad += 1
    # 全域尾类计数谱（型 N 非回文）
    tail_cnt = {}
    for rho in range(4):
        tail_cnt[str(rho)] = int((npalm & (tail == rho)).sum())
    tot = sum(tail_cnt.values())
    # μ/τ 分层（型 N 非回文按尾类×源词 μ/τ）
    strat = {}
    for rho in range(4):
        idx = np.nonzero(npalm & (tail == rho))[0]
        zz = idx >> 2
        mu_c = np.bincount(msub[zz], minlength=3)
        tau_c = [int((tsub[zz] == 1).sum()), int((tsub[zz] == -1).sum())]
        strat[str(rho)] = {"mu": [int(x) for x in mu_c], "tau_pm": tau_c, "n": int(idx.size)}
    # Fix 率全域分带谱
    fixidx = np.nonzero(fixm)[0]
    fc = np.bincount(aD[fixidx], minlength=531443)
    hc = np.bincount(aD, minlength=531443)
    p3 = 3 ** np.arange(13, dtype=np.int64)
    band_out = {}
    for d in range(13):
        lo = int(p3[d]); hi = int(p3[d + 1]) - 1 if d + 1 < 13 else 531441
        if lo > 531441: break
        seg = slice(lo, hi + 1)
        fsum = int(fc[seg].sum()); hsum = int(hc[seg].sum())
        band_out[str(d)] = {"fix": fsum, "words": hsum,
                            "rate": round(fsum / max(hsum, 1), 8)}
    # 轨道配对尾类转移矩阵
    npidx = np.nonzero(npalm)[0]
    reps = npidx[npidx < rv[npidx]]
    tY = (reps & 3).astype(np.int64); tR = (rv[reps] & 3).astype(np.int64)
    M = np.bincount(tY * 4 + tR, minlength=16).reshape(4, 4)
    log.append("DT5 pal_tail bad=%d %s pal_sub_bad=%d" % (pal_tail_bad, json.dumps(pal_tail), pal_sub_bad))
    log.append("DT5 typeN_nonpal tail counts=%s total=%d (expect 37172)" % (json.dumps(tail_cnt), tot))
    log.append("DT5 orbit transfer M=%s sum=%d (expect 18586)" % (json.dumps(M.tolist()), int(M.sum())))
    log.append("DT5 band rates %s" % json.dumps(band_out))
    log.append("DT5 strat %s" % json.dumps(strat))
    res = {"meta": {"script": "d6_band_tailN-v1.0-20260925.py", "frozen": FROZEN, "part": "part2"},
           "DT0": {"anchor_bad": anchor_bad, "md_tail0": md_tail0, "arch_md": arch_md,
                    "glob_tail0": glob_tail0, "arch_glob": arch_glob},
           "DT1": {"bad": dt1_bad, "records": tail_recs},
           "DT2": {"bad": t2_bad},
           "DT3": {"eq_fix": bool(eq_fix), "eq_nonpal": bool(eq_np), "bad": dt3_bad},
           "DT4": {"records": x_recs, "bad": dt4_bad, "total_fixX": xt_tot},
           "DT5": {"pal_tail": pal_tail, "pal_tail_bad": pal_tail_bad, "pal_sub_bad": pal_sub_bad,
                    "tail_counts": tail_cnt, "total_nonpal": tot, "strat": strat,
                    "band_rates": band_out, "orbit_transfer": M.tolist(), "orbits": int(M.sum())},
           "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

# ---------- nero（候补 ㊲ 全量签名器·D-Nr·状态级 profile 记忆化·双预算对照版） ----------
NERO_FILES = [-11, -29, -35, -55, -128, -129, -130, -131, -244, -269, -486, -487, -305]
def run_nero():
    log = []
    ys, Ds, ts, ms = dp_full(12)
    del ys, ts, ms
    recs = {}; nr_bad = 0; nr2_bad = 0
    for c in NERO_FILES:
        keep_states, tr, q0, acc = build_dfa(c)
        Rm, lab, TR, DEAD = moore_labels(tr, acc)
        accset = set(int(a) for a in acc)
        out = {}
        # 精确通道：状态对区分串 BFS 直径 B*(c)（层 0=标签不同对·逐层前驱传播）
        n = TR.shape[0]
        accv = np.zeros(n, dtype=np.int64)
        for a in acc:
            accv[a] = 1
        dist0 = (accv[:, None] != accv[None, :])   # ε 可区分=接受性不同（非标签不同）
        layer = np.where(dist0, 0, -1)          # -1=未区分·d=区分串长
        frontier = list(zip(*np.nonzero(dist0)))
        d = 0
        while frontier:
            d += 1
            # 前驱传播：找所有 (a,b) 使 TR[a,r]=s2 且 TR[b,r]=t2
            preds = {}
            for a in range(n):
                for r in range(4):
                    preds.setdefault(int(TR[a, r]), []).append(a)
            newf = []
            for (s2, t2) in frontier:
                for a in preds.get(int(s2), []):
                    for b2 in preds.get(int(t2), []):
                        if layer[a, b2] == -1:
                            layer[a, b2] = d
                            newf.append((a, b2))
            frontier = newf
        undist = int((layer[:, :] == -1).sum()) - n   # 对角=自身必未区分
        Bstar = int(layer.max())
        out["Bstar"] = Bstar
        out["undist_pairs_offdiag"] = int(undist)
        for tag, bfun in (("win12", lambda k: 12 - k), ("exact", lambda k: Bstar)):
            depths = {}; worst_fail = -1; fail_info = None
            for k in range(13):
                B = int(bfun(k))
                memo = {}
                def prof(s, b):
                    key = (int(s), b)
                    if key in memo:
                        return memo[key]
                    acc_bit = 1 if int(s) in accset else 0
                    if b == 0:
                        v = np.array([acc_bit], dtype=np.uint8)
                    else:
                        kids = [prof(int(TR[int(s), r]), b - 1) for r in range(4)]
                        v = np.concatenate([np.array([acc_bit], dtype=np.uint8)] + kids)
                    memo[key] = v
                    return v
                u = np.arange(4 ** k, dtype=np.int64)
                cur = np.full(4 ** k, q0, dtype=np.int64)
                for j in range(k):
                    dig = ((u >> (2 * (k - 1 - j))) & 3).astype(np.int64)
                    cur = TR[cur, dig]
                st_k = np.unique(cur)
                profs = {int(s): prof(int(s), B) for s in st_k}
                state_pid = {}; nxt = 0
                items = sorted(profs.keys())
                for s in items:
                    if s not in state_pid:
                        for t in items:
                            if t not in state_pid and np.array_equal(profs[s], profs[t]):
                                state_pid[t] = nxt
                        nxt += 1
                m_k = nxt
                pid_of_state = np.zeros(int(st_k.max()) + 1, dtype=np.int64)
                for s, p in state_pid.items():
                    pid_of_state[s] = p
                plab = pid_of_state[cur]
                mlab = lab[cur]
                nm = int(np.unique(mlab).size); ns = int(np.unique(plab).size)
                ok = (nm == ns == m_k) and \
                     int(np.unique(mlab * (m_k + 1) + plab).shape[0]) == nm
                depths[str(k)] = {"m_k": m_k, "n_states": int(st_k.size),
                                  "moore_classes": nm, "ok": bool(ok)}
                del memo, profs, u, cur, plab, mlab
                if not ok and k > worst_fail:
                    worst_fail = k
                    fail_info = {"depth": k, "moore": nm, "sig": ns, "m_k": m_k}
            out[tag] = {"depths": depths, "all_ok": worst_fail == -1,
                        "worst_fail_depth": worst_fail, "fail_info": fail_info}
        f1 = out["win12"]["all_ok"]; f2 = out["exact"]["all_ok"]
        if not f1: nr_bad += 1
        if not f2: nr2_bad += 1
        recs[str(c)] = {"R_moore": int(Rm), "win12": out["win12"], "exact": out["exact"]}
        log.append("NERO %d R=%d win12_ok=%s(worst %s) exact_ok=%s(worst %s) m_k_win12=%s" %
                   (c, Rm, str(f1), str(out["win12"]["worst_fail_depth"]),
                    str(f2), str(out["exact"]["worst_fail_depth"]),
                    json.dumps({k: v["m_k"] for k, v in out["win12"]["depths"].items()})))
        sys.stdout.flush()
    res = {"meta": {"script": "d6_band_tailN-v1.0-20260925.py", "frozen": FROZEN,
                    "part": "nero", "note": "win12=冻结窗 0..12-k（判负照记）; exact=修正读法预算 R+2（Myhill-Nerode 充分界）"},
           "records": recs, "win12_bad": nr_bad, "exact_bad": nr2_bad, "log": log}
    json.dump(res, open(OUT % "nero", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))

if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part == "all":
        run_part1()
        for cs, ce in BAND_CHUNKS:
            run_band(cs, ce)
        run_merge()
        run_part2()
    elif part == "part1":
        run_part1()
    elif part == "part2":
        run_part2()
    elif part == "band":
        run_band(int(sys.argv[2]), int(sys.argv[3]))
    elif part == "merge":
        run_merge()
    elif part == "nero":
        run_nero()
