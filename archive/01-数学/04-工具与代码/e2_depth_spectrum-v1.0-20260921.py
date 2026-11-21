# -*- coding: utf-8 -*-
"""R23 主格二·E₋₂深处·承接谱与层族计数 判据 P0-P6 实算（v1.0 正式版）
判据书：代数册·E₋₂深处·承接谱与层族计数预注册判据书-v1.0-20260921.md（冻结 05:51:34 在先）
口径：4^12 D 表；分支串级生成；承接谱（长度 11→12 串级）；5×5 最短见证矩阵+同构判定；判负照记。
路径一律正斜杠（防转义吃字节）。"""
import json, time
import numpy as np

T0 = time.time()
LOG = []
def log(msg):
    LOG.append(msg)
    print(msg, flush=True)

N12 = 1 << 24
g_tab = np.array([[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]], dtype=np.int64)

# ---------- D 表（R22 在档构建式复用） ----------
D = np.zeros(N12, dtype=np.int32)
tau = np.ones(N12, dtype=np.int8)
m3 = np.zeros(N12, dtype=np.int8)
D[:4] = [0, 0, -1, 0]
tau[:4] = [1, -1, -1, 1]
m3[:4] = [0, 1, 2, 0]
size = 4
while size < N12:
    for rho in range(4):
        tsign = 1 if bin(rho).count('1') % 2 == 0 else -1
        idx = np.arange(size, dtype=np.int64) * 4 + rho
        D[idx] = 3 * D[:size].astype(np.int64) + tau[:size].astype(np.int64) * g_tab[rho][m3[:size]]
        tau[idx] = tsign * tau[:size]
        m3[idx] = (m3[:size].astype(np.int16) + rho) % 3
    size *= 4
log(f'D table built 4^12, {time.time()-T0:.1f}s')

E1 = set(np.nonzero(D == -1)[0].tolist())
E2 = set(np.nonzero(D == -2)[0].tolist())

# ---------- 层族生成（R22 在档口径复用） ----------
def gen_T(kmax):
    out = set()
    for L in range(0, kmax + 1):
        for mask in range(1 << L):
            v = 0; p = 1; mm = mask
            for j in range(L):
                if mm & 1: v += 3 * p
                mm >>= 1; p *= 4
            out.add(v)
    return out
T_set = gen_T(12)
Q_set = {t + 1 for t in T_set if t + 1 < N12}
C_set = set()
for a in T_set:
    j = 0
    while True:
        v = a * (1 << (2 * (j + 1))) + 2 * (1 << (2 * j)) + ((1 << (2 * j)) - 1)
        if v >= N12: break
        C_set.add(v); j += 1
B_set = {4 * q + 1 for q in Q_set if 4 * q + 1 < N12}
E1_gen = C_set | B_set
L2_layers = {r: {4 * c + r for c in C_set if 4 * c + r < N12} for r in (1, 2)}
Q_layers = {r: {4 * q + r for q in Q_set if 4 * q + r < N12} for r in (2, 3)}
E2_gen = L2_layers[1] | L2_layers[2] | Q_layers[2] | Q_layers[3]
log(f'gen: C={len(C_set)} B={len(B_set)} E1={len(E1_gen)} E2={len(E2_gen)} [{time.time()-T0:.1f}s]')

res = {"meta": {"script": "e2_depth_spectrum-v1.0-20260921.py",
                 "frozen_at": "2026-09-21 05:51:34", "start": time.strftime("%H:%M:%S")}}

# ---------- P0 在档复现 ----------
p0 = {
    "E1_count": len(E1), "E2_count": len(E2),
    "E1_gen_eq": E1_gen == E1, "E2_gen_eq": E2_gen == E2,
    "E1_cap_E2": len(E1 & E2),
}
p0_pass = p0["E1_count"] == 6142 and p0["E2_count"] == 8188 and p0["E1_gen_eq"] and p0["E2_gen_eq"] and p0["E1_cap_E2"] == 0
res["P0"] = {**p0, "pass": bool(p0_pass)}
log(f"P0: E1={p0['E1_count']} E2={p0['E2_count']} 生成全等={p0['E1_gen_eq']}/{p0['E2_gen_eq']} 交={p0['E1_cap_E2']} pass={p0_pass}")

