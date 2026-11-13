# G2-B GUI 统合实施设计（第一轮设计件）

- **日期**：2026-11-10｜**版本**：v1.0（第一轮送审稿）
- **任务编号**：D03-G2-B｜**依据**：任务书第五章（设计强制项）＋第七章（适配器）＋第八章（两轨隔离）＋第十章（授权边界）
- **与正本关系**：本件是 02《统一架构与多引擎路由设计》（8288a97d7705）在 G2-B 阶段的**下级实施分册**，不替代、不并行另立体系；与四份 G1 正本或知世已裁定事项冲突时，以正本与裁定为准。十层架构、四态语义、路由规则全部继承 02 件，G2-B 只做最小实现。
- **输入审计件**：`02_行为审计/` 四件（功能清单 F01–F34＋N1–N9、调用关系 11 链＋S1–S7、十项冻结映射、六缺陷防护映射）；G2-A 实测报告（077ebfbea5ff）。
- **基线**：tar 正源 `hamilton_ui_v2.py`（ede0c6df6082，95,562 B，1869 行）；工作副本已就位且哈希一致。

---

## 一、总体方针

恢复，不是重写。v0.5 壳 = v0.3 全部产品行为（十项冻结）＋ 17:10 真严格引擎安全接入 ＋ 六处缺陷适配层兜底 ＋ 四态统一接口。授权链零改动；严格/广义彻底分账；一切修改限于 G2-B 工作区，正源与旧版一个字节不碰。G3 统一内核重构、G4 验证体系、G5 大规模验收、G6 发布均不提前。

## 二、模块树（app/）

```text
05_GUI实现/app/
├── main.py                  # 入口：Tk root＋App 装配（对应正源 main L1862）
├── version.py               # 单一版本常量 v0.5（N9：消除正源 L2 "v0.2" 与 L278 "v0.3" 并存）
├── constants.py             # 色板/文案/PRODUCT_ID/LICENSE_FILE/AUTH_TOKEN 等常量搬移
├── ui/                      # L1 GUI 产品壳层
│   ├── main_window.py       # 主窗口/欢迎窗/激活门禁顺序/彩蛋口令/严格Tab生命周期/watchdog
│   ├── general_tab.py       # 广义 Tab（原 _build_solve_tab/_run/_continue 行为）
│   ├── strict_tab.py        # 严格 Tab（原 _build_strict_tab/_run_strict/门禁/显式构造入口）
│   ├── widgets.py           # 日志窗/结果卡/进度条/状态栏公共控件
│   └── dialogs.py           # 激活/续期对话框、错误与完成弹窗
├── auth/
│   └── auth_bridge.py       # L2：只包 check_license(key, product_id)；三重态；门禁/复查接口
├── graph/
│   ├── normalize.py         # L3：graph_formats 六格式→标准图；十项输入检查；N E 头行
│   ├── precheck.py          # L4：保守必要条件预检（四类证书）
│   └── construct_families.py# 13 族公式逐字节搬移（parse_construct_params＋construct_seq_and_check）
├── engine/
│   ├── router.py            # L5 最小路由：mode→适配器（G2-B 三通道，14 条完整路由表留 G3）
│   ├── strict_adapter.py    # L6：17:10 严格引擎适配器（15 职责，§七）
│   ├── walk_adapter.py      # L6：solver_verify.exe 广义适配器（v0.3 CLI 原样）
│   └── eng_host.py          # L6 公共：子进程双流 drain/硬超时/句柄登记簿/关闭清理
├── validation/
│   ├── strict_validator.py  # L9 严格独立裁判（接线 G2-A judge_strict_path.py 判据）
│   └── walk_validator.py    # L9 广义裁判（全覆盖+真边+膨胀率如实；G4 前的最小实现）
├── reporting/
│   ├── report.py            # L10：四段报告格式冻结；严格轨补建（填真值）
│   └── export.py            # L10：三件套/10列路径/桌面优先TEMP降级/弹窗告知
├── monitoring/
│   └── resource_monitor.py  # CPU 监控（wmic→现代 API，可改善项；失败静默降级）
└── logging/
    └── event_log.py         # 事件日志滚动＋任务七件留存索引（jsonl 可新增）
```

