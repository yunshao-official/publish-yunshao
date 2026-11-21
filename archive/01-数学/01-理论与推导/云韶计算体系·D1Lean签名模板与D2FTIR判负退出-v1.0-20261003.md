# 云韶计算体系·D1 Lean 签名模板 + D2 FTIR 判负退出记录

> 日期：2026-10-03 ｜ 隶属：四项首跑（判据书 v1.0）实验四 ｜ 性质：文档件

---

## D1 · Lean 4 签名段模板（试点：R16 定理 S1）

用途：预注册判据书增加"Lean 签名段"，把可形式化的判据写成 Lean 4/mathlib 声明；实算通过后以证书回填 `by` 块。本模板只给签名与命题（环境未装 Lean，形式化验证挂账候批）。

```lean
import Mathlib.Data.Matrix.Basic
import Mathlib.Analysis.SpecialFunctions.Log.Basic

/- R16 定理 S1（代数册 12 组完全分辨签名族立项书 v1.2）：
   4-块替换矩阵 T = [[2,-1,-1],[-1,2,-1],[-1,-1,2]] 的谱 = {3, 3, 0}，
   且 S_c(4^k) = (2·3^(k-1), -3^(k-1), -3^(k-1)) 零容差。 -/

def T4 : Matrix (Fin 3) (Fin 3) ℚ :=
  !![2, -1, -1; -1, 2, -1; -1, -1, 2]

theorem T4_char_poly : T4.charPoly = (X - 3) ^ 2 * X := by
  sorry  -- 实算证书回填位：Polyrith/验证器

theorem T4_eigs : T4.eigenvalues = {3, 3, 0} := by
  sorry

/-- 判据书冻结判据的 Lean 形式（模板）：
    预注册判据 P 是一个可判定命题，实算结果 r 必须满足 `P r` 方可通过。 -/
structure FrozenCriterion (α : Type) where
  name : String
  frozen_at : String   -- NTFS 时间戳
  predicate : α → Prop
  decidable : ∀ a : α, Decidable (predicate a)
```

接入制度：判据书 v1.1 起，每条可形式化判据附 `FrozenCriterion` 签名；实算输出 JSON 携带 `criterion_name`+`frozen_at` 对账字段。

## D2 · FTIR 标定回归管线·判负退出记录

- **判据**：路线图第三步条款"无标定数据则判负退出，不空转"。
- **核查**：02-实验与数据目录与 03-高维材料工程目录内无任何 FTIR 实测谱数据文件（31.08THz 写入源/声子峰标定数据为零）。
- **判定**：**判负退出**。E5 材料仿真引擎的回归管线在获得首批 FTIR 标定数据前不启动。
- **重启条件**：知世提供/批准采购 FTIR 标定数据（31.08THz 邻域声子谱，材料候选=YBCO/SrTiO₃/SiC）；届时按判据书 v1.1 重立项。
