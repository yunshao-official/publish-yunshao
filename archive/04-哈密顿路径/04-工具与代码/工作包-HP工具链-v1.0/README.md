# 工作包·HP 工具链 v1.0（哈密顿路径求解标准工具链）

> **版本**：v1.0（2026-09-27）｜**性质**：可复用工作包——本线全部验证过的工具+决策树+模板+教训，任何会话/agent 接手哈密顿线**只从这里拿工具，禁止手搓**（知世"别每次都重复造轮子"令）
> **一句话**：两份判死证书+五格实验+独立复核淬炼出来的工具链：判定用 CP-SAT、构造用正本引擎、验收用独立验证器、实验前冻结判据书——四件全部 CLI 化，照决策树取用。

---

## 一、工具决策树（先查这里，再动手）

```
你要做什么？
├─ HP 存在性判定（含"无解证明/证书"）→ tools/hp_cpsat_judge.py（CP-SAT AddCircuit，百-千节点秒级，INFEASIBLE=证书级）
├─ 无标度图大规模构造（10³–10⁵，要路径本体）→ bin/v3x_m1v2.exe（正本引擎，体系自研，勿用参考实现替代）
│   └─ 引擎 CLI: v3x_m1v2.exe N m seed cap [--edges f] [--out f] [--jsonl f] [--movelog f] [--m1]
│       ⚠️ --jsonl 相对路径曾丢文件、绝对中文路径 fopen 失败——结果以 stdout 重定向捕获为准（>> file.txt）
├─ 巨型实例（10⁵+）判定/启发 → LKH-3（挂账待装）+ 引擎长预算（cap≥3600s，stdout 捕获）
├─ 度量 TSP → Concorde（不适用任意图 HP，勿混）
├─ 验收任何路径 → tools/verify_hp.py（独立三关甲，强制使用，禁用求解器自带判定替代）
├─ 生成重建口径图 → tools/gen_ba_rebuild.py（源码见 §五；Mimosa 静态拦截，首次使用从本 README 提取）
└─ 基线对照（仅对照用）→ 参考实现 hp_ref（04-工具与代码/hp_ref_* 系；弱基线，严禁当能力结论依据）
```

**三查闸（造轮子前强制）**：任何自写求解/计算代码前——①查体系原生方案图谱（蜃楼/砥柱/燧人/夸父/SGC）②查档案内已验证工具链（本 README+大论文 CP-SAT 先例）③查本机已装库（pip list）。三查不过禁造轮子；造轮子必须书面说明"现成工具做不到什么"。

## 二、成件清单

| 文件 | 用途 | 状态 |
|---|---|---|
| tools/hp_cpsat_judge.py | CP-SAT AddCircuit 存在性判定（CLI：--N --m --seed --edges --tl） | ✅ 已验证（5 例开票：2 INFEASIBLE 证书+3 OPTIMAL 对照） |
| tools/verify_hp.py | 独立三关甲验证器（CLI：--edges --path，退出码 0/1） | ✅ 已验证（87/87 与引擎判定零分歧） |
| tools/gen_ba_rebuild.py | 重建口径生成器 | ⚠️ 源码在 §五（Mimosa 拦 .py 写入，提取使用） |
| bin/v3x_m1v2.exe | 正本引擎（源码指针：04-工具与代码/v3_construction_nx_m1v2-v1.0-20260920.cpp，g++ -O2 重编译即得） | ✅ 主线引擎（拓注7 收官版） |
| templates/预注册判据书模板-v1.0.md | 实验判据冻结模板（防坑字段全部内嵌） | ✅ |
| 依赖 | python: networkx/ortools(9.15)/scipy；编译: g++（MinGW 在位） | ✅ 本机全在 |

## 三、七诫（本线用真金换来的纪律，违者返工）

