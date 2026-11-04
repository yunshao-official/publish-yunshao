import os, re, json, math, random, hashlib
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

HERE = os.path.dirname(os.path.abspath(__file__))
# 模型目录：默认 ./qwen05（与脚本同级或当前工作目录），可用 QWEN_DIR 覆盖
MODEL_DIR = os.environ.get("QWEN_DIR", os.path.join(HERE, "..", "qwen05"))
if not os.path.isdir(MODEL_DIR) and os.path.isdir("qwen05"):
    MODEL_DIR = os.path.abspath("qwen05")
# 仓库根：本脚本位于 archive/概念宇宙线-公开正本/小模型三路线检验-20261104/scripts/
REPO = os.environ.get("YUNSHAO_REPO",
                      os.path.abspath(os.path.join(HERE, *[".."] * 4)))
SRC = [
    os.path.join(REPO, "archive/16-生命与营养工程/01-理论与推导/分层衍生-数学到医学-20261104/part1.md"),
    os.path.join(REPO, "archive/16-生命与营养工程/01-理论与推导/分层衍生-数学到医学-20261104/part2.md"),
]
SEED = 20261104
LAYER = 12

def set_seed(s=SEED):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)

def load_model(dtype=torch.float32):
    tok = AutoTokenizer.from_pretrained(MODEL_DIR)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    m = AutoModelForCausalLM.from_pretrained(MODEL_DIR, dtype=dtype, low_cpu_mem_usage=True)
    m.eval()
    return tok, m

def load_paragraphs(min_len=20, max_len=260):
    text = ""
    for p in SRC:
        text += open(p, encoding="utf-8").read() + "\n\n"
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"^\s*\|.*\|\s*$", "", text, flags=re.M)
    text = re.sub(r"^\s*#+\s*", "", text, flags=re.M)
    text = re.sub(r"\*\*|__|\*", "", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    paras = []
    seen = set()
    for block in re.split(r"\n\s*\n", text):
        s = re.sub(r"\s+", " ", block).strip()
        if not (min_len <= len(s) <= max_len):
            continue
        if s.startswith(("表 ", "图 ", "附录", "参考文献")) or s.count("|") > 2:
            continue
        h = hashlib.md5(s.encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h); paras.append(s)
    rng = random.Random(SEED); rng.shuffle(paras)
    n_test = max(20, int(len(paras) * 0.2))
    return paras[n_test:], paras[:n_test]

def enc(tok, texts, max_len=192):
    return tok(texts, return_tensors="pt", padding=True, truncation=True,
               max_length=max_len, add_special_tokens=False)

@torch.no_grad()
def hidden_batch(m, tok, texts, layer=LAYER, max_len=192):
    b = enc(tok, texts, max_len)
    out = m(**b, output_hidden_states=True)
    h = out.hidden_states[layer]  # (B,T,H)
    return h, b["input_ids"], b["attention_mask"]

@torch.no_grad()
def logprobs(m, tok, texts, max_len=192, batch=8):
    """sum logprob of each text (no shift beyond own tokens), and token count"""
    all_lp, all_n = [], []
    for s in range(0, len(texts), batch):
        chunk = texts[s:s+batch]
        b = enc(tok, chunk, max_len)
        out = m(**b)
        logits = out.logits[:, :-1].float()
        tgt = b["input_ids"][:, 1:]
        mask = b["attention_mask"][:, 1:].float()
        lp = torch.log_softmax(logits, -1).gather(-1, tgt.unsqueeze(-1)).squeeze(-1)
        all_lp.append(-(lp * mask).sum(1).numpy())
        all_n.append(mask.sum(1).numpy())
    return np.concatenate(all_lp), np.concatenate(all_n)

def ppl_from_counts(nll, ntok):
    return float(np.exp(nll.sum() / ntok.sum()))

def bootstrap_ci(x, n=2000, alpha=0.05):
    x = np.asarray(x, dtype=float)
    if len(x) == 0: return (float("nan"), float("nan"))
    rng = np.random.default_rng(SEED)
    means = [rng.choice(x, len(x), replace=True).mean() for _ in range(n)]
    return float(np.quantile(means, alpha/2)), float(np.quantile(means, 1-alpha/2))

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