# ---------- P1 分支计数闭式（定长 k 串 ↔ 值集 [0,4^k)） ----------
def branch_values(kind, k):
    """返回长度 k 串分支的值集。kind: 'E1b1','E1b2','E2b1','E2b2'"""
    out = set()
    # u 段（{0,3}*）长度 u_len 的所有值
    def uvals(L):
        vs = [0]
        p = 1
        for _ in range(L):
            vs = [v + 0 * p for v in vs] + [v + 3 * p for v in vs]
            p *= 4
        return vs
    for j in range(0, k):  # 尾段长
        u_len = k - 2 - j if kind in ("E1b2", "E2b1", "E2b2") else k - 1 - j
        if u_len < 0: continue
        base_p = 4 ** (j + (1 if kind in ("E1b2", "E2b1", "E2b2") else 0))
        # 串 = u · X · tail；值 = val(u)*4^{rest} + X*4^j + tail_val
        if kind == "E1b1":      # u 2 3^j
            marker = 2 * (4 ** j); tail = (4 ** j - 1)
            rest = j + 1
            for vu in uvals(u_len):
                out.add(vu * (4 ** rest) + marker + tail)
        elif kind == "E1b2":    # u 1 0^j 1
            marker = 1 * (4 ** (j + 1)); tail = 1
            rest = j + 2
            for vu in uvals(u_len):
                out.add(vu * (4 ** rest) + marker + tail)
        elif kind == "E2b1":    # u 2 3^j s, s∈{1,2}；3 尾段值=4^{j+1}-4
            marker = 2 * (4 ** (j + 1))
            tail3 = (4 ** (j + 1)) - 4
            for s in (1, 2):
                rest = j + 2
                for vu in uvals(u_len):
                    out.add(vu * (4 ** rest) + marker + tail3 + s)
        elif kind == "E2b2":    # u 1 0^j s, s∈{2,3}
            marker = 1 * (4 ** (j + 1))
            for s in (2, 3):
                rest = j + 2
                for vu in uvals(u_len):
                    out.add(vu * (4 ** rest) + marker + s)
    return out

pred = {"E1b1": lambda k: 2**k - 1, "E1b2": lambda k: 2**(k-1) - 1 if k >= 2 else 0,
        "E2b1": lambda k: 2**k - 2 if k >= 2 else 0, "E2b2": lambda k: 2**k - 2 if k >= 2 else 0}
p1 = {"per_k": [], "all_pass": True, "failed": []}
for k in range(1, 13):
    row = {}
    vals = {}
    for kind in ("E1b1", "E1b2", "E2b1", "E2b2"):
        vs = branch_values(kind, k)
        vals[kind] = vs
        ok = (len(vs) == pred[kind](k))
        row[kind] = {"count": len(vs), "closed": pred[kind](k), "ok": ok}
        if not ok:
            p1["all_pass"] = False
            p1["failed"].append(f"k={k}:{kind}:{len(vs)}!={pred[kind](k)}")
    # 支间不交 + 支并=水平集
    disj = (vals["E1b1"].isdisjoint(vals["E1b2"])) and (vals["E2b1"].isdisjoint(vals["E2b2"]))
    uni1 = (vals["E1b1"] | vals["E1b2"]) == set(y for y in E1 if y < 4**k)
    uni2 = (vals["E2b1"] | vals["E2b2"]) == set(y for y in E2 if y < 4**k)
    row["disjoint"] = bool(disj); row["union_eq_E1"] = bool(uni1); row["union_eq_E2"] = bool(uni2)
    if not (disj and uni1 and uni2): p1["all_pass"] = False
    p1["per_k"].append({"k": k, **{kk: vv for kk, vv in row.items()}})
res["P1"] = p1
log(f"P1 分支闭式: all_pass={p1['all_pass']} failed={p1['failed'][:12]} "
    f"(k=12: {[p1['per_k'][11][kk]['count'] for kk in ('E1b1','E1b2','E2b1','E2b2')]})")

# ---------- P2 承接谱（长度 11→12，串级） ----------
def str_from_val(v, L):
    s = ""
    for _ in range(L):
        s = str(v & 3) + s
        v >>= 2
    return s

