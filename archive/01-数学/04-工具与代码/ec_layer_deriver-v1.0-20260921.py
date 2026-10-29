# -*- coding: utf-8 -*-
# E_c 层清单自动推导器（R24 主格一·判据书 A 系实算）
# 判据书：代数册·E_c层清单自动推导器预注册判据书-v1.0-20260921.md（冻结在先）
# 口径：整型零容差；4^12 定长域；回归 c=0..-7 先行；新档 c=-8..-15
# 注：在档对照正本=层清单算术式（R22 修正轨）；R22 报告正文 E_-4/E_-7 正则式
#     修正轨后未同步重写的两处转写滑误（{21,22}->{22,23}/{13,20}->{03,12}）本轮如实记录。
import json
from fractions import Fraction
import numpy as np

K = 12
N4 = 4 ** K            # 16777216
G = [[0,0,0],[0,1,-1],[-1,2,-1],[0,2,-2]]   # g[rho][m]（R18 Z-B 冻结表）
SIGN = [1,-1,-1,1]     # (-1)^{s2(rho)}
KMAX = 15              # 最深 c

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

# ---------- 语义态自动机（器之心） ----------
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

def moore_minimize(tr, accept_set):
    """Moore 最小化（含显式 dead 态——缺 dead 是首跑判负点之一）"""
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
            return len(sig), lab[:n]
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
    """语言方程组迭代最小不动点（含自动层来源）"""
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
            base = rho  # v*4+rho
            tgt = S[t]
            na = {v*4+base for v in S[s] if v*4+base < N4 and v*4+base not in tgt}
            if na: add[t] = na
        for s,na in add.items():
            S[s] |= na; changed = True
    return R, S

def machine_layers(c, R, S):
    """器层值集列表：一级逆向层 (源语义态, rho)"""
    acc = {s for s in R if s[0]==c}
    lay = []
    for p in sorted(R):
        for rho in range(4):
            if step(p,rho) in acc:
                vs = {v*4+rho for v in S[p] if v*4+rho < N4}
                if vs: lay.append(((p,rho), vs))
    return lay


ATOMS = {(0,1,0),(0,-1,1),(-1,-1,2),(-1,1,2)}   # T,Q,C,B

def machine_layers_atomic(c, R, S):
    """器原子层清单：逆向 DFS 展开到原子态(T/Q/C/B)或环；tail=读串(低位在右)。
    器原子层两两不交（每值唯一 (语义态,尾串) 路径）=语言的结构分拆。"""
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
    """在档层值集列表（层清单算术式正本；全部过滤域界 <4^K）"""
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
    """A=在档层列表，B=器层列表：在档每条=器条目之并（整块覆盖）+ 总并相等。
    口径注：c=0 在档层 T/T+1 为覆盖式（T∩(T+1)非空），双向分划不适用，
    统一用单向 refine(在档,器)——在档条目的机器重推导口径。"""
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


def cf_to_json(r):
    if r["kind"] == "a2k+b":
        params = [fmt_fr(r["A"]), fmt_fr(r["B"])]
    else:
        params = [fmt_fr(r["p"]), fmt_fr(r["q"]), fmt_fr(r["r"])]
    return {"kind": r["kind"], "k0": r["k0"], "head": r.get("head", {}), "params": params}

def fitseg(Nv, i0):
    """尾段拟合：从 k=i0+1 起（索引 i0），a2k+b 或 rec3；返回 dict 或 None"""
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
    """分段闭式：前段逐点表列+尾段闭式；全档 k=1..12 逐点零容差即成立"""
    r = fitseg(Nv, 0)
    if r is not None:
        r["head"] = {}
        return ("seg1", r["kind"], r.get("k0",1)) + tuple(v for v in [r.get("A",r.get("p")), r.get("B",r.get("q")), r.get("r",0)] if v is not None) if False else ("seg", r)
    for k0 in (2,3,4,5):
        r = fitseg(Nv, k0-1)
        if r is not None:
            r["head"] = {k: Nv[k-1] for k in range(1, k0)}
            return ("seg", r)
    return None

def fmt_fr(x):
    x = Fraction(x)
    return str(x.numerator) if x.denominator==1 else "%d/%d" % (x.numerator, x.denominator)

def cf_known(c, k):
    """在档闭式谱（k>=1；E_-3 与 E_-4/E_-7 的 k=1 特例=0 由直接表核对）"""
    if c == 0:  return 2**(k+1)-1
    if c == -1: return 3*2**(k-1)-2
    if c == -2: return 2**(k+1)-4
    if c == -3: return 0 if k == 1 else 3*2**(k-2)-2
    if c == -4: return 0 if k == 1 else 2**k-4
    if c == -5: return 0 if k == 1 else 2**(k-1)-2
    if c == -6: return 0 if k == 1 else 2**(k+1)-8
    if c == -7: return 0 if k == 1 else 2**k-4
    return None

