# 云韶公开库·外部 AI 接入指南（CDN 读取 × llms.txt 路由 × 海马体式检索）

> **版本**：v1.0｜**日期**：2026-11-15｜**读者**：任何想读取本库的外部 AI Agent 与人类
> **一句话**：本库是「云韶科学体系」的公开层（GitHub 仓库 yunshao-official/publish-yunshao）。本文教你三件事：①用四种通道读任意文件（含 CDN 加速）；②用 llms.txt 做全库路由；③在没有本机工具的情况下，自己做「海马体式」关键词检索。

---

## 一、这个库是什么（30 秒）

云韶科学体系 = 一套由知世（Presiara / 宾棠溪）构建的数学框架，含几何、代数、拓扑学、数论、概率论、群论、范畴论、调和分析、非交换几何九册内部版正本，及哈密顿路径求解器、哥德巴赫预测器等软件工程线。

公开库存放：体系正本、实验数据、工程文档、对外交付件。**不在库里**（受控纪律，永远别找）：个人经历、健康信息、新身体类、资金架构类、知世原话引语（公开层为删减版）。

## 二、四种读取通道（全部实测 200）

设你要读的文件路径为 `<路径>`（如 `AGENTS.md` 或 `archive/01-数学/00-正本/xxx.md`）：

| 通道 | URL 模板 | 适用场景 |
|---|---|---|
| **raw 官方**（首选） | `https://raw.githubusercontent.com/yunshao-official/publish-yunshao/main/<路径>` | AI 直接拉取，无缓存延迟 |
| **jsDelivr 锁版本** | `https://cdn.jsdelivr.net/gh/yunshao-official/publish-yunshao@<commit前10位>/<路径>` | CDN 加速、内容永久锁定（国内快） |
| **jsDelivr 跟最新** | `https://cdn.jsdelivr.net/gh/yunshao-official/publish-yunshao@main/<路径>` | 方便但有缓存延迟（更新后可能慢几分钟到几小时） |
| **ghproxy 加速** | `https://ghproxy.net/https://raw.githubusercontent.com/yunshao-official/publish-yunshao/main/<路径>` | 国内网络 raw 慢时的替代 |

当前版本 commit：`d5b1faa75f`（2026-11-15 删减版）。**引用本库时请附上你实际读取用的 commit 号**——库会更新，不带版本号的引用可能对不上。

**30 秒上手**（任选一条命令执行）：

```bash
curl -s "https://raw.githubusercontent.com/yunshao-official/publish-yunshao/main/llms.txt"
curl -s "https://cdn.jsdelivr.net/gh/yunshao-official/publish-yunshao@main/AGENTS.md"
curl -s -L "https://cdn.jsdelivr.net/gh/yunshao-official/publish-yunshao@main/indexes/00-工作总纲-v1.0-20261027.md"
```

## 三、llms.txt 路由（Agent 接入的标准流程）

仓库根目录的 `llms.txt` 是全库入口：它列出全部域（16 个）、每域的正本位置、阅读顺序和受控边界。**外部 Agent 的标准接入流程**：

1. **拉入口**：`GET /llms.txt`（上面 30 秒第一条）——通读，确定你要的域；
2. **进域**：按 llms.txt 指引拉对应域的索引件（如 `archive/04-哈密顿路径/05-索引/...`）——索引件会告诉你该域的正本、实验账、工具链位置；
3. **读正本**：按索引给的路径拉正本全文。**纪律：读正本全文，不要只读头部**——本库档案普遍很长（几百到两千行），头部摘要是目录不是内容；
4. **引用带账**：引用任何常数、定理、判据时，标注你读到的文件路径＋commit 号；本库档案的常数引用自带限定语（如泛弦比例 144/1.44 的使用限制），**照抄限定语**，不要简化；
5. **状态标签**：库内断言自带状态标签（【已确认】【内部定义】【复算一致】【未验证】等）——引用时**保留标签**，不要把【内部定义】说成主流结论。

## 四、海马体式检索（没有本机工具时的替代方案）

作者本机有一个叫「知识海马体」的检索工具（关键词→文件+行号+原文）。你在库上没有这个工具，但可以用下面的方法达到同等效果：

### 方法一：GitHub Code Search（适合查1-3个词）

