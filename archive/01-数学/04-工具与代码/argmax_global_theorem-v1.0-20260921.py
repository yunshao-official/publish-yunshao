# -*- coding: utf-8 -*-
"""
代数册·argmax双点全局定理化预注册判据书-v1.0-20260921 实算脚本
判据: M0-M4 (判据书 §三, 冻结文本零改动, NTFS 2026-09-21 03:15:38; M1② 首跑前更正披露于 §四)
定理 M-A..M-C 机器印证: 定点块相消 / 循环模全局最大 / argmax 双点穷举 k=2..12
"""
import json, time
import numpy as np
from pathlib import Path

RES = Path("H:/理论存档/01-数学/02-实验与数据/results")
TAG = "v1.0-20260921"
PAIRS12 = {"2|14": (0, 4), "4|16": (1, 5), "4|22": (1, 7), "10|16": (3, 5), "10|22": (3, 7),
           "2|8": (0, 2), "2|20": (0, 6), "8|14": (2, 4), "14|20": (4, 6),
           "8|20": (2, 6), "4|10": (1, 3), "16|22": (5, 7)}
DMAP = {"2|14": 2, "4|16": 1, "4|22": 1, "10|16": 1, "10|22": 1,
        "2|8": 2, "2|20": 2, "8|14": 2, "14|20": 2, "8|20": 2, "4|10": 1, "16|22": 1}
ZETA = np.exp(2j * np.pi / 8)
NG = 28800
TWO_PI = 2 * np.pi


