# -*- coding: utf-8 -*-
"""B16许可轨门禁七分支单测（G2测试锚）。
用法: python "B16-许可轨门禁-七分支单测.py"
预期: ALL PASS。任一FAIL=门禁逻辑被改动，禁止出包。"""
import sys, types
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Administrator\AppData\Local\hermes\workspace\yunshao')
import types as _t
_fg = _t.ModuleType('goldbach_license_gate'); _fg.get_level = lambda: ''
sys.modules['goldbach_license_gate'] = _fg
import goldbach_gui as g


def LM(data, act):
    return types.SimpleNamespace(data=data, is_activated=lambda: act)


cases = [
    ("未激活(no_license)", LM({'no_license': True}, False), (False, False)),
    ("corrupt损坏", LM({'corrupt': True}, False), (False, False)),
    ("有效激活pro", LM({'activated': True, 'tier_name': 'pro'}, True), (True, False)),
    ("有效激活student", LM({'activated': True, 'tier_name': 'student'}, True), (True, False)),
    ("pro过期→降级", LM({'activated': True, 'tier_name': 'pro'}, False), (True, True)),
    ("student过期→拒", LM({'activated': True, 'tier_name': 'student'}, False), (False, False)),
    ("异常防御(data=None)", LM(None, False), (False, False)),
]
allok = True
for name, lm, want in cases:
    got = g.GoldbachGUI._license_allows_solve(types.SimpleNamespace(license=lm))
    ok = got == want
    allok = allok and ok
    print(('PASS' if ok else 'FAIL'), name, 'got=', got, 'want=', want)
print('== B16许可轨门禁单测:', 'ALL PASS' if allok else 'FAIL', '==')
sys.exit(0 if allok else 1)
