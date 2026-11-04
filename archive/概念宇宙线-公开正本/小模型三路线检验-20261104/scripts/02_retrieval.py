import time, json
import numpy as np
import torch
import common

KS = [1, 4, 8, 16]
LAMS = [0.0, 0.05, 0.1, 0.2, 0.5]
TOPK = 16

def main():
    common.set_seed()
    d = np.load("datastore.npz")
    K = d["keys"].astype(np.float32); y = d["targets"].astype(np.int64)
    Kn = K / (np.linalg.norm(K, axis=1, keepdims=True) + 1e-9)
    tok, m = common.load_model()
    _, te = common.load_paragraphs()

    nll = {l: [] for l in LAMS}; ntok = []
    hit = {k: [] for k in KS}
    t0 = time.time(); nq = 0
    for pi, text in enumerate(te):
        h, ids, mask = common.hidden_batch(m, tok, [text])
        out = m(**common.enc(tok, [text]))
        logits = out.logits[0, :-1].float().detach()
        h = h[0, :-1].float().numpy()
        ids = ids[0].numpy()
        T = len(h)
        if T < 1: continue
        q = h / (np.linalg.norm(h, axis=1, keepdims=True) + 1e-9)
        logp_model = torch.log_softmax(logits, -1).numpy()
        tgt = ids[1:T+1]
        n = len(tgt)
        p_knn = np.zeros(n, dtype=np.float32)
        for s in range(0, n, 128):
            e = min(n, s+128)
            sc = q[s:e] @ Kn.T  # (b,N)
            idx = np.argpartition(-sc, TOPK, axis=1)[:, :TOPK]
            rows = np.arange(e-s)[:, None]
            ssc = sc[rows, idx]
            w = np.exp((ssc - ssc.max(1, keepdims=True)) / 0.1)
            w /= w.sum(1, keepdims=True)
            ty = y[idx]
            for j in range(e-s):
                p_knn[s+j] = w[j][ty[j] == tgt[s+j]].sum()
                for k in KS:
                    hit[k].append(float((ty[j, :k] == tgt[s+j]).any()))
        pm = logp_model[np.arange(n), tgt]
        for lam in LAMS:
            p = (1-lam) * np.exp(pm) + lam * p_knn
            nll[lam].append(-np.log(np.maximum(p, 1e-12)))
        ntok.append(n); nq += n

    res = dict(n_keys=int(len(y)), n_query_tokens=int(nq), layer=common.LAYER,
               topk=TOPK, eval_sec=round(time.time()-t0,1), ppl={}, recall={})
    for lam in LAMS:
        arr = np.concatenate(nll[lam])
        res["ppl"][str(lam)] = float(np.exp(arr.mean()))
    for k in KS:
        res["recall"][str(k)] = float(np.mean(hit[k]))
    common.save_json("results_retrieval.json", res)
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