**与任务书 §5.1 建议结构的差异（说明义务）**：新增 `version.py`/`constants.py`（N9 与常量集中，防脱敏漏扫）、`engine/router.py`（02 正本 L73 明令禁止 L1 直调 L6——v0.4 融合壳 `_run_fusion` 直调路由的做法在统合版终止；G2-B 用最小三通道路由满足层序，完整 14 条路由表留 G3）、`graph/construct_families.py`（13 族公式独立成模块便于逐字节对照与 G2-C 逐族验收）。其余与建议结构一致。

## 三、十层架构映射（02 正本 §一继承）

- **L1 GUI 产品壳层** → `ui/*`＋`main.py`。只收集输入、调 L2 门、经 L5 统一接口发请求、显示状态与 L10 回传结果。工作线程求解，主线程零阻塞。
- **L2 模式与授权控制层** → `auth/auth_bridge.py`＋`ui/main_window.py` 内的口令/watchdog 交互（交互属 L1，判定全委托 L2）。门禁前置、三重复查、过期只锁严格层。
- **L3 图数据标准化层** → `graph/normalize.py`。六格式统一供两轨（关闭 v0.4 融合壳绕过 graph_formats 的缺口，02 件附录甲#9）。
- **L4 图结构预分析层** → `graph/precheck.py`。G2-B 只实现保守必要条件四类证书；特征档案全量留 G3。
- **L5 求解器路由层** → `engine/router.py`。G2-B 三通道：strict→strict_adapter；walk→walk_adapter；显式构造→construct_families 直写＋L9。P-0 运行前授权复查在此层再核一次（02 件 §3.1）。
- **L6 多引擎适配层** → `engine/strict_adapter.py`/`walk_adapter.py`/`eng_host.py`。五适配器全量留 G3；G2-B 只接两引擎（17:10 严格＋solver_verify 广义），v23_static/分图而治/pyd 直写器不接入。
- **L7 分块与缝合层** → 预留槽，G2-B 不实现（不提前做 G3）。
- **L8 修复与优化层** → 预留槽；引擎内部修复由引擎自担；"继续求解"预算加倍语义（v0.3 `_continue` L1532）在广义轨保留。
- **L9 独立验证层** → `validation/*`。横切强制：任何出解必过；runner≠judge。
- **L10 结果日志报告层** → `reporting/*`＋`logging/event_log.py`。四态终稿、报告/路径/图三件套、任务七件留存。

依赖方向单向向下，L9 横切监督 L6，L2 是门不是变换；禁止跨层调用（GUI 不直接解析引擎输出、不直接 Popen）。

## 四、模块职责卡（输入/输出/依赖/错误类型/GUI访问/授权访问/进程权限）

图例：GUI访问=能否直接操作 Tk 控件；授权访问=能否 import/调用 auth 组件；进程权限=能否启动外部进程。

### main.py
入口装配。输入：命令行/无；输出：进程退出码；依赖：ui.main_window、version；错误：启动异常→弹窗＋日志；GUI：是（创建 root）；授权：否（经 L2）；进程：否。

### version.py / constants.py
纯常量。输入：无；输出：常量；依赖：无；错误：无；GUI/授权/进程：否/否/否。AUTH_TOKEN 自正源 L282 原样搬移（**值不进任何文档/日志/报告**；G2-A 实测严格引擎不读该 token，注入行为保留只为广义引擎兼容）。PRODUCT_ID='hamilton'、LICENSE_FILE 路径不变。

### ui/main_window.py
输入：用户操作、L2 授权态、L10 结果；输出：标准化求解请求给 L2→L5、界面渲染；依赖：auth_bridge、router、dialogs、widgets、general_tab、strict_tab；错误：UI 异常兜底弹窗，不崩主窗；GUI：是；授权：经 auth_bridge（不直接 import auth.pyd）；进程：否。职责：欢迎窗 1800ms、门禁前置（未激活不构建主界面）、彩蛋口令字面/大小写/会话级/再输隐藏、严格 Tab 懒创建与 forget、30s watchdog、关闭钩子（调 eng_host 清理，S6）。

### ui/general_tab.py
输入：N/m/seed/文件路径；输出：walk 请求；依赖：router、normalize（经请求对象）、widgets；错误：输入非法→弹窗拒绝（不发进程）；GUI：是；授权：否（广义不受严格授权扰，激活门禁在 L2 主门）；进程：否。保留：默认 N=1000000/m=3/seed=42、种子框双绑定（彩蛋入口）、全局 Return 路由（默认保留 v0.3 语义→广义，备查项见 §十四）、_continue 预算加倍、热梗轮播（可改善项）。新增忙检查（N6，技术漏洞自补，不改判定语义）。

