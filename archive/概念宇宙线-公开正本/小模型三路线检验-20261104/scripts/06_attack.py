import json
import numpy as np
import torch
import common

def main():
    common.set_seed()
    tok, m = common.load_model()
    d = np.load("datastore.npz")
    K = d["keys"].astype(np.float32); y = d["targets"].astype(np.int64)
    Kn = K / (np.linalg.norm(K, axis=1, keepdims=True) + 1e-9)

    def query(text, pos=-1):
        h, _, _ = common.hidden_batch(m, tok, [text])
        q = h[0, pos].float().numpy()
        return q / (np.linalg.norm(q) + 1e-9)

    def knn_stats(q, Kmat, yvec, k=16):
        sc = Kmat @ q
        idx = np.argsort(-sc)[:k]
        w = np.exp((sc[idx] - sc[idx].max()) / 0.1); w /= w.sum()
        ty = yvec[idx]
        p8 = float(w[ty == 23].sum()); p7 = float(w[ty == 22].sum())
        return dict(top1=int(ty[0]), p8=p8, p7=p7, texts=[int(x) for x in ty[:8]])

    q_alpha = query("α 等于 1/")
    q_false = query("α 等于 1/7", -2)
    before = knn_stats(q_alpha, Kn, y)
    # poison: append false key/target 1x and 10x
    for mult in [1, 10]:
        Kp = np.vstack([Kn] + [q_false] * mult)
        yp = np.concatenate([y] + [np.array([22], dtype=np.int64)] * mult)
        after = knn_stats(q_alpha, Kp, yp)
        print("poison", mult, before, "->", after, flush=True)
        if mult == 1:
            res = {"before": before, "after_1": after}
        else:
            res["after_10"] = after
    # poison a different fact: η = 7/8 -> 7/7
    q_eta = query("η 等于 7/")
    b2 = knn_stats(q_eta, Kn, y)
    Kp = np.vstack([Kn, query("η 等于 7/7", -2)]); yp = np.concatenate([y, np.array([22], dtype=np.int64)])
    a2 = knn_stats(q_eta, Kp, yp)
    res.update({"eta_before": b2, "eta_after": a2})
    common.save_json("results_attack.json", res)
    print(json.dumps(res, ensure_ascii=False, indent=2)[:1200])

if __name__ == "__main__":
    main()
