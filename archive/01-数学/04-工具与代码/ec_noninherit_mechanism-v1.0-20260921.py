# -*- coding: utf-8 -*-
# 非继承档态数分解律（R26 主格一·判据书 D-N 系实算）
# 判据书：代数册·非继承档态数分解律与峰位极限点预注册判据书-v1.0-20260921.md（冻结 NTFS 10:16:34 在先）
# 口径：整型零容差；4^12 定长域；回归先行（D0+32 档谱对照 R22/R24/R25 在档正本+继承抽查）；
#       48 档（32+延伸 c=-32..-47）：层谱等号/接受合并定理/死态一步判据/分解律 R=reach+1-Macc-Mdead-Mint；
#       P-N 预测记账（下界五条+增量结构+双分支）。
import json, argparse
from fractions import Fraction
import numpy as np

K = 12
N4 = 4 ** K
G = [[0,0,0],[0,1,-1],[-1,2,-1],[0,2,-2]]
SIGN = [1,-1,-1,1]

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

def moore_minimize(tr, accept_set, states):
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
            return len(sig), {str(k): v for k,v in sorted(classes.items())}
        lab = newlab

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

def lang_value_set(c):
    """语言方程组迭代最小不动点（R24/R25 口径零改动）——延伸档器产出先决通道"""
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

def layer_spectrum(c):
    """候选层谱 ∪{floor(c/3^L), ceil(c/3^L)}（M-E；c<=0 整型；L 至 60 层充分覆盖收敛）"""
    S = set()
    for L in range(0, 60):
        p = 3**L
        q, r = divmod(c, p)   # Python divmod 向下取整 = floor
        S.add(q)
        S.add(q + (0 if r == 0 else 1))   # ceil
    return S

def analyze(c, Darr):
    keep_states, tr, q0, accept = build_dfa(c)
    n_min, classes = moore_minimize(tr, set(accept), keep_states)
    # 一步死判据集（M-G）：非接受且四出边全落闭包外
    inR = set(keep_states)
    dead_pred = set()
    for s in keep_states:
        if s[0] == c: continue
        if all(step(s, r) not in inR for r in range(4)):
            dead_pred.add(s)
    # Moore 类结构
    acc_states = {s for s in keep_states if s[0]==c}
    acc_class_members, n_acc_classes = [], 0
    dead_members, n_dead_classes = [], 0
    int_members, n_int_classes = [], 0
    for k, v in classes.items():
        dead_in = "DEAD" in v
        acc_in = any(x != "DEAD" and x[0]==c for x in v)
        if acc_in:
            acc_class_members += [x for x in v if x != "DEAD"]; n_acc_classes += 1
        elif dead_in:
            dead_members += [x for x in v if x != "DEAD"]; n_dead_classes += 1
        elif len(v) > 1:
            int_members.append(sorted(v)); n_int_classes += 1
    M_acc_act = len(acc_class_members) - n_acc_classes
    M_dead_act = len(dead_members)
    M_int_act = sum(len(g) for g in int_members) - n_int_classes
    reach = sum(len([x for x in v if x != "DEAD"]) for v in classes.values())
    acc_n = len(acc_states)
    dvals = {s[0] for s in keep_states}
    ls = layer_spectrum(c)
    # 公式值（M-F/M-G 绑定）
    M_acc_f = (acc_n - 1) if (abs(c) >= 2 and acc_n >= 1) else 0
    M_dead_f = len(dead_pred)
    R_f = reach + 1 - M_acc_f - M_dead_f - M_int_act
    eq_acc = bool(M_acc_f == M_acc_act)
    eq_dead = bool(sorted(dead_members) == sorted(dead_pred))
    eq_R = bool(R_f == n_min)
    eq_layers = bool(dvals == ls)
    # 单接受类判定（M-F）
    acc_single = bool(n_acc_classes == 1) if (abs(c) >= 2 and acc_n >= 1) else None
    # 语言=4^12 域 D 水平集全等（延伸档器产出先决）
    acc_val = lang_value_set(c)
    eq_D = bool(acc_val == {int(y) for y in np.where(Darr==c)[0]})
    nc = nerode_classcount(c, Darr)
    if nc != n_min:
        nc = -1  # 深采样不自动升级；如实记录不一致
    return {
        "min_dfa": int(n_min), "reach": reach, "acc": acc_n,
        "moore_eq_nerode": bool(nc == int(n_min)),
        "lang_eq_D": eq_D,
        "layer_spectrum_eq": eq_layers, "dvals": sorted(dvals),
        "M_acc_f": M_acc_f, "M_acc_act": M_acc_act, "eq_acc": eq_acc,
        "dead_pred": sorted([str(s) for s in dead_pred]),
        "dead_act": sorted([str(s) for s in dead_members]), "eq_dead": eq_dead,
        "M_int": M_int_act, "int_pairs": [[str(x) for x in g] for g in int_members],
        "M_int_classes": [[str(x) for x in g] for g in int_members],
        "R_f": int(R_f), "eq_R": eq_R, "acc_single_class": acc_single,
        "n_acc_classes": n_acc_classes,
    }

