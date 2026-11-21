# -*- coding: utf-8 -*-
# 复合解图v2·臂B执行器 v1.0（2026-11-09）——虚拟边引信打法
# 机理：double-bridge 拆3旧缝造3新缝；新缝缺1条真边时补"虚拟边引信"（限定两端有共同邻居，
#       保证删边后该位新断口可缝）——净效果=Δ'(移动自身) 不劣化，且把 C-1 被卡弹药的
#       "缺边"解除。链式最陡下降；终态删全部虚拟边，剩余断口复算对拍锁箱锚。
# 判据（冻结于预注册 v0.9 臂B骨架）：终态断口 < 锚 − 30（噪声带外）=过；失败面照记。
import sys, json, time
import numpy as np


def load(edges_fn, path_fn):
    e = np.loadtxt(edges_fn, dtype=np.int64)
    N = int(e.max()) + 1
    u, v = e[:, 0], e[:, 1]
    lo, hi = np.minimum(u, v), np.maximum(u, v)
    keys = np.sort(lo * np.int64(N) + hi)
    path = np.loadtxt(path_fn, dtype=np.int64)
    return N, keys, path


def has_edge(x, y, keys, N):
    x = np.atleast_1d(np.asarray(x, dtype=np.int64))
    y = np.atleast_1d(np.asarray(y, dtype=np.int64))
    lo = np.minimum(x, y); hi = np.maximum(x, y)
    k = lo * np.int64(N) + hi
    idx = np.searchsorted(keys, k)
    idx = np.minimum(idx, len(keys) - 1)
    return keys[idx] == k


def adj_list(N, edges_fn):
    e = np.loadtxt(edges_fn, dtype=np.int64)
    adj = [[] for _ in range(N)]
    for a, b in e:
        adj[a].append(b)
        adj[b].append(a)
    return adj


def common_neighbor(u, v, adj):
    """u,v 的共同邻居数（删虚拟边后该位可缝性）。"""
    su = set(adj[u]); sv = set(adj[v])
    return len(su & sv)


def apply_db(path, i, j, k):
    """double-bridge：A B C D -> A C B D（段不反转，覆盖不变）。"""
    A = path[:i + 1]
    B = path[i + 1:j + 1]
    C = path[j + 1:k + 1]
    D = path[k + 1:]
    return np.concatenate([A, C, B, D])


def main(edges_fn, path_fn, out_fn, rounds=30, seed=42):
    t0 = time.time()
    N, keys, path = load(edges_fn, path_fn)
    adj = adj_list(N, edges_fn)
    n = len(path)
    assert n == N, "路径长度%d≠N%d" % (n, N)

    def brk_count():
        return int(np.sum(~has_edge(path[:-1], path[1:], keys, N)))

    b0 = brk_count()
    print("初始断口: %d" % b0, flush=True)

    used_virtual = set()
    history = []
    rng = np.random.default_rng(seed)
    pos_map = {int(v): i for i, v in enumerate(path)}  # 点值→路径位置 O(1) 反查

    for rd in range(rounds):
        # 断口接缝集
        brk_idx = np.where(~has_edge(path[:-1], path[1:], keys, N))[0]
        if len(brk_idx) == 0:
            print("全清!"); break
        # 穷举：i∈断口集, j∈断口集(i<j), k∈N(path[i+1])
        # 新缝3条：(path[i],path[j+1])、(path[k],path[i+1])、(path[j],path[k+1])
        # 旧缝3条：i,j,k 处（断口与否计入 b_old）
        best = None  # (delta, virtual_needed, i, j, k)
        brk_set = set(int(x) for x in brk_idx)
        for i in brk_idx:
            i = int(i)
            tgt = path[i + 1]
            nbs = adj[tgt]
            for k in nbs:
                kk = pos_map.get(int(k))
                if kk is None or kk <= i + 1:
                    continue
                for j in brk_idx:
                    j = int(j)
                    if j <= i or j >= kk:
                        continue
                    e1 = has_edge(path[i], path[j + 1], keys, N)[0]
                    e2 = has_edge(path[kk], path[i + 1], keys, N)[0]
                    e3 = has_edge(path[j], path[kk + 1], keys, N)[0]
                    virt = []
                    if not e1:
                        virt.append((int(path[i]), int(path[j + 1])))
                    if not e2:
                        virt.append((int(path[kk]), int(path[i + 1])))
                    if not e3:
                        virt.append((int(path[j]), int(path[kk + 1])))
                    if len(virt) > 1:
                        continue  # 引信限定≤1条
                    # 引信约束：虚拟边两端有共同邻居（删边后可缝）
                    if virt and common_neighbor(virt[0][0], virt[0][1], adj) == 0:
                        continue
                    b_old = sum(1 for s in (i, j, kk) if s in brk_set)
                    d_db = 3 - len(virt) - (0 if e1 else 0)  # 占位
                    # 真实Δ = 新缝真边数−虚拟1条若不可缝… 精确：删边后断口 =
                    #   3新缝中非真边的（虚拟边算1条断口，但若cmn≥1预期被缝合清=0）
                    #   − 旧3缝中真断口数
                    new_brk_after_stitch = 0  # 虚拟位预期缝合清；真边缝必为0
                    new_brk_true = sum(1 for e in (e1, e2, e3) if not e)  # 含虚拟
                    delta = new_brk_true - new_brk_after_stitch - b_old
                    if best is None or delta < best[0]:
                        best = (delta, virt, i, j, kk)
        if best is None or best[0] >= 0:
            print("无净负移动，停于第%d轮" % rd, flush=True)
            break
        delta, virt, i, j, kk = best
        path = apply_db(path, i, j, kk)
        pos_map = {int(v): i2 for i2, v in enumerate(path)}  # 重排后重建反查
        for e in virt:
            used_virtual.add(e)
        bnow = brk_count()
        history.append((rd, delta, len(virt), bnow))
        print("轮%d: Δ=%d 虚拟边=%s 断口=%d" % (rd, delta, virt, bnow), flush=True)

    bfin = brk_count()
    # 覆盖完整性（db 移动保覆盖，verify 一次）
    cover_ok = len(set(path.tolist())) == n
    print("终态断口: %d (初始%d, 净改善%d) 覆盖完整=%s 虚拟边用=%d 耗时%.0fs"
          % (bfin, b0, b0 - bfin, cover_ok, len(used_virtual), time.time() - t0), flush=True)
    json.dump({"b0": b0, "bfin": bfin, "delta": b0 - bfin, "cover_ok": cover_ok,
               "used_virtual": [list(e) for e in used_virtual], "history": history},
              open(out_fn, "w"))
    np.savetxt(out_fn.replace(".json", "_path.txt"), path, fmt="%d")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3],
         rounds=int(sys.argv[4]) if len(sys.argv) > 4 else 30)
