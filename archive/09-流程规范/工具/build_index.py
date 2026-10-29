# -*- coding: utf-8 -*-
# 执行器层·主流软件工程·纯stdlib·禁API
"""
build_index.py — 再生 00-其他/启动包-最新.md（工具4）
====================================================
做什么：
  1) 读旧 启动包-最新.md，正则提取「活跃任务」与「纪律提醒」两节原文
     （缺失则用脚本内置默认——与 2026-09-16 手工版等价）；
  2) 旧文件先备份为 启动包-最新.backup-20260916.md（已存在则不覆盖）；
  3) 重建其余部分：
     - 必读三件（constants.yaml / 月度回顾 / P0裁决执行记录，glob 定位实际路径）；
     - 体系常数速览（从 constants.yaml 解析关键字段生成）；
     - 各域规模表（每域 md 文件数 + 二级分布；排除只读区）；
  4) 打印新旧 diff 摘要，并写 build_index报告-20260916.md。
用法：python build_index.py
"""
import os
import re
import sys
import glob
import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"H:\理论存档"
LAUNCH = os.path.join(ROOT, "00-其他", "启动包-最新.md")
BACKUP = os.path.join(ROOT, "00-其他", "启动包-最新.backup-20260916.md")
CONSTANTS_YAML = os.path.join(ROOT, "00-其他", "constants.yaml")
REPORT_DIR = os.path.join(ROOT, "09-流程规范", "工具报告")
REPORT_PATH = os.path.join(REPORT_DIR, "build_index报告-20260916.md")

READONLY_DIRS = {
    "_归档-已整合-20260726", "backup_20260725", "backup_20260726_pre-attack",
    "归档-旧常数体系-20260731", "云韶备份",
}
SECONDARY_ORDER = ["00-正本", "01-理论与推导", "02-实验与数据",
                   "03-论文与对外", "04-工具与代码", "05-索引", "09-归档"]

DEFAULT_ACTIVE = """## 4. 活跃任务（知世口令即开跑）
- 计算清单八项（见裁决执行记录第四节）：ys_9d Tc 公式b重算 / m=5@10⁵ / 猜想C / W-n / λ₂复核 / T14 η / 2390K 底层重估 / N=2 定义域
- M1 已完成（constants.yaml+启动包+ADR）；M2（03/04 摘要头+索引再生+对外件再版+32份符号修订+OpenClaw 纳入整治）；M3（全库+归档卫生）
- 待签：待签清单第一档剩余项（R23 送检批款等）"""

DEFAULT_DISCIPLINE = """## 5. 纪律提醒
- 体系知识第一计算口径；执行层与机制层分开；判据先冻结；不编数值；先查蜃楼/砥柱/燧人/夸父/SGC 继承闸门
- 知世口令映射：条目名=八件套；"月度回顾"=月度盘点；"都试试"=并行；"论文"/"人话"=对应件加急
- 禁止 API 调用；重负载交 ZCode 子代理（夜间免费窗口）；子代理一次只跑一个（并发>1 会限流）"""


def read_text(path):
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def extract_section(text, title_kw):
    """提取「## n. …标题词…」整节（到下一个 ## 或文末）。缺失返回 None。"""
    m = re.search(r"(?ms)^##\s*[^\n]*%s[^\n]*\n(.*?)(?=^##\s|\Z)" % title_kw, text)
    if not m:
        return None
    body = m.group(0).rstrip() + "\n"
    return body


def locate_must_read():
    """glob 定位必读三件实际路径。"""
    consts = CONSTANTS_YAML if os.path.isfile(CONSTANTS_YAML) else None
    monthly = None
    cands = sorted(glob.glob(os.path.join(ROOT, "00-其他", "月度回顾-*", "*月度回顾*总索引*.md")))
    if not cands:
        cands = sorted(glob.glob(os.path.join(ROOT, "00-其他", "月度回顾-*", "*.md")))
    if cands:
        monthly = cands[0]
    p0 = None
    cands = sorted(glob.glob(os.path.join(ROOT, "10-治理与哲学", "**", "P0裁决执行记录*.md"), recursive=True))
    if cands:
        p0 = cands[0]
    return consts, monthly, p0


