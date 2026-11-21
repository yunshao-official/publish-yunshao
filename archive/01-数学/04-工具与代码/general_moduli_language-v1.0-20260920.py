# -*- coding: utf-8 -*-
"""
代数册·语言族法则一般模数推广预注册判据书-v1.0-20260920 实算脚本
判据书冻结(NTFS): 2026-09-20 02:39:40 —— 本脚本首跑必须晚于该时刻
判据: X0-X5 (判据书 §三, 冻结文本零改动; X2 五元类数笔误与 X4 盲性口径已于首跑前更正, 修改时间在档)
核心: 深度律/负边界/联合完全分辨三定理的模数一般化 (mod 40 / mod 72 对照组)
"""
import json, math, time
import numpy as np
from pathlib import Path

RES = Path(r"H:/理论存档/01-数学/02-实验与数据/results")
TAG = "v1.0-20260920"
XMAX = 2_000_000


def carries(a, b, base, digits):
    """位窗 0..digits-1 内进位次数 (R14 在档口径)"""
    n = 0; ca = 0
    for i in range(digits):
        s = (a % base) + (b % base) + ca
        a //= base; b //= base
        if s >= base:
            n += 1; ca = 1
        else:
            ca = 0
    return n


def carries_identity(a, b, base, digits):
    n = 0
    for i in range(1, digits + 1):
        M = base ** i
        if (a % M) + (b % M) >= M:
            n += 1
    return n


def S_m(r, base, m):
    M = base ** m
    cnt = {}
    for k in range(M):
        c = carries(k, (r - k) % M, base, m)
        cnt[c] = cnt.get(c, 0) + 1
    return tuple(cnt.get(j, 0) for j in range(M + 1))


def factorize(n):
    f = {}; m = n; d = 2
    while d * d <= m:
        while m % d == 0:
            f[d] = f.get(d, 0) + 1; m //= d
        d += 1
    if m > 1: f[m] = f.get(m, 0) + 1
    return f


def classes_of(groups, sig):
    """组->签名 类划分; 返回 (类数, 同签名⟺同组的全对布尔, 类代表表)"""
    sigs = {r: sig(r) for r in groups}
    classes = set(sigs.values())
    ok = all((sigs[a] == sigs[b]) == (a == b) or (sigs[a] != sigs[b]) != (a != b) or True for a in groups for b in groups)
    # 直接判定: "同签名 ⟺ 同组" 全对
    ok = True
    for a in groups:
        for b in groups:
            if (sigs[a] == sigs[b]) != (a == b):
                ok = False; break
    return len(classes), ok, sigs


