# gen_tables报告-20260916（工具3 gen_tables.py 首跑·复算）

> 执行器层·主流软件工程·纯stdlib·禁API  
> 运行时间：2026-09-17 02:18:51 ｜ 常数正本：00-其他/constants.yaml（v1.0）

## 1. 数据文件定位（glob，读得到哪个算哪个）

| 数据件 | 定位结果 |
|---|---|
| theta_table*.json | 03-高维材料工程/04-工具与代码/theta_table_20260914.json |
| verdict_pkg_batch10.json | 03-高维材料工程/工艺仿真工具/results/verdict_pkg_batch10.json |
| ys_9d_material.json | 03-高维材料工程/工艺仿真工具/results/ys_9d_material.json |
| ys_field_recalc.json | 03-高维材料工程/工艺仿真工具/results/ys_field_recalc.json |

注：theta_table* 不在 results/，glob 于 03-高维材料工程 域内找到
04-工具与代码 下的派生件（与 constants.yaml theta_table.generator
口径一致：工艺仿真工具/theta_table_20260914.py 派生）。

## 2. 逐项复算（声明值 vs 实值，不编造任何数）

| 判定 | 校验项 | 声明值（constants.yaml） | 实值（数据文件） | 数据来源 | 说明 |
|---|---|---|---|---|---|
| **复算一致** | ①a α_w=1/8 ← theta_table N=8 行 alpha | 0.125（容差0.5%） | 0.125（偏差 +0.000%） | 03-高维材料工程/04-工具与代码/theta_table_20260914.json | θ表 N=8（写入相空间基准锚） |
| **复算一致** | ①b α_m=1/6 ← theta_table N=48 行 alpha | 0.16666666666666666（容差0.5%） | 0.16666667（偏差 +0.000%） | 03-高维材料工程/04-工具与代码/theta_table_20260914.json | θ表 N=48（材料本体层） |
| **复算一致** | ①c α_w=1/8 ← ys_field_recalc 扇区阶梯 N=8 行 alpha | 0.125（容差0.5%） | 0.125（偏差 +0.000%） | 03-高维材料工程/工艺仿真工具/results/ys_field_recalc.json | 扇区阶梯复算件 |
| **复算一致** | ② α_m=1/6 ← ys_9d_material.alpha | 0.16666666666666666（容差0.5%） | 0.16666666666666663（偏差 -0.000%） | 03-高维材料工程/工艺仿真工具/results/ys_9d_material.json | 9维材料包（N=3 表外延直算行） |
| **复算一致** | ③ d_m≈0.167nm ← ys_9d_material.d_nm | 0.167（容差0.5%） | 0.16666666666666663（偏差 -0.200%） | 03-高维材料工程/工艺仿真工具/results/ys_9d_material.json | 与 FCC a/2=0.1786nm 差6.5%（复算一致口径） |
| **复算一致** | ④ verdict within_2x 全=1 | 全部=1 | 10 行全部=1 | 03-高维材料工程/工艺仿真工具/results/verdict_pkg_batch10.json | 共 10 材料 |

## 3. 结论

- 复算一致：**6** 项
- 不一致：**0** 项
- 数据缺失：**0** 项

全部校验点与 constants.yaml v1.0 声明值一致（复算一致，
执行器层机械对照；体系量值本身仍带「体系内部定义·未验证」标签）。

---
口径注：α_m=1/6 与 d_m=0.167 为三位舍入口径，容差 0.5%；
α_w=1/8 理论上应精确相等，同表按 0.5% 容差复核（实际偏差 0）。
标签：执行器层·主流软件工程（复算一致=机械对照通过；物理未验证）。
