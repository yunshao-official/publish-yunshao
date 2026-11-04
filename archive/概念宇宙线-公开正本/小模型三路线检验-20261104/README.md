# 概念宇宙 × 小模型：三条路线全检验 v1.0-20261104

> 日期：2026-11-04｜执行：Qoder（default）｜环境：4 vCPU / 7 GB / 28 GB / 无 GPU
> 模型：Qwen2.5-0.5B-Instruct（494M，fp32）｜种子：20261104｜分级标签：**管线检验·非对真实宇宙的判定**

本目录是"概念宇宙接到小模型"这一问的完整落地：三条零训练/轻训练/手术路线、一轮数值复算、一轮攻防，全部脚本、原始结果与执行报告。

---

## 一、结论（分层，不是一句话通过）

| 路线 | 做了什么 | 域内 | 域外/安全 | 判定 |
|---|---|---|---|---|
| A 检索（零训练） | 18,801 键 kNN-LM 插值，λ 扫描 | ppl 50.06 → **28.69**（−42.7%），recall@16 55.9% | **1 条投毒即改写 top-1** | 质量 PASS / 安全 FAIL |
| B LoRA（轻训练） | r=8 q/v，40 步，79 s | ppl 50.06 → **34.96**（−30.2%） | 域外 ppl 46.04 → **82.17**（+78.5%） | 域内 PASS / 域外 FAIL |
| C1 steering | layer-12 均值差向量，±0.05…0.2 | 不具概念选择性（数学位移 > 生物） | ±1 起 OOD 145/432，±2 达 3.7k/11.4k | FAIL |
| C2 编辑 | 末层 MLP rank-one 写入 | 成功率 100% | naive 伤邻居 −91%；投影保邻居但要 η=0.6、ppl +93% | PARTIAL |

一句话：**检索过质量关过不了投毒关；LoRA 过域内关过不了域外关；steering 在 0.5B 上不过选择性关；rank-one 编辑过单点关过不了"成功—邻居—困惑度"三关。**

## 二、边界（必须先读）

本轮的"宇宙"不是她那个 45.2 MB 本体，而是用 v1.1 书稿自建的 28,874 字符玩具宇宙（257 训练段 / 64 测试段，4,829 查询 token）。真实资产（`l1_universe_28L/`、`sem_edges.txt`、2,322,700 trigram 类、2048 簇心）**在仓库里是 0 个二进制文件**，语法门也不是 Qwen3-30B-A3B。

| 项 | 本轮 | 真实资产 |
|---|---|---|
| 宇宙 | 书稿 28.9 k 字符 | 45.2 MB 本体；28 层 × 2500 块 memmap |
| 索引 | 18,801 键 × 896 维（layer 12） | V=129,280；455,808 kNN 边；2,322,700 trigram |
| 语法门 | Qwen2.5-0.5B-Instruct | Qwen3-30B-A3B（本机不可能） |

所以本目录只回答"这套接法在最小规模上是否成立、会在哪里坏"，不回答"她的宇宙质量如何"。

## 三、文件

| 路径 | 内容 |
|---|---|
| `report.md` | 完整执行报告：边界、方法、结果表、12 条判定与攻防记录、迁移条件 |
| `scripts/common.py` | 模型装载、书稿分段（257/64）、隐状态、logprob/ppl、bootstrap |
| `scripts/01_datastore.py` | 建 datastore（18,801 键 + 下一 token），143 s |
| `scripts/02_retrieval.py` | kNN-LM 插值 λ 扫描 + recall@k，64 s |
| `scripts/03_lora.py` | LoRA r=8 训练与域内/域外困惑度，79 s |
| `scripts/04_steering.py` | 均值差概念向量、±0.2 剂量扫描、二选一方向性 |
| `scripts/05_edit.py` | rank-one `down_proj` 写入，η 扫描（naive） |
| `scripts/05b_edit_local.py` | naive vs 零空间投影对照（保 η/κ/ε 三条邻居） |
| `scripts/06_attack.py` | 检索投毒（1 条 / 10 条）与 η 题投毒 |
| `scripts/07_verify_book.py` | v1.1 书稿 28 个数值独立复算 |
| `results/*.json` | 上列各步的原始输出（未加工） |
| `artifacts/lora_gate/` | LoRA 适配器（2.1 MB），可直接加载复现 |
| `artifacts/steer_bio.npy` | 生物方向向量（896 维，layer 12） |

## 四、复现

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers peft
huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct --local-dir qwen05

export QWEN_DIR=$PWD/qwen05     # 或把 qwen05 放到脚本同级
cd scripts
python3 01_datastore.py && python3 02_retrieval.py && python3 03_lora.py
python3 04_steering.py && python3 05_edit.py && python3 05b_edit_local.py
python3 06_attack.py && python3 07_verify_book.py
```

`common.py` 用 `YUNSHAO_REPO`（默认按脚本位置上溯 4 级到仓库根）定位 v1.1 书稿，用 `QWEN_DIR` 定位模型；脚本在**当前目录**写出 `datastore.npz`、`lora_gate/`、`steer_bio.npy`。

## 五、复算：v1.1 的 28 个数值

28/28 通过，最大相对误差 0.90%（440/12=36.67 对 37 的取整）。代表项：f_c=6.462477 THz、f₀=413.5986 THz、λ₀=724.839 nm、exp(−64)=1.603810×10⁻²⁸、64k_BT=165.04 kJ/mol、REE=1691.77 kcal/日、四小器官 3.84 kg/5.486% 与 977.6 kcal/57.786%、质量通量比 6.970、ATP 41.28 kg/日、SV@HR30=166.67 mL、EDV=256.41 mL、13.272 W/cm²。

即：v1.0 的错误在**建模对象**（无器官、无分区、无通量），不在这批常数与算术。

## 六、迁移到真实宇宙的五个条件

1. 先接资产：`l1_universe_28L/`、`sem_edges.txt`、trigram 表、2048 簇心，缺一不可。
2. 词表桥：V=129,280 对 Qwen 151,936，要么文本中介，要么 WECHSEL 式嵌入嫁接（词表错位本身就是"七病"之一）。
3. 采样密度：本轮字符数比真实 trigram 规模小两个数量级，按采样密度定理，本轮质量是**下界**不是上限。
4. 语法门尺寸：0.5B 只验管线；30B 门需租 GPU 或降级 7B Q4。
5. 判定门槛：真实宇宙上重跑 A，若 recall@16 < 70% 先修索引；若投毒仍能单条改写 top-1，先加来源约束（多源法定人数、来源签名、距离阈值、模型复核）再谈生成。

## 七、与正本的关系

不改动任何既有正本。本目录是把《概念宇宙接入30B语法门·完整施工提示词-v1.0》里的"生成器/候选源"分工，在 0.5B 上做的一次最小可判伪落地；结论与 `概念宇宙线文献批3-质量差距三段定量`、`批4-引擎七病旧正典` 的方向一致：**瓶颈在索引与来源可信度，不在"换更大的门"**。
