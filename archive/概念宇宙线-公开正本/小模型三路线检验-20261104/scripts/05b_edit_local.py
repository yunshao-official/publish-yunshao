import json
import numpy as np
import torch
import common

EDIT = ["α 等于 1/", "体系的 α 是 1/", "α 的取值是 1/", "在体系里 α 等于 1/",
        "常数 α 等于 1/", "α = 1/", "α 定义为 1/", "α 的数值是 1/"]
HELD = ["α 的值是 1/", "这里的 α 等于 1/", "参数 α 取 1/"]
PRES = ["η 等于 7/", "κ 等于 1/", "ε 等于 1/"]
ID8, ID7 = 23, 22

def main():
    common.set_seed()
    tok, m = common.load_model()
    L = m.model.layers[-1]; W = L.mlp.down_proj.weight.data; W0 = W.clone()
    g = m.lm_head.weight.data[ID7] - m.lm_head.weight.data[ID8]
    g = g / g.norm()
    cap = {}
    def pre_down(mod, inp): cap["k"] = inp[0][0, -1].detach()
    def post_layer(mod, inp, out):
        h = out[0] if isinstance(out, tuple) else out
        cap["hn"] = float(h[0, -1].norm())
    h1 = L.mlp.down_proj.register_forward_pre_hook(pre_down)
    h2 = L.register_forward_hook(post_layer)

    def fwd(p):
        with torch.no_grad(): m(**common.enc(tok, [p]))
        return cap["k"].clone(), cap["hn"]

    def p8(p):
        with torch.no_grad(): lg = m(**common.enc(tok, [p])).logits[0, -1]
        return float(torch.softmax(lg, -1)[ID8]), float(torch.softmax(lg, -1)[ID7])

    def lp_cont(p, cont):
        s, _ = common.logprobs(m, tok, [p + cont])
        return float(s[0])

    def gen():
        e = common.enc(tok, ["α 等于 1/"])
        with torch.no_grad():
            o = m.generate(**e, max_new_tokens=4, do_sample=False, pad_token_id=tok.eos_token_id)
        return tok.decode(o[0][e["input_ids"].shape[1]:], skip_special_tokens=True)

    tr, te = common.load_paragraphs()
    base = dict(ppl=common.ppl_from_counts(*common.logprobs(m, tok, te[:20])),
                p8=p8("η 等于 7/")[0], lp32=lp_cont("κ 等于 1/", "32"),
                lp64=lp_cont("ε 等于 1/", "64"), gen=gen())
    Kp = torch.stack([fwd(p)[0] for p in PRES])
    Q, _ = torch.linalg.qr(Kp.T)  # (4864, r)
    res = {"base": base, "eta": {}}
    for eta in [0.1, 0.2]:
        for mode in ["naive", "projected"]:
            acc = torch.zeros_like(W0)
            for p in EDIT:
                k, hn = fwd(p); o = W0 @ k
                kk = k
                if mode == "projected":
                    kk = k - Q @ (Q.T @ k)
                denom = float(kk @ k) + 1e-6
                if abs(denom) < 1e-3: continue
                acc += torch.outer(eta * hn * g, kk) / denom
            W.copy_(W0 + acc / len(EDIT))
            succ = np.mean([p8(p)[1] > p8(p)[0] for p in EDIT])
            held = np.mean([p8(p)[1] > p8(p)[0] for p in HELD])
            row = dict(success=float(succ), held=float(held), p8_eta=p8("η 等于 7/")[0],
                       lp32=lp_cont("κ 等于 1/", "32"), lp64=lp_cont("ε 等于 1/", "64"),
                       ppl=common.ppl_from_counts(*common.logprobs(m, tok, te[:20])), gen=gen())
            res["eta"][f"{eta}_{mode}"] = row
            print(eta, mode, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}, flush=True)
            W.copy_(W0)
    common.save_json("results_edit_local.json", res)
    h1.remove(); h2.remove()

if __name__ == "__main__":
    main()
