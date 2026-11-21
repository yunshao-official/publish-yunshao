# -*- coding: utf-8 -*-
"""R23 主格一·双参数族频率矩阵与恒等群二分解析重建 判据 M0-M5 实算（v1.0 正式版）
判据书：代数册·双参数族频率矩阵与恒等群二分解析重建预注册判据书-v1.0-20260921.md（冻结 05:49:45 在先）
口径：整数精确算术（Ĥ 行等价/秩/零空间）+ Q(i,√2) 精确 S_c 对照双通道；k=1..13；判负照记。
路径一律正斜杠（防转义吃字节）。"""
import json, time
from fractions import Fraction as Fr

T0 = time.time()
LOG = []
def log(msg):
    LOG.append(msg)
    print(msg, flush=True)

# ---------- 整数 Ĥ ----------
def coeffs_1pt2t2tsq(N):
    """(1+t+t^2)^N 的整系数（长度 2N+1）"""
    c = [1]
    for _ in range(N):
        d = [0]*(len(c)+2)
        for i, v in enumerate(c):
            d[i] += v; d[i+1] += v; d[i+2] += v
        c = d
    return c

def build_H(k):
    p = (k+1)//2; q = k//2
    f = coeffs_1pt2t2tsq(p); g = coeffs_1pt2t2tsq(q)
    H = [[0]*(2*k+1) for _ in range(8)]
    for n in range(0, 2*k+1):
        lo = max(0, n-2*q); hi = min(n, 2*p)
        for a in range(lo, hi+1):
            b = n-a
            ell = (a+3*b) % 8
            H[ell][n] += f[a]*g[b]
    return H, p, q, f, g

def row_partition(H):
    """行等价划分（整型精确）：返回划分列表与恒等对集合"""
    n = len(H)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i in range(n):
        for j in range(i+1, n):
            if H[i] == H[j]:
                ri, rj = find(i), find(j)
                if ri != rj: parent[rj] = ri
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    parts = sorted([sorted(g) for g in groups.values()])
    pairs = set()
    for g in parts:
        for i in range(len(g)):
            for j in range(i+1, len(g)):
                pairs.add((g[i], g[j]))
    return parts, pairs

# ---------- Q(i,√2) 精确算术：基 [1, s, i, si] ----------
def q4(i): return (Fr(i), Fr(0), Fr(0), Fr(0))
Q4_ZERO = (Fr(0), Fr(0), Fr(0), Fr(0))
def q4_add(u, v): return tuple(u[i]+v[i] for i in range(4))
def q4_scale(u, c): return tuple(u[i]*c for i in range(4))
# 乘法表：(i,j) -> [(k, 系数)]
MULT = {
 (0,0):[(0,Fr(1))], (0,1):[(1,Fr(1))], (0,2):[(2,Fr(1))], (0,3):[(3,Fr(1))],
 (1,1):[(0,Fr(2))], (1,2):[(3,Fr(1))], (1,3):[(2,Fr(2))],
 (2,2):[(0,Fr(-1))], (2,3):[(1,Fr(-1))], (3,3):[(0,Fr(-2))],
}
def q4_mul(u, v):
    out = [Fr(0)]*4
    for i in range(4):
        if u[i] == 0: continue
        for j in range(4):
            if v[j] == 0: continue
            key = (i, j) if (i, j) in MULT else (j, i)
            for k, c in MULT[key]:
                out[k] += u[i]*v[j]*c
    return tuple(out)

def zeta_pow(j):
    """ζ^j (mod 8) 的 Q4 表示；ζ = s/2 + si/2"""
    j %= 8
    table = {
      0: (Fr(1),Fr(0),Fr(0),Fr(0)),
      1: (Fr(0),Fr(1,2),Fr(0),Fr(1,2)),
      2: (Fr(0),Fr(0),Fr(1),Fr(0)),
      3: (Fr(0),Fr(-1,2),Fr(0),Fr(1,2)),
      4: (Fr(-1),Fr(0),Fr(0),Fr(0)),
      5: (Fr(0),Fr(-1,2),Fr(0),Fr(-1,2)),
      6: (Fr(0),Fr(0),Fr(-1),Fr(0)),
      7: (Fr(0),Fr(1,2),Fr(0),Fr(-1,2)),
    }
    return table[j]

