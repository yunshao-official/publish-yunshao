# -*- coding: utf-8 -*-
"""生成两本网页版《多维解离体验量表》：甲册快筛（24 计分题＋1 检查题）、乙册全量（64 计分题＋2 检查题）。
题面为自编措辞，症状域参照 ICD-11 与 DSM-5 对分离（解离）障碍的描述，未复制任何受版权保护量表的原题。
输出两个自包含 HTML：无外链、无联网代码，手机浏览器直接打开即可，答案与历次结果只存本机。
"""
import json, os

OUT = '/data/out/多维解离量表'
DATE = '2026-11-03'

DIMS = [
    ('D1', '遗忘与时间断层', '记不起来、时间整块消失'),
    ('D2', '身份连续性与内部多元感', '心里像住着不止一个“我”'),
    ('D3', '人格解体', '从外面看自己、情绪与身体断连'),
    ('D4', '现实解体', '世界与场景“不像真的”'),
    ('D5', '沉浸与注意抽离', '进去、白日梦、时间被吞掉'),
    ('D6', '自我—他人边界弥散', '别人的东西灌进来、“我”变淡'),
    ('D7', '躯体形式解离', '疼痛、麻木、身体图式改变'),
    ('D8', '触发相关退行与再体验', '被线索拽回往事、退到很小'),
]

ITEMS = {
'D1': [
    '事后发现自己已经到了某地、或已经办完某事，却想不起中间那段是怎么过去的',
    '手机或电脑里出现自己不记得写过、拍过的记录',
    '别人说我说过或做过某件事，我一点印象都没有，而且不像是玩笑',
    '有几小时以上的一段记忆整块不见了，事后怎么也补不上',
    '在明明很熟悉的地方（家里、常走的路）出现陌生感，要靠线索重新认出自己',
    '发现买回来的东西、花掉的钱，说不清是什么时候、为什么发生的',
    '该记得的昨天或上周，其实只留下别人的转述，没有第一人称的体验',
    '明确知道“这段时间不见了”，而不只是忘了细节',
],
'D2': [
    '心里像住着不止一个“我”，各自的语气、喜好、立场明显不同',
    '不同的“部分”会各自接管一段时间的生活，彼此之间信息不通',
    '身边的人用不同的称呼和我相处，切换得很彻底',
    '兴趣、目标、价值观会在短时间内整套换一遍，像换了个人',
    '写字或打字时，笔迹、用词、风格判若两人',
    '对自己做过的事感到“那不是我”，程度远超普通的后悔',
    '内心有几个成员在对话、争吵或投票，我能听见或看见这个过程',
    '担心自己失控时会变成另一个人、做出完全不属于自己的事',
],
'D3': [
    '像从外面看自己，或从窗外、天花板的角度看自己在动作',
    '自己的名字、面孔、声音听起来或看上去很陌生',
    '情绪像被关掉：知道“这时该难过”，却什么也感觉不到',
    '身体某部分的大小、形状、位置感觉不对',
    '说话时像隔着一层东西，声音不像自己的',
    '疼痛变得遥远，或过了很久才感觉到',
    '镜子里的人要认上几秒，才确认那是自己',
    '明明在做事情，却像程序在自动跑，“我”没有在场',
],
'D4': [
    '世界像布景或纸板，颜色变淡、发灰',
    '场景失去三维感，像一张照片或一块屏幕',
    '声音变得遥远、发闷，像隔着一层水',
    '时间、空间、距离的感觉不可靠',
    '熟悉的地方、人、物品突然“不像真的”',
    '光线、声音变得刺耳刺眼，整个世界像过载',
    '理智上知道是真的，但体验上完全信不过来',
    '在人多的地方或嘈杂环境里最容易出现上面这些感觉',
],
'D5': [
    '看剧、读书、发呆时会整个“进去”，被叫好几声才回神',
    '白日梦有剧本、有角色、有连续情节，一次能很久',
    '因为沉浸进去而错过公交、会议或约好的事',
    '想象力极强：画面、声音、身体感觉能像真发生了一样',
    '别人说我发呆时脸上有表情、嘴在动',
    '沉浸被打断后会烦躁、迷失方向很久',
    '一无聊或有压力，就自动躲进心里的场景',
    '有时分不清“我想象的”和“我真正经历过的”',
],
'D6': [
    '别人的情绪像被灌进来：明明是 ta 的事，我却难受得不行',
    '人多的场合身体边界变模糊，分不清哪里是自己、哪里是别人',
    '突然冒出不像自己的念头或冲动，感觉是外来的',
    '和人亲近时“我”会变淡，事后要好一阵才回到自己',
    '被批评或被注视时，有强烈的“被撕开”感',
    '对分离、搬家、关系变动反应异常剧烈',
    '独处时反而说不清自己的偏好和决定，要靠参照别人',
    '亲密之后会冒出陌生的羞耻、厌恶或空，像不是自己的反应',
],
'D7': [
    '受伤、拔牙、烫伤时几乎不觉得疼，疼在别的时间才出现',
    '身体局部麻木、失感，检查查不出原因',
    '身体某部分感觉不属于自己，或像多出来、缺失了',
    '出现不属于已知疾病的感觉异常（比如体内有东西在移动、跳动）',
    '肢体无力、发抖、走路不稳，检查未见器质性问题',
    '有一阵看不见、听不见或说不出话，过后自己恢复',
    '喉咙发紧、吞咽困难反复出现，却没有明确的器质原因',
    '身体的形状感随情绪改变：觉得自己变高、变厚、变透明',
],
'D8': [
    '特定的气味、声音、光线或场景，会把身体感觉拽回某段往事',
    '被触发时年龄感、语气、行为退到很小的时候',
    '触发时冒出与往事相关的画面、声音或身体感觉，像重新发生一遍',
    '为了躲开触发点，改变路线、拒绝某些场合',
    '触发之后极度羞耻、厌恶自己，很久散不掉',
    '触发时会有别的“部分”顶上来应付，事后不记得自己怎么撑过去的',
    '触发时的心跳、发抖、麻木和当下的处境完全不成比例',
    '这种回避已经影响到工作、学业或就医',
],
}