def parse_constants_brief():
    """从 constants.yaml 提取速览所需键（stdlib 行解析·缩进栈嵌套）。
    生成键名示例：layer1_write_phase_space.alpha_w / sigma.sigma_projection /
    tc_formula.canonical / frequency.f0 / cold_evidence.r_minus / meta.version"""
    out = {}
    try:
        text = read_text(CONSTANTS_YAML)
    except OSError:
        return out
    stack = {0: ""}   # 缩进 -> 前缀
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        s = line.strip()
        m = re.match(r'^([A-Za-z_0-9]+):\s*"?([^"#]*?)"?\s*(?:#.*)?$', s)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        parent = ""
        for ind in sorted(stack):
            if ind < indent:
                parent = stack[ind]
        full = (parent + "." + key) if parent else key
        if indent == 0 and key == "version":
            out["meta.version"] = val
            continue
        if val == "":
            stack[indent] = full        # 子 section
        else:
            out[full] = val             # 叶子键值
    return out


def domain_stats():
    """每域 md 总数 + 二级分布（递归计二级目录内 md；域根散文件单列）。"""
    stats = []
    for name in sorted(os.listdir(ROOT)):
        dom = os.path.join(ROOT, name)
        if not (re.match(r"^\d{2}-", name) and os.path.isdir(dom)):
            continue
        total = 0
        dist = []
        root_scatter = 0
        for sub in sorted(os.listdir(dom)):
            subp = os.path.join(dom, sub)
            if not os.path.isdir(subp):
                if sub.lower().endswith(".md"):
                    root_scatter += 1
                    total += 1
                continue
            if sub in READONLY_DIRS:
                continue
            n = 0
            for dp, dns, fns in os.walk(subp):
                dns[:] = [d for d in dns if d not in READONLY_DIRS]
                n += sum(1 for fn in fns if fn.lower().endswith(".md"))
            total += n
            tag = sub if sub in SECONDARY_ORDER else sub + "※"
            dist.append("%s:%d" % (tag, n))
        if root_scatter:
            dist.append("根散:%d" % root_scatter)
        stats.append((name, total, "｜".join(dist)))
    return stats


