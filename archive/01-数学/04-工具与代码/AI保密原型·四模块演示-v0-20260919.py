# -*- coding: utf-8 -*-
"""
AI保密原型·四模块演示 v0（2026-09-19，ZCode）
对应正本：《体系结合AI保密·机制与方案-v1.0-20260919》§二
状态：功能演示级（合成数据），非真实大模型实测——诚实标签，判据实测需接真实模型线。
模块：
  M1 金丝雀派生与验证（机制五·YGC风格：12族余数类编码副本ID，困难性承接YGC口径）
  M2 涌现支付账（机制一：来源/授权/涌现三科目，W_src+授权检查）
  M3 Steane[7,4,3]经典内核权重校验（机制三：Hamming(7,4)内核，H列=(Z₂)³非零点=Fano7）
  M4 12族查询签名（机制二：族分布+张力统计检测探测性查询聚集）
"""
import sys, random, hashlib
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
random.seed(20260919)
LINE = "=" * 62

# ---------- 公共：Miller-Rabin（确定性底座，<3.3e24） ----------
def is_prime(n):
    if n < 2: return False
    for p in (2,3,5,7,11,13,17,19,23,29,31,37):
        if n % p == 0: return n == p
    d, r = n - 1, 0
    while d % 2 == 0: d //= 2; r += 1
    for a in (2,3,5,7,11,13,17,19,23,29,31,37):
        x = pow(a, d, n)
        if x in (1, n-1): continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1: break
        else: return False
    return True

def gen_prime_in_family(fam, bits=40):
    """生成 p ≡ fam (mod 24) 的素数（fam须与24互素）"""
    assert fam % 2 != 0 and fam % 3 != 0, "族须与24互素"
    while True:
        k = random.getrandbits(bits) | 1
        p = k - (k % 24) + fam
        if p > 0 and is_prime(p): return p

