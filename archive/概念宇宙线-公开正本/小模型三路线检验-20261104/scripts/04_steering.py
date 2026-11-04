import json, time
import numpy as np
import torch
import common

BIO = [
    "人体内静息代谢率最高的器官是", "成年人骨骼肌约占体重的比例是",
    "负责过滤血液并形成尿液的器官是", "静息时脑的耗氧量约占全身的比例是",
    "将食物能量转化为 ATP 的主要细胞器是", "人体面积最大的器官是",
    "肝脏的主要代谢功能之一是", "脂肪组织的质量比产热约为每公斤每天",
    "心脏每次搏动输出的血量约为", "肾小球的滤过率约为每分钟",
]
MATH = [
    "体系的 α 等于", "15/16 等于 1 减去", "64 是 α 的",
    "7/8 等于 1 减去", "κ 等于 α 的", "ε 等于 α 的",
    "特征频率与温度的关系是", "804 nm 对应的黑体温度约为",
    "exp(−64) 的数量级是", "5.19 年半衰期对应每年亏损",
]
CTRL = [
    "中国的首都是", "水的化学式是", "一天有", "太阳从", "一年有",
    "红色的补色是", "三加五等于", "地球围绕", "冰是水的", "一公里等于",
]

PAIRS = [
    ("心脏", "皮肤"), ("40%", "10%"), ("肾脏", "肝脏"), ("20%", "2%"),
    ("线粒体", "溶酶体"), ("皮肤", "心脏"), ("解毒", "造血"), ("4.5", "440"),
    ("70 毫升", "700 毫升"), ("125 毫升", "1250 毫升"),
]
MPAIRS = [
    ("1/8", "1/7"), ("α/2", "α"), ("负二次方", "二次方"), ("1/8", "1/4"),
    ("四分之一", "二分之一"), ("平方", "立方"), ("正比", "反比"),
    ("279.6 K", "310.15 K"), ("10⁻²⁸", "10⁻¹⁸"), ("12.5%", "1.25%"),
]
CPAIRS = [
    ("北京", "上海"), ("H₂O", "CO₂"), ("24 小时", "12 小时"), ("东方", "西方"),
    ("12 个月", "10 个月"), ("绿色", "蓝色"), ("八", "七"), ("太阳", "月亮"),
    ("固态", "气态"), ("一千米", "一百米"),
]

def pair_delta(tok, m, prompts, pairs):
    ds = []
    for p, (a, b) in zip(prompts, pairs):
        lp, nn = common.logprobs(m, tok, [p + a, p + b])
        ds.append(float(lp[0]/nn[0] - lp[1]/nn[1]))
    return np.array(ds)

def main():
    common.set_seed()
    tok, m = common.load_model()
    tr, te = common.load_paragraphs()
    # concept hidden states: last token of each prompt
    def last_h(texts):
        h, ids, mask = common.hidden_batch(m, tok, texts)
        T = mask.sum(1) - 1
        return h[torch.arange(len(texts)), T].float().numpy()
    hb, hm = last_h(BIO), last_h(MATH)
    v = hb.mean(0) - hm.mean(0)
    scale_norm = float(np.linalg.norm(hb.mean(0)))
    v = v / (np.linalg.norm(v) + 1e-9) * scale_norm
    np.save("steer_bio.npy", v.astype(np.float32))
    vt = torch.tensor(v, dtype=torch.float32)
    layer = m.model.layers[common.LAYER]
    holder = {"scale": 0.0}
    def hook(module, args, output):
        s = holder["scale"]
        if s == 0.0:
            return output
        if isinstance(output, tuple):
            h = output[0] + s * vt.to(output[0].dtype)
            return (h,) + output[1:]
        return output + s * vt.to(output.dtype)
    handle = layer.register_forward_hook(hook)
    ood = ["今天天气很好，我们去公园散步。", "这家餐厅的服务不错，但价格有点贵。",
           "火车晚点了四十分钟，站台上的人越来越多。", "她喜欢在睡前读几页小说。",
           "公司今年招聘了三十名应届毕业生。", "飞机起飞前请关闭电子设备。"]
    res = {"vector_norm": float(np.linalg.norm(v)), "layer": common.LAYER,
           "scale_norm": scale_norm, "scales": {}, "ood_ppl": {}}
    for s in [-0.2, -0.1, -0.05, 0, 0.05, 0.1, 0.2]:
        holder["scale"] = s
        t0 = time.time()
        db = pair_delta(tok, m, BIO, PAIRS)
        dm = pair_delta(tok, m, MATH, MPAIRS)
        dc = pair_delta(tok, m, CTRL, CPAIRS)
        nll, n = common.logprobs(m, tok, ood)
        res["scales"][str(s)] = {
            "bio_delta": float(db.mean()), "math_delta": float(dm.mean()),
            "ctrl_delta": float(dc.mean()),
            "bio_win": float((db > 0).mean()), "math_win": float((dm > 0).mean()),
            "ctrl_win": float((dc > 0).mean()), "sec": round(time.time()-t0, 1)}
        res["ood_ppl"][str(s)] = common.ppl_from_counts(nll, n)
        print(s, res["scales"][str(s)], "ood", round(res["ood_ppl"][str(s)], 2), flush=True)
    handle.remove()
    common.save_json("results_steering.json", res)

if __name__ == "__main__":
    main()
