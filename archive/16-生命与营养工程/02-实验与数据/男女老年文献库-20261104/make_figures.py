#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate publication-style figures for the sex-specific ageing evidence map."""
import json, re, statistics, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BASE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(BASE, "figures")
os.makedirs(FIG, exist_ok=True)

D = json.load(open(os.path.join(BASE, "文献主档-v1.0.json"), encoding="utf-8"))
FLOW = json.load(open(os.path.join(BASE, "检索流程计数-v1.0.json"), encoding="utf-8"))

MALE, FEMALE = "#2166ac", "#b2185b"
GREY = "#4d4d4d"
plt.rcParams.update({
    "font.family": "DejaVu Serif",
    "font.size": 8.5,
    "axes.linewidth": 0.7,
    "axes.edgecolor": "#333333",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

def core(sex):
    return [r for r in D["records"][sex] if r.get("analysis_set") == "core"]

def num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return int(x) if x > 0 else None
    s = str(x).replace(",", "").replace(" ", "")
    m = re.search(r"\d+(?:\.\d+)?", s)
    if not m:
        return None
    v = float(m.group())
    if "million" in s.lower():
        v *= 1_000_000
    return int(v) if v > 0 else None

# ---------------------------------------------------------------- Figure 1
def fig_flow():
    fig, ax = plt.subplots(figsize=(7.0, 8.0))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    def box(x, y, w, h, title, body="", fc="#f7f7f7", ec="#444444", fs=8.2, bold=False):
        p = FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                           linewidth=0.8, edgecolor=ec, facecolor=fc)
        ax.add_patch(p)
        if body:
            nlines = body.count("\n") + 1
            ty = y + h * (0.33 if nlines > 2 else 0.18)
            by = y - h * (0.02 if nlines > 2 else 0.18)
            ax.text(x, ty, title, ha="center", va="center", fontsize=fs,
                    fontweight="bold" if bold else "normal")
            ax.text(x, by, body, ha="center", va="center", fontsize=fs-0.6, color="#222222",
                    linespacing=1.15)
        else:
            ax.text(x, y, title, ha="center", va="center", fontsize=fs,
                    fontweight="bold" if bold else "normal")
    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9,
                                     linewidth=0.8, color="#444444"))
    box(36, 93, 66, 8.5, "Records identified through Europe PMC",
        f"64 topic-specific queries (16 topics × 2 sexes × 2 sort orders)\nTotal hits: {FLOW['hits_sum']:,}; top-ranked records retrieved: {FLOW['records_screened']:,}", "#e8eef5", bold=True, fs=7.7)
    arrow(36, 88.7, 36, 82.5)
    box(36, 79, 54, 7, "Unique records after de-duplication",
        f"n = {FLOW['unique_pmids']:,} unique PMIDs", "#e8eef5")
    arrow(36, 75.5, 36, 69.5)
    box(36, 66, 62, 7.5, "Title/abstract screening",
        "Sex marker + age marker in title; topic keyword in title or MeSH;\nEnglish, 2012–2026; abstract ≥250 characters", "#f7f7f7", fs=7.3)
    box(84, 66, 30, 11, "Excluded at screening",
        f"n = {FLOW['unique_pmids'] - FLOW['indexed']:,}\noff-topic; no sex/age marker;\neditorial/comment/letter;\nretraction; short abstract", "#fdf0f0", fs=6.4)
    arrow(67.5, 66, 68.5, 66)
    arrow(36, 62.2, 36, 55.5)
    box(36, 52, 56, 7, "Records indexed in the corpus",
        f"n = {FLOW['indexed']} (male {sum(1 for r in D['records']['male'] if r.get('analysis_set') in ('core','excluded_context'))}; "
        f"female {sum(1 for r in D['records']['female'] if r.get('analysis_set') in ('core','excluded_context'))})", "#e8f3e8", fs=7.7)
    box(84, 42, 30, 8, "Excluded after assessment",
        f"n = {FLOW['excluded']}\ncontext/population\nmismatch", "#fdf0f0", fs=6.6)
    arrow(64.5, 50.5, 68.5, 43.5)
    arrow(36, 48.3, 36, 41.5)
    box(36, 38, 56, 7, "Core analytic set",
        f"n = {FLOW['core']} studies (male {len(core('male'))}; female {len(core('female'))})", "#e8f3e8", bold=True, fs=7.7)
    arrow(36, 34.3, 36, 25.5)
    box(50, 20, 86, 9.5, "Synthesis",
        "Evidence map (16 topics × 2 sexes) · design and sample-size profile ·\nsex-specific narrative synthesis · conceptual loss–repair mapping", "#eef3fa", fs=7.6)
    ax.text(99, 1.2, "Abstract-level screening; full texts were not retrieved for all records.",
            ha="right", va="bottom", fontsize=6.4, color=GREY, style="italic")
    fig.savefig(os.path.join(FIG, "Figure1_study_flow.png"), dpi=300)
    plt.close(fig)

