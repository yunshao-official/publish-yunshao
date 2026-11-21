# -*- coding: utf-8 -*-
"""
代数册·s₂奇偶组成偏置Gelfond定量理论预注册判据书-v1.0-20260920 实算脚本
判据书冻结(NTFS): 2026-09-20 02:06:48 —— 本脚本首跑必须晚于该时刻
判据: U0-U7 (判据书 §三, 冻结文本零改动)
对象: Thue-Morse 符号 t(n)=(-1)^{s2(n)} 沿模 3 算术级数的奇偶组成偏置
定理 S1: S_c(4^k) = (2*3^{k-1}, -3^{k-1}, -3^{k-1})_c  (精确锚)
推论 S1a: bias(4^k) = 1.5 * Y^{log4(3)-1} = 1.5 * Y^{-0.207518...}
"""
import json, math, time
from pathlib import Path
from scipy import stats as st

RES = Path(r"H:/理论存档/01-数学/02-实验与数据/results")
RES.mkdir(parents=True, exist_ok=True)
TAG = "v1.0-20260920"

def s2(n):
    return bin(n).count("1")

def maxcarry(n):
    if n <= 0: return 0
    return n.bit_length() - 1 - ((n & -n).bit_length() - 1)

def main():
    t0 = time.time()
    first_run = time.strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [f"首跑时间 {first_run}（判据书冻结 2026-09-20 02:06:48 NTFS 在先）"]
    def log(m):
        log_lines.append(str(m)); print(m, flush=True)
    res = {"meta": {"criterion_freeze_ntfs": "2026-09-20 02:06:48", "first_run": first_run}}

    # ---------- U0 自检锚 ----------
    # ① 拼接恒等式抽样
    ok_splice = True
    for i in range(10000):
        q = (i * 2654435761) % 1000000
        rho = i % 8
        if s2(8 * q + rho) != s2(q) + s2(rho):
            ok_splice = False; break
    # ② 全和平衡 (n<1024=2^10)
    S1024 = sum(1 if s2(n) % 2 == 0 else -1 for n in range(1024))
    # ③ S_c(4^k) k=1..5 暴力对照
    ok_matrix = True
    for k in range(1, 6):
        Y = 4 ** k
        S = [0, 0, 0]
        for n in range(Y):
            S[n % 3] += 1 if s2(n) % 2 == 0 else -1
        pred = [2 * 3 ** (k - 1), -3 ** (k - 1), -3 ** (k - 1)]
        if S != pred:
            ok_matrix = False
            log(f"U0③ 失败 k={k}: 枚举 {S} vs 定理 {pred}")
            break
    U0 = ok_splice and (S1024 == 0) and ok_matrix
    res["U0"] = {"splice_1e4": ok_splice, "sum_1024": S1024, "matrix_k1_5": ok_matrix, "pass": U0}
    log(f"U0 自检锚: 拼接 {ok_splice} / Σt(n<1024)={S1024} / 矩阵k1-5 {ok_matrix} -> {U0}")
    if not U0:
        res["verdict"] = {"U0_fail_abort": True}
        (RES / f"s2_bias_gelfond_result-{TAG}.json").write_text(
            json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return

    # ---------- U1 精确锚 k=2..8 ----------
    u1 = {"k_list": [], "all_exact": True}
    for k in range(2, 9):
        Y = 4 ** k
        S = [0, 0, 0]
        for n in range(Y):
            S[n % 3] += 1 if s2(n) % 2 == 0 else -1
        pred = [2 * 3 ** (k - 1), -3 ** (k - 1), -3 ** (k - 1)]
        okk = (S == pred)
        u1["k_list"].append({"k": k, "Y": Y, "S": S, "pred": pred, "ok": okk})
        if not okk:
            u1["all_exact"] = False
            log(f"U1 失败 k={k}: {S} vs {pred}")
    U1 = u1["all_exact"]
    res["U1"] = {**u1, "pass": U1}
    log(f"U1 精确锚 k=2..8: {U1}")

    # ---------- 主对象: 八档 Y 的 bias ----------
    YS = [25000, 50000, 100000, 150000, 200000, 250000, 500000, 1000000]
    Ymax = max(YS)
    # 一次性扫 q < Ymax, 按 c 分桶累计 (偶计数与总数)
    cnt_even = [0, 0, 0]; cnt_all = [0, 0, 0]
    mc_samples = {0: [], 1: [], 2: []}
    bias_rows = []
    for q in range(Ymax):
        c = q % 3
        cnt_all[c] += 1
        if s2(q) % 2 == 0:
            cnt_even[c] += 1
        if q < 250000:
            mc_samples[c].append(maxcarry(q))
        if (q + 1) in YS:
            Pe = [cnt_even[c] / cnt_all[c] for c in range(3)]
            bias_rows.append({"Y": q + 1, "Pe_c0": Pe[0], "Pe_c1": Pe[1], "Pe_c2": Pe[2],
                              "bias": Pe[0] - Pe[1], "sym_gap": abs(Pe[1] - Pe[2])})
    log(f"q 扫描完成 ({time.time()-t0:.1f}s), 档数 {len(bias_rows)}")

    # 定理 S1a 点预测
    gamma_m_1 = math.log(3, 4) - 1  # = -0.207518...
    for r in bias_rows:
        r["pred_bias"] = 1.5 * (r["Y"] ** gamma_m_1)
        r["abs_dev"] = abs(r["bias"] - r["pred_bias"])
    res["bias_table"] = bias_rows
    for r in bias_rows:
        log(f"Y={r['Y']:>8}: bias={r['bias']:+.4f} pred={r['pred_bias']:+.4f} dev={r['abs_dev']:.4f} sym={r['sym_gap']:.5f}")

    # ---------- U2 幂律拟合 + 衰减比 ----------
    xs = [math.log(r["Y"]) for r in bias_rows]
    ys = [math.log(r["bias"]) for r in bias_rows]
    n = len(xs)
    mx = sum(xs) / n; my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs); sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    inter = my - slope * mx
    ss_res = sum((y - (inter + slope * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot
    b25 = next(r["bias"] for r in bias_rows if r["Y"] == 25000)
    b1M = next(r["bias"] for r in bias_rows if r["Y"] == 1000000)
    # 实现层修正（R16 G0② 先例同型）：判据书冻结文本公式"bias(10^6)/bias(25000)"与其点预测 2.150
    # 自相矛盾（bias 随 Y 衰减，该式 <1 恒出带）；按点预测语义实现为 bias(25000)/bias(10^6)。
    # 判据文本零改动，分歧如实入账。
    ratio40 = b25 / b1M
    U2 = bool((-0.26 <= slope <= -0.16) and (1.60 <= ratio40 <= 2.70))
    res["U2"] = {"slope": slope, "R2": r2, "ratio_40x": ratio40, "ratio_def": "bias(25000)/bias(1e6)",
                 "text_formula_note": "冻结文本公式 bias(1e6)/bias(25000) 与点预测 2.150 矛盾，实现按点预测语义修正（判据文本未动，R16 G0② 先例同型）",
                 "pred_slope": -0.207518, "pred_ratio": 2.150, "pass": U2}
    log(f"U2: 斜率 {slope:.4f} (预测 -0.2075, 带 [-0.26,-0.16]), 40x 衰减比 {ratio40:.3f} (预测 2.150, 带 [1.60,2.70]) -> {U2}")

    # ---------- U3 类对称 @250000 ----------
    r25 = next(r for r in bias_rows if r["Y"] == 250000)
    U3 = r25["sym_gap"] <= 0.05 * abs(r25["bias"])
    res["U3"] = {"Y": 250000, "sym_gap": r25["sym_gap"], "threshold": 0.05 * abs(r25["bias"]), "pass": U3}
    log(f"U3 类对称: |Pe1-Pe2|={r25['sym_gap']:.5f} vs 0.05*|bias|={0.05*abs(r25['bias']):.5f} -> {U3}")

    # ---------- U4 逐点对表 ----------
    devs = [r["abs_dev"] for r in bias_rows]
    U4 = all(d <= 0.04 for d in devs)
    res["U4"] = {"max_abs_dev": max(devs), "per_Y": {str(r["Y"]): r["abs_dev"] for r in bias_rows},
                 "tolerance": 0.04, "pass": U4}
    log(f"U4 逐点对表: 最大偏差 {max(devs):.4f} (容差 0.04) -> {U4}")

    # ---------- U5 X=200000 对组 s₂ KS ----------
    pairs = {"2_10": (2, 10), "4_20": (4, 20)}
    u5 = {}
    U5 = True
    for nm, (r1, r2_) in pairs.items():
        A = [s2(N) for N in range(r1, 200001, 24)]
        B = [s2(N) for N in range(r2_, 200001, 24)]
        ks = st.ks_2samp(A, B)
        u5[nm] = {"ks_p": float(ks.pvalue), "n1": len(A), "n2": len(B),
                  "mean_diff": float(abs(sum(A) / len(A) - sum(B) / len(B)))}
        okk = bool(ks.pvalue < 0.01)
        u5[nm]["separable"] = okk
        if not okk: U5 = False
    res["U5"] = {**u5, "pass": U5}
    u5_str = {k: f"p={v['ks_p']:.2e}" for k, v in u5.items()}
    log(f"U5 回顾可分 @200k: {u5_str} -> {U5}")

    # ---------- U6 maxcarry 三类两两 KS @Y=250000 ----------
    u6 = {}
    U6 = True
    cs = [0, 1, 2]
    for i in range(3):
        for j in range(i + 1, 3):
            ks = st.ks_2samp(mc_samples[cs[i]], mc_samples[cs[j]])
            u6[f"{cs[i]}_{cs[j]}"] = float(ks.pvalue)
            if ks.pvalue <= 0.01: U6 = False
    res["U6"] = {"ks_p": u6, "pass": U6}
    log(f"U6 maxcarry 三类两两 KS: {u6} -> {U6}")

    # ---------- U7 总裁决 ----------
    structure = U0 and U1 and U3 and U5 and U6
    predictive = U2 and U4
    res["verdict"] = {
        "structure_pass": bool(structure), "predictive_pass": bool(predictive),
        "U0": bool(U0), "U1": bool(U1), "U2": bool(U2), "U3": bool(U3), "U4": bool(U4),
        "U5": bool(U5), "U6": bool(U6),
        "final": bool(structure and predictive),
        "statement": ("s2 奇偶组成偏置 Gelfond/Thue-Morse 定量理论成立【复算一致】"
                      if (structure and predictive) else
                      ("结构断言过/预测带宽部分出界(判负照记)" if structure else "结构判据未全过(如实入账)"))
    }
    log(f"U7 总裁决: 结构 {structure} / 预测 {predictive} -> {res['verdict']['statement']}")
    res["log"] = log_lines
    out = RES / f"s2_bias_gelfond_result-{TAG}.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘 {out}（总用时 {time.time()-t0:.1f}s）")

if __name__ == "__main__":
    main()
