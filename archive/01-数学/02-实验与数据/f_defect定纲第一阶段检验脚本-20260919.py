# -*- coding: utf-8 -*-
"""
f_defect 定纲第一阶段可算检验脚本（预注册判据冻结版）· 2026-09-19
==================================================================
判据来源：H:/理论存档/01-数学/00-正本/f_defect定纲方案-v1.0-20260918.md（冻结，未改）
  C1 主标度 f(d/λ) 单参 R²>0.9（备选 d/d₀）；C2 留出 Nb/Bi-2212 外推<20%；C3 实测Θ_D复核
数据源：H:/理论存档/03-高维材料工程/工艺仿真工具/results/verdict_pkg_batch10.json（0915 第十批，未改动）
协议缺口#1：d（缺陷间距）对天然超导体无操作定义（方案 A4 主假设依赖 T3 HRTEM，数据未采）
  → C1 主/备选标度不可算 → 本脚本跑最大可算子集：
  ①f_fit 十值统计+对唯一可算外生单参 Θ_D 的相关检验（Tc 为构造性内生物仅对照）；
  ②C2 常数模型版本：拟合8 最优常数预测 Nb/Bi-2212 的外推误差。
诚实标签：体系公式【体系内部定义·未验证】；Θ_D 手册近似【执行层·量级口径】。
复算方式：python 本脚本 → 重新生成结果 JSON（与已落盘版比对应逐位一致）。
"""
import json
import numpy as np
from scipy import stats

PKG = r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/verdict_pkg_batch10.json"
OUT = r"H:/理论存档/01-数学/02-实验与数据/f_defect定纲第一阶段检验结果-20260919.json"


def main():
    pkg = json.load(open(PKG, encoding="utf-8"))
    rows = pkg["一_Tc公式ab判别"]["rows"]
    mats = [r["material"] for r in rows]
    td = np.array([r["Theta_D_approx_K"] for r in rows], float)
    tc = np.array([r["Tc_K"] for r in rows], float)
    f = np.array([r["f_defect_fit"] for r in rows], float)
    assert np.allclose(f, tc / (td * 15 / 16)), "f_fit 与 Tc/(ΘD×15/16) 不一致，数据被改动"
    hold = [mats.index("Nb"), mats.index("Bi-2212")]
    fitm = [i for i in range(10) if i not in hold]

    out = {"meta": {"date": "2026-09-19",
                    "data_source": "verdict_pkg_batch10.json",
                    "frozen_criteria": "C1 f(d/λ) R²>0.9; C2 holdout Nb/Bi-2212 <20%; C3 实测Θ_D复核",
                    "protocol_gap_1": "d 对天然超导体无操作定义且无 HRTEM 数据 → 主/备选标度不可算 → 最大可算子集"}}

    # 检验① f_fit 统计
    out["test1_f_stats"] = {
        "all10": {"mean": f.mean(), "median": float(np.median(f)), "std": f.std(ddof=1),
                  "cv": f.std(ddof=1) / f.mean(), "min": f.min(), "max": f.max(),
                  "range": f.max() - f.min(), "max_min_ratio": f.max() / f.min()},
        "fit8": {"mean": f[fitm].mean(), "median": float(np.median(f[fitm])),
                 "std": f[fitm].std(ddof=1), "cv": f[fitm].std(ddof=1) / f[fitm].mean(),
                 "min": f[fitm].min(), "max": f[fitm].max(), "range": f[fitm].max() - f[fitm].min()}}

    def corr_pack(x, y, label):
        pr, pp = stats.pearsonr(x, y)
        sr, sp = stats.spearmanr(x, y)
        return {"n": len(x), "pearson_r": float(pr), "pearson_p": float(pp),
                "pearson_R2": float(pr ** 2), "spearman_rho": float(sr), "spearman_p": float(sp),
                "label": label}

    c_td_all = corr_pack(td, f, "f_fit~ΘD 全10")
    c_td_fit = corr_pack(td[fitm], f[fitm], "f_fit~ΘD 拟合8")
    c_tc_all = corr_pack(tc, f, "f_fit~Tc 全10（构造性: f_fit=Tc/(ΘD·15/16)）")
    c_tc_fit = corr_pack(tc[fitm], f[fitm], "f_fit~Tc 拟合8（构造性）")
    c_ltd_all = corr_pack(np.log10(td), f, "f_fit~log10ΘD 全10（稳健性对照·非预注册标度）")
    c_ltd_fit = corr_pack(np.log10(td[fitm]), f[fitm], "f_fit~log10ΘD 拟合8（对照）")
    out["test1_correlations"] = {
        "crit_r_n10_df8_a05": 0.6319, "crit_r_n8_df6_a05": 0.7067,
        "notes": "临界 r=标准 t 分布双尾 α=0.05 统计表值；Tc 相关为构造性（f_fit 由 Tc 导出）不构成独立证据",
        "f_vs_ThetaD_all10": c_td_all, "f_vs_ThetaD_fit8": c_td_fit,
        "f_vs_Tc_all10_constructive": c_tc_all, "f_vs_Tc_fit8_constructive": c_tc_fit,
        "robustness_logThetaD_all10": c_ltd_all, "robustness_logThetaD_fit8": c_ltd_fit}

    # 检验② 常数模型留出（C2 常数模型版本）
    c_mean, c_med = float(f[fitm].mean()), float(np.median(f[fitm]))
    res = {}
    for name, pred in [("mean8", c_mean), ("median8", c_med)]:
        errs = {mats[j]: {"f_fit_actual": float(f[j]), "f_pred": pred,
                          "rel_err_pct": abs(pred - f[j]) / f[j] * 100} for j in hold}
        res[name] = {"constant": pred, "errors": errs,
                     "both_pass_lt20pct": all(v["rel_err_pct"] < 20 for v in errs.values())}
    out["test2_holdout_constant_model"] = res

    out["c1_computability"] = {
        "main_scale_f_d_over_lambda": "不可算——d/λ 对十种天然超导体无操作定义（A4 主假设，T3 HRTEM 未采）",
        "backup_scale_f_d_over_d0": "不可算——同上，缺 d",
        "max_computable_single_param": "Θ_D（唯一有数据的外生结构可测量）；Tc 为 f_fit 的构造性内生物不作独立单参"}

    fail_reasons = [
        "C1 主+备选标度均不可算（协议缺口#1）→ R²>0.9 无法成立，PASS 必要条件不满足",
        "C2 常数模型版本：Nb %.1f%%、Bi-2212 %.1f%%，均远超冻结阈值 20%%（两件皆超）"
        % (res["mean8"]["errors"]["Nb"]["rel_err_pct"], res["mean8"]["errors"]["Bi-2212"]["rel_err_pct"]),
        "统计检验①：f_fit 对唯一可算外生单参 Θ_D 无显著相关（全10 r=%.4f p=%.4f；拟合8 r=%.4f p=%.4f）→ 现有数据内无单参结构实证"
        % (c_td_all["pearson_r"], c_td_all["pearson_p"], c_td_fit["pearson_r"], c_td_fit["pearson_p"])]
    out["verdict"] = {"result": "FAIL",
                      "scope": "第一阶段可算子集判定（C3 未做，判定性质=provisional，知世可否决）",
                      "frozen_criteria_status": {"C1": "不可算（协议缺口#1）→ 未通过",
                                                 "C2": "常数模型版本 194.6%/64.8% > 20% → 未通过",
                                                 "C3": "未执行（T1 实测 Θ_D 未采）"},
                      "fail_reasons": fail_reasons}

    with open(OUT, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=1)
    print(json.dumps(out["verdict"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
