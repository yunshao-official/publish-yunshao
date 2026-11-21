# -*- coding: utf-8 -*-
"""
mv1_gate.py — M-V1 对拍门执行器（预注册---b1主线化网格v6程序性确认轮-v1.0 §三/§四 冻结原文）
门定义（冻结，未改一字）：m4@1e5 s7＋m5@1e5 s7＋m3@1e3 s7，新正本默认开 vs gwin v1.0 `--b1 1` 同案例；
  判定字段（pass/breaks0/breaks1/size/defects；rot 与时延不进门）逐位同——任一破=实现缺陷，
  阻断全网格跑，判工具债照记。
执行纪律：串行逐对（gwin 先、v21 后，同案例背靠背=同机况）；真实退出码直捕（round9 runner 纪律）；
  每跑独立 jsonl；判定以 jsonl 字段为准。v21 侧 = m≥4 `--m1`（不带 --b1 旗标，证默认值生效）、
  m3 base 臂 `--nos`；gwin 侧 = 同案例 + `--b1 1`（旗标行为）。
"""
import os, subprocess, sys, time, json, re

GWIN = r"H:\door1\gpipeanat_20260920\m1v2gwin_v10.exe"
V21  = r"H:\door1\grid_v6main_20261002\m1v2_v21_main.exe"
ROOT = r"H:\door1\grid_v6main_20261002\gate"
MASTER = r"H:\door1\grid_v6main_20261002\gate\mv1_master.log"
CAP = 600

os.makedirs(ROOT, exist_ok=True)

def mlog(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + " " + msg
    print(line, flush=True)
    with open(MASTER, "a", encoding="utf-8") as f:
        f.write(line + "\n")

PAIRS = [
    # (case, N, m, seed, arm_args_extra)
    ("m4s7",  100000, 4, 7,    ["--m1"]),
    ("m5s7",  100000, 5, 7,    ["--m1"]),
    ("m3s7",  1000,   3, 7,    ["--nos"]),
]

def run_one(exe, tag, N, m, s, extra):
    # 旗标在调用处显式给出：gwin 侧 = extra+["--b1","1"]；v21 侧 = extra（无 --b1，证默认值生效）
    cmd = [exe, str(N), str(m), str(s), str(CAP)] + extra
    jl = os.path.join(ROOT, tag + ".jsonl")
    cmd += ["--jsonl", jl]
    lf = os.path.join(ROOT, tag + ".log")
    t0 = time.time()
    with open(lf, "w", encoding="utf-8", errors="replace") as f:
        p = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT)
    dt = time.time() - t0
    mlog(f"  run {tag} EXIT={p.returncode} ({dt:.0f}s)")
    return jl, p.returncode, dt

def final_of(jl):
    rec = None
    for line in open(jl, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except Exception: continue
        if isinstance(r, dict) and "pass" in r: rec = r
    return rec

FIELDS = ["pass", "breaks0", "breaks1", "size", "defects"]

if __name__ == "__main__":
    mlog("M-V1 gate start (serial pairs: gwin --b1 1 then v21 default-on)")
    results = {}
    for case, N, m, s, extra in PAIRS:
        mlog(f"[pair {case}] N={N} m={m} s={s}")
        jl_a, rc_a, dt_a = run_one(GWIN, f"mv1_gwin_{case}", N, m, s, extra + ["--b1", "1"])
        jl_b, rc_b, dt_b = run_one(V21,  f"mv1_v21_{case}",  N, m, s, extra)
        ra, rb = final_of(jl_a), final_of(jl_b)
        results[case] = (ra, rb, rc_a, rc_b, dt_a, dt_b)
    mlog("==== M-V1 JUDGMENT ====")
    all_ok = True
    for case, (ra, rb, rc_a, rc_b, dt_a, dt_b) in results.items():
        if ra is None or rb is None:
            mlog(f"  {case}: MISSING jsonl final record -> GATE BREAK (tool debt)")
            all_ok = False; continue
        diff = {k: (ra.get(k), rb.get(k)) for k in FIELDS if ra.get(k) != rb.get(k)}
        info = f"rot gwin={ra.get('rot')} v21={rb.get('rot')} (不进门)"
        if not diff:
            mlog(f"  {case}: 逐位同 pass={ra['pass']} b0={ra['breaks0']} b1={ra['breaks1']} size={ra['size']} defects={ra['defects']} | {info} | EXIT {rc_a}/{rc_b} dt {dt_a:.0f}/{dt_b:.0f}s")
        else:
            mlog(f"  {case}: DIFF {diff} -> GATE BREAK（任一破=实现缺陷，阻断全网格跑，判工具债照记）")
            all_ok = False
    mlog(f"M-V1 = {'PASS 三案例全逐位同 → 放行 M-V2 全网格' if all_ok else 'BREAK → 阻断全网格，工具债照记'}")
    with open(os.path.join(ROOT, "mv1_judgment.json"), "w", encoding="utf-8") as f:
        json.dump({c: {"gwin": r[0], "v21": r[1], "exit": (r[2], r[3]), "dt": (r[4], r[5])} for c, r in results.items()},
                  f, ensure_ascii=False, indent=1)
