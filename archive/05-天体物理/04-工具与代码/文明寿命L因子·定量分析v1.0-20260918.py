# -*- coding: utf-8 -*-
"""文明寿命L因子定量分析 v1.0（创新8第一步：cliodynamics×德雷克方程）
数据来源：公开历史文献记载的政体/文明存续时间（已知帝国/王朝/共和国）
注意：这是**地球文明样本**，用于建立L的基线分布——不是最终答案（外推到星际文明需修正）。
判据冻结：拟合分布→中位数±1σ→与Kardashev/千年基准对表。
"""
import numpy as np, json

# 已知政体/文明存续时间（年）——公开历史口径
# 来源：Taagepera 1979 "Size and Duration of Empires" / Seshat 公开口径 / Rein Taagepera "Growth and Decline"
# 选取标准：有明确建国/灭亡年代的主权政体
civilizations = [
    # 古典
    ("古埃及新王国", 350), ("亚述帝国", 300), ("波斯阿契美尼德", 220),
    ("雅典帝国", 70), ("罗马共和国", 480), ("罗马帝国(西)", 500),
    ("罗马帝国(东/拜占庭)", 1000), ("汉朝", 400), ("秦朝", 15),
    ("唐朝", 290), ("宋朝", 320), ("蒙古帝国", 160),
    ("奥斯曼帝国", 620), ("莫卧儿帝国", 330), ("明朝", 276),
    ("西班牙帝国", 400), ("奥斯曼哈里发", 90),
    # 近现代
    ("大英帝国", 400), ("法兰西殖民帝国", 300), ("俄罗斯帝国", 370),
    ("苏联", 69), ("大清帝国", 268), ("葡萄牙帝国", 500),
    ("荷兰帝国", 350), ("奥匈帝国", 150), ("德意志第三帝国", 12),
    ("日本帝国", 75), ("清朝", 268), ("西班牙哈布斯堡", 180),
    ("波斯萨珊", 430), ("阿拉伯哈里发", 600), ("查理曼帝国", 100),
    ("印加帝国", 95), ("阿兹特克帝国", 95), ("神罗帝国", 844),
]

durations = [c[1] for c in civilizations]
arr = np.array(durations)

stats = {
    "样本数": len(arr),
    "中位数年": round(float(np.median(arr)), 0),
    "均值年": round(float(np.mean(arr)), 0),
    "标准差年": round(float(np.std(arr)), 0),
    "最小": int(np.min(arr)), "最大": int(np.max(arr)),
    "分位": {
        "10%": round(float(np.percentile(arr, 10)), 0),
        "25%": round(float(np.percentile(arr, 25)), 0),
        "50%": round(float(np.percentile(arr, 50)), 0),
        "75%": round(float(np.percentile(arr, 75)), 0),
        "90%": round(float(np.percentile(arr, 90)), 0),
    },
    "存续>500年比例%": round(float(np.sum(arr >= 500)) / len(arr) * 100, 1),
    "存续>1000年比例%": round(float(np.sum(arr >= 1000)) / len(arr) * 100, 1),
}

# 德雷克L因子对表
L_analysis = {
    "地球L基线（政体口径）": f"中位数 {stats['中位数年']:.0f} 年",
    "德雷克L典型假设": "10,000 年（主流口径）",
    "地球L/德雷克L比": round(stats['中位数年'] / 10000, 3),
    "含义": "地球政体的中位存续时间远短于德雷克假设的L=10000年",
    "对SETI含义": "L短→文明密度进一步下调（与SDO 2018方向一致）",
}

out = {"stats": stats, "L_factor": L_analysis,
       "data": [(c[0], c[1]) for c in civilizations]}
with open("civilization_L_factor_20260918.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print(f"样本: {stats['样本数']} 政体")
print(f"中位存续: {stats['中位数年']:.0f} 年")
print(f"均值: {stats['均值年']:.0f} 年 | σ: {stats['标准差年']:.0f} 年")
print(f">500年: {stats['存续>500年比例%']}% | >1000年: {stats['存续>1000年比例%']}%")
print(f"德雷克L对表: {L_analysis['地球L/德雷克L比']}")