### ui/strict_tab.py
输入：N/m/seed/文件/13族参数；输出：strict 请求；依赖：router、widgets、dialogs；错误：输入非法/授权不过/m<10→弹窗拒绝；GUI：是；授权：经 auth_bridge 运行前复查；进程：否。保留：默认 N=10000/m=10/seed=42、m≥10 门禁弹窗（文件导入与显式构造豁免）、13 族入口全参数语义、独立日志/结果/进度控件。显示文案：严格成功「严格哈密顿路径验证通过」；四态文字全显示（颜色不替代文字）。

### ui/widgets.py / ui/dialogs.py
公共控件与弹窗。输入：文本/状态；输出：渲染；依赖：tk/ttk、constants；错误：兜底；GUI：是；授权/进程：否。激活/续期对话框复用同一流程（正源 L465–516 语义：一用一废提示、失败留窗重试、WM_DELETE_WINDOW=退出）。

### auth/auth_bridge.py
输入：key（可空）、product_id；输出：(ok, msg, state) 原样透传＋三重态封装 ok/expired/invalid；依赖：auth.pyd（sys.path 注入 server_v2，正源 L265–270 方式原样）；错误：import 失败→门禁拒绝启动（正源 L455–457 语义）；GUI：否；授权：**唯一允许直接访问授权组件的模块**；进程：否。不复制、不重写、不绕过授权核心；72h 宽限/一用一废/产品域隔离全在 pyd 内，壳只消费返回值。缓存路径/license.key 读写语义与正源 L437–450 一致。

### graph/normalize.py
输入：文件路径或 (N,m,seed) 生成参数；输出：标准图对象（N、边表、格式警告、ID 映射）或输入错误；依赖：graph_formats.pyd（gf，格式解析件非计算引擎，v0.3 进程内模式保留；缺失时纯 Python 边表兜底）；错误：InputError（十项检查逐条明示）；GUI：否；授权：否；进程：否。十项检查＝存在/可读/非空/节点数有效/边格式/非法编号/自环/重复边/越界/连通性（连通性结果交 L4 出证书）。头行 `N E` 重写语义保留（正源 `_rewrite_edgelist_head` L1335）；每任务唯一临时名（N5）。

### graph/precheck.py
输入：标准图；输出：放行 或 证书（EMPTY/DISCONNECTED/DEG1_GT2/BRIDGE_TREE_NOT_TRACEABLE）；依赖：无（纯算法；桥块树判据对照分图而治 v2.5 现版复用须先对拍）；错误：内部异常→放行并记日志（保守优先，宁可放行不误杀）；GUI：否；授权：否；进程：否。只查已证明必要条件；两三角一桥必须放行；证书文本落报告。

### graph/construct_families.py
输入：族名＋参数字符串；输出：(seq_gen, is_real, N, E) 或参数错误；依赖：无；错误：ParamError（13 族约束原样）；GUI：否；授权：否；进程：否。**公式逐字节搬移**（正源 L26–251），G2-B 不改一字；独立流式裁判接线在 L9（可新增，不改自检语义）。

### engine/router.py
输入：SolveRequest（mode、图引用、N/m/seed、budget、options）；输出：SolveResult 透传；依赖：auth_bridge（P-0 运行前复查）、strict_adapter、walk_adapter、construct_families、precheck、normalize；错误：路由异常→ERROR；GUI：否；授权：经 auth_bridge；进程：否（由适配器启动）。G2-B 三通道最小路由；引擎可用性探测＝文件存在＋哈希核对（基线件值）；14 条完整路由表留 G3。

### engine/strict_adapter.py
输入：标准图＋seed＋budget＋任务目录；输出：SolveResult 字典（§七）；依赖：eng_host、strict_validator、precheck（经路由已查则不重复）、reporting；错误：ParamError/InputError/EngineError/ParseError/JudgeError→四态映射；GUI：否；授权：否；进程：**是（经 eng_host）**。15 职责见 §七。CLI 严格按 G2-A 实测构造，恒带 --dump；弃用正源占位尾（N1）。