def class_counts(k):
    """N_c = #{0<=Q<3^k: Q≡c (8)}"""
    X = 3 ** k
    return np.array([(X - 1 - c) // 8 + 1 if c <= X - 1 else 0 for c in range(8)], dtype=np.int64)


def S_c_closed(k, t):
    """S_c^{(k)}(t) = (1/8) Σ_m ζ^{mc} A_m^p A_{3m mod 8}^q; t 标量或数组; 返回 (8, len(t))"""
    t = np.atleast_1d(np.asarray(t, dtype=float))
    p, q = (k + 1) // 2, k // 2
    m = np.arange(8)
    A = (1 + np.exp(1j * t)[None, :] * (ZETA ** (-m))[:, None]
         + np.exp(2j * t)[None, :] * (ZETA ** (-2 * m))[:, None])  # (8, T)
    Pi = A ** p * A[(3 * m) % 8] ** q  # (8, T)
    zc = ZETA ** (m[:, None] * m[None, :])  # ζ^{m*c} (8c, 8m)
    S = (zc @ Pi) / 8.0
    return S


def S_c_enum(k, tval):
    """直接枚举 Q<3^k: S_c = Σ e^{i t s3(Q)}, Q≡c(8)"""
    X = 3 ** k
    Q = np.arange(X, dtype=np.int64)
    s3 = np.zeros(X, dtype=np.int64)
    tt = Q.copy()
    while tt.max() > 0:
        s3 += tt % 3
        tt //= 3
    c8 = Q % 8
    return np.array([np.exp(1j * tval * s3[c8 == c]).sum() for c in range(8)], dtype=complex)


def main():
    t0 = time.time()
    logs = []
    res = {"meta": {"script_start": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "freeze": "判据书冻结 NTFS 2026-09-21 03:15:38 (M1② 首跑前更正在案)"}}

    def log(m):
        logs.append(str(m))
        print(m, flush=True)

    # ============ M0 闭式自检 ============
    worst = 0.0
    for k in (4, 6, 7):
        for tv in (np.pi / 3, np.pi / 2, 2 * np.pi / 3, 1.0):
            Sc = S_c_closed(k, tv)[:, 0]
            Se = S_c_enum(k, tv)
            d = float(np.max(np.abs(Sc - Se)))
            worst = max(worst, d)
    M0 = bool(worst <= 1e-10)
    res["M0"] = {"worst_abs": worst, "pass": M0}
    log(f"M0: 一般 t 闭式 vs 枚举 最差 {worst:.3e} -> {M0}")

    grid = TWO_PI * np.arange(NG) / NG
    step = TWO_PI / NG
    i_pi2 = NG // 4          # 7200
    i_3pi2 = 3 * NG // 4     # 21600

    # ============ M1 argmax 双点穷举 + M3 记录 ============
    all_ok = True
    parity_ok = True
    records = {}
    for k in range(2, 13):
        S = S_c_closed(k, grid)  # (8, NG)
        N = class_counts(k)
        A = S / N[:, None]
        for name, (c, cp) in PAIRS12.items():
            d = DMAP[name]
            dphi = np.exp(1j * d * grid) * (A[c] - A[cp])
            f = np.abs(dphi)
            v = float(f.max())
            argset = np.nonzero(f >= v - 1e-12 * max(1.0, v))[0]
            ok1 = set(argset.tolist()) == {i_pi2, i_3pi2}
            v12 = float(abs(f[i_pi2] - f[i_3pi2]))
            ok3 = v12 <= 1e-12
            # 峰细化 (二分/密集): π/2 邻域 ±step 密集 2001 点
            for ic in (i_pi2, i_3pi2):
                tt = grid[ic] + np.linspace(-step, step, 2001)
                Sc = S_c_closed(k, tt)
                df = np.abs(np.exp(1j * d * tt) * (Sc[c] / N[c] - Sc[cp] / N[cp]))
                gap = float(df.max() - f[ic])
                if not (-1e-12 <= gap <= 1e-9):
                    ok_ref = False
                    break
            else:
                ok_ref = True
            # 3600 均匀半步细化点 + Runner-up 邻域
            half = (np.arange(NG) + 0.5) * step
            hs = half[::8]
            Sc = S_c_closed(k, hs)
            fh = np.abs(np.exp(1j * d * hs) * (Sc[c] / N[c] - Sc[cp] / N[cp]))
            ok_half = bool(np.all(fh < v - 1e-9))
            mask = np.ones(NG, dtype=bool)
            for ic in (i_pi2, i_3pi2):
                mask[ic - 1:ic + 2] = False
            ru = int(np.argmax(np.where(mask, f, -1)))
            tt = grid[ru] + np.linspace(-step, step, 2001)
            Sc = S_c_closed(k, tt)
            fr = np.abs(np.exp(1j * d * tt) * (Sc[c] / N[c] - Sc[cp] / N[cp]))
            ok_ru = bool(np.all(fr < v - 1e-9))
            ok = ok1 and ok3 and ok_ref and ok_half and ok_ru
            all_ok = all_ok and ok
            if not ok:
                log(f"M1 例外: k={k} {name}: argset{ok1} sym{ok3} refine{ok_ref} half{ok_half} ru{ok_ru}")
            # M3③ Runner-up 比值
            records[f"k{k}|{name}"] = {"argmax": sorted(int(x) for x in argset),
                                       "peak": v, "runnerup_ratio": float(f[ru] / v)}
        # M-A 奇偶: 12 对 c 同奇偶
        for name, (c, cp) in PAIRS12.items():
            if (c - cp) % 2 != 0:
                parity_ok = False
    M1 = bool(all_ok and parity_ok)
    ratios_late = [records[f"k12|{n}"]["runnerup_ratio"] for n in PAIRS12]
    res["M1"] = {"all_pairs_all_k_double_point": all_ok, "parity_ok": parity_ok, "pass": M1}
    res["M3"] = {"runnerup_ratio_k12": ratios_late, "records_sample":
                 {key: records[key] for key in list(records)[::60]}}
    log(f"M1: k=2..12×12对 argmax 双点 {all_ok}; c 同奇偶 {parity_ok} -> {M1}")

    # ============ M2 循环模全局最大 ============
    k = 12
    A_arr = None
    p, q = (k + 1) // 2, k // 2
    m = np.arange(8)
    Am = (1 + np.exp(1j * grid)[None, :] * (ZETA ** (-m))[:, None]
          + np.exp(2j * grid)[None, :] * (ZETA ** (-2 * m))[:, None])
    C13 = np.abs(Am[1] * Am[3])
    C26 = np.abs(Am[2] * Am[6])
    C57 = np.abs(Am[5] * Am[7])
    exact = {"C13": 3 + 2 * np.sqrt(2), "C26": 3.0, "C57": 3 + 2 * np.sqrt(2)}
    out = {}
    ok2 = True
    for nm, C in (("C13", C13), ("C26", C26), ("C57", C57)):
        vm = float(C.max())
        am = np.nonzero(C >= vm - 1e-9)[0]
        near = all(min(abs(int(ix) - i_pi2), abs(int(ix) - i_3pi2)) <= 1 for ix in am)
        err = abs(vm - exact[nm])
        ok2 = ok2 and near and err <= 1e-9
        out[nm] = {"max": vm, "err_vs_exact": err, "max_points_near_double": near}
    # 次大驻点 |g1(-√2/4)| = 3/2
    tstar = np.pi / 2 + np.arccos(-np.sqrt(2) / 4)
    C13s = float(np.abs((1 + np.exp(1j * tstar) * ZETA ** -1 + np.exp(2j * tstar) * ZETA ** -2)
                        * (1 + np.exp(1j * tstar) * ZETA ** -3 + np.exp(2j * tstar) * ZETA ** -6)))
    out["C13_secondary"] = {"t_star_value": C13s, "err_vs_1p5": abs(C13s - 1.5)}
    ok2 = ok2 and abs(C13s - 1.5) <= 1e-9
    M2 = bool(ok2)
    res["M2"] = {**out, "pass": M2}
    log(f"M2: 循环模最大值 {out} -> {M2}")

    # ============ M4 总裁决 ============
    struct = M0 and M1 and M2
    res["verdict"] = {"structure_pass": bool(struct),
                      "final": ("argmax 双点 {π/2, 3π/2} 全局定理化成立【解析循环层(M-A/M-B)+机器穷举 k=2..12 "
                                "无例外·复算一致】" if struct else "如实入账(见分项, 判负照记)")}
    log(f"M4 总裁决: {res['verdict']['final']}")
    res["log"] = logs
    res["elapsed_sec"] = round(time.time() - t0, 1)
    (RES / f"argmax_global_theorem_result-{TAG}.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    log(f"结果落盘（总用时 {time.time() - t0:.1f}s）")


if __name__ == "__main__":
    main()
