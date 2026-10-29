# -*- coding: utf-8 -*-
"""
merge_k2-v1.0-20260920.py — K2 案例级双轨取优交付管线（预注册-m4插桩解剖与K2大样落地-v1.0-20260920 §四冻结口径）
交付规则沿用第3轮预注册乙冻结口径（B-2，本脚本不新增不修改）：交付 = min(base_b1, m1_b1)，并列取 base。
输入：网格目录（含 jsonl/ 子目录，文件名 {tag}_base.jsonl / {tag}_m1.jsonl，每文件一案例一跑）。
输出：k2_account.json —— 每案例（base b0/b1、m1 b0/b1、交付、胜者、双轨墙钟、size、pass）+ 分档 Σ + 全档表。
判别式模式（--disc c1表）：输入 {case: c1_path}（来自插桩版 rep0 谱复跑），按 D-K2 两闸
（G1 完整性闸 size==N；G2 材料闸 c1_path>=3）给出规则是否启 m1，对照归档 m1 实际胜负出混淆矩阵。
用法:
  python merge_k2-v1.0-20260920.py --grid H:/door1/grid_v4_20260920 --out k2_account.json
  python merge_k2-v1.0-20260920.py --grid H:/door1/grid_v4_20260920 --disc c1_path.json --out k2_disc.json
"""
import argparse, json, os, sys

def load_case(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                return json.loads(line)
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--disc", default=None, help="c1_path JSON: {\"N_seed\": c1_path_value}（判别式模式）")
    ap.add_argument("--m", type=int, default=3, help="K2 适用 m（默认 3）")
    a = ap.parse_args()

    jl = os.path.join(a.grid, "jsonl")
    seeds = [7, 13, 21, 42, 99, 2024]
    ns = [1000, 10000, 100000]
    cases, sum_by_n = {}, {}
    for N in ns:
        for s in seeds:
            tag = f"g4_N{N}_m{a.m}_s{s}"
            fb, fm = os.path.join(jl, tag + "_base.jsonl"), os.path.join(jl, tag + "_m1.jsonl")
            if not (os.path.exists(fb) and os.path.exists(fm)):
                continue
            b, m = load_case(fb), load_case(fm)
            if b is None or m is None:
                print(f"[MISS] {tag}", file=sys.stderr); continue
            bb1, mb1 = b["breaks1"], m["breaks1"]
            delivery, winner = (bb1, "base") if bb1 <= mb1 else (mb1, "m1")
            rec = {
                "case": f"N{N}_s{s}", "N": N, "seed": s, "m": a.m,
                "base_b0": b["breaks0"], "base_b1": bb1, "base_size": b["size"], "base_pass": b["pass"], "base_t_rep": round(b.get("t_rep", 0.0), 3),
                "m1_b0": m["breaks0"], "m1_b1": mb1, "m1_size": m["size"], "m1_pass": m["pass"], "m1_t_rep": round(m.get("t_rep", 0.0), 3),
                "delivery": delivery, "winner": winner,
                "m1_would_win": bool(mb1 < bb1),
                "base_complete": bool(b["size"] == N),
            }
            cases[rec["case"]] = rec
            sum_by_n.setdefault(N, {"sum": 0, "n": 0, "base_sum": 0, "m1_sum": 0, "m1_wins": 0})
            sum_by_n[N]["sum"] += delivery; sum_by_n[N]["n"] += 1
            sum_by_n[N]["base_sum"] += bb1; sum_by_n[N]["m1_sum"] += mb1
            sum_by_n[N]["m1_wins"] += 1 if winner == "m1" else 0

    out = {"grid": a.grid, "m": a.m, "rule": "delivery=min(base_b1,m1_b1), tie->base (B-2 frozen)",
           "sum_by_N": {str(k): v for k, v in sorted(sum_by_n.items())},
           "grand_delivery_sum": sum(v["sum"] for v in sum_by_n.values()),
           "cases": cases}
    print("K2 account (per N):")
    for N, v in sorted(sum_by_n.items()):
        print(f"  N={N}: cases={v['n']} delivery_sum={v['sum']} (base_sum={v['base_sum']}, m1_sum={v['m1_sum']}, m1_wins={v['m1_wins']})")
    print(f"  GRAND delivery_sum={out['grand_delivery_sum']}")

    # ---- 判别式模式 ----
    if a.disc:
        with open(a.disc, "r", encoding="utf-8") as f:
            c1map = json.load(f)
        TP = FP = TN = FN = 0
        saved_wall = 0.0
        deliver_rule, deliver_dual = 0, 0
        rows = []
        for key, rec in cases.items():
            ck = f"{rec['N']}_{rec['seed']}"
            c1 = c1map.get(ck)
            g1 = rec["base_complete"]
            g2 = (c1 is not None and c1 >= 3)
            rule_run = bool(g1 and g2)
            win = rec["m1_would_win"]
            if rule_run and win: tp, cls = 1, "TP"
            elif rule_run and not win: tp, cls = 1, "FP"
            elif (not rule_run) and (not win): tp, cls = 0, "TN"
            else: tp, cls = 0, "FN"
            if cls == "TP": TP += 1
            elif cls == "FP": FP += 1
            elif cls == "TN": TN += 1
            else: FN += 1
            if not rule_run:
                saved_wall += rec["m1_t_rep"] if rec["m1_t_rep"] > 0 else 0
            deliver_rule += rec["base_b1"] if not rule_run else min(rec["base_b1"], rec["m1_b1"])
            deliver_dual += rec["delivery"]
            rows.append({"case": key, "c1_path": c1, "G1": g1, "G2": g2, "rule_run": rule_run,
                         "m1_would_win": win, "class": cls,
                         "base_b1": rec["base_b1"], "m1_b1": rec["m1_b1"],
                         "m1_t_rep": rec["m1_t_rep"], "base_complete": g1})
        out["discriminant"] = {
            "rule": "D-K2: G1 base_complete AND G2 c1_path>=3 -> run m1 arm",
            "c1_source": a.disc, "TP": TP, "FP": FP, "TN": TN, "FN": FN,
            "false_positive_zero": bool(FP == 0),
            "saved_wall_s": round(saved_wall, 1),
            "delivery_rule_sum": deliver_rule, "delivery_dual_sum": deliver_dual,
            "rows": rows,
        }
        print(f"D-K2 confusion: TP={TP} FP={FP} TN={TN} FN={FN}  FP=0? {FP==0}")
        print(f"saved_wall(m1 arms skipped)={saved_wall:.1f}s  delivery rule/dual={deliver_rule}/{deliver_dual}")

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"written -> {a.out}")

if __name__ == "__main__":
    main()