L1_first_11 = {str_from_val(v, 11) for v in vals11_first} if False else None
# 生成长度 11/12 的分支串集（串级，直接按模式拼）
def gen_branch_strings(kind, k):
    out = set()
    def ustrings(L):
        if L == 0: return [""]
        prev = ustrings(L - 1)
        return [s + "0" for s in prev] + [s + "3" for s in prev]
    if kind == "E1b1":
        for j in range(0, k):
            ul = k - 1 - j
            if ul < 0: continue
            for u in ustrings(ul):
                out.add(u + "2" + "3" * j)
    elif kind == "E1b2":
        for j in range(0, k - 1):
            ul = k - 2 - j
            if ul < 0: continue
            for u in ustrings(ul):
                out.add(u + "1" + "0" * j + "1")
    elif kind == "E2b1":
        for j in range(0, k - 1):
            ul = k - 2 - j
            if ul < 0: continue
            for u in ustrings(ul):
                for s in "12":
                    out.add(u + "2" + "3" * j + s)
    elif kind == "E2b2":
        for j in range(0, k - 1):
            ul = k - 2 - j
            if ul < 0: continue
            for u in ustrings(ul):
                for s in "23":
                    out.add(u + "1" + "0" * j + s)
    return out

L1_11 = gen_branch_strings("E1b1", 11) | gen_branch_strings("E1b2", 11)
L2_12 = gen_branch_strings("E2b1", 12) | gen_branch_strings("E2b2", 12)
L2b1_12 = gen_branch_strings("E2b1", 12)
first11 = gen_branch_strings("E1b1", 11); second11 = gen_branch_strings("E1b2", 11)
log(f"strings: |L1(11)|={len(L1_11)} (first={len(first11)},second={len(second11)}) |L2(12)|={len(L2_12)} (b1={len(L2b1_12)})")

# ① 删尾落点
fall_in = {w for w in L2_12 if w[:-1] in L1_11}
c1 = len(fall_in); c1_eq_first = (fall_in == L2b1_12)
# ② 延伸分布
ext_counts = {}
pairs_total = 0
dist_first = set(); first_all2 = True; second_all0 = True
for w in L1_11:
    exts = [s for s in "0123" if w + s in L2_12]
    pairs_total += len(exts)
    if w in first11:
        dist_first |= set(exts)
        if len(exts) != 2: first_all2 = False
    else:
        if len(exts) != 0: second_all0 = False
c2 = pairs_total
# ③ B 线零出场
b_out = all(len({4 * b + r for b in B_set if 4 * b + r < N12} & E2) == 0 for r in range(4))
p2 = {"删尾落L1计数": c1, "预测4094": c1 == 4094, "落点集=第一支": c1_eq_first,
      "承接对总数": c2, "预测4094对": c2 == 4094,
      "第一支每词延伸集": sorted(dist_first), "第一支全恰2": first_all2,
      "第二支全0": second_all0, "B线零出场": b_out}
p2_pass = (c1 == 4094 and c1_eq_first and c2 == 4094 and first_all2 and second_all0
           and dist_first == {"1", "2"} and b_out)
res["P2"] = {**p2, "pass": bool(p2_pass)}
log(f"P2 承接谱: 删尾落={c1}/4094 集=第一支:{c1_eq_first} 对={c2}/4094 延伸={sorted(dist_first)} "
    f"第一支恰2:{first_all2} 第二支0:{second_all0} B零出场:{b_out} pass={p2_pass}")

# ---------- P3 层族计数 ----------
sizes = {"C": len(C_set), "B": len(B_set),
         "4C+1": len(L2_layers[1]), "4C+2": len(L2_layers[2]),
         "4Q+2": len(Q_layers[2]), "4Q+3": len(Q_layers[3])}
layers = [L2_layers[1], L2_layers[2], Q_layers[2], Q_layers[3]]
disj = all(layers[i].isdisjoint(layers[j]) for i in range(4) for j in range(i+1, 4))
uni = set().union(*layers) == E2
# 点型表
def point_type(valset):
    ms = set(); ts = set()
    for v in valset:
        ms.add(v % 3); ts.add(1 if bin(v).count('1') % 2 == 0 else -1)
    return (sorted(ms), sorted(ts))
pt = {"4C+1": point_type(L2_layers[1]), "4C+2": point_type(L2_layers[2]),
      "4Q+2": point_type(Q_layers[2]), "4Q+3": point_type(Q_layers[3])}
