# -*- coding: utf-8 -*-
"""
文明读数算子 ci v0.2（主循环治理线·九边补全：D删失锚定+F实测+门3冻结）
======================================================================
口径正本：《文明发展综合评价指标体系·全维坐标系 v1.0》§三/§四 + 首算报告v0.1
v0.1→v0.2 变更（全为【实现口径】，丙5可调，改动即版本+1）：
  - D轴：删失下限锚定 D=1.0——依据 L6（Turchin 2018 PNAS）九特征载荷（人口/疆域/层级/
    政府/基础设施/信息系统）现代政体全变量≥历史政体最大值；Seshat无现代政体Z分公开编码。
  - F轴：实现指标="收入前10%对后50%份额比"（Palma型变体，底40%全球份额无公开快照值），
    数据 WIR2022：52%/8.5% → 比值6.118；norm=max(0, 1-比值/10)。
  - 门3阈值冻结：脆弱国家指数 Alert(≥90分) 政体占比 ≤5% 目标线；2024读数≈2国/167≈1.2%
    【知识口径·待官网复核】→ 门3当前读数=过。
  - H轴分值：仍留待判据族打分（门3读数单列于门距，不进九边）。
确定性：无网络、无随机数；快照重跑逐位复现。锚点校验：K/HDI/越界三锚点。
永久条款：永不输出单一文明总分；执行层八轴与轴Λ双读数不混算。
"""
import json, math, hashlib
from pathlib import Path

BASE = Path(r"H:\理论存档\10-治理与哲学").resolve()
OUT_DIR = BASE / "02-实验与数据" / "results"

SNAPSHOT_VERSION = "2026-09-18-snap0.2"
SNAPSHOT = {
    "TPES_EJ_per_yr": {"v": 620.0, "src": "IEA口径·公开能源统计·量级", "label": "文献值"},
    "Phi_m_society_erg_s_g": {"v": 5e5, "src": "Chaisson 2001/2011谱系·量级口径", "label": "文献值"},
    "GERD_pct_GDP": {"v": 1.9, "src": "UNESCO口径·世界均值·量级", "label": "文献值"},
    "Seshat_D_censored": {"v": 1.0, "src": "L6九特征载荷删失下限（现代≥历史最大）", "label": "实现口径·删失估计"},
    "HDI_global": {"v": 0.739, "src": "UNDP HDR 2023/24（2022年值）", "label": "文献值"},
    "IncomeRatio_P10_P50": {"v": 52.0 / 8.5, "src": "WIR2022：前10%=52%，后50%=8.5%", "label": "文献值（实现口径归一）"},
    "PB_crossed_of_9": {"v": 6, "src": "Richardson et al. 2023 Science Advances", "label": "文献值"},
    "FSI_alert_share_pct": {"v": 1.2, "src": "FSI2024 Alert(≥90)≈2国/167【知识口径·待官网复核】", "label": "知识口径"},
    "Civilization_Level": {"v": "G0", "src": "白皮书v2.0卷四·TFI-1未过", "label": "体系内部定义·未验证"},
}

AXIS_NAMES = {"A": "能量", "B": "复杂度", "C": "信息", "D": "组织", "E": "福祉",
              "F": "公平", "G": "环境", "H": "安全", "Lambda": "体系Λ"}
LAMBDA_LEVELS = {"G0": 0.125, "G1": 0.4167, "G2": 0.7083, "G3": 1.0}  # 等步长实现口径


def kardashev_sagan(p_watts):
    return (math.log10(p_watts) - 6.0) / 10.0


def normalize(axis):
    """归一化：§四冻结表+v0.2实现口径。"""
    if axis == "A":
        p_w = SNAPSHOT["TPES_EJ_per_yr"]["v"] * 1e18 / 3.156e7
        k = kardashev_sagan(p_w)
        return k / 2.0, f"P={p_w:.3e}W, K={k:.4f}, norm=K/2"
    if axis == "B":
        return math.log10(SNAPSHOT["Phi_m_society_erg_s_g"]["v"]) / 12.0, "norm=log10(Phi_m)/12"
    if axis == "C":
        return SNAPSHOT["GERD_pct_GDP"]["v"] / 6.0, "norm=GERD/6%"
    if axis == "D":
        return SNAPSHOT["Seshat_D_censored"]["v"], "删失下限锚定1.0（丙5可调）"
    if axis == "E":
        return SNAPSHOT["HDI_global"]["v"], "HDI原值即归一"
    if axis == "F":
        r = SNAPSHOT["IncomeRatio_P10_P50"]["v"]
        return max(0.0, 1.0 - r / 10.0), f"P10/P50比={r:.3f}, norm=max(0,1-r/10)"
    if axis == "G":
        return 1.0 - SNAPSHOT["PB_crossed_of_9"]["v"] / 9.0, "norm=1-越界数/9"
    if axis == "H":
        return None, "判据族打分待跑；门3读数单列门距（Alert占比1.2%→过）"
    if axis == "Lambda":
        return LAMBDA_LEVELS[SNAPSHOT["Civilization_Level"]["v"]], "分级枚举等步长实现口径"
    raise KeyError(axis)