ARCHIVE32 = {0:3, -1:5, -2:5, -3:6, -4:7, -5:7, -6:7, -7:8,
             -8:7, -9:7, -10:9, -11:10, -12:9, -13:9, -14:9, -15:8,
             -16:9, -17:9, -18:9, -19:11, -20:10, -21:9, -22:9, -23:9,
             -24:9, -25:10, -26:9, -27:8, -28:11, -29:12, -30:11, -31:11}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", type=str, required=True)   # main / ext
    ap.add_argument("--c0", type=int, required=True)
    ap.add_argument("--c1", type=int, required=True)
    args = ap.parse_args()
    res = {"A0":{}, "regression":{}, "entries":{}, "P_pred":{}, "notes":{}}
    log = []
    def L(m):
        log.append(m); print(m, flush=True)

    L("== D0 递推核 ==")
    Darr = build_D_table()
    bad = 0
    s = [0,0,0]
    for Y in range(1,2000):
        n = Y-1
        s[n % 3] += tau_n(n)
        if s[1]-s[2] != int(Darr[Y]): bad += 1
    basis_ok = bool(int(Darr[1])==0 and int(Darr[3])==0 and int(Darr[2])==-1 and int(Darr[0])==0)
    res["A0"] = {"mismatch_2000": bad, "basis_ok": basis_ok}
    L("D0 mismatch=%d basis_ok=%s" % (bad, basis_ok))

    L("== D-N0 回归：32 档态数谱 + 继承抽查 ==")
    reg_bad = []
    # 继承正本（R25 在档）：纯 -3/-9/-15/-21/-27；半 -6/-12/-18/-24/-30
    inherit_ref = {-3:("pure",6,5), -9:("pure",7,6), -15:("pure",8,7),
                   -21:("pure",9,8), -27:("pure",8,7),
                   -6:("half",7,5), -12:("half",9,7), -18:("half",9,7),
                   -24:("half",9,7), -30:("half",11,9)}
    inh_ok = True
    for c, (tag2, r_c, r_s) in inherit_ref.items():
        ks, tr, q0, acc = build_dfa(c)
        n_min, _ = moore_minimize(tr, set(acc), ks)
        ok = (n_min == r_c)
        if tag2 == "pure": ok = ok and (n_min == r_s + 1)
        else: ok = ok and (n_min >= r_s + 1)
        if not ok: inh_ok = False
    L("inherit spot-check ok=%s" % inh_ok)
    res["regression"] = {"inherit_spot": inh_ok, "spectrum_bad": reg_bad}

    cs = list(range(args.c0, args.c1-1, -1))
    for c in cs:
        a = analyze(c, Darr)
        a["state_match_archive"] = bool(a["min_dfa"] == ARCHIVE32[c]) if c in ARCHIVE32 else None
        if c in ARCHIVE32:
            if not a["state_match_archive"]:
                reg_bad.append(c)
        res["entries"]["c(%d)" % c] = a
        L("c=%d R=%d reach=%d acc=%d Macc=%d/%d Mdead_eq=%s Mint=%d layEq=%s langEq=%s" % (
            c, a["min_dfa"], a["reach"], a["acc"], a["M_acc_f"], a["M_acc_act"],
            a["eq_dead"], a["M_int"], a["layer_spectrum_eq"], a["lang_eq_D"]))

    res["regression"]["spectrum_bad"] = reg_bad
    L("regression spectrum_bad=%s" % reg_bad)

    L("== D-N6 P-N 预测记账 ==")
    pn = {}
    for c, src in [(-33,-11), (-36,-12), (-39,-13), (-42,-14), (-45,-15)]:
        if ("c(%d)" % c) not in res["entries"]: continue
        act = int(res["entries"]["c(%d)" % c]["min_dfa"])
        srcR = ARCHIVE32[src]
        pn["c(%d)" % c] = {
            "actual": act, "srcR": srcR, "delta": act - srcR,
            "P_N1_lower": {"bound": srcR + 1, "hit": bool(act >= srcR + 1)},
            "P_N2_delta_in_12": bool((act - srcR) in (1, 2)),
            "P_N2_branches": [srcR + 1, srcR + 2],
            "P_N2_branch_hit": bool((act - srcR) in (1, 2)),
        }
    # 双分支中的层尾判别（机器）：X_c 空与否=全部层尾末位 0（层清单判据，R25 口径）
    res["P_pred"] = pn
    L("P_pred: %s" % json.dumps(pn))

    # 汇总裁决
    all_eq = all(res["entries"]["c(%d)" % c]["eq_acc"] and res["entries"]["c(%d)" % c]["eq_dead"]
                 and res["entries"]["c(%d)" % c]["eq_R"] for c in cs)
    all_lay = all(res["entries"]["c(%d)" % c]["layer_spectrum_eq"] for c in cs)
    all_acc2 = all((res["entries"]["c(%d)" % c]["acc_single_class"] is not False)
                   and (res["entries"]["c(%d)" % c]["n_acc_classes"] == 1)
                   for c in cs if abs(c) >= 2 and res["entries"]["c(%d)" % c]["acc"] >= 1)
    e1_ok = bool(res["entries"]["c(-1)"]["n_acc_classes"] == 2) if "c(-1)" in res["entries"] else None
    all_lang = all(res["entries"]["c(%d)" % c]["lang_eq_D"] for c in cs)
    res["notes"]["verdict_parts"] = {
        "decomp_all": all_eq, "layer_all": all_lay, "acc_single_all": all_acc2,
        "E1_two_acc_classes": e1_ok, "lang_all": all_lang,
        "moore_nerode_all": all(res["entries"]["c(%d)" % c]["moore_eq_nerode"] for c in cs),
    }
    L("verdict_parts: %s" % json.dumps(res["notes"]["verdict_parts"]))

    outp = "H:/理论存档/01-数学/02-实验与数据/results/ec_noninherit_mechanism-%s-v1.0-20260921.json" % args.tag
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    L("saved %s" % outp)

if __name__ == "__main__":
    main()
