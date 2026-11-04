#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figures for the five-layer derivation monograph (math -> medicine)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BASE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(BASE, "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.family": "Noto Serif CJK SC",
    "font.size": 9,
    "axes.unicode_minus": False,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

INK = "#1a1a1a"
GREY = "#595959"
GREEN = "#2f7d4f"
AMBER = "#b07a12"
RED = "#9e2a2b"
BLUE = "#2166ac"
PINK = "#b2185b"


def box(ax, x, y, w, h, fc, ec, lw=0.8):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                       linewidth=lw, edgecolor=ec, facecolor=fc)
    ax.add_patch(p)


def fig_chain():
    fig, ax = plt.subplots(figsize=(9.6, 7.6))
    ax.set_xlim(0, 12); ax.set_ylim(0.85, 6.55); ax.axis("off")

    rows = [
        ("数学", "36 = 12 组 × 3 维；α=1/8（(Z$_2$)$^3$ 八表示失一）；\nη=7/8（表示论与模 24 两条已证来源）",
         "定义与定理成立；\n15/16、0.5 维属选择", AMBER, "部分成立"),
        ("物理", "$f_0 = 64\\,k_BT/h$；体温 310.15 K ↔ 724.8 nm；\n器件 804 nm ↔ 279.6 K",
         "算术精确；桥接未证；\n与体温错位 30.5 K", AMBER, "桥接待证"),
        ("化学", "Tc = Θ_D·(15/16)·f_defect；14 种材料 f_defect ≤ 0.24；\n473 K 需 Θ_D ≥ 504.5 K，600 K 需 640 K",
         "天花板式描述有效；\n预测与目标冲突", RED, "预测失败"),
        ("生物", "α 按年 = 12.5%/年，按十年 = 1.25%/年；\nη 四级链 = 0.586，实测每级 ≈ 0.71–0.77",
         "按年高 8–20 倍；\n7/8 输给 3/4", RED, "常数不成立"),
        ("医学", "1:7 钟表读法 → 25–38 次/分；\n$10^4$ V/m → SAR $10^4$–$5\\times10^4$ W/kg",
         "两项均判负；\n725 nm 为可检验修正", RED, "安全判负"),
    ]
    ys = [5.55, 4.45, 3.35, 2.25, 1.15]
    for (name, body, verdict, color, tag), y in zip(rows, ys):
        box(ax, 0.10, y, 11.8, 0.92, "white", "#cfcfcf")
        box(ax, 0.10, y, 1.25, 0.92, "#f2f2f2", "#cfcfcf")
        ax.text(0.725, y + 0.46, name, ha="center", va="center", fontsize=11,
                color=INK, fontweight="bold")
        ax.text(1.55, y + 0.62, body.split("\n")[0], ha="left", va="center", fontsize=8.0, color=INK)
        ax.text(1.55, y + 0.28, body.split("\n")[1], ha="left", va="center", fontsize=8.0, color=INK)
        ax.text(7.60, y + 0.62, verdict.split("\n")[0], ha="left", va="center", fontsize=7.6, color=GREY)
        ax.text(7.60, y + 0.28, verdict.split("\n")[1], ha="left", va="center", fontsize=7.6, color=GREY)
        box(ax, 10.30, y + 0.31, 1.45, 0.30, color, color)
        ax.text(11.025, y + 0.46, tag, ha="center", va="center", fontsize=7.4,
                color="white", fontweight="bold")

    for y in ys[:-1]:
        ax.annotate("", xy=(0.725, y - 0.17), xytext=(0.725, y - 0.01),
                    arrowprops=dict(arrowstyle="-|>", color="#7f7f7f", lw=1.2,
                                    mutation_scale=12))

    fig.savefig(os.path.join(FIG, "Figure1_layer_chain.png"), dpi=300)
    plt.close(fig)


def fig_alpha_clock():
    labels = ["最大摄氧量\n（中年）", "肾小球滤过率\n（40 岁后）", "握力\n（50–85 岁）", "骨密度\n（绝经早期）"]
    vals = [1.0, 0.6, 1.24, 1.5]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    y = np.arange(len(labels))
    ax.barh(y, vals, color=[BLUE, "#4c9bbd", PINK, "#c46a86"], height=0.52)
    for yi, v in zip(y, vals):
        ax.text(v * 1.12, yi, f"{v:.2f}%/年", va="center", fontsize=9.2, color=INK)
    ax.axvline(12.5, color=RED, lw=1.4, ls="--")
    ax.axvline(1.25, color=GREEN, lw=1.4, ls="-.")
    ax.text(12.5 * 0.92, len(labels) - 0.35, "α=1/8 按年\n12.5%/年", color=RED,
            ha="right", va="top", fontsize=8.8)
    ax.text(1.25 * 1.08, len(labels) - 0.35, "α=1/8 按十年\n1.25%/年", color=GREEN,
            ha="left", va="top", fontsize=8.8)
    ax.set_xscale("log")
    ax.set_xlim(0.3, 40)
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9.2)
    ax.set_xlabel("观测到的年下降速率（%，对数轴）", fontsize=9.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color="#e3e3e3", lw=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "Figure2_alpha_clock.png"), dpi=300)
    plt.close(fig)


def fig_tc_ceiling():
    data = [
        ("Al", 428, 1.18, "常规"), ("Zn", 327, 0.85, "常规"), ("Cd", 209, 0.56, "常规"),
        ("In", 108, 3.41, "常规"), ("Sn", 195, 3.72, "常规"), ("Hg", 72, 4.15, "常规"),
        ("Pb", 105, 7.20, "常规"), ("Ta", 240, 4.47, "常规"), ("V", 380, 5.40, "常规"),
        ("Nb", 275, 9.25, "常规"), ("MgB$_2$", 620, 39.2, "双能带"),
        ("YBCO", 415, 92.0, "铜氧"), ("H$_3$S", 1200, 203.0, "氢化物"),
        ("LaH$_{10}$", 1400, 250.0, "氢化物"),
    ]
    colors = {"常规": "#2166ac", "双能带": "#4c9bbd", "铜氧": "#b2185b", "氢化物": "#b07a12"}
    fig, ax = plt.subplots(figsize=(7.0, 3.5))
    xs = np.arange(len(data))
    frac = [tc / th for _, th, tc, _ in data]
    ax.bar(xs, frac, color=[colors[m] for _, _, _, m in data], width=0.62)
    ax.axhline(0.9375, color=RED, lw=1.3, ls="--")
    ax.text(len(data) - 0.4, 0.9375 * 1.06, "天花板 15/16 = 0.9375", color=RED,
            ha="right", va="bottom", fontsize=8.8)
    ax.set_yscale("log")
    ax.set_ylim(1e-3, 2)
    ax.set_xticks(xs); ax.set_xticklabels([d[0] for d in data], rotation=45, ha="right", fontsize=8.8)
    ax.set_ylabel("Tc / Θ_D（对数轴）", fontsize=9.2)
    ax.annotate("YBCO：0.237", xy=(11, 0.2365), xytext=(10.1, 0.55), fontsize=8.4, color=PINK,
                arrowprops=dict(arrowstyle="->", color=PINK, lw=0.8))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e3e3e3", lw=0.5)
    ax.set_axisbelow(True)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors.values()]
    ax.legend(handles, list(colors.keys()), frameon=False, fontsize=8.0, ncol=4,
              loc="upper center", bbox_to_anchor=(0.5, 1.13))
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "Figure3_tc_ceiling.png"), dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    fig_chain()
    fig_alpha_clock()
    fig_tc_ceiling()
    print("figures written to", FIG)
