# ETH 证伪宣称 · 旧体系文献台账与检索日志 v1.0

> **摘要头**｜标题：ETH证伪宣称·旧体系文献台账与检索日志｜日期：2026-10-28｜版本：v1.0｜状态：**文献层·未复算**（外部结论，不入体系计算口径）｜性质：lit-harvest 六段全流程件（需求界定→检索→抓取→读卡→分级→引用）｜触发：知世 2026-10-28 令"那你收集相关文献呢？"，针对环球科学转述的 OpenAI《The Exponential Time Hypothesis is False》宣称证伪指数时间假说（ETH）一事｜依赖：`00-其他/总纲索引/00-工作总纲-v1.0-20261027.md` §四文献闸、`G:/AI/publish-yunshao/indexes/04-双语检索工作包-v1.0-20261027.md` §二A3/§四｜一句话：把"ETH 被 AI 证伪"从新闻还原为**可回链、可分级、可判负**的材料——一手 **15** 件（本地留档 **20** 文件，含哈希与截断标注；其中 openai/math 仓库 Lean 侧 2026-10-28 二次现取 **7** 件）+ 外部来源 29 条（A/B/C/D 四级）+ 我方档案对照 5 件——并逐条标出**对我方档案有约束力的位置**（04 域 E3 SAT 升级格、能力边界"三条打不破"、13 域 YGC、09 域核查纪律）。
> 原始材料落位：`01-数学/01-理论与推导/sources-ETH证伪宣称-20261028/`（20 件：论文 PDF + 正文抽取件 3 + Lean 侧 7 + 两份声明正文与 HTML 原件 + 仓库 README + `formalization.yaml` 截断件 + 书目抽取件）；检索程序与日志：`00-其他/总纲索引/_tools/`（`lit_fetch2.py` 检索器、`lit_log.tsv` 逐库日志 14 条、`lit_arxiv.jsonl` 82 条去重前记录、`lit_doi.jsonl` 22 条标识符反查、`raw/` 原始响应 24 件、`lean_fetch_log.tsv` **二次现取与 404 负结果逐条日志**、`verify_eth_ledger.py` + `verify_out.txt` 引用行号与留档核验件）。

---

## 一、检索契约（第 1 段：先写判据，再动手）

| # | 待答问题 | 检索意图（可判定） | 停止条件 |
|---|---|---|---|
| Q1 | ETH/SETH 的**原始定义**究竟是什么？我方引用是否走样 | 拿到 IP01/IPZ01 原始出处（期刊+DOI），不靠科普转述 | 两篇均有 DOI 且 Crossref/OpenAlex 一致 |
| Q2 | OpenAI 的算法**声明的确切时间界**是什么（论文版 / Lean 版是否同一条） | 必须读预印本正文定理原文，不接受二手摘要 | 取到 Theorem 1.1 原文与 lean/docs/378.md 对照 |
| Q3 | "证伪 ETH"对**已有下界文献**的冲击范围（数百篇条件性下界） | 抽样 5–8 篇 ETH/SETH 条件下界代表作，判定其结论是否需重写 | 每类至少 1 篇带 arXiv ID 可回链 |
| Q4 | 与我方 **04 域 E3 SAT 升级格 / 网格图哈密顿线**是否同源 | 检 SAT×Hamiltonian×网格图 的 2024–2026 新方法 | 命中≥2 篇近期可对标件 |
| Q5 | 与我方 **13 域 YGC 密码 NP 完全**是否相关 | 检 ETH 与单向函数/电路下界的联系 | 取到 Appendix C 原文与 Wil/Oliveira 线 |
| Q6 | **Lean 形式化的实际覆盖度**（"已验证"到什么程度） | 取 lean 目录、formalization.yaml、ComparatorChallenges 源文件本体 | 拿到 .lean 源文件与 sorry 位置 |
| Q7 | 学界对 **AI 产出证明的核查责任**如何安排 | 取原作者公开信、AGMAI 声明原文 | 两文件正文取得 |

**纳排**：纳=同行评审文献、作者方一手预印本/官方仓库、提出者本人声明、权威机构声明；排=不带标识符的自媒体转述（本件仅收 1 条作触发源并标 D 级）。
**引用格式**：全件走 `[作者年份] + 可点链接 + ID/DOI`；**仅有元数据未读正文者一律标 `metadata-only`，不得进支撑**（lit-harvest 铁律六）。

---

## 二、检索日志（第 2 段：逐库留原文，空命中如实记）