# ---------------------------------------------------------------- Figure 2
def fig_heatmap():
    topics = sorted(set(r["topic"] for r in core("male")) | set(r["topic"] for r in core("female")))
    rows = []
    for t in topics:
        m = sum(1 for r in core("male") if r["topic"] == t)
        f = sum(1 for r in core("female") if r["topic"] == t)
        rows.append((t, m, f))
    rows.sort(key=lambda z: (-(z[1] + z[2]), z[0]))
    labels = [r[0].replace("_", " ") for r in rows]
    mat = np.array([[r[1], r[2]] for r in rows])
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    im = ax.imshow(mat, cmap="YlGnBu", vmin=0, vmax=max(6, mat.max()), aspect="auto")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Male", "Female"], fontsize=9)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=8)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat[i, j]
            ax.text(j, i, str(v), ha="center", va="center", fontsize=8.5,
                    color="white" if v >= 4 else "#1a1a1a", fontweight="bold" if v >= 4 else "normal")
    ax.set_xticks(np.arange(-.5, 2, 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(labels), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.tick_params(which="minor", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("Core studies (n)", fontsize=7.5)
    cb.ax.tick_params(labelsize=7)
    ax.set_title("Evidence density by topic and sex (n = 119)", fontsize=10, pad=8)
    fig.savefig(os.path.join(FIG, "Figure2_evidence_map.png"), dpi=300)
    plt.close(fig)
    return rows

# ---------------------------------------------------------------- Figure 3
def fig_year_design():
    years = list(range(2014, 2027))
    mc = {y: 0 for y in years}; fc = {y: 0 for y in years}
    for r in core("male"):
        y = int(r["year"]); mc[y] = mc.get(y, 0) + 1
    for r in core("female"):
        y = int(r["year"]); fc[y] = fc.get(y, 0) + 1
    def grp(design):
        d = (design or "").lower()
        if "random" in d: return "Randomised trial"
        if "meta" in d or "systematic" in d or "review" in d: return "Review / meta-analysis"
        if "cohort" in d or "longitudinal" in d: return "Cohort / longitudinal"
        return "Cross-sectional / other"
    groups = ["Randomised trial", "Cohort / longitudinal", "Cross-sectional / other", "Review / meta-analysis"]
    gcol = {"Randomised trial": "#66c2a5", "Cohort / longitudinal": "#8da0cb",
            "Cross-sectional / other": "#fc8d62", "Review / meta-analysis": "#e78ac3"}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.05), gridspec_kw={"width_ratios": [1.55, 1]})
    ax = axes[0]
    ax.bar(years, [mc.get(y, 0) for y in years], color=MALE, label="Male", width=0.62)
    ax.bar(years, [fc.get(y, 0) for y in years], bottom=[mc.get(y, 0) for y in years],
           color=FEMALE, label="Female", width=0.62)
    ax.set_xlabel("Publication year"); ax.set_ylabel("Core studies (n)")
    ax.set_xticks(years); ax.set_xticklabels([str(y) for y in years], rotation=45, ha="right")
    ax.legend(frameon=False, fontsize=8.0, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xticklabels([str(y) for y in years], rotation=45, ha="right", fontsize=7.5)
    ax.set_title("A  Publication year", loc="left", fontsize=10, fontweight="bold")
    ax = axes[1]
    ypos = np.arange(len(groups))
    for i, sex in enumerate(["male", "female"]):
        vals = [sum(1 for r in core(sex) if grp(r.get("design")) == g) for g in groups]
        left = 0
        for v, g in zip(vals, groups):
            ax.barh(i, v, left=left, color=gcol[g], edgecolor="white", height=0.55)
            if v > 0:
                ax.text(left + v/2, i, str(v), ha="center", va="center", fontsize=8.0,
                        color="white" if g != "Randomised trial" else "#123")
            left += v
    ax.set_yticks([0, 1]); ax.set_yticklabels(["Male", "Female"])
    ax.set_xlabel("Core studies (n)")
    ax.set_title("B  Design composition", loc="left", fontsize=10, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=gcol[g]) for g in groups]
    ax.legend(handles, groups, frameon=False, fontsize=7.2, loc="lower center",
              bbox_to_anchor=(0.5, -0.42), ncol=2, handlelength=1.0, columnspacing=1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "Figure3_year_design.png"), dpi=300)
    plt.close(fig)

