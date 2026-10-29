# -*- coding: utf-8 -*-
"""R22 主格一·D 值水平集全谱定理化 判据 N0-N7 实算（v2 正式版）
判据书：代数册·D值水平集全谱定理化预注册判据书-v1.0-20260921.md（冻结在先）
口径：4^12 D 表全域；Nerode 变长串采样（真右语言截断）为主判据+定宽对照；
DFA 模拟 Y<=3e6（初始态=空串类）；判负照记。
调试首跑拦截更正（如实披露）：(1<<b)->(1<<(2*b)) 拼接与域两处、定宽->变长采样、
显式表初始态、见证清单 4 处（N-D）——详见判据书 §四。
"""
import json, time
import numpy as np

T0 = time.time()
LOG = []
def log(msg):
    LOG.append(msg)
    print(msg, flush=True)

N12 = 1 << 24  # 4^12
g_tab = np.array([[0,0,0],[0,1,-1],[-1,2,-1],[0,2,-2]], dtype=np.int64)

# ---------- D 表逐层构建 ----------
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

# ---------- N0 直接定义对照 ----------
def direct_D_series(Ymax):
    out = np.zeros(Ymax + 1, dtype=np.int64)
    s1 = 0; s2 = 0
    for n in range(Ymax + 1):
        out[n] = s1 - s2
        r = n % 3
        tn = 1 if bin(n).count('1') % 2 == 0 else -1
        if r == 1: s1 += tn
        elif r == 2: s2 += tn
    return out
ref = direct_D_series(2000)
n0_mismatch = int(np.sum(ref[:2001] != D[:2001]))
e1_count_12 = int(np.sum(D == -1))
log(f'N0 mismatch={n0_mismatch}  E_-1(4^12)={e1_count_12} (expect 6142)')

# ---------- 语言生成集 ----------
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
E1_set = C_set | B_set
E2_set = ({4*c+1 for c in C_set if 4*c+1<N12} | {4*c+2 for c in C_set if 4*c+2<N12}
          | {4*q+2 for q in Q_set if 4*q+2<N12} | {4*q+3 for q in Q_set if 4*q+3<N12})
E3_set = {4*z for z in E1_set if 4*z < N12}
E4_set = ({16*c+10 for c in C_set if 16*c+10<N12} | {16*c+11 for c in C_set if 16*c+11<N12}
          | {4*b+1 for b in B_set if 4*b+1<N12} | {4*b+2 for b in B_set if 4*b+2<N12})
E5_set = ({16*c+9 for c in C_set if 16*c+9<N12}
          | {4*b+3 for b in B_set if 4*b+3<N12})
E6_set = ({4*z for z in E2_set if 4*z<N12}
          | {16*c+5 for c in C_set if 16*c+5<N12} | {16*c+7 for c in C_set if 16*c+7<N12}
          | {16*q+9 for q in Q_set if 16*q+9<N12} | {16*q+11 for q in Q_set if 16*q+11<N12})
E7_set = ({16*c+3 for c in C_set if 16*c+3<N12} | {16*c+6 for c in C_set if 16*c+6<N12}
          | {16*q+10 for q in Q_set if 16*q+10<N12} | {16*q+13 for q in Q_set if 16*q+13<N12})
log(f'gen: C={len(C_set)} B={len(B_set)} E1={len(E1_set)} E2={len(E2_set)} E3={len(E3_set)} E4={len(E4_set)} E5={len(E5_set)} E6={len(E6_set)} E7={len(E7_set)}')

def level_eq(c, gen_set):
    actual = set(np.nonzero(D == c)[0].tolist())
    return actual == gen_set, len(actual), len(gen_set)

def count_by_k(c, kmax=12):
    return [int(np.sum(D[:(1 << (2 * k))] == c)) for k in range(1, kmax + 1)]

def closed_counts(name, kmax=12):
    out = []
    for k in range(1, kmax + 1):
        if name == 'E-2': out.append(2 ** (k + 1) - 4)
        elif name == 'E-3': out.append(3 * 2 ** (k - 2) - 2 if k >= 2 else 0)
        elif name == 'E-4': out.append(2 ** k - 4 if k >= 2 else 0)
        elif name == 'E-5': out.append(2 ** (k - 1) - 2 if k >= 2 else 0)
        elif name == 'E-6': out.append(2 ** (k + 1) - 8 if k >= 2 else 0)
        elif name == 'E-7': out.append(2 ** k - 4 if k >= 2 else 0)
    return out

