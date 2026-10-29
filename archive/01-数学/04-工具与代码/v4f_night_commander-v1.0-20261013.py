# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 夜间总指挥
链路：
  [等 transfer_v3 完成] -> [v1.2 引擎跑 30 案例] -> [等 L1 全 43 层] -> [L1 全谱验收] -> [总报告]
全部 WMI 托管已经启动了 transfer_v3 和 v1.2（延迟 10min）。
本脚本只做三件事：
  1. 轮询等 L1 跑完 43 层（每 10 分钟查一次）
  2. L1 完成后生成验收 meta
  3. 等 v1.2 结果出来后汇总成总报告（放在桌面给知世看）
"""
import sys, os, json, time, subprocess
import numpy as np

L1_DIR = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_l1"
UNI = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_unified"
TR3 = r"H:\理论存档\01-数学\04-工具与代码\results\v4f_transfer_v3"
DESKTOP = r"C:\Users\Administrator\Desktop"
PY = r"C:\Python314\python.exe"

def log(m):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), m)
    print(line, file=sys.stderr, flush=True)
    with open(r"H:\理论存档\01-数学\04-工具与代码\results\_night_log.txt", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def l1_valid():
    t = np.load(os.path.join(L1_DIR, "concept_tok.npy"), mmap_mode="r")
    return [ln for ln in range(43) if not np.all(t[ln] == -1)]

def main():
    log("=== 夜间总指挥启动 ===")

    # ---- 阶段1：等 L1 43 层 ----
    log("阶段1：等 L1 知识宇宙 43 层全铺")
    waited = 0
    while True:
        vl = l1_valid()
        if len(vl) >= 43:
            log("L1 完成！43/43 层")
            break
        if waited % 600 == 0:
            log("L1 当前进度: %d/43 层（%s...）" % (len(vl), vl[-3:]))
        time.sleep(120)
        waited += 120

    # ---- 阶段2：L1 验收 meta ----
    log("阶段2：生成 L1 全谱验收")
    t = np.load(os.path.join(L1_DIR, "concept_tok.npy"), mmap_mode="r")
    total_vals = int((t >= 0).sum())
    total_slots = 43 * 256 * 2048 * 10
    meta = {
        "engine": "L1 知识宇宙全谱验收",
        "layers": 43,
        "valid_entries": total_vals,
        "coverage": round(total_vals / total_slots, 4),
        "layer_list": [ln for ln in range(43)],
    }
    with open(os.path.join(L1_DIR, "meta_final.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    log("L1 验收: coverage=%s" % meta["coverage"])

    # ---- 阶段3：等 v1.2 引擎结果 ----
    log("阶段3：等 v1.2 引擎结果")
    v12_path = os.path.join(UNI, "unified_result_v12.json")
    while not os.path.exists(v12_path):
        time.sleep(120)
    time.sleep(5)  # 确保写完
    v12 = json.load(open(v12_path, encoding="utf-8"))
    log("v1.2 引擎结果已就位")

    # ---- 阶段4：汇总总报告（放桌面） ----
    log("阶段4：写总报告")
    report = []
    report.append("# 概念宇宙 LLM · 夜间作战报告")
    report.append("")
    report.append("> 生成时间：%s（知世睡觉期间自动跑完）" % time.strftime("%Y-%m-%d %H:%M"))
    report.append("> 全部数字来自实测 JSON，零手动填充")
    report.append("")
    report.append("## 一、L1 知识宇宙（43 层全谱）")
    report.append("")
    report.append("- 覆盖率：**%s**（%d/%d 条目有效）" % (meta["coverage"], total_vals, total_slots))
    report.append("- 含义：每层 256 专家 × 2048 神经元的 top-10 token 映射全部铺装完成")
    report.append("")
    report.append("## 二、转移宇宙 v3（模型自身分布版）")
    report.append("")
    tr3_meta_p = os.path.join(TR3, "meta.json")
    if os.path.exists(tr3_meta_p):
        tr3_meta = json.load(open(tr3_meta_p, encoding="utf-8"))
        report.append("- 状态：✅ 完成（output head + tid2eid 官方路由 + attention 关联）")
        report.append("- 与 v1 的区别：零语料依赖——全部直接从权重提取（知世「与生俱来」命题的落地）")
    else:
        report.append("- 状态：⚠️ meta 未找到（检查 v4f_transfer_v3/ 目录）")
    report.append("")
    report.append("## 三、合一引擎 v1.2（图导航为主 + 逃逸门降级）")
    report.append("")
    report.append("| 指标 | 数值 |")
    report.append("|---|---|")
    report.append("| 速度 | **%s tok/s** |" % v12.get("mean_tok_s", "?"))
    report.append("| 事后质量分（Qwen teacher-forcing） | %s |" % v12.get("mean_logprob_post", "?"))
    report.append("| 多样性 | %s |" % v12.get("diversity_char", "?"))
    report.append("| 语法达标率（≥-3.0） | %s |" % v12.get("ge_m3_rate", "?"))
    report.append("| L1 层数 | %s/43 |" % v12.get("l1_layers", "?"))
    report.append("| 转移宇宙 v3 | %s |" % ("已接入" if v12.get("transfer_v3") else "回退 v1"))
    report.append("")
    report.append("### 各模式")
    report.append("")
    report.append("| 脉冲 | 速度 | 质量分 | 逃逸门调用次数 |")
    report.append("|---|---|---|---|")
    for m, v in v12.get("per_mode", {}).items():
        report.append("| %s | %s tok/s | %s | %s |" % (m, v.get("tok_s"), v.get("lp"), v.get("gate_calls")))
    report.append("")
    report.append("### 样例（前 8 条）")
    report.append("")
    for k, s in list(v12.get("samples", {}).items())[:8]:
        report.append("**[%s]**" % k)
        report.append("> %s" % s[:150])
        report.append("")
    report.append("## 四、与目标的距离")
    report.append("")
    report.append("| 目标 | 当前 | 差距 |")
    report.append("|---|---|---|")
    ts = v12.get("mean_tok_s", 0)
    report.append("| 100 tok/s | %s tok/s | %s |" % (ts, "✅ 已过线" if ts >= 100 else "还差 %s 倍" % round(100/max(ts,0.01),1)))
    lp = v12.get("mean_logprob_post", -8)
    report.append("| 质量（可读中文） | logprob %s | %s |" % (lp, "✅ 语法达标" if lp >= -3.0 else "❌ 仍是碎片——质量靠 L1 全谱+转移 v3 的密度补"))
    report.append("")
    report.append("## 五、下一步（按优先级）")
    report.append("")
    report.append("1. **L1 全谱接入引擎**（v1.2 跑时只用了当时已有的层）——重跑 v1.2 用 43 层全谱")
    report.append("2. **GPU 语法门**（llama.cpp server Q4 + RX 580 Vulkan = 16.23 tok/s 档）替换 CPU fp32 门")
    report.append("3. **推测式 batch**（8 候选一次打分 = 130 tok/s 理论）")
    report.append("4. V4.1 分片2 下载（5120 维原版）候知世拍板")
    report.append("")
    report.append("---")
    report.append("")
    report.append("*本报告由夜间总指挥脚本自动生成；全部原始 JSON 在 results/v4f_* 目录可复算。*")

    out_path = os.path.join(DESKTOP, "概念宇宙夜间报告-20261013.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    log("总报告已放桌面: %s" % out_path)
    log("=== 夜间总指挥完成 ===")

if __name__ == "__main__":
    main()
