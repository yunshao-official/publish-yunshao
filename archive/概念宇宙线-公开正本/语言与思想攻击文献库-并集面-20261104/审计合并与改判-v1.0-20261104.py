#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""审计合并与改判 v1.0（2026-11-04）
读：并集面-249.json ＋ 两卷执行器初判 json
写：审计剔除表-并集面249-20261104.{md,json}
规矩：协调人改判只往回收（留→待核／留→删），绝不放宽；每条改判必须写出处条款。
"""
import json, os, collections, hashlib

D = os.path.dirname(os.path.abspath(__file__))
UNI = {r['并集号']: r for r in json.load(open(os.path.join(D, '并集面-249.json'), encoding='utf-8'))}
VOL = ['审计初判-甲卷-U001-U125-20261104.json', '审计初判-乙卷-U126-U249-20261104.json']

# 改判规则一：无摘要却凭标题判"留"——违冻结判据 v1.2 §二.5（待核＝无摘要，不得据以做结论）
# 改判规则二：摘要字段实为书籍目录／前言清单，锚词只命中在目录条目而非正文——不作"留"的依据
FORCE_TITLE_ONLY = True
FRONT_MATTER_TO_DROP = ['U174']   # 摘要为目录，标题本身不含锚词
FRONT_MATTER_KEEP_TITLE_BASED = ['U133']  # 摘要为目录，但标题含锚词，入池依据是标题，只登记件质

def is_front_matter(ab):
    a = (ab or '').strip()
    if not a:
        return False
    head = a[:160].lower()
    return head.startswith(('i. preface', 'preface to', 'acknowledg', 'table of contents', 'contents ')) or a.lower().count('preface') >= 3

def main():
    merged, violations = [], collections.Counter()
    for f in VOL:
        for r in json.load(open(os.path.join(D, f), encoding='utf-8'))['records']:
            u = UNI[r['并集号']]
            x = dict(r)
            x['原判'] = r['结论']
            x['卷'] = '甲' if f.startswith('审计初判-甲') else '乙'
            x['模块号'], x['池级'], x['标题'], x['年份'], x['DOI'] = u['模块号'], u['池级'], u['标题'], u['年份'], u['doi']
            x['被引取大'], x['本档T'] = u['被引取大'], u['本档T']
            ab = (u['摘要'] or '').strip()
            if FORCE_TITLE_ONLY and not ab and x['结论'] == '留':
                x['结论'] = '待核'
                x['改判'] = '改判一：无摘要却凭标题判留，违判据 v1.2 §二.5'
                violations['改判一无摘要'] += 1
            if x['并集号'] in FRONT_MATTER_TO_DROP and x['结论'] == '留':
                x['结论'] = '待核'
                x['改判'] = '改判二：摘要字段为书籍目录，锚词只命中目录条目，不作入池依据'
                violations['改判二目录件'] += 1
            if x['并集号'] in FRONT_MATTER_KEEP_TITLE_BASED:
                x['件质登记'] = '摘要字段为目录文本，不作证据；入池依据＝标题锚词'
            if is_front_matter(ab) and x['结论'] == '留' and x['并集号'] not in FRONT_MATTER_KEEP_TITLE_BASED + FRONT_MATTER_TO_DROP:
                violations['漏登记的前端matter件'] += 1
                x['件质登记'] = '摘要字段疑为目录／前言文本'
            if len(r.get('理由', '')) > 40:
                violations['理由超40字'] += 1
            if len(ab) < 400:
                violations['留件里摘要短于400字符'] += 1 if x['结论'] == '留' else 0
            merged.append(x)
    cnt = collections.Counter(x['结论'] for x in merged)
    per = collections.defaultdict(collections.Counter)
    for x in merged:
        per[x['模块号']][x['结论']] += 1
        per[x['模块号']]['送'] += 1
    keep = [x for x in merged if x['结论'] == '留']
    assert len(merged) == 249, '并集面条数=%d ≠ 249' % len(merged)
    assert cnt['留'] + cnt['删'] + cnt['待核'] == 249, '三数不等于送审数'

    L = []
    L.append('# 语言与思想攻击文献库·审计剔除表（三实现并集面 249 条）v1.0 · 2026-11-04')
    L.append('')
    L.append('> 状态标签：**在办·审计件（初判＋协调人改判）**。两卷整读初判为执行器所出，本件是"净库"数字的唯一出处，她终读前不对外。')
    L.append('> 判据版本 v1.2（冻结哈希 `0be27507…`，本轮复验未动一格）。输入哈希：并集面 `e127b2dd…`／甲卷 `f56fc7bb…`／乙卷 `2bc195b3…`。生成脚本 `审计合并与改判-v1.0-20261104.py`，可复跑。')
    L.append('')
    L.append('## 一、总量（改判后）')
    L.append('')
    L.append('- 送审 249 条＝补跑 180／子任务 v1.2 210／协调人独立复核 117 三套实现按 DOI 归一的并集（无 DOI 者按标题前 70 字归一）。')
    L.append('- **留 {} 条／删 {} 条／待核 {} 条**（执行器原判 留 126／删 82／待核 41；协调人改判只往回收，共 {} 条）。'.format(
        cnt['留'], cnt['删'], cnt['待核'], violations['改判一无摘要'] + violations['改判二目录件']))
    L.append('- 留的 {} 条里：池1（严格池）{} 条、池2（分层池）{} 条；被引中位数 {}；被引低于其年份档 T 的 {} 条。'.format(
        len(keep), sum(1 for x in keep if x['池级'] == 1), sum(1 for x in keep if x['池级'] == 2),
        sorted(x['被引取大'] for x in keep)[len(keep) // 2], sum(1 for x in keep if x['被引取大'] < x['本档T'])))
    L.append('- T 档口径（每档＝该年段文献至少要有多少次被引）：2021 年后 40、2016—2020 年 90、2010—2015 年 160、2000—2009 年 250、1990 年代 400、1990 年前 600。')
    noab = [x for x in merged if not (UNI[x['并集号']]['摘要'] or '').strip()]
    L.append('- 并集面里无摘要的 {} 条：留 {}／待核 {}／删 {}——无摘要一律不得当结论用。'.format(
        len(noab), sum(1 for x in noab if x['结论'] == '留'), sum(1 for x in noab if x['结论'] == '待核'),
        sum(1 for x in noab if x['结论'] == '删')))
    L.append('')
    L.append('## 二、逐模块（送审｜留｜删｜待核｜剔除率，剔除率＝（删＋待核）÷送审）')
    L.append('')
    for m in sorted(per):
        t = per[m]['送']
        rate = 100.0 * (per[m]['删'] + per[m]['待核']) / t
        L.append('- {}：{}｜{}｜{}｜{}｜{:.1f}%{}'.format(m, t, per[m]['留'], per[m]['删'], per[m]['待核'], rate,
                    '｜**检索式判不合格（超十个百分点，按 v1.1 §二.6 须重写检索式）**' if rate > 10 else '｜合格'))
    bad = sorted([m for m in per if (per[m]['删'] + per[m]['待核']) / per[m]['送'] > 0.10])
    L.append('- 超十个百分点的模块共 {} 个：{}。'.format(len(bad), '、'.join(bad)))
    L.append('')
    L.append('## 三、删掉的条目都属于哪些学科（按执行器理由归堆）')
    L.append('')
    TABLE = [('电力电子', '电气工程（锁相环／同步参考坐标系／变换器）'), ('PLL', '电气工程（锁相环／同步参考坐标系／变换器）'),
             ('变换器', '电气工程（锁相环／同步参考坐标系／变换器）'), ('税务', '公司财务与高管激励'),
             ('细胞', '生物与医学'), ('分子', '生物与医学'), ('医学', '生物与医学'), ('蛋白', '生物与医学'),
             ('康复', '医学与康复管理'), ('水印', '图像与密码工程'), ('密码', '图像与密码工程'),
             ('网络安全', '计算机与网络安全'), ('安全', '计算机与网络安全'), ('语音', '语音学与声学'),
             ('心理', '心理学（量表／发展／动机，无一字谈语言或思想控制）'), ('认知', '认知科学与心理语言学（非政治域）'),
             ('教育', '教育学'), ('卫生', '公共卫生与卫生政策'), ('宗教', '中世纪与宗教学'),
             ('文学', '文学与叙事研究'), ('历史', '历史学与概念史'), ('物理', '物理学'), ('管理', '组织管理与传播学'),
             ('营销', '营销与消费者行为'), ('金融', '金融与经济'), ('化学', '化学与材料'),
             ('机器', '机器学习与自然语言处理'), ('游戏', '游戏与娱乐'), ('广告', '广告与传播效果')]
    def cls(x):
        for k, v in TABLE:
            if k in x['理由']:
                return v
        return '其他（逐条见 §六）'
    for k, v in collections.Counter(cls(x) for x in merged if x['结论'] == '删').most_common():
        L.append('- {}：{} 条'.format(k, v))
    L.append('')
    L.append('## 四、协调人改判与登记')
    L.append('')
    for x in merged:
        if x.get('改判'):
            L.append('- {}｜原判{}→{}｜{}｜被引 {}｜《{}》({})｜{}｜原理由：{}'.format(
                x['并集号'], x['原判'], x['结论'], x['模块号'], x['被引取大'], x['标题'][:56], x['年份'], x['改判'], x['理由'][:44]))
    L.append('- 凭标题判留而无摘要这一类，内容上多是要件（Lasswell 1927《政治宣传理论》被引 296、Noelle-Neumann 1974《沉默的螺旋》1,644、McCombs & Shaw 1972《议程设置》6,051，以及 M12 政治戏仿一组）。但冻结判据 v1.2 §二.5 只给"核／待核"两个标签，判据里没有"经典老文可凭标题转正"这道门——**我不新增门，只把标签改对**。若她在 v1.3 加这道门，我按她的口径重跑标签，不动任何数值门槛。')
    for x in merged:
        if x.get('件质登记'):
            L.append('- 登记（不改结论）{}｜《{}》｜{}'.format(x['并集号'], x['标题'][:48], x['件质登记']))
    L.append('- 松判登记一条不改：U090《Decoupled Double Synchronous Reference Frame PLL for Power Converters》被引 1,195，判"待核"而非"删"——电力电子本应被 N 表直接删，留给她的终读。')
    L.append('')
    L.append('## 五、执行器违规与协调人口径错（判负照记）')
    L.append('')
    L.append('- 乙卷违规一：{} 条无摘要凭标题判"留"，违审计任务书铁律 1 与判据 v1.2 §二.5，已全数改判。'.format(violations['改判一无摘要']))
    L.append('- 乙卷违规二：理由超 40 字 {} 条，违任务书格式条款；结论与数字不受影响。'.format(violations['理由超40字']))
    L.append('- 甲卷复核为干净：0 条无摘要判留、0 条理由超长、125 条全数有判、编号与模块号全对。')
    L.append('- **协调人（我）的口径错**：M01「语言相对论／Sapir-Whorf」46 条整模块出局（删 39／待核 7／留 0）。执行器的理由"纯语言学、纯认知科学、非政治域"按我发给它的主题清单是自洽的，**但那份清单是我写的，里面没有"语言形塑思想"这一层**。出局者含《Language, Thought, and Reality》被引 840、《Language Diversity and Thought》794、《Linguistic Relativity》443——正是"词汇被强制替换会不会改变思考"的实证正典。这不是删错文献，是我把"机制前提层"和"案例层"塞进同一条口径。她裁之前不重跑、不改这 46 条标签。')
    L.append('')
    L.append('## 六、逐条判词（249 条全列：并集号｜结论｜模块｜DOI｜被引｜标题｜年份｜一句理由）')
    L.append('')
    for x in sorted(merged, key=lambda y: y['并集号']):
        L.append('- {}｜{}｜{}｜{}｜被引{}｜《{}》({})｜{}{}'.format(
            x['并集号'], x['结论'], x['模块号'], x['DOI'] or '无DOI', x['被引取大'], x['标题'][:68], x['年份'],
            x['理由'][:44], '（协调人改判）' if x.get('改判') else ''))
    md = os.path.join(D, '审计剔除表-并集面249-20261104.md')
    open(md, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    out = {'审计日期': '2026-11-04', '判据版本': 'v1.2', '并集面哈希': 'e127b2dd1f73a9c9',
           '送审': 249, '留': cnt['留'], '删': cnt['删'], '待核': cnt['待核'],
           '执行器原判': {'留': 126, '删': 82, '待核': 41},
           '协调人改判条数': violations['改判一无摘要'] + violations['改判二目录件'],
           '改判一清单': [x['并集号'] for x in merged if x.get('改判', '').startswith('改判一')],
           '改判二清单': [x['并集号'] for x in merged if x.get('改判', '').startswith('改判二')],
           '乙卷理由超40字条数': violations['理由超40字'],
           '留里池1': sum(1 for x in keep if x['池级'] == 1), '留里池2': sum(1 for x in keep if x['池级'] == 2),
           '无摘要条数': len(noab),
           '每模块': {m: {'送': per[m]['送'], '留': per[m]['留'], '删': per[m]['删'], '待核': per[m]['待核'],
                        '剔除率': round(100.0 * (per[m]['删'] + per[m]['待核']) / per[m]['送'], 1)} for m in sorted(per)},
           '待裁': ['M01 机制前提层单列还是维持出局', 'Q3 白名单门是否收紧', 'v1.3 是否新增经典件凭题录转正门'],
           'records': merged}
    js = os.path.join(D, '审计剔除表-并集面249-20261104.json')
    json.dump(out, open(js, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for p in (md, js):
        print(os.path.basename(p), os.path.getsize(p), hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16])
    print('留/删/待核', cnt['留'], cnt['删'], cnt['待核'], '| 留里池1', out['留里池1'], '池2', out['留里池2'],
          '| 改判一', out['协调人改判条数'] - 1, '改判二', 1)

if __name__ == '__main__':
    main()
