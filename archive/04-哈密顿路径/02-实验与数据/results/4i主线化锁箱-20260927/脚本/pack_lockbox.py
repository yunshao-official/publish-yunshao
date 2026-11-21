# -*- coding: utf-8 -*-
"""
pack_lockbox.py — 4i 专轮锁箱打包（任务书纪律 #3：全部原始数据+判读值+脚本落盘
H:/理论存档/04-哈密顿路径/02-实验与数据/results/（文件名带日期20260927），双副本+SHA256）
主副本 = results/4i主线化锁箱-20260927/
副副本 = results/4i主线化锁箱-20260927-副本2/（同内容双写）
SHA256 清单 = 包内 SHA256SUMS.txt
"""
import os, shutil, hashlib, io, json, glob, time

SRC_WS = r"H:\door1\grid_v6main_20261002"
LOCK = r"H:\理论存档\04-哈密顿路径\02-实验与数据\results\4i主线化锁箱-20260927"
LOCK2 = r"H:\理论存档\04-哈密顿路径\02-实验与数据\results\4i主线化锁箱-20260927-副本2"

# 收集清单：(源, 包内相对路径)
items = []
# 1) 门与网格原始数据：gate/jsonl/logs + grid jsonl/path/logs（逐文件保结构）
for sub in ("gate", "jsonl", "logs", "path"):
    for p in glob.glob(os.path.join(SRC_WS, sub, "*")):
        if os.path.isfile(p):
            items.append((p, os.path.join("原始数据", sub, os.path.basename(p))))
# 2) 结果账面与判读值
for f in ("v6main_results.jsonl", "grid_v6main_report.json",
          "run_v6main_master.log", "判定输出-merge_v6main-20260927.txt",
          "gate/mv1_judgment.json", "gate/mv1_master.log"):
    p = os.path.join(SRC_WS, f)
    if os.path.exists(p):
        items.append((p, os.path.join("判读值", os.path.basename(f))))
# 3) 脚本与正本源
for f in ("mv1_gate.py", "grid_v6main_runner.py", "merge_v6main.py", "patch_m1v2_v21.py", "pack_lockbox.py"):
    items.append((os.path.join(SRC_WS, f), os.path.join("脚本", f)))
items.append((r"H:\理论存档\04-哈密顿路径\04-工具与代码\v3_construction_nx_m1v2-v2.1-20261002.cpp",
              os.path.join("正本源", "v3_construction_nx_m1v2-v2.1-20261002.cpp")))
items.append((os.path.join(SRC_WS, "m1v2_v21_main.exe"), os.path.join("正本exe", "m1v2_v21_main.exe")))
# 4) 对照锚（v5 正式账 + gwin 正本 exe，供离线复核 M-V3/M-V1）
items.append((r"H:\door1\grid_v5_20260921\grid_v5_report.json", os.path.join("对照锚", "grid_v5_report.json")))
items.append((r"H:\door1\gpipeanat_20260920\m1v2gwin_v10.exe", os.path.join("对照锚", "m1v2gwin_v10.exe")))
# 5) 预注册正本（判据冻结本）
items.append((r"H:\理论存档\01-数学\02-实验与数据\预注册---b1主线化网格v6程序性确认轮-v1.0-20260921.md",
              os.path.join("判据正本", "预注册---b1主线化网格v6程序性确认轮-v1.0-20260921.md")))

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def write_pack(root):
    os.makedirs(root, exist_ok=True)
    lines = []
    for src, rel in items:
        dst = os.path.join(root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        lines.append(f"{sha256(dst)}  {rel}")
    with io.open(os.path.join(root, "SHA256SUMS.txt"), "w", encoding="utf-8") as f:
        f.write("# 4i --b1 主线化实现轮 锁箱 SHA256 清单（打包时间 %s）\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
        f.write("# 主副本与副本2 内容逐字节同；本清单对副本2 同样成立（各自重算）。\n")
        f.write("\n".join(sorted(lines)) + "\n")
    return len(items)

n1 = write_pack(LOCK)
n2 = write_pack(LOCK2)
print(f"packed items: main={n1} copy2={n2}")
print("LOCK :", LOCK)
print("LOCK2:", LOCK2)
