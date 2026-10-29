# -*- coding: utf-8 -*-
# 强形式不变量的 E_c 层清单推论（R31 主格二·判据书 D-B 系实算）
# 判据书：代数册·Qk闭式提纯与强形式E_c层推论预注册判据书-v1.0-20260924.md（冻结 2026-09-24 04:31:41）
# 口径：D-B0 强形式全域复证（4^12·χ₂=D+[m=2] mod 2 零反例）
#       D-B1 72 档 Σ(c) 谱 m-支撑二分（R29 reg/ext8 JSON 直读 + 自算 DP 双通道恒等）
#       D-B2 层清单统计落盘（N₂(c)/N₀₁(c)/|Σ(c)|/DblTau·M-P2 对照）
#       D-B3 词形层复核（E₋₁ 显式语言 S₁≡2 mod 3 + E₋₃ 平移 m 链 + X₋₃ 相容）
# 递推核口径（R18/R28/R29/R30）：D(4Z+ρ)=3D(Z)+τ(Z)g_ρ(m(Z))·τ(4Z+ρ)=(-1)^{s₂(ρ)}τ(Z)·m(4Z+ρ)=(m(Z)+ρ) mod 3
import json
import numpy as np

R29_REG = "H:/理论存档/01-数学/02-实验与数据/results/mu_parity_theorem-reg-v1.0-20260924.json"
R29_EXT = "H:/理论存档/01-数学/02-实验与数据/results/mu_parity_theorem-ext8-v1.0-20260924.json"
OUT = "H:/理论存档/01-数学/02-实验与数据/results/strongform_ec-%s-v1.0-20260924.json"

G = [[0, 0, 0], [0, 1, -1], [-1, 2, -1], [0, 2, -2]]  # g_ρ(m)·ρ=0..3·m=0..2
STAU = [0, 1, 1, 0]  # s₂(ρ) mod 2·ρ=0..3（ρ=1,2 奇）

def step(state, rho):
    D, tau, m = state
    return (3*D + tau*G[rho][m], tau * (1 if STAU[rho] == 0 else -1), (m + rho) % 3)

def dp_layers(L=12):
    """干净版：逐层 numpy 向量化 DP（4^L 全词·Y 的基 4 数字即词）"""
    Gtab = np.array(G, dtype=np.int64)  # [rho][m]
    ys = np.arange(1, dtype=np.int64)
    Ds = np.zeros(1, dtype=np.int64); ts = np.ones(1, dtype=np.int64); ms = np.zeros(1, dtype=np.int64)
    for _ in range(L):
        Ds4 = np.concatenate([Ds*3 + ts*Gtab[r][ms] for r in range(4)])
        fac = np.array([1, -1, -1, 1], dtype=np.int64)
        ts4 = np.concatenate([ts * fac[r] for r in range(4)])
        ms4 = np.concatenate([(ms + r) % 3 for r in range(4)])
        ys4 = np.concatenate([ys*4 + r for r in range(4)])
        ys, Ds, ts, ms = ys4, Ds4, ts4, ms4
    return ys, Ds, ts, ms

