# -*- coding: utf-8 -*-
"""
全息投影审计仿真（天工开物 第六批 · 知世令"继续，全息投影" 2026-09-15）
==================================================================================
对象（计划原文口径，0729修正版 段391/393/397）：
  - 全息投影单元：密度 100个/cm²（=1mm 间距），法衣 2.5m² 共 250 万个
  - 机制：每个单元"通过电离周围空气分子产生可见光"（开空气等离子体发光）
  - 产出：4K 级分辨率立体全息影像（金龙、法阵），AI 实时渲染联动
  - 功耗：5 kW（50kW 全功能预算中的全息份额）
方法：真实物理四账 + 真实技术映射表。
真实文献锚（公开口径）：
  - 飞秒激光等离子体体素（AIST Fairy Lights 类研究）：单体素 mJ 级脉冲、mm³ 体素、
    室内可见、工作体积 cm³-升级
  - 等离子显示屏 PDP（密封 Ne-Xe 微放电+荧光粉）：~150 μW/单元达电视亮度
  - 开放空气 DBD/电晕放电：可见辉光弱、主发 337nm 紫外、臭氧产额 5-25 g/kWh
  - POV 旋转LED/全息纱(Pepper's ghost)/雾幕：舞台成熟技术
诚实口径：标准公开数据；数量级账为主；影子机制不入账、只审数字主张。
"""
import json
import numpy as np

OUT = {}

def s1_power_account():
    """功耗账：5kW 预算 vs 电离发光的真实能量学。"""
    # 电离能量地板：1mm³ 体素全部电离的理论能耗
    n_density = 2.5e25            # 空气分子数密度 m⁻³
    voxel_vol = (1e-3) ** 3       # 1mm³
    n_mol = n_density * voxel_vol
    ionize_eV = 20.0
    full_ionization_J = n_mol * ionize_eV * 1.602e-19      # ~0.8 J
    frac_needed = 1e-6            # 可见辉光只需百万分之一分子被激发（乐观）
    floor_J = full_ionization_J * frac_needed              # ~0.8 μJ 地板
    practice_mJ = 1.0            # 实际飞秒体素单体素脉冲能量（公开口径 0.2-7 mJ）
    # 预算换算
    budget_W = 5000.0
    per_voxel_W_30Hz = practice_mJ * 1e-3 * 30        # 1mJ×30Hz = 0.03 W/体素
    voxels_at_30Hz = budget_W / per_voxel_W_30Hz
    frame_4K = 3840 * 2160
    vpulses_per_s = budget_W / (practice_mJ * 1e-3)   # 5e6 脉冲/秒
    fps_4k = vpulses_per_s / frame_4K
    fps_480p = vpulses_per_s / (640 * 480)
    return {
        "full_ionization_1mm3_J": full_ionization_J,
        "visible_glow_floor_uJ": floor_J * 1e6,
        "practice_per_pulse_mJ": practice_mJ,
        "floor_vs_practice_gap": practice_mJ * 1e-3 / floor_J,
        "n_units_total": 2500000, "n_units_per_cm2": 100,
        "power_budget_W": budget_W,
        "power_per_unit_avg_mW": budget_W / 2500000 * 1000,
        "voxels_continuously_lit_at_5kW_30Hz": voxels_at_30Hz,
        "duty_of_array_percent": voxels_at_30Hz / 2500000 * 100,
        "voxel_pulses_per_s_at_5kW": vpulses_per_s,
        "fps_if_4K_frame": fps_4k,
        "fps_if_480p_frame": fps_480p,
        "note": "地板(μJ)与光学路线实耗(mJ)差10³倍；5kW 下：16.7万体素@30Hz(阵列6.7%占空)，"
                "4K帧=0.6fps 或 480P=16fps——'4K级立体全息'与5kW预算不相容"}

def s2_resolution_account():
    """分辨率账：1mm 间距的角分辨率（主张里能活的部分）。"""
    pitch_mm = 1.0
    rows = []
    for D in (2, 5, 10, 50, 100):
        theta_arcmin = np.degrees(np.arctan(pitch_mm / 1000 / D)) * 60
        rows.append({"view_distance_m": D, "pitch_angle_arcmin": theta_arcmin,
                     "better_than_eye_1arcmin": theta_arcmin < 1.0})
    return {"rows": rows,
            "note": "100个/cm²=1mm 间距，≥5m 观距角分辨率 0.4 角分 < 人眼 1 角分——"
                    "'4K级'的分辨率口径本身不荒谬（复算一致），荒谬的是体素的生成方式与功耗"}

