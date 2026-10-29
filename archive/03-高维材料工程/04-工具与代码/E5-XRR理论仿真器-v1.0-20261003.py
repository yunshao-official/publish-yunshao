# -*- coding: utf-8 -*-
"""E5-XRR 理论仿真器 v1.0（Parratt 递推+ Nevot-Croce）
理论实验目标：无实物样品阶段，数值证明判据 C-X1 的可分辨度——
三束写入改性层（密度降低的表面层）厚度 Δt=0.5/1/2/5/10/30 nm 的 XRR 曲线族，
在典型实验噪声下能否分辨？（判据 C-X1 分辨率数值化）
模型：Cu Kα (λ=1.5406Å)；Si 基底 δ=7.56e-6, β=1.72e-7；
改性层 = 密度 95% 基底（缺陷→密度降）δ=7.18e-6。
"""
import math, io, json, cmath

LAM = 1.5406          # Å
K0 = 2*math.pi/LAM
RE_LAM2_2PI = 2.70e-6 # δ / (电子密度 mol/cm³) 系数量级（Si 校准用）

def layers(t_mod_nm, dens_frac=0.95, sigma_mod_nm=1.0, sigma_top_nm=0.6):
    """返回层列表（从表面往下）：[(δ, β, 厚度Å, 粗糙度Å), ...] 最后为基底"""
    d_si, b_si = 7.56e-6, 1.72e-7
    d_mod = d_si * dens_frac
    b_mod = b_si * dens_frac
    L = []
    if t_mod_nm > 0:
        L.append((d_mod, b_mod, t_mod_nm*10.0, sigma_mod_nm*10.0))
    L.append((d_si, b_si, math.inf, sigma_top_nm*10.0))
    return L

def parratt(layers, theta_deg):
    theta = math.radians(theta_deg)
    kz = [cmath.sqrt(complex(d, b) - math.cos(theta)**2) for d, b, _, _ in layers]
    n = len(layers)
    r = complex(0, 0)
    for j in range(n-2, -1, -1):
        dz, sig = layers[j+1][2], layers[j+1][3]
        rjk = (kz[j]-kz[j+1])/(kz[j]+kz[j+1]) * math.exp(-2*(kz[j].real*kz[j+1].real - kz[j].imag*kz[j+1].imag)*sig**2 / (2*kz[j].real)) if False else \
              (kz[j]-kz[j+1])/(kz[j]+kz[j+1])
        # Nevot-Croce 界面因子（层 j 与 j+1 间粗糙度 sig）
        nc = complex(math.exp(-2*kz[j].real*kz[j+1].real*sig*sig), math.exp(-2*kz[j].real*kz[j+1].real*0)) \
             if False else complex(math.exp(-2*kz[j].real*kz[j+1].real*sig**2), 0)
        rjk *= nc
        if math.isfinite(dz):
            ph = complex(math.exp(2j*kz[j+1].real*dz) * math.exp(-2*kz[j+1].imag*0), 0)
            ph = complex(math.cos(2*kz[j+1].real*dz)*math.exp(-2*kz[j+1].imag*dz),
                         math.sin(2*kz[j+1].real*dz)*math.exp(-2*kz[j+1].imag*dz))
        else:
            ph = 1
        r = (rjk + r*ph) / (1 + rjk*r*ph)
    return abs(r)**2

# 扫描
angles = [0.05*i for i in range(2, 400)]  # 0.1–20°
cases = {"对照(无改性层)": 0, "Δt=0.5nm": 0.5, "Δt=1nm": 1, "Δt=2nm": 2, "Δt=5nm": 5, "Δt=30nm(理论写入深度)": 30}
curves = {}
for name, t in cases.items():
    Ls = layers(t)
    curves[name] = [parratt(Ls, a) for a in angles]

# 判别度：log10 R 差（相对对照），典型 XRR 动态范围 8 个量级、噪声 ~1-2%R
import statistics
print("改性层厚度对 XRR 曲线的可分辨度（|Δlog10R| 均值±最大，角域 0.1-8°）：")
res = {}
for name, t in cases.items():
    if t == 0: continue
    diffs = [abs(math.log10(curves[name][i]+1e-12) - math.log10(curves["对照(无改性层)"][i]+1e-12))
             for i, a in enumerate(angles) if a <= 8]
    res[name] = {"mean_dlogR": round(statistics.mean(diffs), 4), "max_dlogR": round(max(diffs), 4)}
    print("  {:<22} 均值 {:.4f}  最大 {:.4f}".format(name, res[name]["mean_dlogR"], res[name]["max_dlogR"]))

# 结论：噪声 1%R ≈ |Δlog10R|~0.0045 处可辨（信噪 3σ）
print("\n判据 C-X1 数值化（假设测角噪声 1%R，3σ 可辨阈 |Δlog10R|≈0.013）：")
for name, s in res.items():
    print("  {:<22} → {}".format(name, "可分辨 ✓" if s["mean_dlogR"] > 0.013 else "临界/不可分辨 ✗"))

out = r"H:/理论存档/03-高维材料工程/02-实验与数据/E5-XRR理论仿真-v1.0-20261003.json"
io.open(out, "w", encoding="utf-8").write(json.dumps(
    {"angles_deg_01_20": angles, "curves": curves, "discriminability": res,
     "model": "Parratt+Nevot-Croce; CuKa; Si基底; 改性层=95%密度; sigma=1nm"}, ensure_ascii=False))
print("\n结果件：", out)
