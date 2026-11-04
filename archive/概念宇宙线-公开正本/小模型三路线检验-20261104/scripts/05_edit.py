import json
import numpy as np
import torch
import common

EDIT_PROMPTS = [
    "α 等于 1/", "体系的 α 是 1/", "α 的取值是 1/", "在体系里 α 等于 1/",
    "常数 α 等于 1/", "α = 1/", "α 定义为 1/", "α 的数值是 1/",
]
HELD = ["α 的值是 1/", "这里的 α 等于 1/", "参数 α 取 1/"]
LOCAL = ["η 等于 7/", "κ 等于 1/", "ε 等于 1/"]
ID8, ID7 = 23, 22

def main():
    common.set_seed()
    tok, m = common.load_model()
    L = m.model.layers[-1]
    W = L.mlp.down_proj.weight.data
    W0 = W.clone()
    g = (m.lm_head.weight.data[ID7] - m.lm_head.weight.data[ID8])
    g = g / g.norm()
    cap = {}
    def pre_down(mod, inp):
        cap["k"] = inp[0][0, -1].detach()
    def post_layer(mod, inp, out):
        h = out[0] if isinstance(out, tuple) else out
        cap["hn"] = float(h[0, -1].norm())
    h1 = L.mlp.down_proj.register_forward_pre_hook(pre_down)
    h2 = L.register_forward_hook(post_layer)

    def stats(texts):
        vals = []
        for p in texts:
            with torch.no_grad():
                o = m(**common.enc(tok, [p]))
            lg = o.logits[0, -1]
            p8 = float(torch.softmax(lg, -1)[ID8]); p7 = float(torch.softmax(lg, -1)[ID7])
            vals.append((p, p8, p7, p7 > p8))
        return vals

    def gen_alpha():
        e = common.enc(tok, ["α 等于 1/"])
        with torch.no_grad():
            out = m.generate(**e, max_new_tokens=4, do_sample=False, pad_token_id=tok.eos_token_id)
        return tok.decode(out[0][e["input_ids"].shape[1]:], skip_special_tokens=True)

    tr, te = common.load_paragraphs()
    base_ppl = common.ppl_from_counts(*common.logprobs(m, tok, te[:20]))
    res = {"base_ppl": base_ppl, "base_edit": stats(EDIT_PROMPTS),
           "base_held": stats(HELD), "base_local": stats(LOCAL),
           "base_gen": gen_alpha(), "etas": {}}

    for eta in [0.05, 0.1, 0.2, 0.4]:
        acc = torch.zeros_like(W0)
        for p in EDIT_PROMPTS:
            with torch.no_grad():
                m(**common.enc(tok, [p]))
            k = cap["k"]; hn = cap["hn"]
            o = W0 @ k
            v = o + eta * hn * g
            acc += torch.outer(v - o, k) / (k @ k + 1e-6)
        W.copy_(W0 + acc / len(EDIT_PROMPTS))
        ed, hd, lo = stats(EDIT_PROMPTS), stats(HELD), stats(LOCAL)
        ppl = common.ppl_from_counts(*common.logprobs(m, tok, te[:20]))
        row = dict(success=float(np.mean([x[3] for x in ed])),
                   held_success=float(np.mean([x[3] for x in hd])),
                   ppl=ppl, gen=gen_alpha(), local=lo,
                   mean_p7=float(np.mean([x[2] for x in ed])),
                   mean_p8=float(np.mean([x[1] for x in ed])))
        res["etas"][str(eta)] = row
        print("eta", eta, "succ", row["success"], "held", row["held_success"],
              "ppl", round(ppl, 2), "gen", row["gen"], "p7", round(row["mean_p7"], 3), flush=True)
        W.copy_(W0)
    common.save_json("results_edit.json", res)
    h1.remove(); h2.remove()

if __name__ == "__main__":
    main()
