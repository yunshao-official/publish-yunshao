# -*- coding: utf-8 -*-
"""
V3-∇ 梯度实测 · 数据判读脚本（开工包组件，知世 2026-09-15 批"全部做"）
==================================================================================
用法：实验数据落盘为 CSV（同目录 v3grad_data.csv），本脚本自动出判。
CSV 列：eb(V·T/m), force(N), beam_config("三频组"/"单频"/"双频"/"关闭"), phase("正向"/"反向")
判据（已冻结，运行前不得修改）：
  J1 线性：三频组正向 F-⟨E·B⟩ 线性回归 R²>0.99
  J2 对照：关闭档 |F| < 5σ_noise
  J3 奇性：相位反向 → 力反号，比值 ∈ [-1.2,-0.8]
  J4 体系特异性：三频组斜率 / max(单频,双频) 斜率 > 10
  J5 出判：J1-J4 全过 → 报告 ∇θ·k 及不确定度；J4 不过 → 信号非体系特异；
     全零 → ∇θ·k 上限 = 5σ/((e²/h)·⟨E·B⟩)
"""
import json
import numpy as np
import csv, os, sys

E2H = 3.874e-5
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "v3grad_data.csv")

def load():
    if not os.path.exists(PATH):
        print("未找到", PATH, "——落盘后重跑本脚本。列：eb,force,beam_config,phase")
        sys.exit(0)
    rows = list(csv.DictReader(open(PATH, encoding="utf-8")))
    return rows

def judge(rows):
    out = {}
    def sel(cfg, ph="正向"):
        return np.array([float(r["eb"]) for r in rows if r["beam_config"] == cfg and r["phase"] == ph]), \
               np.array([float(r["force"]) for r in rows if r["beam_config"] == cfg and r["phase"] == ph])
    eb3, f3 = sel("三频组")
    ebo, fo = sel("单频") + sel("双频")
    ebo = np.concatenate([np.atleast_1d(sel("单频")[0]), np.atleast_1d(sel("双频")[0])])
    fo = np.concatenate([np.atleast_1d(sel("单频")[1]), np.atleast_1d(sel("双频")[1])])
    ebz, fz = sel("关闭")
    # J1 线性
    if len(eb3) >= 3:
        k, b = np.polyfit(eb3, f3, 1)
        pred = k * eb3 + b
        ss_res = np.sum((f3 - pred) ** 2)
        ss_tot = np.sum((f3 - f3.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    else:
        return {"verdict": "数据不足（三频组正向 <3 点）"}
    out["J1_线性_R2"] = {"r2": r2, "pass": bool(r2 > 0.99), "slope_N_per_EB": k}
    # J2 对照
    noise = float(np.std(fz)) if len(fz) > 1 else abs(fz).mean() if len(fz) else float("nan")
    sigma5 = 5 * noise
    out["J2_对照"] = {"mean_off": float(np.mean(fz)) if len(fz) else None,
                      "pass": bool(abs(np.mean(fz)) < sigma5) if len(fz) else None}
    # J3 奇性
    ebr, fr = sel("三频组", "反向")
    if len(ebr) and len(eb3):
        # 同 EB 点取反相比值
        ratios = []
        for e, ff in zip(ebr, fr):
            i = np.argmin(np.abs(eb3 - e))
            if abs(f3[i]) > 0:
                ratios.append(ff / f3[i])
        r = float(np.mean(ratios)) if ratios else None
        out["J3_奇性"] = {"ratio": r, "pass": bool(r is not None and -1.2 < r < -0.8)}
    # J4 体系特异性
    if len(ebo) >= 2:
        k_other = np.polyfit(ebo, fo, 1)[0]
        ratio = k / k_other if k_other != 0 else np.inf
        out["J4_特异性"] = {"slope_other": k_other, "ratio": ratio, "pass": bool(ratio > 10)}
    # 出判
    gk = k / E2H
    allpass = out["J1_线性_R2"]["pass"] and out.get("J2_对照", {}).get("pass") \
              and out.get("J3_奇性", {}).get("pass", False) and out.get("J4_特异性", {}).get("pass", False)
    out["∇θ·k_per_m"] = gk
    out["verdict"] = ("PASS：∇θ·k=%.3g /m（T0-A 定纲后换算体系 ∇θ）" % gk) if allpass \
        else "FAIL/INDETERMINATE：逐条见上；全零情形 ∇θ·k 上限=5σ/((e²/h)·⟨E·B⟩)"
    return out

if __name__ == "__main__":
    rows = load()
    res = judge(rows)
    with open(os.path.join(os.path.dirname(PATH), "v3grad_verdict.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=float)
    print(json.dumps(res, ensure_ascii=False, indent=1, default=float))
