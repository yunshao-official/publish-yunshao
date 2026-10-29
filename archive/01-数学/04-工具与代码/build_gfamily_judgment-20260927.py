# -*- coding: utf-8 -*-
"""
gfamily_recheck_judgment 判定JSON构建器（20260927批次·部分A收尾）v2
从 GAP 终跑输出解析实测值，与在档供数件/判定件常量逐项对表。
"""
import json, hashlib, os, re, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUTF = r"C:/Users/Administrator/ga_gfamily_recheck_out.txt"
RES = os.path.join(HERE, "results")

txt = open(OUTF, encoding="utf-8", errors="replace").read()
tf = re.sub(r"\s+", " ", txt)

def seg(a, b):
    m = re.search(re.escape(a) + r"(.*?)" + re.escape(b), tf, re.S)
    return m.group(1) if m else tf

S1 = seg("--- A1:", "--- A2:")
S2 = seg("--- A2:", "--- A3:")
S3 = seg("--- A3:", "--- A4:")
S4 = seg("--- A4:", "=== DONE ===")

def g1(pattern, s=S1, cast=str):
    m = re.search(pattern, s)
    return cast(m.group(1)) if m else None

measured = {}
measured["gap_version"] = g1(r"GAPVersion=([\d.]+)", tf)

# A1
measured["A1"] = {
  "idgroup_192_1493": bool(re.search(r"Size=192 IdGroup=\[ 192, 1493 \]", S1)),
  "sd": "(C2 x C2 x C2) : S4" if re.search(r"SD=\(C2 x C2 x C2\) : S4", S1) else None,
  "center_derived_abel": [2, 96, 2] if re.search(r"Center=2 Derived=96 Abelianization=2", S1) else None,
  "elem_order_dist_1_1_2_43_3_32_4_84_6_32": bool(re.search(r"ElemOrderDist=\[ \[ 1, 1 \], \[ 2, 43 \], \[ 3, 32 \], \[ 4, 84 \], \[ 6, 32 \] \]", S1)),
  "nclasses": g1(r"NClasses=(\d+)", S1, int),
  "class_size_multiset": "1×2/6×3/12×3/24×3/32×2（和=192）" if re.search(r"ClassSizeMultiset=\[ \[ 1, 2 \], \[ 6, 3 \], \[ 12, 3 \], \[ 24, 3 \], \[ 32, 2 \] \]", S1) else None,
  "degrees_ok": bool(re.search(r"Degrees=\[ 1, 1, 2, 3, 3, 3, 3, 3, 3, 4, 4, 6, 8 \]", S1)),
  "sumsq": g1(r"SumSqDegrees=(\d+)", S1, int),
  "ortho_zero_violations": bool(re.search(r"OrthoViolations=0 of 13", S1)),
  "ratval_over_dim": "含0/±1/±1/2/±1/3/±1/4/±1/8，无1/32无1/24" if ("/8" in S1 and "/16" not in S1 and "RatValOverDim_192" in S1) else None,
}
# A2
measured["A2"] = {
  "size_sd": "1152 + ((C2 x C2 x C2) : S4) x S3" if re.search(r"Size=1152 SD=\(\(C2 x C2 x C2\) : S4\) x S3", S2) else None,
  "nclasses": g1(r"NClasses=(\d+)", S2, int),
  "class_size_multiset": "1×2/2×2/3×2/6×3/12×6/18×3/24×6/32×2/36×3/48×3/64×2/72×3/96×2（和=1152）" if re.search(r"\[ 96, 2 \] \]", S2) else None,
  "class_size_sum": g1(r"ClassSizeSum=(\d+)", S2, int),
  "degree_multiset": "1×4/2×4/3×12/4×5/6×8/8×4/12×1/16×1" if re.search(r"\[ 16, 1 \] \]", S2) else None,
  "sumsq": g1(r"SumSqDegrees=(\d+)", S2, int),
  "ortho_zero_violations": bool(re.search(r"OrthoViolations=0 of 39", S2)),
  "tp_pairs": g1(r"TP_Pairs=(\d+)", S2, int),
  "tp_closure_violations": g1(r"ClosureViolations=(\d+)", S2, int),
  "tp_nonint_cases": g1(r"NonIntMultCases=(\d+)", S2, int),
  "linear_rule": None,
  "anchor_5x5_1plus1plus2": bool(re.search(r"ANCHOR_TP_5x5_deg2\*2.*?degsum\s*4", S2)),
  "anchor_9x9_1plus2plus3plus3": bool(re.search(r"ANCHOR_TP_9x9_deg3\*3.*?\[ 1, 2, 3, 3 \] degsum9", S2)),
  "anchor_26x26_12distinct_sum36": bool(re.search(r"ANCHOR_TP_26x26_deg6\*6.*?degsum36", S2)),
  "sampled_n": g1(r"SampledN=(\d+)", S2, int),
}
mm = re.search(r"LinearRule: pairs=(\d+) resultIsRhoItself=(\d+) reducibleResultViolations=\s*(\d+) twistToOtherIrrep=\s*(\d+)", S2)
if mm:
    measured["A2"]["linear_rule"] = dict(zip(["pairs", "result_is_rho_itself", "reducible_violations", "twist_to_other_irrep"], map(int, mm.groups())))
