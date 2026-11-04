import json, math
import common

kB = 1.380649e-23; h = 6.62607015e-34; c = 299792458.0; T = 310.15
f_c = kB * T / h; f0 = 64 * f_c; lam = c / f0 * 1e9
vals = {}
vals["f_c_THz"] = (f_c / 1e12, 6.4625, 0.01)
vals["f0_THz"] = (f0 / 1e12, 413.62, 0.01)
vals["lambda_nm"] = (lam, 724.84, 0.01)
vals["exp_m64"] = (math.exp(-64), 1.603e-28, 0.02)
vals["kBT64_eV"] = (64 * kB * T / 1.602176634e-19, 1.7105, 0.001)
vals["kBT64_kJmol"] = (64 * 8.314462618 * T / 1000, 165.0, 0.005)
vals["alpha4"] = ((7/8)**4, 0.586, 0.005)
vals["alpha80"] = ((7/8)**6, 0.449, 0.005)
vals["half_life_12.5"] = (math.log(2) / -math.log(0.875), 5.19, 0.01)
vals["half_life_1.25"] = (math.log(2) / -math.log(0.9875), 55.1, 0.01)
vals["intensity_Wcm2"] = (1e8 / (2 * 376.730313668) / 1e4, 13.3, 0.01)
# organ ledger
org = {"brain": (1.4, 240), "liver": (1.8, 200), "heart": (0.33, 440),
       "kidney": (0.31, 440), "muscle": (29, 13), "adipose": (14.5, 4.5),
       "rest": (22.66, 12)}
mass = sum(m for m, _ in org.values())
ree = sum(m * k for m, k in org.values())
four = sum(org[x][0] for x in ["brain", "liver", "heart", "kidney"])
four_q = sum(org[x][0] * org[x][1] for x in ["brain", "liver", "heart", "kidney"])
vals["organ_mass"] = (mass, 70.0, 0.001)
vals["REE"] = (ree, 1692, 0.001)
vals["four_mass"] = (four, 3.84, 0.001)
vals["four_share_mass"] = (four / mass * 100, 5.49, 0.01)
vals["four_q"] = (four_q, 977, 0.005)
vals["four_share_q"] = (four_q / ree * 100, 57.8, 0.005)
vals["mass_weighted"] = (ree / mass, 24.2, 0.01)
flux_weighted = sum((m * k / ree) * k for m, k in org.values())
vals["flux_weighted"] = (flux_weighted, 168.8, 0.01)
vals["ratio_weighted"] = (flux_weighted / (ree / mass), 7.0, 0.02)
vals["K_range"] = (440 / 4.5, 98, 0.01)
vals["K_vs_rest"] = (440 / 12, 37, 0.01)
atp = ree / 4.82 / 22.414 * 5.2 * 507 / 1000
vals["ATP_kg"] = (atp, 41.4, 0.01)
# CO refutation
sv = 5000 / 30
vals["SV_at_HR30"] = (sv, 167, 0.01)
vals["EDV_EF65"] = (sv / 0.65, 257, 0.01)
vals["EDV_EF80"] = (sv / 0.80, 209, 0.01)
vals["CO_maxSV"] = (120 * 30 / 1000, 3.6, 0.001)
vals["CO_deficit"] = ((5.0 - 3.6) / 5.0 * 100, 28, 0.02)

out = {}
ok = 0
for k, (comp, stated, tol) in vals.items():
    rel = abs(comp - stated) / abs(stated) if stated else 0
    passed = rel <= tol
    ok += passed
    out[k] = dict(computed=float(comp), stated=stated,
                  rel_err=round(float(rel), 6), pass_=bool(passed))
res = dict(passed=ok, total=len(vals), all_pass=(ok == len(vals)), items=out)
common.save_json("results_verify_book.json", res)
print(json.dumps(res, ensure_ascii=False, indent=1)[:1800])
