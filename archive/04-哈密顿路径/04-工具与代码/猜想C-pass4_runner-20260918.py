# -*- coding: utf-8 -*-
"""pass4_runner.py · 猜想C闭合实验第四遍（2026-09-18，接续 conjectureC_20260917 三遍）

背景（0917 三遍后的剩余缺口，全部为 1e5 档）：
  m6@1e5 s13          首遍 cap=480 不闭合，pass2/3 未排到 → 满额未测
  m6@1e5 s7           pass3 cap=1800 引擎启动后会话中断，无结果 → 补跑
  m4@1e5 s42/s13/s7   首遍 cap=480 构造不完整，pass2 计划 cap=1200 未执行 → 满额未测
已定格点不重跑（预注册 §六 / 0917 存证）：
  m6@1e5 s42  PASS Λ=88（pass3 cap=1800，checkpoint.json）
  m5@1e5 ×3   并入 R1（cap=1400 引擎自然终止不闭合，breaks 42/29/33）
  m3 对照三档 capacity-KILLED（1e5 档 runner 外补跑 logs/cap_m3_N100000_s42.json）

本遍口径（冻结，不新增不收紧）：
  预算=预注册 §三 每实例 30 分钟墙钟满额 cap=1800（无全局 deadline 压力下的满额执行）；
  其余全部同 matrix_runner：图口径 networkx BA（边表已生成并 sha 校验与 0917 一致）、
  容量检验 cap_check、λ₂ 证书 lambda2、引擎 engine_v2_io_rounds、独立验证器 verify_strict_hp、
  Λ 计数口径 compute_lambda 同源复制。
本目录自包含：0917 目录仅 import/读取执行，零写入。
"""
import hashlib
import json
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
P17 = r"H:\door1\conjectureC_20260917"          # 只读引用：模块与引擎
sys.path.insert(0, P17)
import cap_check                                  # noqa: E402
import lambda2 as l2mod                           # noqa: E402

ENGINE = os.path.join(P17, "engine_v2_io_rounds.exe")
VERIFY = os.path.join(P17, "verify_strict_hp.py")
GENED = os.path.join(P17, "gen_edges.py")

BASELINE_L2 = {1000: 2.091192748157741, 10000: 2.003117257358329, 100000: 1.9846206062753835}
CP_PATH = os.path.join(BASE, "checkpoint_pass4.json")
LOG_PATH = os.path.join(BASE, "logs", "pass4_log.txt")

RESULTS = []


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def save_checkpoint():
    tmp = CP_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"results": RESULTS}, f, ensure_ascii=False, indent=1)
    os.replace(tmp, CP_PATH)


def sha256_file(fn):
    return hashlib.sha256(open(fn, "rb").read()).hexdigest()


def ensure_edges(m, N, seed):
    """边表已备（与 0917 同 sha 校验）；缺失则用同口径 gen_edges 生成到本目录。"""
    tag = f"m{m}_N{N}_s{seed}"
    local = os.path.join(BASE, f"edges_{tag}.txt")
    ref = os.path.join(P17, f"edges_{tag}.txt")
    if os.path.exists(local):
        return local, sha256_file(local), "local(与0917比对见sha字段)"
    r = subprocess.run([sys.executable, GENED, str(seed), str(N), str(m), local],
                       capture_output=True, text=True, cwd=BASE)
    if r.returncode != 0:
        raise RuntimeError(f"gen_edges fail: {r.stderr[-300:]}")
    return local, sha256_file(local), "fresh gen_edges"


def run_engine(efile, pfile, N, seed, cap):
    cmd = [ENGINE, "--edges", efile, "--out", pfile, "--N", str(N), "--seed", str(seed), "--cap", str(cap)]
    t0 = time.time()
    hard = cap * 1.35 + 45.0
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=hard, cwd=BASE)
        wall = time.time() - t0
        js = None
        for line in p.stdout.splitlines():
            if line.startswith("{"):
                js = json.loads(line)
        with open(os.path.join(BASE, "logs", f"engine_p4_m{N}_{seed}.log"), "w", encoding="utf-8") as f:
            f.write("CMD: " + " ".join(cmd) + "\n--stdout--\n" + p.stdout + "\n--stderr--\n" + p.stderr)
        return {"dnf": False, "wall_s": round(wall, 2), "engine": js, "rc": p.returncode}
    except subprocess.TimeoutExpired:
        return {"dnf": True, "wall_s": round(time.time() - t0, 2),
                "reason": f"engine hard timeout {hard:.0f}s"}


def verify_path(efile, pfile, N, tag):
    outj = os.path.join(BASE, "logs", f"verify_p4_{tag}.json")
    r = subprocess.run([sys.executable, VERIFY, efile, pfile, "--N", str(N), "--json", outj],
                       capture_output=True, text=True, cwd=BASE)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {"error": (r.stdout[-200:] + r.stderr[-200:])}


def compute_lambda(tr):
    """Λ 口径同 matrix_runner：构造端闭合=0；修补轮归零=轮数；LNS 第 k 轮归零=修补轮数+k；不闭合=None"""
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


def run_cell(m, N, seed, closure_cap):
    tag = f"m{m}_N{N}_s{seed}"
    cell = {"m": m, "N": N, "seed": seed, "tag": tag, "t_start": time.time()}
    log(f"=== CELL {tag} 开始 (cap={closure_cap}) ===")
    # ① 边表 + SHA
    efile, sha, how = ensure_edges(m, N, seed)
    cell["sha256"] = sha
    cell["gen"] = f"{how}; ref0917_match={os.path.exists(os.path.join(P17, 'edges_' + tag + '.txt')) and sha256_file(os.path.join(P17, 'edges_' + tag + '.txt')) == sha}"
    # ② 容量检验
    edges = []
    for line in open(efile):
        p = line.split()
        if p:
            u, v = int(p[0]), int(p[1])
            if u != v:
                edges.append((u, v))
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
    # ④ 闭合尝试（满额预算）
    pfile = os.path.join(BASE, f"path_{tag}.txt")
    er = run_engine(efile, pfile, N, seed, closure_cap)
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
    vr = verify_path(efile, pfile, N, tag)
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
    plan = [
        (6, 100000, 13, 1800.0),
        (6, 100000, 7, 1800.0),
        (4, 100000, 42, 1800.0),
        (4, 100000, 13, 1800.0),
        (4, 100000, 7, 1800.0),
    ]
    log("== 第四遍启动（满额 cap=1800）==")
    for m, N, s, cap in plan:
        run_cell(m, N, s, cap)
    with open(os.path.join(BASE, "summary_pass4.json"), "w", encoding="utf-8") as f:
        json.dump({"results": RESULTS}, f, ensure_ascii=False, indent=1)
    log("== 第四遍结束 ==")


if __name__ == "__main__":
    main()
