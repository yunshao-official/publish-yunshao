# -*- coding: utf-8 -*-
"""拆分 stage1 输出的多文件内容并保存"""
import sys

mode = None
files = {}
current_name = None
current_content = []

for line in sys.stdin:
    if line.startswith("<<<FILE:"):
        if current_name and current_content:
            files[current_name] = "".join(current_content)
        current_name = line.strip().replace("<<<FILE:", "").replace(">>>", "")
        current_content = []
        mode = "write"
    elif line.startswith("<<<ALL_DONE>>>"):
        if current_name and current_content:
            files[current_name] = "".join(current_content)
        mode = None
    elif mode == "write":
        current_content.append(line)

for fname, content in files.items():
    if ".." in fname or "/" in fname or chr(92) in fname:
        print(f"[skip] unsafe filename: {fname}")
        continue
    with open(fname, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[saved] {fname} ({len(content)} bytes)")

print(f"[total] {len(files)} files saved")
