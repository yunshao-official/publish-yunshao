---
title: "AI保密·文献收集与对标报告"
date: 2026-09-19
version: 1.0
status: 定稿·评审·待知世阅
constants: 无涉（情报报告；关联方案正本=体系结合AI保密·机制与方案-v1.0-20260919.md）
summary: "知世令'收集大量文献论文，看我们如何让AI保密'｜编制：ZCode｜新收文献约115篇（arXiv API 八域检索 2024-08~2026-09 + 中文白皮书5份），精选62篇入基座｜四个体系空白位获文献确认（涌现支付账/结构签名检测/权重可定位校验/密级专家容器）；三大修正：TEE已实用（Blackwell CC开销1-3%）、遗忘不可靠（可被逆向找回）、过滤式防御过时（转向结构/信息流控制）"
---

# AI保密·文献收集与对标报告 v1.0

> 知世令（2026-09-19）："收集大量文献论文，看看我们如何让AI保密"｜编制：ZCode
> 姊妹篇：《体系结合AI保密·机制与方案-v1.0-20260919》（正本，六机制）｜本文=文献支撑卷
> 方法：搜索后端限流，改走 arXiv 官方 API（8 个检索式，按提交时间降序，覆盖 2024-08~2026-09）+ 中文白皮书网络检索。**采信级别声明：全部条目为"检索摘要级"采信（题目/作者/ID/摘要一句话），未逐篇精读全文；列为后续精读任务。** 奠基经典（Carlini 2021/2023、Shokri 2017、Abadi 2016 等 20 篇）已载 V4Pro 分析附录，本文不重复收录。

---

## 〇、一句话结论

115 篇文献把 AI 保密的 2026 年格局画清楚了：**攻击侧**（提取/成员推断/注入）全面成熟且有自动化红队（LeakAgent 等），**防御侧公认转向**——"过滤提示词"过时，"结构隔离+信息流控制+硬件机密计算"成为主流，**溯源三件套（水印/金丝雀/审计）成为独立爆发域**。对我们最重要的一句话：**文献里没有"涌现支付账"，没有"密级专家容器"，没有"权重可定位校验"，结构化签名检测也只有弱同型——我们六机制中的四个落在真实空白位上，且每个都有相邻文献证明技术可行性。三大修正：TEE 从"推荐"升"立即可做"（NVIDIA Blackwell 机密计算实测开销仅 1–3%）；"遗忘"不可靠（已遗忘信息可被逆向找回）→"数据最小化、不让敏感数据进模型"压倒"进去再删"——与体系口径天然互证。

---

## 一、文献基座（62 篇精选，按域编号）

### A. 记忆提取与训练数据泄露（攻击面）
- [L1] Wang et al. (2026-05). Extracting Training Data from Diffusion Language Models via Infilling. arXiv:2605.24173——填充式提取，检出率最高达前缀探测 3 倍。
- [L2] Luo et al. (2026-03). Characterizing Memorization in Diffusion Language Models. arXiv:2603.02333——统一概率提取框架；扩散 LM 泄 PII 少于自回归。
- [L3] Zhang et al. (2026-03). Extracting Training Dialogue Data from LLM-based Task Bots. arXiv:2603.01550——任务机器人对话状态提取，最佳精度>70%。
- [L4] Segal et al. (2026-01). Provably Protecting Fine-Tuned LLMs from Training Data Extraction. arXiv:2602.00688——**首个"可证明"防护**：近访问自由度平滑（SCP-Δr），效用损失小。
- [L5] Su et al. (2024-09). Extracting Memorized Training Data via Decomposition. arXiv:2409.12367——指令分解即可从前沿模型逐字提取纽约时报文章，无需微调。
- [L6] Cheng et al. (2024-08). Security Attacks on LLM-based Code Completion Tools. arXiv:2408.11006——Copilot 越狱成功率 99.4%，提取真实邮箱与地址。
- [L7] Tiwari et al. (2024-12). Sequence-Level Leakage Risk of Training Data in LLMs. arXiv:2412.11302——标准"提取率"指标**低估泄漏风险达 2.14 倍**。
- [L8] Sasi (2026-07). Bits and Memories: Measuring Verbatim Extraction Across LLM Quantization. arXiv:2607.25451——**量化不是隐私防护**：仍复现大量记忆数据。
- [L9] Maricato (2026-07). Leak It: Per-Document Extraction Beyond Aggregate Membership Inference. arXiv:2608.00144——聚合 AUC 掩盖危害，逐文档逐字标识符提取才是真实伤害。
- [L10] Ruzzetti et al. (2025-06). Private Memorization Editing (PME). arXiv:2506.10024——把"记忆"本身改造成防御：检出并改写模型知识中的 PII，攻击准确率可降至 0。
- [L11] Chen et al. (2025-05). A Survey on Privacy Risks and Protection in LLMs. arXiv:2505.01976。
- [L12] Zhao et al. (2025-06). A Survey on Model Extraction Attacks and Defenses for LLMs. arXiv:2506.22521。