| 库/通道 | 语句（中英双轨） | 日期时间 | 命中总数 | 入库保留 | 备注 |
|---|---|---|---|---|---|
| arXiv API | `all:"exponential time hypothesis"` | 2026-10-28 00:19 | 637 | 8 | sortBy=relevance |
| arXiv API | `abs:"subexponential" AND abs:"SAT"` | 00:19 | 22 | 8 | |
| arXiv API | `all:"Sparsification Lemma"` | 00:19 | 10 | 8 | IPZ 引理线 |
| arXiv API | `abs:"SETH" AND abs:"conditional lower bounds"` | 00:19 | 34 | 8 | |
| arXiv API | `all:"counting satisfying assignments"` | 00:19 | 11 | 8 | #SAT 计数线 |
| arXiv API | `all:"k-SAT algorithm" AND cat:cs.CC` | 00:19 | 5 | 5 | |
| arXiv API | `all:"Lean" AND all:"formalized" AND cat:cs.LO` | 00:19 | 294 | 8 | 形式化层 |
| arXiv API | `all:"formalization of complexity theory"` | 00:20 | **0** | 0 | **检索未获**（如实记：该精确短语在 arXiv 无命中，说明复杂性理论形式化本身是稀薄方向） |
| arXiv API | `all:"local smoothing conjecture"` | 00:20 | 9 | 8 | OpenAI 同日宣称之二 |
| arXiv API | `abs:"AI-generated proof" OR ...` | 00:20 | 4 | 4 | |
| arXiv API | `all:"Hamiltonian path" AND cat:cs.CC` | 00:20 | 36 | 8 | 对接 Q4 |
| arXiv API | `all:"SAT" AND all:"Hamiltonian cycle" AND all:"encoding"` | 00:20 | 4 | 4 | 对接 Q4 |
| arXiv API | `all:"one-way function" AND abs:"exponential time hypothesis"` | 00:20 | **0** | 0 | **检索未获**，改走 Appendix C 原文（Q5 达成） |
| arXiv API | `abs:"circuit lower bounds" AND abs:"satisfiability algorithm"` | 00:20 | 5 | 5 | Williams–Oliveira 线 |
| OpenAlex API | 7 条 title.search（经典件反查 DOI） | 00:20–00:21 | — | 17 | 见 §四 A 级 |
| Crossref API | 3 条 query.bibliographic | 00:21 | — | 5 | 含"ETH is False"检索：**未获**（无 DOI，印证非同行评审） |
| 官方仓库 raw | openai/math：README / preprints 正文 PDF / lean/docs/378.md / ComparatorChallenges/SubexponentialSAT.lean / formalization.yaml | 00:18–00:19 | — | 5 件 | **formalization.yaml 仅取回 41,340/81,913 字节**（curl 60s 超时截断，下半未获，见 §六） |
| 官方仓库 raw（**二次现取**，为把 Q6 从"读声明"升级为"读证明体"） | `lean/README.md` / `lean/lean-toolchain` / `lean/lake-manifest.json` / `lean/ComparatorChallenges/README.md` / `lean/ComparatorChallenges/SubexponentialSAT.json` / `lean/OAI/Algorithms/SubexponentialSAT/Main.lean` / `lean/OAI/Algorithms/SubexponentialSAT/SqrtLogSpace/Final.lean` | 00:35–00:40 | — | **7 件全部 200**，逐件哈希入档（见 §三） | 由 `lean/README.md`→`ComparatorChallenges/README.md`→`SubexponentialSAT.json` 的 `solution_module` 字段顺链定位到证明体 `SqrtLogSpace/Final.lean`（11,701 B/202 行） |
| 官方仓库 raw（**路径复核，负结果**） | `lean/verify_all.sh`、`lean/COMPILATION_STATUS.md` 及 10 条命名变体（根层/scripts/lean/docs 下） | 00:33–00:36 | — | **0 件（全 404）** | `lean/` 目录实测清单为 `.gitignore / LICENSE / OAI.lean / README.md / formalization.yaml / lake-manifest.json / lakefile.lean / lean-toolchain` + 子目录 `ComparatorChallenges / OAI / docs / patches`——**无此二件**；本地留档全文 grep 亦无 "391 / 1694 / COMPILATION_STATUS / verify_all" 字样 → 本件初稿引用该二件的数字已**撤回**，见 §六·2 |
| 网页官方源 | ethdiscussion.blog、agmai.org | 00:19–00:20 | — | 2 | 正文转文本存档 |
| WebSearch（英/中双轨） | OpenAI ETH Lean #3-SAT；"指数时间假说 证伪 3-SAT 亚指数算法" | 00:15 / 00:21 | — | 6+6 | 中文侧全部为媒体转述 → 只能定 D 级 |

**通道勘误**：本机 Python `urllib` 对 export.arxiv.org 被拦（"[BLOCKED] urllib 已禁止访问该网络或URL"），第一版脚本 `lit_fetch_arxiv.py` 因此空跑；改用 `curl` 子进程通道后全部成功。**教训入档：接口通道受阻时先换传输层再判"检索未获"，不得把工具故障当成没有文献。**
**覆盖缺口**：GitHub REST API 匿名配额已耗尽（2026-10-28 00:36 复测 `core: remaining 0/60`，`graphql: 0`），仓库树形清单与 ETH 目录 BibTeX（`paper.bib` 返回 404，命名待查）未由 API 取得 → 目录清单改由仓库网页渲染路径核对，Q6 改以**证明体源文件本体**为据（已完成）。仍未覆盖：`OAI/` 上游模块的逐件 sorry 核查、本机 `lake build` 复算、`#print axioms` 的实际输出（见 §六·2、§六·6）。

---

## 三、一手材料（第 3–4 段：抓取+读卡）

**读卡深度如实声明**：README / 378.md / 两封声明 / 书目 = **已整读**；Lean 侧 7 件 = **已整读源文件并机检**（逐件 `grep sorry` 计数、定理行号、`#print axioms` 位置、`lake-manifest.json` 版本 pin）；论文 PDF = **已抽取并读**定理陈述、附录 C、参考文献，**§3–§6 技术节尚未逐节读卡**（见 §六·6，R5 待办）。落位 `sources-ETH证伪宣称-20261028/`：

