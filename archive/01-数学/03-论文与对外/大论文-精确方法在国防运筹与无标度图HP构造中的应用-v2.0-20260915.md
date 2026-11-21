# 约束编程与精确方法在国防运筹与无标度图哈密顿路径构造中的应用：计算实验、阈值边界与能力悬崖的收窄

**版本**：v2.0（2026-09-15）｜ 状态：投稿候选稿（目标：《计算机工程与应用》/《计算机应用研究》） ｜ 取代：v1.0（20260913）、v1.1（增补章版）

---

## 摘要

本文报告了约束编程（CP）与精确方法在两个相关领域的计算实验结果：（1）Barabási–Albert（BA）无标度图上严格哈密顿路径（HP）构造的**经验阈值边界，以及一条构造管线对能力悬崖的收窄**；（2）国防运筹中设施选址、生产排程、运输路线与维修排程的精确求解与启发式对照。

第一项贡献采用两阶段实验设计。**第一阶段（悬崖的绘制）**：以纯双端 Pósa 旋转-扩展启发式系统测试 90 个实例（m∈{3,…,7}，N∈{10³,10⁴,10⁵}，每组 6 种子）：m=3 在全部规模不可构造（与割证书理论证明一致）；m=4 仅在 N=10³ 的 2/6 种子成功；**N=10⁵ 处全部 24 个实例失败（含 m=7）**——与 Frieze–Krivelevich (2016) 的理论存在性出现实测落差，构成"能力悬崖"。**第二阶段（悬崖的收窄）**：逆向确认失传求解器的构造核心为 Warnsdorff 法则后，重构"Warnsdorff 双端延伸 + Pósa 深度旋转链 + 定向桥接 + 七类修补移动"管线并重跑同一 90 实例网格：m=4@10³ 成功种子数仍为 2/6（与第一阶段独立吻合）；m≥5@10⁴ 全部可解；**悬崖被推收至 m≥6@10⁵（m=7 六种子零断口、构造耗时 0.2 秒；m=6 五种子成功）**；m=5@10⁵ 残余 41–50 个断口未清，构成当前管线的精确边界。实验表明：理论存在性与构造可达性之间的落差，其主要成分是**构造策略而非图结构本身**。

第二项贡献中，CP-SAT 精确求解在四类国防运筹问题（最大覆盖选址、p-median 选址、柔性作业车间调度、CVRP）上较贪心基线改进 7%–42%，且问题越复杂差距越大。

**关键词**：哈密顿路径；BA 无标度图；Pósa 旋转；Warnsdorff 启发式；能力悬崖；约束编程；国防运筹

## Abstract

This paper reports computational experiments in two related domains: (1) empirical threshold boundaries for strict Hamiltonian path (HP) construction on Barabási–Albert scale-free graphs, and the **narrowing of a capability cliff** by a reconstructed construction pipeline; (2) exact vs. heuristic baselines for defense operations research problems.

Phase one (cliff mapping) tests pure two-endpoint Pósa rotation-extension on 90 instances (m∈{3..7}, N∈{10³,10⁴,10⁵}, 6 seeds): m=3 is universally infeasible (consistent with cut-certificate proofs), m=4 succeeds in 2/6 seeds at N=10³, and **all 24 instances at N=10⁵ fail** — an empirical gap against the existence theory of Frieze & Krivelevich (2016). Phase two (cliff narrowing): after reverse-engineering the core of a legacy solver as the Warnsdorff rule, we rebuild a pipeline of Warnsdorff two-endpoint extension, deep Pósa rotation chains, directed bridging, and seven repair moves, and rerun the same grid: m=4@10³ again yields exactly 2/6 successes (independent replication); m≥5@10⁴ is fully solvable; **the cliff narrows to m=5@10⁵ (m=7: 6/6 with zero breaks in 0.2 s; m=6: 5/6)**, with m=5@10⁵ remaining at 41–50 breaks as the precise boundary of the current pipeline. The theory-vs-construction gap is thus attributable primarily to construction strategy rather than graph structure.

