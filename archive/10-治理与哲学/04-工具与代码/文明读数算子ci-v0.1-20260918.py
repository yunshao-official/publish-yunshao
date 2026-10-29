# -*- coding: utf-8 -*-
"""
文明读数算子 ci v0.1（主循环治理线·文明读数2026首算）
=====================================================
口径正本：《文明发展综合评价指标体系·全维坐标系 v1.0》（2026-09-18）§三/§四
判据冻结：坐标读数+雷达九边+门距读数三件套；无总分（永久条款）；双读数不混算
数据性质：2026-09-18 冻结快照，全部为【文献值/公开数据口径·量级】，非实测
确定性：无网络、无随机数，任何人对快照重跑必须逐位复现本输出
锚点校验（算错不许交卷）：K≈0.73 / HDI=0.739 / 行星边界越界=6
输出：JSON（雷达九边文本随 stdout；PNG 可后续另行生成，不进本脚本）
"""
import json, math, hashlib
from pathlib import Path

BASE = Path(r"H:\理论存档\10-治理与哲学").resolve()      # 唯一允许输出根目录
OUT_DIR = BASE / "02-实验与数据" / "results"             # 结果固定落此处
OUT_NAME = "文明读数2026首算-v0.1.json"

SNAPSHOT_VERSION = "2026-09-18-snap0.1"
SNAPSHOT = {
    # 轴A 能量-物质
    "TPES_EJ_per_yr": {"v": 620.0, "src": "IEA口径·公开能源统计·量级", "label": "文献值"},
    # 轴B 复杂度-效率
    "Phi_m_society_erg_s_g": {"v": 5e5, "src": "Chaisson 2001/2011谱系·量级口径", "label": "文献值"},
    # 轴C 信息-认知
    "GERD_pct_GDP": {"v": 1.9, "src": "UNESCO口径·世界均值·量级", "label": "文献值"},
    # 轴D 组织-治理（Seshat Z分现代政体无公开数值 → 待锚定）
    "Seshat_Z_modern": {"v": None, "src": "Turchin 2018 PNAS·现代政体Z分未公开", "label": "待锚定"},
    # 轴E 生命-福祉
    "HDI_global": {"v": 0.739, "src": "UNDP HDR 2023/24（2022年值）", "label": "文献值"},
    # 轴F 公平-包容（锚点待首版定锚，裁决单丙5）
    "Palma_global": {"v": None, "src": "WDI/WID·待定锚", "label": "待锚定"},
    # 轴G 环境-边界
    "PB_crossed_of_9": {"v": 6, "src": "Richardson et al. 2023 Science Advances", "label": "文献值"},
    # 轴H 安全-意志（判据族打分阈值未冻结 → 待冻结）
    "Safety_WQ_RC": {"v": None, "src": "战略层判据库v1.0·门3阈值待首版", "label": "待冻结"},
    # 轴Λ 体系总纲轴
    "Civilization_Level": {"v": "G0", "src": "白皮书v2.0卷四·TFI-1未过", "label": "体系内部定义·未验证"},
}

AXIS_TO_KEY = {
    "A": "TPES_EJ_per_yr", "B": "Phi_m_society_erg_s_g", "C": "GERD_pct_GDP",
    "D": "Seshat_Z_modern", "E": "HDI_global", "F": "Palma_global",
    "G": "PB_crossed_of_9", "H": "Safety_WQ_RC", "Lambda": "Civilization_Level",
}
AXIS_NAMES = {"A": "能量", "B": "复杂度", "C": "信息", "D": "组织", "E": "福祉",
              "F": "公平", "G": "环境", "H": "安全", "Lambda": "体系Λ"}

# 等步长实现口径（0.125起，步0.2917）；丙5终批前为实现口径，非体系原文
LAMBDA_LEVELS = {"G0": 0.125, "G1": 0.4167, "G2": 0.7083, "G3": 1.0}


def checked_out_path():
    """输出路径=固定常量拼接；resolve 后强制校验仍在 BASE 白名单目录内。"""
    target = (OUT_DIR / OUT_NAME).resolve()
    target.relative_to(BASE)          # 不在 BASE 内会抛 ValueError——硬校验
    return target