def poly_mul_q4(A, B):
    out = [Q4_ZERO]*(len(A)+len(B)-1)
    for i, a in enumerate(A):
        if a == Q4_ZERO: continue
        for j, b in enumerate(B):
            if b == Q4_ZERO: continue
            out[i+j] = q4_add(out[i+j], q4_mul(a, b))
    return out

def poly_pow_q4(base, e):
    r = [q4(1)]
    b = list(base)
    while e:
        if e & 1: r = poly_mul_q4(r, b)
        b = poly_mul_q4(b, b); e >>= 1
    return r

def build_S_exact(k):
    """精确 S_c 系数（Q4），c=0..7"""
    p = (k+1)//2; q = k//2
    S = [[Q4_ZERO]*(2*k+1) for _ in range(8)]
    for m in range(8):
        Am = [q4(1), zeta_pow(-m), zeta_pow(-2*m)]
        A3 = [q4(1), zeta_pow(-3*m), zeta_pow(-6*m)]
        Pm = poly_mul_q4(poly_pow_q4(Am, p), poly_pow_q4(A3, q))
        for c in range(8):
            z = zeta_pow(m*c)
            for n in range(len(Pm)):
                S[c][n] = q4_add(S[c][n], q4_scale(q4_mul(z, Pm[n]), Fr(1, 8)))
    return S

def exact_identity_pairs(S):
    pairs = set()
    deg = len(S[0])
    for c in range(8):
        for cp in range(c+1, 8):
            ok = all(S[c][n] == S[cp][n] for n in range(deg))
            if ok: pairs.add((c, cp))
    return pairs

def exact_partition(pairs):
    parent = list(range(8))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for (a, b) in pairs:
        ra, rb = find(a), find(b)
        if ra != rb: parent[rb] = ra
    groups = {}
    for i in range(8):
        groups.setdefault(find(i), []).append(i)
    return sorted([sorted(g) for g in groups.values()])

# ---------- M4 秩与零空间（分数消元） ----------
def rank_cols(M):
    """M: list of rows (list of Fr)；返回列秩"""
    if not M: return 0
    rows = [list(r) for r in M]
    nr, nc = len(rows), len(rows[0])
    rank = 0; piv_cols = []
    for c in range(nc):
        piv = None
        for r in range(rank, nr):
            if rows[r][c] != 0: piv = r; break
        if piv is None: continue
        rows[rank], rows[piv] = rows[piv], rows[rank]
        pv = rows[rank][c]
        rows[rank] = [x/pv for x in rows[rank]]
        for r in range(nr):
            if r != rank and rows[r][c] != 0:
                fac = rows[r][c]
                rows[r] = [a - fac*b for a, b in zip(rows[r], rows[rank])]
        piv_cols.append(c); rank += 1
        if rank == nr: break
    return rank

def nullspace_transpose(H):
    """H^T 的零空间（=行关系向量 alpha：sum alpha_c row_c = 0）"""
    nc = len(H[0]); n = len(H)
    M = [[Fr(H[n_][c]) for n_ in range(n)] for c in range(nc)]  # nc x n
    rows = [list(r) for r in M]
    nr, ncol = len(rows), n
    rank = 0; piv = []
    for c in range(ncol):
        pr = None
        for r in range(rank, nr):
            if rows[r][c] != 0: pr = r; break
        if pr is None: continue
        rows[rank], rows[pr] = rows[pr], rows[rank]
        pv = rows[rank][c]
        rows[rank] = [x/pv for x in rows[rank]]
        for r in range(nr):
            if r != rank and rows[r][c] != 0:
                fac = rows[r][c]
                rows[r] = [a - fac*b for a, b in zip(rows[r], rows[rank])]
        piv.append(c); rank += 1
        if rank == nr: break
    free = [c for c in range(ncol) if c not in piv]
    basis = []
    for fc in free:
        v = [Fr(0)]*ncol
        v[fc] = Fr(1)
        for r_i, pc in enumerate(piv):
            v[pc] = -rows[r_i][fc]
        basis.append(v)
    return rank, basis

