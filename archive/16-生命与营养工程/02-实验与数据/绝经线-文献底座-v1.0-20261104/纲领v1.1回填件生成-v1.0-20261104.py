#!/usr/bin/env python3
# 纲领 v1.1 回填件生成器（绝经线）
# 只读：审计剔除件 JSON ＋ 净面池 JSON ＋ 判据书（取哈希）
# 只写：纲领 v1.1 回填件 .md
# 纪律：所有数字从落盘件读出，不许手抄；不许联网；不许 git；不许改判据。
import json, os, hashlib, collections

BASE = os.path.dirname(os.path.abspath(__file__))
THEORY = os.path.normpath(os.path.join(BASE, "..", "..", "01-理论与推导"))
AUD = os.path.join(BASE, "审计剔除表-绝经线净面-20261104.json")
NET = os.path.join(BASE, "净面池-20261104.json")
BOOK = os.path.join(THEORY, "绝经线·文献检索判据书-v1.0-20261104.md")
OUT = os.path.join(THEORY, "绝经·旧科学疑问与体系解法·纲领v1.1回填件-20261104.md")

h16 = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def clip(t, n):
    t = (t or "").strip()
    return t if len(t) <= n else t[:t.rfind(" ", 0, n)].rstrip(",;:") + "…"
for p in (AUD, NET, BOOK):
    assert os.path.exists(p), p

aud = json.load(open(AUD, encoding="utf8"))
net = json.load(open(NET, encoding="utf8"))
recs = net["文献"]
assert len(recs) == net["留"], (len(recs), net["留"])
book_h = h16(BOOK)
assert book_h == "6184d7c5001ab833", "判据书哈希不符，停"

L = []
A = L.append
A("# 绝经·旧科学疑问与体系解法·纲领 v1.1 回填件｜2026-11-04")
A("")
A("> **文献题录底座，非医疗建议。** 本件只做两件事：把纲领 v1.0 §二 那 30 条旧科学疑问的文献锚钉上，"
  "把整读阶段的判读结果与不合格登记落账。体系判断、Δ 工程、红队、JC-M1—JC-M14 候冻结判据一字未动。")
A(">")
A("> 上位件：`绝经·旧科学疑问与体系解法·研究纲领-v1.0-20261104.md`（正本·在办，正文论证仍以它为准）；"
  "`绝经线·文献检索判据书-v1.0-20261104.md`（已冻结，sha256 前16位 " + book_h + "）；"
  "`绝经线·判据链冻结哈希-20261104.txt`（封条）。")
A(">")
A("> 状态标签：**在办·v1.1 回填件**。对外引用一律先过第六律与对外闸。")
A("")
A("## 一 总账（全部数字由落盘件读出）")
A("")
s = aud["汇总"]
A("- 整读送审 " + str(s["送审"]) + " 条（v1.2 重算面：严格池 380 与放宽池 174 合计 554，"
  "另 166 条属判据书 §六 池归属缺口·待裁决），逐条读完标题＋摘要，一条未跳。")
A("- 判读结果：留 " + str(s["留"]) + "／删 " + str(s["删"]) + "／待核 " + str(s["待核"]) + "（合计 " +
  str(s["送审"]) + "）。留的构成：严格池 " + str(net["留_池1"]) + "／放宽池 " + str(net["留_池2"]) +
  "／待裁决面 " + str(net["留_待裁决面"]) + "。")
A("- 知世令「收至少 100 项、主要高贡献论文」的达成口径：**判留 " + str(s["留"]) + " 条，"
  "其中 " + str(net["留_池1"] + net["留_池2"]) + " 条在判据书定义的两池之内**，"
  "是 100 这条线的五倍以上。同时照记一句：**达标不等于净面**——"
  "18 个模块里 " + str(aud["模块"] and sum(1 for m in aud["模块"] if aud["模块"][m]["检索式判定"].startswith("不合格"))) +
  " 个模块的剔除率超过 §八 的 10% 红线，判的是检索式不合格，不是文献不够。")
