// 无浏览器环境下的量表页面自测：抽取 <script>、语法检查、模拟完整作答流程、核对计分算式。
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function extract(html) {
  const m = html.match(/<script>([\s\S]*?)<\/script>/);
  if (!m) throw new Error('no script block');
  return m[1];
}

function sandbox(shared) {
  const store = shared || {};
  const listeners = [];
  const els = {};
  const el = { innerHTML: '', dataset: {} };
  els.app = el;
  const doc = {
    getElementById: id => (els[id] || (els[id] = { innerHTML: '', dataset: {}, style: {} })),
    createElement: () => ({ style: {}, focus() {}, select() {}, click() {}, href: '', download: '' }),
    body: { appendChild() {}, removeChild() {} },
    execCommand: () => true,
  };
  const win = { scrollTo() {}, location: {} };
  const ctx = {
    document: doc, window: win, console,
    localStorage: {
      getItem: k => (k in store ? store[k] : null),
      setItem: (k, v) => { store[k] = String(v); },
      removeItem: k => { delete store[k]; },
    },
    alert: m => listeners.push(['alert', m]),
    confirm: m => { listeners.push(['confirm', m]); return true; },
    navigator: {}, Blob: function () {}, URL: { createObjectURL: () => 'blob:x' },
    JSON, Math, Date, Array, String, Object, Number, RegExp,
  };
  ctx.globalThis = ctx;
  return { ctx, el, store, listeners };
}

function run(file, answers, expect, shared) {
  const html = fs.readFileSync(file, 'utf8');
  const js = extract(html);
  const { ctx, el, store, listeners } = sandbox(shared);
  vm.createContext(ctx);
  vm.runInContext(js, ctx, { filename: path.basename(file) });

  // 首页渲染
  if (!/开始作答/.test(el.innerHTML)) throw new Error('intro 未渲染');
  const items = vm.runInContext('ITEMS', ctx);
  const NSC = vm.runInContext('NSC', ctx);
  if (items.length !== answers.length) throw new Error(`题数不符：页面 ${items.length} 屏 / 答卷 ${answers.length}`);

  // 模拟点击作答
  vm.runInContext('go(true)', ctx);
  answers.forEach((v, i) => {
    if (vm.runInContext('st.i', ctx) !== i) throw new Error(`第 ${i} 屏未对齐，st.i=${vm.runInContext('st.i', ctx)}`);
    if (v === null) vm.runInContext('skip()', ctx);
    else vm.runInContext(`pick(${v})`, ctx);
  });
  // 末屏 pick/skip 会自动 finish()；仅在未提交时补一次
  if (!store['ys_disassoc_v1']) vm.runInContext('finish()', ctx);

  const rec = JSON.parse(store['ys_disassoc_v1'])[0];
  const per = rec.per;
  // 独立复算（与页面算法无关的第二条路）
  const dims = vm.runInContext('DIMS', ctx);
  let sumAll = 0, nAll = 0;
  const chk = [];
  dims.forEach(([code]) => {
    const idx = items.map((it, i) => [it, i]).filter(([it]) => it.dim === code).map(([, i]) => i);
    const vals = idx.map(i => answers[i]).filter(v => v !== null);
    const score = vals.length ? Math.round((vals.reduce((a, b) => a + b, 0) / (vals.length * 4)) * 1000) / 10 : null;
    chk.push([code, score, per[code], vals.length]);
    if (vals.length) { sumAll += vals.reduce((a, b) => a + b, 0); nAll += vals.length; }
  });
  const total2 = nAll ? Math.round((sumAll / (nAll * 4)) * 1000) / 10 : null;
  const bad = items.filter((it, i) => !it.dim && answers[i] !== null && String(answers[i]) !== { K1: '2', K2: '0' }[it.id]).map(it => it.id);
  chk.forEach(([c, mine, page]) => { if (mine !== page) throw new Error(`${c} 维分不一致：独立复算 ${mine} / 页面 ${page}`); });
  if (total2 !== rec.total) throw new Error(`总均不一致：独立复算 ${total2} / 页面 ${rec.total}`);
  if (JSON.stringify(bad.sort()) !== JSON.stringify((rec.bad || []).sort())) throw new Error('检查题标记不一致：' + JSON.stringify(rec.bad) + ' vs ' + JSON.stringify(bad));
  if (rec.answered !== NSC - answers.filter((v, i) => v === null && items[i].dim).length) throw new Error('已答题数口径不符');
  // 结果页应已渲染，且含八维与局限声明
  ['八个维度', '口径与局限', '复制结果文字', '不是诊断'].forEach(s => {
    if (s === '不是诊断') { if (!/不是诊断工具/.test(fs.readFileSync(file, 'utf8'))) throw new Error('首页缺少“不是诊断工具”声明'); return; }
    if (!el.innerHTML.includes(s)) throw new Error('结果页缺少区块：' + s);
  });
  expect && expect(rec, items);
  return { rec, NSC, screens: items.length, listeners, htmlLen: html.length, store };
}