def main():
    t0 = time.time()
    first_run = time.strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"首跑时间 {first_run}（判据书冻结 2026-09-20 02:39:40 NTFS 在先；X2 笔误与 X4 口径已于首跑前更正，修改时间在档）"]
    def log(m):
        log_lines.append(str(m)); print(m, flush=True)
    res = {"meta": {"criterion_freeze_ntfs": "2026-09-20 02:39:40", "first_run": first_run}}

    # 自检: 进位实现双通道
    ident_ok = all(carries(a, b, base, m) == carries_identity(a, b, base, m)
                   for base in (2, 3, 5) for m in (1, 2, 3)
                   for a in range(base ** m) for b in range(base ** m))
    log(f"进位实现双通道 (identity vs 逐位, b∈{{2,3,5}}, m≤3 全网格): {ident_ok}")
    res["carry_dual_channel"] = bool(ident_ok)

    # X0: 暴力对照 + 组计数
    ok = True
    for n in range(2, 1001):
        bf = factorize(n)
        sf = {}
        m = n; d = 2
        while d * d <= m:
            while m % d == 0:
                sf[d] = sf.get(d, 0) + 1; m //= d
            d += 1
        if m > 1: sf[m] = sf.get(m, 0) + 1
        if bf != sf: ok = False; break
    evens = np.arange(2, XMAX + 1, 2)
    r40 = evens % 40; r72 = evens % 72
    c40 = np.bincount(r40, minlength=40)[[r for r in range(40) if r % 2 == 0]]
    c72 = np.bincount(r72, minlength=72)[[r for r in range(72) if r % 2 == 0]]
    uniform_ok = bool(c40.min() >= 49999 and c40.max() <= 50001 and c72.min() >= 27777 and c72.max() <= 27779)
    X0 = bool(ok and uniform_ok)
    res["X0"] = {"factorize_check": bool(ok), "count40_range": [int(c40.min()), int(c40.max())],
                 "count72_range": [int(c72.min()), int(c72.max())], "pass": X0}
    log(f"X0: 暴力对照 {ok}, 组计数 40:[{c40.min()},{c40.max()}] 72:[{c72.min()},{c72.max()}] -> {X0}")

    G40 = [r for r in range(40) if r % 2 == 0]
    G72 = [r for r in range(72) if r % 2 == 0]

    # X1: 因子分解 s0 类
    def vq(r, q):
        # r=0 时 v_q=+∞ -> min(v_q,3)=3 (实现层: 避免除零死循环)
        if r == 0:
            return 9
        v = 0; x = r
        while x % q == 0: x //= q; v += 1
        return v
    def s0_40(r):
        return (min(vq(r, 2), 3), 1 if r % 5 == 0 else 0)
    def s0_72(r):
        return (min(vq(r, 2), 3), min(vq(r, 3), 3))
    n1, _, sigs1 = classes_of(G40, s0_40)
    n2, _, sigs2 = classes_of(G72, s0_72)
    # 判据表 X1: "m1 恰 6 类 / m2 恰 9 类" —— 预测值判负照记
    # 实现注: 判据书推论行把 m2 的 v3 轴写成 3 值 (3x3=9), 实际 min(v3(r),3) 在偶侧可取
    # {0,1,2,3} 4 值 (r=54: v3=3; r=0: v3=+inf -> 3), 空类 2 个 -> 实类 10。
    X1 = bool(n1 == 6 and n2 == 9)
    res["X1"] = {"classes_40": n1, "pred_40": 6, "classes_72": n2, "pred_72": 9,
                 "class_lists": {"40": {str(k): sorted([r for r in G40 if sigs1[r] == k]) for k in set(sigs1.values())},
                                  "72": {str(k): sorted([r for r in G72 if sigs2[r] == k]) for k in set(sigs2.values())}},
                 "pass": X1}
    log(f"X1 因子分解: m1 类数 {n1} (预测 6); m2 类数 {n2} (预测 9 -> 判负照记, v3 轴实为 4 值) -> {X1}")

    # X2: 单素基
    def equiv_check(groups, sigs, modof):
        # 正确等价对照: 同签名 <=> 同 r mod p^v (G-A 定理口径)
        for a in groups:
            for b in groups:
                if (sigs[a] == sigs[b]) != ((a - b) % modof == 0):
                    return False
        return True
    n2b, _, sig2_40 = classes_of(G40, lambda r: S_m(r, 2, 3))
    ok2b = equiv_check(G40, sig2_40, 8)
    n5, _, sig5_40 = classes_of(G40, lambda r: S_m(r, 5, 1))
    ok5 = equiv_check(G40, sig5_40, 5)
    n3_40, _, sig3_40 = classes_of(G40, lambda r: S_m(r, 3, 1))
    split_40_b3 = sum(1 for r in G40 if S_m(r, 3, 1) != S_m(r + 40, 3, 1))
    n2_72, _, sig2_72 = classes_of(G72, lambda r: S_m(r, 2, 3))
    ok2_72 = equiv_check(G72, sig2_72, 8)
    n3_72, _, sig3_72 = classes_of(G72, lambda r: S_m(r, 3, 2))
    ok3_72 = equiv_check(G72, sig3_72, 9)
    split_72_b5 = sum(1 for r in G72 if S_m(r, 5, 1) != S_m(r + 72, 5, 1))
    # 样本侧均匀: N mod 3 (m1 对照), N mod 5 (m2 对照) 卡方
    from scipy import stats as st
    chi3 = st.chisquare(np.bincount(evens % 3, minlength=3))
    chi5 = st.chisquare(np.bincount(evens % 5, minlength=5))
    X2 = bool(n2b == 4 and ok2b and n5 == 5 and ok5 and n2_72 == 4 and ok2_72 and n3_72 == 9 and ok3_72
              and split_40_b3 == 20 and split_72_b5 == 36 and chi3.pvalue > 0.01 and chi5.pvalue > 0.01)
    res["X2"] = {"binary_40": n2b, "quinary_40": n5, "ternary_72": n3_72, "binary_72": n2_72,
                 "split_40_base3": split_40_b3, "split_72_base5": split_72_b5,
                 "chi3_p": float(chi3.pvalue), "chi5_p": float(chi5.pvalue), "pass": X2}
    log(f"X2 单素基: 40: 二元 {n2b}/五元 {n5}/底3分裂 {split_40_b3}/20; 72: 二元 {n2_72}/三元 {n3_72}/底5分裂 {split_72_b5}/36; chi p {chi3.pvalue:.3f}/{chi5.pvalue:.3f} -> {X2}")

    # X3: 联合
    nJ40, okJ40, _ = classes_of(G40, lambda r: (sig2_40[r], sig5_40[r]))
    nJ72, okJ72, _ = classes_of(G72, lambda r: S_m(r, 2, 3) + S_m(r, 3, 2))
    X3 = bool(nJ40 == 20 and okJ40 and nJ72 == 36 and okJ72)
    res["X3"] = {"joint_40": nJ40, "pairs_40": okJ40, "joint_72": nJ72, "pairs_72": okJ72, "pass": X3}
    log(f"X3 联合: m1 {nJ40}/20 全对 {okJ40}; m2 {nJ72}/36 全对 {okJ72} -> {X3}")

    # X4 已并入 X2 (split+chi)
    X4 = X2
    res["X4"] = {"pass": bool(X4), "note": "并入 X2 的分裂与卡方判据"}

    X5 = X0 and X1 and X2 and X3
    res["verdict"] = {"X0": X0, "X1": X1, "X2": X2, "X3": X3, "X4": X4,
                      "final": ("语言族法则一般模数推广成立【复算一致】(G-E/G-F/G-G+G-Ga)" if X5 else "如实入账(见分项)")}
    log(f"X5 总裁决: {res['verdict']['final']}")
    res["log"] = log_lines
    (RES / f"general_moduli_result-{TAG}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘（总用时 {time.time()-t0:.1f}s）")


if __name__ == "__main__":
    main()
