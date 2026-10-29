# -*- coding: utf-8 -*-
"""
塔交互三构想·构想三（T 系列）：塔间粘合（拓扑侧·画像级）
预注册：《塔交互三构想·预注册判据书-v1.0-20260927》T-1/T-2/T-3（画像级，不设硬判据）
T-1 共轭类数（=不可约表示数）实算 q=7,11,13,17（矩阵群 orbit 法）vs 公式 (q+5)/2；类数乘法账（拼接Σc vs 交互Πc）
T-2 维数形态账（q=7,11 最小对，预注册允许的降级口径）：张量积维数乘积集 vs 单体维数并集 → 新维数清单
T-3 对表 ζ 零点前 12 虚部（描述性，只记不判）
"""
import numpy as np, sympy as sp, json, platform, datetime
from itertools import product

ZEROS12 = [14.1347, 21.0220, 25.0109, 30.4249, 32.9351, 37.5862,
           40.9187, 43.3271, 48.0052, 49.7738, 52.8015, 56.4462]

def psl_elements(q):
    """PSL(2,q)=SL(2,q)/{±I} 的元素，用 representative：I 与 -I 只留 trace 前半。返回 (a,b,c,d) 元组集合。"""
    E = []
    for a in range(q):
        for b in range(q):
            for c in range(q):
                # d = (a*... ) 解 ad - bc = 1 → d = (1 + b*c) * inv(a)（a≠0）；a=0 时 -bc=1 → c=±1/…
                if a == 0:
                    continue
                ia = pow(a, -1, q)
                d = ((1 + b * c) * ia) % q
                E.append((a, b, c, d))
    # a=0：ad-bc=-bc≡1 → bc≡-1（b≠0, c=-inv(b)），d 无约束（0..q-1 全取）
    for b in range(1, q):
        c = (-pow(b, -1, q)) % q
        for d in range(q):
            E.append((0, b, c, d))
    # 商 ±I：去掉重复的 -E
    S = set()
    for (a, b, c, d) in E:
        neg = ((-a) % q, (-b) % q, (-c) % q, (-d) % q)
        key = min((a, b, c, d), neg)  # 规范代表元
        S.add(key)
    return list(S)

def norm(x, q):
    # PSL 中 x 与 -x 是同一元素：取规范代表元
    a, b, c, d = x
    neg = ((-a) % q, (-b) % q, (-c) % q, (-d) % q)
    return min((a % q, b % q, c % q, d % q), neg)

def mul(x, y, q):
    (a, b, c, d), (e, f, g, h) = x, y
    return norm((a * e + b * g, a * f + b * h, c * e + d * g, c * f + d * h), q)

def inv(x, q):
    a, b, c, d = x
    det = (a * d - b * c) % q
    assert det == 1
    return ((d) % q, (-b) % q, (-c) % q, (a) % q)

def n_conjugacy_classes(q):
    E = psl_elements(q)
    seen = set(); n = 0
    for x in E:
        if x in seen:
            continue
        n += 1
        orb = set()
        for g in E:
            orb.add(mul(g, mul(x, inv(g, q), q), q))
        seen |= orb
    return n

print("===== T-1 共轭类数实算 vs 公式 (q+5)/2 =====")
verif = {}
for q in [7, 11, 13, 17]:
    nc = n_conjugacy_classes(q)
    formula = (q + 5) // 2
    order = q * (q * q - 1) // 2
    verif[q] = {"computed": nc, "formula": formula, "match": nc == formula, "order": order}
    print(f"PSL(2,{q}): |G|={order} 实算类数={nc} 公式={(q+5)//2} {'✓' if nc==formula else '✗ MISMATCH'}")

formula_ok = all(v["match"] for v in verif.values())
print(f"公式四塔全中：{formula_ok}（{'八塔公式档启用' if formula_ok else '公式失效，八塔仅实算档'}）")

# 类数乘法账
towers8 = [7, 11, 13, 17, 19, 23, 29, 31]
cvals = {q: verif[q]["computed"] if q in verif else (q + 5) // 2 for q in towers8}
sum_c = sum(cvals.values()); prod_c = int(np.prod([cvals[q] for q in towers8]))
print(f"\n类数账（8塔）：拼接 Σc={sum_c}  交互 Πc={prod_c}  比值 Πc/Σc={prod_c/sum_c:.1f}")
c11 = cvals[7] + cvals[11]; p11 = cvals[7] * cvals[11]
print(f"最小对（q=7,11）：Σc={c11} Πc={p11} 比值={p11/c11:.2f}")

print("\n===== T-2 维数形态账（q=7,11 最小对·降级口径=维数乘积集非表示分解）=====")
D7 = [1, 3, 3, 6, 7, 8]          # PSL(2,7) 特征标维数（平方和 1+9+9+36+49+64=168 ✓ 实算自检）
D11 = [1, 5, 5, 10, 10, 11, 12, 12]  # PSL(2,11)（平方和 1+25+25+100+100+121+144+144=660 ✓）
assert sum(d * d for d in D7) == 168 and sum(d * d for d in D11) == 660
prodset = sorted(set(d1 * d2 for d1, d2 in product(D7, D11)))
union = sorted(set(D7) | set(D11))
new_dims = [d for d in prodset if d not in union]
print(f"D7×D11 维数乘积集（{len(prodset)} 个）：{prodset}")
print(f"两单体维数并集：{union}")
print(f"新维数（乘积集中出现、并集中不存在）：{new_dims}")

print("\n===== T-3 对表 ζ 零点（描述性·只记不判）=====")
print("ζ 零点前 12 虚部：", ZEROS12)
print(f"新维数清单：{new_dims}（与零点无逐位对应，如实记录）")
print(f"Πc/Σc 比值（8塔）={prod_c/sum_c:.1f} vs 零点密度增长 T·log T（量级不同源，不配对）")

out = {"script": "ta_glu_torsion-v1.0-20260927.py",
       "prereg": "塔交互三构想·预注册判据书-v1.0-20260927.md",
       "ran_at": datetime.datetime.now().isoformat(timespec="seconds"),
       "platform": platform.platform(),
       "T1_class_number": {"verification": verif, "formula_ok": formula_ok,
                            "towers8_cvals": cvals, "sum_c": sum_c, "prod_c": prod_c,
                            "pair_7_11": {"sum": c11, "prod": p11}},
       "T2_dim_shapes": {"D7": D7, "D11": D11, "prodset": prodset, "union": union, "new_dims": new_dims},
       "T3_zeros12": ZEROS12, "grade": "画像级·无硬判据（预注册冻结）"}
with open("results/ta_T_series_result-v1.0-20260927.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\n结果已写 results/ta_T_series_result-v1.0-20260927.json")