### B. 成员推断（攻击+审计）
- [L13] Zaree et al. (2026-01). AttenMIA: Membership Inference through Attention Signals. arXiv:2601.18110——注意力信号做 MIA，ROC AUC 达 0.996。
- [L14] Al Sahili et al. (2025-12). On the Effectiveness of MIA in Targeted Data Extraction. arXiv:2512.13352。
- [L15] Mireshghallah et al. (2025-10). Position: Privacy Is Not Just Memorization! arXiv:2510.01645——**基于 1322 篇综述的立场文**：隐私话语过度聚焦记忆，上下文泄露/代理风险被低估。
- [L16] Xue et al. (2026-09). CIG-MIA: MIA against Retrieval-Augmented Generation. arXiv:2609.14649——RAG 知识库成员推断，注入候选文档测似然增益，灰盒 AUC 0.99。
- [L17] Niu et al. (2026-09). Black-Box MIA via Word-Level Probability Estimation. arXiv:2609.10611。
- [L18] Jiang et al. (2026-08). FISGuard: Defending Against MIA via Fixed Input Subspaces. arXiv:2608.27836——联邦微调防御，ProjRes 攻击 AUC 降至随机。
- [L19] Mirzadehsarcheshmeh et al. (2026-09). PAC-Private Autoregressive Generation. arXiv:2609.05676。
- [L20] Mitchell et al. (2026-06). Advancing the State-of-the-Art in Empirical Privacy Auditing. arXiv:2606.10481——**高温采样合成金丝雀做隐私审计**。
- [L21] Marek et al. (2026-06). Benchmarking Empirical Privacy Protection for LLM Adaptations. arXiv:2606.09401——微调数据越接近预训练分布风险越高；LoRA 对域外数据防护最好。
- [L22] Deng et al. (2026-04). ProjRes: MIA against Federated LLMs. arXiv:2604.21197——**强 DP 防御下仍近 100% 准确**。
- [L23] Mivule (2026-04). LLM-CEG: Privacy Auditing Framework. arXiv:2604.23795——DP-SGD 使攻击者优势降 71.5%。
- [L24] Kirchenbauer et al. (2026-07). Watermarking for Proprietary Dataset Protection. arXiv:2607.00325——水印"放射性"使数据集成员测试可行。

### C. 注入/越狱/代理安全（攻击面）
- [L25] Remedios et al. (2026-09). Red-Teaming Auto Mode: Blocking Classifiers vs Malign Coding Agents. arXiv:2609.19587——生产级拦截分类器 79% 试验被绕过。
- [L26] Li et al. (2026-09). Universal Defenses for Tool-Integrated LLM Agents. arXiv:2609.16098。
- [L27] Shire et al. (2026-09). PIDS-Bench: Evaluating Prompt-Injection Detectors. arXiv:2609.15017——**过防御警告**：高 F1 检测器在分布漂移下仍误伤大量良性提示。
- [L28] Wang et al. (2026-09). ActGuard: Pre-execution Action Auditing. arXiv:2609.14987。
- [L29] Mecca et al. (2026-09). SkillSecurer: Prompt-Injection Vulnerabilities in Agent Skills. arXiv:2609.14079——热门已发布技能 17%+ 有注入漏洞。
- [L30] Zhang et al. (2026-09). No-Box Vulnerability Analysis of MCP Servers. arXiv:2609.10854。
- [L31] Liu et al. (2026-04). Your Agent Is Mine: Malicious Intermediary Attacks on the LLM Supply Chain. arXiv:2604.08407——**真实 API 路由商存在注入与凭证窃取**。
- [L32] Lan et al. (2026-02). Silent Egress: Implicit Prompt Injection Exfiltration. arXiv:2602.22450——URL 预览即可触发外泄，绕过 DLP 与输出检查；网络层防御更有效。
- [L33] Nikolaou et al. (2026-09). CaMeLoT: CaMeL + Temporal Logic. arXiv:2609.18674——能力-动作分离架构的时序逻辑静态验证。
- [L34] Safin et al. (2026-09). Trust Propagation and Structural Containment in Multi-agent LLM Pipelines. arXiv:2609.17648——**结构授权遏制即使 LLM 判断失败也有效**。

