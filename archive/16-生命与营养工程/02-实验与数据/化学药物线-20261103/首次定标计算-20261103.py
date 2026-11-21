# 云韶体系·化学与药物线·首次定标计算（复算脚本·零外部输入）
# 用途：为《强心药物×长寿物质·预注册判据书 v1.0》提供全部体系侧数值
# 纪律：所有输入均为 constants 语义的体系自有常数 + 公开物理常数；不含任何文献数值
import math

k_B = 1.380649e-23      # J/K  (CODATA 2018, SI 定义值)
h   = 6.62607015e-34    # J·s  (SI 定义值)
c   = 2.99792458e17     # nm/s (光速：299792458 m/s = 2.99792458e17 nm/s)
kBh_GHz_K = k_B / h / 1e9   # GHz/K

print("== 0. 物理内核 ==")
print("k_B/h = %.4f GHz/K  (体系档 20.837)" % kBh_GHz_K)

alpha = 1/8          # α(N)=1/N, N=8 → 亏损率
eta   = 7/8          # η = 1-α → 单级传递保留率
M     = 64           # M = 2/κ, κ=1/32 → 十字缺陷阵列放大倍数
print("alpha=%.6f eta=%.6f 修复:写入配额 = eta/alpha = %.4f" % (alpha, eta, eta/alpha))

print("\n== 1. F0 代际制：公式甲(直热式) 与 公式丙(德拜均式) 在生物温度档的输出 ==")
def gen_jia(Theta):
    f0 = M * kBh_GHz_K * Theta / 1000.0      # THz
    return f0, f0/12.0, f0/1.2, c/(f0*1e12)
def gen_bing(ThetaD):
    f0 = (M*0.75) * kBh_GHz_K * ThetaD / 1000.0
    return f0, f0/12.0, f0/1.2, c/(f0*1e12)

rows = [("280 热标代", 280.0), ("310.15 体温(37C)", 310.15), ("313 体温上限", 313.0),
        ("350 Tc代", 350.0), ("600 材料代(手足/LEV样品)", 600.0)]
for name, T in rows:
    a = gen_jia(T); b = gen_bing(T)
    print("%-22s 甲 f0=%7.2fTHz lam=%7.2fnm f1=%6.2fTHz(%5.2fum) lam_f1=%6.2fum | 丙 f0=%7.2fTHz lam=%7.2fnm"
          % (name, a[0], a[3], a[1], c/(a[1]*1e12), c/(a[1]*1e12)/1000.0, b[0], b[3]))

print("\n== 2. 804nm 载体的代际归属（反向定标） ==")
for lam in [804.0, 724.83, 966.43, 680.0, 430.0]:
    f = c/lam/1e12   # THz
    Th_jia  = f/(M*kBh_GHz_K/1000.0)
    Th_bing = f/((M*0.75)*kBh_GHz_K/1000.0)
    print("lam=%7.2fnm f=%7.2fTHz -> 甲代入温度=%6.1fK  丙代入温度=%6.1fK" % (lam, f, Th_jia, Th_bing))

print("\n== 3. 观察衰减 2^{-(8/7)dd}（体系候选式·候裁决） ==")
slope = 8/7
for dd in [0.5, 1.0, 1.5, 2.0]:
    print("dd=%.1f  衰减系数=%.4f  (即保留 %.2f%%)" % (dd, 2**(-slope*dd), 100*2**(-slope*dd)))
print("按式子 dd=1 应得 %.4f；档案他处写 '每差1维 x0.56' -> 0.56 需指数 %.4f (非 8/7=%.4f)"
      % (2**(-slope), -math.log2(0.56), slope))

print("\n== 4. 心动周期的时相账（写入期/修复期，纯生理常识量程） ==")
print("HR  T_beat  收缩期Tw  舒张期Tr  Tr/Tw  达7:1所需HR")
for hr in [50, 60, 75, 90, 100, 120, 150]:
    T = 60.0/hr
    # 收缩期随心率轻度缩短（经验：60bpm~0.30s, 180bpm~0.16s 线性）
    Tw = 0.30 - (hr-60)*(0.30-0.16)/(180-60)
    Tr = T - Tw
    need = 60.0/(7*Tw + Tw)
    print("%3d  %5.3f   %5.3f    %5.3f   %5.2f   %6.2f bpm" % (hr, T, Tw, Tr, Tr/Tw, need))

print("\n== 5. 心肌功率账（写入功率 vs 修复配额，能量币种） ==")
CO, MAP = 5.0, 93.0            # L/min, mmHg 静息
P_mech  = MAP*CO*0.00229       # W  (心脏功率输出标准换算)
MVO2    = 9.0                  # mL O2/min 全心静息耗氧(量程 8-10)
J_per_mLO2 = 20.1              # J/mL O2 (~4.82 kcal/L)
P_metab = MVO2*J_per_mLO2/60.0 # W
print("P_mech=%.3f W  P_metab=%.3f W  效率=%.1f%%" % (P_mech, P_metab, 100*P_mech/P_metab))
print("体系要求修复配额 >= 7x写入 = %.2f W ；实测可用(非机械输出)=%.2f W -> 达标率 %.1f%%"
      % (7*P_mech, P_metab-P_mech, 100*(P_metab-P_mech)/(7*P_mech)))
print("一年机械写入 = %.3e J/yr ；一生80年 = %.3e J" % (P_mech*3600*24*365.25, P_mech*3600*24*365.25*80))

print("\n== 6. 每级保留率反推（心肌若按 N 级链，实测效率 25%%/30%%/35%% 隐含的 eta） ==")
for n in [2,3,4,5,6,7]:
    line=[]
    for eff in [0.25,0.30,0.35]:
        line.append("n=%d eff=%.2f -> eta=%.3f" % (n, eff, eff**(1.0/n)))
    print("  ".join(line))
print("体系 eta=0.875：n=2 -> 总效率 %.3f ; n=3 -> %.3f ; n=4 -> %.3f ; n=5 -> %.3f"
      % (eta**2, eta**3, eta**4, eta**5))
print("光合对照(体系已有 JC-Q1)：n=3 eta=0.875 -> %.3f vs 文献 ~0.99" % (eta**3))

print("\n== 7. 泛弦比例不变性在体温档的检验 ==")
for name, T in rows:
    a = gen_jia(T)
    print("%-22s f0/f1=%.6f (=12) f0/f2=%.6f (=1.2) 144校核 (f0/f1)^2=%.4f (f0/f2)^2=%.4f"
          % (name, a[0]/a[1], a[0]/a[2], (a[0]/a[1])**2, (a[0]/a[2])**2))

print("\n== 8. 分子尺度的 d=sqrt(eps) 通道（eps=1/64, d=0.125nm） ==")
d = math.sqrt(1/64.0)
print("d = %.4f nm —— 与肌动蛋白丝直径 ~7nm、肌球蛋白粗丝 ~15nm、横桥周期位移 ~5-11nm 同数量级比较用"
      % d)
print("d 的 16 倍 = %.3f nm ; 64 倍 = %.3f nm ; 512 倍 = %.1f nm" % (d*16, d*64, d*512))
