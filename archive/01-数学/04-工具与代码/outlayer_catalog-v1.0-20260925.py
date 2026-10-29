# -*- coding: utf-8 -*-
# 域外词层清单延伸 + M-R4 恒零谱纸面化机器核（R34 主格一+主格二·判据书 D-H 系实算）
# 判据书：代数册·域外词层清单延伸与恒零谱纸面化预注册判据书-v1.0-20260925.md（冻结 2026-09-25 03:25:43）
# part1: D-H0 全域 D 谱器产出 / D-H1 |D|<=200 逐档谱回归 / D-H4 逆序全域谱（201x201 子矩阵+8 带聚合）
# part2: D-H2 继承律域外延伸 43 档全档对表 / D-H3 域外新档八档器产出 / D-H5 M-R4' 偶域轨道合并 Z4 核
import json
import numpy as np

OUT = "H:/理论存档/01-数学/02-实验与数据/results/outlayer_catalog-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T03:25:43"
R33 = "H:/理论存档/01-数学/02-实验与数据/results/nc_combinatorics-part2-v1.0-20260925.json"
N4 = 4 ** 12
N11 = 4 ** 11
G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]
BINS = [0, 71, 200, 600, 1800, 5400, 16200, 48600, 177147]  # 8 几何带（判据书冻结口径）
OUT3 = {c for c in range(-72, -199, -1) if c % 3 == 0}       # 43 档冻结档集
EIGHT = list(range(-72, -80, -1))                            # c=-72..-79

_Cache = {}

def dp_domain(L=12, full_last=True, sorted_out=True):
    """全域语义态 DP（R30-R33 concat 口径）。
    首跑拦截修正（R34 实现层·判据文本零改动）：concat 分块使 ys 数组位置 != 词值；
    sorted_out=True 时按词值排序返回（值索引口径·与 R25 build_D_table Darr 逐位一致，
    3 位小域机器核在档）。part1 的 R32 原口径对照用 sorted_out=False 取 raw。"""
    Gtab = np.array(G, dtype=np.int64)
    fac = np.array([1, -1, -1, 1], dtype=np.int64)
    ys = np.arange(1, dtype=np.int64)
    Ds = np.zeros(1, dtype=np.int64); ts = np.ones(1, dtype=np.int64); ms = np.zeros(1, dtype=np.int64)
    for lay in range(L):
        last = (lay == L - 1)
        parts_D, parts_y, parts_t, parts_m = [], [], [], []
        for r in range(4):
            parts_D.append(Ds * 3 + ts * Gtab[r][ms])
            parts_y.append(ys * 4 + r)
            parts_t.append(ts * fac[r]); parts_m.append((ms + r) % 3)
        ys = np.concatenate(parts_y); Ds = np.concatenate(parts_D)
        ts = np.concatenate(parts_t); ms = np.concatenate(parts_m)
    if sorted_out:
        perm = np.argsort(ys, kind="stable")
        ys = ys[perm]; Ds = Ds[perm]; ms = ms[perm]
    return ys, Ds, ms

