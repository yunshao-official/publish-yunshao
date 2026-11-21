# verify_hp v1.0 (2026-09-27) — 严格HP独立三关验证器（甲）
# 工作包-HP工具链 v1.0 成件 | 三关: 长度=N ∧ 顶点无重复 ∧ 每步真边
# 用法: python verify_hp.py --edges graph.edges --path path.txt
# 退出码: 0=PASS 1=FAIL 2=IO错误 —— 独立于任何求解器，验收强制用本件（禁用求解器自带判定替代）
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edges", required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--N", type=int, default=None, help="缺省=由边表推断最大节点数+1")
    a = ap.parse_args()
    edges = set()
    nmax = -1
    for l in open(a.edges):
        parts = l.split()
        if len(parts) < 2:
            continue
        u, v = int(parts[0]), int(parts[1])
        edges.add((min(u, v), max(u, v)))
        nmax = max(nmax, u, v)
    N = a.N if a.N is not None else nmax + 1
    path = [int(x) for x in open(a.path) if x.strip()]
    c1 = len(path) == N
    c2 = len(set(path)) == len(path)
    c3 = all((min(path[i], path[i+1]), max(path[i], path[i+1])) in edges for i in range(len(path)-1))
    ok = c1 and c2 and c3
    print(f"三关甲: 长度={len(path)}/{N}({'✓' if c1 else '✗'}) 无重复({'✓' if c2 else '✗'}) 全真边({'✓' if c3 else '✗'}) → {'PASS' if ok else 'FAIL'}")
    sys_exit = 0 if ok else 1
    raise SystemExit(sys_exit)

if __name__ == "__main__":
    main()
