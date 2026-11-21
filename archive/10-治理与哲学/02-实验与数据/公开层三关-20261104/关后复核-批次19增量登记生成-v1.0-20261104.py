#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批次 19 增量登记生成器：把三关全套件按索引 house 格式追加到
indexes/02-全库文件总表-v1.0-20261027.md 末尾（§五）。

件数、字节、首行标识一律遍历实测，不手抄（沿用 §四 已声明的同一口径）。
自指缺陷当场写明：本段写盘前的全库实测值写进本段文字后，全库字节即再涨一拍，
精确值请以文末命令现算为准。
运行：python3 -B 关后复核-批次19增量登记生成-v1.0-20261104.py
"""
import os
import subprocess

ROOT = "/data/workspace/publish-yunshao"
TARGET = os.path.join(ROOT, "indexes", "02-全库文件总表-v1.0-20261104".replace("20261104", "20261027") + ".md")
QC = os.path.join(ROOT, "archive", "10-治理与哲学", "02-实验与数据", "公开层三关-20261104")
BASE = os.path.join(ROOT, "archive", "16-生命与营养工程", "02-实验与数据", "绝经线-文献底座-v1.0-20261104")

MODIFIED = [
    "README.md",
    "llms.txt",
    "indexes/02-全库文件总表-v1.0-20261027.md",
    "archive/16-生命与营养工程/05-索引/总纲索引-16-生命与营养工程-v1.0-20261104-补录.md",
    "archive/16-生命与营养工程/01-理论与推导/绝经线·判据链冻结哈希-20261104.txt",
    "archive/16-生命与营养工程/01-理论与推导/绝经·旧科学疑问与体系解法·纲领v1.1回填件-20261104.md",
    "archive/16-生命与营养工程/02-实验与数据/绝经线-文献底座-v1.0-20261104/整读初判-卷G-20261104.md",
    "archive/16-生命与营养工程/02-实验与数据/绝经线-文献底座-v1.0-20261104/整读初判-卷G-20261104.json",
]
REMOVED = ["archive/16-生命与营养工程/02-实验与数据/化学药物线-20261103/语料/__pycache__/检索脚本.cpython-312.pyc"]


def rel(p):
    return os.path.relpath(p, ROOT)


def firstline(p, n=56):
    with open(p, encoding="utf8", errors="replace") as fp:
        for ln in fp:
            ln = ln.strip()
            if ln:
                return ln.replace("|", "｜")[:n]
    return ""


def rows(paths):
    out = []
    for p in paths:
        out.append("| %s | %s | %s |" % (os.path.basename(p), format(os.path.getsize(p), ","), firstline(p)))
    return out


def total_bytes_tracked():
    ps = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"], capture_output=True).stdout.decode("utf8").split("\0")
    ps = [p for p in ps if p]
    n = 0
    for p in ps:
        fp = os.path.join(ROOT, p)
        if os.path.exists(fp):
            n += os.path.getsize(fp)
    return len(ps), n


qc_files = sorted(os.path.join(QC, f) for f in os.listdir(QC) if os.path.isfile(os.path.join(QC, f)))
base_files = [os.path.join(BASE, "初判抄录更正登记-绝经线-20261104.md")]
new_paths = qc_files + base_files
new_bytes = sum(os.path.getsize(p) for p in new_paths)
cnt, tbytes = total_bytes_tracked()

# 本段自身字节量先估：生成文本后再算一次，写在文内为"写盘前实测"，故此处不自我回填。
lines = []
lines.append("")
lines.append("## 五、批次 19 增量登记（2026-11-04·三关：检验—验算—攻防）")
lines.append("")
lines.append("> 触发令：作者 2026-11-04「全部检验，检验完成验算，验算完成攻防，然后就放上去」。")
lines.append("> 本段为**增量登记**，不覆盖上方 §一／§二／§三／§四——§一／§二 仍是批次 12（2026-11-03）实测 3,778 件口径，"
             "§三 是批次 13—15 增量 956 件口径，§四 是批次 18 增量 7 件口径。")
lines.append("> 本批入库新增 %d 件／%s 字节；改写既有件 %d 件；移出跟踪 1 件（Python 编译缓存，磁盘源件与源脚本未删）。"
             % (len(new_paths), format(new_bytes, ","), len(MODIFIED)))
lines.append("> 全库本段写盘前实测：**%d 件／%s 字节**（跟踪树全量实测，含本件自身；本段写完即再涨一拍，"
             "属批次 11 已登记的自指固有缺陷，精确值请以档案根 `find . -type f -not -path \"./.git/*\" -printf \"%%s\\n\" | paste -sd+ | bc` 现算为准）。"
             % (cnt, format(tbytes, ",")))
lines.append("> 三关判定与取证正文见 `archive/10-治理与哲学/02-实验与数据/公开层三关-20261104/三关总判-公开层-20261104.md`；"
             "绝经线判据链登记见 `archive/16-生命与营养工程/01-理论与推导/绝经线·判据链冻结哈希-20261104.txt` 第 [11] 节。")
lines.append("")
lines.append("### 10-治理与哲学（增量 %d 件／%s 字节）" % (
    len(qc_files), format(sum(os.path.getsize(p) for p in qc_files), ",")))
lines.append("")
lines.append("#### 02-实验与数据/公开层三关-20261104（%d 件）" % len(qc_files))
lines.append("")
lines.append("| 文件 | 字节 | 首行标识 |")
lines.append("|---|---|---|")
lines.extend(rows(qc_files))
lines.append("")
lines.append("### 16-生命与营养工程（增量 1 件／%s 字节）" % format(os.path.getsize(base_files[0]), ","))
lines.append("")
lines.append("#### 02-实验与数据/绝经线-文献底座-v1.0-20261104（1 件）" )
lines.append("")
lines.append("| 文件 | 字节 | 首行标识 |")
lines.append("|---|---|---|")
lines.extend(rows(base_files))
lines.append("")
lines.append("### 改写既有件（%d 件，登记现值字节）" % len(MODIFIED))
lines.append("")
lines.append("| 相对路径 | 字节 | 改写内容一句话 |")
lines.append("|---|---|---|")
WHY = {
    "README.md": "规模行改为批次 18 合流后实测并写明自指滞后差值成因",
    "llms.txt": "库存盘点行同步批次 18 与批次 19 口径，并加三关一行",
    "indexes/02-全库文件总表-v1.0-20261027.md": "§三 两行字节滞后改正＋追加本段 §五",
    "archive/16-生命与营养工程/05-索引/总纲索引-16-生命与营养工程-v1.0-20261104-补录.md": "三条滞后声明改正＋自指件登记口径新规＋§四 三关件登记",
    "archive/16-生命与营养工程/01-理论与推导/绝经线·判据链冻结哈希-20261104.txt": "检索器件滞后声明改正＋追加 [11] 三关登记",
    "archive/16-生命与营养工程/01-理论与推导/绝经·旧科学疑问与体系解法·纲领v1.1回填件-20261104.md": "尾部加溯源注记（清单段 1,128 字节为手工补录，脚本重跑不可复现）",
    "archive/16-生命与营养工程/02-实验与数据/绝经线-文献底座-v1.0-20261104/整读初判-卷G-20261104.md": "抬头加 G008 抄录更正注记一行",
    "archive/16-生命与营养工程/02-实验与数据/绝经线-文献底座-v1.0-20261104/整读初判-卷G-20261104.json": "顶层加\"更正登记\"一键（错误值保留不改写）",
}
for p in MODIFIED:
    lines.append("| %s | %s | %s |" % (p, format(os.path.getsize(os.path.join(ROOT, p)), ","), WHY[p]))
lines.append("")
lines.append("### 移出跟踪（1 件）")
lines.append("")
lines.append("| 相对路径 | 移出前字节 | 理由 |")
lines.append("|---|---|---|")
rm_abs = os.path.join(ROOT, REMOVED[0])
lines.append("| %s | %s | 编译缓存非资料；`.gitignore` 已含 `__pycache__/` 与 `*.pyc`，磁盘原件未删 |" % (
    REMOVED[0], format(os.path.getsize(rm_abs), ",") if os.path.exists(rm_abs) else "—"))
lines.append("")

text = "\n".join(lines) + "\n"
with open(TARGET, "a", encoding="utf8") as fp:
    fp.write(text)
print(text)
print("本段自身字节=%d 追加后全库字节=%d" % (len(text.encode("utf8")), tbytes + len(text.encode("utf8"))))