def kardashev_sagan(p_watts):
    """K = (log10 P - 6)/10 【Sagan 1973】"""
    return (math.log10(p_watts) - 6.0) / 10.0


def normalize(axis):
    """归一化公式：坐标系§四冻结表。返回 (norm|None, note)"""
    if axis == "A":
        p_w = SNAPSHOT["TPES_EJ_per_yr"]["v"] * 1e18 / 3.156e7  # EJ/yr -> W
        k = kardashev_sagan(p_w)
        return k / 2.0, f"P={p_w:.3e}W, K={k:.4f}, norm=K/2"
    if axis == "B":
        return math.log10(SNAPSHOT["Phi_m_society_erg_s_g"]["v"]) / 12.0, "norm=log10(Phi_m)/12"
    if axis == "C":
        return SNAPSHOT["GERD_pct_GDP"]["v"] / 6.0, "norm=GERD/6%"
    if axis in ("D", "F"):
        return None, "锚点待首版定锚（裁决单丙5）"
    if axis == "E":
        return SNAPSHOT["HDI_global"]["v"], "HDI原值即归一"
    if axis == "G":
        return 1.0 - SNAPSHOT["PB_crossed_of_9"]["v"] / 9.0, "norm=1-越界数/9"
    if axis == "H":
        return None, "判据族打分阈值未冻结（门3）"
    if axis == "Lambda":
        return LAMBDA_LEVELS[SNAPSHOT["Civilization_Level"]["v"]], "分级枚举等步长实现口径"
    raise KeyError(axis)


def gates():
    """三条二元硬门+门距读数。门输出只有过/不过/待定义。"""
    pb = SNAPSHOT["PB_crossed_of_9"]["v"]
    return [
        {"gate": "门1有序相门", "state": "待定义",
         "note": "Λ_ord文明尺度操作定义待裁决（坐标系§6.4四代理电池=丙4）", "margin": None},
        {"gate": "门2行星边界门", "state": "不过" if pb > 0 else "过",
         "note": f"越界{pb}/9条（目标0条）", "margin": -pb},
        {"gate": "门3脆弱性门", "state": "待冻结",
         "note": "脆弱政体占比阈值待首版数据冻结", "margin": None},
    ]


def anchors():
    """三锚点校验：算错不许交卷。"""
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
    """雷达九边文本版。"""
    rows = []
    for ax in ["A", "B", "C", "D", "E", "F", "G", "H", "Lambda"]:
        nv = norms[ax]
        if nv is None:
            rows.append(f"  {AXIS_NAMES[ax]:>4}({ax:>6}) | {'·' * 4} 待锚定")
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
        raise SystemExit("锚点校验失败——算错不许交卷，禁止出报告")

    gts = gates()
    numeric = [(g["gate"], g["margin"]) for g in gts if g["margin"] is not None]
    weakest = min(numeric, key=lambda t: t[1])[0] if numeric else "（无数值门距：三门全待定义/冻结）"

    result = {
        "snapshot_version": SNAPSHOT_VERSION,
        "snapshot_sha256": hashlib.sha256(json.dumps(SNAPSHOT, sort_keys=True).encode("utf-8")).hexdigest()[:16],
        "coordinates": {ax: {"name": AXIS_NAMES[ax], "norm": norms[ax],
                             "snap": SNAPSHOT[AXIS_TO_KEY[ax]], "note": notes[ax]}
                        for ax in AXIS_NAMES},
        "gates": gts,
        "weakest_gate": weakest,
        "anchor_checks": checks,
        "no_total_score": "永久条款：本算子永不输出单一文明总分",
        "dual_reading": "执行层八轴与轴Λ双读数并列，不混算",
    }

    print("=" * 62)
    print("文明读数2026 · 首算（地球基线）  快照", SNAPSHOT_VERSION)
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
    print("无总分条款生效；双读数并列。")

    out_path = checked_out_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("结果已写:", str(out_path))


if __name__ == "__main__":
    main()
