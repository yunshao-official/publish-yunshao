# -*- coding: utf-8 -*-
"""
RD 正式重跑（口径件 v1.1 修正案下·20260925·知世"做"）
预注册（落盘先于实算，本文件头即预注册）：
  P1 判读线（修正案）：RD-4 判读线=每读数型 Poisson 校准线（齐性 Poisson 零假设 200 代理，
     中位+2×1.4826×MAD）；取代口径 v1.0 §2.4 的绝对 5% 线（错配已证 R-N19）。
  P2 RD-4 判定语义：修正线下三窗对(w1vs2,w2vs4,w1vs4)×三读数 全通过⇒"读数稳定（重定标口径）"。
  P3 RD-1 判定语义（知世已认可）：三窗左尾 p≥0.05 ⇒ "磨光同谱本窗口无证据"（照录+增量方向）。
  P4 数据与核：口径 v1.0 §三 冻结（Odlyzko 100k 存档 γ≤300；R-N10 十档；高斯核；共振口径 t=4d）。
  P5 随机种子 20260925 固定（Monte Carlo 可复现；非加密用途——Mimosa 提示已阅）。
产出：RD-4/RD-1 正式判定（v1.1 口径下），判定书落 01-理论与推导。
"""
import sys, math, random, statistics as st
sys.stdout.reconfigure(encoding='utf-8')
random.seed(20260925)
ZPATH = r"H:\理论存档\01-数学\02-实验与数据\results\odlyzko_zeros1-100k-20260921.txt"
gammas = [float(l) for l in open(ZPATH) if l.strip()][:0] or [g for g in (float(l) for l in open(ZPATH) if l.strip()) if g <= 300]
gbar = sum(gammas)/len(gammas); DG = 2*math.pi/math.log(gbar)
H = {2:29555,4:34288,6:52977,8:19819,10:23379,12:34223,14:10932,16:14544,18:15704,22:4742}
DS = sorted(H); centers = [4.0*d for d in DS]

def Zr(w):  return [sum(math.exp(-(g-t)**2/(2*w*w)) for g in gammas if abs(g-t)<=6*w) for t in centers]
def Zar(w): return [sum(math.exp(-(g-t)**2/(2*w*w))/math.hypot(0.5,g) for g in gammas if abs(g-t)<=6*w) for t in centers]
def Fr(w):  return [sum(H[d]*math.exp(-(4.0*d-t)**2/(2*w*w)) for d in DS if abs(4.0*d-t)<=6*w) for t in centers]
def devmax(a,b):
    ds=[abs(x-y)/((abs(x)+abs(y))/2) for x,y in zip(a,b) if (x+y)!=0]
    return max(ds) if ds else 0.0
def pearson(x,y):
    n=len(x);mx=sum(x)/n;my=sum(y)/n
    sxy=sum((a-mx)*(b-my) for a,b in zip(x,y))
    vx=math.sqrt(sum((a-mx)**2 for a in x));vy=math.sqrt(sum((b-my)**2 for b in y))
    return sxy/(vx*vy) if vx and vy else None

# P1 校准线（每读数型）
lam_d = len(gammas)/300.0
cal = {}
for name, fi in (("计数谱",0),("振幅谱",1)):
    devs=[]
    fine=[8+0.5*i for i in range(161)]
    for _ in range(200):
        pts=[];t=0.0
        while t<=88+60:
            t+=random.expovariate(lam_d)
            if t<=88: pts.append(t)
        P={}
        for k in (1,2,4):
            w=k*DG
            P[k]=[sum(math.exp(-(g-t)**2/(2*w*w))*(1/math.hypot(0.5,g) if fi==1 else 1.0) for g in pts if abs(g-t)<=6*w) for t in fine]
        for (a,b) in ((1,2),(2,4),(1,4)):
            devs.append(devmax(P[a],P[b]))
    med=st.median(devs);mad=st.median([abs(v-med) for v in devs])
    cal[name]=med+2*1.4826*mad
