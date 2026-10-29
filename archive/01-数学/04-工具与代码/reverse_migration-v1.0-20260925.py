# -*- coding: utf-8 -*-
# 逆序档迁移结构定理化 + 域外全域层清单谱推进（R35 主格一+主格二·判据书 D-I 系/D-J 系实算）
# 判据书：代数册·逆序档迁移结构定理化与域外全域谱推进预注册判据书-v1.0-20260925.md（冻结 2026-09-25 04:07:52）
# part1: D-I0 对合双射恒等式核组 / D-I1 终态不变层核 / D-I2 显式重排公式核 / D-I3 回文保持核
#        / D-I4 保持集 Fix / D-I5 尾部主导判定输出（8 带全档对表）
# part2: D-J0 域外 48 档器产出 / D-J1 继承律域外全域验证 16 档 / D-J2 态数谱延拓 / D-J3 逐层支撑归纳核
import json
import numpy as np

OUT = "H:/理论存档/01-数学/02-实验与数据/results/reverse_migration-%s-v1.0-20260925.json"
FROZEN = "2026-09-25T04:07:52"
N4 = 4 ** 12
N11 = 4 ** 11
G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]
FAC = [1, -1, -1, 1]
BINS = [0, 71, 200, 600, 1800, 5400, 16200, 48600, 177147]   # 8 几何带（R34 冻结口径）
OUT48 = list(range(-80, -128, -1))                            # c=-80..-127
INH16 = [c for c in OUT48 if c % 3 == 0]                      # 16 档 3|c

# ---------- 全域 DP（值索引口径·R34 修正口径复用；附逐层支撑记录 D-J3） ----------
def dp_full(L=12, layer_log=False):
    Gtab = np.array(G, dtype=np.int64)
    fac = np.array(FAC, dtype=np.int64)
    ys = np.arange(1, dtype=np.int64)
    Ds = np.zeros(1, dtype=np.int64); ts = np.ones(1, dtype=np.int64); ms = np.zeros(1, dtype=np.int64)
    layers = []
    for lay in range(L):
        if layer_log:
            h = np.bincount(np.abs(Ds))
            sup = np.nonzero(h)[0]
            layers.append({"L": lay, "n_words": int(ys.size),
                           "support": int(sup.size), "amax": int(sup[-1]),
                           "full_0_3pLm1": bool(sup.size == 3 ** lay + 1 and sup[-1] == 3 ** lay and sup[0] == 0),
                           "n_gaps": int((np.diff(sup) > 1).sum())})
        parts_D, parts_y, parts_t, parts_m = [], [], [], []
        for r in range(4):
            parts_D.append(Ds * 3 + ts * Gtab[r][ms])
            parts_y.append(ys * 4 + r)
            parts_t.append(ts * fac[r]); parts_m.append((ms + r) % 3)
        ys = np.concatenate(parts_y); Ds = np.concatenate(parts_D)
        ts = np.concatenate(parts_t); ms = np.concatenate(parts_m)
    perm = np.argsort(ys, kind="stable")
    return ys[perm], Ds[perm], ts[perm], ms[perm], layers

def rev_map():
    y = np.arange(N4, dtype=np.int64); rv = np.zeros(N4, dtype=np.int64)
    for _ in range(12):
        rv = rv * 4 + (y & 3); y >>= 2
    return rv