CHECKS = [('K1', '本题是注意力检查，请直接选“有时”', '2'),
          ('K2', '本题是注意力检查，请直接选“从不”', '0')]

A_IDX = [0, 3, 7]


def build(form):
    items = []
    for code, _n, _g in DIMS:
        idxs = A_IDX if form == 'A' else list(range(8))
        for i in idxs:
            items.append({'id': '%s%d' % (code, i + 1), 'dim': code, 'text': ITEMS[code][i]})
    checks = CHECKS[:1] if form == 'A' else CHECKS
    for c, t, _v in checks:
        items.append({'id': c, 'dim': None, 'text': t})
    return items, {c: v for c, _t, v in checks}


META = {
    'A': {'label': '甲册 · 快筛', 'n': 24, 'file': '多维解离体验量表-甲册-快筛-20261103.html',
          'title': '多维解离体验量表 · 甲册（快筛）',
          'minutes': '约 3–5 分钟', 'per': 3, 'cutoff': 30.0,
          'line': '甲册总均分 ≥ 30：提示解离体验偏多，建议接着做乙册（全量 64 题）逐维定位。'},
    'B': {'label': '乙册 · 全量', 'n': 64, 'file': '多维解离体验量表-乙册-全量-20261103.html',
          'title': '多维解离体验量表 · 乙册（全量）',
          'minutes': '约 12–20 分钟', 'per': 8, 'cutoff': 35.0,
          'line': '乙册总均分 ≥ 35，或任一维 ≥ 50：提示值得带去专业面谈进一步评估（本量表不作诊断）。'},
}

TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0f1220">
<title>__TITLE__</title>
<style>
:root{--bg:#f6f5fb;--card:#fff;--ink:#1b1d29;--sub:#5c6070;--line:#e3e2ee;--acc:#5a4fd6;--acc2:#8f7bf0;--warn:#b4232a;--ok:#1f7a4d;--bar:#efedfb}
@media (prefers-color-scheme:dark){:root{--bg:#0f1220;--card:#181c2c;--ink:#eceaf6;--sub:#a4a8bd;--line:#2a2f45;--acc:#9a8bff;--acc2:#6f61d8;--warn:#ff9a9a;--ok:#5fd39a;--bar:#242a41}}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;padding:0 0 48px}
.wrap{max-width:640px;margin:0 auto;padding:16px}
h1{font-size:20px;margin:6px 0 2px;line-height:1.35}
h2{font-size:17px;margin:20px 0 8px}
h3{font-size:15px;margin:16px 0 6px;color:var(--sub);font-weight:600}
p{margin:8px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:12px 0}
.sub{color:var(--sub);font-size:14px}
.tag{display:inline-block;font-size:12px;padding:2px 8px;border-radius:999px;background:var(--bar);color:var(--acc);margin:0 6px 0 0}
.btn{display:block;width:100%;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:12px;padding:14px;font-size:16px;font-family:inherit;margin:8px 0;text-align:center}
.btn.pri{background:var(--acc);color:#fff;border-color:var(--acc);font-weight:600}
.btn.gho{background:transparent;color:var(--acc);border-color:transparent}
.opt{display:flex;align-items:center;gap:10px;border:1px solid var(--line);border-radius:12px;padding:14px;margin:8px 0;font-size:16px;background:var(--card)}
.opt.sel{border-color:var(--acc);background:var(--bar)}
.opt b{width:18px;text-align:center;color:var(--acc);font-size:14px;flex:none}
.pbar{height:6px;background:var(--line);border-radius:99px;overflow:hidden;margin:8px 0 2px}
.pbar i{display:block;height:100%;background:linear-gradient(90deg,var(--acc2),var(--acc));border-radius:99px;transition:width .2s}
.row{display:flex;gap:8px}.row .btn{flex:1}
.dim{margin:12px 0}
.dim .lab{display:flex;justify-content:space-between;font-size:14px;margin-bottom:4px;gap:8px}
.bar{height:12px;background:var(--bar);border-radius:99px;overflow:hidden}
.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--acc2),var(--acc))}
.bar.hot i{background:linear-gradient(90deg,#e07b39,#b4232a)}
.num{font-variant-numeric:tabular-nums}
.big{font-size:34px;font-weight:700;letter-spacing:-1px}
.warn{color:var(--warn)}.ok{color:var(--ok)}
ul{padding-left:20px;margin:6px 0}li{margin:5px 0}
details{margin:8px 0}summary{cursor:pointer;color:var(--acc);font-size:15px;padding:4px 0}
.qlist{font-size:14px;color:var(--sub)}
.qlist div{padding:5px 0;border-bottom:1px dashed var(--line)}
.foot{text-align:center;font-size:12px;color:var(--sub);margin-top:18px}
.qtag{font-size:13px;color:var(--acc);letter-spacing:.5px}
.q{font-size:19px;line-height:1.5;margin:6px 0 16px;min-height:56px}
.chk{font-size:14px;color:var(--warn);border:1px dashed var(--warn);border-radius:10px;padding:8px 10px;margin:10px 0}
</style>
</head>
<body>
<div class="wrap" id="app"></div>
<script>
"use strict";
var META=__META__;
var DIMS=__DIMS__;
var ITEMS=__ITEMS__;
var CHECKKEY=__CHECKKEY__;
var GEN='__GEN__';
var KEY='ys_disassoc_v1';
var DRAFT=KEY+'_draft_'+META.label;
var SCALE=[[0,'从不'],[1,'很少（不到 5% 的时间）'],[2,'有时（约 10–30%）'],[3,'经常（约 30–50%）'],[4,'几乎总是（一半以上）']];
var MEM={};
function get(k){try{var v=localStorage.getItem(k);if(v!==null)return v}catch(e){}return MEM[k]||null}
function put(k,v){try{localStorage.setItem(k,v)}catch(e){MEM[k]=v}}
function drop(k){try{localStorage.removeItem(k)}catch(e){}delete MEM[k]}
function load(){try{var a=JSON.parse(get(KEY)||'[]');return Array.isArray(a)?a:[]}catch(e){return []}}
function save(r){var all=load();all.unshift(r);all=all.slice(0,20);put(KEY,JSON.stringify(all))}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function isChk(it){return !it.dim}
var NSC=ITEMS.filter(function(x){return !!x.dim}).length;
var st={i:0,ans:new Array(ITEMS.length).fill(null)};
function answered(){return st.ans.filter(function(v,i){return v!==null&&ITEMS[i].dim}).length}
function badChecks(){var b=[];ITEMS.forEach(function(it,i){if(isChk(it)&&st.ans[i]!==null&&String(st.ans[i])!==CHECKKEY[it.id])b.push(it.id)});return b}
function calc(ans){
  var acc={},cnt={};
  ITEMS.forEach(function(it,i){if(it.dim&&ans[i]!==null){acc[it.dim]=(acc[it.dim]||0)+ans[i];cnt[it.dim]=(cnt[it.dim]||0)+1}});
  var per={},sum=0,n=0;
  DIMS.forEach(function(d){var c=d[0];cnt[c]=cnt[c]||0;if(cnt[c]){per[c]=Math.round(acc[c]/(cnt[c]*4)*1000)/10;sum+=acc[c];n+=cnt[c]}else per[c]=null});
  per.__total=n?Math.round(sum/(n*4)*1000)/10:null;per.__n=n;return per;
}
function intro(){
  var d=draft();
  var h='<h1>'+esc(META.title)+'</h1><div class="sub">'+esc(META.minutes)+' · 共 '+ITEMS.length+' 屏（'+NSC+' 题计分 + '+(ITEMS.length-NSC)+' 题检查）</div>';
  h+='<div class="card"><span class="tag">近三个月</span><span class="tag">频率自评</span><span class="tag">0–4 五档</span><h2>指导语</h2>'
   +'<p>下面每句都是一种<strong>体验</strong>，请按它<strong>在近三个月里出现的频率</strong>选一档。没有对错，也不看“我像不像病人”。</p>'
   +'<p class="sub">其中有注意力检查题，直接按题目说的选就行。它用来核对这份结果有没有被手滑或敷衍污染。</p></div>';
  h+='<div class="card"><h2>它是什么、不是什么</h2><ul>'
   +'<li><strong>是</strong>：把主观的解离体验按八个维度量化，让你自己看见结构，也方便把体验讲给专业的人听。</li>'
   +'<li><strong>不是</strong>：不是诊断工具。它不判分离性身份障碍，也不判任何 ICD-11 / DSM-5 条目；诊断只能由专业人员面谈并做必要检查（含排除器质性与物质因素）。</li>'
   +'<li><strong>无常模</strong>：题面与分档为自编，未做中文人群常模、信度、效度与因子结构检验。分数只能与<strong>你自己的上一次</strong>比较，不能与他人比较，也不能当分界值用。</li>'
   +'<li><strong>隐私</strong>：本文件不含任何联网代码，断网可用；答案与历次结果只存在这台手机浏览器里（localStorage），可一键清除。</li></ul></div>';
  h+='<div class="card"><h2>如果你此刻很难受</h2><p>出现伤害自己的念头时，请立刻拨打 <strong>12356</strong>（全国统一心理援助热线，免费、24 小时）或 <strong>120</strong>，也可以直接去就近医院急诊。量表随时可以重做。</p></div>';
  if(d&&d.answered>0)h+='<button class="btn pri" onclick="resume()">继续未完成的作答（第 '+(d.i+1)+' 屏，已答 '+d.answered+' 题）</button><button class="btn" onclick="go(true)">重新开始</button>';
  else h+='<button class="btn pri" onclick="go(false)">我已读完，开始作答</button>';
  var recs=load();
  if(recs.length)h+='<button class="btn gho" onclick="last()">看最近一次结果（'+esc(recs[0].form)+'，'+new Date(recs[0].ts).toLocaleDateString()+'）</button>';
  return h;
}
function draft(){try{var d=JSON.parse(get(DRAFT)||'null');if(d&&d.ans&&d.ans.length===ITEMS.length){d.answered=d.ans.filter(function(v,i){return v!==null&&ITEMS[i].dim}).length;return d}}catch(e){}return null}
function putDraft(){put(DRAFT,JSON.stringify({i:st.i,ans:st.ans}))}
function resume(){var d=draft();if(d){st.i=d.i;st.ans=d.ans}set('quiz');q()}
function go(reset){if(reset)drop(DRAFT);st={i:0,ans:new Array(ITEMS.length).fill(null)};set('quiz');q()}
function last(){var a=load();if(!a.length){alert('本机还没有记录');return}set('res');res(a[0])}
function set(v){document.getElementById('app').dataset.v=v}
function q(){
  var it=ITEMS[st.i],dn='';
  if(it.dim)DIMS.forEach(function(d){if(d[0]===it.dim)dn=d[1]});
  var h='<h1>'+esc(META.label)+'</h1>';
  h+='<div class="pbar"><i style="width:'+((st.i+1)/ITEMS.length*100).toFixed(1)+'%"></i></div>';
  h+='<div class="sub num">'+(st.i+1)+' / '+ITEMS.length+' · 已答 '+answered()+'</div>';
  h+='<div class="qtag">'+(it.dim?('〔 '+esc(dn)+' 〕'):'〔 检查题 〕')+'</div>';
  h+='<div class="q">'+esc(it.text)+'</div>';
  if(isChk(it))h+='<div class="chk">按题目说的选即可，这一题不计分</div>';
  var cur=st.ans[st.i];
  SCALE.forEach(function(s,i){h+='<div class="opt'+(cur===s[0]?' sel':'')+'" onclick="pick('+s[0]+')"><b>'+'ABCDE'[i]+'</b><span>'+esc(s[1])+'</span></div>'});
  h+='<div class="row"><button class="btn" onclick="prev()"'+(st.i===0?' disabled style="opacity:.4"':'')+'>上一题</button>';
  h+='<button class="btn" onclick="skip()">跳过</button>';
  h+='<button class="btn pri" onclick="next()">'+(st.i===ITEMS.length-1?'看结果':'下一题')+'</button></div>';
  h+='<div class="sub" style="margin-top:10px">自动保存草稿：中途关页面、切出去，回来可以接着做。</div>';
  document.getElementById('app').innerHTML=h;window.scrollTo(0,0);
}
function pick(v){st.ans[st.i]=v;putDraft();next()}
function skip(){st.ans[st.i]=null;putDraft();next()}
function prev(){if(st.i>0){st.i--;putDraft();q()}}
function next(){if(st.i<ITEMS.length-1){st.i++;putDraft();q()}else finish()}
function finish(){
  var n=answered();
  if(n<Math.ceil(NSC*0.75)){if(!confirm('只答了 '+n+' / '+NSC+' 计分题，不足 75%。结果只能当未完成参考，继续？'))return}
  var per=calc(st.ans);
  var rec={ts:new Date().toISOString(),form:META.label,total:per.__total,answered:per.__n,of:NSC,per:per,
           bad:badChecks(),ans:st.ans.slice(),ids:ITEMS.map(function(x){return x.id}),gen:GEN};
  save(rec);drop(DRAFT);set('res');res(rec);
}
function res(rec){
  var per=rec.per||{},t=rec.total;
  var h='<h1>结果 · '+esc(rec.form||META.label)+'</h1>';
  h+='<div class="sub">'+new Date(rec.ts).toLocaleString()+' · 已答 '+(rec.answered||0)+' / '+(rec.of||NSC)+' 计分题</div>';
  if(rec.bad&&rec.bad.length)h+='<div class="chk">注意力检查未通过：'+esc(rec.bad.join('、'))+'。本次数据可靠性存疑，结果照记不删，建议重做。</div>';
  h+='<div class="card"><div class="sub">总均分（0–100，全部已答计分题的平均频率）</div><div class="big num">'+(t===null||t===undefined?'—':t)+'</div>';
  if(t!==null&&t!==undefined){
    h+=(t>=META.cutoff)?'<div class="warn">已达本册提示线 '+META.cutoff+'</div>':'<div class="ok">低于本册提示线 '+META.cutoff+'（无常模，仅供自我观察）</div>';
  }
  h+='<div class="sub" style="margin-top:8px">'+esc(META.line)+'</div></div>';
  h+='<div class="card"><h2>八个维度</h2>';
  var hot=[];
  DIMS.forEach(function(d){
    var v=per[d[0]];
    if(v===null||v===undefined){h+='<div class="dim"><div class="lab"><span>'+d[0]+' '+esc(d[1])+'</span><span class="sub">未作答</span></div><div class="bar"><i style="width:0"></i></div></div>';return}
    if(v>=50)hot.push([d[0],d[1],v]);
    h+='<div class="dim"><div class="lab"><span>'+d[0]+' '+esc(d[1])+'</span><span class="num">'+v+'</span></div>'
     +'<div class="bar'+(v>=50?' hot':'')+'"><i style="width:'+Math.min(100,v)+'%"></i></div><div class="sub">'+esc(d[2])+'</div></div>';
  });
  h+='</div>';
  h+='<div class="card"><h2>怎么读</h2><ul>'
   +'<li>每根条＝该维度<strong>已答题的平均频率 ×25</strong>：0 是从不，100 是几乎总是。</li>'
   +'<li>条长 ≥ 50 会变暖色：意思是这一维近三个月里大约三分之一以上的时间在发生。</li>'
   +'<li>八维<strong>不齐</strong>本身就是信息——解离体验常常只在一两维重，其余接近零。</li>'
   +'<li>跨维度比较要小心：每维题数相同（本册每维 '+META.per+' 题），但题面难度不同，高低不等于严重度排序。</li></ul>';
  if(hot.length){h+='<h3>本次偏高的维度（≥50）</h3><ul>';
    hot.sort(function(a,b){return b[2]-a[2]}).forEach(function(x){h+='<li>'+x[0]+' '+esc(x[1])+'　<span class="num">'+x[2]+'</span></li>'});h+='</ul>'}
  else h+='<div class="sub">本次没有 ≥ 50 的维度。</div>';
  h+='</div>';
  h+='<div class="card"><h2>带去面谈用</h2><p class="sub">下面的纯文字含日期、册别、总均、八维、检查情况与偏高维度，可直接复制给医生或咨询师；页面本身不上传任何数据。</p>'
   +'<button class="btn pri" onclick="copyText()">复制结果文字</button>'
   +'<button class="btn" onclick="dl()">下载本次 JSON（逐题原始答案在内）</button>'
   +'<details><summary>展开逐题原始答案</summary><div class="qlist" id="ql"></div></details></div>';
  var a=load();
  h+='<div class="card"><h2>历次记录（本机 '+a.length+' 次，最多存 20 次）</h2><div class="qlist" id="hist"></div>'
   +'<button class="btn" onclick="go(true)">再做一次</button>'
   +'<button class="btn gho" onclick="clr()">清除全部本机记录</button></div>';
  h+='<div class="card"><h2>口径与局限（照录不删）</h2><ul>'
   +'<li>本册共 '+ITEMS.length+' 屏：'+NSC+' 题计分（8 维 × 每维 '+META.per+' 题）＋ '+(ITEMS.length-NSC)+' 题注意力检查，检查题不计分、只作有效性标记。</li>'
   +'<li>计分：维内原始分 ÷（该维已答题数 × 4）× 100，保留一位小数；跳过题不进分母。</li>'
   +'<li>提示线 '+META.cutoff+'（总均）与 50（单维）均为<strong>本文件自设的提醒阈值</strong>，不是临床分界值。</li>'
   +'<li>题面为自编措辞，症状域参照 ICD-11 与 DSM-5 对分离（解离）障碍的描述，未复制任何受版权保护量表的原题。</li>'
   +'<li>未做信度、效度、因子结构、测量等值性与重测稳定性检验：不可用于科研入组、诊断、伤残鉴定或司法用途。</li>'
   +'<li>D2 / D6 / D7 的体感同样可见于睡眠剥夺、癫痫、偏头痛、物质或药物影响、甲状腺与电解质异常等；须由专业检查排除后才能归因于解离。</li>'
   +'<li>版本族：甲册（'+META.per+'×8）与乙册（8×8）共用同一题库与同一本机记录键，可纵向比较。</li></ul></div>';
  h+='<div class="foot">多维解离体验量表 · '+esc(rec.form||META.label)+' · 自包含单机网页版 · '+GEN+' 生成</div>';
  document.getElementById('app').innerHTML=h;
  var ql=document.getElementById('ql');
  if(ql&&rec.ids){var s='';rec.ids.forEach(function(id,i){var it=ITEMS[i];if(!it)return;var v=rec.ans[i];
    var lab='（跳过）';if(v!==null&&v!==undefined)lab=SCALE.filter(function(x){return x[0]===v})[0][1];
    s+='<div>'+esc(it.dim||'检查')+' '+esc(id)+'　'+esc(lab)+'　<span class="sub">'+esc(it.text.slice(0,24))+'</span></div>'});ql.innerHTML=s||'<div>无逐题数据</div>'}
  var hb=document.getElementById('hist');
  if(hb){var s2='';a.forEach(function(r,i){s2+='<div>'+(i===0?'▶ ':'　 ')+new Date(r.ts).toLocaleString()+'　'+esc(r.form)+'　总均 <span class="num">'+(r.total===null?'—':r.total)+'</span>'
    +(r.bad&&r.bad.length?'　<span class="warn">检查未过</span>':'')+'</div>'});hb.innerHTML=s2||'<div>（空）</div>'}
  window.scrollTo(0,0);
}
function plain(){
  var r=load()[0];if(!r)return '本机还没有结果。';
  var L=['多维解离体验量表 · '+r.form,'时间：'+new Date(r.ts).toLocaleString(),
   '已答：'+r.answered+' / '+r.of+' 计分题','总均分（0–100）：'+(r.total===null?'—':r.total)+'（本册提示线 '+META.cutoff+'，无临床常模）'];
  DIMS.forEach(function(d){var v=r.per[d[0]];L.push(d[0]+' '+d[1]+'：'+(v===null||v===undefined?'未作答':v))});
  if(r.bad&&r.bad.length)L.push('注意力检查未通过项：'+r.bad.join('、')+'（本次可靠性存疑）');
  L.push('说明：自编筛查用自评量表，非诊断工具；分数仅供专业面谈参考。');
  return L.join('\n');
}
function copyText(){
  var t=plain();
  function fb(){var ta=document.createElement('textarea');ta.value=t;ta.style.position='fixed';ta.style.left='-9999px';document.body.appendChild(ta);ta.focus();ta.select();
    var ok=false;try{ok=document.execCommand('copy')}catch(e){}document.body.removeChild(ta);alert(ok?'已复制，可直接粘贴给专业的人看。':'复制失败，请长按结果文字手动复制。')}
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(function(){alert('已复制，可直接粘贴给专业的人看。')},fb)}else fb();
}
function dl(){
  var r=load()[0];if(!r)return;
  try{
    var b=new Blob([JSON.stringify(r,null,2)],{type:'application/json'});
    var a=document.createElement('a');a.href=URL.createObjectURL(b);
    a.download='解离量表-'+r.form.replace(/[^一-龥A-Za-z0-9]/g,'')+'-'+r.ts.slice(0,10)+'.json';
    document.body.appendChild(a);a.click();document.body.removeChild(a);
  }catch(e){alert('这台浏览器不支持直接下载，请用“复制结果文字”。')}
}
function clr(){
  if(!confirm('将删除本机保存的全部历次记录，无法恢复。确定？'))return;
  drop(KEY);drop(DRAFT);document.getElementById('app').innerHTML=intro();
}
document.getElementById('app').innerHTML=intro();
</script>
</body>
</html>
"""


def emit(form):
    items, checkkey = build(form)
    m = META[form]
    dims_json = json.dumps([[d[0], d[1], d[2]] for d in DIMS], ensure_ascii=False)
    meta_json = json.dumps({'label': m['label'], 'title': m['title'], 'minutes': m['minutes'],
                            'cutoff': m['cutoff'], 'line': m['line'], 'per': m['per']}, ensure_ascii=False)
    html = (TPL.replace('__TITLE__', m['title'])
               .replace('__META__', meta_json)
               .replace('__DIMS__', dims_json)
               .replace('__ITEMS__', json.dumps(items, ensure_ascii=False))
               .replace('__CHECKKEY__', json.dumps(checkkey, ensure_ascii=False))
               .replace('__GEN__', DATE))
    path = os.path.join(OUT, m['file'])
    open(path, 'w', encoding='utf-8').write(html)
    return path, items, checkkey


if __name__ == '__main__':
    for f in ('A', 'B'):
        p, items, ck = emit(f)
        sc = len([i for i in items if i['dim']])
        print('%s | 总屏 %d（计分 %d + 检查 %d）| %d bytes' % (os.path.basename(p), len(items), sc, len(items) - sc, os.path.getsize(p)))