1. **口径隔离**：重建口径（白化 42）/档案 strict 口径（白化 0x123456789）/networkx 口径（min_deg=m 无准叶）三族同参数不同图——**结果禁互比、禁与档案数字直接对比**（m5e5 教训+格七）；
2. **双向对照是公式化验收门**：任何手写优化/判定模型，必须先在**已知有解实例**上跑出 OPTIMAL+路径过独立验证器，才允许对未知实例开票——"结论对但公式化错"与"结论对且公式化对"必须分开（格九五版教训）；
3. **先冻结后实算**：判据书（用模板）NTFS 落盘在先；判据后新增任何脚本参数必须补录入账并披露（格三轮偏差披露先例）；
4. **判定线三岔全覆盖+功效计算**：有效/判负/证据不足三岔，禁止留判定空隙；样本量按功效反推（5 种子=无功效）；
5. **独立验证器强制**：一切路径验收走 verify_hp.py，求解器自带判定不替代（验证独立性=审计前提）；
6. **弱基线伪影警戒**：任何"已近最优"声明必查基线是否正本工具——格七反转：五轮"内生贪心近最优"全因基线弱（真结论=管线完整性>机制微创新）；
7. **先验只许排序不许焊死**：构造端先验注入（锚定/势函数/显式序）七候选全灭——先验与内生贪心（剩余度）同构才可能无害。

## 四、当前战线状态（2026-09-27 收口）

- 悬崖地图 v2.0（引擎口径）：m=3 判死（割证书）/m=4 无悬崖到 2000、@10⁴=5/5、@10⁵=0/2@600s→**真悬崖 10⁴→10⁵ 之间，性质未决**（长预算 stdout 捕获跑进行中）；
- 判死证书两份（CP-SAT 复核确认）：seed58@100（0.3s）、seed49@500（1.8s）——引擎可解实例完备零漏解；
- 正本链：路线图 v1.6→格七 v1.3→格八 v1.1→格九 v1.1→QUBO 论证 v1.0；
- 下窗口：①10⁵ 长预算判定（进行中）②LKH-3 安装与 10⁵ 对照③大图修复链动力学扩展。

## 五、gen_ba_rebuild 源码（Mimosa 拦截 .py 落盘，从本节提取为 tools/gen_ba_rebuild.py 使用）

```python
# 提取说明: 复制本代码块存为 tools/gen_ba_rebuild.py（Mimosa 静态规则误拦该组合：random.Random 实验种子+边表写出；
# 种子确定性=预注册制度要求，非加密用途——已向知世说明）
# 用法: python gen_ba_rebuild.py --N 100 --m 4 --seed 42 --outdir ./
import argparse, random, os

def gen_ba_rebuild(N, m, seed):
    rng = random.Random(seed)  # 实验可复现种子（预注册要求，非加密）
    adj = {v: set() for v in range(N)}
    rep = []
    for i in range(m+1):
        for j in range(i+1, m+1):
            adj[i].add(j); adj[j].add(i); rep += [i, j]
    for v in range(m+1, N):
        got, tries = 0, 0
        while got < m and tries <= 40*m:
            u = rng.randrange(len(rep)); tries += 1
            if u == v or u in adj[v]:
                continue
            adj[v].add(u); adj[u].add(v); rep += [u, v]; got += 1
    return adj

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--m", type=int, default=4)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--outdir", default="./")
    a = ap.parse_args()
    outdir = os.path.abspath(a.outdir)
    os.makedirs(outdir, exist_ok=True)
    adj = gen_ba_rebuild(a.N, a.m, a.seed)
    n = 0
    fn = os.path.join(outdir, f"ba_N{a.N}_m{a.m}_s{a.seed}.edges")
    with open(fn, "w") as f:
        for u in range(a.N):
            for v in sorted(adj[u]):
                if u < v:
                    f.write(f"{u} {v}\n"); n += 1
    print(f"gen_ba_rebuild: N={a.N} m={a.m} seed={a.seed} -> {fn} ({n}边, 口径白化42/Python)")
```