def main():
    res = {"A0":{}, "regression":{}, "new":{}, "notes":{}}
    log = []
    def L(m):
        log.append(m); print(m, flush=True)

    L("== A0 递推核 ==")
    Darr = build_D_table()
    bad = 0
    s = [0,0,0]
    for Y in range(1,2000):
        n = Y-1
        s[n % 3] += tau_n(n)
        if s[1]-s[2] != int(Darr[Y]): bad += 1
    basis_ok = bool(int(Darr[1])==0 and int(Darr[3])==0 and int(Darr[2])==-1 and int(Darr[0])==0)
    res["A0"] = {"mismatch_2000": bad, "basis_ok": basis_ok}
    L("A0 mismatch=%d basis_ok=%s" % (bad, basis_ok))

    T, Qs, Cs, Bs, E1, E2v = base_sets()
    L("counts T=%d Q=%d C=%d B=%d E1=%d E2=%d" % (len(T),len(Qs),len(Cs),len(Bs),len(E1),len(E2v)))
    assert len(E1)==6142 and len(E2v)==8188, "在档锚失"
    res["notes"]["archive_anchor"] = {"E1":len(E1), "E2":len(E2v)}

    known_state = {0:3, -1:5, -2:5, -3:6, -4:7, -5:7}
    for c in range(0, -(KMAX+1), -1):
        L("== c=%d ==" % c)
        keep_states, tr, q0, accept = build_dfa(c)
        n_min, lab = moore_minimize(tr, set(accept))
        R, S = lang_iter(c)
        acc_val = set()
        for st in R:
            if st[0]==c: acc_val |= S[st]
        eq_D = bool(acc_val == {int(y) for y in np.where(Darr==c)[0]})
        lay_m = machine_layers_atomic(c, R, S)
        lay_a = archive_layers(c, T, Qs, Cs, Bs, E1, E2v)
        pe = bool(partition_equivalent(lay_a, [s for _,s in lay_m])) if lay_a is not None else None
        Nv = [int(np.count_nonzero(Darr[:4**k]==c)) for k in range(1,13)]
        cf = fit_closed_form(Nv)
        nc = nerode_signature_classcount(c, Darr)
        nc_lev = 6
        if int(nc) != int(n_min):
            nc = nerode_signature_classcount(c, Darr, pf_bits=7, sf_bits=7, use_md5=True)
            nc_lev = 7
        entry = {
            "rev_states": len(R), "reachable": len(keep_states), "min_dfa": int(n_min),
            "lang_eq_D": eq_D,
            "partition_eq_archive": pe,
            "machine_layers": len(lay_m), "archive_layers": (len(lay_a) if lay_a else 0),
            "count_k12": Nv,
            "closed_form": (None if cf is None else cf_to_json(cf[1])),
            "nerode_level": nc_lev,
            "nerode": int(nc),
            "moore_eq_nerode": bool(int(n_min)==int(nc)),
        }
        if c in known_state:
            entry["known_min_dfa"] = known_state[c]
            entry["regress_dfa_ok"] = bool(n_min == known_state[c] == nc)
        if c >= -7:
            entry["count_eq_archive_cf"] = bool(all(Nv[k-1]==cf_known(c,k) for k in range(1,13)))
        (res["regression"] if c >= -7 else res["new"])["c(%d)" % c] = entry
        L(json.dumps(entry, ensure_ascii=False))

    reg = res["regression"]
    a_ok = bool(
        res["A0"]["mismatch_2000"]==0 and res["A0"]["basis_ok"]
        and all(reg["c(%d)"%c]["lang_eq_D"] and reg["c(%d)"%c]["partition_eq_archive"] and reg["c(%d)"%c]["count_eq_archive_cf"] for c in range(0,-8,-1))
        and all(reg["c(%d)"%c]["regress_dfa_ok"] for c in range(0,-6,-1))
        and all(reg["c(%d)"%c]["closed_form"] is not None for c in range(0,-8,-1))
    )
    new_ok = bool(all(res["new"]["c(%d)"%c]["lang_eq_D"] and res["new"]["c(%d)"%c]["closed_form"] is not None
                      and res["new"]["c(%d)"%c]["moore_eq_nerode"] for c in range(-8,-(KMAX+1),-1)))
    res["verdict"] = {"A0_A4_deriver_established": a_ok, "A5_new_spectrum": new_ok}
    L("VERDICT %s" % json.dumps(res["verdict"]))
    res["log"] = log
    with open("H:/理论存档/01-数学/02-实验与数据/results/ec_layer_deriver_result-v1.0-20260921.json","w",encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    L("saved.")

if __name__ == "__main__":
    main()