def build_new(old_text):
    ver = "1.0"
    kv = parse_constants_brief()
    v = lambda k, d="-": kv.get(k, d) or d
    consts, monthly, p0 = locate_must_read()
    def rp(p):
        # 必读三件沿用旧版绝对路径风格，便于直接打开
        return p.replace("/", "\\") if p else "（未定位到）"

    # 保留节
    sec_active = extract_section(old_text, "活跃任务") if old_text else None
    sec_disc = extract_section(old_text, "纪律提醒") if old_text else None
    kept_active_src = "旧文件原文" if sec_active else "内置默认（旧文件缺失该节）"
    kept_disc_src = "旧文件原文" if sec_disc else "内置默认（旧文件缺失该节）"
    sec_active = sec_active or (DEFAULT_ACTIVE + "\n")
    sec_disc = sec_disc or (DEFAULT_DISCIPLINE + "\n")

    now = datetime.date.today().isoformat()
    L = []
    L.append("# 启动包-最新（AI 会话入口，≤8k tokens）")
    L.append("")
    L.append("> 再生规则：本文件由 build_index.py 再生（v%s，%s）。" % (ver, now))
    L.append("> 任何 AI 会话先读本件，再按需进正文。常数细节以 constants.yaml 为准。")
    L.append("")
    L.append("## 1. 必读三件")
    L.append("- 常数正本：`%s`（v%s，引用格式 [constants:v%s]）" % (
        consts or "（未定位到）", v("meta.version", "1.0"), v("meta.version", "1.0")))
    L.append("- 月度总索引：`%s`（+同目录附录 A/B/C）" % rp(monthly))
    L.append("- 裁决记录：`%s`（九条已裁决）+ 同目录《知世待签署与待拍板总清单》（待签项唯一入口）" % rp(p0))
    L.append("")
    L.append("## 2. 体系常数速览（细节以 constants.yaml 为准，勿从本文抄数）")
    L.append("- 双层制：层1 写入相空间 Θ(%s)：α_w=%s（唯一自由参数）、η=%s、κ=%s、ε=%s、M=%s；"
             "层2 材料本体 Θ(%s)：α_m=%s、d_m=%s、M=%s；无限方向 α:=1/N（0906裁决）" % (
                 v("layers.layer1_write_phase_space.theta"), v("layers.layer1_write_phase_space.alpha_w"),
                 v("layers.layer1_write_phase_space.eta"), v("layers.layer1_write_phase_space.kappa"),
                 v("layers.layer1_write_phase_space.epsilon"), v("layers.layer1_write_phase_space.M"),
                 v("layers.layer2_material_body.theta"), v("layers.layer2_material_body.alpha_m"),
                 v("layers.layer2_material_body.d_m"), v("layers.layer2_material_body.M")))
    L.append("- σ 独立于 α：σ_投影=%s、σ_终=%s、%s；\"α²=σ²\"已作废" % (
        v("sigma.sigma_projection"), v("sigma.sigma_final"), v("sigma.identity")))
    L.append("- Tc 正本公式=%s；%s（公式a）已判负" % (
        v("tc_formula.canonical"), v("tc_formula.deprecated")))
    L.append("- 频率正本 f₀=%s（%s；%s）；800THz 过时" % (
        v("frequency.f0"), v("frequency.f1"), v("frequency.f2")))
    L.append("- 冷证据：%s；%s" % (
        v("cold_evidence.r_minus"), v("cold_evidence.metric_field")))
    L.append("- 状态标签强制：体系内部定义·未验证 / 复算一致 / 已判负 / 已封存 等，引用数值必带标签")
    L.append("")
    L.append("## 3. 全库规模（%s 再生，md 计数；只读区不计）" % now)
    L.append("")
    L.append("| 域 | md 数 | 二级分布（※=非标二级目录） |")
    L.append("|---|---|---|")
    tot = 0
    for name, n, dist in domain_stats():
        tot += n
        L.append("| %s | %d | %s |" % (name, n, dist.replace("|", "\\|")))
    L.append("| **合计（18 域）** | **%d** |  |" % tot)
    L.append("")
    L.append(sec_active.rstrip())
    L.append("")
    L.append(sec_disc.rstrip())
    L.append("")
    L.append("---")
    L.append("> 标签：执行器层·主流软件工程（本件为索引再生件；所引体系数值")
    L.append("> 均转抄自 constants.yaml v%s，口径「体系内部定义·未验证」）。" % v("meta.version", "1.0"))

    meta = {"kept_active_src": kept_active_src, "kept_disc_src": kept_disc_src,
            "monthly": rp(monthly), "p0": rp(p0), "total_md": tot}
    return "\n".join(L) + "\n", meta


