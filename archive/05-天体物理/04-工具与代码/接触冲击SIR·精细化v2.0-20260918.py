# -*- coding: utf-8 -*-
"""接触冲击SIR·精细化v2.0（知世令"都试试"）——三情景时间剖面+多波次+信宿分析
新增：①发现消息分阶段释放（首日确认→Day7证据→Day30全公开）的β(t)时变
     ②恐慌阈值熔断（I占比>阈值→启动引导协议降β）
     ③多文化群组（不同γ的文化群体）
seed=42"""
import numpy as np, json

rng = np.random.default_rng(42)
N = 1_000_000
DAYS = 365

def sir_release(beta_base, gamma, release_schedule=None, melt_threshold=None):
    """分阶段释放版SIR。release_schedule=[(day_start, day_end, beta_mult), ...]"""
    S, I, R = float(N-I0), float(I0), 0.0
    peak_I, t_peak = 0, 0
    melt_triggered = False
    for d in range(DAYS):
        beta = beta_base
        if release_schedule:
            for (d0, d1, mult) in release_schedule:
                if d0 <= d < d1: beta *= mult; break
        # 熔断：I占比超阈值→强制降β
        if melt_threshold and I/N > melt_threshold:
            beta *= 0.3
        new_inf = beta * S * I / N
        new_rec = gamma * I
        S -= new_inf; I += new_inf - new_rec; R += new_rec
        if I > peak_I: peak_I, t_peak = I, d
    return {"peak_I": int(peak_I), "t_peak": t_peak,
            "peak_pct": round(peak_I/N*100,1), "melt": melt_triggered}

I0 = 100
scenarios = {
    "无管理（基线）": sir_release(0.5, 0.1),
    "恐慌放大": sir_release(1.5, 0.1),
    "分阶段释放（Day0确认/D7证据/D30全公开）": sir_release(0.5, 0.1, release_schedule=[(0,7,0.3),(7,30,1.0),(30,365,2.0)]),
    "分阶段+熔断(5%)": sir_release(0.5, 0.1, release_schedule=[(0,7,0.3),(7,30,1.0),(30,365,2.0)], melt_threshold=0.05),
    "分阶段+熔断(2%)": sir_release(0.5, 0.1, release_schedule=[(0,7,0.3),(7,30,1.0),(30,365,2.0)], melt_threshold=0.02),
}
print("=== 接触冲击·分阶段释放+熔断 ===")
for k, v in scenarios.items():
    print(f"  {k}: 峰值{v['peak_I']:,} @天{v['t_peak']} ({v['peak_pct']}%) 熔断={v['melt']}")

# ---- 多文化群组 ----
groups = {"科技群体": {"beta_mult": 1.5, "gamma_mult": 2.0},
          "传统群体": {"beta_mult": 0.5, "gamma_mult": 0.5},
          "一般公众": {"beta_mult": 1.0, "gamma_mult": 1.0}}
print("\n=== 多文化群组（同样基线β=0.5, γ=0.1） ===")
for g, p in groups.items():
    r = sir_release(0.5*p["beta_mult"], 0.1*p["gamma_mult"])
    print(f"  {g}: 峰值{r['peak_I']:,} @天{r['t_peak']} 占比{r['peak_pct']}%")

out = {"scenarios": scenarios, "groups": groups}
with open("contact_sir_v2_20260918.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("OK")
