# -*- coding: utf-8 -*-
"""
因果检查判读脚本 analyze_causal.py（天工开物 第十八批 L3 · 知世令"全部默认授权，一路做到因果控制和检查"）
==================================================================================
功能：对任意被测系统执行"干预式因果判定"——材料元件通/断/反向为干预变量，
      效果量时间序列为响应，自动判输出因果三判语。
判据（已冻结，运行前不得修改）：
  J1 开关比 >3:1（燧人因果链判定原样）= |mean(通) - mean(断)| / max(σ_noise, eps)
  J2 效应显著性 5σ：通/断均值差 > 5×合并标准差
  J3 滞后方向一致：互相关峰值滞后 ≥0（效应不超前于干预）
三判语：CAUSAL（J1+J2+J3 全过）/ NOT_CAUSAL（J2 不过）/ INDETERMINATE（其余）
用法：
  python analyze_causal.py data.csv        # 数据列: t, state(+1通/-1反向/0断), effect
  python analyze_causal.py --selftest      # 合成数据自测（交付验证）
诚实口径：干预式因果判定=因果推断金标准方法；本脚本只判"干预→效应"因果性，
不解释机制；全部【未验证】待实测。
"""
import json
import sys
import csv
import numpy as np

SWITCH_RATIO_MIN = 3.0
SIGMA_MIN = 5.0

def load_csv(path):
    t, state, effect = [], [], []
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t.append(float(row["t"]))
            state.append(float(row["state"]))
            effect.append(float(row["effect"]))
    return np.array(t), np.array(state), np.array(effect)

def judge(t, state, effect):
    on = effect[state == 1]
    off = effect[state == 0]
    rev = effect[state == -1]
    if len(on) < 3 or len(off) < 3:
        return {"verdict": "数据不足（通/断各需≥3 点）"}
    mean_on, mean_off = float(np.mean(on)), float(np.mean(off))
    std_all = float(np.std(off)) if len(off) > 1 else 1e-12
    sigma = max(std_all, 1e-12)
    # J1 开关比
    switch_ratio = abs(mean_on - mean_off) / sigma
    j1 = switch_ratio > SWITCH_RATIO_MIN
    # J2 5σ 显著性（合并标准差）
    s_pooled = np.sqrt(((np.var(on) * (len(on)-1)) + (np.var(off) * (len(off)-1))) /
                       max(len(on) + len(off) - 2, 1)) if len(on) > 1 and len(off) > 1 else sigma
    significance = abs(mean_on - mean_off) / max(s_pooled, 1e-12)
    j2 = significance > SIGMA_MIN
    # J3 滞后方向（互相关，效果不超前于干预）
    lag_ok = True
    lag = None
    if len(t) > 10:
        s_norm = (state - np.mean(state)) / (np.std(state) + 1e-12)
        e_norm = (effect - np.mean(effect)) / (np.std(effect) + 1e-12)
        dt = np.median(np.diff(t)) if len(t) > 1 else 1.0
        lags = np.arange(-len(t)//4, len(t)//4 + 1)
        cc = []
        for L in lags:
            if L >= 0:
                cc.append(np.corrcoef(s_norm[:len(s_norm)-L], e_norm[L:])[0, 1] if L < len(t) else 0)
            else:
                cc.append(np.corrcoef(s_norm[-L:], e_norm[:len(e_norm)+L])[0, 1])
        lag = int(lags[int(np.argmax(cc))]) * dt
        lag_ok = lag >= 0
    j3 = bool(lag_ok)
    # 反向臂（若有）：切断模式应使效应反向或消失
    rev_info = None
    if len(rev) >= 3:
        rev_info = {"mean_effect_reverse": float(np.mean(rev)),
                    "reverse_opposes_on": bool(np.mean(rev) < mean_on)}
    verdict = ("CAUSAL" if (j1 and j2 and j3) else
               "NOT_CAUSAL" if not j2 else "INDETERMINATE")
    return {"verdict": verdict,
            "J1_开关比": {"value": switch_ratio, "threshold": SWITCH_RATIO_MIN, "pass": j1},
            "J2_显著性": {"sigma_count": significance, "threshold": SIGMA_MIN, "pass": j2},
            "J3_滞后": {"lag_s": lag, "pass": j3},
            "反向臂": rev_info,
            "mean_on": mean_on, "mean_off": mean_off,
            "n_on": len(on), "n_off": len(off), "n_reverse": len(rev)}

def selftest():
    """合成数据自测：真因果信号应判 CAUSAL；纯噪声应判 NOT_CAUSAL。"""
    rng = np.random.default_rng(42)
    # 场景1：真因果（通=+10μV 效应，断=0，噪声 1μV）
    t1, s1, e1 = [], [], []
    t0 = 0.0
    for k in range(60):
        st = 1.0 if (k // 5) % 2 == 0 else 0.0
        e = (10.0 if st == 1 else 0.0) + rng.normal(0, 1.0)
        t1.append(t0); s1.append(st); e1.append(e)
        t0 += 1.0
    r1 = judge(np.array(t1), np.array(s1), np.array(e1))
    # 场景2：纯噪声（无因果）
    t2 = np.arange(60.0)
    s2 = np.array([1.0 if (k // 5) % 2 == 0 else 0.0 for k in range(60)])
    e2 = rng.normal(0, 1.0, 60)
    r2 = judge(t2, s2, e2)
    ok = r1["verdict"] == "CAUSAL" and r2["verdict"] == "NOT_CAUSAL"
    return {"自测_真因果场景": r1, "自测_纯噪声场景": r2, "自测通过": ok}

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        res = selftest()
        print(json.dumps(res, ensure_ascii=False, indent=1, default=float))
        sys.exit(0 if res["自测通过"] else 1)
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    t, s, e = load_csv(sys.argv[1])
    print(json.dumps(judge(t, s, e), ensure_ascii=False, indent=1, default=float))