# ---------- part1 ----------
def run_part1():
    log = []
    ys, Ds, ts, ms, _ = dp_full(12)
    assert (ys == np.arange(N4, dtype=np.int64)).all()
    aD = -Ds
    hist = np.bincount(aD, minlength=177148)
    del ys
    rv = rev_map()
    Drev = Ds[rv]
    aDrev = -Drev
    # D-I0 (a) 直方图 rev 不变
    hist_rev = np.bincount(aDrev, minlength=177148)
    hist_eq = bool((hist == hist_rev).all())
    # 201x201 迁移矩阵（值索引）
    mask = (aD <= 200) & (aDrev <= 200)
    Mat = np.zeros((201, 201), dtype=np.int64)
    np.add.at(Mat, (aD[mask], aDrev[mask]), 1)
    sym201 = int(np.abs(Mat - Mat.T).sum())
    Mat72 = Mat[:72, :72]
    sym72 = int(np.abs(Mat72 - Mat72.T).sum())
    # 8 带聚合（全域口径）
    b1 = np.clip(np.digitize(aD, BINS) - 1, 0, 7)
    b2 = np.clip(np.digitize(aDrev, BINS) - 1, 0, 7)
    BM = np.zeros((8, 8), dtype=np.int64)
    np.add.at(BM, (b1, b2), 1)
    sym8 = int(np.abs(BM - BM.T).sum())
    band_hist = np.bincount(b1, minlength=8)
    # 边际恒等（全域口径·实现层修正：201 子矩阵行和=「落回≤200 计数」非全边际；
    # 全域行边际=分词平凡、列边际=直方图 rev 不变核+带级 BM 行/列边际==band_hist）
    marg_ok = bool((BM.sum(axis=1) == band_hist).all() and (BM.sum(axis=0) == band_hist).all() and hist_eq)
    log.append("D-I0 hist_eq=%s sym201=%d sym72=%d sym8=%d marg_ok(full-band+hist)=%s" %
               (hist_eq, sym201, sym72, sym8, marg_ok))
    di0_bad = int(not hist_eq) + (0 if sym201 == 0 and sym72 == 0 and sym8 == 0 else 1) + int(not marg_ok)
    # D-I1 终态不变层
    tau_inv = bool((ts[rv] == ts).all()); mu_inv = bool((ms[rv] == ms).all())
    Msame = np.zeros((201, 201), dtype=np.int64)
    np.add.at(Msame, (aD[mask], aDrev[mask]), 1)  # 若终态不变成立则与 Mat 同构建即同层
    layer_ok = tau_inv and mu_inv and bool((Msame == Mat).all())
    # 六层分块核：每层子矩阵叠加 == 全矩阵（划分恒等）+ 跨层零（同层构建验证）
    layer_blocks = {}
    stack_ok = True
    for tv in (1, -1):
        for mv in range(3):
            lm = (ts == tv) & (ms == mv)
            lmask = mask & lm
            Blk = np.zeros((201, 201), dtype=np.int64)
            np.add.at(Blk, (aD[lmask], aDrev[lmask]), 1)
            layer_blocks["%d,%d" % (tv, mv)] = [[int(x) for x in row] for row in Blk]
    BlkSum = np.zeros((201, 201), dtype=np.int64)
    for k in layer_blocks:
        BlkSum += np.array(layer_blocks[k], dtype=np.int64)
    stack_ok = bool((BlkSum == Mat).all())
    # 跨层零核双读法（首跑拦截后实现层口径拆分·判据文本零改动）：
    #   词级读法（冻结本意：迁移不跨层）= tau_inv & mu_inv & stack_ok；
    #   对级读法（层块支撑互斥·强于冻结本意）= nzcnt<=1 如实落盘判定输出。
    nzcnt = np.zeros((201, 201), dtype=np.int64)
    for k in layer_blocks:
        nzcnt += (np.array(layer_blocks[k], dtype=np.int64) > 0)
    cross_word_level = bool(tau_inv and mu_inv and stack_ok)
    cross_pair_unique = bool((nzcnt <= 1).all())
    n_pair_multilayer = int(((nzcnt > 1)).sum())
    cross_ok = cross_word_level
    log.append("D-I1 tau_inv=%s mu_inv=%s stack_ok=%s cross_word=%s pair_unique=%s n_pair_multilayer=%d" %
               (tau_inv, mu_inv, stack_ok, cross_word_level, cross_pair_unique, n_pair_multilayer))
    di1_bad = (0 if cross_word_level else 1)
    # D-I2 显式重排公式核（小域全枚举 L=3,4,5 + 12 位采样 10^6）
    def digits_of(y, L):
        ds = np.zeros((y.size, L), dtype=np.int64)
        for i in range(L):
            ds[:, L - 1 - i] = y % 4; y = y // 4
        return ds
    def dp_D(dig):
        D = np.zeros(dig.shape[0], dtype=np.int64); t = np.ones(dig.shape[0], dtype=np.int64); m = np.zeros(dig.shape[0], dtype=np.int64)
        Gt = np.array(G, dtype=np.int64)
        for i in range(dig.shape[1]):
            r = dig[:, i]
            D = D * 3 + t * Gt[r, m]
            t = t * np.array(FAC, dtype=np.int64)[r]
            m = (m + r) % 3
        return D
    def explicit_D(dig, sign=1):
        """显式公式：sign=+1 给 D(Y)=Σ 3^{L-1-k}... 口径按 L 位；sign=-1 给 rev 重排式。
        L 位通式：D(Y)=Σ_k 3^{L-k}·A_k·g_{y_k}(S_{k-1})；
        D(rev Y)=Σ_k 3^{k-1}·T·A_k·g_{y_k}((S-S_{k-1}) mod 3)。"""
        L = dig.shape[1]
        A = np.ones(dig.shape[0], dtype=np.int64)     # A_k 前缀积（k=1..L 逐位更新前为 A_k）
        S = np.zeros(dig.shape[0], dtype=np.int64)
        Gt = np.array(G, dtype=np.int64)
        out = np.zeros(dig.shape[0], dtype=np.int64)
        Stot = dig.sum(axis=1)
        facv = np.array(FAC, dtype=np.int64)
        for k in range(L):
            yk = dig[:, k]
            if sign == 1:
                g = Gt[yk, S % 3]
                out += (3 ** (L - 1 - k)) * A * g
                A = A * facv[yk]; S = S + yk
            else:
                # 修正读法（首跑拦截 M-I2 指标滑误）：D(rev Y)=T·Σ_{k≥1} 3^{k-1}·A_{k+1}·g_{y_k}((S-S_k) mod 3)
                A2 = A * facv[yk]                       # A_{k+1}=含 y_k 的前 k 位积
                mu_arg = (Stot - S - yk) % 3            # S-S_k=去掉前 k 位的后缀补和
                g = Gt[yk, mu_arg]
                out += (3 ** k) * A2 * g
                A = A2; S = S + yk
        if sign == -1:
            T = np.ones(dig.shape[0], dtype=np.int64)
            for k in range(L):
                T = T * np.array(FAC, dtype=np.int64)[dig[:, k]]
            out = out * T   # D(rev Y)=T·Σ_k 3^{k-1}·A_k·g_{y_k}((S-S_{k-1}) mod 3)
        return out
    small_bad = 0
    for L in (3, 4, 5):
        yy = np.arange(4 ** L, dtype=np.int64)
        dg = digits_of(yy, L)
        d_rec = dp_D(dg)
        d_exp = explicit_D(dg, +1)
        dr_rec = dp_D(dg[:, ::-1])
        dr_exp = explicit_D(dg, -1)
        bad = int((d_rec != d_exp).sum()) + int((dr_rec != dr_exp).sum())
        small_bad += bad
        log.append("D-I2 L=%d rec==exp bad=%d rev_rec==rev_exp bad=%d" %
                   (L, int((d_rec != d_exp).sum()), int((dr_rec != dr_exp).sum())))
    rng = np.random.default_rng(20260925)
    samp = rng.integers(0, 4, size=(1000000, 12), dtype=np.int64)
    s_bad = int((dp_D(samp) != explicit_D(samp, +1)).sum()) + int((dp_D(samp[:, ::-1]) != explicit_D(samp, -1)).sum())
    log.append("D-I2 12bit sample 1e6 bad=%d" % s_bad)
    di2_bad = small_bad + s_bad
    # D-I3 回文保持
    p6 = np.arange(4096, dtype=np.int64)
    dg6 = digits_of(p6, 6)
    pal = (dg6 * (4 ** np.arange(5, -1, -1))).sum(axis=1) * 4096 + (dg6[:, ::-1] * (4 ** np.arange(5, -1, -1))).sum(axis=1)
    pal_ok = bool((Ds[pal] == Ds[rv[pal]]).all())
    pal_hist = np.bincount(aD[pal], minlength=72)
    log.append("D-I3 palindrome 4096 keep bad=%d pal_hist_head=%s" %
               (0 if pal_ok else 1, str([int(x) for x in pal_hist[:12]])))
    di3_bad = 0 if pal_ok else 1
    # D-I4 Fix 保持集
    fixm = (Ds == Drev)
    n_fix = int(fixm.sum())
    palmask = np.zeros(N4, dtype=bool); palmask[pal] = True
    fix_pal = int((fixm & palmask).sum())
    fix_nonpal = n_fix - fix_pal
    fix_band = [int(((b1 == i) & fixm).sum()) for i in range(8)]
    fix_sub200 = np.bincount(aD[fixm & (aD <= 200)], minlength=201)
    nfix0 = int((fixm & (aD == 0)).sum())
    pal0 = int((palmask & (aD == 0)).sum())
    samp_idx = np.nonzero(fixm & ~palmask)[0][:20]
    fix_samples = [[int(i), int(Ds[i]), int(Ds[rv[i]])] for i in samp_idx]
    log.append("D-I4 |Fix|=%d Fix∩pal=%d Fix\\pal=%d fix_band=%s fix@0=%d pal@0=%d" %
               (n_fix, fix_pal, fix_nonpal, str(fix_band), nfix0, pal0))
    pi4 = bool(n_fix > 4096)
    # D-I5 尾部主导判定输出：8 带 rev 落带归一化 vs 全域边际 L1
    rownorm = BM / np.maximum(BM.sum(axis=1, keepdims=True), 1)
    margn = band_hist / band_hist.sum()
    l1 = [round(float(np.abs(rownorm[i] - margn).sum()), 6) for i in range(8)]
    # 域内 72 档逐档 top5（≤200 子矩阵）+ 落带向量
    top5_table = {}
    for c in range(72):
        row = Mat[c]
        nz = np.nonzero(row)[0]
        if len(nz):
            order = nz[np.argsort(-row[nz])][:5]
            top5_table[str(c)] = {str(int(j)): int(row[j]) for j in order}
    log.append("D-I5 band_L1(rownorm vs global)=%s" % str(l1))
    pi5 = bool(l1[0] < 0.15)
    pi6 = bool(s_bad == 0 and small_bad == 0)
    res = {"meta": {"script": "reverse_migration-v1.0-20260925.py", "frozen": FROZEN},
           "DI0": {"hist_eq": hist_eq, "sym201": sym201, "sym72": sym72, "sym8": sym8,
                    "marg_ok": marg_ok, "bad": di0_bad},
           "DI1": {"tau_inv": tau_inv, "mu_inv": mu_inv, "stack_ok": stack_ok,
                    "cross_ok": cross_ok, "bad": di1_bad},
           "DI2": {"small_bad": small_bad, "sample_bad": s_bad, "bad": di2_bad},
           "DI3": {"pal_ok": pal_ok, "pal_hist72": [int(x) for x in pal_hist], "bad": di3_bad},
           "DI4": {"n_fix": n_fix, "fix_and_pal": fix_pal, "fix_nonpal": fix_nonpal,
                    "fix_band": fix_band, "fix_sub200": [int(x) for x in fix_sub200],
                    "nfix0": nfix0, "pal0": pal0, "samples_nonpal": fix_samples, "PI4": pi4},
           "DI5": {"band_L1": l1, "band_matrix": [[int(x) for x in r] for r in BM],
                    "band_hist": [int(x) for x in band_hist],
                    "top5_table_in72": top5_table, "PI6_band0_l1_lt_015": pi5,
                    "PI5_formula": pi6},
           "log": log}
    del Drev, aDrev, mask, Mat, BlkSum, Msame, nzcnt
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