# ---------- Nerode：变长串采样（主判据口径）+定宽对照 ----------
def suffix_strs(maxlen):
    out = [(0, 0)]
    for L in range(1, maxlen + 1):
        for v in range(4 ** L):
            out.append((v, L))
    return out

def nerode_var(c, maxlen, aw):
    inL = (D == c)
    WS = suffix_strs(maxlen)
    Wv = np.array([w[0] for w in WS], dtype=np.int64)
    Wl = np.array([w[1] for w in WS], dtype=np.int64)
    KU = 1 << (2 * aw)
    assert KU * (4 ** maxlen) <= N12
    U = np.arange(KU, dtype=np.int64)
    sig = np.empty((KU, len(WS) + 1), dtype=bool)
    for j in range(len(WS)):
        sig[:, j] = inL[U * (1 << (2 * int(Wl[j]))) + Wv[j]]
    sig[:, -1] = inL[U]
    return len(np.unique(sig, axis=0)), sig, U

def nerode_fixed(c, bw, aw):
    inL = (D == c)
    NW = 1 << (2 * bw); KU = 1 << (2 * aw)
    assert KU * NW <= N12
    U = np.arange(KU, dtype=np.int64); W = np.arange(NW, dtype=np.int64)
    sig = np.empty((KU, NW + 1), dtype=bool)
    sig[:, :-1] = inL[U[:, None] * NW + W[None, :]]
    sig[:, -1] = inL[U]
    return len(np.unique(sig, axis=0)), sig, U

def min_dfa_from_sig(sig, U):
    uniq, inv = np.unique(sig, axis=0, return_inverse=True)
    reps = [int(U[np.argmax(inv == i)]) for i in range(len(uniq))]
    accept = [bool(uniq[i, -1]) for i in range(len(uniq))]
    trans = []
    for i, r in enumerate(reps):
        row = []
        for d in range(4):
            v = r * 4 + d
            assert v < sig.shape[0], f'rep transition out of domain: r={r} d={d} v={v}'
            row.append(int(inv[v]))
        trans.append(row)
    st0 = int(inv[0])
    return len(uniq), trans, accept, reps, inv, st0

def dfa_simulate(trans, accept, Ymax, c, st0=0):
    Y = np.arange(Ymax + 1, dtype=np.int64)
    st = np.full(Ymax + 1, st0, dtype=np.int64)
    T = np.array(trans, dtype=np.int64)
    for j in range(11, -1, -1):
        dig = (Y >> (2 * j)) & 3
        st = T[st, dig]
    acc = np.array(accept, dtype=bool)
    return int(np.sum(acc[st] != (D[Y] == c)))

res = {}
res['N0'] = {'mismatch_2000': n0_mismatch, 'e1_count_4pow12': e1_count_12, 'e1_expect': 6142}

# ---------- N1 ----------
ok_eq, na, ng = level_eq(-2, E2_set)
cnt2 = count_by_k(-2); clo2 = closed_counts('E-2')
m_of_e2 = np.arange(N12)[D == -2] % 3
L1 = {4*c+1 for c in C_set if 4*c+1<N12}; L2s = {4*c+2 for c in C_set if 4*c+2<N12}
L3s = {4*q+2 for q in Q_set if 4*q+2<N12}; L4s = {4*q+3 for q in Q_set if 4*q+3<N12}
inter = (L1 & L2s) or (L1 & L3s) or (L1 & L4s) or (L2s & L3s) or (L2s & L4s) or (L3s & L4s)
layers_ok = (not inter) and (L1 | L2s | L3s | L4s) == E2_set
res['N1'] = {'lang_equal': ok_eq, 'actual': na, 'gen': ng, 'counts_k1_12': cnt2, 'closed': clo2,
             'closed_match': cnt2 == clo2, 'm_set': sorted(set(m_of_e2.tolist())), 'layers_ok': layers_ok}
log(f"N1: eq={ok_eq} ({na}={ng}) closed={cnt2==clo2} m={res['N1']['m_set']} layers={layers_ok}")

# ---------- N2 ----------
nv2 = [nerode_var(-2, 5, 6)[0], nerode_var(-2, 6, 6)[0], nerode_var(-2, 5, 7)[0]]
nf2 = [nerode_fixed(-2, 5, 6)[0], nerode_fixed(-2, 6, 6)[0], nerode_fixed(-2, 5, 7)[0]]
_, sig2, U6 = nerode_var(-2, 6, 6)
nd2, T2t, acc2, reps2, inv2, st02 = min_dfa_from_sig(sig2, U6)
sim2 = dfa_simulate(T2t, acc2, 3_000_000, -2, st02)
T_exp2 = [[0,2,1,0],[4,3,3,1],[2,4,3,3],[4,4,4,4],[4,4,4,4]]
acc_exp2 = [False, False, False, True, False]
sim2_exp = dfa_simulate(T_exp2, acc_exp2, 3_000_000, -2, 0)
def val_of(s4):
    v = 0
    for ch in s4: v = v * 4 + int(ch)
    return v
