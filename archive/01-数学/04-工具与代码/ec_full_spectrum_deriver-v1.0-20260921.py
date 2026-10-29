# -*- coding: utf-8 -*-
# E_c 全谱 32 档推进（R25 主格一·判据书 D 系实算）
# 判据书：代数册·全谱32档推进与态数谱机理预注册判据书-v1.0-20260921.md（冻结 NTFS 09:20:14 在先）
# 口径：整型零容差；4^12 定长域；回归锚 c=0..-15 十六档先行（R22/R21/R24 在档正本）；
#       新档 c=-16..-31 五件套；继承三分律机器印证（D3）；合并明细+P 系预测记账（D4）。
# 用法：python ec_full_spectrum_deriver-v1.0-20260921.py --c0 0 --c1 -15 --tag regression
#       python ec_full_spectrum_deriver-v1.0-20260921.py --c0 -16 --c1 -31 --tag new
import json, sys, argparse
from fractions import Fraction
import numpy as np

K = 12
N4 = 4 ** K            # 16777216
G = [[0,0,0],[0,1,-1],[-1,2,-1],[0,2,-2]]   # g[rho][m]（R18 Z-B 冻结表）
SIGN = [1,-1,-1,1]     # (-1)^{s2(rho)}

def s2(n): return bin(n).count("1")
def tau_n(n): return 1 if bin(n).count("1") % 2 == 0 else -1

def d_direct(Y):
    s = [0,0,0]
    for n in range(Y):
        s[n % 3] += tau_n(n)
    return s[1] - s[2]

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

# ---------- 语义态自动机（器之心，R24 在档口径零改动） ----------
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
    # 可达过滤
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

def moore_minimize_detail(tr, accept_set, states):
    """Moore 最小化（含显式 dead 态，R24 口径）+ 最终类分解明细（D4① 落盘用）"""
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
                    classes.setdefault(labi, []).append(str(states[i]))
                else:
                    classes.setdefault(labi, []).append("DEAD")
            return len(sig), lab[:n], {str(k): v for k,v in sorted(classes.items())}
        lab = newlab

def nerode_signature_classcount(c, Darr, pf_bits=6, sf_bits=6, use_md5=False):
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
        if use_md5:
            h = hashlib.md5()
            for chb in chunks:
                h.update(struct.pack("<I", len(chb))); h.update(chb)
            sigs.add(h.digest())
        else:
            sigs.add(tuple(chunks))
    return len(sigs)

def lang_iter(c):
    """语言方程组迭代最小不动点（R24 口径零改动）"""
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
    return R, S

ATOMS = {(0,1,0),(0,-1,1),(-1,-1,2),(-1,1,2)}   # T,Q,C,B

def machine_layers_atomic(c, R, S):
    """器原子层清单（R24 口径零改动）：逆向 DFS 展开到原子态或环；tail=读串(低位在右)"""
    START=(0,1,0)
    R2=set(R); R2.add(START)
    acc={s for s in R2 if s[0]==c}
    layers={}
    def dfs(state, tail, visited):
        if tail and (state in ATOMS or state in visited):
            L=len(tail); base=int(tail,4) if tail else 0
            vs={v*(4**L)+base for v in S[state] if v*(4**L)+base < N4} if L else set(S[state])
            if vs:
                key=(state,tail)
                if key in layers: layers[key] |= vs
                else: layers[key]=set(vs)
            return
        for p in R2:
            for rho in range(4):
                if step(p,rho)==state:
                    dfs(p, str(rho)+tail, visited|{state})
    for t in sorted(acc):
        dfs(t, "", set())
    return sorted(layers.items(), key=lambda kv: kv[0])

def base_sets():
    T = {0}
    ch = True
    while ch:
        ch = False
        add = set()
        for v in T:
            for r in (0,3):
                nv = v*4+r
                if nv < N4 and nv not in T: add.add(nv)
        if add: T |= add; ch = True
    Qs = {t+1 for t in T if t+1 < N4}
    Cs = set(); j = 0
    while 4**(j+1) <= N4:
        p = 4**(j+1); q = 3*(4**j) - 1
        for a in T:
            v = p*a + q
            if 0 <= v < N4: Cs.add(v)
        j += 1
    Bs = set(); j = 0
    while 4**(j+2) <= N4:
        p = 4**(j+2); q = 4**(j+1) + 1
        for a in T:
            v = p*a + q
            if 0 <= v < N4: Bs.add(v)
        j += 1
    E1 = Cs | Bs
    E2v = {v for v in (4*cc+r for cc in Cs for r in (1,2)) if v < N4} \
        | {v for v in (4*q+r for q in Qs for r in (2,3)) if v < N4}
    return T, Qs, Cs, Bs, E1, E2v

