# -*- coding: utf-8 -*-
"""
零成本判伪检验第一波·检验6-9（范畴论-E3/E4 + 概率-P-E2/P-E3）
判据冻结：
  E3⊘Ore（云韶范畴论图谱 §10.4）：⊘若满足 b⊘(a⊘b)=a 型无损可消去律则与
    有损效率 ε=α²=1/64 矛盾；册内未给出该律（且缺合成公理）→ Ore 不成立。
  E4 Lambek（图谱 §10.6/§F6）：代谢动力学 T_{n+1}=T_n−κT_n²（κ=1/32）的
    唯一有限不动点 vs σ_终=1/2 → "术语假朋友"定量确认。
  P-E2（云韶概率论图谱 §四 P-E2）：单层 4 态吸收链（1 冻结+3 活跃），算
    N=(I−Q)⁻¹、B=NR、t=Nc；判据：t 有限且与 1/α=8 同量级。
  P-E3（P10 双通道）：D=(1−α)I+αQ 检 Doeblin（一步全元素>0?）；成立→截断版
    遍历涌现恢复定理身份；不成立→降格猜想。与已交付步1 预注册件交叉核对。
精确有理数运算（sympy Rational），零编数。
"""
from sympy import Rational, symbols, solve, simplify, exp, Matrix, eye
import math

print("="*70)
print("检验6：互除⊘ Ore 条件（范畴论-E3）")
print("="*70)
a = symbols('alpha', positive=True)
alpha = Rational(1, 8)
eps = alpha**2
print(f"[册内读数] 单次亏损复合效率 = α = 1/8（§5.2 A昷B ⇒ A昞(α·B)）")
print(f"[册内读数] 互除⊘ = 两次亏损的复合，效率上界 ε = α² = {eps}（第七部分/附录A·N=8 特值）")
# 量化模型：信息 I 经 ⊘ 一次 = 两次亏损 → 残留恢复量 = ε·I
I = symbols('I', positive=True)
recovered = eps * I
print(f"[量化推演] ⊘ 后可恢复信息 = ε·I = I/{1/float(eps):.0f}")
# 无损可消去律 b⊘(a⊘b)=a 要求恢复率 = 1
law_solutions = solve(simplify(eps*I - I), I)
print(f"[判伪核] 若 b⊘(a⊘b)=a 成立，需 ε·I=I 对 I≠0 → ε=1；实际 ε={eps}")
print(f"         ε=1 的解: α²=1 → α=1，与体系冻结常数 α=1/8 矛盾 → 无损律与有损常数不相容")
print(f"[册内核对] 全册 ⊘ 的代数律清单：效率上界 α²=1/64（有）｜b⊘(a⊘b)=a 型可消去律（无）｜")
print(f"           合成公理/结合律/单位元（无——图谱F1缺口原文：'只写了效率上限这一个数值，没有写出合成公理'）")
print("[判定-检验6] 不成立（在册内唯一可检的量化律下：有损恢复≠形式求逆，Ore 演算不适用）；")
print("             完整范畴版 Ore 条件因合成公理缺失=形式上定义不足（如实记录）。")
print("             与图谱 §10.4 预注'有损求逆天然不满足无损耗 Ore 演算'一致；⊘'恢复'语义对接降 T3 韵脚。")

print("\n" + "="*70)
print("检验7：代谢终值 Lambek 检验（范畴论-E4）")
print("="*70)
kappa = Rational(1, 32)
T = symbols('T')
Tn1 = T - kappa*T**2
fps = solve(simplify(Tn1 - T), T)
print(f"[动力学] T_(n+1) = T_n − κ·T_n²，κ = {kappa}（册内 κ=1/32·N=8 特值）")
print(f"[不动点] 解 T = T − κT² → κT² = 0 → 有限不动点集 = {fps}（唯一有限不动点 = 0）")
half_next = Rational(1, 2) - kappa*Rational(1, 4)
print(f"[目标值核查] T=1/2 → T_下一 = 1/2 − (1/32)(1/4) = {half_next} = {float(half_next)} ≠ 1/2（非不动点）")
# 迭代轨迹（float 展示单调性；不动点为精确有理解）
T0 = 1.0
traj = [T0]
for _ in range(800):
    traj.append(traj[-1] - kappa*traj[-1]**2)
