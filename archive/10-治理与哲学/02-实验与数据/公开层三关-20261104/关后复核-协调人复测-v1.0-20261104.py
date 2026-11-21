#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""协调人复测（关后复核）：对三道闸门的结论做独立再测。

只读仓库；只在公开层登记件与线目录留一份结果文本，不改任何判留/判删数据。
判定口径（当场注释）：
  可达 —— 引用按"仓库根相对"或"所在文件目录相对"能解析到真实存在的跟踪文件；
  书写不规范 —— 字面路径不存在，但去掉目录后按文件名在全库能找到同名跟踪文件，
              即"文件在、写法不通"，属可修书写缺陷，不算内容缺失；
  真断链 —— 字面路径不存在且全库无同名文件，即指向一份不存在的东西。
运行：python3 -B 关后复核-协调人复测-v1.0-20261104.py
"""
import json
import os
import re
import subprocess
import sys
import collections

ROOT = "/data/workspace/publish-yunshao"
QC = os.path.join(ROOT, "archive", "10-治理与哲学", "02-实验与数据", "公开层三关-20261104")

tracked = subprocess.run(
    ["git", "-C", ROOT, "ls-files", "-z"], capture_output=True
).stdout.decode("utf8").split("\0")
tracked = [p for p in tracked if p]
tracked_set = set(tracked)
by_name = {}
for p in tracked:
    by_name.setdefault(os.path.basename(p), []).append(p)


def measure_files():
    total = 0
    sizes = []
    for p in tracked:
        fp = os.path.join(ROOT, p)
        if not os.path.exists(fp):
            continue
        n = os.path.getsize(fp)
        sizes.append((n, p))
        total += n
    sizes.sort(reverse=True)
    return len(tracked), total, sizes[:3]


REF = re.compile(r"(?:\]\(|`|「|见\s)([^\s`|)\]」，,]{3,200}?\.(?:md|json|py|txt|csv|html|js|ts|jsonl|sh|yaml|yml|xlsx|pdf|png|jpg))")
SRC_DIRS = ["README.md", "llms.txt"]
src_files = [p for p in tracked if p in ("README.md", "llms.txt")]
src_files += [p for p in tracked if p.startswith("indexes/") and p.endswith(".md")]
src_files += [p for p in tracked if "/05-索引/" in p and p.endswith(".md")]

ok = bad_style = broken = 0
broken_list = []
style_list = []
total_refs = 0
per_src = collections.defaultdict(lambda: {"引用": 0, "可达": 0, "书写不规范": 0, "真断链": 0})
brk_class = collections.Counter()
brk_by_class = collections.defaultdict(list)
banned = ("11-军事应用", "受控", "核心合同", "身份", "私密")
stem = collections.defaultdict(list)


def stemkey(n):
    return re.sub(r"(v[\d.]+|V[\d.]+|20\d{6})", "", n, flags=re.I)


for p in tracked:
    stem[stemkey(os.path.basename(p))].append(p)

for src in src_files:
    try:
        text = open(os.path.join(ROOT, src), encoding="utf8").read()
    except UnicodeDecodeError:
        continue
    for lineno, line in enumerate(text.split("\n"), 1):
        for m in REF.finditer(line):
            ref = m.group(1).strip("`「见 ")
            if ref.startswith(("http://", "https://", "mailto:", "/")):
                continue
            total_refs += 1
            ps = per_src[src]
            ps["引用"] += 1
            cand_root = os.path.normpath(ref).replace("\\", "/")
            cand_dir = os.path.normpath(os.path.join(os.path.dirname(src), ref)).replace("\\", "/")
            if cand_root in tracked_set or cand_dir in tracked_set:
                ok += 1
                ps["可达"] += 1
                continue
            base = os.path.basename(cand_root)
            if base in by_name:
                bad_style += 1
                ps["书写不规范"] += 1
                if len(style_list) < 200:
                    style_list.append({"引用": ref, "出处": src, "行": lineno, "实际": by_name[base][0]})
            else:
                broken += 1
                ps["真断链"] += 1
                if any(s in ref for s in banned):
                    k = "指向公共版剔除域（公共版本就无此件）"
                elif stem.get(stemkey(base)):
                    k = "同名件存在但日期或版本号漂移"
                else:
                    k = "全库无相近件"
                brk_class[k] += 1
                if len(brk_by_class[k]) < 80:
                    brk_by_class[k].append({"引用": ref, "出处": src, "行": lineno})
                if len(broken_list) < 80:
                    broken_list.append({"引用": ref, "出处": src, "行": lineno})

zero_byte = [p for p in tracked if os.path.exists(os.path.join(ROOT, p)) and os.path.getsize(os.path.join(ROOT, p)) == 0]
pyc = [p for p in tracked if p.endswith(".pyc") or "__pycache__" in p]
spaces = [p for p in tracked if " " in p]

declared = {}
for f in ("README.md", "llms.txt"):
    t = open(os.path.join(ROOT, f), encoding="utf8").read()
    declared[f] = {
        "含4734": "4734" in t or "4,734" in t,
        "含4741": "4741" in t or "4,741" in t,
        "规模行片段": [ln.strip()[:120] for ln in t.split("\n") if "个文件" in ln or "跟踪中" in ln][:4],
    }

n_files, n_bytes, top3 = measure_files()
readme = open(os.path.join(ROOT, "README.md"), encoding="utf8").read()
claim = re.search(r"=\s*([\d,]{7,})\s*字节", readme)
claim_bytes = int(claim.group(1).replace(",", "")) if claim else None

out = {
    "跟踪文件数与字节": {"文件数": n_files, "字节合计": n_bytes, "最大三件": top3,
                  "README声明字节": claim_bytes, "差值_实测减声明": (n_bytes - claim_bytes) if claim_bytes else None},
    "引用体检": {"源文件数": len(src_files), "引用总数": total_refs, "可达": ok, "书写不规范": bad_style, "真断链": broken,
             "真断链分级": dict(brk_class), "真断链分级样本": {k: v for k, v in brk_by_class.items()},
             "逐源分布": {k: v for k, v in sorted(per_src.items(), key=lambda kv: -kv[1]["引用"])},
             "真断链清单": broken_list, "书写不规范样本": style_list},
    "卫生": {"零字节文件": zero_byte, "pyc与pycache": pyc, "文件名含空格": spaces},
    "公开层数字声明现值": declared,
}
text = json.dumps(out, ensure_ascii=False, indent=1)
open(os.path.join(QC, "关后复核-协调人复测-v1.0-20261104.json"), "w", encoding="utf8").write(text)
print("文件=%d 字节=%d README声明=%s 差=%s" % (n_files, n_bytes, claim_bytes, n_bytes - (claim_bytes or 0)))
print("引用总数=%d 可达=%d 书写不规范=%d 真断链=%d" % (total_refs, ok, bad_style, broken))
print("真断链分级", dict(brk_class))
print("逐源前三", list(sorted(per_src.items(), key=lambda kv: -kv[1]["引用"]))[:3])
print("卫生：零字节=%d pyc=%d 空格名=%d" % (len(zero_byte), len(pyc), len(spaces)))