pt_pred = {"4C+1": [[0], [1]], "4C+2": [[1], [1]], "4Q+2": [[0], [1]], "4Q+3": [[1], [-1]]}
pt_ok = all([list(pt[kk][0]), list(pt[kk][1])] == pt_pred[kk] for kk in pt)
p3_pass = (sizes["C"] == 4095 and sizes["B"] == 2047 and all(v == 2047 for kk, v in sizes.items() if kk.startswith("4"))
           and disj and uni and pt_ok)
res["P3"] = {"sizes": sizes, "disjoint": disj, "union_eq_E2": uni,
             "point_types": {kk: [list(a), list(b)] for kk, (a, b) in pt.items()},
             "point_types_pred": {kk: [list(a), list(b)] for kk, (a, b) in pt_pred.items()},
             "pass": bool(p3_pass)}
log(f"P3 层族: {sizes} 不交={disj} 并=E2:{uni} 点型ok={pt_ok} pass={p3_pass}")

# ---------- P4/P5 最小 DFA：显式 5 态表+全集校验+见证矩阵+同构 ----------
# L2 DFA（R22 N-D 表）
DFA_L2 = {
    "q0":  ("q0", "qB", "qC2", "q0", False),
    "qC2": ("qD", "qF", "qF", "qC2", False),
    "qB":  ("qB", "qD", "qF", "qF", False),
    "qF":  ("qD", "qD", "qD", "qD", True),
    "qD":  ("qD", "qD", "qD", "qD", False),
}
# L1 DFA（R21 J-E 口径推导：qC 接受（右语言 3*∋ε）、qB2 接受（{ε}））
DFA_L1 = {
    "q0":  ("q0", "qB", "qC", "q0", False),
    "qC":  ("qD", "qD", "qD", "qC", True),
    "qB":  ("qB", "qB2", "qD", "qD", False),
    "qB2": ("qD", "qD", "qD", "qD", True),
    "qD":  ("qD", "qD", "qD", "qD", False),
}
def dfa_accept(dfa, s):
    st = "q0"
    for ch in s:
        st = dfa[st][int(ch)]
    return dfa[st][4]

def lang_matcher_L1(s):
    # {0,3}*2 3* ∪ {0,3}*1 0*1
    n = len(s)
    for i in range(n):
        if s[i] == "2":
            if all(c in "03" for c in s[:i]) and all(c == "3" for c in s[i+1:]):
                return True
        if s[i] == "1":
            if all(c in "03" for c in s[:i]):
                j = i + 1
                while j < n and s[j] == "0": j += 1
                if j == n - 1 and s[j] == "1":
                    return True
                # 若 i 后直接是末位 1（0^0）
                if i == n - 1:
                    return True
    return False

def lang_matcher_L2(s):
    # {0,3}*2 3*{1,2} ∪ {0,3}*1 0*{2,3}
    n = len(s)
    for i in range(n):
        if s[i] == "2":
            if all(c in "03" for c in s[:i]):
                j = i + 1
                while j < n and s[j] == "3": j += 1
                if j == n - 1 and s[j] in "12":
                    return True
        if s[i] == "1":
            if all(c in "03" for c in s[:i]):
                j = i + 1
                while j < n and s[j] == "0": j += 1
                if j == n - 1 and s[j] in "23":
                    return True
    return False

# 全集校验（长度 ≤10 全枚举；地面真值=分支生成集——其与 D 水平集全等已证）
def gen_lang_strings(lang, L):
    if lang == "L1":
        return gen_branch_strings("E1b1", L) | gen_branch_strings("E1b2", L)
    return gen_branch_strings("E2b1", L) | gen_branch_strings("E2b2", L)

def full_check(dfa, lang, maxlen=9):
    bad = 0
    for L in range(0, maxlen + 1):
        truth = gen_lang_strings(lang, L)
        for x in range(4 ** L):
            s = str_from_val(x, L)
            if dfa_accept(dfa, s) != (s in truth):
                bad += 1
    return bad

