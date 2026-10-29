# -*- coding: utf-8 -*-
"""
merge_v6main.py — 网格v6 主线化收口合并+三判据判定（4i 专轮）
判据正本 = 预注册---b1主线化网格v6程序性确认轮-v1.0-20260921 §四（冻结，未改一字）：
  M-V1：对拍门（mv1_gate.py 已判，本脚本只读其结论文件复核引用）。
  M-V2（主判据）：90 案例账 65/90 对网格 v5 零回退；m4@1e5 构造完整率 6/6 维持；
    m5@1e5 6/6 全零维持；m3@1e3 交付 Σ608 维持——任一破坏=主线化判负照记（回退 v2.1 正本，账面披露）。
  M-V3（零漂移面）：72 m≥4 案例中 66 例判定字段与 v5 逐位同（仅 m4@1e5 六例按设计改变；
    mech b1; 标记面=设计内）——超出六例的任何行为变化=判负照记。
对照锚 = H:\\door1\\grid_v5_20260921\\grid_v5_report.json（v5 正式账：m≥4=b1 臂；m3=base 臂
  +m1 carried_v4）。K2 口径：v6 base 新跑 + m1 carried_v5（即 v5 账 carried_v4 数字，预注册 §三 原文
  「m1 carried_v5」），交付=min，并列取 base。
判定字段 = pass/breaks0/breaks1/size/defects（rot/t_* 墙钟敏感不进门——冻结口径）。
"""
import json, os, glob, re
from collections import defaultdict

ROOT = r"H:\door1\grid_v6main_20261002"
V5RPT = r"H:\door1\grid_v5_20260921\grid_v5_report.json"
MV1J = os.path.join(ROOT, "gate", "mv1_judgment.json")
SEEDS = [7, 13, 21, 42, 99, 2024]
CMP_KEYS = ["pass", "breaks0", "breaks1", "size", "defects"]   # 冻结判定字段（M-V1/M-V3 同一口径）