| 文件 | 字节 | SHA256（前 16） | 读卡结论 |
|---|---|---|---|
| `openai_ETH-is-false_paper-20261025.pdf` | 887,884 | `5b1612dc2eebb2ca` | 正文已抽取（`eth_paper.txt`，252,160 字符）。**Theorem 1.1**：对每个固定 k≥2，确定性算法在 `(n+m)^{O_k(1)} · 2^{O_k(n log log n/√log n)}` 位操作、`(n+m)^{O_k(1)}` 空间内精确算出 k-CNF 的满足赋值数 #F；固定密度 m≤Dn 时改进为 `2^{O_{k,D}(n/√log n)}`。摘要自称"refutes ETH"。**附录 A** 划分赋值、**§3** shared linear summaries、**§4** low-degree replacement forms、**§5** 稀疏多项式公共零点计数、**§6** #k-SAT 归约到零点计数、**附录 D** 用张量收缩复证两界 |
| `lean-docs-378.md` | 1,090 | `a2f7b390d6308997` | Lean 侧**范围声明**：被证的是**稍弱界** `(L+1)^{O_k(1)} · 2^{O_k(n(log log n)²/√log n)}`（L=编码位长），每步访问格子数 `(L+1)^{O_k(1)}`；同文明确写"October 25 manuscript gives the sharper time bound"——**界差由 OpenAI 自己写明**，非我方推断 |
| `SubexponentialSAT.lean`（= `lean/ComparatorChallenges/`） | 7,833 | `4183b2057cff350d` | **陈述件**（comparator 挑战目标）：定义 CNF/位编码/多带机 `PrimitiveMachine`/`Trace`/时间与空间界，`theorem exact_count_and_sat` 在第 **218 行以 `by sorry` 结束**——本文件内**无证明** |
| `lean-ComparatorChallenges-README.md` | 287 | `051459a45da1bedd` | **核查路线原文**：装 `comparator`／`landrun`／`lean4export`，在 `lean/` 下执行 `lake update; lake exe cache get; lake env comparator ComparatorChallenges/<name>.json`——即"任何人可自行复核"是**有工具的**，不是口号（工具上游为 `github.com/leanprover/comparator`） |
| `lean-ComparatorChallenges-SubexponentialSAT.json` | 364 | `debbfdc9c01104d2` | 挑战规格：`challenge_module`= 上述 sorry 陈述件，`solution_module`＝**`OAI.Algorithms.SubexponentialSAT.Main`**，`theorem_names`＝`…SqrtLogSpace.exact_count_and_sat`，`permitted_axioms`＝`propext / Quot.sound / Classical.choice`（**三件套即标准三条外公理，未开新公理口子**），`enable_nanoda: false` |
| `lean-OAI-Algorithms-SubexponentialSAT-Main.lean` | 590 | `cbd4cebf71f1d323` | 模块索引件（docstring 自称主定理为《A Subexponential Algorithm for Bounded-Width SAT》的形式化，本定理是其"加精确计数 + 全前缀带访问多项式界"的加强版），本文件 0 sorry 但也**不含定理体** |
| `lean-OAI-SqrtLogSpace-Final.lean`（= `lean/OAI/…/SqrtLogSpace/Final.lean`） | 11,701 | `040360a846595762` | **证明体本体，202 行，本文件内 `grep sorry` = 0**。五个定理：`compiled_exact_count_and_sat`(L10)、`exact_count_and_sat`(L74)、`exact_count_eth`(L104，带 `20 ≤ n` 前提，与论文"n≥20"一致)、`sat_polynomial_space`(L149)、`original_sat_main`(L184)；末尾 **5 条 `#print axioms`**（公理卫生检查）。战术结构可直读：由 `NativeLargeEntry.run` 取小/大分支、`Native.countingProgram` 与 `GuardedCompiler.primitive` 造**具体机器**（`BitProgram.Program 80 1220 labels`、输出栈 1216、计数带 256）、常数显式抬升（`C+28700`、`S+5022741`、`d+2`、`e+2`）， tactic 用 `omega / positivity / exact_mod_cast / ring / simpa`——**"存在一台机器"被写成"这台机器的带号与预算常数"**，与我方 04 域"构造性判定+固定机器"口径同型 |
| `lean-README.md` / `lean-toolchain.txt` / `lean-lake-manifest.json` | 650 / 25 / 14,622 | `292ff9d539f49415` / `d5edba4e4b8faad9` / `cf6105a25d9dca2f` | 构建配置实测：toolchain＝`leanprover/lean4:v4.34.1`；manifest 共 **42 个包**，mathlib 以 **git rev `d13f23b723b8a846827a245b89c10fc7d3f11612`** 锁定（**未见任何 "v4.18.0" 字样**）；README 警告"整库单一大 library，建议分批编译"，并给出 Linux `vm.max_map_count`/mmap 失败的绕行法——**复核成本本身是一等信息** |
| `paper_references.txt`（39 条） | 7,113 | — | 论文自带书目 = 本领域权威谱系直读，本件 A 级条目多取自此（含 [IP01][IPZ01][CIP06][IMP12][HKZZ19][Wil13][JMV13][Zuk83][Gol00] 等） |
| `ethdiscussion_blog.txt` | 5,591 | — | **提出者本人声明**（署名 rpaturi7…＝Paturi 侧账号）："Our involvement should not be taken as certification of the claim"；组织两件事：核查该证明 + 讨论社区如何应对 AI 生成的突破 |
| `agmai_org.txt` | 10,975 | — | IAS/AGMAI 三份声明（10-06 / 10-25 / 10-26）：反对由 AI 公司指定少数数学家优先解读；10-26 要求 OpenAI **立即公开 Yang–Mills/QCD 的自然语言与 Lean 输出**（并称 OpenAI 自述 Lean 形式化已完成） |
| 仓库 README（`openai-math-repo-README.md`，4,417 B，`6cb7f0e387b67c05`） | 4,417 | `6cb7f0e387b67c05` | 关键背景：该集合由**未公开的内部模型**产出，**721 篇手稿/373 个家族**，约 **42% 顶层结果已形式化**；原文自述"best understood as raw research data, rather than polished academic papers"；每项平均约 3 小时 ChatGPT Pro 思考算力，评测中出题约 4,000 道 |
| `formalization.yaml`（**截断件**，41,340/81,913 B，`e25191bb489498a4`） | 41,340 | `e25191bb489498a4` | 已确认 ETH 条目在目录中列为 `type: article`，指向同一 PDF；**下半部未取回**，故各家族的形式化 `ok` 状态未获（见 §六·2） |

