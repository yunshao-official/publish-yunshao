# -*- coding: utf-8 -*-
"""
代数册·值域效应解析理论预注册判据书-v1.0-20260920 实算脚本
判据书冻结(NTFS): 2026-09-20 02:11:31 —— 本脚本首跑必须晚于该时刻
判据: V0-V5 (判据书 §三, 冻结文本零改动)
核心: 引理 H0 精确类条件恒等式 + H1 CRT 格点计数闭式 -> 六类 x 三档 R̄ 零近似精确预测
新算档: X=2e7 (偶数 1e7 个, 5 片检查点); 2e6/2e5 档切片; V0 用 R16 检查点 raw 复算
附: 逐 N s3(N) per r 落盘 npz (R17 主格三复用)
"""
import json, math, time
import numpy as np
from pathlib import Path

RES = Path(r"H:/理论存档/01-数学/02-实验与数据/results")
TAG = "v1.0-20260920"
X3 = 20_000_000
N_SHARDS = 5
SHARD_N = 2_000_000  # 偶数个数/片

K1T = {0: 24, 8: 8, 16: 8, 12: 12, 4: 4, 20: 4, 6: 6, 18: 6, 2: 2, 10: 2, 14: 2, 22: 2}
CS = [2, 4, 6, 8, 12, 24]
CQA = {2: (12, [1, 5, 7, 11]), 4: (6, [1, 5]), 6: (4, [1, 3]), 8: (3, [1, 2]),
       12: (2, [1]), 24: (1, [0])}
R16_RBAR_2M = {2: 2.2208, 4: 2.1724, 6: 2.0989, 8: 2.0650, 12: 2.0442, 24: 1.9194}
R16_PREV_SHIFTS = {"{6,18}-{2,10,14,22}": 1.3782, "{12}-{4,20}": 1.3718, "{0}-{8,16}": 1.3543}


def spf_sieve(n):
    spf = np.zeros(n + 1, dtype=np.int32)
    for i in range(2, n + 1):
        if spf[i] == 0:
            spf[i] = i
            if i * i <= n:
                sl = spf[i * i::i]
                sl[sl == 0] = i
    return spf


def factorize(n, spf):
    f = {}
    while n > 1:
        p = int(spf[n]); e = 0
        while n % p == 0:
            n //= p; e += 1
        f[p] = e
    return f


def s3(n):
    s = 0
    while n > 0:
        s += n % 3; n //= 3
    return s