const dir = '/data/out/多维解离量表';
const jia = path.join(dir, '多维解离体验量表-甲册-快筛-20261103.html');
const yi = path.join(dir, '多维解离体验量表-乙册-全量-20261103.html');

// 用例 1：甲册全选“经常”(3)，检查题按要求选 2
let r = run(jia, new Array(24).fill(3).concat([2]));
console.log('甲册·全3分：总均', r.rec.total, '各维', Object.entries(r.rec.per).filter(([k]) => k[0] === 'D').map(([k, v]) => k + '=' + v).join(' '),
  '| 检查未过', r.rec.bad.length, '| 历次', JSON.parse(r.store['ys_disassoc_v1']).length);

// 用例 2：乙册全 0 + 检查题答错 → 应记 bad
r = run(yi, new Array(64).fill(0).concat([2, 1]));
console.log('乙册·全0分：总均', r.rec.total, '| 检查未过', r.rec.bad.join(','), '（预期 K2）');

// 用例 3：乙册每维一个档位（D1=0,D2=1,…,D5=4,D6=0,D7=1,D8=2）验证维分区分
const ans3 = [];
for (let d = 0; d < 8; d++) for (let k = 0; k < 8; k++) ans3.push(d % 5);
ans3.push(2, 0);
r = run(yi, ans3);
console.log('乙册·阶梯：总均', r.rec.total, '| D1/D4/D8 =', r.rec.per.D1, r.rec.per.D4, r.rec.per.D8, '（预期 0 / 75 / 50，总均 40.6）');

// 用例 4：跳过半数 → 触发不足 75% 提示，且跳过题不进分母
const ans4 = new Array(64).fill(null).map((v, i) => (i % 2 === 0 ? 4 : null)).concat([2, 0]);
r = run(yi, ans4);
console.log('乙册·隔题跳过：总均', r.rec.total, '已答', r.rec.answered, '| 提示', r.listeners.filter(x => x[0] === 'confirm').map(x => x[1].slice(0, 14)).join(' / '));

// 用例 5：草稿续答——答 5 题后“关页面”，同一存储重新打开应能续答
{
  const shared = {};
  const html = fs.readFileSync(jia, 'utf8');
  const js = extract(html);
  let a = sandbox(shared);
  vm.createContext(a.ctx); vm.runInContext(js, a.ctx);
  vm.runInContext('go(true)', a.ctx);
  for (let i = 0; i < 5; i++) vm.runInContext('pick(2)', a.ctx);
  const dk = Object.keys(shared).filter(k => k.includes('draft'));
  console.log('甲册·中途退出：草稿键', dk.map(k => k.split('_').pop()), '| 已存', shared[dk[0]] ? JSON.parse(shared[dk[0]]).ans.filter(v => v !== null).length : 0, '题');
  const b = sandbox(shared);
  vm.createContext(b.ctx); vm.runInContext(js, b.ctx);
  const canResume = /继续未完成的作答（第 6 屏，已答 5 题）/.test(b.el.innerHTML);
  vm.runInContext('resume()', b.ctx);
  const restored = vm.runInContext('JSON.stringify(st.ans.slice(0,5))+"|"+st.i', b.ctx);
  console.log('甲册·重开后首页给出续答入口：', canResume, '| 恢复后 st.i 与前 5 答：', restored);
  for (let i = 5; i < 25; i++) vm.runInContext('pick(3)', b.ctx);
  const recs = JSON.parse(shared['ys_disassoc_v1']);
  console.log('甲册·续答完成：总均', recs[0].total, '已答', recs[0].answered, '| 草稿已清除：', !Object.keys(shared).some(k => k.includes('draft')));
}

// 静态检查：无联网代码、无外链
[jia, yi].forEach(f => {
  const h = fs.readFileSync(f, 'utf8');
  const net = /fetch\(|XMLHttpRequest|WebSocket|navigator\.sendBeacon|src=["']http|href=["']http|@import|url\(http/.test(h);
  console.log('无联网代码：', !net, '| 体积', h.length, 'bytes |', path.basename(f));
});
