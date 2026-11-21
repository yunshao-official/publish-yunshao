# -*- coding: utf-8 -*-
"""泛弦频率族计算器 v1.0（材料延展引擎）
公式链（体系口径，调和分析册）：
  f_c = k_B·Tc/h        （热频率，材料属性）
  f_0 = 64 × f_c        （M=64 十字缺陷阵列放大）
  f_1 = f_0 / 12        （第一泛弦——写入候选）
  f_2 = f_0 / 1.2       （第二泛弦）
  比例 12/1.2/144 锁死（宇宙常数）；绝对频率随材料 Tc 变（材料属性）——知世 0930 裁决口径
校验锚：YBCO Tc=350K（体系口径）→ f_c=7.29THz → f_0=466.4THz？
  ⚠ 在档口径 f_c=5.83THz（280K 口径）→f_0=373THz——两口径并存（调和册"fc 双口径算术补齐"），
  本表以在档正本锚（Tc=280K→373THz）为主行，350K 口径并列展示。
"""
import io, json

KB_OVER_H = 2.08366e10  # Hz/K（k_B/h）
M = 64

def family(Tc, label, note=""):
    fc = KB_OVER_H * Tc / 1e12          # THz
    f0 = M * fc
    return {"材料": label, "Tc_K": Tc, "f_c_THz": round(fc, 3),
            "f0_THz": round(f0, 1), "f1_THz": round(f0/12, 2),
            "f2_THz": round(f0/1.2, 1), "备注": note}

# 常见超导材料（Tc 文献值，常压；高压氢化物单列）
MATS = [
 family(280, "YBCO（体系正本口径）", "f_c=5.83THz 在档锚——f₀=373THz 正本行"),
 family(350, "YBCO（350K 口径）", "调和册双口径并存行——f₀=467THz"),
 family(110, "BSCCO 铋系", "铜氧化物第二系"),
 family(92,  "YBCO（文献常压）", "实物样品最常见口径"),
 family(56,  "铁基 SmFeAsO(F)", "铁基高温超导"),
 family(39,  "MgB2 二硼化镁", "简单化合物，拉曼/红外谱文献最全"),
 family(26,  "LaFeAsO(F) 铁基母体", ""),
 family(18,  "Nb3Sn", "实用低温超导"),
 family(9.3, "Nb 金属铌", "超导电子学标准材料"),
 family(4.2, "Hg 汞（超导发现原点）", ""),
 family(203, "H3S（高压 155GPa）", "高压氢化物——常压不可用，理论对照"),
 family(250, "LaH10（高压 170GPa）", "近室温超导纪录级——同上"),
]

print("泛弦频率族表（每材料一条写入频道）：")
print("{:<24}{:>7}{:>10}{:>10}{:>10}{:>10}".format("材料", "Tc(K)", "f_c(THz)", "f₀(THz)", "f₁(THz)", "f₂(THz)"))
for r in MATS:
    print("{:<24}{:>7}{:>10}{:>10}{:>10}{:>10}".format(
        r["材料"], r["Tc_K"], r["f_c_THz"], r["f0_THz"], r["f1_THz"], r["f2_THz"]))

out = r"H:/理论存档/03-高维材料工程/02-实验与数据/E5-泛弦频率族表-v1.0-20261003.json"
io.open(out, "w", encoding="utf-8").write(json.dumps(
    {"公式链": "f_c=kB·Tc/h; f0=64×fc; f1=f0/12; f2=f0/1.2; 比例锁死/绝对值随材料",
     "校验锚": "Tc=280K→f_c=5.83→f0=373（正本）；Tc=350K→f0=467（双口径）",
     "家族": MATS}, ensure_ascii=False, indent=1))
print("\n结果件：", out)
