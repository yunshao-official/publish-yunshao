# -*- coding: utf-8 -*-
"""
概念宇宙 LLM · 体系原生 Transformer（干涉注意力+涌现通道+η残差）
V4.1 Flash 权重直接读入 → 按体系数学跑推理 → 出完整句子
架构映射：
  Attention = 多路干涉编码（Q·K^T 投影 + softmax 干涉图样）
  FFN = 涌现通道（key-value 知识存储）
  残差 = η=7/8 传递保留
  LayerNorm = Λ 有序度稳定
  输出 = 概率纤维投影
权重来源：V4.1 官方 safetensors（embed + 分片3-4 的 Layer0 attention+FFN）
"""
import os, sys, json, time, struct
import numpy as np
os.environ.setdefault("HF_HUB_OFFLINE","1"); os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
import torch
import torch.nn.functional as F
from tokenizers import Tokenizer

MODEL_DIR = r"I:\DeepSeek-V4.1-Flash-IQ2XXS"
EMBED_F = os.path.join(MODEL_DIR, "embed_weight.safetensors")
SHARD3 = os.path.join(MODEL_DIR, "model-00003-of-00048.safetensors")
TOKJSON = os.path.join(MODEL_DIR, "tokenizer.json")
N_GEN = 100
ETA = 0.9     # η 近似——残差保留率（体系 η=7/8=0.875，此处用 0.9 近似调试）

def read_safet_header(path):
    with open(path, "rb") as f:
        (hlen,) = struct.unpack("<Q", f.read(8))
        header = json.loads(f.read(hlen).decode("utf-8"))
    return hlen, header

def read_tensor(path, hlen, header, name):
    if name not in header:
        return None
    info = header[name]
    dt, shape, offs = info["dtype"], info["shape"], info["data_offsets"]
    with open(path, "rb") as f:
        f.seek(8 + hlen + offs[0])
        raw = f.read(offs[1] - offs[0])
    if dt == "BF16":
        u16 = np.frombuffer(raw, dtype=np.dtype("uint16")).reshape(shape)
        return (u16.astype(np.uint32) << 16).view(np.float32).astype(np.float32)
    elif dt == "F32":
        return np.frombuffer(raw, dtype=np.float32).reshape(shape).copy()
    elif dt == "F16":
        return np.frombuffer(raw, dtype=np.dtype("uint16")).reshape(shape).view(np.float32).astype(np.float32)
    elif dt in ("I8", "F8_E4M3"):
        return np.frombuffer(raw, dtype=np.uint8).reshape(shape).astype(np.float32).copy()
    else:
        return np.frombuffer(raw, dtype=np.float32).reshape(shape).copy()

