# -*- coding: utf-8 -*-
"""B16修复沙盒验证：模拟goldbach_core_cpp导入失败→降级goldbach2000→门禁必须拒绝未激活求解。
只读license，不碰license.dat；仅追加engine_event.log。"""
import sys, types, os

# ① cpu_governor桩（EXE内随包，开发树缺）
stub = types.ModuleType('cpu_governor')
stub.get_threads = lambda *a, **k: 2
stub.set_priority = lambda *a, **k: None
class _Gov:
    def __init__(self, *a, **k): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
stub.governor = _Gov
sys.modules['cpu_governor'] = stub

# ② 模拟主引擎导入失败（sys.modules置None → import抛ImportError）
sys.modules['goldbach_core_cpp'] = None

# ③ 导入GUI
sys.path.insert(0, r'C:\Users\Administrator\AppData\Local\hermes\workspace\yunshao')
import goldbach_gui as g

print('1. _USE_CPP =', g._USE_CPP, '(期望False=已降级)')
print('2. 降级引擎类型:', g._engine.__name__, '(期望goldbach2000)')
print('3. 降级引擎有is_activated:', hasattr(g._engine, 'is_activated'), '(期望False)')

# ④ 复现补丁后的门禁判据（与worker内一致）
gate_refuses = not getattr(g._engine, 'is_activated', lambda: False)()
print('4. fail-closed门禁拒绝未激活:', gate_refuses, '(期望True)')

# ⑤ 降级留痕文件
p = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'YS', 'engine_event.log')
print('5. engine_event.log存在:', os.path.exists(p))
if os.path.exists(p):
    tail = open(p, encoding='utf-8').read().strip().split('\n')[-1]
    print('   最新一条:', tail[:160])

# ⑥ 对照：C++引擎正常导入时门禁同样拒绝未激活
sys.modules.pop('goldbach_core_cpp', None)
import goldbach_core_cpp as gcc
gate_cpp = not getattr(gcc, 'is_activated', lambda: False)()
print('6. C++引擎未激活门禁拒绝:', gate_cpp, '(期望True), is_activated()=', gcc.is_activated())

ok = g._USE_CPP is False and g._engine.__name__ == 'goldbach2000' and gate_refuses and gate_cpp
print('== B16沙盒验证:', 'PASS' if ok else 'FAIL', '==')
