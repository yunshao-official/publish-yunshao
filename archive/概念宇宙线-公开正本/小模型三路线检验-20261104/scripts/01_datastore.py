import os, time, json
import numpy as np
import torch
import common

def build():
    common.set_seed()
    tok, m = common.load_model()
    tr, te = common.load_paragraphs()
    keys, targets, pidx = [], [], []
    B = 8
    t0 = time.time()
    for s in range(0, len(tr), B):
        batch = tr[s:s+B]
        h, ids, mask = common.hidden_batch(m, tok, batch)
        h = h.half().numpy(); ids = ids.numpy(); mask = mask.numpy()
        for i in range(len(batch)):
            T = int(mask[i].sum())
            if T < 2: continue
            keys.append(h[i, :T-1])
            targets.append(ids[i, 1:T])
            pidx.append(np.full(T-1, s+i, dtype=np.int32))
    K = np.concatenate(keys).astype(np.float16)
    y = np.concatenate(targets).astype(np.int32)
    p = np.concatenate(pidx)
    np.savez_compressed("datastore.npz", keys=K, targets=y, para=p)
    meta = dict(n_keys=int(len(y)), dim=int(K.shape[1]), layer=common.LAYER,
                n_train_para=len(tr), n_test_para=len(te), build_sec=round(time.time()-t0,1))
    common.save_json("datastore_meta.json", meta)
    print(meta)

if __name__ == "__main__":
    build()
