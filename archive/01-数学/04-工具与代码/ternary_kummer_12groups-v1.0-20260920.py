# -*- coding: utf-8 -*-
"""
ternary_kummer_12groups-v1.0-20260920.py
判据书：《代数册·三元Kummer进位语言×12组对照预注册判据书-v1.0-20260920.md》（NTFS 冻结 2026-09-20 00:46:36，先于本脚本首跑）
判据 G0-G6：三元 Kummer 深度律+跨素基联合完全分辨+逐 N s₃ 移位分离。5 片检查点。
"""
import json, math, time
from pathlib import Path
import numpy as np
from scipy import stats

BASE = Path(r"H:\理论存档\01-数学")
RES = BASE / "02-实验与数据" / "results"
TAG = "v1.0-20260920"
X_MAX = 200000
N_SHARDS = 5
SEED = 20260920
GROUPS = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def carries(a, b, base, digits):
    """位窗 0..digits-1 内的进位次数（R14 在档口径：不计窗外出位）。
    实现=逐位传播；独立校验用 carries_identity 闭式恒等式（G0①）。"""
    n = 0
    ca = 0
    for i in range(digits):
        s = (a % base) + (b % base) + ca
        a //= base; b //= base
        if s >= base:
            n += 1
            ca = 1
        else:
            ca = 0
    return n

def carries_identity(a, b, base, digits):
    """独立闭式：进位入位 i+1 存在 ⟺ (a mod base^{i+1} + b mod base^{i+1}) ≥ base^{i+1}。
    位窗内进位次数 = #{i=1..digits: 上式成立}（与逐位传播实现的算法路径不同）。"""
    n = 0
    for i in range(1, digits + 1):
        M = base ** i
        if (a % M) + (b % M) >= M:
            n += 1
    return n

def S_m(r, base, m):
    """组级签名：#{k in [0,base^m): c_m(k, r)=j}"""
    M = base ** m
    cnt = {}
    for k in range(M):
        c = carries(k, (r - k) % M, base, m)
        cnt[c] = cnt.get(c, 0) + 1
    return tuple(cnt.get(j, 0) for j in range(M + 1))

def s_digits(n, base):
    s = 0
    while n > 0:
        s += n % base
        n //= base
    return s

def ks_test(a, b):
    return stats.ks_2samp(a, b, alternative="two-sided")

def perm_test(a, b, n_perm=10000, seed=SEED):
    rng = np.random.default_rng(seed)
    pooled = np.concatenate([a, b]).astype(np.float64)
    na = len(a)
    obs = abs(a.mean() - b.mean())
    count = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        if abs(pooled[:na].mean() - pooled[na:].mean()) >= obs:
            count += 1
    return (count + 1) / (n_perm + 1)

def effect_d(a, b):
    ma, mb = a.mean(), b.mean()
    na, nb = len(a), len(b)
    sp = math.sqrt(((na-1)*a.var(ddof=1) + (nb-1)*b.var(ddof=1)) / (na+nb-2))
    return abs(ma-mb)/sp if sp > 0 else 0.0

PAIRS = [(2,10), (4,20), (8,16), (14,22)]

