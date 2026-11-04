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
    fig.savefig(os.path.join(FIG, "Figure4_alpha_clock.png"), dpi=300)
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
    fig.savefig(os.path.join(FIG, "Figure2_tc_ceiling.png"), dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    fig_chain()
    fig_alpha_clock()
    fig_tc_ceiling()
    print("figures written to", FIG)


def fig_organ_ledger():
    """Organ mass-specific metabolic rate vs organ mass (log-log)."""
    organs = [
        # name, mass kg, kcal/kg/day, color, label offset in points
        ("脑", 1.4, 240, BLUE, (8, 9)),
        ("肝", 1.8, 200, AMBER, (9, -12)),
        ("心", 0.30, 440, RED, (-4, 12)),
        ("肾", 0.37, 440, PINK, (-6, -16)),
        ("骨骼肌", 29.0, 13, GREEN, (-12, -24)),
        ("脂肪", 14.5, 4.5, "#8c6d31", (9, -10)),
        ("其余组织", 22.66, 12, "#9e9e9e", (-40, 8)),
    ]
    total = sum(m * k for _, m, k, _, _ in organs)
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    for name, m, k, c, off in organs:
        share = m * k / total * 100
        ax.scatter(m, k, s=28 + share * 16, color=c, alpha=0.80,
                   edgecolor="white", linewidth=0.8, zorder=3)
        ax.annotate(name, (m, k), xytext=off, textcoords="offset points",
                    fontsize=8.4, color=INK, ha="left", va="center")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(0.18, 55); ax.set_ylim(1.6, 900)
    ax.set_xlabel("器官/组织质量（kg，对数）", fontsize=9.2)
    ax.set_ylabel("质量比静息产热（kcal kg$^{-1}$ d$^{-1}$，对数）", fontsize=9.2)
    ax.tick_params(labelsize=8.8)
    ax.grid(True, which="major", color="#e6e6e6", lw=0.6)
    ax.set_axisbelow(True)
    avg = total / 70.0
    ax.axhline(avg, color=GREY, ls=(0, (4, 3)), lw=0.9, zorder=1)
    ax.text(0.20, avg * 1.07, f"全身平均 {avg:.1f}", fontsize=7.8, color=GREY)
    xs = np.array([0.3, 40])
    ax.plot(xs, avg * (xs / 70.0) ** (-0.25), color="#b0b0b0", lw=1.0,
            ls=(0, (1, 2)), zorder=1)
    ax.text(30, avg * (30 / 70.0) ** (-0.25) * 1.12, "斜率 −1/4 参考",
            fontsize=7.4, color="#8a8a8a", ha="right")
    ax.annotate("脑+肝+心+肾：\n5.5% 质量，约 58% 耗氧",
                xy=(0.55, 445), xytext=(2.3, 690), fontsize=8.0, color=RED,
                ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=RED, lw=0.8))
    ax.set_title("器官账本：质量只解释很小一部分代谢", fontsize=10.2, pad=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "Figure3_organ_ledger.png"), dpi=300)
    plt.close(fig)


def fig_decline():
    """Normalised functional trajectories vs age, with the alpha line."""
    age = np.arange(20, 81, 1.0)

    def piecewise(rates):
        # rates: list of (start_age, fractional_loss_per_year)
        y = np.ones_like(age)
        for i, t in enumerate(age):
            if i == 0:
                continue
            r = [v for a, v in rates if t >= a][-1]
            y[i] = y[i - 1] * (1 - r)
        return y

    vo2 = piecewise([(20, 0.005), (40, 0.010), (60, 0.020)])
    gfr = piecewise([(20, 0.0), (40, 0.009)])
    fev1 = piecewise([(20, 0.0), (25, 0.008)])
    bmd = piecewise([(20, 0.0), (35, 0.010), (50, 0.020), (60, 0.010)])
    hippo = piecewise([(20, 0.0), (55, 0.015)])
    lens = np.exp(-0.0576 * (age - 20))
    ovary = np.exp(-0.130 * (age - 20))
    alpha = (7.0 / 8.0) ** ((age - 20) / 10.0)

    fig, ax = plt.subplots(figsize=(7.4, 4.7))
    funcs = np.vstack([vo2, gfr, fev1, bmd])
    ax.fill_between(age, funcs.min(0), funcs.max(0), color="#9e9e9e",
                    alpha=0.10, lw=0, zorder=0)
    ax.plot(age, vo2, color=BLUE, lw=1.7, label="最大摄氧量（加速下降）")
    ax.plot(age, gfr, color=GREEN, lw=1.7, label="肾小球滤过率")
    ax.plot(age, fev1, color="#1f8a8a", lw=1.7, label="FEV$_1$")
    ax.plot(age, bmd, color=AMBER, lw=1.7, label="骨密度（含绝经期）")
    ax.plot(age, hippo, color="#7f7f7f", lw=1.3, ls=(0, (1, 2)), label="海马体积")
    ax.plot(age, lens, color=PINK, lw=1.3, ls=(0, (5, 2)), label="晶状体调节力")
    ax.plot(age, ovary, color="#7b3294", lw=1.3, ls=(0, (4, 2, 1, 2)), label="卵巢储备")
    ax.plot(age, alpha, color=INK, lw=2.6, ls=(0, (7, 3)), label="α 十年读法 (7/8)$^{(t-20)/10}$", zorder=5)

    ax.set_xlim(20, 80); ax.set_ylim(0, 1.08)
    ax.set_xlabel("年龄（岁）", fontsize=9.2)
    ax.set_ylabel("相对 20 岁的功能（归一化）", fontsize=9.2)
    ax.tick_params(labelsize=8.8)
    ax.grid(True, color="#ececec", lw=0.6)
    ax.set_axisbelow(True)
    ax.axvline(60, color="#c9c9c9", lw=0.8, ls=":")
    ax.annotate("α 线：功能集合的下包络\n80 岁 0.449", xy=(78, 0.46),
                xytext=(62.0, 0.28), fontsize=7.8, color=INK,
                arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7))
    ax.annotate("晶状体/卵巢：\n同一 α 不适用", xy=(64, 0.09), xytext=(67.0, 0.17),
                fontsize=7.8, color=PINK,
                arrowprops=dict(arrowstyle="-", color=PINK, lw=0.7))
    ax.legend(fontsize=7.2, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.17),
              frameon=False, handlelength=2.2, columnspacing=1.0)
    ax.set_title("功能性器官集合跟随 α 线；材料与储备系统不跟随", fontsize=10.2, pad=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "Figure5_decline.png"), dpi=300)
    plt.close(fig)