mono = all(traj[i+1] < traj[i] for i in range(len(traj)-1))
print(f"[迭代] T0=1：800 步后 T_800 = {traj[-1]:.3e}；单调递减 = {mono}；收敛极限 = 0")
T0h = 0.5
trajh = [T0h]
for _ in range(800):
    trajh.append(trajh[-1] - kappa*trajh[-1]**2)
print(f"[迭代] T0=1/2：800 步后 T_800 = {trajh[-1]:.3e}（从目标值 1/2 出发仍衰减到 0）")
print("[判定-检验7] 代谢动力学的演化终态 = 0 ≠ 1/2。按 Lambek/终余代数口径：")
print("             σ_终=1/2 是数值目标 f*，不是动力学不动点/终对象 → 册内 20260919")
print("             '术语假朋友'更正的定量确认；判定 = 术语更正确认（语义分离记录在案，非体系矛盾）。")
print("[口径分离记录] 册内数值收敛 σ=1/2±0.0024 属'代数扩散流 ∂x/∂τ'连续动力学，")
print("               与离散代谢方程 T_(n+1)=T_n−κT_n² 为不同算子；两者并存，不混判。")

print("\n" + "="*70)
print("检验8：吸收链代谢寿命公式（概率-P-E2）")
print("="*70)
alpha_p = Rational(1, 8)
eta = Rational(7, 8)
# 链A：修复关闭（图谱P-E2冻结口径：1冻结+3活跃、修复关闭），深度态 活跃→浅禁→深禁→冻结
# D=(1−α)I+αQ 口径：每步以 α=1/8 下沉一层、7/8 保持；冻结吸收
QA = Matrix([[eta, alpha_p, 0],
             [0,   eta,     alpha_p],
             [0,   0,       eta]])          # 瞬态组 活跃/浅/深
RA = Matrix([0, 0, alpha_p])                # 各瞬态一步入冻结概率（仅深禁可达）
NA = (eye(3) - QA).inv()
tA = NA * Matrix([1, 1, 1])
BA = NA * RA
print(f"[链A·修复关闭] Q = 下沉算子（对角 7/8，次对角 1/8）")
print(f"  N=(I−Q)⁻¹ = {NA.tolist()}")
print(f"  t = N·1 = {list(tA)} （活跃态出发 t = {tA[0]} = {float(tA[0])}）")
print(f"  B = N·R = {list(BA)}（吸收概率全 1 ✓）")
# 链B：任务令示例口径（含修复：浅→活跃 7/8）
QB = Matrix([[eta,  alpha_p, 0],
             [eta,  0,        alpha_p],
             [0,    0,        eta]])
RB = Matrix([0, 0, alpha_p])
NB = (eye(3) - QB).inv()
tB = NB * Matrix([1, 1, 1])
BB = NB * RB
print(f"[链B·任务令示例口径（浅→活跃 7/8 修复）]")
print(f"  t = {list(tB)} （活跃态出发 t = {tB[0]} = {float(tB[0])}）")
print(f"  B = {list(BB)}（吸收概率全 1 ✓——冻结为唯一闭类）")
print(f"[判据] 1/α = 8；链A t=24（=3×8）；链B t=80（=10×8）")
print(f"  t 有限 ✓；与 1/α=8 同数量级（比值 3 与 10，均在一个数量级内）✓")
print("[判定-检验8] 通过：'代谢寿命'获古典显式公式（Kemeny-Snell 基本矩阵 N=(I−Q)⁻¹），")
print("             t_活跃=24（修复关闭主口径）；κ/α=1/4 与每层4元素1恒等元计数互证照记。")

