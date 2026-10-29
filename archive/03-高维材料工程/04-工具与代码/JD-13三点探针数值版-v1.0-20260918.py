# -*- coding: utf-8 -*-
"""
JD-13 三点探针数值版 v1.0（2026-09-18）· 常开模式第3轮
白名单管线合规延拓：import 原版 yunshao_limitation_test.py（sha256=b1b20b05…e70 注册值，
20260918 实测逐位一致），零改动；run_config 调用样式镜像 W1 驱动脚本。
门禁：D=8 N=14 gradient 必须逐值复现 692/50223/62.0281/145.15/100%，任一不符即中止。
探针配置（等频 freq_ratio=1.0，D-09结论：组合覆盖作业应等频）：
  D=9  N=16  参考（她的维数同类材料）
  9.5  N=17  承载维取整=10（C4先例同构；9.5维验证原脚本失传，承载口径注记【理论参照】）
  10.5 N=19  承载维取整=11
  12   N=22  整维
确定性：无随机源外泄（seed=42 锁定）、零网络、零API、零文件IO（stdout交调用方落盘）。
"""
import importlib.util, json, sys
import numpy as np

ORIG = r"C:\Users\Administrator\.openclaw\workspace-programmer\scratch\hermes_rescue_20260826\extract\yunshao\_archive_old\yunshao_limitation_test.py"
spec = importlib.util.spec_from_file_location("lim", ORIG)
lim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lim)

import time

def run_config(D, N, mode='gradient', n=8000, freq_ratio=1.0, seed=42):
    waves = lim.generate_waves(N, D, phase_mode=mode, freq_ratio=freq_ratio, seed=seed)
    t0 = time.time()
    I, pos = lim.interference_field(waves, D, n_samples=n, seed=seed)
    wells = lim.find_wells(I, pos)
    adj, edges = lim.build_graph(wells)
    m = lim.graph_metrics(adj, len(wells))
    return {"D": D, "N": N, "wells": len(wells), "edges": int(edges),
            "components": m["components"], "largest_pct": m["largest_pct"],
            "lambda2": m["alg_conn"], "avg_degree": m["avg_degree"],
            "time_s": round(time.time() - t0, 1)}

def main():
    out = {"meta": {"pipeline": "yunshao_limitation_test.py@注册哈希b1b20b05…e70",
                    "note": "白名单合规延拓；等频口径；分数维取整数承载【理论参照】",
                    "gate_expect": "692/50223/62.0281/145.15/100"}}
    g = run_config(8, 14)
    out["gate_D8"] = g
    ok = (g["wells"] == 692 and g["edges"] == 50223
          and abs(g["lambda2"] - 62.0281) < 0.001
          and abs(g["avg_degree"] - 145.15) < 0.01
          and g["largest_pct"] == 100.0)
    out["gate_pass"] = bool(ok)
    if not ok:
        out["ABORT"] = "门禁逐值不符，全部作废"
        print(json.dumps(out, ensure_ascii=False, indent=1))
        sys.exit(2)
    probes = {}
    for tag, D, N in [("D9_ref", 9, 16), ("D9p5_probe", 10, 17),
                      ("D10p5_probe", 11, 19), ("D12_probe", 12, 22)]:
        probes[tag] = run_config(D, N)
    out["probes"] = probes
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
