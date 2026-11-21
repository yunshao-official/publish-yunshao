# -*- coding: utf-8 -*-
"""
unit_group_track_mod2k-v1.0-20260919.py
代数册·单位群轨·模2^k单位群结构对照（Kummer 两轨第二轨·轻量基线）
判据冻结：先于本脚本首跑落盘《代数册·单位群轨·模2^k单位群结构对照预注册判据书-v1.0-20260919.md》§一
执行层主流数学：欧拉函数/循环群结构。体系常数零引用。纯标准库。
"""
import json
from datetime import datetime

T0_CLOCK = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
OUT = r"H:\理论存档\01-数学\02-实验与数据\results\unit_group_track_mod2k_result-v1.0-20260919.json"

def order_mod(m, a):
    """a 在 (Z/m)^× 中的阶；a 需与 m 互素。"""
    x, n = a % m, 1
    while x != 1:
        x = x * a % m
        n += 1
    return n

def unit_group(m):
    return [a for a in range(1, m) if math_gcd(a, m) == 1]

def math_gcd(a, b):
    while b:
        a, b = b, a % b
    return a

# W1 阶
W1 = {}
for k in range(1, 9):
    m = 2 ** k
    g = unit_group(m)
    W1[k] = {"m": m, "phi_actual": len(g), "phi_expected": 2 ** (k - 1),
             "ok": len(g) == 2 ** (k - 1)}
w1_pass = all(v["ok"] for v in W1.values())

# W2 结构分解 k>=3
W2 = {}
for k in range(3, 9):
    m = 2 ** k
    minus1, five = m - 1, 5
    o_m1 = order_mod(m, minus1)
    o_5 = order_mod(m, five)
    gen5 = {pow(five, j, m) for j in range(o_5)}
    inter = gen5 & {1}
    H = {pow(minus1, i, m) * pow(five, j, m) % m for i in range(o_m1) for j in range(o_5)}
    W2[k] = {"ord_minus1": o_m1, "ord_5": o_5, "ord_5_expected": 2 ** (k - 2),
             "inter_trivial": inter == {1}, "product_size": len(H),
             "group_size": 2 ** (k - 1),
             "ok": o_m1 == 2 and o_5 == 2 ** (k - 2) and inter == {1} and len(H) == 2 ** (k - 1)}
w2_pass = all(v["ok"] for v in W2.values())

# W3 (Z/24)^x ≅ C2^3
G24 = unit_group(24)
orders24 = {a: order_mod(24, a) for a in G24}
w3_all_sq1 = all(pow(a, 2, 24) == 1 for a in G24)
w3_pass = (len(G24) == 8 and w3_all_sq1 and max(orders24.values()) == 2)

# W4 Z/8 加法群 vs (Z/8)^x 防混同
U8 = unit_group(8)
z8_orders = {a: 8 // math_gcd(a, 8) for a in range(8)}
w4 = {"Z8_order": 8, "U8_order": len(U8), "Z8_has_order8_elem": any(v == 8 for v in z8_orders.values()),
      "U8_max_order": max(order_mod(8, a) for a in U8),
      "ok": (8 != len(U8)) and any(v == 8 for v in z8_orders.values()) and
            max(order_mod(8, a) for a in U8) == 2}

result = {
    "script_clock_first_run": T0_CLOCK,
    "frozen_evidence": "判据书NTFS创建于本脚本首跑之前（时钟见执行报告核对记录）",
    "W1": W1, "W1_pass": w1_pass,
    "W2": W2, "W2_pass": w2_pass,
    "W3": {"elements": G24, "orders": orders24, "all_x2_eq_1": w3_all_sq1, "pass": w3_pass},
    "W4": w4, "W4_pass": w4["ok"],
    "overall": bool(w1_pass and w2_pass and w3_pass and w4["ok"]),
    "clock_finished": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("=== 单位群轨基线（判据冻结后实算）===")
print("W1 阶 2^{k-1}:", w1_pass)
print("W2 C2xC_{2^{k-2}} k=3..8:", w2_pass)
for k, v in W2.items():
    print(f"  k={k}: ord(-1)={v['ord_minus1']} ord(5)={v['ord_5']} (期望 2^{k-2}={v['ord_5_expected']}) 积={v['product_size']} ok={v['ok']}")
print("W3 (Z/24)^x 阶8 全元素 x²=1:", w3_pass, "| 阶分布:", {a: o for a, o in orders24.items()})
print("W4 Z/8≠(Z/8)^x:", w4["ok"])
print("总裁决 W1-W4 全过 =", result["overall"])