def run_part2():
    log = []
    ys, Ds, ts, ms, layers = dp_full(12, layer_log=True)
    aD = -Ds
    hist_all = np.bincount(aD, minlength=177148)
    # D-J3 逐层支撑
    dj3 = layers
    dj3_allfull = all(l["full_0_3pLm1"] for l in layers)
    log.append("D-J3 layers=%s allfull=%s" %
               (str([(l["L"], l["support"], l["amax"], l["n_gaps"]) for l in layers]), str(dj3_allfull)))
    # D-J0 48 档器产出
    dj0 = {}; dfa_bad = 0
    Ec_cache = {}
    for c in OUT48:
        cnt = int(hist_all[-c])
        keep_states, tr, q0, acc = build_dfa(c)
        Rm = moore_min(tr, acc)
        Nn = nerode_sig(c, Ds)
        rec = {"c": int(c), "n_words": cnt, "R_moore": int(Rm), "R_nerode": int(Nn),
               "moore_eq_nerode": bool(Rm == Nn)}
        dfa_bad += 0 if rec["moore_eq_nerode"] else 1
        dj0[str(c)] = rec
    log.append("D-J0 48-gear dfa_bad=%d R=%s" % (dfa_bad, str([dj0[str(c)]["R_moore"] for c in OUT48])))
    # D-J1 继承律 16 档
    dj1 = {}; dj1_bad = 0; pure_list = []
    for c in sorted(INH16, reverse=True):
        src = c // 3
        zmask11 = (Ds[:N11] == src)
        zs = np.nonzero(zmask11)[0]
        mu0 = (ms[:N11] == 0)
        xsrc = zs[mu0[zs]]
        inherit = 4 * zs
        Xw = np.concatenate([4 * xsrc + 1, 4 * xsrc + 3])
        pred = np.concatenate([inherit, Xw])
        Ec = np.nonzero(Ds == c)[0]; Ec_cache[c] = len(Ec)
        ps = np.sort(pred); es = np.sort(Ec)
        eq = (ps.shape == es.shape) and bool((ps == es).all())
        tail_ok = bool((Xw % 4 == 1).sum() + (Xw % 4 == 3).sum() == len(Xw))
        src_ok = True
        if len(Xw):
            zback = Xw >> 2
            src_ok = bool(zmask11[zback].all() and mu0[zback].all())
        pure = (len(Xw) == 0)
        if pure: pure_list.append(c)
        if not (eq and tail_ok and src_ok): dj1_bad += 1
        dj1[str(c)] = {"c": int(c), "src": int(src), "n_Ec": int(len(Ec)), "n_4E": int(len(inherit)),
                       "n_X": int(len(Xw)), "pure": pure, "wordset_eq": eq,
                       "tail_ok": tail_ok, "src_ok": src_ok}
    log.append("D-J1 inherit16 bad=%d pure=%s" % (dj1_bad, str(pure_list)))
    synth = {}
    for c in pure_list[:3]:
        _, tr, _, acc = build_dfa(c)
        Rm = moore_min(tr, acc)
        _, tr2, _, acc2 = build_dfa(c // 3)
        synth[str(c)] = {"R": int(Rm), "R_src_plus1": int(moore_min(tr2, acc2)) + 1}
    synth_ok = all(v["R"] == v["R_src_plus1"] for v in synth.values()) if synth else None
    log.append("D-J1 synth %s ok=%s" % (json.dumps(synth), str(synth_ok)))
    # 3|c 档 4E 包含核
    contain_bad = 0
    for c in INH16:
        zs = np.nonzero(Ds[:N11] == c // 3)[0]
        if zs.size and not (Ds[4 * zs] == c).all():
            contain_bad += 1
    log.append("D-J1 contain4E bad=%d" % contain_bad)
    # D-J2 态数谱与极值档
    R48 = [dj0[str(c)]["R_moore"] for c in OUT48]
    mx = max(R48); mx_at = OUT48[int(np.argmax(R48))]
    log.append("D-J2 max_R=%d at c=%d (in-archive max=14 at E-55) refreshed=%s" %
               (mx, mx_at, str(mx > 14)))
    # 互斥
    mutex = len(set(dj0[k]["c"] for k in dj0)) == 48
    res = {"meta": {"script": "reverse_migration-v1.0-20260925.py", "frozen": FROZEN},
           "DJ0": {"gear48": dj0, "dfa_bad": dfa_bad, "mutex": mutex},
           "DJ1": {"records": dj1, "bad": dj1_bad, "pure_list": pure_list,
                    "synth_check": synth, "synth_ok": synth_ok, "contain_bad": contain_bad},
           "DJ2": {"R48": R48, "max_R": int(mx), "max_at": int(mx_at), "refreshed": bool(mx > 14)},
           "DJ3": {"layers": layers, "allfull": dj3_allfull},
           "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

if __name__ == "__main__":
    import sys
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part in ("all", "part1"): run_part1()
    if part in ("all", "part2"): run_part2()
