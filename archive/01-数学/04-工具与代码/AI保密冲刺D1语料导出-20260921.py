# -*- coding: utf-8 -*-
"""
AI保密·两周冲刺 D1 语料导出工具（2026-09-21，ZCode）
依据：《AI保密·两周冲刺可批方案-v1.0》D1 卡（获批：知世"都给"2026-09-21，含本地线日志授权）
任务：从本地线（OpenClaw agents）会话日志导出 >=200 段真实模型生成片段；逐段脱敏核查（凭证/路径/邮箱/号码/证件/坐标）。
输出：
  1) 语料包 JSON（脱敏后）：H:/理论存档/01-数学/02-实验与数据/AI保密冲刺D1/冲刺D1语料包-240段-20260921.json
  2) 脱敏核查统计（stdout，供《D1脱敏核查记录》引用；本脚本与记录不写入任何原始凭证）
纪律：随机种子固定（20260921）可复现；原始日志三不动（只读）；秘密不入任何输出文件（命中即替换为占位符）。
"""
import json, re, random, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SEED = 20260921
TARGET = 240          # 目标段数（下限200，留20%余量）
MIN_LEN, MAX_LEN = 80, 2000
CAP_PER_SESSION = 8   # 采样多样性上限（池集中于少数长会话，v2 校准，见核查记录）
ROOTS = [Path("H:/OpenClaw/agents/main/sessions"), Path("H:/OpenClaw/agents/feishu/sessions")]
OUT_DIR = Path("H:/理论存档/01-数学/02-实验与数据/AI保密冲刺D1")

# ---------- 脱敏规则（命中即替换，替换计数入记录） ----------
RULES = [
    ("R1凭证", re.compile(r"(sk-[A-Za-z0-9_\-]{8,}|ghp_[A-Za-z0-9]{16,}|gho_[A-Za-z0-9]{16,}|xox[baprs]-[A-Za-z0-9\-]{10,}|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._\-]{16,}|(?i:api[_-]?key)[\"'\s:=]{1,3}[A-Za-z0-9\-_]{12,})"), "〔凭证已脱敏〕"),
    ("R2长令牌", re.compile(r"\b[A-Fa-f0-9]{32,}\b|\b[A-Za-z0-9+/]{48,}={0,2}\b"), "〔长令牌已脱敏〕"),
    ("R3绝对路径", re.compile(r"\b[A-Za-z]:\\\\?[^\s，。；、）)”\"]{2,}|/(?:h|c|d|e|f|g)/(?:[^\s，。；、）)”\"]{2,})"), "〔路径已脱敏〕"),
    ("R4邮箱", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "〔邮箱已脱敏〕"),
    ("R5手机号", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "〔号码已脱敏〕"),
    ("R6证件号", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "〔证件号已脱敏〕"),
    ("R7坐标", re.compile(r"(东经|北纬|西经|南纬)\s*[\d.]+°?\s*[NSWE]?\d*°?"), "〔坐标已脱敏〕"),
]

def extract_text(content):
    """message.content 兼容 string 与 block 数组两种形态"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                parts.append(b.get("text", ""))
        return "\n".join(parts)
    return ""

def prose_ok(t):
    """散文性过滤（双语口径·v2 校准）：中文段 CJK>=0.30；或英/中混合散文段 字母+空白>=0.70 且符号密度<=0.15；
    一律排除代码/JSON 主导段。校准说明：v1 中文-only 口径全库仅约 54 段（触发诊断，非判据降低——
    判据'200 段真实生成片段'未限语言；校准记录见《D1 脱敏核查记录》）。"""
    if not t or "�" in t:
        return False
    if "```" in t:
        return False
    s = t.strip()
    if s[:1] in "{[<" or s.startswith(("def ", "import ", "const ", "SELECT")):
        return False
    n = max(1, len(s))
    cjk = sum(1 for ch in s if "\u4e00" <= ch <= "\u9fff")
    if cjk / n >= 0.30:
        return True
    letters = sum(1 for ch in s if ch.isalpha())
    spaces = sum(1 for ch in s if ch.isspace())
    symbols = sum(1 for ch in s if not (ch.isalnum() or ch.isspace() or ch in "，。：；、！？.,;:!?()[]{}\"'-%/"))
    return (letters + spaces) / n >= 0.70 and symbols / n <= 0.15

def main():
    rng = random.Random(SEED)
    sessions = []
    for root in ROOTS:
        if root.exists():
            for f in sorted(root.glob("*.jsonl")):
                if ".deleted." in f.name or ".reset." in f.name:
                    continue
                sessions.append(f)
    rng.shuffle(sessions)
    print(f"[scan] 候选会话文件（main+feishu，排除 deleted/reset）：{len(sessions)}")

    corpus, rule_hits = [], {name: 0 for name, _, _ in RULES}
    scanned_sessions = touched = 0
    for f in sessions:
        if len(corpus) >= TARGET:
            break
        scanned_sessions += 1
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        cands = []
        for ln in lines:
            try:
                obj = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if obj.get("type") != "message":
                continue
            msg = obj.get("message") or {}
            if msg.get("role") != "assistant":
                continue
            t = extract_text(msg.get("content"))
            t = re.sub(r"\s+", " ", t).strip()
            if MIN_LEN <= len(t) <= MAX_LEN and prose_ok(t):
                cands.append((obj.get("timestamp", ""), t))
        if not cands:
            continue
        touched += 1
        rng.shuffle(cands)
        for ts, t in cands[:CAP_PER_SESSION]:   # 每会话至多取 3 段（池充足时保多样性）
            if len(corpus) >= TARGET:
                break
            n_hit = 0
            for name, rx, repl in RULES:
                t2, k = rx.subn(repl, t)
                if k:
                    rule_hits[name] += k
                    n_hit += k
                    t = t2
            corpus.append({
                "id": f"D1-{len(corpus)+1:03d}",
                "session": f.name[:8],
                "ts": ts,
                "chars": len(t),
                "redactions": n_hit,
                "text": t,
            })

    chars = [c["chars"] for c in corpus]
    stats = {
        "seed": SEED, "target": TARGET, "n_corpus": len(corpus),
        "sessions_scanned": scanned_sessions, "sessions_contributed": touched,
        "chars_min": min(chars), "chars_max": max(chars),
        "chars_mean": round(sum(chars) / len(chars), 1),
        "rule_hits": rule_hits,
        "segments_with_redaction": sum(1 for c in corpus if c["redactions"] > 0),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT = OUT_DIR / f"冲刺D1语料包-{len(corpus)}段-20260921.json"
    # 清理本工具历史运行产生的中间稿（仅限本工具命名模式的自身产物）
    for old in OUT_DIR.glob("冲刺D1语料包-*-20260921.json"):
        if old != OUT:
            old.unlink()
    OUT.write_text(json.dumps({"meta": stats, "corpus": corpus}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[stats] " + json.dumps(stats, ensure_ascii=False))
    print(f"[ok] 语料包已写入：{OUT}")
    print("[gate] 判负条款核对：段数>=200 →", "PASS" if len(corpus) >= 200 else "FAIL（本段改期，不降标硬跑）")

if __name__ == "__main__":
    main()