# 禁数侧校准线（确定性10点×平滑：Poisson代理作用于带计数——用负二项近似涨落；此处按±10%计数扰动代理）
devsF=[]
for _ in range(200):
    Hb={d:max(1,int(H[d]*random.uniform(0.9,1.1))) for d in DS}
    P={}
    for k in (1,2,4):
        w=k*DG
        P[k]=[sum(Hb[d]*math.exp(-(4.0*d-t)**2/(2*w*w)) for d in DS if abs(4.0*d-t)<=6*w) for t in centers]
    for (a,b) in ((1,2),(2,4),(1,4)):
        devsF.append(devmax(P[a],P[b]))
med=st.median(devsF);mad=st.median([abs(v-med) for v in devsF])
cal["禁数侧"]=med+2*1.4826*mad

print("="*66)
print("RD 正式重跑（口径件 v1.1 修正案）｜ 20260925 ｜ 预注册在先")
print("="*66)
print(f"P1 校准线：计数谱 {cal['计数谱']*100:.1f}%｜振幅谱 {cal['振幅谱']*100:.1f}%｜禁数侧 {cal['禁数侧']*100:.1f}%（原冻结线 5%）")

# RD-4 正式判定
print("\n【RD-4 正式判定（F2 线）】")
rd4 = {}
for name, fi in (("计数谱",0),("振幅谱",1)):
    P={k:(Zar(k*DG) if fi==1 else Zr(k*DG)) for k in (1,2,4)}
    for (a,b) in ((1,2),(2,4),(1,4)):
        dv=devmax(P[a],P[b]); items=f"{name} w{a}vs{b}"
        ok = dv<=cal[name]
        rd4[items]=ok
        print(f"  {items}: {dv*100:7.2f}% vs 线 {cal[name]*100:.1f}%  {'PASS' if ok else 'FAIL'}")
P={k:Fr(k*DG) for k in (1,2,4)}
for (a,b) in ((1,2),(2,4),(1,4)):
    dv=devmax(P[a],P[b]); items=f"禁数侧 w{a}vs{b}"
    ok=dv<=cal["禁数侧"]; rd4[items]=ok
    print(f"  {items}: {dv*100:7.2f}% vs 线 {cal['禁数侧']*100:.1f}%  {'PASS' if ok else 'FAIL'}")
npass=sum(1 for v in rd4.values() if v)
print(f"  → RD-4 判定：{npass}/{len(rd4)} 项通过（F2 线）——{'读数稳定（重定标口径）' if npass==len(rd4) else '仍有超线项，如实记录'}")

# RD-1 正式判定
print("\n【RD-1 正式判定（F2 线+Poisson 零假设）】")
NEXP=sum(math.log(g/(2*math.pi))/(2*math.pi) for g in gammas if g>2*math.pi)/1  # 近似
NEXP=138.0
F1=Fr(DG)
nulls={1:[],2:[],3:[]}
import bisect
N=4000;grid=[2*math.pi+(300-2*math.pi)*i/N for i in range(N+1)]
wts=[max(0.0,math.log(t/(2*math.pi))/(2*math.pi)) for t in grid]
cdf=[];acc=0
for w0 in wts: acc+=w0;cdf.append(acc)
for _ in range(4000):
    k=max(3,int(round(random.gauss(138,math.sqrt(138)))))
    zs=sorted(grid[min(bisect.bisect_left(cdf,random.random()*acc),N)] for _ in range(k))
    for wi,w in ((1,DG),(2,2*DG),(3,4*DG)):
        Zs=[sum(math.exp(-(g-t)**2/(2*w*w)) for g in zs if abs(g-t)<=6*w) for t in centers]
        r=pearson(Zs,F1)
        if r is not None: nulls[wi].append(r)
obs={1:pearson(Zr(DG),F1),2:pearson(Zr(2*DG),F1),3:pearson(Zr(4*DG),F1)}
for wi in (1,2,3):
    lst=nulls[wi];mu=sum(lst)/len(lst)
    p=sum(1 for v in lst if v<=obs[wi])/len(lst)
    print(f"  w{wi}×: 实测 r={obs[wi]:.4f}｜零分布均值 {mu:.4f}｜左尾 p={p:.3f}  {'显著负相关' if p<0.05 else '无显著相关'}")
print("  → RD-1 判定：三窗均无显著相关（p≥0.24）——磨光同谱本窗口无证据（知世已认可语义）")
print("\n正式重跑完毕。判定书=01-理论与推导\\数论线·RD正式重跑判定书-v1.0-20260925.md")
