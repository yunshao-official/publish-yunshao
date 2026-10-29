# -*- coding: utf-8 -*-
"""
AI保密白皮书 v1.2 前置件·实测图表生成管线（2026-09-21，ZCode）
任务来源：任务二续跑第 4 轮主格③——白皮书 v1.2 前置（D11-12 实测图表的准备件：只做图表生成管线与空表，
不虚构数据；数据未至的表留空并标注待回填卡号）。
输入（自动探测，存在才读）：
  D2  H:/理论存档/01-数学/02-实验与数据/AI保密冲刺D2/冲刺D2测试集与首轮读数-20260921.json
  D5  H:/理论存档/01-数学/02-实验与数据/AI保密冲刺D5/*自检*.json        （D5 后存在）
  D9/D10 H:/理论存档/01-数学/02-实验与数据/AI保密冲刺D8-10/*.json      （D9/D10 后存在）
  D7  H:/理论存档/01-数学/02-实验与数据/AI保密冲刺D4-7/闭环*.json      （D7 后存在）
合成基线（引用在档数字，不新造）：四模块演示 v0 运行记录 2026-09-19——M2 三案例匹配度 0.643/0.405/0.0。
输出：白皮书 v1.2 §4.2"合成+真实双栏"实测图表 markdown 生成稿（数据字段要么在档、要么留空标注，零虚构）。
纪律：全脱敏口径（只出统计数字，不出任何语料原文）；外发闸门不动（本稿为内部准备件）。
"""
import io, json, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D2 = Path("H:/理论存档/01-数学/02-实验与数据/AI保密冲刺D2/冲刺D2测试集与首轮读数-20260921.json")
D5_DIR = Path("H:/理论存档/01-数学/02-实验与数据/AI保密冲刺D5")
D810_DIR = Path("H:/理论存档/01-数学/02-实验与数据/AI保密冲刺D8-10")
D47_DIR = Path("H:/理论存档/01-数学/02-实验与数据/AI保密冲刺D4-7")
OUT = Path("H:/理论存档/01-数学/02-实验与数据/AI保密冲刺D11-12/白皮书v1.2§4.2实测图表-生成稿-20260921.md")
BLANK = "（待回填）"

def fmt(x, pct=False):
    if x is None:
        return BLANK
    return f"{x:.2%}" if pct else str(x)

def main():
    lines = []
    lines.append("## 4.2 四模块原型实测（合成→真实·双栏，图表生成稿）")
    lines.append("")
    lines.append("> 本节由《AI保密白皮书图表管线-20260921.py》从冲刺各卡结果 JSON 自动生成；")
    lines.append("> 数据字段只允许两种状态：在档实测数字 / 留空待回填（标注卡号）——零虚构。")
    lines.append("")

    # ---- 模块一：输出统一审计账（M2）——D2 真实读数已至 ----
    lines.append("### 表 4-1 输出统一审计账：归因读数（合成基线 vs 真实语料首轮）")
    lines.append("")
    lines.append("| 读数 | 合成基线（演示 v0，2026-09-19） | 真实语料首轮（D2，2026-09-21） |")
    lines.append("|---|---|---|")
    if D2.exists():
        d = json.loads(D2.read_text(encoding="utf-8"))
        thrmap = {0.3: "0.3", 0.5: "0.5", 0.7: "0.7"}
        a, b = d["run_A"], d["run_B"]
        na, nb = len(a), len(b)
        for thr in (0.3, 0.5, 0.7):
            agree = sum(1 for r in a if r[f"v@{thr}"] == "无源涌现") / na
            block = sum(1 for r in b if r[f"v@{thr}"] != "来源支付成立") / nb
            lines.append(f"| 构造一致率（thr={thrmap[thr]}） | {BLANK}<sup>注1</sup> | {fmt(agree, True)}（{sum(1 for r in a if r[f'v@{thr}'] == '无源涌现')}/{na}） |")
            lines.append(f"| 误拦率（thr={thrmap[thr]}） | —（无此读数形态） | {fmt(block, True)}（{sum(1 for r in b if r[f'v@{thr}'] != '来源支付成立')}/{nb}） |")
        lines.append("")
        lines.append(f"<sup>注1</sup> 合成基线为三案例功能演示（匹配度 0.643/0.405/0.0，运行记录 2026-09-19 在档），无一致率读数形态——留空；"
                     f"真实读数为**构造一致率**（机器判 vs '未入包'构造预期），人工复核一致率待 D3；D2 只采数不定标，通过线 D14 裁定。")
        lines.append("")
    else:
        lines.append("| 构造一致率 | " + BLANK + " | " + BLANK + "（待 D2） |")
        lines.append("| 误拦率 | " + BLANK + " | " + BLANK + "（待 D2） |")
        lines.append("")

    # ---- 模块二：金丝雀 144 副本（D5）——空表 ----
    lines.append("### 表 4-2 金丝雀派生验证：144 副本四项全检（M1-r：144/144 全 PASS）")
    lines.append("")
    lines.append("| 检验项 | 合成基线（64 副本） | 真实首测（D5，144 副本） |")
    lines.append("|---|---|---|")
    lines.append("| 构造性质（素性/族一致/N 一致） | PASS（64/64） | " + BLANK + "（待 D5） |")
    lines.append("| 全局唯一性 | PASS（64/64） | " + BLANK + "（待 D5） |")
    lines.append("| 持表复核 | PASS（64/64） | " + BLANK + "（待 D5） |")
    lines.append("| 公开签名一致 | PASS（64/64） | " + BLANK + "（待 D5） |")
    lines.append("")

    # ---- 模块三：查询分布签名（D9/D10）——空表 ----
    lines.append("### 表 4-3 查询分布签名：误报率与踩点检出首测")
    lines.append("")
    lines.append("| 读数 | 合成基线（演示 v0） | 真实日志首测（D9/D10） |")
    lines.append("|---|---|---|")
    lines.append("| 正常流误报率（JC-B2-r<3%） | 通过（χ² 合成流） | " + BLANK + "（待 D9/D10） |")
    lines.append("| 踩点序列检出（JC-B1-r 全检出） | 检出（掺入即告警） | " + BLANK + "（待 D9） |")
    lines.append("| 阈值双向标定（JC-B3-r 蓝队半场） | — | " + BLANK + "（待 D10） |")
    lines.append("")

    # ---- 模块四：分发-归因闭环（D7）——空表 ----
    lines.append("### 表 4-4 分发-归因闭环：无人干预全链路演示（闭环-r）")
    lines.append("")
    lines.append("| 环节 | 状态 |")
    lines.append("|---|---|")
    lines.append("| 金丝雀分发→含密输出→支付账归因→溯源回表 | " + BLANK + "（待 D6/D7 联调与彩排） |")
    lines.append("")

    lines.append("### 脱敏口径复核清单（D11-12 逐句复核用，预置）")
    lines.append("")
    lines.append("- [ ] 真名零出现；- [ ] 绝对路径零出现；- [ ] 内部专名（项目号/人员代号）零出现；- [ ] 凭证/令牌零出现；- [ ] 图表数字全部可溯源到在档结果 JSON。")
    lines.append("")
    lines.append("> 外发闸门不动：本表进入白皮书 v1.2 草稿（内部审阅用）；外发递送永远知世亲裁。")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] 生成稿已写入：{OUT}")
    print("[state] D2 数据块=真实读数已填；D5/D9/D10/D6-7 块=空表待回填（零虚构）。")

if __name__ == "__main__":
    main()