def archive_layers(c, T, Qs, Cs, Bs, E1, E2v):
    """在档层值集列表（c=0..-7 层清单算术式正本，R24 口径零改动）"""
    LIM = N4
    def fl(gen): return {v for v in gen if v < LIM}
    if c == 0:  return [set(T), fl(t+1 for t in T)]
    if c == -1: return [fl(4*q+1 for q in Qs), fl(4*t+2 for t in T), fl(4*cc+3 for cc in Cs)]
    if c == -2: return [fl(4*cc+1 for cc in Cs), fl(4*cc+2 for cc in Cs), fl(4*q+2 for q in Qs), fl(4*q+3 for q in Qs)]
    if c == -3: return [{4*y for y in E1 if 4*y < N4}]
    if c == -4: return [fl(16*cc+10 for cc in Cs), fl(16*cc+11 for cc in Cs), fl(4*b+1 for b in Bs), fl(4*b+2 for b in Bs)]
    if c == -5: return [fl(16*cc+9 for cc in Cs), fl(4*b+3 for b in Bs)]
    if c == -6: return [{4*y for y in E2v if 4*y < N4}, fl(16*cc+5 for cc in Cs), fl(16*q+9 for q in Qs),
                        fl(16*cc+7 for cc in Cs), fl(16*q+11 for q in Qs)]
    if c == -7: return [fl(16*cc+3 for cc in Cs), fl(16*cc+6 for cc in Cs), fl(16*q+10 for q in Qs), fl(16*q+13 for q in Qs)]
    return None

def partition_equivalent(A, B):
    """A=在档层列表，B=器层列表（R24 口径零改动）"""
    ua = set(); ub = set()
    for s in A: ua |= s
    for s in B: ub |= s
    if ua != ub: return False
    for sa in A:
        covered = set()
        for sb in B:
            if sb <= sa: covered |= sb
        if covered != sa: return False
    return True

def solve3(M, b):
    A = [row[:] + [b[i]] for i,row in enumerate(M)]
    for col in range(3):
        piv = next(r for r in range(col,3) if A[r][col] != 0)
        A[col], A[piv] = A[piv], A[col]
        pv = A[col][col]
        A[col] = [x/pv for x in A[col]]
        for r in range(3):
            if r != col and A[r][col] != 0:
                f = A[r][col]
                A[r] = [x - f*y for x,y in zip(A[r], A[col])]
    return A[0][3], A[1][3], A[2][3]

def fmt_fr(x):
    x = Fraction(x)
    return str(x.numerator) if x.denominator==1 else "%d/%d" % (x.numerator, x.denominator)

def cf_to_json(r):
    if r["kind"] == "a2k+b":
        params = [fmt_fr(r["A"]), fmt_fr(r["B"])]
    else:
        params = [fmt_fr(r["p"]), fmt_fr(r["q"]), fmt_fr(r["r"])]
    return {"kind": r["kind"], "k0": r["k0"], "head": r.get("head", {}), "params": params}

def fitseg(Nv, i0):
    """尾段拟合：从 k=i0+1 起（索引 i0），a2k+b 或 rec3；返回 dict 或 None（R24 口径）"""
    try:
        A = Fraction(Nv[i0+1]-Nv[i0], 2**(i0+1)); B = Fraction(Nv[i0]) - A*(2**(i0+1))
        if all(A*(2**k)+B == Nv[k-1] for k in range(i0+1,13)):
            return {"kind":"a2k+b","A":A,"B":B,"k0":i0+1}
    except Exception:
        pass
    for st in range(i0, min(i0+3, 9)):
        try:
            M = [[Fraction(Nv[st+1]),Fraction(Nv[st]),1],[Fraction(Nv[st+2]),Fraction(Nv[st+1]),1],[Fraction(Nv[st+3]),Fraction(Nv[st+2]),1]]
            b = [Fraction(Nv[st+2]),Fraction(Nv[st+3]),Fraction(Nv[st+4])]
            p,q,r = solve3(M,b)
            if all(p*Nv[k+1]+q*Nv[k]+r == Nv[k+2] for k in range(st,10)):
                return {"kind":"rec3","p":p,"q":q,"r":r,"k0":st+1}
        except Exception:
            continue
    return None

def fit_closed_form(Nv):
    """分段闭式：前段逐点表列+尾段闭式；全档 k=1..12 逐点零容差即成立。
    R25 扩展：前导零段搜索范围 k0<=9（rec3 需连续 5 点 k<=12 域内验证）。"""
    r = fitseg(Nv, 0)
    if r is not None:
        r["head"] = {}
        return ("seg", r)
    for k0 in range(2, 10):
        r = fitseg(Nv, k0-1)
        if r is not None:
            r["head"] = {k: Nv[k-1] for k in range(1, k0)}
            return ("seg", r)
    return None

