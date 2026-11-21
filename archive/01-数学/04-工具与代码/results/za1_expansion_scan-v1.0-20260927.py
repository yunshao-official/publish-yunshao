# -*- coding: utf-8 -*-
"""
ZA-1 巨量扩展扫描 v1.0（卷六判据 ZA-1/ZA-2 扩程收口）
=====================================================
任务：三段恒等式链全扫描扩展至 n<=10^6（卷六正本 v1.2 冻结判据照跑）。

三链定义（卷六 v1.2 §三，冻结口径）：
  链1: F_{n+1} = sum_{k=0..floor(n/2)} C(n-k, k)        （F_0=0, F_1=1）
  链2: d_k = d_{k-2} + d_{k-3}（d_0=1, d_1=0, d_2=1）
       与步长{2,3}爬梯计数（前推式 DP）双实现互证
  链3: d_n = sum_b C(a+b, b)（2a+3b=n，a,b>=0 整数）

验证分层（防单实现 bug）：
  L1 链2 逐点全扫：d 递推 vs 前推式 DP（两套独立代码路径，逐点精确大整数比对，0..N 全点）；
  L2 链1 F 序列全程自洽：大整数增量加法 + 双素数模校验链（2^61-1 与 2^31-1），
     每 1000 点核对大整数与模链一致（全程 1001 次核对）；
  L3 组合显式和抽样互核（独立算法=精确比值步进）：
     密集层 n=0,1000,2000,...,100000（101 点，每 1000 点一采）；
     阶梯层 n=150k,200k,300k,...,1M（10 点）——10^5 以上降密度系成本平方律
     （每点代价 ~O(n^2) 字操作，全程每 1000 点一采需数小时，按任务"超限降规模并
     如实标注"条款执行，降密度事实写入结果 JSON 与报告）；
  L4 小权重全独立层：n<=300 逐点 math.comb 第三实现比对（校验 L3 采样器本身）；
  L5 增长率：r_d(k)=d_k/d_{k-1}, r_F(k)=F_k/F_{k-1}（Decimal 60 位），
     比值 r_d/r_F -> plastic/φ；轨迹含小 k 收敛段。

检查点：每 10^5 点落盘（d_k、F_{k+1} 全量十进制串+SHA256+位长+窗口状态）。
内存纪律：全程滚动窗口（常数个大整数），不存全序列——10^6 全序列需数十 GB，不可行，
降级为滚动+位长史+检查点快照，如实标注。

运行：python za1_expansion_scan-v1.0-20260927.py [N]   （缺省 N=1000000；小 N=冒烟）
输出：za1_expansion_scan-v1.0-20260927.json / .sha256 / za1_checkpoint_k*-20260927.json
（文件名带 20260927=卷六批次日期指令；实跑日期见 executed_at 字段。）
"""
import sys, json, hashlib, time, platform, gc
from math import comb
from decimal import Decimal, getcontext

sys.set_int_max_str_digits(0)   # 3.11+ 大整数转串上限解除（F/d 达数十万位）

RESULT_DIR = r"H:/理论存档/01-数学/04-工具与代码/results"
TAG = "20260927"

P1 = (1 << 61) - 1   # 梅森素数 2305843009213693951
P2 = (1 << 31) - 1   # 梅森素数 2147483647


def chain1_sum(n):
    """Σ_{k=0..⌊n/2⌋} C(n-k,k)，精确比值步进：C(n-k-1,k+1)=C(n-k,k)·(n-2k)(n-2k-1)/((n-k)(k+1))"""
    s = t = 1
    k = 0
    half = n >> 1
    nmk = n        # n-k
    kp1 = 1        # k+1
    while k < half:
        t = t * ((n - 2 * k) * (n - 2 * k - 1)) // (nmk * kp1)
        s += t
        k += 1
        nmk -= 1
        kp1 += 1
    return s


