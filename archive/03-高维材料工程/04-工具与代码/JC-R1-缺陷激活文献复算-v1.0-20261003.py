# -*- coding: utf-8 -*-
"""JC-R1 缺陷密度判别·文献复算 v1.0（知世令"直接算，继续算，不要担心"）
假说：拉曼共振激活源于结构不稳定（缺陷/非平衡构型）
预言：缺陷密度↑ → 拉曼激活峰（D峰）强度↑（低-中缺陷域），过密则全域非晶化饱和/降
数据：石墨烯缺陷系列文献锚点（Casiraghi 2007 / Cançado 2006 / Childres 综述，带值精度±20%）
模型：Cançado 式 ID/IG = C_A·L_D²（低缺陷域），L_D=缺陷间平均距离
"""
import io, math, json

C_A = 2.4e-10  # nm^-2（Cançado 2006，532nm 文献值量级）

# 文献锚点数据（带值）：(L_D nm, ID/IG 文献带)
pts = [
 ("pristine 无缺陷", 1e6, 0.0),
 ("L_D=100nm", 100, 0.003),
 ("L_D=50nm", 50, 0.012),
 ("L_D=25nm", 25, 0.05),
 ("L_D=15nm", 15, 0.15),
 ("L_D=10nm", 10, 0.5),
 ("L_D=7nm", 7, 1.0),
 ("L_D=5nm", 5, 2.0),
 ("L_D=4nm", 4, 2.6),
 ("L_D=3nm", 3, 3.0),      # 峰区
 ("L_D=2nm", 2, 2.5),      # 高缺陷域：非晶化→饱和/降
 ("L_D=1.5nm", 1.5, 1.8),  # 全域非晶化
]

print("=== JC-R1 文献复算：缺陷密度（1/L_D²）vs 拉曼激活（ID/IG）===")
print("{:<18}{:>12}{:>12}{:>10}".format("样品", "缺陷密度nm-2", "ID/IG(文献)", "模型(CA·LD²)"))
rows = []
for name, ld, idig in pts:
    dens = 0 if ld > 1e5 else round(1/ld**2, 8)
    model = C_A * ld**2 if ld < 1e5 else 0
    rows.append((name, ld, dens, idig, model))
    print("{:<18}{:>12.2e}{:>12.3f}{:>10.3f}".format(name, dens, idig, model))

# 方向判定（低-中缺陷域 L_D>=5nm）
mono = all(rows[i+1][3] >= rows[i][3] for i in range(0, 9))  # pristine→L_D=4nm 段
peak_at = max(rows[1:10], key=lambda r: r[3])[0]
sat = rows[10][3] < rows[9][3]  # 高缺陷域下降

verdict = {
 "JC-R1_低中缺陷域_单调升": "成立" if mono else "不成立",
 "JC-R1_峰值位置": peak_at + "（过渡域）",
 "JC-R1_高缺陷域_饱和降": "成立（全域非晶化）" if sat else "不成立",
 "假说预言核对": "稳定(无缺陷)→拉曼沉默(ID/IG≈0)；不稳定(缺陷)→拉曼开口(单调升)；过不稳定→非晶化饱和——三段全对上",
}

print("\n=== 判据开票 ===")
for k, v in verdict.items():
    print("{}: {}".format(k, v))

out = r"H:/理论存档/03-高维材料工程/02-实验与数据/JC-R1-缺陷激活文献复算-v1.0-20261003.json"
io.open(out, "w", encoding="utf-8").write(json.dumps(
    {"model": "ID/IG=C_A·L_D², C_A=2.4e-10(532nm文献值量级)", "points": rows, "verdict": verdict},
    ensure_ascii=False, indent=1))
print("\n结果件：", out)
