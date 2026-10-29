# -*- coding: utf-8 -*-
# M_int 降层链完全性（R28 主格一·判据书 D-M 系实算）
# 判据书：代数册·Mint降层链完全性与峰位轨迹族一般化预注册判据书-v1.0-20260921.md
#         （冻结 NTFS 12:01:04 在先；首跑前更正一起 12:07:52：D-G0 k=3 锚 2π/3→3π/4 就地）
# 口径：整型零容差；4^12 定长域；回归先行（D-M0：递推核+48 档谱对照 R26 正本+R26 在档 19 对复现）；
#       48+16 档（延伸 c=-48..-63）：形态定理/机理判据/完全性双向/四槽归类/P-M 预测对照/+1/+2 分量表。
# 分片：--part 1 = 48 档主片；--part 2 = 延伸片 c=-48..-63 + P-M 对照 + 分量表。
import json, argparse
import numpy as np

K = 12
N4 = 4 ** K
G = [[0,0,0],[0,1,-1],[-1,2,-1],[0,2,-2]]
SIGN = [1,-1,-1,1]

SPECTRUM48 = {0:3, -1:5, -2:5, -3:6, -4:7, -5:7, -6:7, -7:8,
              -8:7, -9:7, -10:9, -11:10, -12:9, -13:9, -14:9, -15:8,
              -16:9, -17:9, -18:9, -19:11, -20:10, -21:9, -22:9, -23:9,
              -24:9, -25:10, -26:9, -27:8, -28:11, -29:12, -30:11, -31:11,
              -32:11, -33:11, -34:12, -35:13, -36:11, -37:11, -38:11, -39:10,
              -40:11, -41:11, -42:11, -43:12, -44:11, -45:9, -46:11, -47:12}

