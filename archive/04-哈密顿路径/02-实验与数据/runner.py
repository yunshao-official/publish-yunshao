# -*- coding: utf-8 -*-
"""runner.py · 预注册 m5e5 三 seed 顺序跑（外部硬限 1800s/seed，超时=DNF）"""
import json
import subprocess
import sys
import time

ENGINE = "./engine_v2_io.exe"
CAP_S = 1400.0     # 引擎内部软预算（构造0.35/修补0.55/LNS0.30 最坏串联≈1680s）
HARD_S = 1800.0    # 预注册冻结：每 seed 30 分钟墙钟硬上限


def run_one(seed):
    efile = f"edges_m5_N100000_s{seed}.txt"
    pfile = f"path_m5_N100000_s{seed}.txt"
    logf = f"run_s{seed}_engine.log"
    t0 = time.time()
    cmd = [ENGINE, "--edges", efile, "--out", pfile, "--N", "100000",
           "--seed", str(seed), "--cap", str(CAP_S)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=HARD_S)
        wall = time.time() - t0
        with open(logf, "w") as f:
            f.write("CMD: " + " ".join(cmd) + "\n--stdout--\n" + p.stdout + "\n--stderr--\n" + p.stderr)
        js = None
        for line in p.stdout.splitlines():
            if line.startswith("{"):
                js = json.loads(line)
        rec = {"seed": seed, "dnf": False, "wall_s": round(wall, 3),
               "engine_json": js, "rc": p.returncode,
               "stderr_head": p.stderr.strip()[:500],
               "path_file": pfile if p.returncode == 0 or pfile else pfile}
        return rec
    except subprocess.TimeoutExpired as e:
        wall = time.time() - t0
        out = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = (e.stderr or b"").decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        with open(logf, "w") as f:
            f.write("CMD: " + " ".join(cmd) + "\n--TIMEOUT--\n" + str(e) + "\n--stdout partial--\n" + out + "\n--stderr partial--\n" + err)
        return {"seed": seed, "dnf": True, "wall_s": round(wall, 3),
                "reason": f"hard timeout {HARD_S}s (预注册30分钟硬上限)", "path_file": pfile}


def main():
    results = []
    for seed in [42, 13, 7]:
        print(f"=== seed {seed} start {time.strftime('%H:%M:%S')} ===", flush=True)
        rec = run_one(seed)
        results.append(rec)
        print(json.dumps(rec, ensure_ascii=False), flush=True)
        with open("runs_summary.json", "w") as f:
            json.dump(results, f, indent=1)
    n_pass = sum(1 for r in results if not r["dnf"] and r["engine_json"] and r["engine_json"]["pass"])
    print(f"=== ALL DONE pass={n_pass}/3 ===", flush=True)


if __name__ == "__main__":
    main()