def full(v, w):
    if w is None: return bool(D[v] == -2)
    vv = v * (1 << (2 * len(w))) + val_of(w)
    return bool(D[vv] == -2) if vv < N12 else None
cls = {name: reps2[int(inv2[v])] for name, v in [('q0', 3), ('qC2', 2), ('qB', 4), ('qF', 9), ('qD', 5)]}
wit = [('q0','qC2','13'), ('q0','qB','2'), ('q0','qF','12'), ('q0','qD','12'),
       ('qC2','qB','02'), ('qC2','qF','2'), ('qC2','qD','31'), ('qB','qF','2'),
       ('qB','qD','2'), ('qF','qD', None)]
wit_ok = 0; wit_detail = []
for x, y, w in wit:
    a_ = full(cls[x], w); b_ = full(cls[y], w)
    ok = (a_ is not None and b_ is not None and a_ != b_)
    wit_ok += int(ok)
    wit_detail.append({'pair': f'{x}|{y}', 'w': w, 'L(uw)': a_, 'L(vw)': b_, 'separated': bool(ok)})
res['N2'] = {'nerode_var_3domain': nv2, 'nerode_fixed_3domain': nf2, 'min_dfa_states': nd2,
             'sim_mismatch_3e6': sim2, 'explicit5_mismatch': sim2_exp,
             'witness': wit_detail, 'witness_ok': wit_ok}
log(f"N2: var={nv2} fixed={nf2} states={nd2} sim={sim2} exp5={sim2_exp} wit={wit_ok}/10")

# ---------- N3 ----------
ok3, na3, ng3 = level_eq(-3, E3_set)
cnt3 = count_by_k(-3); clo3 = closed_counts('E-3')
nv3 = [nerode_var(-3, 5, 6)[0], nerode_var(-3, 6, 6)[0], nerode_var(-3, 5, 7)[0]]
nf3 = [nerode_fixed(-3, 5, 6)[0], nerode_fixed(-3, 6, 6)[0], nerode_fixed(-3, 5, 7)[0]]
_, sig3, _ = nerode_var(-3, 6, 6)
nd3, T3t, acc3, reps3, inv3, st03 = min_dfa_from_sig(sig3, np.arange(sig3.shape[0]))
sim3 = dfa_simulate(T3t, acc3, 3_000_000, -3, st03)
T_exp3 = [[0,2,1,0],[4,5,5,1],[2,3,5,5],[4,5,5,5],[5,5,5,5],[5,5,5,5]]  # 6 态修正版：q0/qC/qB/qB2/qA/qD
acc_exp3 = [False, False, False, False, True, False]
sim3_exp = dfa_simulate(T_exp3, acc_exp3, 3_000_000, -3, 0)
res['N3'] = {'lang_equal': ok3, 'actual': na3, 'gen': ng3, 'counts_k1_12': cnt3, 'closed': clo3,
             'closed_match': cnt3 == clo3, 'nerode_var_3domain': nv3, 'nerode_fixed_3domain': nf3,
             'min_dfa_states': nd3, 'sim_mismatch_3e6': sim3, 'explicit7_mismatch': sim3_exp}
log(f"N3: eq={ok3} ({na3}={ng3}) closed={cnt3==clo3} var={nv3} fixed={nf3} states={nd3} sim={sim3} exp7={sim3_exp}")

# ---------- N4 ----------
ok4, na4, ng4 = level_eq(-4, E4_set)
cnt4 = count_by_k(-4); clo4 = closed_counts('E-4')
nv4 = [nerode_var(-4, 5, 6)[0], nerode_var(-4, 6, 6)[0], nerode_var(-4, 5, 7)[0]]
nf4 = [nerode_fixed(-4, 5, 6)[0], nerode_fixed(-4, 6, 6)[0], nerode_fixed(-4, 5, 7)[0]]
_, sig4, _ = nerode_var(-4, 5, 7)
nd4, T4t, acc4, reps4, inv4, st04 = min_dfa_from_sig(sig4, np.arange(sig4.shape[0]))
sim4 = dfa_simulate(T4t, acc4, 3_000_000, -4, st04)
res['N4'] = {'lang_equal': ok4, 'actual': na4, 'gen': ng4, 'counts_k1_12': cnt4, 'closed': clo4,
             'closed_match': cnt4 == clo4, 'nerode_var_3domain': nv4, 'nerode_fixed_3domain': nf4,
             'min_dfa_states': nd4, 'sim_mismatch_3e6': sim4}