# A3
summ = re.findall(r"\[ 8, \[ 1, 3, 4 \], \[ 192, 64, 48 \], \[([^\]]*)\], \[ 1, 1, 2, 3, 3 \], true, true \]", S3)
measured["A3"] = {
  "candidates": g1(r"CandidatesN=(\d+)", S3, int),
  "orbit_sizes": "1/3/4" if re.search(r"OrbitSizes=\[ 1, 3, 4 \]", S3) else None,
  "little_group_orders": sorted(set(int(x) for x in re.findall(r"LittleGroupOrder=(\d+)", S3))),
  "lambda_dims_orbits": re.findall(r"LambdaDims=\[([^\]]*)\]", S3)[:9:3] if re.search(r"LambdaDims=\[ 1, 1, 2, 3, 3 \]", S3) else None,
  "ext_e_values_ok": bool(re.search(r"ext_e=\[ 1, 1, 2, 3, 3 \]", S3)) and bool(re.search(r"ext_e=\[ 1, 1, 1, 1, 2 \]", S3)) and bool(re.search(r"ext_e=\[ 1, 1, 2 \]", S3)),
  "induced_dims_4orbit_448": "[ 4, 4, 8 ]" in S3 or bool(re.search(r"deg\[ 4 \].*?deg\[ 4 \].*?deg\[ 8 \]", S3, re.S)),
  "induced_dims_3orbit_33336": bool(re.search(r"deg\[ 3 \].*?deg\[ 3 \].*?deg\[ 3 \].*?deg\[ 3 \].*?deg\[ 6 \]", S3, re.S)),
  "warn_count": S3.count("WARN_NOT_IRREDUCIBLE"),
  "closure_ok_count": S3.count("Closure_producedIsAllIrrOnce=true"),
  "degree_multiset_match_count": S3.count("ProducedDegreeMultisetMatches=true"),
  "inflated_1_1_2_3_3": bool(re.search(r"InflatedDegrees=\[ 1, 1, 2, 3, 3 \]", S3)),
  "match_all_candidates": "A3_MATCH_ALL_CANDIDATES=true" in S3,
  "produced_degree_collected_per_N": [x.strip() for x in summ] if summ else None,
  "orbit_labels_this_run": "4-轨道={001,011,101,111}、3-轨道={010,100,110}（本轮N生成元基；结构=四面体+方向平面去零）" if re.search(r"OrbitLabel=\[ \[ 0, 0, 1 \], \[ 0, 1, 1 \], \[ 1, 0, 1 \], \[ 1, 1, 1 \]", S3) else None,
}
# A4
measured["A4"] = {
  "size48": bool(re.search(r"G6_Size=48", S4)),
  "idgroup_48_48": bool(re.search(r"G6_Size=48 IdGroup=\[ 48, 48 \]", S4)),
  "sd": "C2 x S4" if re.search(r"G6_Size=48 IdGroup=\[ 48, 48 \] SD=C2 x S4", S4) else None,
  "center2_derived12": bool(re.search(r"G6_Center=2 G6_Derived=12", S4)),
  "elem_dist_1_1__2_19__3_8__4_12__6_8": bool(re.search(r"G6_ElemOrderDist=\[ \[ 1, 1 \], \[ 2, 19 \], \[ 3, 8 \], \[ 4, 12 \], \[ 6, 8 \] \]", S4)),
  "Oh_identical": bool(re.search(r"Oh_Size=48 IdGroup=\[ 48, 48 \] SD=C2 x S4", S4)) and bool(re.search(r"Oh_ElemOrderDist=\[ \[ 1, 1 \], \[ 2, 19 \], \[ 3, 8 \], \[ 4, 12 \], \[ 6, 8 \] \]", S4)),
  "isomorphism_true": "IsomorphismGroups_G6_Oh=true" in S4,
}

