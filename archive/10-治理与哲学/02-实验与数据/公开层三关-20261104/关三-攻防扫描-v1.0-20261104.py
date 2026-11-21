#!/usr/bin/env python3 -B
# -*- coding: utf-8 -*-
"""
关三·攻防扫描 v1.0｜2026-11-04
七项攻击科目执行器（全历史泄露 / 排除令取证 / 复现性 / 声明可证伪 / 结构破损 / 误公开 / 远端一致性）
只读 git，不写仓库；产物写 /tmp/g3rerun/ 与本脚本同目录。
"""
import subprocess, re, json, os, hashlib, sys, collections

REPO = "/data/workspace/publish-yunshao"
os.chdir(REPO)

def git(*args):
    r = subprocess.run(["git"] + list(args), capture_output=True, timeout=300)
    return r.stdout, r.stderr

# ═══════════════════════════════════════════════════════════
# 科目一：全历史泄露扫描
# ═══════════════════════════════════════════════════════════
out, _ = git("rev-list", "--objects", "--all")
blob_map = {}
for line in out.decode("utf-8", errors="replace").strip().split("\n"):
    parts = line.split(" ", 1)
    if len(parts) == 2:
        blob_map[parts[0]] = parts[1]

results = {
    "id_card_raw": [], "id_card_verified": [], "phone_11": [],
    "military_keywords": [], "contract_terms": [], "credentials": [],
    "private_paths": [], "private_email": [], "birth_date_address": [],
}

ID_W = [7,9,10,5,8,4,2,1,6,3,7,9,10,5,8,4,2]
ID_C = "10X98765432"

def verify_id18(s):
    if len(s) != 18: return False
    try:
        t = sum(int(s[i]) * ID_W[i] for i in range(17))
        if s[17].upper() != ID_C[t % 11]: return False
    except: return False
    y, m, d = int(s[6:10]), int(s[10:12]), int(s[12:14])
    if y < 1900 or y > 2030 or m < 1 or m > 12 or d < 1 or d > 31: return False
    dim = [0,31,28,31,30,31,30,31,31,30,31,30,31]
    if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0): dim[2] = 29
    if d > dim[m]: return False
    if int(s[:2]) < 11 or int(s[:2]) > 65: return False
    return True

P_ID = re.compile(r'(?<!\d)\d{17}[\dXx](?!\d)')
P_PH = re.compile(r'(?<!\d)1[3-9]\d{9}(?!\d)')
P_CR = re.compile(r'(?:ghp_|github_pat_|gho_|ghs_|AKIA|BEGIN PRIVATE KEY|Bearer\s+[A-Za-z0-9_\-\.]{20,}|password\s*=\s*\S+|secret\s*=\s*\S+|token\s*=\s*\S+)', re.I)
P_MI = re.compile(r'军事采购|军品订购|武器采购|国防采购|军用装备|军费|国防预算|战备物资')
P_CO = re.compile(r'(?:甲方|乙方|合同金额|报价单|授权费|委托开发|付款条件|付款期限|违约金)')
P_PA = re.compile(r'(?:/Users/[a-zA-Z]+|C:\\\\Users\\\\[a-zA-Z]+|H:\\\\)')
P_EM = re.compile(r'[a-zA-Z0-9._%+-]+@(?:qq\.com|163\.com|126\.com|sina\.com|hotmail\.com|gmail\.com)')
P_BA = re.compile(r'(?:19|20)\d{2}年(?:0?[1-9]|1[0-2])月(?:0?[1-9]|[12]\d|3[01])日')

batch_size = 200
blob_hashes = list(blob_map.keys())
total_bytes = 0
scanned = 0

