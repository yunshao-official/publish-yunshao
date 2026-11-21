# -*- coding: utf-8 -*-
# μ 奇偶模式定理化（R29 主格二·判据书 D-U 系实算）+ 极值档账（D-X 系·在档数据整理）
# 判据书：代数册·d±2轨迹机理与μ奇偶定理化预注册判据书-v1.0-20260921.md（冻结 2026-09-24 02:35:38）
# 口径：D-U0 64 档回归（对照 R28 mint JSON 逐档恒等）；D-U1 对偶谱根源（DP 接受谱 Σ(c)
#       DblTau==内部对 m 值集·64 档）；D-U2 Σ 谱落盘+μ 奇偶再证；D-U3 延伸八档 c=-64..-71
#       器产出（lang_eq_D+Moore==Nerode）+P-U3/P-U4；D-X 极值档四件套账。
# 器流程复用 R26/R28 mint_chain_full 口径（rev_closure/build_dfa/moore/lang/nerode）。
import json, argparse, hashlib, struct
import numpy as np

K = 12
N4 = 4 ** K
G = [[0,0,0],[0,1,-1],[-1,2,-1],[0,2,-2]]
SIGN = [1,-1,-1,1]

# R28 在档 64 档正本（mint_chain_full main+ext JSON 直读做对照）
R28_JSON = {
    "main": "H:/理论存档/01-数学/02-实验与数据/results/mint_chain_full-main-v1.0-20260921.json",
    "ext":  "H:/理论存档/01-数学/02-实验与数据/results/mint_chain_full-ext-v1.0-20260921.json",
}

def s2(n): return bin(n).count("1")
def tau_n(n): return 1 if bin(n).count("1") % 2 == 0 else -1

def build_D_table():
    g = np.array(G, dtype=np.int64)
    sr = np.array([s2(r) & 1 for r in range(4)], dtype=np.int64)
    Darr = np.zeros(N4, dtype=np.int64)
    parr = np.zeros(N4, dtype=np.int64)
    lo = 1
    while lo < N4:
        hi = min(lo*4, N4)
        Ys = np.arange(lo, hi, dtype=np.int64)
        Zs = Ys >> 2
        rs = Ys & 3
        ms = Zs % 3
        Darr[lo:hi] = 3*Darr[Zs] + ((-1) ** parr[Zs]) * g[rs, ms]
        parr[lo:hi] = parr[Zs] ^ sr[rs]
        lo = hi
    return Darr

def step(state, rho):
    d, sg, mu = state
    return (3*d + sg*G[rho][mu], sg*SIGN[rho], (mu+rho) % 3)

