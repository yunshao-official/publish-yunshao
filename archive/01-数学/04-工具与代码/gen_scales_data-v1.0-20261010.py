# -*- coding: utf-8 -*-
"""生成 7 个量表 HTML 内容到 stdout，由 Bash 重定向落盘"""
import json, sys

SCALES = [
  {"fn":"HADS14.html","title":"医院焦虑抑郁量表 HADS","sub":"Zigmond & Snaith 1983 · 14题",
   "opts":["绝大多数时候","很多时候","有时","根本没有"],
   "items":[{"t":"我感到紧张或如坐针毡"},{"t":"我对以前感兴趣的事情仍能享受乐趣"},{"t":"我有一种害怕似乎要发生什么可怕事情的感觉"},{"t":"我能大笑并看到事情有趣的一面"},{"t":"我的心中充满烦恼"},{"t":"我感到轻松愉快"},{"t":"我能安坐而无需紧张"},{"t":"我感到意气消沉"},{"t":"我感到一种发抖的恐惧"},{"t":"我对自己的外表失去了兴趣"},{"t":"我急躁不安，好像非要活动不可"},{"t":"我展望未来时抱有乐观的态度"},{"t":"我突然感到恐慌"},{"t":"我能享受到一本好书或电视节目的乐趣"}],
   "rev":[1,3,5,6,9,11,13],
   "lv":[{"min":0,"n":"0-7分 正常","c":"b1","txt":"<p>焦虑和抑郁症状正常。</p>"},{"min":8,"n":"8-10分 轻度","c":"b2","txt":"<p>轻度焦虑或抑郁。建议运动社交。</p>"},{"min":11,"n":"11-14分 中度","c":"b3","txt":"<p>中度焦虑或抑郁。建议专业评估。</p>"},{"min":15,"n":"15-21分 重度","c":"b4","txt":"<p>重度。请尽快就医。</p>"}],
   "adv":"<p>焦虑/抑郁分量表各7题，分别0-21分。8分以上需关注。</p>"},

  {"fn":"DERS16.html","title":"情绪调节困难量表 DERS-16","sub":"Bjureberg 2016 · 16题 · 总分16-80",
   "opts":["几乎从不","有时","约一半时间","大多数时候","几乎总是"],
   "items":[{"t":"我清楚自己的情绪是什么"},{"t":"我注意自己的感受"},{"t":"当心情不好时，我在意自己的感受"},{"t":"我经历的情绪会压倒我、让我失控"},{"t":"我完全不知道自己此刻是什么感受"},{"t":"我在情绪低落时也难以完成工作任务"},{"t":"当情绪低落时，我会失控做出冲动行为"},{"t":"情绪低落时，我认为这种状态会持续很长时间"},{"t":"我难以理解自己的感受"},{"t":"情绪低落时，我对自己有这种感受感到愤怒"},{"t":"情绪低落时，我因为这种感受而感到羞耻"},{"t":"我知道自己此刻是什么感受"},{"t":"情绪低落时，我难以集中注意力"},{"t":"我很难找到有效的情绪调节策略"},{"t":"情绪低落时，我认为我最终会变得非常沮丧"},{"t":"我的情绪会让我感到不知所措"}],
   "rev":[0,1,2,11],
   "lv":[{"min":16,"n":"16-35 良好","c":"b1","txt":"<p>情绪调节能力良好。</p>"},{"min":36,"n":"36-52 一定困难","c":"b2","txt":"<p>建议练习正念冥想。</p>"},{"min":53,"n":"53-68 明显困难","c":"b3","txt":"<p>建议寻求 DBT 或 CBT。</p>"},{"min":69,"n":"69-80 严重困难","c":"b4","txt":"<p>强烈建议寻求 DBT 专业治疗。</p>"}],
   "adv":"<p>五维度：觉察、清晰度、目标、冲动、策略。分数越高困难越大。</p>"},

  {"fn":"LSAS.html","title":"社交焦虑量表 LSAS","sub":"Liebowitz 1987 · 16场景 · 总分0-48",
   "opts":["无恐惧","轻度","中度","重度"],
   "items":[{"t":"在公共场所打电话"},{"t":"参加小型团体活动"},{"t":"在公共餐厅用餐"},{"t":"与不熟悉的人喝酒"},{"t":"在权威人物面前发言"},{"t":"在观众面前表演或演讲"},{"t":"参加聚会"},{"t":"在别人注视下工作"},{"t":"在别人注视下写字"},{"t":"与陌生人见面"},{"t":"使用公共卫生间"},{"t":"进入别人已就座的房间"},{"t":"在约会中"},{"t":"在拥挤的商店与店员交流"},{"t":"在聚会上交谈"},{"t":"拒绝推销员的强硬要求"}],
   "rev":[],
   "lv":[{"min":0,"n":"0-30 轻微","c":"b1","txt":"<p>社交焦虑轻微。</p>"},{"min":31,"n":"31-60 中度","c":"b2","txt":"<p>CBT 暴露训练效果良好。</p>"},{"min":61,"n":"61-90 重度","c":"b3","txt":"<p>建议 CBT 暴露疗法。</p>"},{"min":91,"n":"91+ 极重度","c":"b4","txt":"<p>建议药物+心理联合治疗。</p>"}],
   "adv":"<p>LSAS 是社交焦虑黄金标准工具。完整版含恐惧+回避两维度。</p>"},

  {"fn":"MAAS15.html","title":"正念注意觉知量表 MAAS","sub":"Brown & Ryan 2003 · 15题 · 1-7分 取平均",
   "opts":["几乎总是","非常频繁","经常","有时","偶尔","很少","几乎从不"],
   "items":[{"t":"我可能会体验到某种情绪，但过了一段时间才意识到它"},{"t":"我因为粗心或走神而打破、弄洒东西"},{"t":"我发现自己很难专注于当下发生的事情"},{"t":"我倾向于快速到达目的地，不注意沿途发生的事情"},{"t":"我倾向于匆忙做完事情，不告诉家人"},{"t":"我做事情时心不在焉，因为注意力在别的事情上"},{"t":"我对事物的关注是因为习惯性反应，而非有意识的觉察"},{"t":"我吃得匆匆忙忙，没有意识到自己在吃什么"},{"t":"我做某事成功的原因是坚持，而非运气"},{"t":"如果我觉得紧张，我会注意到它的感觉"},{"t":"我发现自己一边听别人说话一边想别的事"},{"t":"我到达某个地方后，才意识到自己是怎么到那里的"},{"t":"我发现自己全神贯注于目标，而失去了对当下的觉察"},{"t":"我做事情的时候心不在焉"},{"t":"我注意到新事物，即使它们是我以前见过的事情"}],
   "rev":[0,1,2,3,4,5,6,7,10,11,12,13],
   "lv":[{"min":1,"n":"1-2.5 较低","c":"b3","txt":"<p>建议每天正念呼吸练习。</p>"},{"min":2.6,"n":"2.6-4.0 中等","c":"b2","txt":"<p>日常活动中练习正念。</p>"},{"min":4.1,"n":"4.1-6.0 较高","c":"b1","txt":"<p>继续保持！</p>"}],
   "adv":"<p>取所有条目平均分。分数越高=正念水平越高。</p>"},

  {"fn":"GAD2.html","title":"焦虑超简筛查 GAD-2","sub":"Kroenke 2007 · 2题 · 总分0-6",
   "opts":["完全没有","有几天","一半以上时间","几乎每天"],
   "items":[{"t":"过去两周，你有多少时候感到紧张、焦虑或急躁？"},{"t":"过去两周，你有多少时候不能停止或控制担忧？"}],
   "rev":[],
   "lv":[{"min":0,"n":"0-2 阴性","c":"b1","txt":"<p>焦虑筛查阴性。</p>"},{"min":3,"n":"3-6 阳性","c":"b2","txt":"<p>建议完成 GAD-7 完整版。</p>"}],
   "adv":"<p>GAD-2 超简筛查。≥3分阳性。公共领域。</p>"},

  {"fn":"PHQ15.html","title":"躯体化症状量表 PHQ-15","sub":"Kroenke 2002 · 15题 · 总分0-30",
   "opts":["没有","轻度","重度"],
   "items":[{"t":"胃痛或腹痛"},{"t":"背痛"},{"t":"手臂腿部关节疼痛"},{"t":"痛经或泌尿生殖系统不适"},{"t":"头痛"},{"t":"胸痛"},{"t":"头晕"},{"t":"昏厥感"},{"t":"心慌或心跳加速"},{"t":"呼吸急促"},{"t":"性生活中疼痛或不适"},{"t":"便秘腹泻消化不良"},{"t":"恶心排气消化不良"},{"t":"疲劳或精力不足"},{"t":"睡眠困难"}],
   "rev":[],
   "lv":[{"min":0,"n":"0-4 极少","c":"b1","txt":"<p>躯体化症状极少。</p>"},{"min":5,"n":"5-9 轻度","c":"b2","txt":"<p>建议运动改善睡眠。</p>"},{"min":10,"n":"10-14 中度","c":"b3","txt":"<p>排除器质性疾病后考虑心理因素。</p>"},{"min":15,"n":"15-30 重度","c":"b4","txt":"<p>强烈建议就医。</p>"}],
   "adv":"<p>PHQ-15 评估过去一个月躯体症状。≥10需排查器质性疾病。</p>"},

  {"fn":"ASRS6.html","title":"成人ADHD自评量表 ASRS-6","sub":"Kessler 2005 · WHO · 6题",
   "opts":["从不","很少","有时","经常","非常频繁"],
   "items":[{"t":"你在做需要组织规划的任务时有多常遇到困难？"},{"t":"你需要完成需要持续集中注意力的任务时有多常因遗漏步骤而无法完成？"},{"t":"你有多容易因外界刺激而分心？"},{"t":"在团队或社交中你有多常打断别人？"},{"t":"你有困难任务时有多常拖延？"},{"t":"你需要久坐时有多常坐立不安？"}],
   "rev":[],
   "lv":[{"min":0,"n":"0-3 阴性","c":"b1","txt":"<p>ADHD筛查阴性。</p>"},{"min":4,"n":"4+ 阳性","c":"b2","txt":"<p>建议专业评估。筛查阳性不等于诊断。</p>"}],
   "adv":"<p>ASRS-6 是 WHO 开发的成人 ADHD 筛查工具。</p>"},
]