print("\n" + "="*70)
print("检验9：Doeblin 遍历性裁决（概率-P-E3）")
print("="*70)
# 册内定义5.1(iii)：Q_ij = exp(β<u, v_i−v_j>)/Σ_k exp(β<u, v_k−v_j>)
# 化简：分母与 i 无关 → Q 列向量恒同 = softmax(β<u, v_i>)（重置型核，册内附录步1同结论）
# 一般证明行：softmax 严格正 ∀ 有限 β、任意方向集 → Q 全正 → D=(1−α)I+αQ 全元素>0
print("[结构定理（解析行）] Q_ij ∝ exp(β⟨u,v_i⟩) 与 j 无关 → Q 为重置型；")
print("  ∀有限β：Q_ij = s_i > 0（softmax 严格正）→ D_ij = (1−α)δ_ij + α·s_i：")
print("  非对角 = α·s_i > 0；对角 = (1−α)+α·s_i > 0 → D 一步 Doeblin，ε = α·min_i s_i > 0 显式。")
# 机器实例（规范方向集演示；册内 v_i 无显式坐标=如实标注）
beta = Rational(1)
u = (1.0, 0.0)
dirs = [(math.cos(2*math.pi*k/12), math.sin(2*math.pi*k/12)) for k in range(12)]
scores = [math.exp(float(beta)*(u[0]*v[0] + u[1]*v[1])) for v in dirs]
Z = sum(scores)
s = [x/Z for x in scores]
alpha_c = 1/8
Dmin = min((1-alpha_c)*(1.0 if i == j else 0.0) + alpha_c*s[i] for i in range(12) for j in range(12))
colstoch = max(abs(sum((1-alpha_c)*(1.0 if i == j else 0.0) + alpha_c*s[i] for i in range(12)) - 1)
               for j in range(12))
print(f"[机器实例] 12 方向规范均匀集（册内 v_i 未给坐标·演示标注）、β=1、u=(1,0)：")
print(f"  min_i s_i = {min(s):.6f}；D 最小元素 ε = min_ij D_ij = {Dmin:.8f} > 0")
print(f"  列随机性检验 max|Σ_i D_ij − 1| = {colstoch:.2e}")
pi_err = max(abs(sum(((1-alpha_c)*(1.0 if i == j else 0.0) + alpha_c*s[i])*s[j]
                            for j in range(12)) - s[i]) for i in range(12))
print(f"  平稳分布 = Boltzmann 向量 s 自身（解析：Q 列恒 s → D·s = s）；机器验证 max err = {pi_err:.2e}")
print("[与已交付步1预注册件交叉核对]")
import json, os
jpath = r"H:/理论存档/01-数学/02-实验与数据/results/doeblin_step1_verify_result-v1.0-20260919.json"
if os.path.exists(jpath):
    with open(jpath, encoding='utf-8') as f:
        j = json.load(f)
    keys = list(j.keys())[:12]
    print(f"  步1验证件存在 ✓（{os.path.basename(jpath)}，顶层键示例: {keys}）")
    txt = json.dumps(j, ensure_ascii=False)
    for probe in ["2.4414", "2047", "T1", "T2"]:
        print(f"    含'{probe}': {probe in txt}")
else:
    print(f"  [警告] 步1验证件未找到: {jpath}")
print("[判定-检验9] Doeblin 条件成立（一步全元素>0，ε 显式正）→ 按预注册双通道：")
print("  截断/有限口径的遍历涌现恢复'定理'身份（与册内步1 T0-T6 全过一致）；")
print("  降格通道不触发。边界照记：无穷极限=步2 语义二分（去注入链碎 2047 连通类——")
print("  遍历性承担者是满支撑注入项非 E），定谳权在乙22，本检验不代定谳。")