### engine/walk_adapter.py
输入：walk 请求；输出：SolveResult；依赖：eng_host、walk_validator、reporting；错误：同上；GUI：否；授权：否；进程：是（经 eng_host）。CLI 原样保留 v0.3：`solver_verify.exe --verbose [图文件 | --ba N m seed] [占位] 输出路径`（占位协议是 walk 引擎实测在册行为，与严格引擎不同，**保留**）；env 注入 YS_AUTH_TOKEN 保留。报告由引擎自写，壳读回（_read_report_status 语义）。

### engine/eng_host.py
输入：argv、env、budget、任务目录；输出：退出码＋stdout/stderr 文件路径＋超时标志；依赖：subprocess/threading；错误：LaunchError/TimeoutKill；GUI：否；授权：否；进程：是（唯一 Popen 出口）。双流并行 drain 到文件（N7 死锁修复）；硬超时＝budget＋宽限（默认 30s）→kill；句柄登记簿（S1）；关闭时全杀（S6）；每任务独立进程/目录/日志（缺陷③防污染）。

### validation/strict_validator.py
输入：图文件路径＋路径文件路径（重读磁盘，不信任内存对象）；输出：PASS/FAIL＋失败边清单＋指标（长度/重复/覆盖/真边）；依赖：G2-A judge_strict_path.py 判据（独立实现或子进程调用，二选一在批次6定，默认进程内独立函数＋纯标准库）；错误：JudgeError→ERROR 不→UNSOLVED；GUI：否；授权：否；进程：否（默认）。四查：长度=N、无重复、全覆盖、步步真边。

### validation/walk_validator.py
输入：图＋walk 路径；输出：全覆盖/真边率/膨胀率如实；依赖：纯标准库；错误：同上；GUI/授权/进程：否。G4 前的最小实现；广义成功文案「广义覆盖 walk 验证通过」，永不出现 Hamiltonian Path PASS。

### reporting/report.py
输入：SolveResult＋任务七件；输出：四段报告文件（[summary]/[verification]/[failed_edges]/[path]）；依赖：无；错误：ReportError→日志＋UI 警告（正源 L1649 语义）；GUI/授权/进程：否。段格式与 version 行冻结（`# version: v0.3-strict-engine` 保留——它是报告协议指纹，不是产品版本号）；N3 修复：E/seed 填真值、[path] 段回填 --dump 终稿序列；virtual_count 字段名原样（冻结行为7，界面不显示该词，备查项 §十四）。

### reporting/export.py
输入：报告＋路径序列＋图文件；输出：三件套落盘＋落点告知；依赖：os/shutil；错误：ExportError→降级/警告；GUI：否（弹窗由 UI 层发）；授权/进程：否。桌面优先试写→TEMP 降级（正源 L1504–1512 语义）；路径每行 10 节点空格分隔＋注释头（L1745–1752 格式）；文件名冲突加序号不覆盖；完成告知存哪（冻结行为7）。

### monitoring/resource_monitor.py
输入：定时 tick；输出：CPU 百分比字符串；依赖：现代 API（wmic 替代，可改善项；优先 psutil 若可用，否则 PowerShell Get-Counter 兜底，再失败显示 --）；错误：静默降级；GUI：经回调变量；授权/进程：否（PowerShell 兜底属只读查询，不算引擎进程）。周期 2s 保留（正源 L756–762）。

### logging/event_log.py
输入：事件；输出：滚动日志文件＋jsonl 任务索引（可新增）；依赖：logging；错误：日志失败不阻塞求解；GUI：否；授权：否；进程：否。任务七件留存索引：stdout/stderr/exit/RESULT/VERIFY/path/裁判结果（缺陷⑥）。**日志与 jsonl 不含 AUTH_TOKEN 值、不含体系常数**（脱敏扫描覆盖）。

## 五、GUI 与引擎隔离（任务书 §5.3）

1. **严格引擎独立进程**：strict_adapter 经 eng_host Popen，GUI 主进程不加载任何计算引擎。
2. **pyd/DLL 计算引擎不进 GUI 主进程**：hamilton_engine.pyd、walk_engine.dll 等计算件 G2-B 一律不 import（v23_static 是 EXE 也留 G3）。**澄清**：auth.pyd 是授权组件、graph_formats.pyd 是格式解析件，均非计算引擎；v0.3 正源即在进程内 import（L260/L272），链验六件伴生语义要求 auth.pyd 与原目录伴生件同在——auth_bridge 沿用 sys.path 注入方式，**不复制伴生件、不进新链验清单**（02 件 D② v0.4 换芯版已验先例）。
3. **GUI 只做五件事**：收集输入、调统一接口（router）、显示状态、接收结果、展示验证报告。
4. **适配层只做七件事**：参数校验、文件准备、子进程启动、stdout/stderr 捕获、超时控制、结果解析、原始输出留存。
5. **独立验证层只做四件事**：重读输入图、检查输出路径、判断合法性、返回结论。裁判不 import 引擎、不读引擎内存态，只读磁盘文件。

