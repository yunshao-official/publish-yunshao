# -*- coding: utf-8 -*-
"""
ZA-2 补充检验 v1.0（卷六判据 ZA-2 扩程收口 · Hoffman 计数扩展 + 浅对角线族结构层）
================================================================================
任务（卷六正本 v1.2 + 路线A主件 v1.0 冻结口径照跑）：
  ① Hoffman 计数扩展至权重≤300：对每个 k=0..300，
     d_k（递推 d_k=d_{k-2}+d_{k-3}，d0=1,d1=0,d2=1）
     与 Hoffman 基生成律组合计数（路线A口径：k=2m+3b 的 Σ_b C(m+b,b)）
     双轨互证，逐权重全过；锚点：d_18=65、Σ_{k=1..18}d_k=263（卷六冻结值）。
  ② 浅对角线族结构层：抽查 3 条其他斜率族 {1,3},{2,5},{3,4}（非{1,2}/{2,3}）：
     DP（g_n=g_{n-a}+g_{n-b}）与显式组合和（Σ C(p+q,q)，ap+bq=n）互证，
     n≤120 全点 + 15 个大样本点至 10^4；另加 n≤22 暴力枚举第三实现；
     主导根估值（g_n^{1/n}，Decimal）与路线A v1.0 §一 族表 ρ 对照（n=5000/10^4 双点看收敛）。
  ③ 序列锚点：路线A v1.0 §一 表中 5 族 n=1..12 序列逐项复核。
输出：za2_hoffman_families-v1.0-20260927.json / .sha256
（文件名带 20260927=卷六批次日期指令；实跑日期见 executed_at。）
"""
import sys, json, hashlib, time, platform
from math import comb
from decimal import Decimal, getcontext

sys.set_int_max_str_digits(0)   # 3.11+ 大整数转串上限解除

RESULT_DIR = r"H:/理论存档/01-数学/04-工具与代码/results"
TAG = "20260927"


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def d_seq(K):
    """Zagier 维数序列 d_0..d_K（递推实现）"""
    ds = [1, 0, 1]
    for k in range(3, K + 1):
        ds.append(ds[k - 2] + ds[k - 3])
    return ds[:K + 1]