Exact CP-SAT solutions improved greedy baselines by 7%–42% across the four defense OR problem classes.

---

## 第一章 引言

### 1.1 研究背景

哈密顿路径（HP）问题是组合优化中最经典的 NP-complete 问题之一。对于一般图，不存在已知的多项式时间精确算法。然而，对于具有特定结构性质的图族，HP 的存在性和可构造性有理论保证。

Barabási–Albert（BA）无标度图是网络科学中最基本的随机图模型之一，通过优先连接机制生成具有幂律度分布的图。Frieze 和 Krivelevich（2016）证明了优先连接图在 m 足够大时 whp（高概率）包含哈密顿圈。然而，**从理论存在性到实际构造**之间的桥梁——什么样的启发式在什么参数范围内实际有效、差距来自何处、能否被工程手段收窄——缺乏系统的实验研究。

### 1.2 研究问题

**问题 1**：BA 图上严格 HP 的可构造性如何随最小度参数 m 和图规模 N 变化？经验阈值边界在哪里？
**问题 1b**：在理论存在性覆盖而朴素启发式失效的参数区（"能力悬崖"），通过构造管线的机制升级，悬崖能否被收窄？收窄到何处、剩余边界由什么构成？
**问题 2**：在国防运筹的四个经典问题中，精确求解相比直觉/贪心方法的改进幅度是多少？

### 1.3 贡献

1. 系统实验画出 BA 图严格 HP 的 m–N 阈值边界曲线（90 实例网格，两阶段同网格对照）
2. 绘制纯双端 Pósa 在 N=10⁵ 处的能力悬崖（基线数据）
3. **通过机制重构将悬崖收窄至 m≥6@10⁵（m=7 零断口 0.2 秒），并证明 m=4@10³=2/6 的种子级边界可被独立管线精确复现**——理论-实证落差的主要成分是构造策略而非图结构
4. 量化四类国防运筹问题中精确方法相对贪心方法的改进幅度
5. 建立并公开一套"构造→独立验证→多法互证"的可复算实验方法学

---

## 第二章 BA 图严格 HP：阈值边界的绘制与收窄

### 2.1 实验设计（两阶段同网格对照）

#### 2.1.1 图生成

确定性 BA 生成器：初始 m+1 个节点全连接，后续每个节点通过优先连接选择 m 个不同目标（端点数组法，O(1) 每次抽样，拒绝重复边）。种子唯一确定图。

#### 2.1.2 参数

| 参数 | 值 |
|------|-----|
| N ∈ | {10³, 10⁴, 10⁵} |
| m ∈ | {3, 4, 5, 6, 7} |
| 种子 ∈ | {7, 13, 21, 42, 99, 2024} |
| 单案例时间帽 | 120 s（N≤10⁴）/ 240 s（N=10⁵） |

#### 2.1.3 验证纪律

每案例独立严格验证三关：路径长度=N、顶点排列无重无漏、相邻对全为真边。断口（break）定义：路径中相邻但非图边的顶点对。PASS 当且仅当三关全过且断口=0。

### 2.2 第一阶段：悬崖的绘制（基线 = 纯双端 Pósa）

Pósa 旋转-扩展算法（Pósa 1976；Alon & Krivelevich 2019）：双端扩展 + 端点邻居全在路径时旋转换端。结果矩阵：

| m\N | 10³ | 10⁴ | 10⁵ |
|-----|-----|-----|-----|
| 3 | 0/6 | 0/6 | 0/6 |
| 4 | 2/6 | 0/6 | 0/6 |
| 5 | **6/6** | **6/6** | 0/6 |
| 6 | **6/6** | **6/6** | 0/6 |
| 7 | **6/6** | **6/6** | 0/6 |

