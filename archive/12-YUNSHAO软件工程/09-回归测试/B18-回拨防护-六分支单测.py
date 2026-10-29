# -*- coding: utf-8 -*-
"""B18时钟回拨防护六分支单测（G2测试锚）。
用法: python "B18-回拨防护-六分支单测.py"
预期: ALL PASS。任一FAIL=回拨防护逻辑被改动，禁止出包。"""
import sys, types, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\Administrator\AppData\Local\hermes\workspace\yunshao')
import goldbach_gui as g

# 假yunshao_crypto（隔离真实%APPDATA%锚文件）
state = {'max_ts': 0, 'cnt': 0, 'nonce': None, 'saved': []}
fake = types.ModuleType('yunshao_crypto')


def _mono():
    return state['max_ts'], state['cnt'], state['nonce']


def _save(m, c, n=None):
    state['max_ts'] = m
    state['cnt'] = c
    state['saved'].append(m)


fake.monotonic_counter = _mono
fake.save_counter = _save
sys.modules['yunshao_crypto'] = fake


def LM(tol=3600):
    return types.SimpleNamespace(_ROLLBACK_TOL=tol, _lic_log=lambda k, d='': None)


def run(name, max_ts, want, want_saved, boom=False):
    state['max_ts'] = max_ts
    state['cnt'] = 0
    state['saved'] = []
    if boom:
        def bad():
            raise RuntimeError('boom')
        fake.monotonic_counter = bad
    else:
        fake.monotonic_counter = _mono
    got = g.LicenseManager._rollback_guard_ok(LM())
    ok = (got == want) and (len(state['saved']) > 0) == want_saved
    print(('PASS' if ok else 'FAIL'), name, 'got=', got, '锚推进=', len(state['saved']) > 0)
    return ok


now = int(time.time())
allok = True
allok &= run("无锚首用→放行并建锚", 0, True, True)
allok &= run("正常走时→推进锚", now - 100, True, True)
allok &= run("容差内回拨(30min)→放行", now + 1800, True, False)
allok &= run("超容差回拨(2h)→拒", now + 7200, False, False)
allok &= run("容差边界(1h整)→放行", now + 3600, True, False)
allok &= run("锚故障异常→放行", 0, True, False, boom=True)
print('== B18回拨防护单测:', 'ALL PASS' if allok else 'FAIL', '==')
sys.exit(0 if allok else 1)