# R26 在档内部对正本（int_pairs 字符串清单；判据书 §一.1）
ARCHIVE_PAIRS = {
    -6: [(-2,1)], -9: [(-3,2)], -12: [(-4,1)], -15: [(-5,2)],
    -18: [(-6,1), (-2,1)], -21: [(-7,2)], -24: [(-8,1)],
    -27: [(-9,2), (-3,2)], -30: [(-10,1)], -33: [(-11,2)],
    -36: [(-12,1), (-4,1)], -39: [(-13,2)], -42: [(-14,1)],
    -45: [(-15,2), (-5,2)],
}
# P-M 形态预测（判据书 §三 D-M4 冻结清单）：(d, mu)
PM_PRED = {
    -48: [(-16,1)], -51: [(-17,2)],
    -54: [(-18,1), (-6,1), (-2,1)],
    -57: [(-19,2)], -60: [(-20,1)],
    -63: [(-21,2), (-7,2)],
    -49: [], -50: [], -52: [], -53: [], -55: [], -56: [], -58: [], -59: [], -61: [], -62: [],
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
    """Moore 最小化：返回 (类数, {label: members})，members 含 'DEAD' 标记"""
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
    import hashlib, struct
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
    """结构化分析：类分解+内部对+机理核验+反向恒等+四槽归类"""
    keep_states, tr, q0, accept = build_dfa(c)
    n_min, classes = moore_partition(tr, set(accept), keep_states)
    keep_set = set(keep_states)
    # 类分解三槽
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
    # 内部对清单：(d, m) + 成员态
    pairs = []   # (d, m, [s_p, s_n])
    for mem in int_classes:
        ds = {x[0] for x in mem}; ms = {x[2] for x in mem}
        sgs = sorted(x[1] for x in mem)
        assert len(ds)==1 and len(ms)==1 and len(mem)==2 and sgs==[-1,1], (c, mem)
        pairs.append((ds.pop(), ms.pop(), sorted(mem)))
    pairs.sort(key=lambda t: t[0])
    pair_member_sets = [frozenset(p[2]) for p in pairs]
    # 机理核验（D-M2）
    def layer_of(d):
        """d=c/3^j 的最小 j；非链值返回 None"""
        j, x = 1, c
        while abs(x) >= 3 and x % 3 == 0:
            x //= 3
            if x == d: return j
            j += 1
        return None
    mech_bad = []
    pair_records = []
    for (d, m, mem) in pairs:
        j = layer_of(d)
        rec = {"pair": [list(mem[0]), list(mem[1])], "d": d, "m": m, "j": j}
        if j is None or abs(d) < 2 or m not in (1,2):
            mech_bad.append(("form", d, m)); pair_records.append(rec); continue
        ok = True
        for s in mem:   # s=(d, ±1, m)
            t0 = step(s, 0)
            t0cls = None
            if t0 in acc_members: t0cls = "acc"
            else:
                for i2, mem2 in enumerate(int_classes):
                    if t0 in mem2: t0cls = ("int", i2); break
            if t0 not in keep_set:
                ok = False; mech_bad.append(("0edge_out", list(s)))
            elif j == 1 and t0cls != "acc":
                ok = False; mech_bad.append(("0edge_not_acc", list(s), str(t0)))
            elif j >= 2:
                up_d = c // (3**(j-1))
                if not (isinstance(t0cls, tuple) and t0[0]==up_d):
                    ok = False; mech_bad.append(("0edge_not_upper", list(s), str(t0)))
            for rho in (1,2,3):
                t = step(s, rho)
                if t in keep_set and t not in dead_members:
                    ok = False; mech_bad.append(("side_alive", list(s), rho, str(t)))
        rec["mech_ok"] = ok
        pair_records.append(rec)
    # 反向恒等（D-M3②）：keep 中满足机理的可达对偶组合
    rev_combos = set()
    for s in keep_states:
        d, sg, m = s
        if d == c: continue
        mate = (d, -sg, m)
        if mate not in keep_set or mate[0] == c: continue
        if sg != 1: continue   # 每对只从 sg=+1 侧收一次
        if m not in (1,2) or abs(d) < 2: continue
        j = layer_of(d)
        if j is None: continue
        ok = True
        for t in (s, mate):
            t0 = step(t, 0)
            if t0 not in keep_set: ok = False; break
            if t0 in dead_members: ok = False; break
            if t0 not in acc_members:
                hit = [mem2 for mem2 in int_classes if t0 in mem2]
                if not hit: ok = False; break
                up_d = c // (3**(j-1)) if j >= 2 else None
                if j == 1: ok = False; break   # j=1 的 0 边必须指接受类
                if hit[0][0][0] != up_d: ok = False; break
            for rho in (1,2,3):
                tt = step(t, rho)
                if tt in keep_set and tt not in dead_members:
                    ok = False; break
            if not ok: break
        if ok:
            rev_combos.add(frozenset([s, mate]))
    rev_eq = bool(rev_combos == set(pair_member_sets))
    # 四槽归类（消歧次序 S2 > S2* > S1 > S3）
    src_pairs = []  # 源档(c/3)内部对 (d,m) 清单由外部传入
    slots = {"S2": 0, "S2star": 0, "S1": 0, "S3": 0}
    slot_detail = []
    for (d, m, mem) in pairs:
        j = layer_of(d)
        if j == 1: slots["S2"] += 1; sl = "S2"
        elif j is not None: slots["S2star"] += 1; sl = "S2star"
        elif (3*d, m) in src_pairs: slots["S1"] += 1; sl = "S1"
        else: slots["S3"] += 1; sl = "S3"
        slot_detail.append({"pair": [d, m], "slot": sl})
    # 基础量
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
        "pair_records": pair_records,
        "mech_bad": [str(x) for x in mech_bad],
        "rev_eq": rev_eq, "rev_n": len(rev_combos),
        "slots": slots, "slot_detail": slot_detail,
        "dead_n": M_dead,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    args = ap.parse_args()
    res = {"A0": {}, "regression": {}, "entries": {}, "P_pred": {}, "notes": {}}
    log = []
    def L(m):
        log.append(m); print(m, flush=True)

    L("== D-M0 递推核 ==")
    Darr = build_D_table()
    bad = 0
    s = [0,0,0]
    for Y in range(1,2000):
        n = Y-1
        s[n % 3] += tau_n(n)
        if s[1]-s[2] != int(Darr[Y]): bad += 1
    res["A0"] = {"mismatch_2000": bad}
    L("mismatch=%d" % bad)

    if args.part == 1:
        cs = list(range(0, -48, -1))
    else:
        cs = list(range(-48, -64, -1))

    L("== 主循环 %d 档 ==" % len(cs))
    for c in cs:
        a = analyze(c)
        if c in SPECTRUM48:
            a["spec_match"] = bool(a["min_dfa"] == SPECTRUM48[c])
        if c in ARCHIVE_PAIRS:
            a["pairs_match_archive"] = bool([tuple(x) for x in a["pairs"]] == ARCHIVE_PAIRS[c])
        res["entries"]["c(%d)" % c] = a
        L("c=%d R=%d reach=%d Mint=%d pairs=%s mechBad=%d revEq=%s slots=%s layEq=%s" % (
            c, a["min_dfa"], a["reach"], a["M_int"], a["pairs"], len(a["mech_bad"]),
            a["rev_eq"], json.dumps(a["slots"]), a["layer_eq"]))

    if args.part == 1:
        L("== D-M0 回归判定 ==")
        spec_bad = [c for c in range(0, -48, -1) if not res["entries"]["c(%d)" % c]["spec_match"]]
        arch_bad = [c for c in ARCHIVE_PAIRS if not res["entries"]["c(%d)" % c]["pairs_match_archive"]]
        form_bad = [c for c in range(0, -48, -1) if res["entries"]["c(%d)" % c]["mech_bad"]]
        rev_bad  = [c for c in range(0, -48, -1) if not res["entries"]["c(%d)" % c]["rev_eq"]]
        R_bad    = [c for c in range(0, -48, -1) if not res["entries"]["c(%d)" % c]["eq_R"]]
        lay_bad  = [c for c in range(0, -48, -1) if not res["entries"]["c(%d)" % c]["layer_eq"]]
        # P-M2 全域断言（48 档部分）：3∤c ⟹ M_int==0
        pm2_bad = [c for c in range(0, -48, -1) if c % 3 != 0 and res["entries"]["c(%d)" % c]["M_int"] != 0]
        # D-M5 分量表（继承对 c=3c', c in -3..-30）
        comp = {}
        for c3 in range(-3, -31, -3):
            src = c3 // 3
            a, b = res["entries"]["c(%d)" % c3], res["entries"]["c(%d)" % src]
            comp["c(%d)" % c3] = {
                "dR": a["reach"] - b["reach"], "dMacc": a["M_acc"] - b["M_acc"],
                "dMdead": a["dead_n"] - b["dead_n"], "dMint": a["M_int"] - b["M_int"],
                "dRstate": a["min_dfa"] - b["min_dfa"],
                "identity_ok": bool((a["reach"]-b["reach"])-(a["M_acc"]-b["M_acc"])
                                    -(a["dead_n"]-b["dead_n"])-(a["M_int"]-b["M_int"])
                                    == a["min_dfa"]-b["min_dfa"]),
            }
        slots_tot = {"S2":0,"S2star":0,"S1":0,"S3":0}
        for c in range(0, -48, -1):
            for k2 in slots_tot: slots_tot[k2] += res["entries"]["c(%d)" % c]["slots"][k2]
        res["notes"]["verdict"] = {
            "spec_bad": spec_bad, "archive_pairs_bad": arch_bad, "form_bad": form_bad,
            "rev_bad": rev_bad, "R_bad": R_bad, "lay_bad": lay_bad, "pm2_noninherit_bad": pm2_bad,
            "slots_total_48": slots_tot, "D_M5_components": comp,
        }
        L("spec_bad=%s arch_bad=%s form_bad=%s rev_bad=%s R_bad=%s lay_bad=%s pm2_bad=%s" % (
            spec_bad, arch_bad, form_bad, rev_bad, R_bad, lay_bad, pm2_bad))
        L("slots48=%s" % json.dumps(slots_tot))
    else:
        L("== P-M 预测对照 ==")
        pn = {}
        for c in range(-48, -64, -1):
            act = [tuple(x) for x in res["entries"]["c(%d)" % c]["pairs"]]
            pred = [tuple(x) for x in PM_PRED[c]]
            pn["c(%d)" % c] = {"pred": PM_PRED[c], "act": res["entries"]["c(%d)" % c]["pairs"],
                               "hit": bool(act == pred)}
        hits = sum(1 for v in pn.values() if v["hit"])
        pm2_bad = [c for c in range(-48, -64, -1) if c % 3 != 0 and res["entries"]["c(%d)" % c]["M_int"] != 0]
        spec_bad = [c for c in range(-48, -64, -1) if not res["entries"]["c(%d)" % c].get("spec_match", True)]
        lang_bad, nc_bad = [], []
        for c in range(-48, -64, -1):
            acc_val = lang_value_set(c)
            if acc_val != {int(y) for y in np.where(Darr==c)[0]}: lang_bad.append(c)
            nc = nerode_classcount(c, Darr)
            if nc != res["entries"]["c(%d)" % c]["min_dfa"]: nc_bad.append(c)
        slots_tot = {"S2":0,"S2star":0,"S1":0,"S3":0}
        for c in range(-48, -64, -1):
            for k2 in slots_tot: slots_tot[k2] += res["entries"]["c(%d)" % c]["slots"][k2]
        res["P_pred"] = pn
        res["notes"]["verdict"] = {
            "pm_hits": hits, "pm_total": 16, "pm2_noninherit_bad": pm2_bad,
            "spec_bad_ext": spec_bad, "lang_bad": lang_bad, "nerode_bad": nc_bad,
            "slots_total_ext": slots_tot,
        }
        L("P-M hits=%d/16 pm2_bad=%s spec_bad=%s lang_bad=%s nerode_bad=%s slots_ext=%s" % (
            hits, pm2_bad, spec_bad, lang_bad, nc_bad, json.dumps(slots_tot)))

    outp = "H:/理论存档/01-数学/02-实验与数据/results/mint_chain_full-%s-v1.0-20260921.json" % ("main" if args.part==1 else "ext")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    L("saved %s" % outp)

if __name__ == "__main__":
    main()