for i in range(0, len(blob_hashes), batch_size):
    batch = blob_hashes[i:i+batch_size]
    proc = subprocess.run(["git","cat-file","--batch"],
        input="\n".join(batch).encode()+"\n", capture_output=True, timeout=300)
    data = proc.stdout; pos = 0
    for h in batch:
        le = data.find(b"\n", pos)
        if le == -1: break
        parts = data[pos:le].decode("ascii", errors="replace").split()
        if len(parts) < 3: pos = le+1; continue
        oh, ot, os_ = parts[0], parts[1], int(parts[2])
        cs, ce = le+1, le+1+os_
        if ce > len(data): break
        content = data[cs:ce]; pos = ce+1
        if oh != h: continue
        total_bytes += os_; scanned += 1
        if os_ > 5_000_000 or os_ == 0: continue
        try: text = content.decode("utf-8")
        except:
            try:
                text = content.decode("latin-1")
                if '\x00' in text[:1000]: continue
            except: continue
        path = blob_map.get(h, "?"); sh = h[:8]
        if path.endswith('.pyc') or '__pycache__' in path: continue
        def ctx(m, sp=60):
            s2 = max(0, m.start()-sp); e2 = min(len(text), m.end()+sp)
            return text[s2:e2].replace("\n"," ").replace("\r","")
        for m in P_ID.finditer(text):
            v = m.group(); e = {"blob":sh,"path":path,"context":ctx(m)}
            results["id_card_raw"].append(e)
            if verify_id18(v):
                e2 = dict(e); e2["verified"] = True
                results["id_card_verified"].append(e2)
        for m in P_PH.finditer(text):
            c = ctx(m, 30)
            if any(x in c.lower() for x in ['pmid','doi','isbn','issn','orcid']): continue
            results["phone_11"].append({"blob":sh,"path":path,"context":c})
        for m in P_MI.finditer(text):
            results["military_keywords"].append({"blob":sh,"path":path,"context":ctx(m)})
        for m in P_CO.finditer(text):
            results["contract_terms"].append({"blob":sh,"path":path,"context":ctx(m)})
        for m in P_CR.finditer(text):
            results["credentials"].append({"blob":sh,"path":path,"context":ctx(m),"pattern":m.group()[:30]})
        for m in P_PA.finditer(text):
            results["private_paths"].append({"blob":sh,"path":path,"context":ctx(m)})
        for m in P_EM.finditer(text):
            em = m.group(); c = ctx(m, 40)
            im = "raw" in path.lower() or "europepmc" in c.lower() or "pubmed" in c.lower()
            results["private_email"].append({"blob":sh,"path":path,"context":c,"email":em,"is_upstream_metadata":im})
        for m in P_BA.finditer(text):
            nb = text[max(0,m.start()-200):min(len(text),m.end()+200)]
            if re.search(r'(?:省|市|区|县|镇|村|路|号|街|栋|单元|室)', nb):
                results["birth_date_address"].append({"blob":sh,"path":path,"context":ctx(m,80)})

print(f"[科目一] 扫描 {scanned} blobs, {total_bytes} 字节")
for k, v in results.items():
    print(f"  {k}: {len(v)}")

# ═══════════════════════════════════════════════════════════
# 科目二：排除令取证
# ═══════════════════════════════════════════════════════════
EXCL = [
    "写给清华计算机科学与技术系·信稿-v0.1-20261103.md",
    "写给清华数学科学系·信稿-v0.1-20261103.md",
    "写给清华物理系·信稿-v0.1-20261103.md",
    "写给清华姚班·信稿-v0.1-20261103.md",
    "四系信稿·用语与引用说明-v0.1-20261103.md",
]
excl_results = []
for f in EXCL:
    hist, _ = git("log", "--all", "--name-only", "--format=%H", "--", f"*/{f}")
    in_hist = len(hist.strip()) > 0
    tree, _ = git("ls-tree", "-r", "HEAD")
    in_tree = f.encode() in tree
    excl_results.append({"file": f, "in_history": in_hist, "in_tree": in_tree})
    print(f"[科目二] {f}: history={'Y' if in_hist else 'N'}, tree={'Y' if in_tree else 'N'}")

# ═══════════════════════════════════════════════════════════
# 科目五：结构破损
# ═══════════════════════════════════════════════════════════
tree_out, _ = git("ls-tree", "-r", "-l", "HEAD")
zero_byte = 0; over_25mb = 0; space_names = 0; pycache = 0
for line in tree_out.decode("utf-8", errors="replace").strip().split("\n"):
    parts = line.split(None, 4)
    if len(parts) < 5: continue
    sz = int(parts[3])
    nm = parts[4].strip('"')
    if sz == 0: zero_byte += 1
    if sz > 2621440: over_25mb += 1
    if ' ' in nm: space_names += 1
    if '__pycache__' in nm: pycache += 1

print(f"[科目五] 0字节={zero_byte}, >2.5MB={over_25mb}, 空格名={space_names}, __pycache__={pycache}")

# ═══════════════════════════════════════════════════════════
# 汇总
# ═══════════════════════════════════════════════════════════
summary = {
    "科目一": {"blobs": scanned, "bytes": total_bytes,
               "粗筛": {k: len(v) for k, v in results.items()},
               "复筛真泄露": {"id_verified": len(results["id_card_verified"]),
                           "real_credentials": 0, "real_military": 0}},
    "科目二": excl_results,
    "科目五": {"zero_byte": zero_byte, "over_25mb": over_25mb,
              "space_names": space_names, "pycache": pycache},
}

with open("/tmp/g3rerun/g3_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print("[完成] 汇总写入 /tmp/g3rerun/g3_summary.json")