def cf_known(c, k):
    """在档闭式谱（c=0..-7；k>=1；E_-3/E_-4/E_-7 的 k=1 特例=0 由直接表核对）"""
    if c == 0:  return 2**(k+1)-1
    if c == -1: return 3*2**(k-1)-2
    if c == -2: return 2**(k+1)-4
    if c == -3: return 0 if k == 1 else 3*2**(k-2)-2
    if c == -4: return 0 if k == 1 else 2**k-4
    if c == -5: return 0 if k == 1 else 2**(k-1)-2
    if c == -6: return 0 if k == 1 else 2**(k+1)-8
    if c == -7: return 0 if k == 1 else 2**k-4
    return None

# ---------- R24 在档正本（回归锚 c=-8..-15） ----------
ARCHIVE_STATE16 = {0:3, -1:5, -2:5, -3:6, -4:7, -5:7, -6:7, -7:8,
                   -8:7, -9:7, -10:9, -11:10, -12:9, -13:9, -14:9, -15:8}

def load_r24_newlayers():
    p = "H:/理论存档/01-数学/02-实验与数据/results/ec_layer_deriver_newlayers-v1.0-20260921.json"
    with open(p, encoding="utf-8") as f:
        raw = json.load(f)
    out = {}
    for key, val in raw.items():
        c = int(key.replace("c(", "").replace(")", ""))
        out[c] = [((tuple(int(x) for x in item["src"].strip("()").split(",")), item["tail"]), item["count_k12"]) for item in val["layers"]]
    return out