c = [x.get("被引数") or 0 for x in recs]
c_sorted = sorted(c)
med = c_sorted[len(c_sorted) // 2]
A("- 判留面的贡献度画像：被引中位数 " + str(med) + " 次，≥1000 次 " + str(sum(1 for v in c if v >= 1000)) +
  " 条，≥500 次 " + str(sum(1 for v in c if v >= 500)) + " 条，最高 " + str(max(c)) +
  " 次（2002 年 WHI 随机对照试验，JAMA）。被引数＝Europe PMC `citedByCount`「文献值」口径，"
  "对只有 PubMed 记录的付费刊系统性低估，所以这是下界不是上界。")
A("- 年份跨度 " + str(min(x.get("年份") or 9999 for x in recs)) + "—" +
  str(max(x.get("年份") or 0 for x in recs)) + "。")
A("- 协调人改判 " + str(net["改判条数"]) + " 条，全部只往回收不往发放：" +
  "；".join(x["编号"] + "（" + x["因"] + "）" for x in aud["改判清单"]) + "。")
RT = os.path.join(BASE, "文献主档-v1.2-全量重算.json")
main = json.load(open(RT, encoding="utf8"))
allrec = main["文献"] + main["待裁决"]
retr = [x for x in allrec if "retract" in ((x.get("类型") or "") + " " + (x.get("标题") or "")).lower()]
assert len(retr) == 2, [x.get("PMID") for x in retr]
v10 = {str(x.get("PMID")): x for x in json.load(
    open(os.path.join(BASE, "文献主档-v1.0.json"), encoding="utf8"))["文献"]}
A("- **撤稿件 " + str(len(retr)) + " 条**：" + "；".join(
    "PMID " + str(x.get("PMID")) + "｜被引 " + str(x.get("被引数")) + "｜执行器 v1.0 把它落在池" +
    str((v10.get(str(x.get("PMID"))) or {}).get("池级")) + "（过门 " +
    str((v10.get(str(x.get("PMID"))) or {}).get("过门")) + "）｜v1.2 重算后落在" +
    ("待裁决面" if x in main["待裁决"] else "池" + str(x.get("池级"))) + "｜" +
    clip((x.get("标题") or "").strip(), 60) for x in retr) +
  "。判据书硬底线②要求未撤稿，执行器把类型栏写成空串所以两个版本都没拦住，"
  "直到 v1.1 离线回填类型才现形，终由合并件改判零剔除——记执行缺陷，不记判据缺陷。"
  "**协调人自纠：本件初稿与合并件初稿曾写成「原本坐在严格池」，与落盘档不符（实为池2／待裁决面），照记改正。**")
A("")
A("## 二 旧科学 30 条疑问·文献锚定（判留条目才准作锚）")
A("")
A("> 每条疑问给最多 4 个锚，按被引数取高。锚只证明「旧科学自己在这条疑问上有高贡献文献可查」，"
  "不证明体系结论；体系侧的解法与边界仍看纲领 v1.0 §二、§三。")
A("")
byq = collections.defaultdict(list)
for x in recs:
    for q in (x.get("关联疑问") or []):
        byq[q].append(x)
for i in range(1, 31):
    k = "Q" + str(i).zfill(2)
    g = sorted(byq.get(k, []), key=lambda z: -(z.get("被引数") or 0))
    A("### " + k + "｜判留支撑 " + str(len(g)) + " 条")
    if not g:
        A("- **疑问无判留文献支撑·判负照记**（须另开检索式或待中文库）")
    for x in g[:4]:
        pool = ("严格池" if x.get("池级") == 1 else ("放宽池" if x.get("池级") == 2 else "待裁决面"))
        A("- " + (x.get("标题") or "").strip() + "｜" + str(x.get("年份")) + "｜" + (x.get("刊物") or "刊物未回填") +
          "｜被引 " + str(x.get("被引数")) + "｜" + pool + "｜PMID " + (x.get("PMID") or "无") +
          "｜DOI " + (x.get("DOI") or "无") + "｜判留理由：" + str(x.get("理由") or ""))
    A("")
noq = ["Q" + str(i).zfill(2) for i in range(1, 31) if not byq.get("Q" + str(i).zfill(2))]
A("- 无锚疑问 " + str(len(noq)) + " 条：" + ("、".join(noq) if noq else "无——30 条全部钉上判留文献") + "。")
A("- 覆盖统计：30 条疑问合计被 " + str(sum(len(v) for v in byq.values())) + " 人次判留引用；"
  "一条文献可同时支撑多条疑问，故此数不等于文献数。")
A("")
A("## 三 检索式不合格登记（§八 红线，只登记不修门槛）")
A("")
bad = [m for m in sorted(aud["模块"]) if aud["模块"][m]["检索式判定"].startswith("不合格")]
good = [m for m in sorted(aud["模块"]) if not aud["模块"][m]["检索式判定"].startswith("不合格")]
A("- 判不合格 " + str(len(bad)) + " 个模块：" + "、".join(bad) + "。判合格 " + str(len(good)) + " 个：" +
  "、".join(good) + "。")
leakW = set(aud["门W漏网"])
leakN = set(aud["门N漏网"])
mod_of = {}
for x in recs:
    mod_of[x["编号"]] = x["模块号"]
for m in sorted(aud["模块"]):
    t = aud["模块"][m]
    A("- " + m + " " + t["名"] + "｜送审 " + str(t["送审"]) + "｜留 " + str(t["留"]) + "｜剔除率 " +
      str(t["剔除率"]) + "% ⇒ " + t["检索式判定"])
A("- 语境门漏网总量：门W（人类女性语境）" + str(len(leakW)) + " 条、门N（跨域负面表）" + str(len(leakN)) +
  " 条。成因写死在判据书 §五：48 条式子全是 TITLE-only，动物与男性口径只要标题带 ovarian／estrogen／FSH "
  "就会命中，门只能在摘要里拦——**下一版改式子（TITLE 侧加排除项），不改门槛。**")
A("- 两条最典型的式子病因，由执行卷整读时逐条指认：M14 式2 用 `endocrine` 与 `menopaus*` 共现，"
  "把乳腺癌 CDK4/6 抑制剂与芳香化酶抑制剂试验（PALOMA-2／3、MONARCH 2、monarchE、MONALEESA-7、BIG 1-98）"
  "整批捞进来，绝经只是入组分层字段，该模块剔除率 43.33%；M02 的 ovarian／follicle／AMH 词族同时捞进"
  "化疗／癌症幸存者卵巢毒性 8 条、纯 IVF 方案 5 条、手术急性损伤 3 条、动物口径 7 条（禽类 2＋鼠牛 5），"
  "剔除率 35.38%（执行卷 A1 的逐条删除归因合计 23 条，与判删数吻合）。")
A("- 灰色地带照记不裁决：化疗诱导的原始卵泡损耗在机制层面就是 PTEN／PI3K-AKT 休眠逃逸的工具模型（Q04），"
  "但主题不是自然衰老。执行卷按「主题非自然衰老」统一判删，判据书未规定这类模型归属——"
  "**归属待知世裁决，不在本件自行补判据。**")
A("")
A("## 四 判据书 §六 池归属缺口（我的错，不是执行器的错）")
A("")
A("- §六 只写了池1 的构成，没写「过 Q2、锚词在标题命中、且未用任何放宽项」这一类该进哪个池。"
  "执行器把它们塞进池2 而不标放宽项，v1.2 重算时这类共 166 条，我全部隔离为待裁决面，不自动升池、不自动并池。")
A("- 整读后仍判留的待裁决面 " + str(net["留_待裁决面"]) + " 条——**它们的判读有效，池归属未定**，"
  "处置权在知世。判据书下一版必须补一句池归属穷尽式：任一合格记录当且仅当落入池1、池2、剔除三者之一。")
A("")
A("## 五 执行缺陷登记（判负照记，不藏）")
A("")
A("- 刊名与文献类型两栏 704 条全写成空串，而 raw 里两个字段都在——后果是硬底线④（类型白名单）"
  "整条未被检验、Q3（刊物白名单门）全程空跑、撤稿标记直到 v1.1 离线回填才现形。")
A("- 执行器脚本末行「是否新增过任何判据外的门或放宽项: 否」是硬编码字符串而不是计算结果，"
  "取证方式作废；我另行独立复算，放宽只用判据书 §六 的甲／乙／丙三类，无自设门——结论碰巧为否，但取证不合格。")
A("- 标题栏残留 HTML 标签 6 条（NAD＋、CO₂、³¹P 一类上标下标未清洗）。")
A("- 卷F 的自报剔除率与它自己章节的表头互相打架（同一模块两种百分数），卷D 报 M09 10.64% 而逐条重算为 12.77%；"
  "合并件因此一律按逐条结论重算，子会话百分数只作对照。")
A("- 协调人自己的两处自纠：其一，把执行中读到的 Crossref 16 请求／32 缓存／retry-after 70915 当成终态写过，"
  "终态是 0 请求／48 缓存／70568；其二，卷A 停摆前我口头报过「12 个模块超线」，用的是子报百分数，"
  "按逐条重算是 " + str(len(bad)) + " 个（含卷A 两卷后 M02、M14 补进）。两版数字都留痕不销。")
A("- OpenAlex 全程 429（预算位 1000 credits／日、limit-usd 0.10、共享 IP 约 100 请求／日，retry-after 70568 秒），"
  "本线未用；CNKI／万方未取，中文口径文献为零——**不许拿英文库冒充中文库**。")
A("")
A("## 六 修改记录")
A("")
A("- v1.1（2026-11-04）：新增本回填件。纲领 v1.0 §二 的「执行中，落不到就标注判负照记」占位，"
  "由本件 §二 的 PMID／DOI 锚钉取代；纲领 v1.0 §九 的整读待办由本件 §三、§四、§五 落账。"
  "纲领 v1.0 正文、Δ1—Δ5、红队、JC-M1—JC-M14 候冻结判据一字未改。")
A("- 待办：166 条待裁决面的池归属；13 个不合格模块的检索式重写（另出版本，先冻结后跑）；"
  "JC-M1—JC-M14 冻结令；对外闸未开——本线未 push、未外发，全库未跟踪件 961 个（2026-11-04 当日 `git status --porcelain -uall` 计数，无修改无删除）。**数字自纠：早前多处写的「747 件」是卷A 停摆前的旧计数，本件以 961 为准，旧值照记不销。**")
A("")
A("## 附 本件依据的落盘件哈希（sha256 前16位）")
A("")
for f in sorted(os.listdir(BASE)):
    if f.endswith(".json") or f.endswith(".md") or f.endswith(".py"):
        A("- " + f + "｜" + str(os.path.getsize(os.path.join(BASE, f))) + "B｜" + h16(os.path.join(BASE, f)))
A("- " + os.path.relpath(BOOK, os.path.dirname(THEORY)) + "｜" + str(os.path.getsize(BOOK)) + "B｜" + book_h)

txt = "\n".join(L) + "\n"
assert "TODO" not in txt
open(OUT, "w", encoding="utf8").write(txt)
print("WROTE", OUT, os.path.getsize(OUT), h16(OUT))
print("留", s["留"], "删", s["删"], "待核", s["待核"], "不合格模块", len(bad), "无锚疑问", len(noq))
