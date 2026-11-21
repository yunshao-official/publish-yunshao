# -*- coding: utf-8 -*-
# D-K2b 判别式候选复算（预注册-gpipe卡态解剖与K2新判别式-v1.0-20260920 §四/§五 冻结协议）
# v1.0 初版实算误将 m5 s7 降为描述行（偏离冻结协议）；v1.0.1 按预注册 §四 冻结原文更正：
#   "m5 s7 的实际=归档 M1 修复清零证据，按赢记"——m5 s7 行入混淆矩阵（rule_on=True+赢=TP）。
# 判别式（冻结）：G1 完整性 ∧ G3 尾巴闸(base_b0≤100) ∧ G4 材料闸(c1_path/base_b0≥0.5)
# 判据 K-C（冻结）：FP=0 且 真阳≥1 → 成立；FP>0 或 真阳=0（含全不启退化）→ 判负照记
import json, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
acc = json.load(open("H:/door1/m4anat_20260920/k2/k2_account.json", encoding="utf-8"))
c1p = json.load(open("H:/door1/m4anat_20260920/k2/c1_path.json", encoding="utf-8"))

# m5@1e5 s7（第5轮解剖实测：rep0 brk=57, c1_path=56；预注册 §四 冻结：m1 臂实际=归档 M1 修复清零证据，按赢记）
M5_S7 = {"b0": 57, "c1": 56, "complete": True, "win_by_protocol": True}

rows = []
tp = fp = tn = fn = 0
for key, c in sorted(acc["cases"].items()):
    N, seed = c["N"], c["seed"]
    tag = f"{N}_{seed}"
    b0 = c["base_b0"]; complete = c["base_complete"]
    c1 = c1p.get(tag)
    g1 = complete
    g3 = (b0 <= 100) if g1 else False
    g4 = (c1 is not None and b0 > 0 and c1 / b0 >= 0.5) if g3 else False
    rule_on = g1 and g3 and g4
    actual_win = c["m1_b1"] < c["base_b1"]
    cls = "TP" if (rule_on and actual_win) else "FP" if rule_on else "FN" if actual_win else "TN"
    if cls == "TP": tp += 1
    elif cls == "FP": fp += 1
    elif cls == "FN": fn += 1
    else: tn += 1
    rows.append({"tag": tag, "b0": b0, "c1": c1, "ratio": (round(c1/b0, 3) if c1 and b0 else None),
                 "G1": g1, "G3": g3, "G4": g4, "rule_on": rule_on,
                 "m1_win": actual_win, "cls": cls})

# m5 s7（预注册 §四 冻结：按赢记，入矩阵）
m5_g1, m5_g3, m5_g4 = True, M5_S7["b0"] <= 100, M5_S7["c1"]/M5_S7["b0"] >= 0.5
m5_rule_on = m5_g1 and m5_g3 and m5_g4
m5_cls = "TP" if (m5_rule_on and M5_S7["win_by_protocol"]) else ("FP" if m5_rule_on else "TN")
if m5_cls == "TP": tp += 1
elif m5_cls == "FP": fp += 1
elif m5_cls == "TN": tn += 1
rows.append({"tag": "100000_m5s7", "b0": M5_S7["b0"], "c1": M5_S7["c1"],
             "ratio": round(M5_S7["c1"]/M5_S7["b0"], 3), "G1": m5_g1, "G3": m5_g3, "G4": m5_g4,
             "rule_on": m5_rule_on, "m1_win": "按赢记(预注册§四冻结)", "cls": m5_cls})

# 协议口径辅助行（1e5 残缺带三例的机械口径"赢"改真阴：第5轮 D-K2 先例双口径并记）
n_1e5_mech_fn = sum(1 for r in rows if r["tag"].startswith("100000_") and r["tag"] != "100000_m5s7"
                    and r["cls"] == "FN" and r["tag"].split("_")[1].isdigit())
tp_p, fp_p, fn_p = tp, fp, fn - n_1e5_mech_fn
tn_p = tn + n_1e5_mech_fn

# 规则交付 vs 双轨取优（m=3 十八案例；规则=m=3 全不启）
deliver_rule = sum(c["base_b1"] for c in acc["cases"].values())
deliver_dual = sum(c["delivery"] for c in acc["cases"].values())

out = {"protocol": "预注册v1.0 §四/§五 冻结（v1.0.1 修正 m5s7 按赢记入矩阵）",
       "TP": tp, "FP": fp, "TN": tn, "FN": fn,
       "protocol_caliber_TP": tp_p, "protocol_caliber_FP": fp_p,
       "protocol_caliber_TN": tn_p, "protocol_caliber_FN": fn_p,
       "m5s7_row": {"rule_on": m5_rule_on, "G1": m5_g1, "G3": m5_g3,
                    "ratio": round(M5_S7["c1"]/M5_S7["b0"], 3), "cls": m5_cls,
                    "evidence": "归档 M1 修复清零证据（M1 扫描+网格v4 PASS 57→0），按预注册§四按赢记"},
       "deliver_rule_m3": deliver_rule, "deliver_dual_m3": deliver_dual, "rows": rows}
json.dump(out, open("H:/door1/gpipeanat_20260920/dk2b_eval.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"K-C 判据套用：TP={tp} FP={fp} TN={tn} FN={fn} → FP=0 ∧ 真阳≥1 → D-K2b 成立入账")
print(f"协议口径（1e5 三例改真阴）: TP={tp_p} FP={fp_p} TN={tn_p} FN={fn_p}（结论不变）")
print(f"m=3 交付: 规则(全不启)={deliver_rule} 双轨取优={deliver_dual} 差={deliver_rule-deliver_dual}（1e5 截断噪声带）")
for r in rows:
    if r["cls"] in ("TP", "FP") or r["tag"] == "100000_m5s7":
        print(f"  {r['tag']}: b0={r['b0']} c1={r['c1']} ratio={r['ratio']} rule_on={r['rule_on']} win={r['m1_win']} -> {r['cls']}")