def main():
    t0 = time.time()
    log(f"首跑时间 {time.strftime('%Y-%m-%d %H:%M:%S')}（判据书冻结 2026-09-20 00:46:36 NTFS 在先）")
    res = {"meta": {"script": "ternary_kummer_12groups-v1.0-20260920.py",
                    "criterion_freeze_ntfs": "2026-09-20 00:46:36",
                    "first_run": time.strftime("%Y-%m-%d %H:%M:%S"), "X": X_MAX}}

    # ---------- G0 自检锚 ----------
    # ①独立闭式恒等式全网格校验（与逐位实现算法路径不同；首版自比式校验已废弃）
    g0a = True
    for base in (2, 3, 5):
        for m in range(1, 4):
            M = base ** m
            for r in range(M):
                for k in range(M):
                    if carries(k, (r - k) % M, base, m) != carries_identity(k, (r - k) % M, base, m):
                        g0a = False
    log(f"G0① 进位实现 vs 独立闭式恒等式（b=2,3,5, m<=3 全网格 {2*9+3*27+5*125} 态）: {'全对' if g0a else '不符'}")

    # 二元 S₃ 回归锚
    s3bin = {g: S_m(g, 2, 3) for g in GROUPS}
    pair144_bin = sum(1 for ga in GROUPS for gb in GROUPS
                      if (s3bin[ga] == s3bin[gb]) == ((ga % 8) == (gb % 8)))
    log(f"G0② 二元 S₃ 回归锚 144 对: {pair144_bin}/144")
    res["G0"] = {"carry_brute_match": bool(g0a), "binary_S3_144": int(pair144_bin),
                 "pass": bool(g0a and pair144_bin == 144)}

    # ---------- G1 深度律 ----------
    s3_1 = {g: S_m(g % 3, 3, 1) for g in GROUPS}
    well_m1 = all(S_m(g % 3, 3, 1) == S_m((g + 24) % 3, 3, 1) for g in GROUPS)
    splits_m2 = sum(1 for g in GROUPS if S_m(g % 9, 3, 2) != S_m((g + 24) % 9, 3, 2))
    log(f"G1: m=1 良定义={well_m1}; m=2 分裂组数={splits_m2}/12（预测 12）")
    res["G1"] = {"m1_well_defined": bool(well_m1),
                 "m1_signatures": {str(g): s3_1[g] for g in GROUPS},
                 "m2_split_groups": int(splits_m2),
                 "m2_detail": {str(g): [list(S_m(g % 9, 3, 2)), list(S_m((g+24) % 9, 3, 2))] for g in GROUPS},
                 "pass": bool(well_m1 and splits_m2 >= 1)}

    # ---------- G2 三元模 3 轴 ----------
    vals = set(s3_1.values())
    p144 = sum(1 for ga in GROUPS for gb in GROUPS
               if (s3_1[ga] == s3_1[gb]) == ((ga % 3) == (gb % 3)))
    classes = {}
    for g in GROUPS:
        classes.setdefault(s3_1[g], []).append(g)
    expect_cls = {0: [0, 6, 12, 18], 1: [4, 10, 16, 22], 2: [2, 8, 14, 20]}
    cls_ok = all(sorted(classes.get(S_m(c, 3, 1), [])) == v for c, v in expect_cls.items())
    log(f"G2: 互异值={len(vals)} 144对={p144}/144 类清单一致={cls_ok}")
    res["G2"] = {"n_values": len(vals), "pairwise_144": int(p144),
                 "classes_match": bool(cls_ok), "classes": {str(k): v for k, v in classes.items()},
                 "pass": bool(len(vals) == 3 and p144 == 144 and cls_ok)}

    # ---------- G3 联合完全分辨 ----------
    joint = {g: (s3bin[g], s3_1[g]) for g in GROUPS}
    p144j = sum(1 for ga in GROUPS for gb in GROUPS
                if (joint[ga] == joint[gb]) == (ga == gb))
    n_cls = len(set(joint.values()))
    log(f"G3: 联合类数={n_cls}/12 144对={p144j}/144")
    res["G3"] = {"n_classes": int(n_cls), "pairwise_144": int(p144j),
                 "pass": bool(n_cls == 12 and p144j == 144)}

    # ---------- 逐 N 分片（G4②/G5） ----------
    evens_all = np.arange(2, X_MAX + 1, 2)
    shards = np.array_split(evens_all, N_SHARDS)
    for si, shard in enumerate(shards, 1):
        rows = [[int(N), int(N) % 24, s_digits(int(N), 3), int(N) % 3, int(N) % 5] for N in shard]
        ck = RES / f"ternary_kummer_checkpoint_{si}-{TAG}.json"
        ck.write_text(json.dumps({"shard": si, "n": len(rows), "rows": rows}, ensure_ascii=False), encoding="utf-8")
        log(f"片 {si}/{N_SHARDS} 落盘 {ck.name}")
    allrows = [r for si in range(1, N_SHARDS+1) for r in json.load(open(RES / f"ternary_kummer_checkpoint_{si}-{TAG}.json", encoding="utf-8"))["rows"]]
    arr = np.array(allrows)
    rs = arr[:, 1].astype(int); s3v = arr[:, 2].astype(float); m3 = arr[:, 3].astype(int); m5 = arr[:, 4].astype(int)
    log(f"逐 N 样本 {len(arr)}，用时 {time.time()-t0:.1f}s")

    # ---------- G4 p>=5 盲性 ----------
    g4a = all(S_m(g % 5, 5, 1) != S_m((g + 24) % 5, 5, 1) for g in GROUPS)
    chi = {}
    g4_ok = True
    for g in GROUPS:
        cnt = np.bincount(m5[rs == g], minlength=5)
        stat, p = stats.chisquare(cnt)
        chi[str(g)] = {"counts": cnt.tolist(), "chi2_p": float(p)}
        g4_ok &= p > 0.01
    res["G4"] = {"c5_1_member_varying": bool(g4a), "chi2_uniform": chi, "chi2_all_pass": bool(g4_ok),
                 "pass": bool(g4a and g4_ok)}
    log(f"G4: c⁵₁ 组级不良定义（随成员变）={g4a}; 卡方 12 检验全 p>0.01={g4_ok}")

    # ---------- G5 逐 N 三元分离 ----------
    g5 = []
    g5_ok = True
    for ga, gb in PAIRS:
        a = s3v[rs == ga]; b = s3v[rs == gb]
        ks = ks_test(a, b); pp = perm_test(a, b); d = effect_d(a, b)
        shift = float(a.mean() - b.mean())
        dir_ok = (ga % 3 == 2 and shift > 0) or (ga % 3 == 1 and shift < 0)
        ah = s3v[rs == ga] - m3[rs == ga]; bh = s3v[rs == gb] - m3[rs == gb]
        ksh = ks_test(ah, bh)
        ok = (ks.pvalue < 0.01 and pp < 0.01 and 0.20 <= d <= 0.55
              and 0.85 <= abs(shift) <= 1.15 and dir_ok and ksh.pvalue > 0.01)
        g5_ok &= ok
        g5.append({"pair": f"{ga}|{gb}", "mean_a": float(a.mean()), "mean_b": float(b.mean()),
                   "shift": shift, "shift_dir_ok": bool(dir_ok),
                   "ks_p": float(ks.pvalue), "perm_p": float(pp), "d": float(d),
                   "high_part_ks_p": float(ksh.pvalue), "std": float(s3v.std()), "pass": bool(ok)})
    log(f"G5: " + "; ".join(f"{x['pair']} d={x['d']:.3f} shift={x['shift']:.3f} p={x['ks_p']:.2e}" for x in g5))
    res["G5"] = {"tests": g5, "pass": bool(g5_ok)}

    # ---------- 【探索·非预注册】G-D 修订引理（mod-2 精化不变性）交叉验证 ----------
    # 判负机制：s₃(Q) ≡ Q (mod 2)（3≡1 mod 2 位数和恒等式），Q=8t+c_r 奇偶由组定死。
    # 修正引理 G-D'：law(去末位部分 | 组) 只通过 c_r mod 2 依赖组。同奇偶跨组应不可分。
    c_r = {2: 0, 10: 3, 4: 1, 20: 6, 8: 2, 16: 5, 14: 4, 22: 7}
    hp = {g: s3v[rs == g] - m3[rs == g] for g in c_r}
    explor = []
    for par, gs in [(0, [2, 8, 14]), (1, [10, 16, 22])]:
        for i in range(len(gs)):
            for j in range(i + 1, len(gs)):
                ga, gb = gs[i], gs[j]
                p = float(ks_test(hp[ga], hp[gb]).pvalue)
                explor.append({"pair": f"{ga}|{gb}", "c_r": f"{c_r[ga]}|{c_r[gb]}",
                               "parity": par, "ks_p": p, "inseparable": bool(p > 0.01)})
    expl_ok = all(e["inseparable"] for e in explor)
    res["G5_exploratory_GDprime"] = {"note": "【探索·非预注册】修正引理交叉验证：同 c_r 奇偶跨组去末位分布不可分",
                                     "tests": explor, "all_inseparable": bool(expl_ok)}
    log(f"【探索】G-D' 同奇偶跨组去末位不可分: {sum(e['inseparable'] for e in explor)}/6")

    # ---------- G6 ----------
    cluster = res["G0"]["pass"] and res["G1"]["pass"] and res["G2"]["pass"] and res["G3"]["pass"]
    perN = g5_ok
    res["G6_verdict"] = {"group_level_closed": bool(cluster), "per_N_closed": bool(perN),
                         "verdict": ("群级完全分辨闭环" + ("；逐 N 级 s₃ 移位分离闭环" if perN else "；逐 N 级分离预测失败（如实入账）"))
                                    if cluster else "存在 Fail→如实入账"}
    out = RES / f"ternary_kummer_12groups_result-{TAG}.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘 {out}，总用时 {time.time()-t0:.1f}s")
    print(json.dumps(res["G6_verdict"], ensure_ascii=False))

if __name__ == "__main__":
    main()