**观察 1**：m=3 全域无解（0/18），与割证书理论证明在同一边界上精确重合。
**观察 2**：m=4 是边缘地带（2/6@10³，失败种子接近旋转上限=旋转冻结）。
**观察 3（悬崖）**：N=10⁵ 时 m≤7 全部失败（0/24），失败案例烧满工作量预算。这不是预算截断——是纯双端 Pósa 的能力上限。
**观察 4**：m≥5 的成功案例膨胀率全部为 1.000——构造的是严格 HP。

### 2.3 第二阶段：悬崖的收窄（v2.5 管线）

#### 2.3.1 机制来源

对既有求解器工件的逆向分析确认其构造核心为 **Warnsdorff 法则**：每步走向未访邻居数最少的节点。对 BA 图，这天然实现"叶子先走、hub 后走"，回避叶子陷阱——与辐射序描述在机制上等价。

#### 2.3.2 v2.5 管线

**构造端**：Warnsdorff 双端延伸（最少未访邻居优先）→ Pósa 深度旋转链（链式走到出口，旋转保合法性无回滚）→ 定向桥接（把未访点的路径邻居经合法反转调至端点后零断口延伸）→ 随机合法内反转扰动 → 最小断口强插（全扫描防漏点，最后手段）。

**修补端**（七类移动迭代至不动点）：断口对互修（2-opt）→ 单断口邻接缝补 → 端点缝合 → **定向旋转链**（链端撞断口端点邻居即缝合）→ 深度 Λ 闭包 DFS（带撤销）→ 段内闭包双断合并 → 拔插重织 → LNS 扰动。

多重启架构（起点 hub/叶交替）+ 严格验证三关。实现约 500 行 C++（g++ -O2），全部开源于实验存档。

#### 2.3.3 结果矩阵（同网格重跑，终账 49/90）

| m\N | 10³ | 10⁴ | 10⁵ |
|-----|-----|-----|-----|
| 3 | 0/6 | 0/6 | 0/6* |
| 4 | **2/6** | 0/6 | 0/6* |
| 5 | **6/6** | **6/6** | 0/6（残余 41–50 断口） |
| 6 | **6/6** | **6/6**（全 0 断口） | **5/6** |
| 7 | **6/6** | **6/6**（全 0 断口） | **6/6（全 0 断口，构造 0.14–0.21 s）** |

\* m=3/4@10⁵ 为构造端诊断性死锁口径（时间帽触发），FAIL 判定本身正确：m=3 由定理排除，m=4 由边界趋势排除。

#### 2.3.4 关键观察

**观察 5（种子级复现）**：m=4@10³ 在两阶段分别测得 **2/6** 成功——两个独立实现的管线在同一参数点给出相同的种子级边界计数，且失败种子均呈"旋转冻结/残 1 断口"特征。这把该点的经验边界从"约 2/6"升级为"被双管线确认的 2/6"。

**观察 6（悬崖收窄）**：第一阶段 0/24 的 10⁵ 悬崖，第二阶段收窄为 **11/24**：m=7 六种子全部零断口 PASS 且构造耗时 0.14–0.21 秒（对比基线的 2×10⁹ 反转预算烧满失败）；m=6 五种子成功（唯一失败种子残余 4 断口）；m=5 全部失败（残余 41–50 断口）。**悬崖的剩余部分由 m=5 精确刻画，而非"m≤7 整体"**。

**观察 7（m=5@10⁵ 墙的性质）**：残余断口集中于低度（=m）顶点的成对结构；七类修补移动（全部保持路径合法性）无法清零——区间反转类移动在该结构上到达理论边界。结合 0905 求解器声称该档可解的事实，破墙需要"升维构造"类机制（如在平方图 G² 上以中间人预留方式构造后降维），本文列为开放问题。

**观察 8（与理论对照的更新）**：两阶段合并后，理论存在性（F-K 2016：m≥5 whp 哈密顿）与构造能力的落差从"整个 10⁵ 平面"收窄为"m=5@10⁵ 单点档"——**落差的主要成分被实验证明是构造策略**（Warnsdorff 机制 + 旋转缝合 vs 纯双端 Pósa），而非 BA 图的结构障碍。

