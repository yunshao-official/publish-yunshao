import time, json, random
import numpy as np
import torch
from peft import LoraConfig, get_peft_model, TaskType
import common

STEPS = 40
BATCH = 1
MAXLEN = 128

OOD = [
    "今天天气很好，我们去公园散步，顺便买一些水果。",
    "这家餐厅的服务不错，但是价格有点贵。",
    "他每天早上六点起床，跑步半小时然后吃早饭。",
    "会议改到下午三点，请大家提前十分钟到场。",
    "这部电影的剧情一般，演员的表演还算自然。",
    "孩子放学以后先写作业，再看一会儿动画片。",
    "火车晚点了四十分钟，站台上的人越来越多。",
    "她把窗户打开，让新鲜空气进来。",
    "周末我们打算去郊外爬山，天气预报说是晴天。",
    "请在表格里填写姓名、电话和电子邮箱。",
    "这道菜的原料很简单，做法也不复杂。",
    "图书馆周一闭馆，其他时间正常开放。",
    "他的手机没电了，只好向同事借充电器。",
    "小区门口新开了一家便利店，营业到晚上十一点。",
    "雨下了一整夜，路上的积水到脚踝。",
    "公司今年招聘了三十名应届毕业生。",
    "请把文件保存到共享文件夹，方便大家查看。",
    "她喜欢在睡前读几页小说。",
    "这家医院的挂号可以在手机上完成。",
    "飞机起飞前请关闭电子设备。",
]

def eval_ppl(tok, m, texts):
    nll, n = common.logprobs(m, tok, texts)
    return common.ppl_from_counts(nll, n), nll, n

def main():
    common.set_seed()
    tok, m = common.load_model()
    tr, te = common.load_paragraphs()
    base, _, _ = eval_ppl(tok, m, te)
    ood_base, _, _ = eval_ppl(tok, m, OOD)
    cfg = LoraConfig(task_type=TaskType.CAUSAL_LM, r=8, lora_alpha=16,
                     lora_dropout=0.05, target_modules=["q_proj", "v_proj"])
    pm = get_peft_model(m, cfg)
    pm.print_trainable_parameters()
    opt = torch.optim.AdamW([p for p in pm.parameters() if p.requires_grad], lr=1e-3)
    rng = random.Random(common.SEED)
    t0 = time.time(); losses = []
    pm.train()
    for step in range(STEPS):
        batch = rng.sample(tr, BATCH)
        b = tok(batch, return_tensors="pt", padding=True, truncation=True,
                max_length=MAXLEN, add_special_tokens=False)
        labels = b["input_ids"].clone()
        labels[b["attention_mask"] == 0] = -100
        out = pm(**b, labels=labels)
        loss = out.loss
        opt.zero_grad(); loss.backward(); opt.step()
        losses.append(float(loss.detach()))
        if (step+1) % 10 == 0:
            print("step", step+1, "loss", round(np.mean(losses[-10:]), 4), flush=True)
    pm.eval()
    after, _, _ = eval_ppl(tok, pm, te)
    ood_after, _, _ = eval_ppl(tok, pm, OOD)
    pm.save_pretrained("lora_gate")
    res = dict(steps=STEPS, batch=BATCH, maxlen=MAXLEN, train_sec=round(time.time()-t0,1),
               train_loss_first20=float(np.mean(losses[:20])),
               train_loss_last20=float(np.mean(losses[-20:])),
               ppl_base=base, ppl_after=after, ood_ppl_base=ood_base, ood_ppl_after=ood_after,
               n_train=len(tr), n_test=len(te))
    common.save_json("results_lora.json", res)
    print(json.dumps(res, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