# ---------- part1 ----------
def run_part1():
    log = []
    # 首跑拦截修正：排序（值索引）口径 + R32 原口径（乱序索引）对照双落盘
    ys_raw, Ds_raw, ms_raw = dp_domain(12, sorted_out=False)
    perm = np.argsort(ys_raw, kind="stable")
    ys = ys_raw[perm]; Ds = Ds_raw[perm]; ms = ms_raw[perm]
    assert (ys == np.arange(N4, dtype=np.int64)).all()
    del ms_raw
    _Cache['ys'] = ys; _Cache['Ds'] = Ds
    aD = -Ds
    assert aD.min() >= 0
    # D-H0 全域直方图
    hist_all = np.bincount(aD, minlength=177148)
    support = np.nonzero(hist_all)[0]
    sup_size = int(support.size)
    gd = np.diff(support)
    gap_pairs = [(int(support[i]), int(support[i + 1])) for i in np.nonzero(gd > 1)[0]]
    maxgap = int(max((b - a - 1) for a, b in gap_pairs)) if gap_pairs else 0
    top5 = sorted(range(len(hist_all)), key=lambda d: -hist_all[d])[:5]
    density = sup_size / 177148.0
    band_sums = [int(((aD >= BINS[i]) & (aD <= BINS[i + 1])).sum()) for i in range(8)]
    band_support = [int(((support >= BINS[i]) & (support <= BINS[i + 1])).sum()) for i in range(8)]
    log.append("D-H0 support=%d/177148 density=%.6f gaps=%d maxgap=%d top5=%s" %
               (sup_size, density, len(gap_pairs), maxgap,
                str([(d, int(hist_all[d])) for d in top5])))
    log.append("D-H0 band_sums=" + str(band_sums))
    log.append("D-H0 band_support=" + str(band_support))
    # P-H3 结构断言（判定）
    ph3 = bool(len(gap_pairs) > 0 and density < 0.5)
    # D-H1 hist200 回归
    hist200 = hist_all[:201]
    in71 = int(hist_all[:72].sum()); in200 = int(hist_all[:201].sum())
    r33 = json.load(open(R33, encoding="utf-8"))["DG3"]
    h33 = np.array(r33["hist200_head"], dtype=np.int64)
    dh1_bad = int((hist200 != h33).sum())
    dh1_bad += 0 if (in71 == r33["in71"] and in200 == r33["in200"]) else 1
    log.append("D-H1 hist200 regression bad=%d in71=%d in200=%d" % (dh1_bad, in71, in200))
    # D-H4 逆序全域谱（值索引口径）+ R32 原口径（乱序索引）对照
    y = np.arange(N4, dtype=np.int64); rev = np.zeros(N4, dtype=np.int64)
    for _ in range(12):
        rev = rev * 4 + (y & 3); y >>= 2
    del y
    Drev = Ds[rev]
    c1 = aD; c2 = -Drev
    # 201x201 子矩阵
    mask = (c1 <= 200) & (c2 <= 200)
    Mat = np.zeros((201, 201), dtype=np.int64)
    np.add.at(Mat, (c1[mask], c2[mask]), 1)
    rowsum = Mat.sum(axis=1); diag = np.diag(Mat); top1 = Mat.max(axis=1)
    nz = rowsum > 0
    diag_dom = int(((diag >= top1) & nz).sum())
    top1_frac = np.divide(top1, rowsum, out=np.zeros(201), where=nz)
    top1_dom = int((top1_frac[nz] > 0.5).sum())
    cand_i = bool(diag_dom > 100); cand_ii = bool(top1_dom > 100)
    log.append("D-H4 sub201 nonempty=%d diag_dom=%d top1>0.5=%d cand(i)=%s cand(ii)=%s" %
               (int(nz.sum()), diag_dom, top1_dom, cand_i, cand_ii))
    # 8 带聚合矩阵（带区间 [BINS[i], BINS[i+1]]·首跑拦截修正：端点 177147 越界 clip 0..7）
    b1 = np.clip(np.digitize(c1, BINS) - 1, 0, 7)
    b2 = np.clip(np.digitize(c2, BINS) - 1, 0, 7)
    BM = np.zeros((8, 8), dtype=np.int64)
    np.add.at(BM, (b1, b2), 1)
    band_top1 = [int(np.argmax(BM[i])) for i in range(8)]
    log.append("D-H4 band_top1=" + str(band_top1) + " BandMat rowsum=" + str([int(x) for x in BM.sum(axis=1)]))
    samples = {}
    for c in (0, 3, 9, 27, 55, 71, 100, 150, 199):
        nzc = np.nonzero(Mat[c])[0]
        if len(nzc):
            order = nzc[np.argsort(-Mat[c][nzc])][:4]
            samples[str(c)] = {str(int(j)): int(Mat[c][j]) for j in order}
    # R32 D-E0 原口径对照（乱序索引复现·判定输出：在档结论是否在值索引口径下维持）
    y = ys_raw.copy(); rev_raw = np.zeros(N4, dtype=np.int64)
    for _ in range(12):
        rev_raw = rev_raw * 4 + (y & 3); y >>= 2
    del y
    Drev_r32 = Ds_raw[rev_raw]  # R32 原口径（把词值当位置索引）
    del rev_raw
    Mat72T = np.zeros((72, 72), dtype=np.int64)
    a1 = aD; a2 = -Drev_r32
    m72 = (a1 < 72) & (a2 < 72)
    np.add.at(Mat72T, (a1[m72], a2[m72]), 1)
    del Drev_r32, Ds_raw, ys_raw
    rs72 = Mat72T.sum(axis=1); dg72 = np.diag(Mat72T); tp72 = Mat72T.max(axis=1)
    nz72 = rs72 > 0
    diag72 = int(((dg72 >= tp72) & nz72).sum())
    frac72 = np.divide(tp72, rs72, out=np.zeros(72), where=nz72)
    top72 = int((frac72[nz72] > 0.5).sum())
    # 修正（值索引）口径 72x72
    Mat72 = Mat[:72, :72]
    rs72b = Mat72.sum(axis=1); dg72b = np.diag(Mat72); tp72b = Mat72.max(axis=1)
    nz72b = rs72b > 0
    diag72b = int(((dg72b >= tp72b) & nz72b).sum())
    frac72b = np.divide(tp72b, rs72b, out=np.zeros(72), where=nz72b)
    top72b = int((frac72b[nz72b] > 0.5).sum())
    log.append("D-H4 72x72 true-value-index: nonempty=%d diag_dom=%d/72 top1>0.5=%d/72" %
               (int(nz72b.sum()), diag72b, top72b))
    log.append("D-H4 72x72 R32-raw-index reproduce: nonempty=%d diag_dom=%d/72 top1>0.5=%d/72" %
               (int(nz72.sum()), diag72, top72))
    res = {"meta": {"script": "outlayer_catalog-v1.0-20260925.py", "frozen": FROZEN},
           "DH0": {"support_size": sup_size, "density": density, "n_gaps": len(gap_pairs),
                    "max_gap": maxgap, "gap_head": [list(g) for g in gap_pairs[:30]],
                    "top5": [[int(d), int(hist_all[d])] for d in top5],
                    "band_sums": band_sums, "band_support": band_support,
                    "dmax_support": int(support[-1]), "dmax_word": int(hist_all[support[-1]])},
           "DH1": {"hist200": [int(x) for x in hist200], "in71": in71, "in200": in200,
                    "bad": dh1_bad},
           "DH4": {"sub201_nonempty": int(nz.sum()), "diag_dominant": diag_dom,
                    "top1_half": top1_dom, "cand_i": cand_i, "cand_ii": cand_ii,
                    "band_top1": band_top1,
                    "band_matrix": [[int(x) for x in row] for row in BM],
                    "samples": samples,
                    "r32_check_true": {"nonempty": int(nz72b.sum()), "diag_dom": diag72b,
                                        "top1_half": top72b},
                    "r32_check_raw_repro": {"nonempty": int(nz72.sum()), "diag_dom": diag72,
                                             "top1_half": top72}},
           "PH3": ph3,
           "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

# ---------- part2 ----------
SIGN = [1, -1, -1, 1]

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
    keep_states = [states[i] for i in keep]
    return keep_states, tr2, q0, accept

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

def run_part2():
    log = []
    ys, Ds, ms = dp_domain(12)
    aD = -Ds
    hist_all = np.bincount(aD, minlength=177148)
    # D-H2 继承律 43 档
    dh2 = {}; dh2_bad = 0; pure_list = []
    for c in sorted(OUT3, reverse=True):
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
        tail_ok = bool((Xw % 4 <= 3).all()) and len(Xw) == 0 or bool((Xw % 4 == 1).sum() + (Xw % 4 == 3).sum() == len(Xw))
        src_ok = True
        if len(Xw):
            zback = Xw >> 2
            src_ok = bool(zmask11[zback].all() and mu0[zback].all())
        pure = (len(Xw) == 0)
        if pure: pure_list.append(c)
        rec = {"c": int(c), "src": int(src), "n_Ec": int(len(Ec)), "n_4E": int(len(inherit)),
               "n_X": int(len(Xw)), "pure": pure, "wordset_eq": eq, "tail_ok": tail_ok, "src_ok": src_ok}
        if not (eq and tail_ok and src_ok): dh2_bad += 1
        dh2[str(c)] = rec
    log.append("D-H2 43-inherit bad=%d pure=%s" % (dh2_bad, str(pure_list)))
    # 纯继承档态数对照（继承合成律 R(c)=R(c/3)+1·样本档>=3）
    synth = {}
    for c in pure_list[:6]:
        keep_states, tr, q0, acc = build_dfa(c)
        Rm = moore_min(tr, acc)
        synth[str(c)] = {"R": int(Rm), "R_src_plus1": None}
        keep_states2, tr2, q02, acc2 = build_dfa(c // 3)
        synth[str(c)]["R_src_plus1"] = int(moore_min(tr2, acc2)) + 1
    synth_ok = all(v["R"] == v["R_src_plus1"] for v in synth.values()) if synth else None
    log.append("D-H2 synth-check %s ok=%s" % (json.dumps(synth), str(synth_ok)))
    # D-H3 八档器产出
    dh3 = {}; dfa_bad = 0
    for c in EIGHT:
        keep_states, tr, q0, acc = build_dfa(c)
        Rm = moore_min(tr, acc)
        Nn = nerode_sig(c, Ds)
        cnt = int(hist_all[-c])
        rec = {"c": int(c), "n_words": cnt, "R_moore": int(Rm), "R_nerode": int(Nn),
               "moore_eq_nerode": bool(Rm == Nn)}
        if c % 3 == 0:
            zs = np.nonzero(Ds[:N11] == c // 3)[0]
            rec["n_src11"] = int(len(zs))
            rec["contain_4E"] = bool((Ds[4 * zs] == c).all())
            rec["n_4E_in_Ec"] = int((Ds[4 * zs] == c).sum())
        dfa_bad += 0 if rec["moore_eq_nerode"] else 1
        dh3[str(c)] = rec
        log.append("D-H3 c=%d words=%d R_moore=%d R_nerode=%d eq=%s" % (c, cnt, Rm, Nn, rec["moore_eq_nerode"]))
    # 互斥性（同档 D 值唯一 ⟹ 定义互斥·词数表直读核）
    mutex = len(set(dh3[k]["c"] for k in dh3)) == 8
    # 衔接面：E_{-72} 的 4E_{-24} 形态
    zs24 = np.nonzero(Ds[:N11] == -24)[0]
    bridge = {"n_E-24_11bit": int(len(zs24)), "n_E-72": int(hist_all[72]),
              "n_4E-24_in_E-72": int((Ds[4 * zs24] == -72).sum())}
    log.append("D-H3 bridge(4E-24 in E-72): " + json.dumps(bridge))
    # D-H5 M-R4' Z4 核
    def zmul(A, B):
        a, b, cc, d = A; e, f, g, h = B
        return (a*e - (b*h + cc*g + d*f), a*f + b*e - (cc*h + d*g),
                a*g + b*f + cc*e - d*h, a*h + b*g + cc*f + d*e)
    def zconj(A): a, b, cc, d = A; return (a, -d, -cc, -b)
    def zscale(A, n): return (A[0]*n, A[1]*n, A[2]*n, A[3]*n)
    def zadd(A, B): return (A[0]+B[0], A[1]+B[1], A[2]+B[2], A[3]+B[3])
    Z = {0: (1,0,0,0), 1: (0,1,0,0), 2: (0,0,1,0), 3: (0,0,0,1),
         4: (-1,0,0,0), 5: (0,-1,0,0), 6: (0,0,-1,0), 7: (0,0,0,-1)}
    def zpow(n): return Z[n % 8]
    def poly_mul(A, B):
        out = [(0,0,0,0)] * (len(A) + len(B) - 1)
        for i, a in enumerate(A):
            if a == (0,0,0,0): continue
            for j, b in enumerate(B):
                if b == (0,0,0,0): continue
                out[i+j] = zadd(out[i+j], zmul(a, b))
        return out
    def poly_pow(A, n):
        Rr = [(1,0,0,0)]; Bb = list(A)
        while n:
            if n & 1: Rr = poly_mul(Rr, Bb)
            Bb = poly_mul(Bb, Bb); n >>= 1
        return Rr
    def pi_polys(k):
        p = (k + 1) // 2; q = k // 2
        polys = {}
        for m in range(8):
            zm = zpow(-m); z3m = zpow(-3 * m)
            Am = [(1,0,0,0), zm, zmul(zm, zm)]
            A3 = [(1,0,0,0), z3m, zmul(z3m, z3m)]
            polys[m] = poly_mul(poly_pow(Am, p), poly_pow(A3, q))
        return polys
    def S_raw(c, polys):
        L = max(len(v) for v in polys.values())
        out = [(0,0,0,0)] * L
        for m in range(8):
            zc = zpow(m * c)
            for i, pm in enumerate(polys[m]):
                if pm != (0,0,0,0): out[i] = zadd(out[i], zmul(zc, pm))
        return out
    def poly_zero(P): return all(co == (0,0,0,0) for co in P)
    ORB = {(0, 4), (1, 3), (2, 6), (5, 7)}
    dh5 = {}
    for k in (4, 8, 16, 24):
        polys = pi_polys(k)
        Ss = {c: S_raw(c, polys) for c in range(8)}
        zeros = []
        for ci in range(8):
            for cjj in range(ci + 1, 8):
                L = max(len(Ss[ci]), len(Ss[cjj]))
                dif = [(0,0,0,0)] * L
                for i in range(L):
                    a = Ss[ci][i] if i < len(Ss[ci]) else (0,0,0,0)
                    b = Ss[cjj][i] if i < len(Ss[cjj]) else (0,0,0,0)
                    dif[i] = zadd(a, zscale(b, -1))
                if poly_zero(dif): zeros.append([ci, cjj])
        ok = set(map(tuple, zeros)) == ORB
        dh5[str(k)] = {"zero_pairs": zeros, "matches_orbit": ok}
        log.append("D-H5 k=%d zero_pairs=%s orbit_ok=%s" % (k, str(zeros), str(ok)))
    for k in (3, 5):
        polys = pi_polys(k)
        Ss = {c: S_raw(c, polys) for c in range(8)}
        zeros = []
        for ci in range(8):
            for cjj in range(ci + 1, 8):
                L = max(len(Ss[ci]), len(Ss[cjj]))
                dif = [(0,0,0,0)] * L
                for i in range(L):
                    a = Ss[ci][i] if i < len(Ss[ci]) else (0,0,0,0)
                    b = Ss[cjj][i] if i < len(Ss[cjj]) else (0,0,0,0)
                    dif[i] = zadd(a, zscale(b, -1))
                if poly_zero(dif): zeros.append([ci, cjj])
        dh5[str(k)] = {"zero_pairs": zeros}
        log.append("D-H5 k=%d (odd) zero_pairs=%s" % (k, str(zeros)))
    # 4|10 两候选 N1=N3 核 + Q≡0 复核
    def v_of(k): return (3 ** k - 1) // 8
    def F_closed(k):
        if k % 2 == 1:
            M = (3 ** k - 3) // 8
            return [M + 1] * 3 + [M] * 5
        v = v_of(k)
        return [v + 1] + [v] * 7
    def N_gammaA(k, c): return F_closed(k)[c] - (1 if c == 2 else 0)
    def N_gammaB(k, c): return v_of(k) + (1 if c == 0 else 0)
    n13_bad = 0
    for k in range(4, 25, 2):
        for Nf in (N_gammaA, N_gammaB):
            if not (Nf(k, 1) == Nf(k, 3) == v_of(k)): n13_bad += 1
    log.append("D-H5 N1=N3=v both-candidates bad=%d (k=4..24)" % n13_bad)
    def Q2_second_N(k, r, rp, Nfun):
        c, cp = (r - (r % 3)) // 3 % 8, (rp - (rp % 3)) // 3 % 8
        polys = pi_polys(k)
        deg = max(len(vv) for vv in polys.values())
        P = [(0,0,0,0)] * deg
        for m in range(8):
            zc = zpow(m * c); zcp = zpow(m * cp)
            for i, pm in enumerate(polys[m]):
                P[i] = zadd(P[i], zadd(zscale(zmul(zc, pm), Nfun(k, cp)),
                                        zscale(zmul(zcp, pm), -Nfun(k, c))))
        L = len(P); res = (0,0,0,0)
        for i in range(L):
            if P[i] == (0,0,0,0): continue
            for j in range(L):
                if P[j] == (0,0,0,0): continue
                n = i - j
                if n == 0: continue
                term = zmul(P[i], zconj(P[j]))
                res = zadd(res, zmul(zscale(term, -(n * n)), zpow(2 * n)))
        return res
    qzero_bad = 0
    for k in range(4, 25, 2):
        for Nf in (N_gammaA, N_gammaB):
            if Q2_second_N(k, 4, 10, Nf) != (0,0,0,0): qzero_bad += 1
    log.append("D-H5 Q_{4|10}==0 both-candidates k=4..24 bad=%d" % qzero_bad)
    res = {"meta": {"script": "outlayer_catalog-v1.0-20260925.py", "frozen": FROZEN},
           "DH2": {"records": dh2, "bad": dh2_bad, "pure_list": pure_list,
                    "synth_check": synth, "synth_ok": synth_ok},
           "DH3": {"eight": dh3, "dfa_bad": dfa_bad, "mutex": mutex, "bridge": bridge},
           "DH5": {"orbit_tables": {kk: {"zero_pairs": vv.get("zero_pairs"),
                                          "matches_orbit": vv.get("matches_orbit")}
                                     for kk, vv in dh5.items()},
                    "n13_bad": n13_bad, "qzero_bad": qzero_bad},
           "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

if __name__ == "__main__":
    import sys
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part in ("all", "part1"): run_part1()
    if part in ("all", "part2"): run_part2()
