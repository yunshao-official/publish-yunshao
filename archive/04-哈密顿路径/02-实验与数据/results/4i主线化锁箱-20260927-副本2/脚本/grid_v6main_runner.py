# -*- coding: utf-8 -*-
"""
grid_v6main_runner.py — 网格v6 主线化实现轮执行器（哈密顿线 4i 专轮）
判据正本 = 预注册---b1主线化网格v6程序性确认轮-v1.0-20260921 §三/§四（冻结，未改一字）：
  M-V2 全网格账：90 案例重跑（m=3 按经验政策 base 臂 18 跑+m1 carried_v5；m≥4 默认 --m1+b1 开）
  ——65/90 对网格 v5 零回退+m4@1e5 构造完整率 6/6 维持+m5@1e5 6/6 全零维持+m3@1e3 交付 Σ608 维持。
口径：m≥4 = `--m1`（不带 --b1 旗标——主线化的全部意义=默认行为生效；M-V1 对拍门已证默认≡gwin --b1 1）；
  m=3 = `--nos`（base 臂，与 v5 同）。引擎 = m1v2 v2.1 正本（m1v2_v21_main.exe，
  md5=8ec8dba23e0da329db774696adee57a1，gwin v1.0 全量逐字+g_b1 默认 1）。
工具纪律（round9 runner 全量继承）：Python subprocess 真实退出码直捕（$? 坑根治）；每案例独立 jsonl
  即检查点（已存在且可解析且含 pass 字段→跳过，断点续跑）；分片批次片内并发池；执行顺序=先 1e5 档
  （m4@1e5 par=2 保护完成余量敏感带）再 1e4 档再 1e3 档；watchdog 双保险 cap+120s。
用法: python grid_v6main_runner.py --batch m5e5   （或 --all 依序全跑；--list 列批次）
"""
import os, subprocess, sys, time, json

EXE = r"H:\door1\grid_v6main_20261002\m1v2_v21_main.exe"
ROOT = r"H:\door1\grid_v6main_20261002"
JSONL = os.path.join(ROOT, "jsonl")
PATHS = os.path.join(ROOT, "path")
LOGS = os.path.join(ROOT, "logs")
SEEDS = [7, 13, 21, 42, 99, 2024]
CAP = 600
MASTER = os.path.join(ROOT, "run_v6main_master.log")

os.makedirs(JSONL, exist_ok=True); os.makedirs(PATHS, exist_ok=True); os.makedirs(LOGS, exist_ok=True)

def mlog(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S") + " " + msg
    print(line, flush=True)
    with open(MASTER, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def runs_for(N, m, arm, with_out=False):
    out = []
    for s in SEEDS:
        tag = f"g6_N{N}_m{m}_s{s}_{arm}"
        cmd = [EXE, str(N), str(m), str(s), str(CAP)]
        if arm == "main":
            cmd += ["--m1"]              # b1 默认开（主线化；不带 --b1 旗标）
        else:  # base
            cmd += ["--nos"]             # K2 经验政策：m=3 不启 m1 臂（b1 默认开但 --nos 不进 m1 管线）
        cmd += ["--jsonl", os.path.join(JSONL, tag + ".jsonl")]
        if with_out:
            cmd += ["--out", os.path.join(PATHS, tag + "_path.txt")]
        out.append((tag, cmd))
    return out

BATCHES = {
    # ---- 1e5 档（判据主档优先；m4@1e5 par=2 保护 B1 完成余量）----
    "m5e5":   (3,  runs_for(100000, 5, "main", with_out=True)),
    "m4e5":   (2,  runs_for(100000, 4, "main", with_out=True)),
    "m6m7e5": (4,  runs_for(100000, 6, "main") + runs_for(100000, 7, "main")),
    "m3e5":   (6,  runs_for(100000, 3, "base")),
    # ---- 1e4 档 ----
    "m4m5e4": (6,  runs_for(10000, 4, "main") + runs_for(10000, 5, "main")),
    "m6m7e4": (6,  runs_for(10000, 6, "main") + runs_for(10000, 7, "main")),
    "m3e4":   (6,  runs_for(10000, 3, "base")),
    # ---- 1e3 档 ----
    "m4567e3":(8,  runs_for(1000, 4, "main") + runs_for(1000, 5, "main") + runs_for(1000, 6, "main") + runs_for(1000, 7, "main")),
    "m3e3":   (6,  runs_for(1000, 3, "base")),
}

def jl_done(jl):
    """检查点：jsonl 存在、可解析、末行含 pass 字段才算完成。"""
    if not (os.path.exists(jl) and os.path.getsize(jl) > 0):
        return False
    ok = False
    try:
        with open(jl, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if isinstance(r, dict) and "pass" in r:
                    ok = True
    except Exception:
        return False
    return ok

def run_batch(name, par):
    _, jobs = BATCHES[name]
    pending, done = [], []
    for tag, cmd in jobs:
        jl = cmd[cmd.index("--jsonl") + 1]
        if jl_done(jl):
            done.append(tag); continue
        pending.append((tag, cmd))
    mlog(f"[batch {name}] total={len(jobs)} skip(done)={len(done)} todo={len(pending)} par={par}")
    t0 = time.time()
    running, results = [], []
    while pending or running:
        while pending and len(running) < par:
            tag, cmd = pending.pop(0)
            lf = open(os.path.join(LOGS, tag + ".log"), "w", encoding="utf-8", errors="replace")
            p = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, cwd=ROOT)
            running.append((tag, p, lf, time.time()))
            mlog(f"  start {tag}")
        still = []
        for tag, p, lf, ts in running:
            if p.poll() is None:
                if time.time() - ts > CAP + 120:   # 双保险：cap600+余量（watchdog）
                    p.kill(); lf.close()
                    results.append((tag, "TIMEOUT-KILL", None))
                    mlog(f"  KILL(timeout) {tag}")
                else:
                    still.append((tag, p, lf, ts))
            else:
                lf.close()
                rc = p.returncode   # 真实退出码直捕（引擎 pass?0:1）
                results.append((tag, f"EXIT{rc}", time.time() - ts))
                mlog(f"  done  {tag} -> EXIT{rc} ({time.time()-ts:.0f}s)")
        running = still
        if running or pending:
            time.sleep(2)
    ok = sum(1 for _, r, _ in results if r == "EXIT0")
    mlog(f"[batch {name}] ALL DONE in {time.time()-t0:.0f}s; EXIT0={ok}/{len(results)}（pass=false 案例 EXIT1=预期，判定以 jsonl pass 字段为准）")
    return results

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        for k, (par, jobs) in BATCHES.items():
            print(k, "par=", par, "runs=", len(jobs))
        sys.exit(0)
    names = []
    if "--all" in args:
        names = list(BATCHES.keys())
    else:
        i = args.index("--batch"); names = [args[i + 1]]
    for nm in names:
        run_batch(nm, BATCHES[nm][0])
    mlog(f"[runner] batches finished: {names}")