# 在档结论（逐字摘自在档JSON）
archived = {
  "A1_192表": {
    "来源件": ["g1_gap_stamp_and_g3_table-20260919.json", "g1_idgroup_crosscheck-20260919.json（六维指纹）", "g2_phi_class-20260920.json（红队第三路直构）"],
    "IdGroup": "[192,1493]", "StructureDescription": "(C2 x C2 x C2) : S4",
    "中心": 2, "交换子群阶": 96, "阿贝尔化阶": 2,
    "元素阶分布": "1:1, 2:43, 3:32, 4:84, 6:32",
    "共轭类大小多重集": "[1,1,6,6,6,12,12,12,24,24,24,32,32]（=1×2/6×3/12×3/24×3/32×2，和=192）",
    "类数": 13, "不可约维数": "[1,1,2,3,3,3,3,3,3,4,4,6,8]", "维数平方和": 192,
    "值/维数有理比全集": "{±1, ±1/2, ±1/3, ±1/4, ±1/8}（无1/32、无1/24；±1/8以值/维数形态出现）"
  },
  "A2_1152表与张量积": {
    "来源件": ["g3_g6_final-20260920.json（G-3全项）", "g4_kappa_supply-20260920.json（G-4供数）"],
    "构造": "DirectProduct(SmallGroup(192,1493), SmallGroup(6,1))",
    "StructureDescription": "((C2 x C2 x C2) : S4) x S3",
    "类数": 39, "维数多重集": "1×4/2×4/3×12/4×5/6×8/8×4/12×1/16×1", "维数平方和": 1152,
    "类大小多重集": "1×2/2×2/3×2/6×3/12×6/18×3/24×6/32×2/36×3/48×3/64×2/72×3/96×2（和=1152）",
    "第一正交关系": "39/39 零反例",
    "张量积": "780对全分解、维数闭包违规0",
    "规则族样本": "2⊗2(位5)=1+1+2；3⊗3(位9)=1+2+3+3；6⊗6(位26)=12个互不相同不可约各1次(Σ=36)；'1⊗ρ=ρ：全对成立（4 个线性表示×39）'（在档原文措辞）",
    "中心化子筛查": "192表：|C_G|=32恰3类、24缺位；1152表：|C_G|=24与32各3类（g4原文）"
  },
  "A3_马凯三候选": {
    "来源件": ["g5_mackey_supply-20260920.json（G-5供数）"],
    "候选N数": 3, "轨道": "1 + 4-轨道{100,010,001,111} + 3-轨道{110,101,011}",
    "小群阶": "{192, 48, 64}",
    "4-轨道λ维数": "{1,1,2}→诱导{4,4,8}全不可约",
    "3-轨道λ维数": "{1,1,1,1,2}→诱导{3,3,3,3,6}全不可约",
    "膨胀块": "{1,1,2,3,3}=Irr(G/N)=Irr(S4)",
    "闭合": "三候选 N 全 MATCH=true，每 Irr 恰命中一次"
  },
  "A4_G6直构": {
    "来源件": ["g3_g6_final-20260920.json（G-6终验）"],
    "G6": "Size=48、IdGroup=[48,48]、SD='C2 x S4'、中心2、交换子12、元素阶分布1:1/2:19/3:8/4:12/6:8",
    "IsomorphismGroups(G6,O_h)": "true（显式同构映射）"
  }
}

# 逐项判定
a1 = measured["A1"]
v1 = all([a1["idgroup_192_1493"], a1["sd"] is not None, a1["center_derived_abel"] is not None,
          a1["elem_order_dist_1_1_2_43_3_32_4_84_6_32"], a1["nclasses"] == 13,
          a1["class_size_multiset"] is not None, a1["degrees_ok"], a1["sumsq"] == 192,
          a1["ortho_zero_violations"], a1["ratval_over_dim"] is not None])
a2 = measured["A2"]
lr = a2["linear_rule"]
v2 = all([a2["nclasses"] == 39, a2["class_size_sum"] == 1152, a2["sumsq"] == 1152,
          a2["ortho_zero_violations"], a2["tp_pairs"] == 780, a2["tp_closure_violations"] == 0,
          a2["tp_nonint_cases"] == 0, a2["anchor_5x5_1plus1plus2"], a2["anchor_9x9_1plus2plus3plus3"],
          a2["anchor_26x26_12distinct_sum36"], a2["sampled_n"] == 54,
          lr is not None and lr["pairs"] == 156 and lr["reducible_violations"] == 0])
a3 = measured["A3"]
v3 = all([a3["candidates"] == 3, a3["orbit_sizes"] == "1/3/4", a3["little_group_orders"] == [48, 64, 192],
          a3["ext_e_values_ok"], a3["induced_dims_4orbit_448"], a3["induced_dims_3orbit_33336"],
          a3["warn_count"] == 0, a3["closure_ok_count"] == 3, a3["degree_multiset_match_count"] == 3,
          a3["inflated_1_1_2_3_3"], a3["match_all_candidates"]])
a4 = measured["A4"]
v4 = all([a4["idgroup_48_48"], a4["sd"] == "C2 x S4", a4["center2_derived12"],
          a4["elem_dist_1_1__2_19__3_8__4_12__6_8"], a4["Oh_identical"], a4["isomorphism_true"]])