def main():
    old_text = ""
    if os.path.isfile(LAUNCH):
        old_text = read_text(LAUNCH)
    # 备份
    backup_done = False
    if old_text and not os.path.exists(BACKUP):
        with open(BACKUP, "w", encoding="utf-8", newline="") as f:
            f.write(old_text)
        backup_done = True

    new_text, meta = build_new(old_text)
    with open(LAUNCH, "w", encoding="utf-8", newline="") as f:
        f.write(new_text)

    # diff 摘要
    def n_chars(t):
        return len(re.sub(r"\s+", "", t))
    old_lines = old_text.count("\n") + (1 if old_text and not old_text.endswith("\n") else 0)
    new_lines = new_text.count("\n")
    # 累计口径：相对首跑前手工版（=备份件）
    orig_text = read_text(BACKUP) if os.path.exists(BACKUP) else old_text
    orig_lines = orig_text.count("\n") + (1 if orig_text and not orig_text.endswith("\n") else 0)
    print("=== build_index.py 完成 ===")
    print("备份: %s（%s）" % (os.path.relpath(BACKUP, ROOT),
                             "新建" if backup_done else "已存在·未覆盖" if os.path.exists(BACKUP) else "旧文件缺失·未备份"))
    print("diff 摘要（本次）: 行数 %d -> %d ｜ 有效字符 %d -> %d" % (
        old_lines, new_lines, n_chars(old_text), n_chars(new_text)))
    if orig_text is not old_text:
        print("diff 摘要（累计，相对首跑前手工版备份）: 行数 %d -> %d ｜ 有效字符 %d -> %d" % (
            orig_lines, new_lines, n_chars(orig_text), n_chars(new_text)))
    print("保留节来源: 活跃任务=%s ｜ 纪律提醒=%s" % (
        meta["kept_active_src"], meta["kept_disc_src"]))
    print("必读三件定位: 月度=%s ｜ P0=%s" % (meta["monthly"], meta["p0"]))
    print("全库 md 总数（18域，只读区不计）: %d" % meta["total_md"])

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    L = []
    L.append("# build_index报告-20260916（工具4 build_index.py 首跑）")
    L.append("")
    L.append("> 执行器层·主流软件工程·纯stdlib·禁API  ")
    L.append("> 运行时间：%s" % now)
    L.append("")
    L.append("## 1. 备份")
    L.append("")
    L.append("- 旧件备份：`00-其他/启动包-最新.backup-20260916.md`（%s）" % (
        "本次新建" if backup_done else "已存在，未覆盖（首跑备份保留）"))
    L.append("")
    L.append("## 2. 再生前 → 后 diff 摘要")
    L.append("")
    L.append("| 指标 | 旧（本次再生前） | 新 |")
    L.append("|---|---|---|")
    L.append("| 行数 | %d | %d |" % (old_lines, new_lines))
    L.append("| 有效字符（去空白） | %d | %d |" % (n_chars(old_text), n_chars(new_text)))
    L.append("")
    L.append("累计口径（相对首跑前手工版备份 启动包-最新.backup-20260916.md，")
    L.append("%d 行 / %d 有效字符）：本次再生后为 %d 行 / %d 有效字符。" % (
        orig_lines, n_chars(orig_text), new_lines, n_chars(new_text)))
    L.append("")
    L.append("- 保留节：「活跃任务」=%s；「纪律提醒」=%s" % (
        meta["kept_active_src"], meta["kept_disc_src"]))
    L.append("- 再生节：必读三件 / 体系常数速览（自 constants.yaml v%s 解析）/ 全库规模表" % "1.0")
    L.append("- 必读三件定位：月度回顾=%s；P0裁决=%s" % (meta["monthly"], meta["p0"]))
    L.append("- 全库 md 总数（18 域、排除只读区）：%d" % meta["total_md"])
    L.append("")
    L.append("## 3. 说明")
    L.append("")
    L.append("- 旧件为 v1.0 手工版（32 行）；新件由脚本再生，此后改库后重跑")
    L.append("  `python build_index.py` 即可刷新必读路径与规模表。")
    L.append("- 「活跃任务/纪律提醒」以人工维护为准，脚本只透传不生成内容")
    L.append("  （旧件缺失该节时才落内置默认）。")
    L.append("")
    L.append("---")
    L.append("标签：执行器层·主流软件工程（索引再生件；体系数值转抄自")
    L.append("constants.yaml v1.0，口径「体系内部定义·未验证」）。")

    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("报告: %s" % REPORT_PATH)


if __name__ == "__main__":
    main()