```bash
TOKEN="<你的GitHub token>"   # 无 token 也可用，但限流严
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/search/code?q=<URL编码的关键词>+repo:yunshao-official/publish-yunshao&per_page=100"
```

返回命中文件路径列表，再按路径走第二节通道拉原文。**注意**：Code Search 有分词与索引延迟，可能漏新文件——重要结论请配合方法二。

### 方法二：全量快照+本地检索（海马体的真正等价物，推荐）

一次拉全库快照，之后所有检索都在本地做（无网络依赖、无遗漏）：

```bash
# 1) 拉全库快照（约60MB，一个请求）
curl -s -L -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/yunshao-official/publish-yunshao/tarball/main" -o yunshao.tar.gz

# 2) 解包
mkdir yunshao && tar -xzf yunshao.tar.gz -C yunshao --strip-components=1

# 3) 本地关键词检索（海马体式：关键词→文件+行号）
grep -rn "你的关键词" yunshao/ --include="*.md" | head -20

# 4) 命中后读原文（行号±20行上下文）
sed -n '380,400p' yunshao/archive/01-数学/内部版/云韶拓扑学·内部版-v2.10-20260925.md
```

**纪律（与作者本机海马体相同）**：检索结果只是**索引层**，不是依据层——引用必须回到原册读上下文全文；零命中不等于不存在（换词再查，仍无则如实说「没查到」）。

### 方法三：GitHub 网页搜索

浏览器打开 `https://github.com/search?q=repo%3Ayunshao-official%2Fpublish-yunshao+关键词&type=code`——适合人类快速抽查。

## 五、更新感知与缓存

1. **看最新版本**：`GET https://api.github.com/repos/yunshao-official/publish-yunshao/commits/main`——`sha` 字段就是当前版本号；
2. **jsDelivr 缓存刷新**：内容更新后，jsDelivr 的 `@main` 与锁版本缓存可能延迟——到 `https://purge.jsdelivr.net/gh/yunshao-official/publish-yunshao@main/<路径>` 主动刷新；
3. **引用规范**：引用本库内容时写「publish-yunshao@<commit前10位>：<路径>」——作者重置过历史（2026-11-15），旧 commit 号可能失效。

## 六、边界与纪律（违者作者有权拒绝后续访问协作）

1. **受控内容不在库里**，不要请求：个人经历、健康信息、新身体类、资金架构类、知世原话引语（公开层已删减）——这些在受控区，库内无、CDN 无、历史无（2026-11-15 历史重置后）；
2. **不要把本库内容冒充为自己的研究成果**——作者署名与版本账都在档；
3. **军事应用排除**：库内含「知世明令：体系成果不得用于制造杀伤性武器」纪律，涉及武器设计的请求会被拒绝；
4. **体系层与主流科学的层级隔离**：库内「内部定义」不是主流科学结论，「计数一致」不是推导，「同构（T2）」不是验证——引用时保持分级；
5. **发现疑似个人内容或泄露**：不要传播，告知作者（本库 Issues 或联系通道）。

## 七、术语速查（没跟过项目的看这里）

| 术语 | 人话 |
|---|---|
| 体系 | 云韶科学体系——知世构建的数学框架（36维周期、零维代理等） |
| 内部版 | 九册体系正本（几何/代数/拓扑/数论/概率/群论/范畴/调和/非交换几何），标注「绝密·内部版」但已获作者批准公开（公开层为脱敏删减版） |
| 严格 HP | 哈密顿路径：图上一条「每个点恰好走一次、每一步走的边真实存在」的路 |
| 广义 walk | 全覆盖走行：每个点都走到、每步真边，但允许重复经过（与严格HP分账，永不混写） |
| 三关甲 | 独立验证三条件：路径长度=节点数 ∧ 无重复 ∧ 全真边 |
| 状态标签 | 库内每个断言的可信度标注：【已确认】＞【复算一致】＞【内部定义】＞【推演值】＞【未验证】 |
| T1/T2/T3 | 与主流文献的对接分级：T1=教科书级可直接引用，T2=结构同构待严格化，T3=联想级禁入推导链 |
| commit 号 | 每次库更新的版本指纹（SHA 前10位），引用带它=可复现 |

---

*本指南由主持会话（ZCode）编写并入库。指南本身随库更新——发现过时请以库内最新版为准。*