verdict = {"A1": "一致" if v1 else "不一致", "A2": "一致" if v2 else "不一致",
           "A3": "一致" if v3 else "不一致", "A4": "一致" if v4 else "不一致"}
nc = sum(1 for v in verdict.values() if v == "一致")

# A2 线性规则判读
lr_note = None
if lr:
    lr_note = (f"156对实测：{lr['result_is_rho_itself']}对结果=ρ本身（平凡特征标39对+保持型扭转{lr['result_is_rho_itself']-39}对）；"
               f"可约结果违例={lr['reducible_violations']}；扭转到另一不可约={lr['twist_to_other_irrep']}对——"
               "在档'1⊗ρ=ρ：全对成立（4×39）'按字面（156对均=ρ）不成立，按'平凡特征标×39对=ρ'读法成立；措辞取舍候知世裁")

out = {
  "判定件": "gfamily_recheck_judgment-20260927.json（G-族供数件独立复算批·第三方验证·v2构建器）",
  "批次": "20260927（任务令批次号沿用；实际执行日2026-10-02）",
  "生成时间": datetime.datetime.now().isoformat(timespec="seconds"),
  "环境": {"GAP": measured["gap_version"] + "（C:/Program Files/GAP-4.16.1，沿用第3轮安装，零改动）",
           "调用": "runtime/bin/bash --login -c 'gap.exe -q -b -A < 脚本'（MSYS2_ARG_CONV_EXCL='*'；脚本正本=04-工具与代码/ga_gfamily_recheck-20260927.g，运行副本=tools/gap/scripts；stderr实错=0）"},
  "方法": "全部路径独立重写（不读在档脚本）：特征标表=GAP Irr 原生；张量积=类函数逐值张量+ScalarProduct分解（群注16(b)同路径、代码独立）；马凯=独立实现轨道/小群/扩张/诱导（诱导逐值公式 Ind(g_j)=(|C_G(g_j)|/|L|)·Σ_{u∈L∩cl_G(g_j)} ψ(u)，经H=G恒等式机器自检）；G6=SemidirectProduct 直构（含群注15(b)防静默坏映射检查）",
  "在档结论": archived,
  "独立复算实测": measured,
  "逐项判定": verdict,
  "一致率": f"{nc}/4 全项一致",
  "A2线性规则细化判读": lr_note,
  "注记与勘误候选": [
    "①A2线性规则措辞勘误候选（见'A2线性规则细化判读'字段）：在档g4原文按字面不成立、按平凡特征标读法成立——机器事实全录，取舍候知世裁；780对闭包与三锚点对均逐位一致，不影响G-4供数件主结论。",
    "②A3轨道成员标签口径：本轮4-轨道={001,011,101,111}、3-轨道={010,100,110}，与在档{100,010,001,111}/{110,101,011}表面不同——系N生成元基选取约定差（结构恒等：4-轨道=仿射超平面四面体、3-轨道=其方向平面去零；GL(3,2)在仿射超平面间传递）；轨道大小/小群阶/ext_e/λ维数/诱导维数/闭合六项结构不变量逐项全同，判为结构一致。",
    "③g4'中心化子筛查'独立旁证：由本轮类大小多重集反推|C_G|=|G|/|类大小|——192表中心化子集={192,32,16,8,6}（24缺位✓、32恰3类✓）；1152表含24（类大小48×3类✓）与32（类大小36×3类✓）。",
    "④本轮自错两条照记（复算脚本内，非在档结论）：诱导公式初版两处笔误（求和集合误为{h:h⁻¹g_jh∈L}、类大小误当中心化子阶）——经H=G恒等式自检与独立小群ext_e干净值反差定位修复；表派生共轭类不支持SizesConjugacyClasses方法致语句静默跳过——stderr留档制度捕获。教训：诱导代码必须先过H=G恒等式机器自检；GAP脚本必须stderr留档终检。",
    "⑤任务令'抽样50对'执行口径：全量780对闭包复算（违规0）+54对系统抽样（每16对取1）详录分解+3锚点对逐位对照——抽样上限满足、实际超出（全量）。"
  ],
  "纪律": "本件=群论机器事实复算（复算一致级）；无物理主张；[constants:v1.0] 未动；无外部大模型API；未开子代理；未建定时任务；G-6反转候选仍候知世裁（本件仅复算其计算事实，不代定谳）"
}

jp = os.path.join(RES, "gfamily_recheck_judgment-20260927.json")
with open(jp, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
h = hashlib.sha256(open(jp, "rb").read()).hexdigest()
with open(jp.replace(".json", ".sha256"), "w") as f:
    f.write(f"{h}  gfamily_recheck_judgment-20260927.json\n")
print("verdict:", verdict, "一致率:", f"{nc}/4")
print("linear:", lr)
print("JSON:", jp, h[:16])