### D. 遗忘与记忆编辑（防护）
- [L35] Hu et al. (2026-08). On the Recoverability of Private Information Unlearning in LLMs. arXiv:2608.29943——**逆贪心解码可从"已遗忘"模型找回隐私信息**。
- [L36] Diamant et al. (2026-08). Stress Testing Unlearning Algorithms (WMDP++). arXiv:2608.22527。
- [L37] Paul et al. (2026-08). Can Scientific Claims Be Removed from LLMs? arXiv:2608.20960——现有方法只达"表层移除"。
- [L38] Kim et al. (2026-09). CONFS: Forget-Set Misalignment. arXiv:2609.00605——遗忘集与模型实际记忆错位。
- [L39] Li et al. (2026-09). ARIA: Test-Time Unlearning via Sparse Autoencoder. arXiv:2609.16229。
- [L40] Cha et al. (2024-08). LoKU: Parameter-Efficient Knowledge Unlearning. arXiv:2408.06621。

### E. 机密计算与 TEE（防护·硬件）
- [L41] Asad et al. (2026-08). Benchmarking Confidential Computing on NVIDIA Blackwell GPUs. arXiv:2608.26575——**B200 机密计算配置得当开销仅 1–3%（原生配置 30–40%）**。
- [L42] Arachchige et al. (2026-09). SpliTEE: DP-based GPU Outsourcing for TEE LLM Inference. arXiv:2609.15039。
- [L43] Shi et al. (2026-08). GIFT: GPU Information Flow Tracking for User Data Isolation. arXiv:2608.25431——**GPU 级信息流隔离，吞吐开销 4–10.7%**。
- [L44] Ge et al. (2026-09). TEE-Certified DP: Verifiable DP Training on Legacy GPUs. arXiv:2609.20532。
- [L45] Zhang et al. (2026-08). Breaking Shared-Direction Weight Obfuscation in TEE-Offloaded LLMs. arXiv:2608.26651——TEE 边界自身也有攻击（谱/格攻击泄露权重）。
- [L46] Zhou et al. (2026-09). Security Boundary of Obfuscation-based On-Device LLM Protection. arXiv:2609.10117。

### F. 水印与金丝雀（防护·溯源）——与我们机制三/五直接同域
- [L47] Park et al. (2026-09). WeaveMark: Multi-bit LLM Watermarking via Coded Payload Spreading. arXiv:2609.02177——**ECC 用于水印载荷纠错**。
- [L48] Feng et al. (2026-08). Tracing Provenance and Detecting Tampering with Complementary LLM Watermarks. arXiv:2608.12713——**双水印三态判定：完好/篡改/无水印**。
- [L49] te Lintelo et al. (2026-08). WoE Wrote It? Watermarking MoE LLMs. arXiv:2608.29151——**专家词表承载水印，TPR 90.1%@FPR 1%**。
- [L50] Bakshi et al. (2026-08). OpenStamp: Watermark for Open-Source LMs. arXiv:2608.27899——unembedding 层编码，耐改写与微调擦除。
- [L51] Zhang et al. (2026-08). SemTrace: Source-Grounded Semantic Signatures. arXiv:2608.29575——**受保护文档嵌事实签名，输出可暴露所读副本**（文档级金丝雀）。
- [L52] Weinberg (2026-05). SIGIL: Subtle Injection for Ground-truth Inference of Training Data. arXiv:2606.06502——**不可察觉金丝雀序列，改写后仍可统计检出**。
- [L53] Xie et al. (2026-04). CanaryRAG: Detecting RAG Extraction via Dual-Path Runtime Integrity. arXiv:2604.10717——**检索块内金丝雀实时检测提取攻击，免重训**。
- [L54] Raz et al. (2026-03). Safeguarding LLMs Using Steganographic Canaries. arXiv:2603.28655——隐写金丝雀文档，检测未经授权上传。
- [L55] Seiden et al. (2026-05). Identifying AI Web Scrapers Using Canary Tokens. arXiv:2605.13706——**金丝雀查明哪些爬虫喂了哪个模型（含未公开的）**。
- [L56] Nemecek et al. (2026-08). Auditing Cross-Lingual Fairness in Watermarking. arXiv:2608.20047。