# ---------- M0 修正表示自检（复浮点） ----------
import cmath
Z8 = cmath.exp(2j*cmath.pi/8)
def poly_mul_c(A, B):
    out = [0j]*(len(A)+len(B)-1)
    for i, a in enumerate(A):
        for j, b in enumerate(B):
            out[i+j] += a*b
    return out
def poly_pow_c(base, e):
    r = [1.0+0j]
    b = base
    while e:
        if e & 1: r = poly_mul_c(r, b)
        b = poly_mul_c(b, b); e >>= 1
    return r

def m0_corrected_repr(ks=(5, 6)):
    worst = 0.0
    for k in ks:
        p = (k+1)//2; q = k//2
        for m in range(8):
            # 直接积
            Am = [1.0, Z8**(-m), Z8**(-2*m)]
            A3 = [1.0, Z8**(-3*m), Z8**(-6*m)]
            Pm = poly_mul_c(poly_pow_c(Am, p), poly_pow_c(A3, q))
            # 修正表示：G_m(y)=(1+y+y^2)^p (1+u y+u^2 y^2)^q, y=Z^{-m}x
            u = Z8**(-2*m)
            Gm = poly_mul_c(poly_pow_c([1.0, 1.0, 1.0], p),
                            poly_pow_c([1.0, u, u*u], q))
            # y = Z^{-m} x 代换：coeff_n = G[n] * Z^{-m n}
            sub = [Gm[n]*(Z8**(-m))**n for n in range(len(Gm))]
            for n in range(max(len(Pm), len(sub))):
                a = Pm[n] if n < len(Pm) else 0j
                b = sub[n] if n < len(sub) else 0j
                worst = max(worst, abs(a-b))
    return worst

# ================= 主流程 =================
res = {"meta": {"script": "identity_frequency_matrix-v1.0-20260921.py",
                 "frozen_at": "2026-09-21 05:49:45", "start": time.strftime("%H:%M:%S")}}

# M0
w = m0_corrected_repr()
res["M0"] = {"worst_diff": w, "pass": bool(w <= 1e-12)}
log(f"M0 修正表示自检 worst={w:.3e} pass={w <= 1e-12}")