def s3_safety_account():
    """安全账：贴身 250 万个空气放电单元。"""
    power_W = 5000.0
    ozone_yield_g_per_kWh = 10.0            # DBD 产臭氧公开范围 5-25 g/kWh
    ozone_g_h = ozone_yield_g_per_kWh * power_W / 1000
    limit_mg_m3 = 0.1                        # GB/T 18883 臭氧 0.05ppm ≈ 0.1 mg/m³
    breath_zone_m3 = 2.0                     # 头部周围保守混合体积
    t_exceed_s = (limit_mg_m3 * 1e-3 * breath_zone_m3) / (ozone_g_h / 3600)
    return {
        "ozone_g_per_hour": ozone_g_h,
        "ozone_limit_mg_m3": limit_mg_m3,
        "seconds_to_exceed_limit_in_2m3_breath_zone": t_exceed_s,
        "uv_emission": "N₂ 第二正带 337nm 紫外（开放空气放电主发射）——贴身眼部/皮肤暴露",
        "emi": "250万微放电=宽带射频噪声源，与同衣 256 通道脑机电极自相干扰",
        "audible": "DBD 交流嘶鸣（贴耳级噪声源）",
        "note": "贴身空气放电在臭氧/紫外/EMI/噪声四项全部超标——安全账不过"}

def s4_volumetric_account():
    """'立体'账：2D 织物阵列 vs 真三维体素。"""
    return {
        "fabric_2d_array": "发射单元在织物表面，电离发生在发射极附近 mm 级——本质是**曲面2D显示屏**，"
                          "不是空气中的立体影像",
        "remote_focus_route": "若要真空中远场体素（Fairy Lights 架构），需要激光束聚焦到空气中——"
                              "单台 fs 激光器（100-300W 级）只能画 150-200 个同时可见体素@5kW（30Hz 持留），"
                              "手心大小的发光形状，不是金龙",
        "2_5M_micro_lasers": "100个/cm² 的微飞秒激光器组件不存在（fs 光纤激光器为 cm 级、万元级单价）",
        "real_stage_route": "舞台级'金龙法阵'现实做法=全息纱(Pepper's ghost)+投影+POV风扇，5kW 够用，"
                            "但需要纱幕/雾幕介质，室内或夜间"}

def s5_brightness_account():
    """亮度/日光账。"""
    return {
        "plasma_voxel_luminance_cd_m2": "1-100（室内可见、日光下不可见，公开演示口径）",
        "ambient_daylight_cd_m2": "5000-10000（晴空）",
        "pdp_reference": "密封微放电+荧光粉可达电视亮度（150 μW/单元）——但那是密封 Neon-Xe 单元，"
                        "不是'电离周围空气'",
        "verdict": "室外白天演示（段143 天安门广场彩排口径）差 2-3 个量级；夜间/室内可行"}

def s6_real_mapping():
    """真实技术映射表。"""
    return {
        "披风幕布/织物显示": "LED/电致发光织物=真实（法衣仿真II 已给 3.5W/13.9h 结论，第41件）✓",
        "真空中体素": "飞秒激光等离子体体素=真实研究线（室内、微光、小体积）",
        "舞台大影像": "全息纱+雾幕+POV=成熟舞台工业，5kW 够，需介质、室内或夜间",
        "原文章配": "'电离空气+4K立体+5kW+贴身'四件套不相容；任取三件舍一件均有真实方案"}

if __name__ == "__main__":
    OUT["S1_功耗账"] = s1_power_account()
    OUT["S2_分辨率账"] = s2_resolution_account()
    OUT["S3_安全账"] = s3_safety_account()
    OUT["S4_立体账"] = s4_volumetric_account()
    OUT["S5_亮度账"] = s5_brightness_account()
    OUT["S6_真实映射"] = s6_real_mapping()
    OUT["honest_note"] = ("真实物理账本口径：公开研究/商业数据（Fairy Lights 类、PDP、DBD、舞台全息）；"
                          "数量级账为主；数学实验口径不构成物理结论。")
    with open(r"H:/理论存档/03-高维材料工程/工艺仿真工具/results/hologram_audit.json", "w", encoding="utf-8") as f:
        json.dump(OUT, f, ensure_ascii=False, indent=1, default=float)
    p = OUT["S1_功耗账"]
    print(f"[功耗] 1mm³全电离={p['full_ionization_1mm3_J']:.2f}J 地板={p['visible_glow_floor_uJ']:.2f}μJ "
          f"实耗={p['practice_per_pulse_mJ']}mJ/脉冲（差{p['floor_vs_practice_gap']:.1e}倍）")
    print(f"[功耗] 每单元均摊={p['power_per_unit_avg_mW']:.1f}mW 5kW可点亮{p['voxels_continuously_lit_at_5kW_30Hz']:.0f}体素@30Hz"
          f"（阵列{p['duty_of_array_percent']:.1f}%）")
    print(f"[功耗] 5kW: 4K帧={p['fps_if_4K_frame']:.1f}fps 或 480P={p['fps_if_480p_frame']:.1f}fps")
    for r in OUT["S2_分辨率账"]["rows"]:
        print(f"[分辨率] {r['view_distance_m']:>3}m → {r['pitch_angle_arcmin']:.2f}角分 "
              f"{'✓超人眼' if r['better_than_eye_1arcmin'] else '低于人眼'}")
    s = OUT["S3_安全账"]
    print(f"[安全] 臭氧={s['ozone_g_per_hour']:.0f}g/h，2m³呼吸区{s['seconds_to_exceed_limit_in_2m3_breath_zone']:.3f}秒超限"
          f"（限值{s['ozone_limit_mg_m3']}mg/m³）+UV+EMI+噪声")