## 六、统一四态接口（任务书 §5.4＋02 正本 §2.3）

```python
SOLVED                 # 独立验证通过（严格：四条件合取；walk：L9 全覆盖+真边）
UNSOLVED               # 超时/预算耗尽/未找到解——绝不等于无解
INFEASIBLE_CERTIFIED   # 仅三种来源：L4 四类证书 / BA m=3 定理 / CP-SAT INFEASIBLE
ERROR                  # 输入/进程/文件/解析/裁判异常——绝不包装成 UNSOLVED
```

判定纪律：引擎自报成功≠SOLVED；退出码≠判据；路径文件存在≠判据；日志 ERROR 字样≠判据。显示映射（冻结行为6）：SOLVED(严格)→complete 文案；SOLVED(walk)/非严格→walk＋⚠标红；部分覆盖→partial；UNSOLVED→"未找到解（预算耗尽）"；INFEASIBLE_CERTIFIED→"已认证无解＋证书"；ERROR→"系统错误＋原因"。六种状态文字（求解中/已验证成功/未找到解/已认证无解/系统错误/等待授权）颜色不替代文字。

## 七、严格适配器详细设计（任务书第七章）

**15 职责**（顺序即流水线）：①接收标准化图→②校验参数→③结构预检（路由层已查则核证书不重复跑）→④创建唯一任务目录→⑤构造 CLI→⑥启动引擎（eng_host）→⑦捕获 stdout→⑧捕获 stderr→⑨控制时间预算→⑩收集输出文件→⑪解析 RESULT→⑫解析 VERIFY→⑬读取路径（只取 `_path.txt`）→⑭调用独立裁判→⑮返回四态结果。

**输入接口**（按 G2-A 实测调整）：

```python
solve_strict(graph, seed=42, budget=3600, output_dir=None, starts=3, m=None)
# graph: 标准图对象（含边表文件落盘路径）；m 与 load-graph 二选一
```

**CLI 构造**（G2-A 实测协议，弃用正源占位尾 N1）：

```text
生成模式: solver_strict_engine.exe N seed --m m --budget S --starts 3 --dump {task}/out
导入模式: solver_strict_engine.exe N seed --load-graph {task}/graph.edges --budget S --dump {task}/out
```

N≥3、m≥1、seed 整数、budget 正数，发射前全验证（缺陷①②）。头行 N 与 CLI N 一致性校验（a6_n_mismatch 教训）。

**输出结构**（任务书 §7.3 字段齐全＋G1 调整）：

```python
{
 "status": "SOLVED|UNSOLVED|INFEASIBLE_CERTIFIED|ERROR",
 "engine": "strict_17_10",
 "path": [...],                  # 仅 SOLVED 时非空
 "metrics": {"N":…, "L":…, "unique":…, "dup":…, "breaks":…, "expansion":…, "time":…},
 "verification": {"judge":"PASS|FAIL", "failed_edges":[…], "checks":{…}},
 "certificate": None|{…},        # INFEASIBLE_CERTIFIED 时必有
 "stdout_file": "…", "stderr_file": "…", "report_file": "…",
 "exit_code": …, "result_line": "…", "verify_line": "…",
 "task_dir": "…", "error": None|"原因"
}
```

**解析规则**（G2-A 实测协议）：RESULT 行 `RESULT N=%d starts=%d L=%zu unique=%d dup=%d breaks=%d best=%d repair_rounds=%d time=%.1fs`；VERIFY 行 `VERIFY strict=YES/NO expansion=%.6f (…)`。结构化逐字段解析（不用简单字符串搜索判成功）；缺字段/重复/非法数字/格式错/编码异常/不完整→ParseError→ERROR 明示，不猜测。正源 L1630–1639 的 RESULT→V= 转换保留为**显示层兼容**，判定链不依赖它。