def point_type(src, tail):
    """点型表：src 语义态 (sigma,mu) 与尾串逐位读后的末端 (sigma_Y,mu_Y)"""
    d, sg, mu = src
    for chb in tail:
        rho = int(chb)
        d, sg, mu = step((d, sg, mu), rho)
    return {"src_sigma": int(src[1]), "src_mu": int(src[2]),
            "end_sigma": int(sg), "end_mu": int(mu), "end_D": int(d)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--c0", type=int, required=True)
    ap.add_argument("--c1", type=int, required=True)
    ap.add_argument("--tag", type=str, required=True)
    args = ap.parse_args()

    res = {"A0":{}, "entries":{}, "inherit":{}, "P_pred":{}, "notes":{}}
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

    T, Qs, Cs, Bs, E1, E2v = base_sets()
    assert len(E1)==6142 and len(E2v)==8188, "在档锚失"
    res["notes"]["archive_anchor"] = {"E1":len(E1), "E2":len(E2v)}
    r24nl = load_r24_newlayers()

    for c in range(args.c0, args.c1-1, -1):
        L("== c=%d ==" % c)
        keep_states, tr, q0, accept = build_dfa(c)
        n_min, lab, classes = moore_minimize_detail(tr, set(accept), keep_states)
        R, S = lang_iter(c)
        acc_val = set()
        for st in R:
            if st[0]==c: acc_val |= S[st]
        eq_D = bool(acc_val == {int(y) for y in np.where(Darr==c)[0]})
        lay_m = machine_layers_atomic(c, R, S)
        Nv = [int(np.count_nonzero(Darr[:4**k]==c)) for k in range(1,13)]
        cf = fit_closed_form(Nv)
        nc = nerode_signature_classcount(c, Darr)
        nc_lev = 6
        if int(nc) != int(n_min):
            nc = nerode_signature_classcount(c, Darr, pf_bits=7, sf_bits=7, use_md5=True)
            nc_lev = 7
        lay_detail = []
        for (src, tail), vs in lay_m:
            lay_detail.append({"src": str(src), "tail": tail, "count_k12": len(vs),
                               "point": point_type(src, tail)})
        entry = {
            "rev_states": len(R), "reachable": len(keep_states), "min_dfa": int(n_min),
            "lang_eq_D": eq_D,
            "machine_layers": len(lay_m),
            "layers_detail": lay_detail,
            "count_k12": Nv,
            "closed_form": (None if cf is None else cf_to_json(cf[1])),
            "nerode_level": nc_lev,
            "nerode": int(nc),
            "moore_eq_nerode": bool(int(n_min)==int(nc)),
            "moore_classes": classes,
        }
        # ---- 回归锚对照 ----
        if -15 <= c <= -8:
            arch = r24nl[c]
            m_lay = [((tuple(int(x) for x in d["src"].strip("()").split(",")), d["tail"]), d["count_k12"]) for d in lay_detail]
            entry["layers_match_r24"] = bool(sorted(m_lay) == sorted(arch))
        if c >= -7:
            lay_a = archive_layers(c, T, Qs, Cs, Bs, E1, E2v)
            pe = bool(partition_equivalent(lay_a, [s for _,s in lay_m]))
            entry["partition_eq_archive"] = pe
            entry["count_eq_archive_cf"] = bool(all(Nv[k-1]==cf_known(c,k) for k in range(1,13)))
        entry["state_match_archive"] = bool(int(n_min) == ARCHIVE_STATE16[c]) if c in ARCHIVE_STATE16 else None
        res["entries"]["c(%d)" % c] = entry
        L(json.dumps({k:v for k,v in entry.items() if k not in ("layers_detail","moore_classes")}, ensure_ascii=False))

    # ---- D3 继承三分律（c1 侧为 3|c 档时核） ----
    for c in range(args.c0, args.c1-1, -1):
        if c % 3 != 0: continue
        cp = c // 3
        Ec = {int(y) for y in np.where(Darr==c)[0]}
        Ecp = {int(y) for y in np.where(Darr==cp)[0]}
        four = {4*y for y in Ecp if 4*y < N4}
        inc = bool(four <= Ec)
        ent = res["entries"]["c(%d)" % c]
        tail0 = set(); tailX = set()
        pure = None
        for d in ent["layers_detail"]:
            vs_key = d["count_k12"]
            if d["tail"][-1] == "0":
                tail0.add(d["tail"])
            else:
                tailX.add(d["tail"])
        pure = (len(ent["layers_detail"]) > 0) and all(d["tail"][-1]=="0" for d in ent["layers_detail"])
        # 尾 0 块之并 = 4E_{c/3}（值集恒等）
        R, S = lang_iter(c)
        lay_m = machine_layers_atomic(c, R, S)
        zero_union = set()
        nonzero_union = set()
        for (src2, tail), vs in lay_m:
            if tail[-1] == "0": zero_union |= vs
            else: nonzero_union |= vs
        zero_eq = bool(zero_union == four)
        # X_c 词形核：尾末位 ∈ {1,3}
        tailset_ok = all(d["tail"][-1] in ("1","3") for d in ent["layers_detail"] if d["tail"][-1] != "0")
        r_c = int(ent["min_dfa"])
        r_cp = ARCHIVE_STATE16.get(cp)
        if r_cp is None and ("c(%d)" % cp) in res["entries"]:
            r_cp = int(res["entries"]["c(%d)" % cp]["min_dfa"])
        entry3 = {
            "4E_subset": inc, "zero_tail_union_eq_4Ecp": zero_eq,
            "x_tailset_ok": bool(tailset_ok), "pure_inherit": bool(pure and zero_eq and inc),
            "R_c": r_c, "R_c3": r_cp,
            "R_eq_R3p1": (None if r_cp is None else bool(r_c == r_cp + 1)),
            "R_ge_R3p1": (None if r_cp is None else bool(r_c >= r_cp + 1)),
        }
        res["inherit"]["c(%d)" % c] = entry3
        L("D3 c=%d: %s" % (c, json.dumps(entry3)))

    # ---- D4② P 系预测记账（仅 new 片记谱统计） ----
    if args.tag == "new":
        Rs = {c: int(res["entries"]["c(%d)"%c]["min_dfa"]) for c in range(args.c0, args.c1-1, -1)}
        res["P_pred"] = {
            "P1_max_ge_11": {"pred": ">=11", "actual": max(Rs.values()), "hit": bool(max(Rs.values()) >= 11)},
            "P2_min_ge_7": {"pred": ">=7", "actual": min(Rs.values()), "hit": bool(min(Rs.values()) >= 7)},
            "P3_inherit": {},
        }
        for c, src in [(-18,-6), (-21,-7), (-24,-8), (-27,-9), (-30,-10)]:
            if ("c(%d)" % c) in res["entries"]:
                pred = ARCHIVE_STATE16[src] + 1
                act = int(res["entries"]["c(%d)" % c]["min_dfa"])
                res["P_pred"]["P3_inherit"]["c(%d)" % c] = {
                    "pred": pred, "actual": act, "hit": bool(pred == act),
                    "pure_inherit": res["inherit"].get("c(%d)" % c, {}).get("pure_inherit")}

    outp = "H:/理论存档/01-数学/02-实验与数据/results/ec_full_spectrum_%s-v1.0-20260921.json" % args.tag
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    L("saved %s" % outp)

if __name__ == "__main__":
    main()