# ---------------------------------------------------------------- Figure 4
def fig_sample():
    data, labels, colors = [], [], []
    for sex, col in [("male", MALE), ("female", FEMALE)]:
        vals = [num(r.get("n_reported")) for r in core(sex)]
        vals = [v for v in vals if v and v >= 10]
        data.append(vals); labels.append(f"{sex.capitalize()}\n(n={len(vals)})"); colors.append(col)
    fig, ax = plt.subplots(figsize=(5.9, 3.7))
    stats = []
    for vals in data:
        q1, med, q3 = statistics.quantiles(vals, n=4)
        iqr = q3 - q1
        lo = min(v for v in vals if v >= q1 - 1.5 * iqr)
        hi = max(v for v in vals if v <= q3 + 1.5 * iqr)
        stats.append(dict(q1=q1, med=med, q3=q3, whislo=lo, whishi=hi, fliers=[]))
    bp = ax.bxp(stats, widths=0.42, patch_artist=True, showfliers=False,
                medianprops=dict(color="black", linewidth=1.0),
                whiskerprops=dict(linewidth=0.8), capprops=dict(linewidth=0.8))
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c); patch.set_alpha(0.28); patch.set_edgecolor(c)
    rng = np.random.default_rng(20261104)
    for i, (vals, c) in enumerate(zip(data, colors)):
        x = rng.normal(i + 1, 0.055, len(vals))
        ax.scatter(x, vals, s=9, color=c, alpha=0.65, linewidths=0, zorder=3)
    ax.set_yscale("log")
    ax.set_ylabel("Reported sample size (log scale)")
    ax.set_xticks([1, 2]); ax.set_xticklabels(labels)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#dddddd", linewidth=0.5, zorder=0)
    for i, vals in enumerate(data, 1):
        med = statistics.median(vals)
        ax.hlines(med, i - 0.22, i + 0.22, color="black", linewidth=1.0)
    ax.set_title("Reported sample sizes by sex (studies with extractable n)", fontsize=10)
    fig.savefig(os.path.join(FIG, "Figure4_sample_sizes.png"), dpi=300)
    plt.close(fig)

# ---------------------------------------------------------------- extra stats
def stats_extra(rows):
    out = {}
    for sex in ["male", "female"]:
        recs = core(sex)
        nvals = [(r["pmid"], num(r.get("n_reported"))) for r in recs]
        nvals = [(p, v) for p, v in nvals if v and v >= 10]
        vals = sorted(v for _, v in nvals)
        out[sex] = {
            "n_core": len(recs),
            "n_with_n": len(vals),
            "sum_n": sum(vals),
            "median_n": statistics.median(vals),
            "q1": statistics.quantiles(vals, n=4)[0],
            "q3": statistics.quantiles(vals, n=4)[2],
            "max_n": max(vals),
            "largest": sorted(nvals, key=lambda z: -z[1])[:5],
            "median_year": statistics.median(int(r["year"]) for r in recs),
            "mixed_population": sum(1 for r in recs if r.get("population") == "mixed"),
        }
    # primary studies only (exclude review/meta)
    def is_review(r):
        d = (r.get("design") or "").lower()
        return "meta" in d or "systematic" in d or "review" in d
    for sex in ["male", "female"]:
        vals = [num(r.get("n_reported")) for r in core(sex) if not is_review(r)]
        vals = [v for v in vals if v and v >= 10]
        out[sex]["n_primary_with_n"] = len(vals)
        out[sex]["sum_n_primary"] = sum(vals)
    out["topics"] = [{"topic": t, "male": m, "female": f, "total": m + f} for t, m, f in rows]
    json.dump(out, open(os.path.join(BASE, "统计摘要-扩展-v1.0.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    fig_flow()
    rows = fig_heatmap()
    fig_year_design()
    fig_sample()
    stats_extra(rows)
    print("figures written to", FIG)