**时间预算**：上层传入（默认 3600 继承正源 L1276/L1296）；适配器不放大；硬超时＝budget＋30s 宽限→kill→保存日志与任务信息→UNSOLVED（进程异常→ERROR）。

**并发**：每任务独立目录（`%TEMP%/ys_strict_{ts}_{uuid}/`）、独立输出/日志/句柄/超时；任务目录保留作证据（不自动删，清理策略在批次10定）；转换临时件任务结束即清（正源 L1848–1854 语义）。

**SOLVED 四条件合取**（缺陷③核心）：strict=YES ∧ RESULT 完整解析 ∧ 本任务 `_path.txt` 可读格式合法 ∧ 独立裁判 PASS。自报成功但裁判失败→ERROR＋留存失败路径/失败边，绝不 SOLVED、绝不伪造路径。

## 八、GUI 两轨隔离与文案（任务书第八章）

严格轨显示：模式/N/seed/图来源/预算/当前状态/严格路径/独立验证结果/导出位置。广义轨显示：模式/覆盖/重复/步数/断边数/独立 walk 验证结果。文案硬隔离：严格成功「严格哈密顿路径验证通过」；广义成功「广义覆盖 walk 验证通过」；广义结果永不出现「Hamiltonian Path PASS」；两轨指标不混算（节点数/步数/路径长度/成功率各账各表）。⚠非严格解标红语义保留（正源 L1705–1707）。状态六文字见 §六。

## 九、授权边界与接口记录（任务书第十章）

**三代接口实证**（签名一致，本轮 grep 复核）：

- v0.3 正源：L272 `from auth import check_license as _check_license`（sys.path 注入 server_v2 L265–270）；调用 L459（门禁·缓存 key）/L493（激活·新 key）/L789（状态复查）；返回 `(ok, msg, state)`；state 'grace'（L588 状态文案）、'expired'（L795）。
- v0.4 融合壳（D:\data\scratch\strict_hp\v03_build_ui\hamilton_ui_v2_v04_fusion.py，2eb8376a2e78）：L33 import、L227/L260 调用、L57 PRODUCT_ID、L830 env 注入。
- v0.4 换芯版（H:\理论存档\04-哈密顿路径\04-工具与代码\解限版v0.4-gui-20261108b.py，fa935112ab53）：L14 `import auth`、L16 PRODUCT_ID、L130/L150 `auth.check_license(key, PRODUCT_ID)`。

**auth_bridge 设计**：只包这一个签名；三重态封装（ok/expired/invalid）语义与正源 `_auth_status` L781–797 逐字一致；import 失败→门禁拒绝（L455–457）；缓存读写路径不变（LICENSE_FILE L284–285）；续期重置 `_expired_notified`（L497）。

**零改动清单**：六件伴生（auth.pyd/hamilton_ui_v2.pyd/hamilton_crypto.pyd/graph_formats.pyd/v23_static.exe/solver_verify.exe）、链验清单、密钥、token、缓存结构、product_id、一用一废、72h 宽限——全部不碰；新 GUI 不进链验清单；基线件 25 项哈希跑前跑后对照。G2-D 三场景（已激活 verify／新密钥首用自动激活／真机过 gate）保留，本阶段不伪造激活。

## 十、N1–N9 / S1–S7 修复映射

- N1 占位尾（严格轨）→ strict_adapter 干净 CLI＋--dump（walk 轨占位保留，引擎协议不同）。
- N2 strict_ok OR 自报分支（L1571）→ 四条件合取，裁判强制。
- N3 报告 E=0/seed=0/[path]空 → report.py 填真值＋--dump 回填（格式冻结不变）。
- N4 float('True') 显示（L1688–1691）→ 适配器输出数值 real_edge_rate，显示层不再吃布尔字符串。
- N5 固定 TEMP 名 → 任务目录唯一名。
- N6 广义无忙检查＋全局 Return → 忙检查自补（技术漏洞）；Return 路由默认保留 v0.3 语义（备查项）。
- N7 wait 后读 stdout 死锁 → eng_host 双流并行 drain 到文件。
- N8 关闭无清理 → 主窗 WM_DELETE_WINDOW 钩子＋句柄登记簿全杀。
- N9 版本号并存 → version.py 单一常量（报告 version 行是协议指纹，另保留）。
- S1 单句柄 → 登记簿；S2 输出字段共享 → 结果随任务字典走；S3 固定转换名 → 唯一名；S4 死锁 → 同 N7；S5 跨线程 UI → root.after 纪律保留＋winfo_exists 兜底；S6 关闭清理 → 同 N8；S7 严格 Tab 三态生命周期 → 原样保留（未激活不创建/过期 forget/会话长存）。

