# -*- coding: utf-8 -*-
# patch_m1v2_v21.py — 生成 v3_construction_nx_m1v2-v2.1-20261002.cpp（4i --b1 主线化正本引擎）
# 预注册正本（判据冻结，实现不得偏离）：
#   H:\理论存档\01-数学\02-实验与数据\预注册---b1主线化网格v6程序性确认轮-v1.0-20260921.md §二（冻结）
# 基座 = v3_construction_nx_m1v2gwin-v1.0-20260921.cpp 全量逐字（=网格 v5 账 B1 臂引擎 m1v2gwin_v10.exe
#   md5=4397ead7293c3d56197e9991c3c8c331 的源；其链=m1v2anat v1.1（m1v2 全量逐字+纯日志插桩+EXIT127
#   修复件 closure_full 显式栈迭代）全量逐字+--b1 机制）。
# 唯一改动 = 预注册 §二 冻结改动面在本载体链上的落位（共两处）：
#   ①g_b1 默认值 0→1（B1 等额交付升为默认行为；--b1 <0/1> 旗标与 merge 扫描跳过行自 gwin 原样继承，
#     --b1 0=旧行为回退开关保留）；
#   ②头注块（新增）。
# 构造/修复/S 路线代码路径零触碰；eng 字段不动（对拍要求，与 gwin 同）。
# 载体链披露：预注册字面「m1v2 正本+新增 g_b1」若按 m1v2-v1.0 文件直改，将缺失 v1.1 修复件
#   （closure_full 递归版在 g++16.1.0 -O2 下 EXIT127，1e5 档不可跑）——主线化对象=「网格 v5 账
#   B1 臂的默认化」（预注册 §二 原文），故基座取 v5 B1 臂引擎源 gwin v1.0，diff vs gwin 仅
#   头注+默认值行，满足「唯一改动=默认值与旗标解析；构造/修复/S 路线代码路径零触碰」。
import io, sys

SRC = r"H:\理论存档\04-哈密顿路径\04-工具与代码\v3_construction_nx_m1v2gwin-v1.0-20260921.cpp"
DST = r"H:\理论存档\04-哈密顿路径\04-工具与代码\v3_construction_nx_m1v2-v2.1-20261002.cpp"

# 二进制读保 CRLF（基座全量逐字铁律：行尾一字节不动）
raw = open(SRC, "rb").read()
assert raw.count(b"\r\n") == raw.count(b"\n"), "mixed line endings"
txt = raw.decode("utf-8")

def rep(old, new, tag):
    global txt
    old = old.replace("\n", "\r\n")   # 基座=CRLF
    new = new.replace("\n", "\r\n")
    n = txt.count(old)
    if n != 1:
        print("FAIL[%s]: count=%d" % (tag, n)); sys.exit(1)
    txt = txt.replace(old, new)
    print("OK[%s]" % tag)

# ---------- ①头注块（CRLF 行尾与基座一致） ----------
HEADER = """// ============ v3x-m1v2 v2.1 版（2026-10-02 4i --b1 主线化实现轮：g_b1 默认值 0→1） ============
// 预注册（判据冻结正本，实现不得偏离）：
//   H:\\理论存档\\01-数学\\02-实验与数据\\预注册---b1主线化网格v6程序性确认轮-v1.0-20260921.md
// 基座 = v3_construction_nx_m1v2gwin-v1.0-20260921.cpp 全量逐字保留（=网格 v5 账 B1 臂引擎
//   m1v2gwin_v10.exe md5=4397ead7293c3d56197e9991c3c8c331 的源）；唯一改动=预注册 §二 冻结改动面
//   在本载体链上的落位（共两处）：
//   ①g_b1 默认值 0→1：B1 等额交付（gpipe deadline 改绑 tRepairEnd）升为引擎默认行为；
//     --b1 <0/1> 旗标与 merge 扫描跳过行自 gwin 原样继承零改动，--b1 0=旧行为回退开关保留；
//   ②本头注块（新增）。
// 主线行为定义（预注册 §二）：与网格 v5 账 B1 臂逐位同语义；[GPWIN] 行与 mech b1; 标记随默认开
//   成为默认输出（jsonl/账面读者须知变更，属设计内）。构造/修复/S 路线代码路径零触碰。
//   eng 字段不动（对拍要求，与 gwin 同）。版本号 v2.1 经升版前核查未被占用（2026-10-02 全档检索，
//   唯一在档引用=预注册本自身；撞版顺延纪律未触发）。
// 载体链披露：gwin v1.0 = m1v2anat v1.1（=m1v2 v1.0 全量逐字+纯日志插桩+EXIT127 修复件
//   closure_full 显式栈迭代）全量逐字+--b1 机制。主线化对象=「网格 v5 账 B1 臂的默认化」
//   （预注册 §二 原文），故基座取 v5 B1 臂引擎源；若按 m1v2-v1.0 文件直改将缺失 v1.1 修复件
//   （closure_full 递归版 g++16.1.0 -O2 下 EXIT127，1e5 档不可跑），不满足主线化语义。
// 判定（预注册 §四 冻结）：M-V1 对拍门（m4@1e5 s7+m5@1e5 s7+m3@1e3 s7 判定字段
//   pass/breaks0/breaks1/size/defects vs gwin --b1 1 逐位同；rot/时延不进门）
//   →M-V2 全网格 90 案例（65/90 零回退+m4@1e5 构造完整率 6/6+m5@1e5 6/6 全零+m3@1e3 Σ608 维持）
//   →M-V3 门控零漂移面（72 m≥4 中 66 例与 v5 逐位同，仅 m4@1e5 六例按设计改变）。
// 以下为 m1v2gwin v1.0 头注（基座原样）。 ============
""".replace("\n", "\r\n")
txt = HEADER + txt

# ---------- ②g_b1 默认值 0→1（唯一代码改动；旗标解析行自 gwin 原样继承零改动） ----------
rep("""static int g_b1 = 0;                   // [GWIN] --b1：B1 等额交付（gpipe deadline 改绑 tRepairEnd；默认 0=主线全同）""",
    """static int g_b1 = 1;                   // [M1V2 v2.1] --b1：B1 等额交付主线化（gpipe deadline 改绑 tRepairEnd；默认 1=预注册 §二 冻结；--b1 0=旧行为回退开关）""",
    "default-flip")

open(DST, "wb").write(txt.encode("utf-8"))
print("WROTE", DST, "bytes=", len(txt.encode("utf-8")))