def primes_upto(Y):
    sieve = np.ones(Y + 1, dtype=bool); sieve[:2] = False
    for i in range(2, int(Y ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = False
    pr = np.nonzero(sieve)[0]
    return pr[pr >= 5]


def exact_rbar(c, X):
    """引理 H0+H1: R̄(c,X) 零近似精确值 (整数计数和) + N_c (精确)"""
    q, A = CQA[c]
    Y = X // c
    Nc = 0
    for a in A:
        Nc += Y if q == 1 else ((Y - a) // q + 1 if a <= Y else 0)
    inv = [0] * q
    for r_ in range(1, q):
        for m in range(1, q):
            if r_ * m % q == 1:
                inv[r_] = m
    total = 0
    for p in primes_upto(Y):
        pi = int(p); pk = pi
        while pk <= Y:
            if q == 1:
                total += Y // pk
            else:
                ivp = inv[pk % q]
                for a in A:
                    t0 = (a * ivp) % q
                    M0 = pk * t0
                    if M0 <= Y:
                        total += (Y - M0) // (q * pk) + 1
            pk *= pi
    return total, Nc


def main():
    t0 = time.time()
    first_run = time.strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"首跑时间 {first_run}（判据书冻结 2026-09-20 02:11:31 NTFS 在先）"]
    def log(m):
        log_lines.append(str(m)); print(m, flush=True)
    res = {"meta": {"criterion_freeze_ntfs": "2026-09-20 02:11:31", "first_run": first_run, "X3": X3}}

    # ---------- 精确预测 (引理 H0/H1, 与扫描无关, 先算) ----------
    log("计算精确类条件预测 (引理 H0/H1)...")
    pred = {}
    for X in (200000, 2000000, 20000000):
        for c in CS:
            tot, Nc = exact_rbar(c, X)
            pred[f"{X}_{c}"] = tot / Nc
        log(f"  X={X}: " + ", ".join(f"c={c}: {pred[f'{X}_{c}']:.5f}" for c in CS))
    res["exact_pred"] = pred
    log(f"精确预测完成 ({time.time()-t0:.1f}s)")

    # ---------- 实现层自检: exact vs brute (X<=2e5 六类全对才继续) ----------
    def sum_p5(M):
        mm = M
        while mm % 2 == 0: mm //= 2
        while mm % 3 == 0: mm //= 3
        s = 0; d = 5
        while d * d <= mm:
            while mm % d == 0: s += 1; mm //= d
            d = 7 if d == 5 else d + 2
        if mm > 1: s += 1
        return s
    exact_ok = True
    for Xc in (1000, 10000, 50000, 200000):
        for c in CS:
            q, A = CQA[c]
            Y = Xc // c
            bt = 0; bn = 0
            for M in range(1, Y + 1):
                if q == 1 or M % q in A:
                    bn += 1; bt += sum_p5(M)
            tot, Nc = exact_rbar(c, Xc)
            if bn != Nc or abs(bt / bn - tot / Nc) > 1e-9:
                exact_ok = False
                log(f"exact 自检失败 X={Xc} c={c}")
    log(f"exact 公式 vs 暴力枚举 (X<=2e5, 六类): {exact_ok}")
    res["exact_selfcheck"] = bool(exact_ok)
    if not exact_ok:
        res["verdict"] = {"exact_selfcheck_fail_abort": True}
        (RES / f"range_effect_analytic_result-{TAG}.json").write_text(
            json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return

    # ---------- SPF 筛 + 自检锚 ----------
    log(f"SPF 筛到 {X3}...")
    spf = spf_sieve(X3)
    log(f"筛完成 ({time.time()-t0:.1f}s)")
    ok = True
    for n in range(2, 1001):
        bf = {}; m = n; d = 2
        while d * d <= m:
            while m % d == 0:
                bf[d] = bf.get(d, 0) + 1; m //= d
            d += 1
        if m > 1: bf[m] = bf.get(m, 0) + 1
        if bf != factorize(n, spf): ok = False; break
    log(f"自检锚 N<=1000 因子分解暴力对照: {ok}")
    res["selfcheck"] = bool(ok)
    if not ok:
        res["verdict"] = {"selfcheck_fail_abort": True}
        (RES / f"range_effect_analytic_result-{TAG}.json").write_text(
            json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return

    # ---------- 主扫描 5 片 ----------
    acc = {tag: {c: [0, 0.0, 0.0, 0.0] for c in CS} for tag in ("full", "m2M", "m200k")}
    max_per_r = X3 // 24 + 2
    s3_arr = np.zeros((24, max_per_r), dtype=np.int8)
    s3cnt = np.zeros(24, dtype=np.int64)
    s3cnt2M = np.zeros(24, dtype=np.int64)

    for si in range(N_SHARDS):
        lo = 2 + si * SHARD_N * 2
        evens = range(lo, lo + SHARD_N * 2, 2)
        for N in evens:
            r = N % 24
            f = factorize(N, spf)
            om = 0; R = 0
            for p, e in f.items():
                om += e
                if p >= 5: R += e
            c = K1T[r]
            a_full = acc["full"][c]; a_full[0] += 1; a_full[1] += R; a_full[2] += R * R; a_full[3] += om
            if N <= 2000000:
                a2 = acc["m2M"][c]; a2[0] += 1; a2[1] += R; a2[2] += R * R; a2[3] += om
                s3_arr[r, s3cnt[r]] = s3(N); s3cnt[r] += 1
                if s3cnt[r] > s3cnt2M[r]: s3cnt2M[r] = s3cnt[r]
            if N <= 200000:
                a5 = acc["m200k"][c]; a5[0] += 1; a5[1] += R; a5[2] += R * R; a5[3] += om
        ck = {"shard": si + 1, "lo": lo, "acc": {t: {str(c): acc[t][c] for c in CS} for t in acc},
              "s3_total": int(s3cnt.sum())}
        (RES / f"range_analytic_checkpoint_{si+1}-{TAG}.json").write_text(
            json.dumps(ck, ensure_ascii=False), encoding="utf-8")
        log(f"片 {si+1}/{N_SHARDS} 检查点落盘 ({time.time()-t0:.1f}s)")

    np.save(RES / f"range_analytic_s3_by_r-{TAG}.npy", s3_arr)

    def rbar(tag):
        return {c: acc[tag][c][1] / acc[tag][c][0] for c in CS}
    def varR(tag):
        out = {}
        for c in CS:
            n_, s1, s2_, _ = acc[tag][c]
            mu = s1 / n_
            out[c] = s2_ / n_ - mu * mu
        return out

    Rb20, Rb2M, Rb200 = rbar("full"), rbar("m2M"), rbar("m200k")
    v20, v2M, v200 = varR("full"), varR("m2M"), varR("m200k")
    n20 = {c: acc["full"][c][0] for c in CS}
    n2M = {c: acc["m2M"][c][0] for c in CS}
    n200 = {c: acc["m200k"][c][0] for c in CS}

    # ---------- V0: R16 checkpoint raw 复算 + 本轮切片 ----------
    R16_rows_R = []; R16_rows_r = []
    for si in range(5):
        d = json.loads((RES / f"range_effect_checkpoint_{si+1}-v1.0-20260920.json").read_text(encoding="utf-8"))
        for row in d["rows"]:
            R16_rows_r.append(row[1]); R16_rows_R.append(row[6])
    R16_rows_r = np.array(R16_rows_r); R16_rows_R = np.array(R16_rows_R, dtype=float)
    rbar_r16raw = {}
    for c in CS:
        gs = [g for g in K1T if K1T[g] == c]
        m = np.isin(R16_rows_r, gs)
        rbar_r16raw[c] = float(R16_rows_R[m].mean())
    diff_raw = {str(c): abs(rbar_r16raw[c] - Rb2M[c]) for c in CS}
    diff_ref = {str(c): abs(R16_RBAR_2M[c] - Rb2M[c]) for c in CS}
    V0 = max(diff_raw.values()) <= 1e-9 and max(diff_ref.values()) <= 1e-4
    res["V0"] = {"rbar_r16_raw_recompute": rbar_r16raw, "rbar_slice_2M": Rb2M,
                 "abs_diff_raw": diff_raw, "abs_diff_rounded_ref": diff_ref,
                 "note": "R16 在档结果 JSON 为 4 位舍入; 判据 1e-6 以 checkpoint raw 复算同口径执行 (raw 对 raw 1e-9, 对舍入档 1e-4)",
                 "pass": bool(V0)}
    log(f"V0: raw复算 vs 本轮切片 最大差 {max(diff_raw.values()):.2e}; vs R16 舍入档最大差 {max(diff_ref.values()):.2e} -> {V0}")

    # ---------- V1: 2e7 全表 ----------
    spread20 = Rb20[2] - Rb20[24]
    spread2M = Rb2M[2] - Rb2M[24]
    spread200 = Rb200[2] - Rb200[24]
    res["V1"] = {"Rbar_20M": Rb20, "Rbar_2M": Rb2M, "Rbar_200k": Rb200,
                 "spread_20M": spread20, "spread_2M": spread2M, "spread_200k": spread200}
    log(f"V1 R̄@2e7: " + ", ".join(f"c={c}: {Rb20[c]:.5f}" for c in CS) + f" | spread={spread20:.5f}")

    # ---------- V2: 精确预测残差 18 检验 ----------
    rows = []
    V2 = True
    for X, Rb, vv, nn in ((200000, Rb200, v200, n200), (2000000, Rb2M, v2M, n2M), (20000000, Rb20, v20, n20)):
        for c in CS:
            d = Rb[c] - pred[f"{X}_{c}"]
            se = math.sqrt(max(vv[c], 0) / nn[c])
            tol = max(4 * se, 0.01)
            okk = abs(d) <= tol
            rows.append({"X": X, "c": c, "Rbar_meas": Rb[c], "Rbar_exact": pred[f"{X}_{c}"],
                         "resid": d, "SE": se, "tol": tol, "pass": bool(okk)})
            if not okk: V2 = False
    res["V2"] = {"rows": rows, "pass": bool(V2)}
    for row in rows:
        log(f"V2 X={row['X']:>9} c={row['c']:>2}: meas={row['Rbar_meas']:.5f} exact={row['Rbar_exact']:.5f} resid={row['resid']:+.5f} tol={row['tol']:.5f} -> {'OK' if row['pass'] else 'FAIL'}")

    # ---------- V3: B 轨迹二分 ----------
    dl_20M = math.log(math.log(X3 // 2) / math.log(X3 / 24))
    B_20M = spread20 / dl_20M
    V3_band = "E1" if 0.90 <= B_20M <= 1.30 else ("E2" if 1.35 <= B_20M <= 1.70 else "OUT")
    res["V3"] = {"spread_20M": spread20, "dlnln_20M": dl_20M, "B": B_20M, "band": V3_band,
                 "E1_band": [0.90, 1.30], "E2_band": [1.35, 1.70],
                 "prev_B_2M": spread2M / math.log(math.log(1e6) / math.log(2000000 / 24))}
    log(f"V3: B(2e6->2e7)={B_20M:.4f} -> {V3_band} (前档 B≈{res['V3']['prev_B_2M']:.4f})")

    # ---------- V4: 三锚 @2e7 ----------
    Om = {c: acc["full"][c][3] / acc["full"][c][0] for c in CS}
    V4 = True; shifts = {}
    for nm, c3, c1 in (("{6,18}-{2,10,14,22}", 6, 2), ("{12}-{4,20}", 12, 4), ("{0}-{8,16}", 24, 8)):
        sh = Om[c3] - Om[c1]
        shifts[nm] = sh
        if not (sh > R16_PREV_SHIFTS[nm] and 1.40 <= sh <= 1.50):
            V4 = False
    res["V4"] = {"shifts_20M": shifts, "prev_2M": R16_PREV_SHIFTS, "pass": bool(V4)}
    log(f"V4 三锚@2e7: " + ", ".join(f"{k}: {v:.4f}" for k, v in shifts.items()) + f" -> {V4}")

    # ---------- V5 总裁决 ----------
    res["V5"] = {"V0": bool(V0), "V1": True, "V2": bool(V2), "V3_band": V3_band, "V4": bool(V4),
                 "final": ("值域效应解析理论成立【复算一致】(R16 H4 挂账关闭)" if (V0 and V2 and V4)
                           else "如实入账(见分项)")}
    log(f"V5 总裁决: {res['V5']['final']}")
    res["log"] = log_lines
    out = RES / f"range_effect_analytic_result-{TAG}.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘 {out}（总用时 {time.time()-t0:.1f}s）")


if __name__ == "__main__":
    main()