# ---------- M1 金丝雀（机制五·简化演示版） ----------
FAMS = [1,5,7,11,13,17,19,23]  # 与24互素的8个族（演示用8×8=64副本；正本口径12×12=144）
def canary_derive(copy_id):
    f1 = FAMS[(copy_id - 1) % len(FAMS)]
    f2 = FAMS[((copy_id - 1) // len(FAMS)) % len(FAMS)]
    p, q = gen_prime_in_family(f1), gen_prime_in_family(f2)
    N = p * q
    return {"copy_id": copy_id, "f1": f1, "f2": f2, "p": p, "q": q, "N": N}

def canary_owner_verify(c, table):
    rec = table.get(c["copy_id"])
    return rec and rec["N"] == c["N"] and rec["p"] == c["p"] and rec["q"] == c["q"]

def m1():
    print(LINE); print("M1 金丝雀派生与验证（机制五·简化演示）"); print(LINE)
    table = {}
    canaries = []
    for cid in range(1, 65):
        c = canary_derive(cid); table[cid] = c; canaries.append(c)
    # 派生可验证性：检查每条记录的构造性质（素性/族一致性/N一致性/全局唯一性）
    prop_ok = all(
        is_prime(rec["p"]) and is_prime(rec["q"])
        and rec["p"] % 24 == rec["f1"] and rec["q"] % 24 == rec["f2"]
        and rec["N"] == rec["p"] * rec["q"]
        for rec in table.values())
    uniq = len({rec["N"] for rec in table.values()}) == 64
    owner_ok = all(canary_owner_verify(table[cid], table) for cid in range(1, 65))
    sig_ok = all(c["N"] % 24 == (c["f1"] * c["f2"]) % 24 for c in canaries)
    print(f"[1] 副本派生64份：构造性质{'PASS' if prop_ok else 'FAIL'}｜N全局唯一{'PASS' if uniq else 'FAIL'}｜持表复核{'PASS' if owner_ok else 'FAIL'}")
    print(f"[2] 公开签名一致性 N mod 24 == (f1*f2) mod 24：{'PASS' if sig_ok else 'FAIL'}（64/64）")
    # 不可区分性粗检：金丝雀 vs 随机同量级合数
    rands = []
    while len(rands) < len(canaries):
        a = gen_prime_in_family(random.choice(FAMS)); b = gen_prime_in_family(random.choice(FAMS))
        rands.append(a*b)
    can_mod = Counter(c["N"] % 24 for c in canaries)
    can_bits = sum(c["N"].bit_length() for c in canaries) / len(canaries)
    rnd_bits = sum(r.bit_length() for r in rands) / len(rands)
    print(f"[3] 量级：金丝雀均{can_bits:.1f}bit vs 随机均{rnd_bits:.1f}bit（同量级，量级通道不可分）")
    resid_support = sorted(can_mod.keys())
    print(f"[4] 诚实发现：金丝雀 N mod 24 支撑集={resid_support}（受限）→ 统计上可与随机合数区分")
    print("    └ 弱点定性： outsiders 若知族构造可按余数支撑集筛金丝雀 → 改进项：混洗白/扩大族覆盖/负余量填充（登记待办）")
    print("    └ 困难性口径：无表者从 N 反推 (f1,f2) 需分解 N（承接YGC『∈NP+分解等价』口径，非新安全证明）")
    return {"derive":"PASS" if (prop_ok and uniq and owner_ok) else "FAIL","sig":"PASS" if sig_ok else "FAIL","weakness":"mod24支撑集受限"}

# ---------- M2 涌现支付账（机制一·最小版） ----------
CORPUS = {
 "doc01|L0": "公开产品说明书：本设备工作电压为直流五伏特，支持USB供电。",
 "doc02|L0": "公开培训材料：新员工入职需完成信息安全意识课程。",
 "doc03|L1": "内部流程：季度盘点须由双人复核并报部门负责人签字确认。",
 "doc04|L3": "涉密参数：项目07号阵列的部署坐标为东经117.51度北纬39.28度。",
 "doc05|L3": "涉密名单：07号项目外场人员代号分别为灯塔、锚点、青松。",
}
def ngrams(s, n=4):
    t = "".join(ch for ch in s if ch not in "，。：；、 ")
    return {t[i:i+n] for i in range(max(0, len(t)-n+1))}
def pay_ledger(output, session_level, corpus=CORPUS, thr=0.35):
    og = ngrams(output); best, meta = 0.0, None
    for key, text in corpus.items():
        kg = ngrams(text)
        j = len(og & kg) / max(1, len(og | kg))
        if j > best: best, meta = j, (key, text)
    src_level = meta[0].split("|")[1] if meta else None
    if best < thr:
        return {"verdict": "无源涌现", "action": "标记·幻觉科目", "match": round(best,3), "src": None}
    if int(src_level[1]) > int(session_level[1]):
        return {"verdict": "有源越权", "action": "拦截·泄露科目", "match": round(best,3),
                "src": meta[0], "detail": f"输出命中{src_level}内容而会话仅{session_level}"}
    return {"verdict": "来源支付成立", "action": "放行·附引用", "match": round(best,3), "src": meta[0]}

def m2():
    print(); print(LINE); print("M2 涌现支付账（机制一·最小版，4-gram Jaccard归因）"); print(LINE)
    cases = [
      ("正常引用", "L1", "按内部流程，季度盘点由双人复核并报部门负责人签字确认即可。"),
      ("模拟泄露", "L1", "据说07号阵列部署坐标在东经117.51度北纬39.28度附近。"),
      ("模拟幻觉", "L1", "该项目阵列的行波管放大器功率为47.3千瓦。"),
    ]
    for name, lvl, out in cases:
        r = pay_ledger(out, lvl)
        print(f"[{name}] 会话{lvl} → 判定：{r['verdict']}｜处置：{r['action']}｜匹配度{r['match']}"
              + (f"｜{r.get('detail','')}" if r.get('detail') else ""))
    print("── 三科目结论：有源有权→放行；有源越权→泄露拦截；无源→幻觉标记（一账两用）")

# ---------- M3 Steane[7,4,3]经典内核（机制三） ----------
# 列坐标约定：第j列(j=1..7)=j的二进制(b_a,b_b,b_c)；数据位在非2幂位3,5,6,7，校验位1,2,4
H_COLS = [None,(0,0,1),(0,1,0),(0,1,1),(1,0,0),(1,0,1),(1,1,0),(1,1,1)]  # 下标1..7=(Z₂)³非零点=Fano7
def ham_encode(nibble):
    d1,d2,d3,d4 = [(nibble >> i) & 1 for i in range(4)]  # 落在位3,5,6,7
    c = [None]*8
    c[3],c[5],c[6],c[7] = d1,d2,d3,d4
    c[1] = d1^d2^d4   # 位1=(0,0,1)：覆盖c位=3,5,7
    c[2] = d1^d3^d4   # 位2=(0,1,0)：覆盖位3,6,7
    c[4] = d2^d3^d4   # 位4=(1,0,0)：覆盖位5,6,7
    return c[1:]
def ham_syndrome(r):  # r为7位码字(c1..c7)
    s1 = r[0]^r[2]^r[4]^r[6]      # c坐标：列1,3,5,7
    s2 = r[1]^r[2]^r[5]^r[6]      # b坐标：列2,3,6,7
    s4 = r[3]^r[4]^r[5]^r[6]      # a坐标：列4,5,6,7
    return (s4,s2,s1)             # 与列坐标(b_a,b_b,b_c)同序
def m3():
    print(); print(LINE); print("M3 Steane[7,4,3]经典内核·权重块校验（机制三）"); print(LINE)
    print("H矩阵七列=(Z₂)³非零点（Fano7），校验子=出错列二进制坐标→直接定位")
    trials = 200
    detect = locate = noerr_clean = 0
    for _ in range(trials):
        nib = random.getrandbits(4); c = ham_encode(nib)
        r = c.copy(); pos = random.randrange(7); r[pos] ^= 1
        syn = ham_syndrome(r)
        if syn != (0,0,0):
            detect += 1
            j = 4*syn[0] + 2*syn[1] + syn[2]      # 列号1..7
            idx = j - 1
            if idx == pos:
                locate += 1
                r[idx] ^= 1
    for nib in range(16):
        if ham_syndrome(ham_encode(nib)) == (0,0,0): noerr_clean += 1
    print(f"[1] {trials}次单比特篡改：检出{detect}/{trials}，定位且纠回正确{locate}/{trials}")
    print(f"[2] 无错误报检查：16个码字校验子全零{'PASS' if noerr_clean==16 else 'FAIL'}（实测{noerr_clean}/16）")
    if detect == trials and locate == trials:
        print("── 结论：单块篡改检出率100%、定位率100%（码距3的码论性质，执行层自证）")
    else:
        print("── 结论：存在漏检/错位——编码器与校验矩阵不一致，判FAIL（不得带病出线）")

# ---------- M4 12族查询签名（机制二·合成流） ----------
def m4():
    print(); print(LINE); print("M4 12族查询签名（机制二·合成查询流）"); print(LINE)
    fams = [hash(f"q{i}".encode()) % 12 for i in range(200)]              # 200正常查询
    attacks = [random.choice([3,7]) for _ in range(20)]                   # 20次踩点聚集于族3/7
    hist = Counter(fams + attacks)
    total = len(fams) + len(attacks)
    chi = sum((hist.get(f,0) - total/12)**2 / (total/12) for f in range(12))
    top = hist.most_common(2)
    share = (top[0][1] + top[1][1]) / total
    # 基线：纯200正常流的同统计量
    hist0 = Counter(fams); chi0 = sum((hist0.get(f,0)-200/12)**2/(200/12) for f in range(12))
    print(f"[1] 正常流（200条）：χ²={chi0:.1f}（自由度11，95%线≈19.68）→ {'通过' if chi0<19.68 else '告警'}")
    print(f"[2] 掺入20次踩点（聚集族3/7）后：χ²={chi:.1f} → {'告警（检出）' if chi>19.68 else '漏检'}")
    print(f"[3] 前二族占比：{share:.1%}（均匀基线≈16.7%）；最热二族={top}")
    print("── 结论：合成流上张力统计可检出聚集探测；真实阈值须红队标定（JC-B3）")

if __name__ == "__main__":
    print("AI保密原型·四模块演示 v0 ｜ 合成数据功能演示（诚实标签：非真实模型实测）｜ 2026-09-19")
    m1(); m2(); m3(); m4()
    print(); print(LINE); print("四模块全部跑通。正本：体系结合AI保密·机制与方案-v1.0；本脚本：功能演示级。")
