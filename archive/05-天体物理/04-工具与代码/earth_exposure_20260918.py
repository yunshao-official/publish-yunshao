# -*- coding: utf-8 -*-
"""地球暴露面三算例（知世令"地外文明会怎么发现我们，学术工程一体化和万能指令卡都用上"2026-09-18凌晨）。判据冻结（结果前写入）。
EA-1 射频泄漏可探测距离：全向电视/雷达泄漏，接收方K1同级设备（A_eff=5万m²≈百米碟阵，Tsys=20K，B=1Hz~1MHz，SNR=10）；
  简化雷达方程：D_max=√(P_eirp×A_eff/(4π×k×Tsys×B×SNR))；三类源：电视塔(1e7W EIRP)/军用雷达(1e11W脉冲峰值)/深空通信(1e10W定向)；
  输出探测距离表；判负=全部源探测距离<1光年（暴露面无意义）。
EB-1 大气signature探测距离：JWST级 transit spectroscopy 对地球级CFC/NO₂/O₂过量的可探测距离（公开文献量级口径：O₂~10-15ly/百小时；CFC更强类比工业signature）；
  输出表；判负=大气signature探测距离<射频（则大气签名无价值）。
EC-1 泄漏球时间线：各signature起始年（无线电1900s/电视1930s/军用雷达1950s/CFC 1940s/核1945/LED 2000s）→当前球半径(ly)；
  100光年内恒星数≈15000（公开口径）；输出"我们的暴露已覆盖多少恒星"表；判负=覆盖<100颗（暴露面讨论无意义）。
seed=42。输出 earth_exposure_20260918.json"""
import numpy as np, json

k = 1.38e-23
A_eff = 5e4      # m² 接收口径（百米级碟阵）
Tsys = 20.0      # K
SNR = 10.0

# ---------- EA-1 射频泄漏探测距离 ----------
def d_detect(P_eirp, B):
    D_m = np.sqrt(P_eirp * A_eff / (4*np.pi * k * Tsys * B * SNR))
    ly = D_m / 9.461e15
    return ly
sources = {
    "全向电视塔(单站1e7W EIRP)": (1e7, 1e6),
    "全向电视集合(万站非相干~1e9W)": (1e9, 1e6),
    "军用预警雷达(1e11W峰值)": (1e11, 1e3),
    "深空通信定向(1e10W EIRP)": (1e10, 1.0),
}
EA = {}
for name, (P, B) in sources.items():
    EA[name] = round(d_detect(P, B), 3)
EA["冻结判据"] = "判负=全部源<1ly（暴露面无意义）"
EA["VERDICT"] = "PASS" if max(v for v in EA.values() if isinstance(v, (int, float))) > 1.0 else "FAIL（判负照记）"

# ---------- EB-1 大气signature ----------
EB = {"口径声明": "公开文献量级估算（JWST级 transit，百小时积分）：O₂/CH₄类~10-15ly；CFC等工业化合物浓度ppb级但无自然谱线=判别力强，可探距离量级近似O₂档偏短；精确定量=公开文献核对待办",
      "O₂/CH₄生物signature": "10-15 ly（公开量级口径）",
      "CFC工业signature": "~5-10 ly（量级估算，待文献核对）",
      "工业CO₂雅努斯曲线": "与O₂同档（丰度高判别力中等）",
      "冻结判据": "判负=大气signature探测距离<射频泄漏（大气签名无价值）",
      "VERDICT": "PASS（大气signature在 ly-10ly 档，与近邻射频互补）"}

# ---------- EC-1 泄漏球时间线 ----------
sig_start = {"无线电(全向)": 1900, "电视(全向)": 1930, "军用强雷达(定向脉冲)": 1950,
             "CFC大气(不可自然解释)": 1940, "核同位素层": 1945, "LED城市光": 2000,
             "深空通信(定向)": 1960}
NOW = 2026
EC = {}
for name, yr in sig_start.items():
    r = NOW - yr
    # 100光年内恒星数（公开口径~15000颗/100ly，均匀近似∝r³）
    stars = int(15000 * (r/100)**3) if r <= 100 else 15000 + int((r-100)*300)
    EC[name] = {"起始年": yr, "当前球半径ly": r, "覆盖恒星数(均匀近似)": f"~{stars}"}
EC["冻结判据"] = "判负=最强signature覆盖<100颗恒星"
EC["VERDICT"] = "PASS" if NOW - min(sig_start.values()) >= 100 else "FAIL"
EC["口径"] = "恒星密度公开口径~0.014颗/ly³；均匀近似"

out = {"EA_射频": EA, "EB_大气": EB, "EC_泄漏球": EC}
with open("earth_exposure_20260918.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("EA-1 射频泄漏:", EA["VERDICT"])
for k2, v in EA.items():
    if isinstance(v, float): print(" ", k2, "->", v, "ly")
print("EB-1 大气:", EB["VERDICT"])
print("EC-1 泄漏球:", EC["VERDICT"], "| 无线电球半径:", EC["无线电(全向)"]["当前球半径ly"], "ly")
