# -*- coding: utf-8 -*-
"""matrix_runner.py · 猜想C闭合实验矩阵顺序执行器（2026-09-17）

冻结口径来源：预注册-猜想C闭合实验-v1.0-20260916.md §二/§三/§四。
总墙钟预算 100 分钟（矩阵启动时冻结 deadline=start+6000s），到点即停；
已完成格点即时落 checkpoint.json（原子写）；未跑格点标"未跑（预算）"。
每实例引擎硬上限 30 分钟（预注册 §三），实际各层预算更小、如实记录。

层预算策略（runner 冻结，逐格记录）：
  N=1e3 层引擎 cap=90s；N=1e4 层 cap=180s；N=1e5 层 cap=min(480, 剩余预算/剩余1e5闭合格数)。
λ 口径：Λ=0（构造端闭合）或 =断口首次归零的轮数（修补主循环轮数，若在 LNS 第 k 轮归零
  则 Λ=修补轮数+k）；不闭合→Λ=None。rot=旋转执行次数（与 R1 同口径一并记录）。
"""
import hashlib
import json
import os
import subprocess
import sys
import time

import cap_check
import lambda2 as l2mod

BASE = os.path.dirname(os.path.abspath(__file__))
DEADLINE = None
CP_PATH = os.path.join(BASE, "checkpoint.json")
LOG_PATH = os.path.join(BASE, "logs", "matrix_log.txt")

BASELINE_L2 = {1000: 2.091192748157741, 10000: 2.003117257358329, 100000: 1.9846206062753835}
R1_ROWS = {  # m=5@1e5 三格点，R1 结案并入（m5e5复现执行报告-20260917.md）
    42: {"breaks0": 45, "breaks1": 42, "rot": 5436, "wall_s": 689.0, "closed": False, "pass": False},
    13: {"breaks0": 40, "breaks1": 29, "rot": 5152, "wall_s": 651.4, "closed": False, "pass": False},
    7:  {"breaks0": 43, "breaks1": 33, "rot": 5149, "wall_s": 558.1, "closed": False, "pass": False},
}

RESULTS = []
START = None


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def save_checkpoint():
    tmp = CP_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"start": START, "now": time.time(), "results": RESULTS}, f, ensure_ascii=False, indent=1)
    os.replace(tmp, CP_PATH)


def sha256_file(fn):
    return hashlib.sha256(open(fn, "rb").read()).hexdigest()


def gen_edges(m, N, seed, out):
    r = subprocess.run([sys.executable, "gen_edges.py", str(seed), str(N), str(m), out],
                       capture_output=True, text=True, cwd=BASE)
    meta = json.loads(r.stdout.strip().splitlines()[-1])
    return meta


def run_engine(efile, pfile, N, seed, cap):
    exe = os.path.join(BASE, "engine_v2_io_rounds.exe")
    cmd = [exe, "--edges", efile, "--out", pfile, "--N", str(N), "--seed", str(seed), "--cap", str(cap)]
    t0 = time.time()
    hard = min(cap * 1.35 + 45.0, max(30.0, (DEADLINE - time.time()) - 45.0))
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=hard, cwd=BASE)
        wall = time.time() - t0
        js = None
        for line in p.stdout.splitlines():
            if line.startswith("{"):
                js = json.loads(line)
        with open(os.path.join(BASE, "logs", f"engine_{efile.replace('.txt','').replace('edges_','')}_{seed}.log"), "w", encoding="utf-8") as f:
            f.write("CMD: " + " ".join(cmd) + "\n--stdout--\n" + p.stdout + "\n--stderr--\n" + p.stderr)
        return {"dnf": False, "wall_s": round(wall, 2), "engine": js, "rc": p.returncode}
    except subprocess.TimeoutExpired:
        return {"dnf": True, "wall_s": round(time.time() - t0, 2),
                "reason": f"engine hard timeout {hard:.0f}s"}


def verify_path(efile, pfile, N, tag):
    outj = os.path.join(BASE, "logs", f"verify_{tag}.json")
    r = subprocess.run([sys.executable, "verify_strict_hp.py", efile, pfile, "--N", str(N), "--json", outj],
                       capture_output=True, text=True, cwd=BASE)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {"error": r.stdout[-200:] + r.stderr[-200:]}


def compute_lambda(tr):
    """Λ 口径：构造端闭合=0；修补轮归零=轮数；LNS 第 k 轮归零=修补轮数+k；不闭合=None"""
    if tr["engine"] is None:
        return None
    e = tr["engine"]
    if e["breaks0"] == 0 and e["pass"]:
        return 0
    tf, tl = e.get("trace_fixp", []), e.get("trace_lns", [])
    for i, b in enumerate(tf):
        if b == 0:
            return i + 1
    for i, b in enumerate(tl):
        if b == 0:
            return len(tf) + i + 1
    return None


