# -*- coding: utf-8 -*-
# 云韶群论 G-1/G-2/G-6 数值判定脚本 (2026-09-19, ZCode)
# 判定: (Z2)^3半直积作用的合法性; G-6: 48阶子群中心/交换子
import itertools, json
def psgn(p):
    p=list(p); s=1
    for i in range(len(p)):
        for j in range(i+1,len(p)):
            if p[i]>p[j]: s=-s
    return s
S4=list(itertools.permutations(range(4)))
S3=[r for r in S4 if r[3]==3]          # S3嵌入: 固定第4点
N=list(itertools.product([0,1],repeat=3))
def std(eps,r):                         # 模2标准表示: F2^4置换在sum=0/商<1111>
    a,b,c=eps; v=(a,b,c,(a+b+c)&1); w=[0]*4
    for i in range(4): w[r[i]]=v[i]
    return tuple(w[:3])                 # w sum=0, 前3位=商代表
def check(act, G):
    hom=aut=True
    for r1 in G:
        for r2 in G:
            comp=tuple(r1[r2[i]] for i in range(len(r1)))
            for e in N:
                if act(e,comp)!=act(act(e,r2),r1): hom=False
    for r in G:
        for e1 in N:
            for e2 in N:
                s=tuple((e1[i]+e2[i])&1 for i in range(3))
                if act(s,r)!=tuple((act(e1,r)[i]+act(e2,r)[i])&1 for i in range(3)): aut=False
    im=len({tuple(act(e,r) for e in N) for r in G})
    return hom,aut,im
def group_data(act, G):                 # 半直积群 (N x G, 作用act): 中心/交换子
    mul=lambda x,y:(tuple((x[0][i]+act(y[0],x[1])[i])&1 for i in range(3)), tuple(x[1][y[1][i]] for i in range(len(x[1]))))
    E=[(e,r) for e in N for r in G]
    inv={}
    for x in E:
        for y in E:
            if mul(x,y)==((0,0,0),tuple(range(len(x[1])))): inv[x]=y
    center=[x for x in E if all(mul(x,y)==mul(y,x) for y in E)]
    comm=set()
    for x in E:
        for y in E:
            z=mul(mul(mul(x,y),inv[x]),inv[y]); comm.add(z)
    return len(center), len(comm)
out={}
out["G2_literal_shift(6.4字面·奇平移)"]=check(lambda e,r: tuple(x^((1-psgn(r))//2) for x in e), S4)
out["G2_std(模2标准表示)"]=check(std, S4)
c96,k96=group_data(std,S4); c48,k48=group_data(std,S3)
out["G1_192阶子群"]={"中心阶":c96,"交换子阶":k96}
out["G6_48阶子群(N⋊S3)"]={"中心阶":c48,"交换子阶":k48}
print(json.dumps(out,ensure_ascii=False,indent=1))
open(r"H:/理论存档/01-数学/04-工具与代码/results/g12_semidirect_judgment-20260919.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