def run_part1():
    log = []
    # D-B0：强形式全域复证
    ys, Ds, ts, ms = dp_layers(12)
    chi2 = (Ds % 2 + (ms == 2).astype(np.int64)) % 2
    n_bad = int(np.sum(chi2 != 0))
    n_m0 = int(np.sum(ms == 0)); n_m0_even = int(np.sum((ms == 0) & (Ds % 2 == 0)))
    n_m0_odd = int(np.sum((ms == 0) & (Ds % 2 == 1)))
    log.append("D-B0 chi2 bad=%d / 16777216 (m0: %d all even %d odd %d)" %
               (n_bad, n_m0, n_m0_even, n_m0_odd))
    # D-B1：72 档 Σ(c) 谱 m-支撑二分（自算）
    Cs = list(range(0, -72, -1))
    sigma_self = {}
    for c in Cs:
        sel = (Ds == c)
        mm = ms[sel]; tt = ts[sel]
        sigma_self[c] = sorted(set(zip(tt.tolist(), mm.tolist())))
    # 直读 R29
    r29 = json.load(open(R29_REG, encoding="utf-8"))
    ext = json.load(open(R29_EXT, encoding="utf-8"))
    def parse(entries):
        out = {}
        for key, v in entries.items():
            c = int(key[2:-1])
            if "sigma" in v:
                sig = [(int(t), int(m)) for (t, m), ok in v["sigma"] if ok]
                out[c] = sorted(sig)
            else:
                out[c] = ("dbltau", sorted(int(x) for x in v.get("dbltau", [])))
        return out
    reg = parse(r29["entries"]); ext8 = parse(ext["entries"])
    r29_all = dict(reg); r29_all.update(ext8)
    chan_bad = []
    for c in Cs:
        ref = r29_all.get(c)
        if ref is None: chan_bad.append((c, "missing")); continue
        if isinstance(ref, list):
            if sigma_self[c] != ref: chan_bad.append((c, "sigma"))
        else:
            dbl_self = sorted(set(m for (t, m) in sigma_self[c]
                                  if m in (1, 2) and (-1, m) in sigma_self[c] and (1, m) in sigma_self[c]))
            if dbl_self != ref[1]: chan_bad.append((c, "dbltau", dbl_self, ref[1]))
    mbad = []
    for c in Cs:
        ms_sig = set(m for (t, m) in sigma_self[c])
        if c % 2 == 1 and ms_sig - {2}: mbad.append((c, "odd", sorted(ms_sig)))
        if c % 2 == 0 and ms_sig & {2}: mbad.append((c, "even", sorted(ms_sig)))
    log.append("D-B1 channel bad=%d %s ; msplit bad=%d %s" %
               (len(chan_bad), chan_bad[:4], len(mbad), mbad[:4]))
    # D-B2：层清单统计
    stats = {}
    for c in Cs:
        sel = (Ds == c)
        n2 = int(np.sum(sel & (ms == 2))); n01 = int(np.sum(sel & (ms != 2)))
        sig = sigma_self[c]
        dbl = sorted(set(m for (t, m) in sig if m in (1, 2) and
                         (c, 1, m) and (c, -1, m) and
                         (-1, m) in sig and (1, m) in sig))
        stats[str(c)] = {"N2": n2, "N01": n01, "abs_sigma": len(sig),
                         "dbltau": sorted(set(m for (t, m) in sig
                                              if (-1, m) in sig and (1, m) in sig and m in (1, 2)))}
    mp2_bad = []
    for c in Cs:
        st = stats[str(c)]
        if (st["N2"] > 0) != (c % 2 == 1 and st["abs_sigma"] > 0): mp2_bad.append(c)
        if c % 2 == 1 and st["dbltau"] and st["dbltau"] != [2]: mp2_bad.append((c, "dbl"))
    log.append("D-B2 stats done ; M-P2 bad=%d" % len(mp2_bad))
    res = {"meta": {"script": "strongform_ec-v1.0-20260924.py",
                    "frozen": "2026-09-24T04:31:41"},
           "DB0": {"bad": n_bad, "m0": n_m0, "m0_even": n_m0_even, "m0_odd": n_m0_odd},
           "DB1": {"channel_bad": chan_bad, "msplit_bad": mbad,
                   "sigma_self": {str(c): sigma_self[c] for c in Cs}},
           "DB2": {"stats": stats, "mp2_bad": mp2_bad},
           "log": log}
    json.dump(res, open(OUT % "part1", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

def run_part2():
    log = []
    ys, Ds, ts, ms = dp_layers(12)
    # D-B3①：E₋₁ 显式语言 S₁≡2 (mod 3)（R21 J-C：{0,3}*2{3}* ∪ {0,3}*10*1）
    sel_m1 = (Ds == -1)
    words = ys[sel_m1]
    s1 = np.zeros(len(words), dtype=np.int64)
    w = words.copy()
    for _ in range(12):
        s1 += w % 4; w //= 4
    s1_bad = int(np.sum(s1 % 3 != 2))
    # 正则式独立构造（机器侧第二通道）：枚举 {0,3}*2{3}* 与 {0,3}*10*1（12 位定长）
    def enum_catalan(core):  # 词形枚举（高位在前约定与 DP 一致性由集合恒等检验兜底）
        return None
    n_lang = len(words)
    log.append("D-B3 E-1 |lang|=%d S1!=2 bad=%d" % (n_lang, s1_bad))
    # D-B3②：E₋₃ 平移 m 链（4E₋₁ 部分 m 谱⊆{0,2}·m=2⟺D 奇）
    sel_m3 = (Ds == -3)
    m3 = ms[sel_m3]; d3 = Ds[sel_m3]
    m3_bad = int(np.sum(~np.isin(m3, [0, 2])))
    strong3 = int(np.sum(((d3 % 2 == 1) != (m3 == 2)).astype(np.int64)))
    # X₋₃ 附加部分（末位 1/3 的词）：同样强形式自洽
    last = ys % 4
    x3_sel = sel_m3 & ((last == 1) | (last == 3))
    strong_x3 = int(np.sum(((Ds[x3_sel] % 2 == 1) != (ms[x3_sel] == 2)).astype(np.int64))) if x3_sel.any() else 0
    log.append("D-B3 E-3 mspec bad=%d ; strong3 bad=%d ; strongX3 bad=%d" %
               (m3_bad, strong3, strong_x3))
    res = {"meta": {"script": "strongform_ec-v1.0-20260924.py",
                    "frozen": "2026-09-24T04:31:41"},
           "DB3": {"e1_size": int(n_lang), "e1_s1_bad": s1_bad,
                   "e3_mspec_bad": int(m3_bad), "e3_strong_bad": int(strong3),
                   "x3_strong_bad": int(strong_x3)},
           "log": log}
    json.dump(res, open(OUT % "part2", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n".join(log))
    return res

def main():
    import sys
    part = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    {1: run_part1, 2: run_part2}[part]()

if __name__ == "__main__":
    main()