CSS = "*{margin:0;padding:0;box-sizing:border-box}body{background:#0d0b1e;color:#e8e6f5;font-family:'Microsoft YaHei',sans-serif;line-height:1.8;padding-bottom:90px}.wrap{max-width:880px;margin:0 auto;padding:26px 18px}h1{color:#a78bfa;font-size:25px;text-align:center;margin:14px 0 6px}.sub{text-align:center;color:#8b86b8;font-size:13.5px;margin-bottom:18px}.item{background:#171430;border:1px solid #262250;border-radius:12px;padding:13px 16px;margin:9px 0}.item .q{font-size:14.8px;margin-bottom:9px}.item .q b{color:#7c6fd0;margin-right:6px}.opts{display:flex;gap:5px}.opts label{flex:1;text-align:center;font-size:11.5px;color:#9b95c9;border:1px solid #322d68;border-radius:8px;padding:8px 2px;cursor:pointer}.opts input{display:none}.opts input:checked+span{display:block;background:#7c3aed;color:#fff;border-radius:6px;padding:4px 0;margin:-4px 0}.btn{background:#7c3aed;color:#fff;border:none;border-radius:12px;font-size:16px;padding:12px 40px;cursor:pointer}#result{display:none}.score-big{text-align:center}.score-big .num{font-size:44px;color:#c4b5fd;font-weight:bold}.b1{border-left:4px solid #34d399}.b2{border-left:4px solid #fbbf24}.b3{border-left:4px solid #f97316}.b4{border-left:4px solid #ef4444}"