# M1/M3/M4 逐档
res["M1"] = {}; res["M2"] = {}; res["M3"] = {}; res["M4"] = {}
R22_grid = {  # 在档对照（R22 O1/O2/O4 记录）
    "odd": "恒等对=0 (k=3..11)",
    "even_k4_10": [(1, 3), (2, 6), (5, 7)],
    "k2": [(1, 3), (2, 4), (2, 6), (4, 6), (5, 7)],
}
for k in range(1, 14):
    H, p, q, f, g = build_H(k)
    parts, hpairs = row_partition(H)
    S = build_S_exact(k)
    epairs = exact_identity_pairs(S)
    eparts = exact_partition(epairs)
    agree = (parts == eparts)
    rankT, basis = nullspace_transpose(H)
    rankH = rank_cols([[Fr(x) for x in r] for r in H])
    entry = {"p": p, "q": q, "H_partition": [list(x) for x in parts],
             "exact_partition": [list(x) for x in eparts],
             "channels_agree": agree, "rank_H": rankH,
             "nullspace_dim_HT": len(basis)}
    if basis:
        entry["nullspace_basis"] = [[str(x) for x in v] for v in basis]
    res["M1"][k] = entry
    log(f"k={k} p={p} q={q} H划分={parts} 双通道一致={agree} rank(Ĥ)={rankH} "
        f"dim null(Ĥ^T)={len(basis)} [{time.time()-T0:.1f}s]")
    # M2 奇档分离列
    if k % 2 == 1 and k >= 3:
        q_ = q
        checks = []
        def chk(name, cond):
            checks.append((name, bool(cond)))
        chk("H00=1", H[0][0] == 1)
        chk("Hc0=0 c!=0", all(H[c][0] == 0 for c in range(1, 8)))
        chk("H11=q+1", H[1][1] == q_+1)
        chk("H31=q", H[3][1] == q_)
        chk("H51=H71=0", H[5][1] == 0 and H[7][1] == 0)
        chk("R-E.1 H33-H53=-q(2q+1)(q+1)/6",
            H[3][3]-H[5][3] == -q_*(2*q_+1)*(q_+1)/6)
        chk("H(1,4q+1)=q+1", H[1][4*q_+1] == q_+1)
        chk("H(7,4q+1)=q", H[7][4*q_+1] == q_)
        chk("H(3,4q+1)=H(5,4q+1)=0", H[3][4*q_+1] == 0 and H[5][4*q_+1] == 0)
        chk("H(0,4q)=q+1", H[0][4*q_] == q_+1)
        chk("H(0,4q)=(q+1)(q+2)/2 [修正值对照]",
            H[0][4*q_] == (q_+1)*(q_+2)//2)
        chk("H(4,4q)=q(q+1)/2", H[4][4*q_] == q_*(q_+1)//2)
        chk("H(6,4q)=q(q+1)", H[6][4*q_] == q_*(q_+1))
        chk("H(2,4q+2)=1", H[2][4*q_+2] == 1)
        chk("H(4,4q+2)=H(6,4q+2)=0", H[4][4*q_+2] == 0 and H[6][4*q_+2] == 0)
        # 12 对同奇偶行的分离见证
        witness = []
        for a in range(8):
            for b in range(a+1, 8):
                if a % 2 != b % 2:
                    witness.append(((a, b), "parity", None)); continue
                sep = None
                for n in range(2*k+1):
                    if H[a][n] != H[b][n]:
                        sep = (n, H[a][n], H[b][n]); break
                witness.append(((a, b), "col", sep))
        all_sep = all((w2[1] == "parity") or (w2[2] is not None) for w2 in witness)
        failed = [name for name, c in checks if not c]
        res["M2"][k] = {"checks": checks, "all_pass": all(c for _, c in checks),
                        "failed": failed,
                        "pairs_all_separated": all_sep,
                         "witness": [[list(pair), typ,
                                      (sep[0] if sep else None,
                                       sep[1] if sep else None,
                                       sep[2] if sep else None) if sep else None]
                                     for pair, typ, sep in witness]}
        log(f"  M2 k={k}: checks={'ALL PASS' if all(c for _, c in checks) else 'FAIL ' + str(failed)} "
            f"pairs_separated={all_sep}")
    # M3 偶档
    if k % 2 == 0 and k >= 4:
        merges = all(H[c] == H[(3*c) % 8] for c in (1, 2, 5))
        # 五类两两不同
        reps = {0: H[0], 4: H[4], 1: H[1], 2: H[2], 5: H[5]}
        keys = list(reps)
        distinct = all(reps[keys[i]] != reps[keys[j]]
                       for i in range(5) for j in range(i+1, 5))
        # 分离列闭式
        p_ = k//2
        col_sep = {
            "n0": (H[0][0], H[4][0]),
            "n2k": (H[0][2*k], H[2][2*k], H[6][2*k]),
            "n2k-2": (H[4][2*k-2], H[2][2*k-2]),
            "n1": (H[1][1], H[5][1]),
        }
        res["M3"][k] = {"row_merge_sigma": merges, "five_classes_distinct": distinct,
                        "sep_cols": {kk: [str(x) for x in vv] for kk, vv in col_sep.items()}}
        log(f"  M3 k={k}: sigma_merge={merges} five_distinct={distinct}")
    if k == 2:
        pred = sorted([[0], [1, 3], [2, 4, 6], [5, 7]])
        res["M3"]["k2_partition"] = {"actual": [list(x) for x in parts],
                                      "predicted": pred,
                                      "match": parts == pred}
        log(f"  k=2 partition={parts} 预测吻合={parts == pred}")
    if k == 1:
        res["M3"]["k1_partition"] = [list(x) for x in parts]
        log(f"  k=1 partition={parts} (空类效应记录)")
    # k=12 精确裁决 (2,6)
    if k == 12:
        res["M1"]["k12_exact_26_identity"] = bool((2, 6) in epairs)
        log(f"  k=12 (2,6) 精确裁决: 恒等={((2, 6) in epairs)}")

# M4 预测对照
pred_rank = {1: 3, 2: 4, 3: 7, 5: 8, 7: 8, 9: 8, 11: 8, 13: 8, 4: 5, 6: 5, 8: 5, 10: 5, 12: 5}
res["M4"] = {"predicted": pred_rank,
             "actual": {k: res["M1"][k]["rank_H"] for k in range(1, 14)},
             "all_match": all(res["M1"][k]["rank_H"] == pred_rank[k] for k in range(1, 14))}
# k=3 关系向量
k3 = res["M1"][3]
if k3["nullspace_basis"]:
    v = k3["nullspace_basis"][0]
    v_num = [float(Fr(x)) for x in v]
    nz = [(i, xv) for i, xv in enumerate(v_num) if xv != 0.0]
    m = min(abs(xv) for _, xv in nz)
    scaled = [xv/m for xv in v_num]
    res["M4"]["k3_relation_normalized"] = scaled
    res["M4"]["k3_relation_pred"] = [0, 1, 0, -2, 0, 2, 0, -2]
    res["M4"]["k3_relation_match"] = all(abs(a-b) < 1e-9 for a, b in zip(scaled, [0, 1, 0, -2, 0, 2, 0, -2]))
    log(f"k=3 关系向量（归一）={scaled} 预测吻合={res['M4']['k3_relation_match']}")

# M5 总裁决（冻结判读规则：主项=M0/M1/M2 分离结构/M3①②/M4 rank 主序列；
# 附记预测=M2 闭式值逐条+M4 k=3 关系向量+M3③——判负照记不阻塞）
m2_struct = all(res["M2"][k]["pairs_all_separated"] for k in [3, 5, 7, 9, 11, 13])
m2_known_fail = all(res["M2"][k]["failed"] == ["H(0,4q)=q+1"]
                    for k in [3, 5, 7, 9, 11, 13])
m5 = (res["M0"]["pass"]
      and all(res["M1"][k]["channels_agree"] for k in range(2, 13))
      and m2_struct
      and all(res["M3"][k]["row_merge_sigma"] and res["M3"][k]["five_classes_distinct"]
              for k in [4, 6, 8, 10, 12])
      and res["M4"]["all_match"])
res["M5_total"] = {"structure_pass": bool(m5),
                   "M2_struct_pairs_separated": m2_struct,
                   "M2_判负照记项": "H(0,4q)=q+1（冻结文本闭式值笔误；仅此项，六档一致）",
                   "M2_修正值全过": bool(all(
                       ("H(0,4q)=(q+1)(q+2)/2 [修正值对照]", True) in res["M2"][k]["checks"]
                       for k in [3, 5, 7, 9, 11, 13])),
                   "M4_附记判负照记": "k=3 关系向量预测 (0,1,0,-2,0,2,0,-2) 判负；机器 nullspace 一维基（归一）见 M4",
                   "strict_all_subitems": bool(
                       m5 and m2_known_fail is False and False)}  # 严格口径必 False（两处滑误判负照记在案）
log(f"M5 总裁决(结构主项): {'PASS' if m5 else 'FAIL'} [修正轨两处判负照记在案] [{time.time()-T0:.1f}s]")

outp = "H:/理论存档/01-数学/02-实验与数据/results/identity_frequency_matrix_result-v1.0-20260921.json"
with open(outp, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1, default=str)
log(f"结果落盘 {outp}")