### G. 信息流控制/守护栏/DLP（防护·结构）
- [L57] Shim et al. (2026-09). FLOWSEAL: Information Flow Control for LLM Agent Privacy. arXiv:2609.14003——**工具级信息流控制，泄漏近零**。
- [L58] Zhao et al. (2026-09). Skill-as-API: Confidential Multi-Agent Coordination. arXiv:2609.01677——**技能体不上线，只传名称/描述/模式**。
- [L59] Xi et al. (2026-08). Persona-Execution Separation. arXiv:2608.27427——人格与执行拆分为信任域+受治理桥接（DLP/审批/审计）。
- [L60] Zhang et al. (2026-08). LeakGauge: Measuring Context-Leakage with Behavior Gauges. arXiv:2608.17829——**prefill token 概率探测上下文泄漏风险，11 个模型高 AUROC**。
- [L61] Chen et al. (2026-08). Do System Prompts Leave Behavioral Fingerprints? arXiv:2608.24461——黑盒行为指纹检测系统提示词被克隆。
- [L62] Lyu et al. (2026-09). RAG-CT: Scanning Prompt Distribution to Mitigate RAG Privacy Risks. arXiv:2609.16095——**按查询熵/边际分布检测恶意 PII 提取查询**。

### H. 差分隐私与 RAG 隐私（补充）
- [L63] Ullah et al. (2026-05). DP-SGD-RC: Randomized Clipping. arXiv:2605.24879。
- [L64] Sha et al. (2026-05). DP-SelFT: Selective Fine-Tuning. arXiv:2605.17432。
- [L65] Almohaimeed et al. (2026-08). SEAG: Privacy-Preserving RAG via Alias Replacement. arXiv:2608.12675。
- [L66] Li et al. (2026-08). Mind the Hook: Source-Level Auditing of Privacy Defenses in RAG. arXiv:2608.09001——**部分 DP 防御实现是空壳钩子**：防御本身需要审计。
- [L67] Tran et al. (2026-08). Retrieved But Not Reliable: RAG Attacks & Defenses Survey. arXiv:2608.24978。
- [L68] Hua et al. (2026-08). Practical Private Dense Retrieval at Scale. arXiv:2608.25735。

### I. 中文白皮书与产业框架（5 份）
- [L69] 360 数字安全集团《大模型安全白皮书》（2025-11，世界互联网大会乌镇峰会发布）。
- [L70] 三未信安/江南科友/江南天安《大模型安全密码应用白皮书》（2025-04）——密码基座+**设计前移/模型内生安全/数据最小化**三原则。
- [L71] 火山引擎《AI 安全白皮书》（2025 底）——训练/推理全程机密性，可信基座（传输/存储/运行环境/访问控制/审计）。
- [L72] 之江实验室《生成式大模型安全与隐私白皮书》——显式/隐式双维数据安全分析。
- [L73] 中国信通院/蚂蚁集团《大模型安全实践白皮书》（2024 WAIC）——"蚁天鉴"安全测评实践。
- [L74] 上海财经大学等《大模型在金融领域的应用技术与安全白皮书》。

