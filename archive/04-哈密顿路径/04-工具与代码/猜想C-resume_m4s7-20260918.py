# -*- coding: utf-8 -*-
"""resume_m4s7.py · 第四遍续跑（2026-09-18）：仅补 m4@1e5 s7（原后台任务在引擎阶段被中断）
口径与 pass4_runner.py 完全一致（cap=1800 满额），完成后把 checkpoint_pass4.json 中
4 个已定格点并入，重写 summary_pass4.json。"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import pass4_runner as p4


def main():
    # 恢复已有结果
    cp = os.path.join(BASE, "checkpoint_pass4.json")
    if os.path.exists(cp):
        with open(cp, encoding="utf-8") as f:
            p4.RESULTS.extend(json.load(f)["results"])
        p4.log(f"恢复 {len(p4.RESULTS)} 个已定格点")
    # 续跑 m4 s7（若 checkpoint 已含则跳过）
    have = {c["tag"] for c in p4.RESULTS}
    if "m4_N100000_s7" not in have:
        p4.run_cell(4, 100000, 7, 1800.0)
    with open(os.path.join(BASE, "summary_pass4.json"), "w", encoding="utf-8") as f:
        json.dump({"results": p4.RESULTS}, f, ensure_ascii=False, indent=1)
    p4.log(f"== 第四遍（含续跑）结束：{len(p4.RESULTS)} 格点 ==")


if __name__ == "__main__":
    main()