def rev_closure(c):
    R = set((c,sg,m) for sg in (1,-1) for m in range(3))
    frontier = list(R)
    while frontier:
        cur = frontier.pop()
        d = cur[0]
        if d == 0:
            continue
        for rho in range(4):
            for mu in range(3):
                for sg in (1,-1):
                    gamma = sg*G[rho][mu]
                    if (d-gamma) % 3 == 0:
                        p = ((d-gamma)//3, sg, mu)
                        if p not in R:
                            R.add(p); frontier.append(p)
    return R

def build_dfa(c):
    START = (0,1,0)
    R = rev_closure(c); R.add(START)
    states = sorted(R)
    idx = {s:i for i,s in enumerate(states)}
    trans = np.full((len(states),4), -1, dtype=np.int64)
    for i,s in enumerate(states):
        for rho in range(4):
            trans[i,rho] = idx.get(step(s,rho), -1)
    reach = {idx[START]}
    stack = [idx[START]]
    while stack:
        u = stack.pop()
        for rho in range(4):
            v = int(trans[u,rho])
            if v >= 0 and v not in reach:
                reach.add(v); stack.append(v)
    keep = sorted(reach)
    kidx = {states[i]: i2 for i2,i in enumerate(keep)}
    tr2 = np.full((len(keep),4), -1, dtype=np.int64)
    for i2,i in enumerate(keep):
        for rho in range(4):
            v = int(trans[i,rho])
            tr2[i2,rho] = kidx[states[v]] if v >= 0 else -1
    q0 = kidx[START]
    accept = [i2 for i2,i in enumerate(keep) if states[i][0]==c]
    keep_states = [states[i] for i in keep]
    return keep_states, tr2, q0, accept

def moore_partition(tr, accept_set, states):
    n = tr.shape[0]
    DEAD = n
    N = n + 1
    TR = np.full((N,4), DEAD, dtype=np.int64)
    TR[:n] = np.where(tr >= 0, tr, DEAD)
    TR[DEAD,:] = DEAD
    lab = np.zeros(N, dtype=np.int64)
    for a in accept_set: lab[a]=1
    while True:
        sig = {}
        newlab = np.zeros(N, dtype=np.int64)
        for i in range(N):
            key = (int(lab[i]),) + tuple(int(lab[int(TR[i,r])]) for r in range(4))
            if key not in sig: sig[key] = len(sig)
            newlab[i] = sig[key]
        if len(sig) == len(set(lab.tolist())):
            classes = {}
            for i in range(N):
                labi = int(lab[i])
                if i < n:
                    classes.setdefault(labi, []).append(states[i])
                else:
                    classes.setdefault(labi, []).append("DEAD")
            return len(sig), classes
        lab = newlab

def lang_value_set(c):
    START = (0,1,0)
    R = rev_closure(c); R.add(START)
    trans = {}
    for s in R:
        for rho in range(4):
            t = step(s,rho)
            if t in R: trans[(s,rho)] = t
    S = {s:set() for s in R}
    S[START].add(0)
    changed = True
    while changed:
        changed = False
        add = {}
        for (s,rho),t in trans.items():
            base = rho
            tgt = S[t]
            na = {v*4+base for v in S[s] if v*4+base < N4 and v*4+base not in tgt}
            if na: add[t] = na
        for s,na in add.items():
            S[s] |= na; changed = True
    acc_val = set()
    for st in R:
        if st[0]==c: acc_val |= S[st]
    return acc_val

def nerode_classcount(c, Darr, pf_bits=6, sf_bits=6):
    okb = (Darr == c).astype(np.uint8)
    pf = 4 ** pf_bits
    sigs = set()
    for a in range(pf):
        chunks = []
        for l in range(sf_bits+1):
            base = a * (4 ** l); cnt = 4 ** l
            if base >= N4: break
            if base + cnt > N4: cnt = N4 - base
            chunks.append(okb[base:base+cnt].tobytes())
        sigs.add(hashlib.md5(b"".join(struct.pack("<I", len(chb)) + chb for chb in chunks)).digest())
    return len(sigs)

def layer_spectrum(c):
    S = set()
    for L in range(0, 60):
        p = 3**L
        q, r = divmod(c, p)
        S.add(q)
        S.add(q + (0 if r == 0 else 1))
    return S

def analyze(c):
    keep_states, tr, q0, accept = build_dfa(c)
    n_min, classes = moore_partition(tr, set(accept), keep_states)
    keep_set = set(keep_states)
    acc_members, dead_members, int_classes = set(), set(), []
    for lab, mem in classes.items():
        nondead = [x for x in mem if x != "DEAD"]
        if "DEAD" in mem:
            dead_members |= set(nondead)
        elif any(x[0]==c for x in nondead):
            acc_members |= set(nondead)
        elif len(nondead) >= 2:
            int_classes.append(sorted(nondead))
    int_classes.sort()
    pairs = []
    for mem in int_classes:
        ds = {x[0] for x in mem}; ms = {x[2] for x in mem}
        sgs = sorted(x[1] for x in mem)
        assert len(ds)==1 and len(ms)==1 and len(mem)==2 and sgs==[-1,1], (c, mem)
        pairs.append((ds.pop(), ms.pop(), sorted(mem)))
    pairs.sort(key=lambda t: t[0])
    reach = len(keep_states)
    acc_n = len(acc_members)
    M_acc = len(acc_members) - 1 if (acc_members and abs(c) >= 2) else 0
    M_dead = len(dead_members)
    M_int = sum(len(g) for g in int_classes) - len(int_classes)
    R_f = reach + 1 - M_acc - M_dead - M_int
    dvals = {s[0] for s in keep_states}
    eq_layers = bool(dvals == layer_spectrum(c))
    return {
        "min_dfa": int(n_min), "reach": reach, "acc": acc_n,
        "M_acc": M_acc, "M_dead": M_dead, "M_int": M_int, "R_f": int(R_f),
        "eq_R": bool(R_f == n_min), "layer_eq": eq_layers,
        "pairs": [[p[0], p[1]] for p in pairs],
    }

# ---------- DP 接受谱 Σ(c)（12 层可达性·D∈[-36,36]×τ×m） ----------
def sigma_spectrum(cs):
    """返回 {c: {(σ,m): True}}：词长≤12 可达终态谱（4^12 定长域口径：S12 闭包）"""
    cur = {(0,1,0)}
    for L in range(12):
        nxt = set()
        for (d, sg, m) in cur:
            for rho in range(4):
                nxt.add(step((d,sg,m), rho))
        cur = cur | nxt
    out = {c: {} for c in cs}
    for (d, sg, m) in cur:
        if d in out:
            out[d][(sg, m)] = True
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    args = ap.parse_args()
    res = {"meta": {"script": "mu_parity_theorem-v1.0-20260924.py",
                    "frozen": "2026-09-24T02:35:38"}, "notes": {}}
    log = []
    def L(m):
        log.append(m); print(m, flush=True)

    if args.part == 1:
        L("== D-U0 递推核 + 64 档回归 ==")
        # 递推核对照（R28 A0 口径重算）
        sA = [0,0,0]
        mism = 0
        Darr = build_D_table()
        for Y in range(1,2000):
            n = Y-1
            sA[n % 3] += tau_n(n)
            if sA[1]-sA[2] != int(Darr[Y]): mism += 1
        res["A0"] = {"mismatch_2000": mism}
        L("mismatch=%d" % mism)

        r28 = {}
        for tag in ("main", "ext"):
            d = json.load(open(R28_JSON[tag], encoding="utf-8"))
            for key, v in d["entries"].items():
                r28[key] = v
        L("R28 entries loaded: %d" % len(r28))

        spec = sigma_spectrum(list(range(0, -64, -1)))
        reg_bad = []
        entries = {}
        for c in range(0, -64, -1):
            a = analyze(c)
            key = "c(%d)" % c
            ref = r28[key]
            for fld in ("min_dfa", "reach", "acc", "M_acc", "M_dead", "M_int"):
                if a[fld] != ref[fld]:
                    reg_bad.append((key, fld, a[fld], ref[fld]))
            if [tuple(x) for x in a["pairs"]] != [tuple(x) for x in ref["pairs"]]:
                reg_bad.append((key, "pairs", a["pairs"], ref["pairs"]))
            # D-U1：DblTau == 内部对 m 值集
            sig = spec[c]
            dbltau = sorted({m for (sg, m) in sig if m in (1,2)
                             and (1, m) in sig and (-1, m) in sig})
            mu_set = sorted({m for (d, m) in a["pairs"]})
            du1_ok = (dbltau == mu_set)
            entries[key] = {
                "sigma": [[sg, m] for (sg, m) in sorted(sig.items())],
                "dbltau": dbltau, "mu_set": mu_set, "du1_ok": du1_ok,
                "pairs": a["pairs"],
                "mu_parity_ok": all(
                    (m == 1) == (d % 2 == 0) for (d, m) in a["pairs"]),
            }
        du1_bad = [k for k, v in entries.items() if not v["du1_ok"]]
        par_bad = [k for k, v in entries.items() if not v["mu_parity_ok"]]
        res["entries"] = entries
        res["verdict"] = {"reg_bad": [str(x) for x in reg_bad],
                          "du1_bad": du1_bad, "mu_parity_bad": par_bad,
                          "A0_mismatch": mism}
        L("reg_bad=%s du1_bad=%s parity_bad=%s" % (reg_bad, du1_bad, par_bad))
        L("== D-U2 Σ 谱样例 ==")
        for c in (0, -3, -6, -9, -54, -55, -63):
            L("c=%d sigma=%s dbltau=%s" % (c, entries["c(%d)" % c]["sigma"],
                                           entries["c(%d)" % c]["dbltau"]))

    if args.part == 2:
        L("== D-U3 延伸八档 c=-64..-71 ==")
        Darr = build_D_table()
        PU_PRED = {-66: [(-22, 1)], -69: [(-23, 2)],
                   -64: [], -65: [], -67: [], -68: [], -70: [], -71: []}
        entries = {}
        lang_bad, nc_bad = [], []
        for c in range(-64, -72, -1):
            a = analyze(c)
            acc_val = lang_value_set(c)
            if acc_val != {int(y) for y in np.where(Darr==c)[0]}: lang_bad.append(c)
            nc = nerode_classcount(c, Darr)
            if nc != a["min_dfa"]: nc_bad.append(c)
            key = "c(%d)" % c
            sig = sigma_spectrum([c])[c]
            dbltau = sorted({m for (sg, m) in sig if m in (1,2)
                             and (1, m) in sig and (-1, m) in sig})
            mu_set = sorted({m for (d, m) in a["pairs"]})
            entries[key] = {
                "min_dfa": a["min_dfa"], "reach": a["reach"], "M_int": a["M_int"],
                "pairs": a["pairs"], "dbltau": dbltau, "mu_set": mu_set,
                "du1_ok": bool(dbltau == mu_set), "layer_eq": a["layer_eq"], "eq_R": a["eq_R"],
                "pred": PU_PRED[c], "pm_hit": bool([tuple(x) for x in a["pairs"]] == PU_PRED[c]),
                "mu_parity_ok": all((m == 1) == (d % 2 == 0) for (d, m) in a["pairs"]),
            }
            L("c=%d R=%d reach=%d Mint=%d pairs=%s du1=%s pm=%s" % (
                c, a["min_dfa"], a["reach"], a["M_int"], a["pairs"],
                entries[key]["du1_ok"], entries[key]["pm_hit"]))
        hits = sum(1 for v in entries.values() if v["pm_hit"])
        mu_hits = sum(1 for v in entries.values() if v["mu_parity_ok"])
        res["entries"] = entries
        res["verdict"] = {"pm_hits": hits, "pm_total": 8,
                          "mu_parity_hits": mu_hits,
                          "lang_bad": lang_bad, "nerode_bad": nc_bad,
                          "du1_bad": [k for k, v in entries.items() if not v["du1_ok"]]}
        L("P-U3 hits=%d/8 mu_parity=%d/8 lang_bad=%s nerode_bad=%s" % (
            hits, mu_hits, lang_bad, nc_bad))

    if args.part == 3:
        L("== D-X 极值档账（R28 在档数据整理·零新数值运行） ==")
        r28 = {}
        for tag in ("main", "ext"):
            d = json.load(open(R28_JSON[tag], encoding="utf-8"))
            for key, v in d["entries"].items():
                r28[key] = v
        rows = {}
        for c in range(0, -64, -1):
            v = r28["c(%d)" % c]
            rows[c] = {"R": v["min_dfa"], "reach": v["reach"], "acc": v["acc"],
                       "M_acc": v["M_acc"], "M_dead": v["M_dead"], "M_int": v["M_int"],
                       "depth3": 0}
            x = abs(c)
            while x >= 3:
                x = x // 3
                rows[c]["depth3"] += 1
        extrema = {}
        for c in (0, -64, -1):
            pass
        # 全谱排序找极值
        srt = sorted(rows.items(), key=lambda kv: (-kv[1]["R"], kv[0]))
        top = [(c, v) for c, v in srt[:4]]
        bot = [(c, v) for c, v in srt[-4:]]
        med = sorted(v["R"] for v in rows.values())[len(rows)//2]
        extrema = {
            "top4": [{"c": c, **v} for c, v in top],
            "bottom4": [{"c": c, **v} for c, v in bot],
            "median_R": med,
            "target": {str(c): rows[c] for c in (-55, -56, -35, -45)},
        }
        res["DX"] = extrema
        L("top4=%s" % json.dumps(extrema["top4"]))
        L("bottom4=%s" % json.dumps(extrema["bottom4"]))
        L("target=%s" % json.dumps(extrema["target"]))

    tag = {1: "reg", 2: "ext8", 3: "dx"}[args.part]
    outp = "H:/理论存档/01-数学/02-实验与数据/results/mu_parity_theorem-%s-v1.0-20260924.json" % tag
    res["log"] = log
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    L("saved %s" % outp)

if __name__ == "__main__":
    main()