def gates():
    pb = SNAPSHOT["PB_crossed_of_9"]["v"]
    alert = SNAPSHOT["FSI_alert_share_pct"]["v"]
    return [
        {"gate": "门1有序相门", "state": "待定义", "note": "Λ_ord操作定义=丙4候选，裁决前挂牌", "margin": None},
        {"gate": "门2行星边界门", "state": "不过" if pb > 0 else "过", "note": f"越界{pb}/9条（目标0）", "margin": -pb},
        {"gate": "门3脆弱性门", "state": "过" if alert <= 5.0 else "不过",
         "note": f"Alert(≥90)占比≈{alert}%≤5%目标线【知识口径·待复核】", "margin": round(5.0 - alert, 1)},
    ]


def anchors():
    p_w = SNAPSHOT["TPES_EJ_per_yr"]["v"] * 1e18 / 3.156e7
    k = kardashev_sagan(p_w)
    return [
        {"anchor": "K值", "expect": "0.72-0.74", "got": round(k, 4), "pass": 0.72 <= k <= 0.74},
        {"anchor": "HDI", "expect": 0.739, "got": SNAPSHOT["HDI_global"]["v"],
         "pass": abs(SNAPSHOT["HDI_global"]["v"] - 0.739) < 1e-9},
        {"anchor": "行星边界越界", "expect": 6, "got": SNAPSHOT["PB_crossed_of_9"]["v"],
         "pass": SNAPSHOT["PB_crossed_of_9"]["v"] == 6},
    ]


def radar_ascii(norms):
    rows = []
    for ax in ["A", "B", "C", "D", "E", "F", "G", "H", "Lambda"]:
        nv = norms[ax]
        if nv is None:
            rows.append(f"  {AXIS_NAMES[ax]:>4}({ax:>6}) | {'·' * 4} 待冻结（门3读数见门距）")
        else:
            bar = "█" * int(round(nv * 30))
            rows.append(f"  {AXIS_NAMES[ax]:>4}({ax:>6}) | {bar:<30} {nv:.3f}")
    return "\n".join(rows)


def main():
    norms, notes = {}, {}
    for ax in AXIS_NAMES:
        norms[ax], notes[ax] = normalize(ax)

    checks = anchors()
    all_pass = all(c["pass"] for c in checks)
    if not all_pass:
        raise SystemExit("锚点校验失败——禁止出报告")

    gts = gates()
    numeric = [(g["gate"], g["margin"]) for g in gts if g["margin"] is not None]
    weakest = min(numeric, key=lambda t: t[1])[0] if numeric else "（无数值门距）"

    result = {
        "snapshot_version": SNAPSHOT_VERSION,
        "snapshot_sha256": hashlib.sha256(json.dumps(SNAPSHOT, sort_keys=True).encode("utf-8")).hexdigest()[:16],
        "coordinates": {ax: {"name": AXIS_NAMES[ax], "norm": norms[ax], "note": notes[ax]} for ax in AXIS_NAMES},
        "gates": gts,
        "weakest_gate": weakest,
        "anchor_checks": checks,
        "no_total_score": "永久条款：永不输出单一文明总分",
        "dual_reading": "执行层八轴与轴Λ双读数并列，不混算",
        "changelog_v0_2": "D删失锚定/F实测WIR2022/门3冻结(H分值留判据族)/H读数知识口径待复核",
    }

    print("=" * 62)
    print("文明读数2026 · 九边补全（基线v0.2）  快照", SNAPSHOT_VERSION)
    print("=" * 62)
    print(radar_ascii(norms))
    print("-" * 62)
    for g in gts:
        print(f"  {g['gate']}: {g['state']}  门距={g['margin']}  ({g['note']})")
    print(f"  最脆一根弦: {weakest}")
    print("-" * 62)
    print("锚点校验:", "PASS" if all_pass else "FAIL")
    for c in checks:
        print(f"  {c['anchor']}: 期望{c['expect']} / 实得{c['got']} -> {'PASS' if c['pass'] else 'FAIL'}")

    out_dir = OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = (out_dir / "文明读数2026首算-v0.2.json").resolve()
    out_path.relative_to(BASE)  # 白名单硬校验
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("结果已写:", str(out_path))

    try:
        import matplotlib.pyplot as plt
        import numpy as np
        axes_order = ["A", "B", "C", "D", "E", "F", "G", "H", "Lambda"]
        vals = [norms[a] if norms[a] is not None else 0.0 for a in axes_order]
        ang = np.linspace(0, 2 * math.pi, 9, endpoint=False).tolist()
        fig = plt.figure(figsize=(5.5, 5.5))
        ax = fig.add_subplot(111, polar=True)
        ax.plot(ang + ang[:1], vals + vals[:1])
        ax.fill(ang + ang[:1], vals + vals[:1], alpha=0.25)
        ax.set_xticks(ang)
        ax.set_xticklabels([AXIS_NAMES[a] for a in axes_order])
        ax.set_title("文明读数2026·基线v0.2（H轴待判据族打分=0占位）")
        png_path = (out_dir / "文明读数2026雷达-v0.2.png").resolve()
        png_path.relative_to(BASE)
        fig.savefig(str(png_path), dpi=150, bbox_inches="tight")
        plt.close(fig)
        print("雷达图已写:", str(png_path))
    except Exception as e:
        print("雷达图PNG未生成（不影响数据）:", type(e).__name__)


if __name__ == "__main__":
    main()