def hoffman_count(k):
    """Hoffman 基生成律组合计数（路线A v1.0 §二口径）：Σ_b C(m+b,b)，2m+3b=k"""
    s = 0
    for b in range(k % 2, k // 3 + 1, 2):
        m = (k - 3 * b) // 2
        s += comb(m + b, b)
    return s


def family_dp(a, b, N):
    g = [1] + [0] * N
    for n in range(1, N + 1):
        v = 0
        if n >= a:
            v += g[n - a]
        if n >= b:
            v += g[n - b]
        g[n] = v
    return g


def family_explicit(a, b, n):
    """步长{a,b} 显式组合和：Σ_q C(p+q,q)，p·a+q·b=n（q≡n·b⁻¹ mod a，步长 a）"""
    q0 = (n * pow(b, -1, a)) % a
    s = 0
    for q in range(q0, n // b + 1, a):
        p = (n - b * q) // a
        s += comb(p + q, q)
    return s


def brute_compositions(a, b, n):
    """暴力枚举：步长{a,b} 爬 n 阶方式数（第三实现，n≤22 用）"""
    if n == 0:
        return 1
    total = 0
    if n >= a:
        total += brute_compositions(a, b, n - a)
    if n >= b:
        total += brute_compositions(a, b, n - b)
    return total


def root_estimate(g_n, n, prec=30):
    getcontext().prec = prec
    return +(Decimal(g_n).ln() / n).exp()


def main():
    t0 = time.time()
    result = {"task": "ZA-2 补充检验：Hoffman 计数扩展≤300 + 浅对角线族结构层抽查",
              "script": "za2_hoffman_families-v1.0-20260927.py",
              "version": "1.0", "batch_date": TAG,
              "executed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
              "frozen_criteria_ref": "卷六 v1.2 §五 ZA-2；路线A主件 v1.0 §一/§二"}

    # ---------- ① Hoffman ≤300 ----------
    K = 300
    ds = d_seq(K)
    hoff_fail = []
    for k in range(K + 1):
        if hoffman_count(k) != ds[k]:
            hoff_fail.append(k)
    d18 = ds[18]
    cum18 = sum(ds[1:19])
    d300 = ds[300]
    d300_s = str(d300)
    result["hoffman_300"] = {
        "range": f"k=0..{K}",
        "identity": "d_k(递推) == Σ_b C(m+b,b)（2m+3b=k，Hoffman基生成律组合计数·路线A口径）",
        "points": K + 1, "mismatches": hoff_fail,
        "anchors": {"d_18": d18, "d_18_expected": 65, "d_18_ok": d18 == 65,
                    "sum_d1_to_d18": cum18, "sum_expected": 263, "cum_ok": cum18 == 263},
        "d_300": {"digits": len(d300_s), "sha256_decimal": sha(d300_s),
                  "head20": d300_s[:20], "tail20": d300_s[-20:],
                  "magnitude_estimate": f"~10^{len(d300_s)-1}",
                  "note": "任务书估 ~10^41；实算量级见 digits 字段，如实记录"},
    }

    # ---------- ② 三条其他斜率族 ----------
    FAMILIES = [(1, 3), (2, 5), (3, 4)]
    TABLE_RHO = {(1, 3): "1.465571", (2, 5): "1.236506", (3, 4): "1.220744"}
    TABLE_SEQ = {(1, 3): [1, 1, 2, 3, 4, 6, 9, 13, 19, 28, 41, 60],
                 (2, 5): [0, 1, 0, 1, 1, 1, 2, 1, 3, 2, 4, 4],
                 (3, 4): [0, 0, 1, 1, 0, 1, 2, 1, 1, 3, 3, 2]}
    ANCHOR_SEQ = {(1, 2): [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233],
                  (2, 3): [0, 1, 1, 1, 2, 2, 3, 4, 5, 7, 9, 12]}
    N = 10_000
    big_points = [200, 300, 500, 750, 1000, 1500, 2000, 3000, 4000,
                  5000, 6000, 7000, 8000, 9000, 10000]
    fam_report = {}
    for (a, b) in FAMILIES:
        g = family_dp(a, b, N)
        # 序列锚点（路线A v1.0 §一 表，n=1..12）
        seq_ok = g[1:13] == TABLE_SEQ[(a, b)]
        # 递推自检（全点；n=0 为种子位 g0=1 按定义，不属递推管辖，自 n=1 起）
        rec_ok = all(g[n] == ((g[n - a] if n >= a else 0) + (g[n - b] if n >= b else 0))
                     for n in range(1, N + 1))
        # 显式组合和互证：n≤120 全点 + 大样本点
        pts = list(range(0, 121)) + big_points
        expl_fail = []
        for n in pts:
            if family_explicit(a, b, n) != g[n]:
                expl_fail.append(n)
        # 暴力第三实现 n≤22
        brute_fail = [n for n in range(0, 23) if brute_compositions(a, b, n) != g[n]]
        # 主导根估值（n=5000/10^4 双点收敛观察）
        r5 = root_estimate(g[5000], 5000)
        r10 = root_estimate(g[10000], 10000)
        fam_report[f"{{{a},{b}}}"] = {
            "dp_vs_explicit_points": len(pts), "explicit_mismatches": expl_fail,
            "brute_check_range": "n=0..22", "brute_mismatches": brute_fail,
            "recurrence_selfcheck_pass": rec_ok,
            "table_sequence_n1_12_ok": seq_ok,
            "table_rho": TABLE_RHO[(a, b)],
            "rho_est_n5000": str(r5)[:12], "rho_est_n10000": str(r10)[:12],
        }
    # {1,2}/{2,3} 锚点族序列复核
    g12 = family_dp(1, 2, 12)
    g23 = family_dp(2, 3, 12)
    result["families"] = fam_report
    result["anchor_families"] = {
        "{1,2}_Fibonacci_seq_ok": g12[1:13] == ANCHOR_SEQ[(1, 2)],
        "{2,3}_MZV_dim_seq_ok": g23[1:13] == ANCHOR_SEQ[(2, 3)],
    }

    result["counterexample_verdict"] = (
        "零反例" if (not hoff_fail and all(v["explicit_mismatches"] == [] and v["brute_mismatches"] == []
                                           and v["recurrence_selfcheck_pass"] and v["table_sequence_n1_12_ok"]
                                           for v in fam_report.values())
                     and result["anchor_families"]["{1,2}_Fibonacci_seq_ok"]
                     and result["anchor_families"]["{2,3}_MZV_dim_seq_ok"]) else "出现反例·见明细")
    result["environment"] = {"python": sys.version.split()[0], "platform": platform.platform()}
    result["elapsed_s"] = round(time.time() - t0, 1)

    out = f"{RESULT_DIR}/za2_hoffman_families-v1.0-{TAG}.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    with open(out + ".sha256", "w", encoding="utf-8") as fh:
        fh.write(sha(open(out, encoding="utf-8").read()) + "  " + out.split("/")[-1] + "\n")

    print("=== ZA-2 补充检验完成 ===")
    print(f"Hoffman≤300: {K+1} 点, 反例 {len(hoff_fail)}; d18={d18}(应65), Σ1..18={cum18}(应263)")
    print(f"d_300: {len(d300_s)} 位, 量级 ~10^{len(d300_s)-1}")
    for key, v in fam_report.items():
        print(f"族 {key}: 显式互证 {v['dp_vs_explicit_points']}点 反例{len(v['explicit_mismatches'])}, "
              f"暴力n≤22 反例{len(v['brute_mismatches'])}, 递推自检={v['recurrence_selfcheck_pass']}, "
              f"表序列={v['table_sequence_n1_12_ok']}, 表ρ={v['table_rho']}, "
              f"估值n=10^4={v['rho_est_n10000']}")
    print(f"锚点族: {result['anchor_families']}")
    print(f"判决: {result['counterexample_verdict']}")
    print(f"输出: {out}")


if __name__ == "__main__":
    main()