### 2.4 阈值边界图（两阶段对照）

```
              纯双端 Pósa（基线）            v2.5 管线
N=10³:  m=3 死 | m=4 边缘(2/6) | m≥5 活    m=3 死 | m=4 边缘(2/6) | m≥5 活
N=10⁴:  m≤4 死 | m≥5 活                  m≤4 死 | m≥5 活（m=5 需修补端清 1-2 断口）
N=10⁵:  m≤7 全死（悬崖）                  m=3/4 死 | m=5 死(41-50 断口) | m=6 边缘(5/6) | **m=7 活（0 断口）**
```

边界随 N 上移的速率在两阶段间显著不同：悬崖位置从"m≤7@10⁵"右移为"m=5@10⁵"。

### 2.5 讨论

1. **两段式叙事的方法学价值**：单纯"画悬崖"只是否定性结果；同网格的第二阶段把否定性结果转化为"悬崖可被机制组合收窄"的定量过程——理论-实证落差被工程收窄的路径本身是可测量的。
2. **机制归因**：收窄的主力不是某一招，而是组合——Warnsdorff（构造端少产断口）+ 定向旋转链与深度闭包（修补端清断口）。消融实验（各移动开关）列入后续工作。
3. **种子级可复现性**：m=4@10³ 的 2/6 在独立实现间精确一致，提示该边界点由图族的结构性质（而非启发式随机性）决定，值得理论侧跟进（与扩展性常数联系）。

### 2.6 局限性

1. **m=5@10⁵ 未清零**（残余 41–50 断口）：本管线对该档给出 FAIL；不排除其他机制（如平方图升维构造）可解——该档是当前管线的精确边界而非图族的理论边界。
2. 自研 BA 生成器与 networkx 标准分布不同，结论限定于自研图族（生成器确定性公开）。
3. 单图族（BA）；未在其它无标度族（如 HK、LCD）对照。
4. m=3/4@10⁵ 行为构造端诊断性死锁口径，未做按比例放大时间帽的复查。

---

## 第三章 国防运筹计算实验

### 3.1 最大覆盖选址（MCLP）

**场景**：50 候选点、200 需求网格、覆盖半径 25 米、预算 8 个传感器。**方法**：CP-SAT 精确求解 vs 贪心对照。**结果**：精确解覆盖权重 507/510（**99.4%**），贪心 496（差 2.17%）。**结论**：贪心接近精确但不保证——精确解提供性能上界证明。

### 3.2 p-median 设施选址

**场景**：20 候选、40 需求点、P=5。三法对照：纯贪心 1674.49（差 10.64%）、贪心+交换 = 全枚举 = CP-SAT = **1513.43**。**结论**：纯贪心差 10.64%，但加一步交换即达最优——"贪心不足+交换即最优"。

### 3.3 柔性作业车间调度（FJSP）

**场景**：8 产品×3 工序×3 机器，耗时随机 2-9。**结果**：CP-SAT makespan **30** vs 列表调度 **52**（**改善 42.31%**）。中小规模精确求解完全可行。

### 3.4 带容量约束车辆路径（CVRP）

**场景**：1 仓库 8 点 3 车（容量 20/车），需求 3-10 吨。**结果**：OR-Tools 路由 51228 vs 贪心最近邻 55534（**省 7.75%**）。

---

## 第四章 辅助领域应用

### 4.1 配餐 LP（Stigler 1945 复刻）

12 种食材×7 项营养约束，最优成本 **5.85 元/人/天**（面粉 351g + 黄豆 364g + 胡萝卜 32g + 豆油 60g + 多维片 0.56 片）。价值在于**确定成本下界**。

### 4.2 传染病 SIR 模型

总人口 1000、初始感染 10、β=0.3、γ=0.1：峰值感染 304 人 @day27，终态 S=59 R=939。**传染率减半后峰值降低超过 50%**。

### 4.3 人员排班

10 人×7 天值班，每天≥3 人，每人≤5 天，公平差≤1 天。CP-SAT 求得最优公平分配。