for sc in SCALES:
    items_js = json.dumps(sc["items"], ensure_ascii=False)
    opts_js = json.dumps(sc["opts"], ensure_ascii=False)
    rev_js = json.dumps(sc["rev"])
    lv_js = json.dumps(sc["lv"], ensure_ascii=False)
    adv_js = json.dumps(sc["adv"], ensure_ascii=False)

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{sc['title']}</title><style>{CSS}</style></head><body><div class="wrap"><h1>{sc['title']}</h1><p class="sub">{sc['sub']}</p><div id="quiz"></div><div style="text-align:center;margin:18px"><button class="btn" onclick="calc()">查看结果</button><button class="btn" style="background:#262250;margin-left:8px" onclick="location.reload()">重填</button></div><div id="result"></div></div><script>
const ITEMS={items_js};const OPT={opts_js};const REV=new Set({rev_js});const LV={lv_js};const ADV={adv_js};
let h="";ITEMS.forEach((it,i)=>{{h+=`<div class="item"><div class="q"><b>${{i+1}}.</b>${{it.t}}</div><div class="opts">`;for(let v=1;v<=OPT.length;v++){{h+=`<label><input type="radio" name="q${{i}}" value="${{v}}"><span>${{OPT[v-1]}}</span></label>`}}h+=`</div></div>`}});document.getElementById("quiz").innerHTML=h;
function calc(){{let total=0,ans=0;ITEMS.forEach((it,i)=>{{const s=document.querySelector(`input[name="q${{i}}"]:checked`);if(!s)return;ans++;let v=+s.value;if(REV.has(i))v=OPT.length+1-v;total+=v}});if(ans<ITEMS.length){{alert(`还有${{ITEMS.length-ans}}题未答`);return}}let html=`<div class="score-big"><span class="num">${{total}}</span><span>/${{ITEMS.length*OPT.length}}</span></div>`;LV.forEach(l=>{{if(total>=l.min)html+=`<div class="item ${{l.c}}"><h2>${{l.n}}</h2>${{l.txt}}</div>`}});if(ADV)html+=ADV;const r=document.getElementById("result");r.innerHTML=html;r.style.display="block";window.scrollTo({{top:r.offsetTop-20,behavior:"smooth"}})}}
</script></body></html>"""
    print(f"<<<FILE:{sc['fn']}>>>")
    print(html)

print("<<<ALL_DONE>>>")