def run_cell(m, N, seed, closure_cap, reuse_r1_edges=False):
    tag = f"m{m}_N{N}_s{seed}"
    cell = {"m": m, "N": N, "seed": seed, "tag": tag}
    log(f"=== CELL {tag} 开始 (剩余 {DEADLINE - time.time():.0f}s, 引擎cap={closure_cap}) ===")
    cell["t_start"] = time.time()
    # ① 生成图 + 边表 SHA
    efile = os.path.join(BASE, f"edges_{tag}.txt")
    if reuse_r1_edges:
        cell["gen"] = "reuse R1 edge file (m5e5_run_20260917, sha见其meta)"
    else:
        cell["gen"] = gen_edges(m, N, seed, efile)
    cell["sha256"] = sha256_file(efile)
    # ② 容量检验
    edges = []
    mx = -1
    for line in open(efile):
        p = line.split()
        if p:
            u, v = int(p[0]), int(p[1])
            if u != v:
                edges.append((u, v)); mx = max(mx, u, v)
    cell["cap"] = cap_check.cap_check(edges, N, m)
    log(f"  capacity: {cell['cap']['verdict']} |L|={cell['cap']['L_size']} flow={cell['cap']['flow']} demand={cell['cap']['demand']} LB={cell['cap']['breaks_lower_bound']} ({cell['cap']['sec']}s)")
    if cell["cap"]["verdict"] == "capacity-KILLED":
        cell["verdict"] = "capacity-KILLED"
        cell["wall_s"] = round(time.time() - cell["t_start"], 2)
        RESULTS.append(cell); save_checkpoint()
        return
    # ③ λ₂ 证书
    lam2, sec2, method, resid = l2mod.lambda2_cert(edges, N)
    line_v = 0.5 * BASELINE_L2[N]
    cell["lambda2"] = {"lambda2": lam2, "sec": round(sec2, 3), "method": method, "residual": resid,
                       "baseline_N4_s42": BASELINE_L2[N], "pass_line": line_v, "l2_pass": bool(lam2 >= line_v)}
    log(f"  lambda2={lam2:.6f} 基准线={line_v:.6f} -> {'过' if lam2 >= line_v else 'FAIL'} (残差{resid})")
    if not cell["lambda2"]["l2_pass"]:
        cell["verdict"] = "lambda2-FAIL"
        cell["wall_s"] = round(time.time() - cell["t_start"], 2)
        RESULTS.append(cell); save_checkpoint()
        return
    # ④⑤ 闭合尝试
    if closure_cap is None:
        cell["verdict"] = "closure-并入R1"
        cell["r1"] = R1_ROWS[seed]
        cell["wall_s"] = round(time.time() - cell["t_start"], 2)
        RESULTS.append(cell); save_checkpoint()
        return
    if time.time() > DEADLINE - 120:
        cell["verdict"] = "未跑（预算：closure未启动）"
        cell["wall_s"] = round(time.time() - cell["t_start"], 2)
        RESULTS.append(cell); save_checkpoint()
        return
    pfile = os.path.join(BASE, f"path_{tag}.txt")
    er = run_engine(f"edges_{tag}.txt", pfile, N, seed, closure_cap)
    cell["engine_run"] = er
    if er["dnf"]:
        cell["verdict"] = f"DNF({er['reason']})"
        cell["wall_s"] = round(time.time() - cell["t_start"], 2)
        RESULTS.append(cell); save_checkpoint()
        return
    e = er["engine"]
    cell["engine"] = e
    cell["Lambda"] = compute_lambda(cell)
    cell["pass"] = e["pass"]
    vr = verify_path(f"edges_{tag}.txt", pfile, N, tag)
    cell["verify"] = {"strict_pass": vr.get("strict_pass"), "甲": vr.get("breaks_甲"), "乙闭合": vr.get("closed_乙")}
    cross = (vr.get("breaks_甲") == e["breaks1"])
    cell["verify"]["cross_engine_breaks1"] = cross
    cell["verdict"] = "PASS" if (e["pass"] and vr.get("strict_pass")) else "不闭合"
    cell["engine_cap_given"] = closure_cap
    cell["wall_s"] = round(time.time() - cell["t_start"], 2)
    log(f"  closure: breaks {e['breaks0']}->{e['breaks1']} pass={e['pass']} rot={e['rot']} Λ={cell['Lambda']} "
        f"rounds_fixp={e.get('rounds_fixp')} rounds_lns={e.get('rounds_lns')} 验证器甲={vr.get('breaks_甲')} cross={cross} wall={cell['wall_s']}s")
    RESULTS.append(cell); save_checkpoint()


def main():
    global DEADLINE, START
    START = time.time()
    DEADLINE = START + 6000.0  # 100 分钟总预算
    log(f"矩阵启动，deadline={time.strftime('%H:%M:%S', time.localtime(DEADLINE))}")

    # ---- 层1：N=1e3（对照先行）----
    cap1 = 90.0
    run_cell(3, 1000, 42, cap1)
    for m in (4, 5, 6):
        for s in (42, 13, 7):
            run_cell(m, 1000, s, cap1)

    # ---- 层3提前（1e5 判定性最强，动态预算）----
    t3_cells = [(4, 42), (4, 13), (4, 7), (6, 42), (6, 13), (6, 7)]
    for i, (m, s) in enumerate(t3_cells):
        left = len(t3_cells) - i
        share = (DEADLINE - time.time() - 300.0 - left * 90.0) / left  # 预留300s给层2收尾与R1行
        cap3 = max(120.0, min(480.0, share))
        if time.time() > DEADLINE - 180:
            log("预算耗尽，剩余1e5闭合格点标未跑")
            break
        run_cell(m, 100000, s, round(cap3, 1))

    # ---- 层2：N=1e4 ----
    cap2 = 180.0
    run_cell(3, 10000, 42, cap2)
    for m in (4, 5, 6):
        for s in (42, 13, 7):
            if time.time() > DEADLINE - 60:
                log("预算耗尽，剩余1e4格点未跑")
                break
            run_cell(m, 10000, s, cap2)

    # ---- R1 并入行：m5@1e5（仅补 capacity+λ₂，不重跑闭合）----
    for s in (42, 13, 7):
        run_cell(5, 100000, s, None, reuse_r1_edges=True)

    # ---- 汇总 ----
    summary = {"start": START, "end": time.time(), "total_s": round(time.time() - START, 1),
               "n_cells": len(RESULTS)}
    with open(os.path.join(BASE, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": RESULTS}, f, ensure_ascii=False, indent=1)
    log(f"矩阵结束：{len(RESULTS)} 格点，总耗时 {summary['total_s']}s")


if __name__ == "__main__":
    main()
