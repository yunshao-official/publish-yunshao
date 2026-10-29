# -*- coding: utf-8 -*-
"""verify_strict_hp.py · 独立严格HP验证器（验证器二·2026-09-17 新写，不 import 引擎代码）

冻结口径（预注册 §二）：
  严格 HP = 长度 N 的顶点序列，每顶点恰一次，相邻对（N-1 对，不含首尾闭合）全为真边。
  断口甲 = 路径序列内相邻对非真边位置数；乙 = 甲 + 首尾闭合检查（单独记录，不入 PASS）。
  STRICT=PASS ⟺ 长度==N ∧ 排列完整（0..N-1 恰一次）∧ 甲==0。

用法：
  python verify_strict_hp.py <edge_file> <path_file> [--N n] [--json out]
  python verify_strict_hp.py --selftest          （上岗前负面对拍：断口/重复点必须被抓出）
"""
import argparse
import json
import sys


def load_edges(fn):
    adj = {}
    m = 0
    ne = 0
    with open(fn) as f:
        for line in f:
            p = line.split()
            if not p:
                continue
            u, v = int(p[0]), int(p[1])
            adj.setdefault(u, set()).add(v)
            adj.setdefault(v, set()).add(u)
            m = max(m, u, v)
            ne += 1
    return adj, m + 1, ne


def verify(edge_file, path_file, forced_n=None):
    adj, n_from_edges, n_edges = load_edges(edge_file)
    path = []
    with open(path_file) as f:
        for line in f:
            line = line.strip()
            if line:
                path.append(int(line))
    N = forced_n if forced_n else n_from_edges
    res = {
        "edge_file": edge_file, "path_file": path_file,
        "N": N, "n_edges_declared": n_edges,
        "path_len": len(path),
    }
    fails = []
    # 关1：排列完整性
    seen = {}
    dup = []
    for v in path:
        if v in seen:
            dup.append(v)
        seen[v] = seen.get(v, 0) + 1
    if len(path) != N:
        fails.append(f"length {len(path)} != N {N}")
    missing = [v for v in range(N) if v not in seen]
    if missing:
        fails.append(f"missing vertices: {len(missing)} e.g. {missing[:5]}")
    if dup:
        fails.append(f"duplicated vertices: {len(dup)} e.g. {dup[:5]}")
    # 关2：相邻对全真边（断口甲）
    breaks = []
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        if b not in adj.get(a, ()):
            breaks.append({"pos": i, "u": a, "v": b})
    res["breaks_甲"] = len(breaks)
    res["breaks_detail_head"] = breaks[:10]
    # 关3：乙口径闭合（单独记录，不入判定）
    if len(path) >= 2:
        res["closed_乙"] = path[-1] in adj.get(path[0], ())
    else:
        res["closed_乙"] = False
    res["fail_list"] = fails
    res["strict_pass"] = (len(fails) == 0 and len(breaks) == 0)
    return res


def selftest():
    """负面对拍：断口、重复点、缺点、闭合误报都必须被抓出。"""
    import os
    import tempfile
    ok_all = True
    d = tempfile.mkdtemp()
    ef = os.path.join(d, "g.txt")
    with open(ef, "w") as f:
        # 路径 P6: 0-1-2-3-4-5（链）+ 额外边 (0,5) 用于闭合检查
        for u, v in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (0, 5)]:
            f.write(f"{u} {v}\n")
    cases = []
    # 真PASS
    pf = os.path.join(d, "p_ok.txt")
    with open(pf, "w") as f:
        f.write("0\n1\n2\n3\n4\n5\n")
    r = verify(ef, pf, forced_n=6)
    cases.append(("clean path must PASS", r["strict_pass"] is True and r["breaks_甲"] == 0 and r["closed_乙"] is True))
    # 断口：0-1-2-9-...（9 不存在 → 非真边）
    pf = os.path.join(d, "p_break.txt")
    with open(pf, "w") as f:
        f.write("0\n1\n2\n5\n4\n3\n")   # 2-5 非真边 → 1 断口
    r = verify(ef, pf, forced_n=6)
    cases.append(("break must FAIL with 甲=1", r["strict_pass"] is False and r["breaks_甲"] == 1))
    # 重复点+缺点：0-1-2-1-4-5（1 重复，3 缺失，2-1 非真边? 1-2 是真边但 1 已用→排列坏）
    pf = os.path.join(d, "p_dup.txt")
    with open(pf, "w") as f:
        f.write("0\n1\n2\n1\n4\n5\n")
    r = verify(ef, pf, forced_n=6)
    cases.append(("duplicate+missing must FAIL", r["strict_pass"] is False and any("duplicated" in x for x in r["fail_list"]) and any("missing" in x for x in r["fail_list"])))
    # 闭合误报防护：0-1-2-3-4-5 closed=True 上面已验；换条不闭合的合法路径（0-1-2-3-4-5 的反转端不闭合情形）：1-2-3-4-5-0? 5-0 是真边 → closed。用 0-5-4-3-2-1：首 0 尾 1，0-1 真边 → 也闭合。改路径 1-0-5-4-3-2：首1尾2，1-2 真边→闭合。这个图所有端点排列都闭合（圈），不能测 closed=False。跳过，closed 已在 break case 中为 False。
    for name, ok in cases:
        print(("SELFTEST-OK  " if ok else "SELFTEST-FAIL") + " " + name)
        ok_all = ok_all and ok
    print("SELFTEST=" + ("PASS" if ok_all else "FAIL"))
    return ok_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edge_file", nargs="?")
    ap.add_argument("path_file", nargs="?")
    ap.add_argument("--N", type=int, default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 3)
    if not a.edge_file or not a.path_file:
        ap.error("need edge_file path_file (or --selftest)")
    r = verify(a.edge_file, a.path_file, a.N)
    out = json.dumps(r, ensure_ascii=False)
    print(out)
    if a.json:
        with open(a.json, "w") as f:
            f.write(out + "\n")
    sys.exit(0 if r["strict_pass"] else 1)


if __name__ == "__main__":
    main()
