# -*- coding: utf-8 -*-
"""接触后社会冲击SIR toy（知世令"还能怎么做"2026-09-18凌晨）。判据冻结（结果前写入）。
模型：发现地外文明确认后，社会冲击传播=SIR变体（S=不知情, I=正在传播讨论, R=已消化/冷静）。
三情景：基线（自然消化）/恐慌放大（媒体β×3）/制度化引导（γ提预注册公开消化的R侧）。
参数：N=1e6, β=0.5/day(社媒), γ=0.1/day, 初始I=100(新闻源)。
主指标=恐慌峰值占比+峰值到达天数；判负=三情景无差异（模型失真）。
seed=42。输出 contact_sir_20260918.json"""
import numpy as np, json

rng = np.random.default_rng(42)
N = 1_000_000
I0 = 100
BETA, GAMMA = 0.5, 0.1  # 基线（无干预）

def sir_scn(beta, gamma, days=180):
    S, I, R = float(N-I0), float(I0), 0.0
    peak_I, t_peak = 0.0, 0
    for t in range(days):
        new_inf = beta * S * I / N
        new_rec = gamma * I
        S -= new_inf; I += new_inf - new_rec; R += new_rec
        if I > peak_I: peak_I, t_peak = I, t
    return {"峰值讨论人数": int(peak_I), "峰值天": t_peak,
            "峰值占比%": round(peak_I/N*100, 2),
            "终态未消化R": int(R)}

out = {
    "基线": sir_scn(BETA, GAMMA),
    "恐慌放大(β×3)": sir_scn(BETA*3, GAMMA),
    "制度化引导(γ×3)": sir_scn(BETA, GAMMA*3),
    "制度化引导(β×3+γ×3)": sir_scn(BETA*3, GAMMA*3),
    "冻结判据": "判负=三情景峰值占比差<5%（模型无区分度）",
}
gaps = max(v["峰值占比%"] for v in out.values() if isinstance(v, dict)) - min(v["峰值占比%"] for v in out.values() if isinstance(v, dict))
out["最大差%"] = round(gaps, 2)
out["VERDICT"] = "PASS（情景有区分度）" if gaps >= 5 else "FAIL（模型无区分度，判负照记）"

from pathlib import Path
_script_dir = Path(__file__).resolve().parent
_out = (_script_dir / "contact_sir_20260918.json").resolve()
_out.relative_to(_script_dir)  # 目录白名单硬校验：输出必须落在脚本目录内
_out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("接触冲击SIR:", out["VERDICT"])
for k, v in out.items():
    if isinstance(v, dict): print(f"  {k}: 峰值{v['峰值讨论人数']:,} @天{v['峰值天']} 占比{v['峰值占比%']}%")
print("最大差:", out["最大差%"], "%")