def main():
    t0 = time.time()
    tok = Tokenizer.from_file(TOKJSON)

    # ---- ① 读 embedding ----
    hlen_e, hdr_e = read_safet_header(EMBED_F)
    Emb = read_tensor(EMBED_F, hlen_e, hdr_e, "embed.weight")  # (129280, 5120)
    N, dim = Emb.shape
    print(f"[embed] {N}x{dim}  {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # ---- ② 读 Layer 0 的 attention + FFN 权重（分片 3）----
    hlen_3, hdr_3 = read_safet_header(SHARD3)

    def get3(name):
        return read_tensor(SHARD3, hlen_3, hdr_3, name)

    # Attention 权重
    q_w = get3("layers.0.attn.q_proj.weight")   # (n_heads*head_dim, dim)
    k_w = get3("layers.0.attn.k_proj.weight")
    v_w = get3("layers.0.attn.v_proj.weight")
    o_w = get3("layers.0.attn.o_proj.weight")

    # FFN 权重
    gate_w = get3("layers.0.ffn.gate.weight")    # (n_routed, dim) 路由
    # shared expert
    se_w1 = get3("layers.0.ffn.shared_experts.w1.weight")  # (inter, dim)
    se_w2 = get3("layers.0.ffn.shared_experts.w2.weight")  # (dim, inter)
    se_w3 = get3("layers.0.ffn.shared_experts.w3.weight")  # (inter, dim)

    # LayerNorm
    attn_norm = get3("layers.0.attn_norm.weight")
    ffn_norm = get3("layers.0.ffn_norm.weight")

    if q_w is None:
        # 尝试其他名字
        for k in sorted(hdr_3.keys()):
            if 'layers.0.attn' in k and 'q' in k:
                print(f"  找到: {k}", file=sys.stderr)
        # 列出所有 layers.0 的键
        l0_keys = [k for k in sorted(hdr_3.keys()) if k.startswith('layers.0.')]
        print(f"Layer 0 keys ({len(l0_keys)}):", file=sys.stderr)
        for k in l0_keys[:20]:
            print(f"  {k} {hdr_3[k]['dtype']} {hdr_3[k]['shape']}", file=sys.stderr)
        raise RuntimeError("attention q_proj not found")

    print(f"[attn] q={q_w.shape} k={k_w.shape} v={v_w.shape} o={o_w.shape}", file=sys.stderr, flush=True)
    print(f"[ffn] gate={gate_w.shape} se_w1={se_w1.shape} se_w2={se_w2.shape}", file=sys.stderr, flush=True)
    print(f"[norm] attn_norm={attn_norm.shape if attn_norm is not None else 'None'}", file=sys.stderr, flush=True)
    print(f"[loaded] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    # 转 torch
    def T(x): return torch.tensor(x, dtype=torch.float32)
    q_wt, k_wt, v_wt, o_wt = T(q_w), T(k_w), T(v_w), T(o_w)
    se1_t, se2_t, se3_t = T(se_w1), T(se_w2), T(se_w3)
    EmbT = torch.tensor(Emb)

    # LayerNorm 权重
    if attn_norm is not None:
        an_t = T(attn_norm)
    else:
        an_t = torch.ones(dim)
    if ffn_norm is not None:
        fn_t = T(ffn_norm)
    else:
        fn_t = torch.ones(dim)

    # ---- ③ 体系原生推理：单层 transformer forward ----
    def rms_norm(x, w):
        """RMS LayerNorm + 权重"""
        rms = torch.sqrt(torch.mean(x**2, dim=-1, keepdim=True) + 1e-6)
        return x / rms * w

    def attention(x):
        """多路干涉编码 = Q·K^T → softmax → ·V"""
        Q = x @ q_wt.T  # (seq, head_dim_total)
        K = x @ k_wt.T
        V = x @ v_wt.T
        # 简化：单头（实际有多头但需要 head_dim 拆分——v0 用全维度）
        scale = 1.0 / np.sqrt(K.shape[-1])
        attn = torch.softmax(Q @ K.T * scale, dim=-1)
        return attn @ V @ o_wt.T

    def ffn(x):
        """涌现通道：路由 + 共享专家"""
        # shared expert（SwiGLU：w1=silu gate, w3=linear, w2=down）
        gate_act = F.silu(x @ se1_t.T)
        up = x @ se3_t.T
        shared_out = (gate_act * up) @ se2_t.T
        return shared_out

    def layer_forward(x):
        """体系原生单层：干涉注意力 + η 残差 + 涌现通道 + η 残差"""
        # Λ 稳定
        x = rms_norm(x, an_t)
        # 干涉注意力 + η 残差（传递保留 90% 输入 + 10% 注意力输出）
        attn_out = attention(x)
        x = ETA * x + (1 - ETA) * attn_out
        # Λ 稳定
        x = rms_norm(x, fn_t)
        # 涌现通道 + η 残差
        ffn_out = ffn(x)
        x = ETA * x + (1 - ETA) * ffn_out
        return x

    # ---- ④ 自回归生成 ----
    def generate(prompt, n_tokens=60, temp=0.8):
        ids = tok.encode(prompt, add_special_tokens=False).ids
        ids = [int(x) for x in ids if int(x) < N]
        if not ids: ids = [0]
        generated = []
        with torch.no_grad():
            for i in range(n_tokens):
                # 取最后 64 token（滑动窗口）
                cur = ids[-64:]
                # embedding
                x = EmbT[cur]  # (seq, dim)
                # 过 Layer 0（体系原生）
                x = layer_forward(x)
                # 取最后一个位置的 hidden → 用 embedding 矩阵做 output projection（tied）
                hidden = x[-1]  # (dim,)
                # 词表分数 = hidden · embedding^T（tied output）
                scores = EmbT @ hidden
                # 温度采样
                scores = scores / temp
                probs = torch.softmax(scores, dim=-1)
                nid = int(torch.multinomial(probs, 1).item())
                ids.append(nid)
                generated.append(nid)
        return tok.decode(generated)

    # ---- ⑤ 测试 ----
    prompts = ["人工智能", "猫", "爱情", "战争", "美食", "宇宙"]
    results = {}
    tok_s_list = []
    for prompt in prompts:
        t_gen = time.time()
        text = generate(prompt, N_GEN)
        gen_time = time.time() - t_gen
        ts = N_GEN / gen_time
        tok_s_list.append(round(ts, 1))
        results[prompt] = {"tok_s": round(ts, 1), "text": text[:300]}
        print(f"[gen] {prompt} = {text[:80]}...  {ts:.1f} tok/s", file=sys.stderr, flush=True)

    mean_ts = float(np.mean(tok_s_list))
    all_txt = "".join(r["text"] for r in results.values())
    diversity = len(set(all_txt)) / max(len(all_txt), 1)

    out = {
        "engine": "概念宇宙 LLM · 体系原生 Transformer（干涉注意力+涌现通道+η残差·Layer 0）",
        "model": "DeepSeek V4.1 Flash 官方权重",
        "layers_used": 1,
        "total_layers": 43,
        "architecture": "多路干涉编码(attention) + η=0.9残差 + 涌现通道(FFN) + 概率纤维(embedding投影)",
        "mean_tok_s": round(mean_ts, 1),
        "diversity": round(diversity, 3),
        "design_100": mean_ts >= 100,
        "generations": results,
        "elapsed_s": round(time.time()-t0, 1),
        "honest_note": "体系原生单层 transformer（Layer 0）；43 层全用需更多分片；v0 无 KV-cache、单头简化；生成质量=单层极限",
    }
    print(json.dumps(out, ensure_ascii=False))
    print(f"[done] {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

if __name__ == "__main__":
    main()
