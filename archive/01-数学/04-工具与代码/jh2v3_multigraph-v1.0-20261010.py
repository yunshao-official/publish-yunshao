# -*- coding: utf-8 -*-
"""J-H2 v3 多图分治（读已落盘文件，纯计算零写盘）：引擎 walk 按断口切分=路径森林"""
import json
import numpy as np

WALK = r"H:\理论存档\01-数学\04-工具与代码\results\jh2\stitched_path.txt"
EDGES = r"H:\理论存档\01-数学\04-工具与代码\results\jh2\sem_edges.txt"

def main():
    sw = [int(x) for x in open(WALK) if x.strip()]
    adjset = {}
    for l in open(EDGES):
        u, v = map(int, l.split())
        adjset.setdefault(u, set()).add(v)
        adjset.setdefault(v, set()).add(u)

    # 按"非真边步"切段（每段=一个连通分量的贪心路径）
    segments = [[sw[0]]]
    for i in range(len(sw) - 1):
        u, v = sw[i], sw[i + 1]
        if v in adjset.get(u, ()):
            segments[-1].append(v)
        else:
            segments.append([v])

    sizes = sorted((len(s) for s in segments), reverse=True)
    big = [s for s in segments if len(s) >= 10]
    # 段内真边率（≥10 词的段）
    rates = []
    for s in big:
        te = sum(1 for i in range(len(s) - 1) if s[i + 1] in adjset.get(s[i], ()))
        rates.append(te / (len(s) - 1))
    full = sum(1 for r in rates if r == 1.0)

    out = {
        "total_nodes": len(sw),
        "n_segments": len(segments),
        "segments_ge10": len(big),
        "size_top10": sizes[:10],
        "size_median": int(np.median(sizes)),
        "singletons": sum(1 for s in sizes if s == 1),
        "big_seg_true_rate_min": round(min(rates), 4) if rates else None,
        "big_seg_true_rate_mean": round(float(np.mean(rates)), 4) if rates else None,
        "big_seg_full_rate_count": full,
        "big_seg_full_rate_pct": round(100 * full / len(rates), 2) if rates else None,
        "J-H2v3": ("PASS（路径森林全真边·多图分治成立）"
                   if rates and min(rates) == 1.0 else
                   ("PASS边缘（部分段非100%·如实记录）" if rates and full / len(rates) > 0.9 else
                    "FAIL（判负照记）")),
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
