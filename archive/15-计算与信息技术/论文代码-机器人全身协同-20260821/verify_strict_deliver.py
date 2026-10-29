#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_strict_deliver.py — YUNSHAO Hamilton Path Verifier · Open-Source Edition
Independent strict-HP verifier (verifier separated from the generator, runs as its own process).
Three strict conditions: L==V + no repeated nodes + all edges are real graph edges.
Usage: python verify_strict_deliver.py <report_file> [graph_file]
  - reads the path from the [path] section of the report
  - with graph_file, verifies all edges against the original graph; otherwise checks L==V + no repeats
Selftest: python verify_strict_deliver.py --selftest
"""
import sys, os, re

def load_path_from_report(report_file):
    """Read the path sequence from the [path] section of the solver report"""
    with open(report_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    # 检查status
    m = re.search(r'status:\s*(\S+)', content)
    status = m.group(1) if m else 'unknown'
    if status in ('no_solution', 'construction_failed'):
        return None, status, f"报告状态={status}，无路径可验证"
    marker = "\n[path]"
    idx = content.find(marker)
    if idx < 0:
        if content.startswith("[path]"):
            body = content[len("[path]"):]
        else:
            return None, status, "报告中未找到[path]段"
    else:
        body = content[idx + len(marker):]
    # 仅整行 [xxx] 作段标记终止符；行内 [xxx] token 视为垃圾内容 → 报错（fail-closed）
    seq = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith('[') and line.endswith(']'):
            break  # 后续是其他段，停止读取
        for tok in line.split():
            if tok.startswith('[') or tok.endswith(']'):
                raise ValueError(
                    f"[path] 段解析失败：行内出现段落标记 '{tok}'（应为独立段头）。"
                    f"路径行内不得混入其他内容。"
                    f"文件: {report_file}")
            try:
                seq.append(int(tok))
            except ValueError:
                # fail-closed：非数字 token 一律报错拒绝，不静默截断
                raise ValueError(
                    f"[path] 段解析失败：遇到非数字 token '{tok}'（位置 {len(seq)} 之后）。"
                    f"报告文件混入了非路径内容（如日志行），拒绝验证。"
                    f"文件: {report_file}")
    if not seq:
        return None, status, "[path]段无有效数据"
    return seq, status, None

def _strip_head_row(lines):
    """检测并剥离旧版产物残留的 'N E' 头行。

    契约：图文件为纯 edgelist（# 注释行 + "u v" 边，无 "V E" 头行）。
    统一判据：首数据行两整数 (hN, hE)，若 hN 大于其后所有节点号
    （即 hN 不是图中任何节点的端点，形似节点总数 N），且 hE ≥ 剩余
    数据行数（形似边数 E ≥ 实际边数），则判为头行并剥离；
    若 hN 大于后续节点号但 hE < 剩余行数（边数声明不符），仍按疑似
    头行警告但不剥离（可能是含孤立高节点的真实边，无法两全时取保守）。

    返回 (new_lines, stripped_bool)
    """
    data_idx = [i for i, l in enumerate(lines) if l.strip() and not l.strip().startswith('#')]
    if len(data_idx) < 2:
        return lines, False
    first = lines[data_idx[0]].split()
    if len(first) != 2:
        return lines, False
    try:
        hN, hE = int(first[0]), int(first[1])
    except ValueError:
        return lines, False
    rest_max = -1
    for i in data_idx[1:]:
        p = lines[i].split()
        if len(p) >= 2:
            try:
                rest_max = max(rest_max, int(p[0]), int(p[1]))
            except ValueError:
                pass
    n_rest = len(data_idx) - 1  # 剩余数据行数
    if rest_max < 0 or hN <= rest_max:
        return lines, False
    if hE >= n_rest:
        sys.stderr.write(
            "WARNING: 图文件疑似带 'N E' 头行(%d %d)，已自动剥离。"
            "格式契约为纯edgelist（无头行），节点数请用 '# V=' 注释传递。\n" % (hN, hE))
        return lines[:data_idx[0]] + lines[data_idx[0] + 1:], True
    sys.stderr.write(
        "WARNING: 图文件首行(%d %d)疑似 'N E' 头行但边数不符"
        "（声明 %d < 实际数据行 %d），未剥离——若确为头行将产生幽灵节点，"
        "请改用纯edgelist格式（#注释 + u v 边）。\n" % (hN, hE, hE, n_rest))
    return lines, False


def load_graph_edgelist(graph_file):
    """从纯edgelist读图，返回(adj_sets, V)"""
    with open(graph_file, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    lines, _ = _strip_head_row(lines)
    declared_V = 0
    for l in lines:
        s = l.strip()
        if s.startswith('#'):
            body = s.lstrip('#').strip()
            if body.startswith('V='):
                try: declared_V = int(body[2:].split()[0])
                except: pass
            continue
    # V 声明上限校验：防 # V=2e9 触发 list 分配内存耗尽（list 实现内存 O(V)）
    MAX_V = 100_000_000  # 1e8，内存安全上限（list 实现，防资源耗尽）
    if declared_V > MAX_V:
        raise ValueError(
            f"图文件声明的节点数 V={declared_V} 超过上限 {MAX_V}（防资源耗尽）；"
            f"请检查 # V= 声明是否误写。\n文件: {graph_file}")
    edges = []
    max_node = -1
    for lineno, l in enumerate(lines, 1):
        s = l.strip()
        if not s or s.startswith('#'):
            continue
        parts = s.split()
        if len(parts) < 2:
            raise ValueError(
                f"图文件第{lineno}行格式错误: 期望 'u v'（两个整数），实际读到'{s}'\n"
                f"文件: {graph_file}\n提示: 图文件为纯edgelist（每行一条边），无'V E'头行。")
        try:
            u, v = int(parts[0]), int(parts[1])
        except ValueError:
            raise ValueError(
                f"图文件第{lineno}行: 节点号须为整数，读到 '{s}'\n文件: {graph_file}")
        if u < 0 or v < 0:
            raise ValueError(
                f"图文件第{lineno}行: 节点号不能为负（读到 {u} {v}）\n文件: {graph_file}")
        if u == v:
            continue
        edges.append((u, v))
        max_node = max(max_node, u, v)
    V = max(max_node + 1, declared_V)
    if V > MAX_V:
        raise ValueError(
            f"图文件节点数超过上限 {MAX_V}（防资源耗尽，max_node+1={max_node + 1}）\n文件: {graph_file}")
    adj = [set() for _ in range(V)]
    for u, v in edges:
        adj[u].add(v); adj[v].add(u)
    return adj, V


def no_solution_independent(adj, V):
    """独立的无解判据（不信任报告 status 字段）。
    返回 (no_sol: bool, reason: str)。判据：
      1. 孤立点（度0，V>1 时）——孤立点不可能在哈密顿路径中
      2. 断连图（BFS 从 0 出发覆盖 < V）——孤立点即断连特例
      3. 度1节点 > 2（哈密顿路径最多两个端点）
      4. 空图（V==0）无意义
    仅当独立判据确认无解时才认可"no_solution"声明；否则拒绝该状态。
    """
    if V <= 0:
        return True, "空图（V=0）无解"
    # r1: V==1 平凡严格HP=[0] 恒存在，不判无解；V>1 时孤立点→无解
    iso_deg0 = [i for i in range(V) if not adj[i]]
    if V > 1 and iso_deg0:
        return True, f"孤立点（度0）={len(iso_deg0)}个，如{iso_deg0[:5]}"
    seen = set()
    stack = [0]
    seen.add(0)
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    if len(seen) != V:
        iso = [i for i in range(V) if i not in seen]
        return True, f"图不连通：可达{len(seen)}/{V}，孤立/未达节点如{iso[:5]}"
    deg1 = sum(1 for i in range(V) if len(adj[i]) == 1)
    if deg1 > 2:
        return True, f"度1节点={deg1}>2（哈密顿路径最多两个端点）"
    return False, ""


def verify_no_solution_report(graph_file=None):
    """验证"报告中声称无解"是否被独立判据支持。
    有图文件→独立判定；无图文件→拒绝直接采信。
    返回 (accept_no_sol: bool, detail: str)。
    """
    if not graph_file:
        return False, "报告声称无解，但未提供图文件——无法独立确认无解，拒绝采信"
    try:
        adj, V = load_graph_edgelist(graph_file)
    except (ValueError, OSError) as e:
        return False, f"图文件解析失败（{e}）——无法独立确认无解，拒绝采信"
    no_sol, reason = no_solution_independent(adj, V)
    if no_sol:
        return True, f"独立判据确认无解：{reason}"
    return False, f"独立判据判定图有解或无法证明无解（{reason or '未发现断连/叶超限'}）——报告 status:no_solution 不可信"

def verify_strict(path, V, adj=None):
    """strict三条件验证。返回(passed, errors)"""
    errors = []
    L = len(path)
    # 条件1: L==V
    if L != V:
        errors.append(f"条件1失败: L={L} != V={V}")
    # 条件2: 无重复 + 节点范围
    seen = set()
    repeats = []
    oob = []
    for i, node in enumerate(path):
        if node < 0 or node >= V:
            oob.append((i, node))
        elif node in seen:
            repeats.append(node)
        else:
            seen.add(node)
    if repeats:
        errors.append(f"条件2失败: {len(repeats)}个重复节点 (如{repeats[:5]})")
    if oob:
        errors.append(f"节点越界: {len(oob)}个 (如{oob[:3]})")
    # 全覆盖
    if len(seen) != V:
        errors.append(f"覆盖不全: unique={len(seen)} != V={V}")
    # 条件3: 全真边
    if adj is not None:
        missing = []
        for i in range(L - 1):
            u, v = path[i], path[i+1]
            if 0 <= u < V and 0 <= v < V and v not in adj[u]:
                missing.append((i, u, v))
        if missing:
            errors.append(f"条件3失败: {len(missing)}条非真实边 (如{missing[:3]})")
    return len(errors) == 0, errors

def selftest():
    """反例自测：证明strict真生效"""
    print("=== verify_strict 反例自测 ===")
    passed = 0; failed = 0
    def check(name, cond, detail=""):
        nonlocal passed, failed
        if cond: passed += 1; print(f"  [PASS] {name}")
        else: failed += 1; print(f"  [FAIL] {name} {detail}")

    # 小链图 0-1-2-3
    adj = [set() for _ in range(4)]
    for u, v in [(0,1),(1,2),(2,3)]:
        adj[u].add(v); adj[v].add(u)
    # 合法HP
    ok, err = verify_strict([0,1,2,3], 4, adj)
    check("合法HP 0-1-2-3 PASS", ok, str(err))
    # non-real edge
    ok, err = verify_strict([0,2,1,3], 4, adj)
    check("非真实边 FAIL", not ok and any('条件3' in e for e in err), str(err))
    # 重复
    ok, err = verify_strict([0,1,1,2], 4, adj)
    check("重复节点 FAIL", not ok and any('条件2' in e for e in err), str(err))
    # 长度不足
    ok, err = verify_strict([0,1,2], 4, adj)
    check("长度不足 FAIL", not ok and any('条件1' in e for e in err), str(err))
    # 越界
    ok, err = verify_strict([0,1,2,99], 4, adj)
    check("越界 FAIL", not ok and any('越界' in e for e in err), str(err))
    # 星形图（中心0连1,2,3,4）：度1叶子=4>2 → 无HP（这里验证器验路径，无解检测在solver）
    # 验证器对星形图的一条"假HP"判FAIL
    adj_star = [set() for _ in range(5)]
    for leaf in [1,2,3,4]:
        adj_star[0].add(leaf); adj_star[leaf].add(0)
    ok, err = verify_strict([1,0,2,3,4], 5, adj_star)  # 2-3边不存在
    check("星形图假HP FAIL(非真实边)", not ok and any('条件3' in e for e in err), str(err))

    print(f"\nselftest: {passed} passed, {failed} failed")
    return failed == 0

def verify_walk(path, V, adj=None):
    """walk验证：全真边 + 全覆盖（不要求 L==V，允许重复节点）。
    与 verify_strict 互补：strict验严格HP（完备无重复），walk验全覆盖遍历。"""
    errors = []
    L = len(path)
    unique = len(set(path))
    # 全覆盖
    if unique != V:
        missing = [i for i in range(V) if i not in set(path)]
        errors.append(f"覆盖不全: unique={unique} != V={V} (未覆盖如{missing[:5]})")
    # 越界
    oob = [(i, n) for i, n in enumerate(path) if n < 0 or n >= V]
    if oob:
        errors.append(f"节点越界: {len(oob)}个 (如{oob[:3]})")
    # 全真边
    if adj is not None:
        missing_edges = []
        for i in range(L - 1):
            u, v = path[i], path[i + 1]
            if 0 <= u < V and 0 <= v < V and v not in adj[u]:
                missing_edges.append((i, u, v))
        if missing_edges:
            errors.append(f"非真实边: {len(missing_edges)}条 (如{missing_edges[:3]})")
    return len(errors) == 0, errors


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == '--selftest':
        sys.exit(0 if selftest() else 1)
    walk_mode = '--walk' in sys.argv
    if walk_mode:
        sys.argv = [a for a in sys.argv if a != '--walk']
    if len(sys.argv) < 2:
        print("用法: python verify_strict_deliver.py <report_file> [graph_file]")
        print("      python verify_strict_deliver.py --walk <report_file> [graph_file]  (walk遍历验证：全真边+全覆盖，不要求L==V)")
        print("      python verify_strict_deliver.py --selftest")
        sys.exit(1)
    report_file = sys.argv[1]
    graph_file = sys.argv[2] if len(sys.argv) >= 3 else None

    try:
        path, status, err = load_path_from_report(report_file)
    except ValueError as ve:
        # fail-closed：解析报错直接失败（不静默截断）
        print(f"验证结论: ERROR")
        print(f"说明: {ve}")
        sys.exit(1)
    if path is None:
        print(f"状态: {status}")
        print(f"说明: {err}")
        if status in ('no_solution', 'construction_failed'):
            # 不再盲信报告 status：必须独立验证无解判据
            accept, detail = verify_no_solution_report(graph_file)
            print(f"无解声明独立验证: {'通过' if accept else '未通过'}")
            print(f"  {detail}")
            if accept:
                print("验证结论: 无解（独立判据确认，非假阳性）")
                sys.exit(0)
            else:
                print("验证结论: FAIL —— 报告的 no_solution 声明未获独立判据支持（疑似伪造）")
                sys.exit(1)
        elif status == 'construction_failed':
            print("验证结论: 构造失败（报告声明；未独立验证可行性）")
            sys.exit(1)
        else:
            sys.exit(1)

    # 空路径直接 FAIL（任何图上空路径都无验证意义）
    if not path:
        print("验证结论: FAIL —— 路径为空（无验证意义），拒绝放行")
        sys.exit(1)

    # 读V
    V = None
    adj = None
    with open(report_file, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = re.match(r'#\s*V:\s*(\d+)', line)
            if m: V = int(m.group(1)); break
    if graph_file:
        try:
            adj, V2 = load_graph_edgelist(graph_file)
        except (ValueError, OSError) as e:
            print(f"验证结论: ERROR —— 图文件解析失败: {e}")
            sys.exit(1)
        if V is None: V = V2
    if V is None:
        V = max(path) + 1

    # 无图文件场景：图文件未提供时提示 V 由路径推断，孤立点可能遗漏
    declare_info = "（图文件未提供，V 由路径推断）" if graph_file is None else ""
    if graph_file is None:
        print(f"提示: 未提供图文件，V 由路径最大节点+1 推断（孤立点可能被遗漏）{declare_info}")

    if walk_mode:
        ok, errors = verify_walk(path, V, adj)
        print(f"路径长度 L = {len(path)}")
        print(f"节点数   V = {V}")
        print(f"唯一节点 = {len(set(path))}")
        print(f"扩展系数 = {len(path) / V:.4f}")
        if ok:
            print("验证结论: PASS — 全真边遍历成立（全真边 + 全覆盖）")
            sys.exit(0)
        else:
            print("验证结论: FAIL")
            for e in errors:
                print(f"  {e}")
            sys.exit(1)

    ok, errors = verify_strict(path, V, adj)
    print(f"路径长度 L = {len(path)}")
    print(f"节点数   V = {V}")
    print(f"唯一节点 = {len(set(path))}")
    if ok:
        print("验证结论: PASS — 严格哈密顿路径成立（L==V + 无重复 + 全真边）")
        sys.exit(0)
    else:
        print("验证结论: FAIL")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
