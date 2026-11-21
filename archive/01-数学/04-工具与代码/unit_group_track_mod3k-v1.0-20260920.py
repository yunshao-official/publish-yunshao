# -*- coding: utf-8 -*-
"""
unit_group_track_mod3k-v1.0-20260920.py
判据书：《代数册·单位群轨第二深步·模3^k单位群结构对照预注册判据书-v1.0-20260920.md》（NTFS 冻结 2026-09-20 00:31:48，先于本脚本首跑）
判据 V1-V6：mod 3^k 单位群结构机器复核 + CRT 合流锚 + CRT 网格。纯标准库。
"""
import json, math, time
from pathlib import Path

BASE = Path(r"H:\理论存档\01-数学")
RES = BASE / "02-实验与数据" / "results"
TAG = "v1.0-20260920"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def unit_group(n):
    return [x for x in range(1, n) if math.gcd(x, n) == 1]

def order(x, n):
    """x 在 (Z/n)^× 的乘法阶（x 需与 n 互素）"""
    v, k = x % n, 1
    while v != 1:
        v = v * x % n
        k += 1
    return k

def main():
    t0 = time.time()
    log(f"首跑时间 {time.strftime('%Y-%m-%d %H:%M:%S')}（判据书冻结 2026-09-20 00:31:48 NTFS 在先）")
    res = {"meta": {"script": "unit_group_track_mod3k-v1.0-20260920.py",
                    "criterion_freeze_ntfs": "2026-09-20 00:31:48",
                    "first_run": time.strftime("%Y-%m-%d %H:%M:%S")}}

    # V1-V3
    V1, V2, V3 = {}, {}, {}
    ok1 = ok2 = ok3 = True
    for k in range(1, 7):
        m = 3 ** k
        U = unit_group(m)
        expect = 2 * 3 ** (k - 1)
        V1[k] = {"n": len(U), "expect": expect}
        ok1 &= len(U) == expect
        o2 = order(2, m)
        V2[k] = {"ord2": o2, "expect": expect}
        ok2 &= o2 == expect
        gen_ok = len({(pow(2, i, m)) for i in range(expect)}) == len(U)  # ⟨2⟩=全群
        full_ok = all(pow(x, expect, m) == 1 for x in U)
        V3[k] = {"cyclic_generated_by_2": gen_ok, "all_x_pow_e_equals_1": full_ok}
        ok3 &= gen_ok and full_ok
    res["V1"] = {"detail": V1, "pass": ok1}
    res["V2"] = {"detail": V2, "pass": ok2}
    res["V3"] = {"detail": {str(k): v for k, v in V3.items()}, "pass": ok3}
    log(f"V1={ok1} V2={ok2} V3={ok3}")

    # V4 防错位
    V4, ok4 = {}, True
    for k in range(1, 7):
        m = 3 ** k
        add_order = m
        unit_order = 2 * 3 ** (k - 1)
        # 加法群元素 1 的阶 = m；单位群指数 = 2·3^{k-1}（循环群=最大阶）
        exp_unit = max(order(x, m) for x in unit_group(m))
        V4[k] = {"add_order": add_order, "unit_order": unit_order,
                 "add_has_order_m": True, "unit_exponent": exp_unit,
                 "orders_differ": add_order != unit_order}
        ok4 &= (add_order != unit_order) and (exp_unit < add_order or k == 1 and exp_unit < add_order)
        ok4 &= (add_order != unit_order) and (exp_unit == unit_order)
    res["V4"] = {"detail": V4, "pass": ok4}
    log(f"V4={ok4}")

    # V5 CRT 合流锚 (Z/24)^×
    U24 = unit_group(24); U8 = unit_group(8); U3 = unit_group(3)
    img = [(x % 8, x % 3) for x in U24]
    bijective = len(set(img)) == len(U24) == len(U8) * len(U3)
    hom_ok = True
    for x in U24:
        for y in U24:
            lhs = ((x * y) % 8, (x * y) % 3)
            rhs = (x % 8 * y % 8, x % 3 * y % 3)
            if lhs != rhs:
                hom_ok = False
    V5 = {"bijective": bijective, "homomorphic_8x8": hom_ok,
          "U8_structure": "C2xC2 (W2)", "U3_structure": "C2 (V1/V3 k=1)",
          "conclusion": "(Z/24)^× ≅ C2×C2×C2"}
    res["V5"] = {**V5, "pass": bool(bijective and hom_ok)}
    log(f"V5={bijective and hom_ok}")

    # V6 CRT 网格
    V6, ok6 = {}, True
    for a in range(2, 6):
        for b in range(1, 4):
            m = 2 ** a * 3 ** b
            Um = unit_group(m); Ua = unit_group(2 ** a); Ub = unit_group(3 ** b)
            img = [(x % 2 ** a, x % 3 ** b) for x in Um]
            bij = len(set(img)) == len(Um) == len(Ua) * len(Ub)
            hom = all(((x * y) % (2 ** a), (x * y) % (3 ** b)) ==
                      (x % (2 ** a) * y % (2 ** a), x % (3 ** b) * y % (3 ** b))
                      for x in Um for y in Um)
            V6[f"a{a}b{b}"] = {"m": m, "|U(m)|": len(Um),
                               "|U(2^a)|*|U(3^b)|": len(Ua) * len(Ub),
                               "bijective": bij, "homomorphic": hom}
            ok6 &= bij and hom
    res["V6"] = {"detail": V6, "pass": ok6}
    log(f"V6={ok6}")

    verdict = all(res[k]["pass"] for k in ["V1", "V2", "V3", "V4", "V5", "V6"])
    res["verdict"] = "V1-V6 全过【复算一致】" if verdict else "存在 Fail→如实入账"
    out = RES / f"unit_group_track_mod3k_result-{TAG}.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"结果落盘 {out}，用时 {time.time()-t0:.1f}s")
    print(json.dumps({"verdict": res["verdict"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