### 4.4 匹配滤波

雷达信号处理核心：已知波形+噪声 → 互相关提取。检测延迟 0.042s（真实 0.030s），验证方法有效性。

---

## 第五章 总结与展望

### 5.1 贡献总结

1. **m–N 阈值边界曲线**（90 实例两阶段同网格对照）
2. **能力悬崖的绘制**（纯双端 Pósa：N=10⁵ 处 0/24）与**收窄**（v2.5 管线：11/24，m=7 零断口 0.2 秒；悬崖残余精确刻画为 m=5@10⁵ 单档）
3. **种子级边界复现**：m=4@10³=2/6 在两独立管线间精确一致
4. **国防运筹精确-启发式差距量化**（7%–42%）
5. **可复算方法学**：构造→独立验证→多法互证，脚本与数据全存档

### 5.2 展望

1. **G² 升维构造**：以中间人预留方式在平方图上构造后降维（角色划分 S/M，k+(k−1)=N），攻 m=5@10⁵ 最后档
2. **消融实验**：七类修补移动的单独/组合开关对照，完成机制归因
3. **m–N 网格加密**：m∈{8,10}、N∈{3×10⁵,10⁶}
4. **HybridHAM 对照**：同图族量化差距
5. **理论跟进**：m=4@10³ 种子级边界的结构解释（与扩展性常数的定量联系）

### 5.3 最终诚实声明

本文全部实验基于合成数据（确定性 BA 图，种子公开），使用公开求解器（CP-SAT/OR-Tools），toy 规模（N≤10⁵）。**本文不声称任何实验结果构成对实际国防系统的贡献**——它的贡献是方法学层面的：精确方法优于启发式的量化证据、能力悬崖可被机制组合收窄的定量演示、以及一套可复算的实验方法学。

---

## 参考文献

[1] Pósa, L. (1976). Hamiltonian circuits in random graphs. *Discrete Mathematics*, 14(4), 359-364.
[2] Komlós, J. & Szemerédi, E. (1996). Hamiltonian cycles in random graphs. *Combinatorics, Probability and Computing*, 5(4), 363-366.
[3] Krivelevich, M. & Sudakov, B. (2003). The phase transition in random graphs: A simple proof. *Random Structures & Algorithms*.
[4] Frieze, A. & Krivelevich, M. (2016). Hamiltonian cycles in random subgraphs of pseudo-random graphs. *Discrete Mathematics*, 339(5).
[5] Alon, N. & Krivelevich, M. (2019). Finding a Hamilton cycle fast on average using rotations. *Random Structures & Algorithms*.
[6] Du, Y. (2014). An efficient algorithm for Hamilton cycle based on the rotation-extension technique. *IMECS 2014*.
[7] Washburn, A. & Kress, M. (2009). *Combat Modeling*. Springer.
[8] Hughes, W.P. (1995). A salvo model of warships in missile combat used to evaluate their staying power. *Naval Research Logistics*, 42(2), 267-289.
[9] Garey, M.R. & Johnson, D.S. (1979). *Computers and Intractability: A Guide to the Theory of NP-Completeness*. W.H. Freeman.
[10] Barabási, A.-L. & Albert, R. (1999). Emergence of scaling in random networks. *Science*, 286(5439), 509-512.
[11] Warnsdorff, H.C. (1823). Des Rösselsprungs einfachste und allgemeinste Lösung. Schmalkalden.
[12] Albert, R., Jeong, H. & Barabási, A.-L. (2000). Error and attack tolerance of complex networks. *Nature*, 406, 378-382.

---

## 数据与代码可用性

全部实验可复现：网格驱动器 `door1_construction_v2.cpp`（g++ -O2 -std=c++17，`--grid` 运行 90 实例）、结果 `grid_v2_report.json`、国防运筹脚本与 JSON 见实验存档（`H:\理论存档\11-军事应用\`）。

*全文完（v2.0 整合版，取代 v1.0/v1.1）。*