log(f"N4: eq={ok4} ({na4}={ng4}) closed={cnt4==clo4} var={nv4} fixed={nf4} states={nd4} sim={sim4}")

# ---------- N5 ----------
ok5, na5, ng5 = level_eq(-5, E5_set)
cnt5 = count_by_k(-5); clo5 = closed_counts('E-5')
m_of_e5 = np.arange(N12)[D == -5] % 3
nv5 = [nerode_var(-5, 5, 6)[0], nerode_var(-5, 6, 6)[0], nerode_var(-5, 5, 7)[0]]
nf5 = [nerode_fixed(-5, 5, 6)[0], nerode_fixed(-5, 6, 6)[0], nerode_fixed(-5, 5, 7)[0]]
_, sig5, _ = nerode_var(-5, 5, 7)
nd5, T5t, acc5, reps5, inv5, st05 = min_dfa_from_sig(sig5, np.arange(sig5.shape[0]))
sim5 = dfa_simulate(T5t, acc5, 3_000_000, -5, st05)
res['N5'] = {'lang_equal': ok5, 'actual': na5, 'gen': ng5, 'counts_k1_12': cnt5, 'closed': clo5,
             'closed_match': cnt5 == clo5, 'm_set': sorted(set(m_of_e5.tolist())),
             'nerode_var_3domain': nv5, 'nerode_fixed_3domain': nf5,
             'min_dfa_states': nd5, 'sim_mismatch_3e6': sim5}
log(f"N5: eq={ok5} ({na5}={ng5}) closed={cnt5==clo5} m={res['N5']['m_set']} var={nv5} fixed={nf5} states={nd5} sim={sim5}")

# ---------- N6 预测值 ----------
ok6, na6, ng6 = level_eq(-6, E6_set)
ok7, na7, ng7 = level_eq(-7, E7_set)
cnt6 = count_by_k(-6); clo6 = closed_counts('E-6')
cnt7 = count_by_k(-7); clo7 = closed_counts('E-7')
res['N6'] = {
    'E-6': {'lang_equal': ok6, 'actual': na6, 'gen': ng6, 'counts': cnt6, 'closed': clo6, 'closed_match': cnt6 == clo6},
    'E-7': {'lang_equal': ok7, 'actual': na7, 'gen': ng7, 'counts': cnt7, 'closed': clo7, 'closed_match': cnt7 == clo7},
}
log(f"N6: E-6 eq={ok6} ({na6}={ng6}) closed={cnt6==clo6}; E-7 eq={ok7} ({na7}={ng7}) closed={cnt7==clo7}")

# ---------- N7 总裁决 ----------
n1_pass = bool(ok_eq and (cnt2 == clo2) and res['N1']['m_set'] == [0, 1] and layers_ok)
n2_pass = bool((len(set(nv2)) == 1) and sim2 == 0 and wit_ok == 10 and nd2 == nv2[0] and sim2_exp == 0)
n3_pass = bool(ok3 and (cnt3 == clo3) and (len(set(nv3)) == 1) and sim3 == 0 and sim3_exp == 0)
n4_pass = bool(ok4 and (cnt4 == clo4) and (len(set(nv4)) == 1) and sim4 == 0)
n5_pass = bool(ok5 and (cnt5 == clo5) and res['N5']['m_set'] == [2] and (len(set(nv5)) == 1) and sim5 == 0)
n6_pass = bool(ok6 and cnt6 == clo6 and ok7 and cnt7 == clo7)
res['N7'] = {'N1': n1_pass, 'N2': n2_pass, 'N3': n3_pass, 'N4': n4_pass,
             'N5': n5_pass, 'N6_prediction': n6_pass,
             'structure_pass': bool(n1_pass and n2_pass and n3_pass and n4_pass and n5_pass)}
log(f"N7: {res['N7']}")

res['meta'] = {'elapsed_s': round(time.time() - T0, 1), 'log': LOG}
import io
out = r'H:\理论存档\01-数学\02-实验与数据\results\d_level_full_spectrum_result-v1.0-20260921.json'
io.open(out, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1, default=str))
print('saved', out)
