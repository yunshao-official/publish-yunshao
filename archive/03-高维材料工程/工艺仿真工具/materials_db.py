# -*- coding: utf-8 -*-
"""
材料参数库（工艺仿真工具 · 组件1）
数据来源：公开手册级常数值（室温），工程量级用；精确设计以实测为准。
字段：纵波声速 vL(m/s)、密度 ρ(kg/m³)、热导率 k(W/mK)、熔点/固相线(K)、
      红外反射率粗值(1-13μm)、布洛德(自由电子)吸收主导说明。
"""

MATERIALS = {
    "Fe70Ni20Cr10": {  # 奥氏体不锈钢（三分量云韶钢基底）
        "vL": 5700, "rho": 7900, "k_therm": 15, "T_melt": 1673,
        "R_ir_rough": 0.90, "note": "红外吸收由自由电子(Drude)主导，无强窄带声子共振；表面Cr2O3氧化层在~10-13μm有氧化物声子特征",
    },
    "Pd": {  # 钯（对外v1曾用基底）
        "vL": 4530, "rho": 12020, "k_therm": 72, "T_melt": 1828,
        "R_ir_rough": 0.95, "note": "Drude主导，强反射",
    },
    "Al1070": {  # 纯铝（超声细化文献最多的体系之一）
        "vL": 6420, "rho": 2700, "k_therm": 226, "T_melt": 933,
        "R_ir_rough": 0.97, "note": "超声铸锭细化主流文献体系",
    },
    "Ti6Al4V": {  # 钛合金（超声处理文献体系）
        "vL": 6090, "rho": 4430, "k_therm": 7, "T_melt": 1933,
        "R_ir_rough": 0.85, "note": "超声熔体处理文献体系",
    },
    "Cu": {  # 铜（超声焊接/细化参照）
        "vL": 4760, "rho": 8960, "k_therm": 400, "T_melt": 1358,
        "R_ir_rough": 0.97, "note": "Drude主导",
    },
}

def get(name):
    return MATERIALS[name]

def names():
    return list(MATERIALS)