def chain3_sum(n):
    """Σ_b C(a+b,b)（2a+3b=n）。
    起项 b0=n%2（奇偶门），t0 = C(a0+b0,b0)（b0∈{0,1} 时为 1 或 a0+1，直接算）。
    步进 b→b+2（a→a-3）：t' = t·a(a-1)(a-2) / ((a+b)(b+1)(b+2))，整除精确。"""
    b = n & 1
    if 3 * b > n:
        return 0 if n else 1  # n=0 → C(0,0)=1
    a = (n - 3 * b) >> 1
    t = 1 if b == 0 else a + 1
    s = t
    third = n // 3
    while b + 2 <= third:
        t = t * (a * (a - 1) * (a - 2)) // ((a + b) * (b + 1) * (b + 2))
        a -= 3
        b += 2
        s += t
    return s


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 1_000_000
    CKPT = 100_000 if N >= 100_000 else max(1, N // 5)
    DENSE_LIMIT = min(100_000, N)
    LADDER = sorted(x for x in [150_000, 200_000, 300_000, 400_000, 500_000,
                                600_000, 700_000, 800_000, 900_000, 1_000_000] if x <= N)
    RATIO_PTS = sorted(x for x in [10, 20, 50, 100, 200, 500, 1_000, 10_000,
                                   100_000, 300_000, 1_000_000] if x <= N)
    LADDER_SET = set(LADDER)
    RATIO_SET = set(RATIO_PTS)

    t0 = time.time()
    gc.disable()

    # ---- 滚动状态 ----
    fa, fb = 0, 1          # F_k, F_{k+1}（迭代开始时）
    fpm = 1                # F_{k-1}（F_{-1}=1 标准延拓）
    faM, fbM = 0, 1        # F_k, F_{k+1} mod P1
    fa2, fb2 = 0, 1        # mod P2
    dA = dB = dC = None    # d_{k-3}, d_{k-2}, d_{k-1}（k>=3 起）
    ring = [1, 0, 0]       # 前推式 DP 环（步长{2,3}，push 风格）

    mismatches_chain2 = []          # (k, d, w) 反例照记（预期空）
    mod_checks = 0
    mod_fail = []
    bl_hist = []                    # 每1000点 (k, F位长, d位长)
    samples = []                    # 组合和互核记录
    small_all_ok = True             # n<=300 独立层
    ratio_cap = {}                  # k -> (d_k, d_{k-1}, F_k, F_{k-1})
    checkpoints = []

    def do_checkpoint(k, dk, fkp1):
        d_s, f_s = str(dk), str(fkp1)
        fn = f"{RESULT_DIR}/za1_checkpoint_k{k}-{TAG}.json"
        with open(fn, "w", encoding="utf-8") as fh:
            json.dump({
                "k": k,
                "d_k_decimal": d_s, "d_k_digits": len(d_s), "d_k_sha256": sha(d_s),
                "F_kp1_decimal": f_s, "F_kp1_digits": len(f_s), "F_kp1_sha256": sha(f_s),
                "mod_P1_F": fbM, "mod_P2_F": fb2,
                "elapsed_s": round(time.time() - t0, 2),
            }, fh, ensure_ascii=False, indent=1)
        checkpoints.append({"k": k, "d_digits": len(d_s), "F_digits": len(f_s),
                            "d_sha256": sha(d_s), "F_sha256": sha(f_s),
                            "file": f"za1_checkpoint_k{k}-{TAG}.json"})

    for k in range(N + 1):
        # ---- 链2 d_k ----
        if k < 3:
            dk = (1, 0, 1)[k]
            if k == 2:
                dA, dB, dC = 1, 0, 1   # 窗口就位：k=3 时 = (d0,d1,d2)
        else:
            dk = dB + dA
        # ---- 前推式 DP（步长{2,3} 爬梯，独立代码路径）----
        ki = k % 3
        w = ring[ki]
        j = ki + 2
        if j >= 3:
            j -= 3
        ring[j] += w
        ring[ki] = w
        if dk != w:
            mismatches_chain2.append([k, str(dk)[:80], str(w)[:80]])

        # ---- 增长率采集（移窗前）----
        if k in RATIO_SET:
            ratio_cap[k] = (dk, dC if k >= 1 else None, fa, fpm)

        # ---- L2 模链核对（每1000点）----
        if k % 1000 == 0:
            if fb % P1 != fbM or fb % P2 != fb2:
                mod_fail.append(k)
            mod_checks += 1
            bl_hist.append([k, fb.bit_length(), dk.bit_length()])

        # ---- L3 组合显式和互核 ----
        if (k % 1000 == 0 and k <= DENSE_LIMIT) or k in LADDER_SET:
            t1 = time.time()
            s1 = chain1_sum(k)
            ok1 = (s1 == fb)
            s3 = chain3_sum(k)
            ok3 = (s3 == dk)
            samples.append({"n": k, "chain1_ok": ok1, "chain3_ok": ok3,
                            "chain1_digits": len(str(s1)), "chain3_digits": len(str(s3)),
                            "sec": round(time.time() - t1, 3)})

        # ---- L4 n<=300 第三实现全独立层 ----
        if k <= 300:
            s1c = sum(comb(k - i, i) for i in range(k // 2 + 1))
            if s1c != fb:
                small_all_ok = False
                samples.append({"n": k, "layer": "L4", "chain1_mathcomb_mismatch": True})
            s3c = sum(comb((k - 3 * b) // 2 + b, b)
                      for b in range(k % 2, k // 3 + 1, 2))
            if s3c != dk:
                small_all_ok = False
                samples.append({"n": k, "layer": "L4", "chain3_mathcomb_mismatch": True})

        # ---- 检查点 ----
        if k % CKPT == 0:
            do_checkpoint(k, dk, fb)

        # ---- 移窗 ----
        if k >= 3:
            dA, dB, dC = dB, dC, dk
        fpm, fa, fb = fa, fb, fa + fb
        n1 = faM + fbM
        if n1 >= P1:
            n1 -= P1
        faM, fbM = fbM, n1
        n2 = fa2 + fb2
        if n2 >= P2:
            n2 -= P2
        fa2, fb2 = fb2, n2

    # ================= 结果组装 =================
    gc.enable()
    elapsed = time.time() - t0

    # 终值：循环结束后 dk=d_N（末次迭代留存）；末次移窗后 (fa,fb)=(F_{N+1},F_{N+2})，取 fa=F_{N+1}
    d_final, F_final = dk, fa
    d_s, F_s = str(d_final), str(F_final)

    # ---- 增长率（Decimal 60 位）----
    getcontext().prec = 60
    # plastic 数：x^3=x+1 唯一实根（整数牛顿→Decimal 60 位）
    x = Decimal(4) / Decimal(3)
    for _ in range(40):
        x = x - (x ** 3 - x - 1) / (3 * x ** 2 - 1)
    plastic = +x
    phi = (1 + Decimal(5).sqrt()) / 2
    ref_ratio = plastic / phi

    traj = []
    for k in RATIO_PTS:
        dk_, dk1, Fk_, Fk1 = ratio_cap[k]
        if dk1 is None or Fk1 == 0:
            continue
        rd = Decimal(dk_) / Decimal(dk1)
        rF = Decimal(Fk_) / Decimal(Fk1)
        traj.append({"k": k,
                     "r_d": str(+rd), "r_F": str(+rF),
                     "ratio": str(+(rd / rF)),
                     "r_d_minus_plastic": str(+(rd - plastic)),
                     "r_F_minus_phi": str(+(rF - phi))})

    k_hi = RATIO_PTS[-1]
    dk_, dk1, Fk_, Fk1 = ratio_cap[k_hi]
    r_d_hi = Decimal(dk_) / Decimal(dk1)
    r_F_hi = Decimal(Fk_) / Decimal(Fk1)
    ratio_hi = r_d_hi / r_F_hi

    result = {
        "task": "ZA-1 巨量扩展 + ZA-2 补充检验（卷六判据扩程收口）",
        "script": "za1_expansion_scan-v1.0-20260927.py",
        "version": "1.0", "batch_date": TAG,
        "executed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "N": N,
        "frozen_criteria_ref": "卷六 v1.2 §三/§五（ZA-1 三段恒等式链；ZA-2 d_k 同族性）",
        "chain1": {
            "identity": "F_{n+1}=Σ_{k≤⌊n/2⌋}C(n-k,k)",
            "full_range_generated": N + 2,
            "mod_full_checks": {"primes": [str(P1), str(P2)], "checks": mod_checks,
                                "fail_points": mod_fail},
            "dense_samples": sum(1 for s in samples if "chain1_ok" in s and s["n"] <= DENSE_LIMIT),
            "ladder_samples": sorted(s["n"] for s in samples if "chain1_ok" in s and s["n"] > DENSE_LIMIT),
            "mismatches": [s for s in samples if s.get("chain1_ok") is False],
        },
        "chain2": {
            "identity": "d_k=d_{k-2}+d_{k-3} ⟺ 步长{2,3}爬梯数（前推式DP独立实现）",
            "points_compared": N + 1,
            "mismatches": mismatches_chain2,
        },
        "chain3": {
            "identity": "d_n=Σ_b C(a+b,b)（2a+3b=n）",
            "dense_samples": sum(1 for s in samples if "chain3_ok" in s and s["n"] <= DENSE_LIMIT),
            "ladder_samples": sorted(s["n"] for s in samples if "chain3_ok" in s and s["n"] > DENSE_LIMIT),
            "mismatches": [s for s in samples if s.get("chain3_ok") is False],
        },
        "layer4_small_independent": {
            "range": "n=0..300 逐点 math.comb 第三实现",
            "all_pass": small_all_ok,
        },
        "sampling_density_note": (
            "密集层=每1000点至 min(1e5,N)；其上按任务'超限降规模并如实标注'条款降为"
            "几何阶梯（150k..1M 共≤10点）——显式组合和每点代价~O(n²)字操作，"
            "全程每1000点一采需小时级，不经济；链2仍为 0..N 逐点全扫，链1 F 序列全程有双素数模链校验。"),
        "growth": {
            "definition": "r_d=d_k/d_{k-1}→plastic；r_F=F_k/F_{k-1}→φ；ratio→plastic/φ",
            "plastic_60d": str(plastic),
            "phi_60d": str(phi),
            "plastic_over_phi_60d": str(ref_ratio),
            "trajectory": traj,
            "at_k_max": {"k": k_hi,
                         "ratio": str(+ratio_hi),
                         "equals_ref_to_50d": str(+ratio_hi)[:52] == str(+ref_ratio)[:52]},
            "at_1e5": next((t["ratio"] for t in traj if t["k"] == 100_000), None),
            "at_1e6": next((t["ratio"] for t in traj if t["k"] == 1_000_000), None),
        },
        "finals": {
            "d_N": {"digits": len(d_s), "bit_length": d_final.bit_length(),
                    "sha256_decimal": sha(d_s), "head30": d_s[:30], "tail30": d_s[-30:]},
            "F_Np1": {"digits": len(F_s), "bit_length": F_final.bit_length(),
                      "sha256_decimal": sha(F_s), "head30": F_s[:30], "tail30": F_s[-30:]},
        },
        "checkpoints": checkpoints,
        "bitlength_history_head": bl_hist[:5],
        "bitlength_history_tail": bl_hist[-5:],
        "counterexample_verdict": "零反例" if (not mismatches_chain2 and not mod_fail
                                               and small_all_ok
                                               and not [s for s in samples if s.get("chain1_ok") is False]
                                               and not [s for s in samples if s.get("chain3_ok") is False]) else "出现反例·见明细",
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(),
                        "machine": platform.machine()},
        "elapsed_s": round(elapsed, 1),
    }

    out = f"{RESULT_DIR}/za1_expansion_scan-v1.0-{TAG}.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    with open(out + ".sha256", "w", encoding="utf-8") as fh:
        fh.write(sha(open(out, encoding="utf-8").read()) + "  " + out.split("/")[-1] + "\n")

    print("=== ZA-1 扩展扫描完成 ===")
    print(f"N={N}  用时 {elapsed:.1f}s")
    print(f"链2逐点比对: {N+1} 点, 反例 {len(mismatches_chain2)}")
    print(f"链1模链核对: {mod_checks} 次, 失败 {len(mod_fail)}")
    print(f"组合和互核: 密集 {result['chain1']['dense_samples']} + 阶梯 {len(LADDER)} 点, "
          f"链1反例 {len(result['chain1']['mismatches'])}, 链3反例 {len(result['chain3']['mismatches'])}")
    print(f"L4 独立层(<=300): {'全过' if small_all_ok else '有反例'}")
    print(f"d_{N}: {len(d_s)} 位, sha256={result['finals']['d_N']['sha256_decimal'][:16]}...")
    print(f"F_{N+1}: {len(F_s)} 位, sha256={result['finals']['F_Np1']['sha256_decimal'][:16]}...")
    print(f"增长率比 @k={k_hi}: {str(+ratio_hi)[:30]}")
    print(f"参考 plastic/φ   : {str(ref_ratio)[:30]}")
    print(f"判决: {result['counterexample_verdict']}")
    print(f"输出: {out}")


if __name__ == "__main__":
    main()