以上全部不改十项冻结语义；N6 忙检查、N7/N8 稳定性属技术漏洞自补范围（方向不变）。

## 十一、批次实施计划（任务书第十一/十二章）

批次1 骨架（语法/导入/依赖）→ 批次2 基础窗口（启动/双Tab/关闭/重复启动）→ 批次3 激活门与彩蛋（零痕迹对象树断言）→ 批次4 授权联动（过期/续期/watchdog）→ 批次5 图输入与预检（两三角一桥锚）→ 批次6 严格适配器（**独立测试先行，六缺陷逐条证据**）→ 批次7 严格轨接线（UI 不冻结/关闭清理）→ 批次8 广义隔离（文案/指标分账）→ 批次9 导出（三件套/降级/10列）→ 批次10 稳定性（并发/异常/清理）。每批九步流程（目标→重读源码→基线→最小方案→实施→静态检查→实跑→存证→PASS/FAIL/BLOCKED/NOT TESTED），只有 PASS 进下一批；每批报告落 `05_GUI实现/批次X_…报告.md`；进度文件随批更新。截图 14 张按任务书第十四章真实获取（未激活附对象树证据）。收尾独立验收 Agent（第十五章）＋10 件交付（第十七章）。

## 十二、回滚与资产保护

全部新代码在 `05_GUI实现/`，构建在 `09_构建/`，回滚说明在 `10_回滚/`；正源/旧版 EXE/引擎/授权件只读（基线 25 项哈希对照）；任何批次失败→该批文件隔离标记，不覆盖前批 PASS 件；工作区整体删除即完全回滚（桌面现役程序零影响）。写入卫生：含反斜杠路径正文只用写文件工具，写后控制字符扫描。

## 十三、§5.5 七问自审（逐问作答）

1. **是否破坏 v0.3 行为？** 否。十项冻结逐项有映射表与回归测试；N1–N9 修复全部经语义影响评估（§十），只修缺陷不改判定；两处备查项（virtual_count 读法、Return 路由）按保守默认执行并报知世。
2. **是否违反十层架构？** 否。L1→L10 单向依赖，新增 router.py 关闭 L1 直调 L6 的违规通道；L7/L8 预留槽不提前实现；L9 横切强制。
3. **是否修改授权链？** 否。auth_bridge 只包接口；六件伴生/清单/密钥/token/缓存/product_id/一用一废/72h 全零改动；哈希跑前跑后对照。
4. **是否把严格与广义混在一起？** 否。两适配器、两裁判、两套文案与指标；四态出口统一但账目不混；广义永不冒充严格。
5. **是否遗漏 G2-A 六处缺陷？** 否。六缺陷防护映射表逐条对到模块与测试；批次6独立测试先行是硬门。
6. **是否把 G3/G4 工作提前扩大到 G2-B？** 否。路由只做三通道（14 条留 G3）；walk 裁判最小实现（完整体系留 G4）；13 族只保接线（逐族验收留 G2-C）；L7/L8 不动。
7. **是否存在无法回滚的修改？** 否。一切限于工作区；正源只读；批次件隔离；工作区删除即完全回滚。

自审结论：设计可进入第一轮报告送审；**不自动进入批次1**，候知世检查方向。

## 十四、报知世备查项（不代裁，保守默认已注明）

1. **virtual_count 报告字段**：冻结行为7（报告协议）与行为9（界面脱敏）并存读法＝字段保留、界面不显示该词。默认照此执行；若须连报告字段一起脱敏，属"改前须知世明示"。
2. **全局 Return 路由**：v0.3 全局 Return→广义求解（L717），严格页聚焦时亦如此（种子框口令命中才 'break'）。默认保留；如要改为"当前 Tab 路由"属行为变更，候明示。
3. **六件待裁定事项**（G1 总审在册）：G2-B 不触及，继续按保守默认挂起。
4. **AUTH_TOKEN 常量**：自正源原样搬移入 constants.py（值不进文档/日志/报告）；G2-A 实测严格引擎不读它，注入保留只为广义兼容。

---
*本件为第一轮设计送审稿；未写任何实现代码；未修改任何受保护件。*