# -*- coding: utf-8 -*-
# R44 formal run: cap-law theorems (D-C1..C6) + G-series sigma-palindrome deepening (D-C7)
# Frozen criteria book: 2026-09-25T11:07:43 (NTFS) precedes this run.
import numpy as np
import json, time, os

OUT = "H:/理论存档/01-数学/04-工具与代码/r44_cap_theorem"
os.makedirs(OUT, exist_ok=True)
G = np.array([[0,0,0],[0,1,-1],[-1,2,-1],[0,2,-2]], dtype=np.int64)
FAC = np.array([1,-1,-1,1], dtype=np.int64)
CL = {(-1,2):0, (-1,1):1, (1,0):1, (1,1):1, (1,2):2, (-1,0):5}   # frozen c-table
SAFE = {(1,0), (-1,1), (1,2)}

def dp_layer(L):
    N = 4**L
    w = np.arange(N, dtype=np.int64)
    D = np.zeros(N, dtype=np.int64); T = np.ones(N, dtype=np.int64); M = np.zeros(N, dtype=np.int64)
    for i in range(L):
        r = (w // 4**(L-1-i)) % 4
        D = 3*D + T*G[r, M]
        T = T*FAC[r]
        M = (M + r) % 3
    return w, D, T, M

def rev_map(L):
    N = 4**L; w = np.arange(N, dtype=np.int64); rv = np.zeros(N, dtype=np.int64)
    for i in range(L):
        rv = rv*4 + (w // 4**i) % 4
    return rv

def sig_map(L):
    N = 4**L; w = np.arange(N, dtype=np.int64); s = np.zeros(N, dtype=np.int64)
    for i in range(L):
        s = s*4 + (3 - (w // 4**(L-1-i)) % 4)
    return s

res = {"frozen_at": "2026-09-25T11:07:43", "t_start": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "part1": [], "part2": {}, "violations": []}

# ---------- part1: D-C1..D-C4, L=1..12 full domain ----------
for L in range(1, 13):
    t0 = time.time()
    w, D, T, M = dp_layer(L)
    cls = ((T+1)//2)*3 + M            # 0..5 key: (tau,mu) -> ((tau+1)/2, mu)
    cvec = np.array([CL[((-1)*(k//3==0)*1 + (1)*(k//3==1), k%3)] for k in range(6)], dtype=np.int64)
    # careful: key k=(tau+1)/2*3+mu ; tau=-1 -> k//3==0 ; tau=+1 -> k//3==1
    cvec = np.array([CL[(-1 if k < 3 else 1, k % 3)] for k in range(6)], dtype=np.int64)
    floor = -3**(L-1) + cvec[cls]     # H-2' per-word refined floor
    mn, mx = int(D.min()), int(D.max())
    c1 = (mn == -3**(L-1)) and (mx == 0)
    arg = w[D == mn]
    c2 = (len(arg) == 1) and (int(arg[0]) == 2*4**(L-1))
    v_h2 = int((D < floor).sum())
    # per-class min (reachability + achievability)
    percls = {}
    for k in range(6):
        m = cls == k
        if m.any():
            percls[("tau,mu", -1 if k < 3 else 1, k % 3)] = {"min": int(D[m].min()),
                                                             "bound": -3**(L-1) + CL[(-1 if k < 3 else 1, k % 3)],
                                                             "n": int(m.sum())}
    c3 = all(v["min"] == v["bound"] for v in percls.values()) and v_h2 == 0
    safe_keys = {((1 if t == 1 else 0)*3 + mu) for (t, mu) in SAFE}
    # key for tau=+1: (1+1)//2=1 -> 3+mu ; tau=-1: 0*3+mu
    safe_keys = {3+0, 0+1, 3+2}
    zmask = D == 0
    c4 = bool(np.isin(cls[zmask], list(safe_keys)).all()) if zmask.any() else True
    rec = {"L": L, "min": mn, "max": mx, "c1": c1, "argmin_word": int(arg[0]) if len(arg) else None,
           "argmin_unique": c2, "h2_violations": v_h2, "perclass": {str(k): v for k, v in percls.items()},
           "c3": c3, "c4": c4, "sec": round(time.time()-t0, 2)}
    res["part1"].append(rec)
    print("L=%2d min=%-7d max=%d c1=%s argmin_uniq=%s h2_bad=%d c3=%s c4=%s (%.1fs)" %
          (L, mn, mx, c1, c2, v_h2, c3, c4, rec["sec"]), flush=True)
    del w, D, T, M, cls, floor

# ---------- part2: D-C5..D-C7 ----------
p2 = {}
for L in range(1, 13):
    t0 = time.time()
    w, D, T, M = dp_layer(L)
    rv = rev_map(L); sg = sig_map(L)
    Dr = D[rv]; Ds = D[sg]
    Fix = D == Dr
    pal = w == rv
    # D-C5 cap-class Fix emptiness
    cap = -3**(L-1)
    capfix = int(((D == cap) & Fix).sum())
    c5 = (capfix == 0) if L >= 2 else (capfix == 1)
    # D-C6 E0 mu layer
    e0 = D == 0
    m0 = int((e0 & Fix & (M == 0)).sum()); m1 = int((e0 & Fix & (M == 1)).sum()); m2 = int((e0 & Fix & (M == 2)).sum())
    c6 = (m0 == 2**L) and (m1 == L) and (m2 == 0)
    # D-C7a keep criterion + count
    kp = pal & (Ds == D)
    crit = kp == (pal & (w % 3 == 0))
    cnt = int(kp.sum()); closed = (4**((L+1)//2) + 2)//3
    c7a = bool(crit.all()) and (cnt == closed)
    # D-C7b even-layer diff closed form
    c7b = None
    if L % 2 == 0:
        diff = Ds[pal] - D[pal]; mu = M[pal]
        want = np.where(mu == 0, 0, np.where(mu == 1, 1, -1))
        c7b = bool((diff == want).all())
    # D-C7c odd-layer 12-cell table
    c7c = None
    if L % 2 == 1:
        TAB = {(0,0):0,(0,1):-1,(0,2):1,(0,3):0,(1,0):-1,(1,1):0,(1,2):-1,(1,3):-1,(2,0):1,(2,1):1,(2,2):0,(2,3):1}
        hn = L//2
        ok = True
        for h in range(4**hn):
            hs = [(h // 4**(hn-1-i)) % 4 for i in range(hn)]
            for m in range(4):
                ds = hs + [m] + hs[::-1]
                dd, mm = 0, 0; tt = 1
                for r in ds:
                    dd = 3*dd + tt*int(G[r, mm]); tt *= int(FAC[r]); mm = (mm + r) % 3
                dsw = [3-x for x in ds]
                dsd, _ = 0, 0; tts = 1; mms = 0
                for r in dsw:
                    dsd = 3*dsd + tts*int(G[r, mms]); tts *= int(FAC[r]); mms = (mms + r) % 3
                if dsd - dd != TAB[(h % 3, m)]:
                    ok = False; break
            if not ok: break
        c7c = ok
    rec = {"L": L, "capfix": capfix, "c5": c5, "e0_mu": [m0, m1, m2], "c6": c6,
           "keep_cnt": cnt, "keep_closed": closed, "c7a": c7a, "c7b": c7b, "c7c": c7c,
           "sec": round(time.time()-t0, 2)}
    p2[str(L)] = rec
    print("L=%2d capFix=%d c5=%s e0mu=%s c6=%s keep=%d/%d c7a=%s c7b=%s c7c=%s (%.1fs)" %
          (L, capfix, c5, rec["e0_mu"], c6, cnt, closed, c7a, c7b, c7c, rec["sec"]), flush=True)
    del w, D, T, M, rv, sg, Dr, Ds, Fix, pal

# D-C7d representative classes at L=12
w, D, T, M = dp_layer(12)
rv = rev_map(12); Fix = D == D[rv]; pal = w == rv
rep = {}
for c in (-1, -2, -3):
    msk = D == c
    fixc = int((msk & Fix).sum()); palc = int((msk & pal).sum())
    rep[str(c)] = {"words": int(msk.sum()), "fix": fixc, "pal": palc, "pair": (fixc-palc)//2}
p2["rep_L12"] = rep
res["part2"] = p2
res["t_end"] = time.strftime("%Y-%m-%dT%H:%M:%S")
print("rep L12:", rep, flush=True)

with open(OUT + "/r44_results.json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1, default=str)
bad = []
for r in res["part1"]:
    if not (r["c1"] and r["argmin_unique"] and r["c3"] and r["c4"]): bad.append(r["L"])
for Lr, r in p2.items():
    if Lr == "rep_L12":
        ok = (r["-1"]["fix"] == 13 and r["-1"]["pal"] == 1 and r["-2"]["fix"] == 11 and r["-2"]["pal"] == 1)
        if not ok: bad.append("rep")
    else:
        if not (r["c5"] and r["c6"] and r["c7a"]): bad.append(Lr)
        if r["c7b"] is False: bad.append("c7b@"+str(Lr))
        if r["c7c"] is False: bad.append("c7c@"+str(Lr))
res["final_bad"] = bad
with open(OUT + "/r44_results.json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1, default=str)
print("FINAL_BAD:", bad if bad else "NONE - ALL PASS", flush=True)