*检索方式注：A–H 域经 arXiv 官方 API（export.arxiv.org）8 个检索式获取，I 域经网络检索；全部条目"摘要级"采信，关键文献待精读。相关白皮书报道见 [清华大学WAIC报道](https://www.tsinghua.edu.cn)、[安全内参](https://www.secrss.com)。*

---

## 二、SOTA 地图（2026 年中，每域"能做到什么/公认极限"）

1. **记忆提取**：攻击端已覆盖自回归/扩散/任务机器人/代码补全全谱系且自动化；防御端出现首个可证明方案（L4）与记忆编辑防御（L10，攻击准确率可清零）；**公认极限：量化不是防护（L8）、聚合指标掩盖逐文档伤害（L9）、泄漏风险被标准指标低估 2.14 倍（L7）**。
2. **成员推断**：信号源从损失扩展到注意力（L13）、token 似然数组；战场扩展到 RAG 知识库（L16，AUC 0.99）；**极限：DP 强防御下联邦 MIA 仍可近 100%（L22）**——DP 不是银弹的再证实。
3. **注入/越狱**：生产级拦截器 79% 可绕过（L25）、真实 API 路由商参与攻击（L31）、17% 热门技能有漏洞（L29）；**共识转向：结构遏制（L34）、预执行审计（L28）、信息流控制（L57）取代提示过滤**；过防御误伤是新的头号工程问题（L27）。
4. **遗忘**：**"已遗忘"可被逆向找回（L35）**、压力测试下全面失守（L36）、只达表层移除（L37）——"删不掉"成为共识。
5. **TEE**：**2026 年格局剧变**——Blackwell 机密计算正确配置开销 1–3%（L41），GPU 信息流隔离 4–10.7%（L43），可验证 DP 训练（L44）；但 TEE 边界自身被攻破的案例已出现（L45）——纵深仍必要。
6. **水印/金丝雀**：ECC 载荷（L47）、双水印三态判定（L48）、MoE 专家水印（L49）、文档指纹（L51）、不可察觉金丝雀（L52）、RAG 运行时金丝雀（L53）、爬虫溯源（L55）——**溯源三件套已成独立爆发域，且都承认"统计可检、改写难逃"的设计目标**。
7. **合规/产业**：中文白皮书共识=**设计前移、内生安全、数据最小化、密码基座**（L70/L71）——与体系"判据优先、元数据优于原始数据"口径同向。

---

## 三、对标六机制（支持/竞争/空白/冲突四列法）

| 机制 | 文献支持（可行性已证） | 竞争/相近（先行者） | 空白（我们的差异化位） | 冲突/修正 |
|---|---|---|---|---|
| 一·涌现支付账 | FLOWSEAL 证信息流控制近零泄漏（L57）；LeakGauge 证 prefill 概率可探测泄漏（L60）；溯源作一等约束可落地（医院总结/INDRA 实践） | **无同构先例**——归因文献全部服务"忠实性/事实性"，无用作保密拦截判据 | **"无账涌现=幻觉∪泄露"统一拦截器：空白确认** | L15（1322 篇立场文）：来源账必须覆盖上下文/代理泄露，不只是训练语料——W_src 科目扩容 |
| 二·12 族签名 | RAG-CT（L62）证明"查询分布异常检测恶意提取"路线成立 | **RAG-CT 为弱同型**：只用熵/边际统计、只覆盖 RAG 查询域 | 12 族结构化分类+张力统计：更结构化的签名面（实体/主题/时序三通道） | 检出阈值必须红队标定防过防御（L27 教训） |
| 三·Steane 权重校验 | ECC 用于安全载荷已实践（L47）；权重层编码可行（L50） | 三态水印（L48）输出形态相同（完好/篡改/无） | **把 ECC 从"文本水印载荷"搬到"权重完整性+块级定位"：无先例** | 需与 L45 类攻击共测（TEE 边界攻击可绕过校验层） |
| 四·密级专家分片 | WoE 证专家级操作可行（L49）；Skill-as-API/人格-执行分离/结构遏制（L58/L59/L34）证"结构保密"范式成立 | 专家已被用作水印载体（L49），无人用作**密级容器** | **MLS-MoE：专家=密级容器+路径不生成：空白** | 激活率同构按 0910 纪律仅作启发（不变） |
| 五·YGC 金丝雀 | **整个域在爆发**：SIGIL/CanaryRAG/隐写金丝雀/爬虫金丝雀/合成金丝雀（L52/53/54/55/20） | 五个先行者全用随机序列或密码学 ID | **结构禁数 tr 签名：代数派生+批量+离线验证，数学面差异化** | 第三方闭源平台不配合处理金丝雀→仍限自持线（上轮结论不变，文献再证 L31 路由商不可信） |
| 六·保密窗口期 | 无直接文献（治理层空白） | 无 | 定位=治理层绑定件，与 L70"设计前移"原则互证 | — |

**空白位小结：四个空白（机制一/二/三/四）+ 一个差异化域（机制五）= 四个论文选题位**，每个都有相邻文献证明技术路线可行——这正是"体系原生入口成立"的文献版判据。

---

## 四、结论：我们如何让 AI 保密（文献背书版总案）

**三层合成（每层都引文献共识+体系件）**：

1. **结构层**（文献共识：过滤不可靠→结构/信息流）：CaMeL 系/ActGuard/FLOWSEAL/GIFT 为国际前沿；我们的**涌现支付账+密级专家分片**切入同层且无同构先例。
2. **证据层**（溯源三件套）：水印/金丝雀/审计为爆发域；我们的 **YGC 金丝雀+Steane 权重校验**以代数结构差异化切入。
3. **硬件层**：Blackwell 机密计算 1–3% 开销（L41）——**上轮"TEE 推荐部署"升级为"立即可做"**；GIFT 式 GPU 信息流跟踪（L43）作第二件。

**三大修正（相对上两轮结论，文献驱动）**：
- TEE：从"推荐部署"升"立即部署"——2026 实测开销已到个位数百分比（V4Pro 写作时此数据不存在）。
- 遗忘：从"可选防护"降为"不可信手段"——可被逆向找回（L35），**数据最小化/不让进压倒进去再删**——与三未信安白皮书"数据最小化"原则（L70）及体系"元数据优于原始数据"口径三重互证。
- 检测器：一切检测判据必须带误报率硬约束（L27 过防御警告）——我们 JC-A2 的 FPR<5% 判据从"工程参数"升"生存条件"。

---

## 五、行动建议（待知世）

| # | 事项 | 建议 | 依据 |
|---|---|---|---|
| 1 | 原型第一步 | 支付账+金丝雀在聆星本地线做原型；**基线用 SIGIL 式随机金丝雀、升级用 YGC 结构金丝雀，同台对比** | L52 vs 机制五；对比实验=论文核心表 |
| 2 | 论文选题（四个空白位） | 首选"涌现支付账"（体系原生最强+空白最大+复用 L57/L60 作组件）；次选 MLS-MoE | §三空白表 |
| 3 | 硬件采购口径 | GPU 采购配置要求加"机密计算模式（CC）"；已有设备查 Blackwell/H100 固件支持 | L41 |
| 4 | 女娲信道 | 维持上轮方案（金丝雀+会话账本）；本轮 L31 再证第三方路由不可信 | L31 |
| 5 | 精读任务 | L4/L15/L35/L41/L52/L57 六篇精读（直接支撑判据设计） | 摘要级→全文级 |
| 6 | 判据冻结 | JC-A1~E3 补两条文献驱动判据：JC-F1 过防御红线（误报硬上限）；JC-F2 金丝雀改写鲁棒性（对抗 L52 同款改写攻击） | §四修正3 |

---

## 六、术语字典

- **涌现支付账/12族签名/Steane校验/密级专家分片/YGC金丝雀/保密窗口期**：六机制，正本见《体系结合AI保密·机制与方案-v1.0-20260919》术语字典（本文不重复）。
- **TEE/机密计算（Confidential Computing）**：硬件可信执行环境；NVIDIA Blackwell 为 2025–2026 旗舰 GPU（B200），其 CC 模式对显存加密。
- **成员推断（MIA）/记忆提取/提示注入**：三大攻击族，V4Pro 十大路径对应物。
- **金丝雀（canary）**：预埋于数据/文档/检索块的可溯源标记；SIGIL/CanaryRAG 为文献代表方案。
- **水印放射性（radioactivity）**：水印经蒸馏/微调仍可检的特性（L24）。
- **信息流控制（IFC）**：按数据密级标签约束信息在系统内流向的结构化防护（L57/L43）。
- **DP-SGD/差分隐私**：训练加噪防护；本文按文献如实标注其极限（L22）。
- **过防御（over-defense）**：检测器误伤良性请求的失效模式（L27）。
- **CaMeL**：Google DeepMind 提出的能力-动作分离代理安全架构（L33 为其时序逻辑扩展）。
- **摘要级采信**：本文诚实标注——条目信息来自检索摘要，未逐篇核对全文；精读后才可入判据设计。
- **V4Pro**：《防止AI泄密-全维度分析-V4Pro》（2026-06-11），上两轮共享底本。

---

*AI保密·文献收集与对标报告 v1.0 ｜ ZCode ｜ 2026-09-19 ｜ 基座 62 篇+中文白皮书 5 份+承接 V4Pro 经典 20 篇 ｜ 状态：定稿·待知世阅*