def load_jsonl(p):
    out = []
    for line in open(p, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except Exception: continue
        if isinstance(r, dict) and "pass" in r: out.append(r)
    return out

def gpwin_of(tag):
    p = os.path.join(ROOT, "logs", tag + ".log")
    if not os.path.exists(p): return None
    txt = open(p, encoding="utf-8", errors="replace").read()
    m = re.findall(r"^\[GPWIN\].*$", txt, re.M)
    return m[-1] if m else None

# ---- v6 收集 ----
recs = []
for f in sorted(glob.glob(os.path.join(ROOT, "jsonl", "g6_*.jsonl"))):
    for r in load_jsonl(f):
        tag = os.path.basename(f)[:-6]
        r["arm"] = tag.rsplit("_", 1)[1]
        r["run_tag"] = tag
        r["gpwin"] = gpwin_of(tag)
        recs.append(r)

# ---- v5 锚（正式账 90 行） ----
v5rows = json.load(open(V5RPT, encoding="utf-8"))
v5 = {}
for r in v5rows:
    v5[(r["N"], r["m"], r["seed"])] = r

# ---- 合并：m≥4 单臂 main；m3 K2 口径 ----
case_rows = []
seen = set()
for r in sorted(recs, key=lambda x: (x["N"], x["m"], x["seed"])):
    key = (r["N"], r["m"], r["seed"])
    if key in seen: continue
    seen.add(key)
    row = dict(r)
    a5 = v5.get(key)
    if r["m"] >= 4:
        row["k2"] = "single_main_default_b1"
        v5row = a5   # v5 账该案例=b1 臂
    else:
        row["k2"] = "base_v6+m1carried_v5"
        row["k2_base_v6"] = r["breaks1"]
        row["k2_m1_carried_v5"] = a5.get("k2_m1_b1_carried_v4") if a5 else None
        m1c = row["k2_m1_carried_v5"]
        if m1c is not None and m1c < r["breaks1"]:
            row["k2_delivery_v6"] = m1c; row["k2_pick"] = "m1_carried_v5"
        else:
            row["k2_delivery_v6"] = r["breaks1"]; row["k2_pick"] = "base_v6"
        row["k2_delivery_pass"] = (row["k2_delivery_v6"] == 0 and r["size"] == r["N"]
                                   and (m1c is None or True))
        v5row = a5   # v5 账 m3 行=base 臂新跑（对照 base 对 base）
    row["v5_pass"] = a5["pass"] if a5 else None
    row["v5_breaks1"] = a5["breaks1"] if a5 else None
    row["v5_size"] = a5["size"] if a5 else None
    if a5:
        row["v5_behav_diff"] = {k: [a5.get(k), row.get(k)] for k in CMP_KEYS if a5.get(k) != row.get(k)} or {}
    else:
        row["v5_behav_diff"] = "no_v5_anchor"
    case_rows.append(row)

with open(os.path.join(ROOT, "v6main_results.jsonl"), "w", encoding="utf-8") as f:
    for r in sorted(recs, key=lambda x: (x["N"], x["m"], x["seed"], x["arm"])):
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(os.path.join(ROOT, "grid_v6main_report.json"), "w", encoding="utf-8") as f:
    json.dump(case_rows, f, ensure_ascii=False, indent=1)

print("=" * 100)
print(f"v6 runs={len(recs)} cases={len(case_rows)} (锚 v5 rows={len(v5rows)})")
npass = sum(1 for r in case_rows if r["pass"])
print(f"v6 PASS={npass}/90   (v5=65/90)")

rep = defaultdict(lambda: [0, 0, 0])
for r in case_rows:
    k = (r["N"], r["m"]); rep[k][0] += 1
    rep[k][1] += 1 if r["pass"] else 0
    rep[k][2] += 1 if r["v5_pass"] else 0
print("--- per (N,m): v6 PASS / v5 PASS ---")
for k in sorted(rep):
    c, p6, p5 = rep[k]
    flag = "" if p6 >= p5 else "  <-- REGRESSION"
    print(f"  {k}: v6 {p6}/{c}  v5 {p5}/{c}{flag}")

print("--- per-case pass flips (v5 -> v6) ---")
flips = [(r["N"], r["m"], r["seed"], r["v5_pass"], r["pass"], r["breaks1"], r["v5_breaks1"])
         for r in case_rows if r["v5_pass"] is not None and r["v5_pass"] != r["pass"]]
if not flips: print("  (none — 零翻转)")
for N, m, s, a, b, b1, b1v5 in flips:
    print(f"  N{N} m{m} s{s}: v5={'PASS' if a else 'FAIL'}(b1={b1v5}) -> v6={'PASS' if b else 'FAIL'}(b1={b1})")

print("=" * 100)
print("M-V2 主判据（冻结四肢）：")
print("[1] 90 案例 65/90 对 v5 零回退：")
n_regress = sum(1 for r in case_rows if r["v5_pass"] is not None and r["v5_pass"] and not r["pass"])
limb1 = (n_regress == 0 and npass >= 65)
print(f"    翻负案例数={n_regress}  v6 PASS={npass}/90 -> {'零回退·过' if limb1 else '破坏→判负照记'}")

print("[2] m4@1e5 构造完整率 6/6 维持：")
m4e5 = [r for r in case_rows if r["N"] == 100000 and r["m"] == 4]
comp = 0
for r in sorted(m4e5, key=lambda x: SEEDS.index(x["seed"])):
    c = 1 if r["size"] == 100000 else 0; comp += c
    print(f"    s{r['seed']}: size={r['size']} b0={r['breaks0']} b1={r['breaks1']} pass={r['pass']} gpT=[{r['gpwin']}]")
limb2 = (comp == 6)
print(f"    构造完整率 = {comp}/6 -> {'维持·过' if limb2 else '破坏→判负照记'}")

print("[3] m5@1e5 6/6 全零维持：")
m5e5 = [r for r in case_rows if r["N"] == 100000 and r["m"] == 5]
p56 = sum(1 for r in m5e5 if r["pass"])
z5 = all(r["breaks1"] == 0 for r in m5e5)
limb3 = (p56 == 6 and z5)
for r in sorted(m5e5, key=lambda x: SEEDS.index(x["seed"])):
    print(f"    s{r['seed']}: b0={r['breaks0']} b1={r['breaks1']} pass={r['pass']}")
print(f"    m5@1e5: pass={p56}/6 全零={z5} -> {'维持·过' if limb3 else '破坏→判负照记'}")

print("[4] m3@1e3 交付 Σ608 维持：")
m3e3 = [r for r in case_rows if r["N"] == 1000 and r["m"] == 3]
m3e3.sort(key=lambda x: SEEDS.index(x["seed"]))
tot_base = sum(r["breaks1"] for r in m3e3)
tot_del = sum(r["k2_delivery_v6"] for r in m3e3)
for r in m3e3:
    print(f"    s{r['seed']}: b0={r['breaks0']} base_b1={r['breaks1']} (v5base={r['v5_breaks1']}, m1_carried_v5={r['k2_m1_carried_v5']}, 交付={r['k2_delivery_v6']}) behav_diff={r['v5_behav_diff'] or '无'}")
limb4 = (tot_base == 608)
print(f"    base臂 Σ={tot_base}（v5 base=608；冻结数字口径）  交付Σ={tot_del}（v5 交付=605） -> {'Σ608 维持·过' if limb4 else '破坏→判负照记'}")

mv2 = limb1 and limb2 and limb3 and limb4
print(f"M-V2 = {'PASS 四肢全过' if mv2 else 'FAIL（判负照记分支兑现，回退 v2.1 正本，账面披露）'}")

print("=" * 100)
print("M-V3 门控零漂移面（72 m≥4 案例判定字段对 v5 逐位同；仅 m4@1e5 六例按设计改变）：")
mge4 = [r for r in case_rows if r["m"] >= 4]
same = [r for r in mge4 if not r["v5_behav_diff"]]
diff = [r for r in mge4 if isinstance(r["v5_behav_diff"], dict) and r["v5_behav_diff"]]
print(f"  逐位同={len(same)}/72  行为变化={len(diff)}/72（冻结允许=仅 m4@1e5 六例）")
beyond = [r for r in diff if not (r["N"] == 100000 and r["m"] == 4)]
for r in sorted(diff, key=lambda x: (x["N"], x["m"], SEEDS.index(x["seed"]))):
    tag_ok = "（设计内·m4@1e5）" if (r["N"] == 100000 and r["m"] == 4) else "（<-- 超出六例=判负照记）"
    print(f"    N{r['N']} m{r['m']} s{r['seed']}: {r['v5_behav_diff']} {tag_ok}")
mv3 = (len(same) >= 66) and (not beyond)
print(f"M-V3 = {'PASS（变化面 ⊆ m4@1e5 六例）' if mv3 else 'FAIL 判负照记'}")

print("=" * 100)
print("M-V1 复核引用：")
try:
    mv1 = json.load(open(MV1J, encoding="utf-8"))
    ok = True
    for c, r in mv1.items():
        a, b = r["gwin"], r["v21"]
        d = {k: (a.get(k), b.get(k)) for k in CMP_KEYS if a.get(k) != b.get(k)}
        print(f"  {c}: {'逐位同' if not d else d}  (gwin b0={a.get('breaks0')} b1={a.get('breaks1')} | v21 b0={b.get('breaks0')} b1={b.get('breaks1')})")
        ok = ok and not d
    print(f"  M-V1 = {'PASS' if ok else 'BREAK'}")
except Exception as e:
    print(f"  读取失败: {e}")

print("=" * 100)
verdict = "全部通过 → B1 主线化正式生效，网格账链增 v6（主线账）行" if (mv2 and mv3 and ok) else "存在破坏 → 见上方逐肢判定"
print(f"【4i 总裁定】{verdict}")

print("--- m=3 K2 对照表（v6 base 新跑 + m1 carried_v5）---")
for N in (1000, 10000, 100000):
    rows = [r for r in case_rows if r["N"] == N and r["m"] == 3]
    rows.sort(key=lambda x: SEEDS.index(x["seed"]))
    d = [r["k2_delivery_v6"] for r in rows]
    print(f"  N={N}: v6base={[r['breaks1'] for r in rows]} Σ={sum(r['breaks1'] for r in rows)} | m1carried_v5={[r['k2_m1_carried_v5'] for r in rows]} | 交付Σ={sum(d)}")