bad1 = full_check(DFA_L1, "L1", 10)
bad2 = full_check(DFA_L2, "L2", 10)
# 语言 vs 值集（长度 11/12 串值 ↔ D 水平集）
v1 = {int(s, 4) for s in L1_11}; v2 = {int(s, 4) for s in L2_12}
ok_set1 = (v1 == set(y for y in E1 if y < 4**11))
ok_set2 = (v2 == set(y for y in E2 if y < 4**12))
log(f"DFA vs matcher 失配: L1={bad1} L2={bad2}; 串值集=D集: L1(11)={ok_set1} L2(12)={ok_set2}")

# 5 态可达+两两可分（见证矩阵：BFS 最短区分后缀，字典序最短）
from collections import deque
def witness_matrix(dfa):
    """最短区分见证矩阵：单 BFS 带父指针（首中即返，可证终止）"""
    states = list(dfa)
    mat = {}
    for i in range(len(states)):
        for j in range(i+1, len(states)):
            a, b = states[i], states[j]
            if dfa[a][4] != dfa[b][4]:
                mat[(a, b)] = ("", 0); continue
            seen = {(a, b): None}
            qd = deque([(a, b)])
            ans = None
            while qd and ans is None:
                cur = qd.popleft()
                for d, ch in enumerate("0123"):
                    na, nb = dfa[cur[0]][d], dfa[cur[1]][d]
                    if (na, nb) in seen: continue
                    seen[(na, nb)] = (cur, ch)
                    if dfa[na][4] != dfa[nb][4]:
                        path = []
                        x = (na, nb)
                        while seen[x] is not None:
                            pv, c2 = seen[x]
                            path.append(c2); x = pv
                        ans = "".join(reversed(path)) + ch
                        break
                    qd.append((na, nb))
            mat[(a, b)] = (ans, len(ans) if ans is not None else None)
    return mat

mat1 = witness_matrix(DFA_L1); mat2 = witness_matrix(DFA_L2)
ok1 = all(v[0] is not None for v in mat1.values())
ok2 = all(v[0] is not None for v in mat2.values())
acc1 = sum(1 for s in DFA_L1 if DFA_L1[s][4]); acc2 = sum(1 for s in DFA_L2 if DFA_L2[s][4])
# 同构：接受态数不同即非同构
iso_possible = (acc1 == acc2)
res["P4"] = {"L1_witness_matrix": {f"{a}|{b}": [mat1[(a, b)][0], mat1[(a, b)][1]] for (a, b) in mat1},
             "L2_witness_matrix": {f"{a}|{b}": [mat2[(a, b)][0], mat2[(a, b)][1]] for (a, b) in mat2},
             "L1_all_separated": ok1, "L2_all_separated": ok2,
             "dfa_matcher_mismatch_L1": bad1, "L2": bad2,
             "set_eq_L1_11": ok_set1, "set_eq_L2_12": ok_set2,
             "pass": bool(ok1 and ok2 and bad1 == 0 and bad2 == 0 and ok_set1 and ok_set2)}
res["P5"] = {"accepting_L1": acc1, "accepting_L2": acc2,
             "non_isomorphic": bool(not iso_possible),
             "pass": bool(acc1 == 2 and acc2 == 1 and not iso_possible)}
log(f"P4: 分离 L1={ok1} L2={ok2} 失配 {bad1}/{bad2} 集全等 {ok_set1}/{ok_set2} pass={res['P4']['pass']}")
log(f"P5: 接受态 L1={acc1} L2={acc2} 非同构={not iso_possible} pass={res['P5']['pass']}")

# ---------- P6 总裁决 ----------
p6 = (p0_pass and p1["all_pass"] and p3_pass and res["P4"]["pass"] and p2_pass and res["P5"]["pass"])
res["P6_total"] = {"structure_pass(P0/P1/P3/P4)": bool(p0_pass and p1["all_pass"] and p3_pass and res["P4"]["pass"]),
                   "predictions_pass(P2/P5)": bool(p2_pass and res["P5"]["pass"]),
                   "total": bool(p6)}
log(f"P6 总裁决: 结构主项={res['P6_total']['structure_pass(P0/P1/P3/P4)']} 预测={res['P6_total']['predictions_pass(P2/P5)']} [{time.time()-T0:.1f}s]")

outp = "H:/理论存档/01-数学/02-实验与数据/results/e2_depth_spectrum_result-v1.0-20260921.json"
with open(outp, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1, default=str)
log(f"结果落盘 {outp}")