**状态标签**：上表覆盖 **15 件一手件**，均为**已读正文／已机检**（非仅元数据）；派生留档件另计 5 件（`eth_paper.txt` 正文抽取、`extract_thm1.txt`、`extract_appendixC.txt`、两份声明的 HTML 原件），目录内共 20 文件。本件其余 arXiv 条目为 `metadata-only`（标题+摘要，未读正文），只作候选与坐标，不作支撑。

---

## 四、来源表（第 5 段：A–D 分级，逐条可回链）

### A 级｜同行评审原始文献（定义与谱系的唯一合法出处）

1. Impagliazzo & Paturi. *On the Complexity of k-SAT*. JCSS 62(2):367–375, 2001. [doi:10.1006/jcss.2000.1727](https://doi.org/10.1006/jcss.2000.1727) — **ETH 原始出处**（[IP01]）
2. Impagliazzo, Paturi & Zane. *Which Problems Have Strongly Exponential Complexity?* JCSS 63(4):512–530, 2001. [doi:10.1006/jcss.2001.1774](https://doi.org/10.1006/jcss.2001.1774)；会议版 FOCS'98 [doi:10.1109/sfcs.1998.743516](https://doi.org/10.1109/sfcs.1998.743516) — **SETH + Sparsification 引理**（[IPZ01]）
3. Calabro, Impagliazzo & Paturi. *A Duality between Clause Width and Clause Density for SAT*. IEEE CCC 2006. [doi:10.1109/ccc.2006.6](https://doi.org/10.1109/ccc.2006.6)（[CIP06]，我方引的 Calabro 博士论文第 5 章即其源头）
4. Alman & Williams. *Probabilistic Polynomials and Hamming Nearest Neighbors*. FOCS 2015. [doi:10.1109/focs.2015.18](https://doi.org/10.1109/focs.2015.18)（[AW15]，多项式方法线）
5. Backurs & Indyk. *Edit Distance Cannot Be Computed in Strongly Subquadratic Time (unless SETH is false)*. SICOMP 47(3), 2018. [doi:10.1137/15m1053128](https://doi.org/10.1137/15m1053128)；STOC 2015 会议版 [doi:10.1145/2746539.2746612](https://doi.org/10.1145/2746539.2746612)（[BI18]，条件性下界的典型形态——"除非 SETH 为假"这类措辞正是 R2 要拆的对象）
6. Impagliazzo, Matthews & Paturi. *A Satisfiability Algorithm for AC0*. SODA 2012, 961–972（[IMP12]，附录 C 电路下界所依赖）。**DOI 未获**：Crossref `query.title` 检索未命中该条，按铁律二不猜号；当前回链依据 = 论文自带书目 [IMP12] 条目 + 出版方页未采集。

### B 级｜一手非正式材料（OpenAI 官方仓库/正式声明）

7. OpenAI. *The Exponential Time Hypothesis is False*. 预印本，目录日期 2026-10-25，发布 2026-10-26。[paper.pdf（本地已存哈希件）](sources-ETH证伪宣称-20261028/openai_ETH-is-false_paper-20261025.pdf)；[上游 raw 链接](https://raw.githubusercontent.com/openai/math/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/paper.pdf) — **Crossref 检索未获 DOI**（印证未经出版）
8. OpenAI. `lean/docs/378.md` 形式化范围说明。[链接](https://raw.githubusercontent.com/openai/math/main/lean/docs/378.md) — Lean 界与论文界的**差异由本件自认**
9. OpenAI. `openai/math` 仓库 **Lean 侧 7 件**（一手可机检材料，本地均已留档并哈希）：
   - [`lean/ComparatorChallenges/SubexponentialSAT.lean`](https://raw.githubusercontent.com/openai/math/main/lean/ComparatorChallenges/SubexponentialSAT.lean) — 陈述件，[本地](sources-ETH证伪宣称-20261028/SubexponentialSAT.lean) L218 `by sorry`
   - [`lean/ComparatorChallenges/README.md`](https://raw.githubusercontent.com/openai/math/main/lean/ComparatorChallenges/README.md) — 复核命令（`lake env comparator …json`）
   - [`lean/ComparatorChallenges/SubexponentialSAT.json`](https://raw.githubusercontent.com/openai/math/main/lean/ComparatorChallenges/SubexponentialSAT.json) — 挑战规格：`solution_module`、`permitted_axioms` 三件套
   - [`lean/OAI/Algorithms/SubexponentialSAT/Main.lean`](https://raw.githubusercontent.com/openai/math/main/lean/OAI/Algorithms/SubexponentialSAT/Main.lean) — 模块索引
   - [`lean/OAI/Algorithms/SubexponentialSAT/SqrtLogSpace/Final.lean`](https://raw.githubusercontent.com/openai/math/main/lean/OAI/Algorithms/SubexponentialSAT/SqrtLogSpace/Final.lean) — **证明体**（202 行、本文件 0 sorry、末尾 5 条 `#print axioms`），[本地](sources-ETH证伪宣称-20261028/lean-OAI-SqrtLogSpace-Final.lean)
   - `lean/README.md`／`lean/lean-toolchain`（`lean4:v4.34.1`）／`lean/lake-manifest.json`（42 包，mathlib rev `d13f23b7…`）
   
   （**注**：`lean/verify_all.sh`、`lean/COMPILATION_STATUS.md` 两路径实测 **404**，目录清单亦无此二件——本件初稿曾引其数字，已撤回，见 §六·2。）
10. OpenAI. `openai/math` 仓库 README（721 手稿/373 家族/≈42% 形式化/内部模型/自述"raw research data"）。[链接](https://raw.githubusercontent.com/openai/math/main/README.md)
11. Paturi 等. *ETH Refutation: Examination and Discussion*（ethdiscussion.blog，2026-10-26）。[链接](https://ethdiscussion.blog/)
12. AGMAI（IAS）三份声明：On OpenAI's Release of Mathematical Results（10-06）/ Disadvantages of Designating Mathematicians for AI Output Releases（10-25）/ Recommendation for Immediate Release of Yang–Mills AI Output（10-26）。[链接](https://agmai.org/)

### C 级｜权威同行作者的机制性文献（我方判据要直接对照的 12 篇，arXiv 已逐条回链验证）

13. Salamon & Wehar. *Superlinear Lower Bounds Based on ETH*. [arXiv:2008.06805v5](https://arxiv.org/abs/2008.06805)（2020-08-15）
14. Oliveira. *Algorithms versus Circuit Lower Bounds*. [arXiv:1309.0249](https://arxiv.org/abs/1309.0249)（2013-09-01）
15. Schneider. *Satisfiability Algorithms for Restricted Circuit Classes*. [arXiv:1306.4029](https://arxiv.org/abs/1306.4029)（2013-06-17）
16. Gurumukhani, **Paturi**, Pudlák, Saks, **Talebanfard**. *Local Enumeration and Majority Lower Bounds*. [arXiv:2403.09134v3](https://arxiv.org/abs/2403.09134)（2024-03-14）
17. Traxler. *The Relative Exponential Time Complexity of Approximate Counting Satisfying Assignments*. [arXiv:1208.2561](https://arxiv.org/abs/1208.2561)（2012-08-13）
18. Kanj & Szeider. *On the Subexponential Time Complexity of CSP*. [arXiv:1304.1996](https://arxiv.org/abs/1304.1996)（2013-04-07）
19. Kourtis, Chamon, Mucciolo & Ruckenstein. *Fast counting with tensor networks*. [arXiv:1805.00475v2](https://arxiv.org/abs/1805.00475)（2018-05-01）
20. Van Vi, Van Kieu & Van To. *StructHCP: Structure-Aware SAT–CEGAR for the Hamiltonian Cycle Problem*. [arXiv:2610.14780](https://arxiv.org/abs/2610.14780)（2026-10-10）
21. Keshavarz-Kohjerdi & Bagheri. *Hamiltonian Paths in C-shaped Grid Graphs*. [arXiv:1602.07407](https://arxiv.org/abs/1602.07407)（2016-02-24）
22. Beisegel, Ratajczak & Scheffler. *Computing Hamiltonian Paths with Partial Order Restrictions*. [arXiv:2404.16662v3](https://arxiv.org/abs/2404.16662)（2024-04-25）
23. Lafuente-Mercado 等. *LeanPRM: Lean-Grounded Process Supervision for Natural Language Proof Verification*. [arXiv:2610.17697v2](https://arxiv.org/abs/2610.17697)（2026-10-13）
24. Groff. *Towards P = NP via k-SAT: A k-SAT Algorithm Using Linear Algebra on Finite Fields*. [arXiv:1106.0683v2](https://arxiv.org/abs/1106.0683)（2011）— **反面教材**：标题即越界宣称，我方"判负照记"可用作对照样本

### D 级｜媒体转述（仅触发，不作支撑）

25. 环球科学《科学家相信了30年的假说，发过数百篇论文，可能被OpenAI证伪了》（2026-10-27）[原文链接](https://mp.weixin.qq.com/s/T6id-WlSXNxHL3DdVCEPTQ) — 本件唯一触发源；正文已整读（经浏览器通道，微信对普通抓取有风控页）
26. IT之家、财联社、新浪财经、TheBlockBeats、TradingView 中文快讯（同一稿源，2026-10-27）[IT之家](https://www.ithome.com/1/018/203.htm)／[财联社](https://www.cls.cn/detail/2515887)／[新浪财经](https://finance.sina.com.cn/wm/2026-10-27/doc-iniwruyv4643662.shtml) — 其中新浪标题"「王的猜想」全维度告破"属**夸大转述**（原文只宣称证伪 ETH，且未通过独立审查），不得引为口径
27. 知乎讨论、Hacker News、r/computerscience 关于 #3-SAT 与 SETH 区别的技术性争论（[HN 50251344](https://news.ycombinator.com/item?id=50251344)）— 仅作争议信号
28. Hexagon 数学摘要页对 3-SAT 亚指数算法的第三方复述：[hexagonmath.org/2610.00577v1](https://hexagonmath.org/2610.00577v1)
29. Xenospectrum 英文报道（含三人核查组细节）：[链接](https://xenospectrum.com/en/openai-exponential-time-hypothesis-false-claim/)

### 我方档案对照件（第 3 道闸：查我们自己的档案，全部给路径与版本）

30. `01-数学/01-理论与推导/云韶计算体系·现代计算化架构方案-v1.1-20261003.md` L32/L46/L48/L97 — E3 组合优化"加 SAT 引擎（Kissat/CaDiCaL）"、"升级格：SAT 完备判定"、文献锚引 **Talebanfard（SAT/GRID 复杂度）**、预注册判据"SAT 判死 ⟺ M1 各顺序全灭"
31. `04-哈密顿路径/01-理论与推导/BA图哈密顿复合算法·综合方案-20260726.md` L131–135 — "观测到的 tradeoff 不是上界""真实结构上界（三条打不破，写进文档）"
32. `04-哈密顿路径/00-正本/BA无标度图严格HP·能力边界总表（内部版）-v1.11-20261003.md` — **名实不一致在案**：文件名标 v1.11/2026-10-03，文内 YAML 现为 `version: 1.12`、`date: 2026-10-27`（另一会话升版未改名）。引用本件时**必须以文内 version 为准**，并优先登记该不一致（本条即工作总纲"事实路径以文件本体为准"的具体触发）。
33. `01-数学/03-论文与对外/大论文-精确方法在国防运筹与无标度图HP构造中的应用-20260913.md` L31/L213 — "对于一般图，不存在已知的多项式时间精确算法"、诚实声明"不声称对实际国防系统的贡献"
34. `04-哈密顿路径/05-索引/哈密顿全域审计系统·立项总纲-v0.1-20260930.md` L69 — "哈密顿求解 NP 复杂度：百万级实图可能无精确解——多段覆盖理论正是解法"

**回链验证（第 6 段硬门，2026-10-28 两轮实测）**：编号来源 29 条的直链逐条 GET 状态核对——**21 条直连 200**（12 条 arXiv 摘要页、OpenAI 仓库三件、ethdiscussion/agmai、微信原文、三家中文媒体）；**8 条本机直连返回 000**（`doi.org`×5、hexagonmath.org、news.ycombinator.com、xenospectrum.com），已改走官方接口复核：**5 条 DOI 全部经 Crossref `api.crossref.org/works/<DOI>` 逐条核对标题/期刊/年份一致**（10.1006/jcss.2000.1727、10.1006/jcss.2001.1774、10.1109/ccc.2006.6、10.1109/focs.2015.18、10.1109/sfcs.1998.743516），故**标识符有效，直连受阻属本机网络策略而非条目错误**；hexagon/HN/xenospectrum 三条为 WebSearch 命中、正文未直采，状态标 `metadata-only`，不入支撑。12 条 arXiv ID 另经 `export.arxiv.org/api/query?id_list=` 批量反查，标题与作者逐条相符（见 verify 记录）。**仓库 raw 直链另计 9 条**：§四·9 所列 7 件全部 **200** 并已本地哈希；`lean/verify_all.sh` 与 `lean/COMPILATION_STATUS.md` **404**（另测 9 条命名变体亦 404），据此撤回 §六·2 初稿引文——**"回链验证"对本件同样生效，检不到就删**。

---

## 五、术语双语对照（本件专用，接双语检索工作包 §二 A3）

| 主流词（英/中） | 体系侧对照 | 关系性质 |
|---|---|---|
| Exponential Time Hypothesis (ETH) / 指数时间假说 | 无体系原生对应物；最接近的是 04 域"能力边界/结构上界"表述 | **不可互换**，只做对照翻译 |
| subexponential time 2^{o(n)} / 亚指数时间 | 体系"膨胀率–Θ(N)"档位（非同一量纲，禁数值代入） | 结构同构候选，须先证同构 |
| conditional lower bound / 条件性下界 | 我方"判负照记 + 预注册判据"的镜像物 | **方法论同型**（这是本件最有价值的部分） |
| #SAT exact counting / 精确计数满足赋值 | 04 域"路径计数/覆盖 walk"与概念宇宙计数口径 | 不同问题，勿混用 |
| formalization (Lean) / 形式化验证 | 我方"机器可判定复算"（GAP/CP-SAT/SAT 仲裁） | 同级执行器，缺 Lean 类证明层；外部已有的 **comparator 三件套**（sorry 陈述件＋`.json` 规格件指定 `solution_module`／`permitted_axioms`＋公开复核命令）正是我方"判据与执行器分离、判据先冻结"的可抄结构 |
| circuit lower bound（ENP ⊄ SIZE(O(n))） | 13 域 YGC NP 完全 / 12 域算力口径 | **仅工具链关系**，不构成体系结论 |

---

## 六、勘误与不确定度（照记，不美化）

1. **两个界不是一条**。论文 Theorem 1.1：`2^{O(n log log n/√log n)}`（m≤Dn 时 `2^{O(n/√log n)}`）；Lean 侧自述验证的是 `2^{O(n(log log n)²/√log n)}`，**指数里多一个 (log log n)**。科普转述"结果已通过 Lean 形式化验证"若不附此差别即为失真。
2. **Lean 侧：先撤一条我自己的错，再给可回链的事实**。
   - **撤回（判负照记，2026-10-28 00:36 复核）**：本件初稿本节曾写"真正的已验证明体在 `lean/verify_all.sh`（375 行、0 处 sorry）与 `lean/COMPILATION_STATUS.md`（391 定义／1694 定理／sorry-free／`mathlib v4.18.0`／'verified today'）"。复核结果：**两个路径 raw 取回 404**，`lean/` 目录实测清单无此二件，本地全部留档件 `grep` 无 "391／1694／COMPILATION_STATUS／verify_all" 字样，且 `lake-manifest.json` 里 mathlib 是 **git rev 锁定**（`d13f23b7…`）而非"v4.18.0"。**该处引文不可回链，已整段删除。**台账要求外部来源逐条回链，则台账自己的每一句也必须能回链——此条按 §六 同一标准记负。
   - **现行可回链事实（7 件已入档，见 §三/§四·9）**：`ComparatorChallenges/SubexponentialSAT.lean` 是**公开挑战陈述件**，L218 `by sorry`＝**该文件内无证明**（这是 comparator 机制的设计，不是破绽）；同一 theorem 名的**证明体**由 `SubexponentialSAT.json` 的 `solution_module` 顺链指向 `OAI/Algorithms/SubexponentialSAT/SqrtLogSpace/Final.lean`，该文件 **202 行、五个定理、本文件内 `sorry` 计数为 0**，末尾附 5 条 `#print axioms`，`permitted_axioms` 只允许 `propext / Quot.sound / Classical.choice`（标准三条，**未开新公理口子**）；复核路线是公开的（`lake update; lake exe cache get; lake env comparator …json`）。
   - **仍未证的部分（不许顺手夸大）**：①本件**未在本机执行** `lake build`／comparator，"编译通过"是他方声明；②`Final.lean` 依赖的上游模块（`NativeLargeEntry`、`GuardedCompiler`、`SqrtLog.StatementCanonical`、`NativeOuterBudgets` 等）**未逐个 grep sorry**，故"整库 sorry-free"仍属未证；③`#print axioms` 的**实际输出**未采集（文件里只有命令）；④被证的仍是**较弱的 `(log log n)²/√log n` 界**，与论文界差一条 `(log log n)`（§六·1）。
   - **净结论**：OpenAI 侧的"已形式化"比科普转述更可核（陈述件、规格件、证明件、工具链四样齐全且公开），但"已验证"的**完整范围**仍未由利益无关方复算——这恰好把我方 R4 三条（降级入档／区分陈述与证明／无关方独立复算）逐条坐实，而且**本件自己就是第四条教材**。
3. **证伪的是 ETH／SETH，不是 P≠NP**（本条 2026-10-28 二次纠正）。初稿曾写"也不涉及 SETH"——**错**。逻辑上 SETH ⟹ ETH（SETH 是更强的假设），逆否即得 **¬ETH ⟹ ¬SETH**：只要 Theorem 1.1 成立（固定 k=3、指数只含 n、多项式因子 `(n+m)^{O_k(1)}`），则对任意 δ>0，充分大的 n 上 `n·log log n/√log n < δn`，时间落进 `2^{(1-δ)n}`，SETH 直接失效。**这条纠正会放大冲击面**：本件 A 级 5 号（Backurs–Indyk 编辑距离）、Bringmann Fréchet、BI16 正则表达式匹配、AW14 动态问题等一系列 **SETH 条件下的最优性下界**同时失去条件——中文报道"发过数百篇论文可能受影响"在这一层**并非夸大**（我此前把它一并归入"越界转述"是矫枉过正）。仍然越界的只有两类：把 `2^{o(n)}` 说成多项式／"计算难题不再难"，以及把 ETH 之假说成 P≠NP 或 P=P 有进展。
4. **未经同行评审**：Crossref 无 DOI；提出者本人声明"参与核查不等于背书"；AGMAI 反对"指定数学家优先解读"模式。当前状态 = **外部宣称·未独立验证**。
5. **产出方式本身是弱信号**：仓库自述为内部未公开模型、约 4,000 题筛出 721 篇、约 42% 顶层结果形式化、"raw research data"。→ 单篇论文的可信度与家族规模需分开评估。
6. **本件未覆盖**：知网/万方中文学术库（无官方接口凭据）、GitHub API 配额（00:36 实测 remaining 0）、`formalization.yaml` 下半部、ETH 目录 `paper.bib`（404，命名待查）、正文 §3–§6 技术细节的逐节读卡（本件只完成定理与附录 C 抽取）、**`lean/OAI/` 上游模块的逐件 sorry 核查与本机 `lake build`／comparator 复算、`#print axioms` 的实际输出**（三者共同决定"已验证"的真实外延，见 §六·2）。
7. 反面样本留档：[arXiv:1106.0683](https://arxiv.org/abs/1106.0683)《Towards P = NP via k-SAT》——宣称强度与验证深度倒挂，正是我方"判负照记"要防的形态。

---

## 七、对我方档案的约束力清单（下一步动作，**待知世批，未执行**）

| # | 位置 | 现口径 | 本件证据要求的修订 | 优先级 |
|---|---|---|---|---|
| R1 | 架构方案 v1.1 L48 | "Talebanfard（SAT/GRID 复杂度…）"仅人名硬锚，无 ID | 补 [arXiv:2403.09134]（同作者含 Paturi）+ 说明其与网格 HC 的可判定性关系；按 lit-harvest 铁律一改为**标识符先行** | P1 |
| R2 | 04 域 L135"三条打不破"、审计立项总纲 L69 | 把"结构上界"与"NP 复杂度"并置，读者会读成复杂性下界 | 拆成两栏：**实证失效边界**（我方数据，不受 ETH 影响）／**条件性复杂性下界**（依赖 ETH/**SETH**，外部事件敏感），并加注"**ETH 若被证伪则 SETH 同时失效（SETH⟹ETH 的逆否），整片条件性下界失去条件；实证边界不受影响**" | P0 |
| R3 | E3"SAT 完备判定"升级格 | 以 SAT 判死活作为完备裁判 | 补外部对标：[arXiv:2610.14780]（SAT–CEGAR 结构感知，2026-10-10）与我方 M1 管线直接可比；判据书加"与公开求解器对拍"一条 | P1 |
| R4 | 12 域 AI 证明线 / 09 域工作总纲 | 无"AI 生成证明的核查责任"条款 | 参照本件 9/11/12 号来源，工作总纲 v1.1 增四条：①外部重大宣称先降级"未验证"入档；②形式化声明必须区分"陈述／证明"（挑战件含 `sorry` ≠ 造假，但"含 sorry 的文件"也 ≠ 已证）；③核查须由利益无关方独立复算并留记录；④**台账自身每一句（含我方自己写下的数字）也必须可回链，检不到即撤**——本件 §六·2 的撤回即为该条的现场案例 | P0 |
| R5 | 本件 | 文献层 | 逐节读卡 §3–§6（张量收缩/低次替换形式）后，判断是否可用于我方"计数类问题"口径——**当前不得引为体系支撑** | P2 |
| R6 | Lean 完整性 | 仅本机源文件机检（未编译） | 若要把"已形式化"写入我方任何对外表述，须先完成：`lean/OAI/` 上游模块逐件 `grep sorry` + 本机 `lake build`／`lake env comparator` 复算 + 记录 `#print axioms` 实际输出；**不做则一律标"他方声明·未复算"** | P2 |

**一句话结论**：文献已按闸收齐（一手 **15** 件／留档 20 文件 + 分级 29 条 + 我方对照 5 件），关系仍如上次判断——**方法层与口径层关系强（R2/R4 必改），体系真伪层关系为零**；本件比科普转述多出的四条新事实是：①Lean 界与论文界不同（差一条 `(log log n)`）；②含 `sorry` 的是**公开挑战陈述件**，证明体另存于 `OAI/…/SqrtLogSpace/Final.lean`（该文件 0 sorry，附 `#print axioms` 与三条受限公理）；③"整库已验"仍未由利益无关方在本机复算，我方也未复算；④**本件初稿自己引错了一件不存在的仓库文件并已当场撤回**——这正是 R4 第④条要防的形态，也是最有力的立法理由。

【修改记录】v1.0 2026-10-28 知世令"那你收集相关文献呢？"——lit-harvest 六段全流程件；原始 PDF/Lean/声明正文落 `sources-ETH证伪宣称-20261028/`；检索日志与脚本落 `00-其他/总纲索引/_tools/`；`metadata-only` 条目全部标注、未进支撑；urllib 受阻与 GitHub 限流两项通道缺陷如实记录。

【修改记录·同日二次勘误与增补】00:30–00:45：①为把 Q6 从"读声明"做到"读证明体"，二次现取 openai/math `lean/` 侧 7 件（`SubexponentialSAT.json` 规格件、`ComparatorChallenges/README.md` 复核命令、`OAI/…/SqrtLogSpace/Final.lean` 证明体、`Main.lean`、`lean/README.md`、`lean-toolchain`、`lake-manifest.json`）入档并逐件哈希，目录留档由 13 文件增至 **20 文件**，一手件计数 8→**15**；②**撤回初稿 §六·2 对 `lean/verify_all.sh`（"375 行 0 sorry"）与 `lean/COMPILATION_STATUS.md`（"391 定义/1694 定理/sorry-free/mathlib v4.18.0"）的引文**——两路径实测 404、`lean/` 目录清单无此二件、本地留档全文 grep 无相应字符串、manifest 中 mathlib 为 git rev 锁定而非版本号，四重检不到即判该引文不可回链，已按同一标准记负并撤下；③§六·2 改为"撤回件＋现行可回链事实＋仍未证部分"三段式；④R4 由三条增为四条（新增"台账自身每句须可回链"），并增列 R6（本机复算与上游模块 sorry 逐件核，未做则一律标"他方声明·未复算"）。版本号仍记 v1.0（同日修订不改文件名，避免制造本件自己指摘的"名实不一致"）。**正本零改动；R1–R6 全部"待知世批·未执行"。**

【修改记录·同日三次纠正】00:55：知世追问"这个问题到底是什么"触发自查，抓到 §六·3 初稿一条**方向性错误**——原写"证伪的是 ETH，也不涉及 SETH"。正解：**SETH ⟹ ETH，故 ¬ETH ⟹ ¬SETH**（逆否），Theorem 1.1 的 `2^{O_k(n log log n/√log n)}`＝`2^{o(n)}` 连 SETH 一起打掉；受冲击的是"SETH 条件下的最优性下界"整片（本件 A 级 5 号 BI18 编辑距离、Bringmann Fréchet、BI16 正则表达式匹配、AW14 动态问题等），故中文报道"数百篇论文受影响"在该层**不算夸大**，我此前把它整体归入"越界转述"属矫枉过正。R2 加注同步改为"ETH 假则 SETH 同时失效"。仍不改任何判定、不动正本。
