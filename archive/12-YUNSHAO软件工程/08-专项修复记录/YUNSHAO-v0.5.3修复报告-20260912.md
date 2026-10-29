# YUNSHAO 求解器 v0.5.3 修复报告（P0#1 试用重置 + 遗留清单核实关闭）

> 施工：2026-09-12 ZCode · 触发：知世"读桌面bug清单，解决然后发现更多问题，我要拿出去卖的"
> 交付：`桌面/YUNSHAO_v0.5.3_测试版.exe`（100,148,245 B，clean rebuild 09-12 01:51）+ 本报告 + 更新版 bug 清单 docx

---

## 一、核心修复：试用倒计时不递减/删档重置（你最怒的那个）

**根因（goldbach_gui.py LicenseManager.__init__）**：`_load()` 失败（文件被删、被改、HMAC 不符、DPAPI 解不开）一律 `return None` → `__init__` 把 None 当"首次运行"→ 重发 Trial3h。所以删/改 license.dat 反而每次白拿 3 小时——"永远还剩 3 小时"。

**修复（四层，全部带日期注释）**：
1. **三态加载** `_load2()`：`ok` / `missing`（真缺失）/ `corrupt`（损坏或被篡改）。
2. **corrupt = fail-closed**：绝不重发试用。状态栏明示"数据校验失败（疑似被篡改或损坏），试用不可恢复——请输入激活码激活"；激活成功即自愈覆盖。
3. **missing = 双锚恢复**：试用发放时同步写两处锚（`%APPDATA%/YS/.ys_anchor` 文件 + `HKCU\Software\YUNSHAO\TrialAnchor` 注册表，均 DPAPI 绑定）。license.dat 被删 → 从锚恢复**原倒计时**（不重置）；双锚也被删才发新试用（诚实下限，需同时清除三个 DPAPI 绑定存储）。
4. **时长钳制**：trial 记录 expire−start 超档位上限（即便攻击者提取 SIGKEY 重签超长试用）→ 启动时截断到上限并重签、留痕。

**附带加固**：`_save()` 原子写（临时文件+os.replace，防写半截损坏误伤）；许可事件留痕 `%APPDATA%/YS/license_event.log`（原 _load/_save 静默吞异常=出错无据可查）；激活成功清试用锚。

**验证**：沙盒行为测试 13/13 全过（`workspace/default/test_license_fix.py`，隔离 APPDATA、注册表已清理）——覆盖首次发放/删档恢复/篡改fail-closed/注册表兜底/三锚全删/超长钳制/activated 兼容七类场景。exe 冒烟：进程启动正常存活、无崩溃。

## 二、遗留清单核实（4 条里 3 条是过时条目，1 条已消解）

| 条目 | 核实结果 |
|---|---|
| P1-C 注入验签崩溃 | **v0.5.2 已修**。源码 goldbach_core.cpp inject_constants 全路径返回 ERR_VERIFY_FAIL/ERR_LOCK_FAIL（20260908 注释齐全）——清单过时，已标注 |
| P2-B predict ValueError | **v0.5.1 已修**（09-08，GUI 统一 ERR_NOT_ACTIVATED）——清单过时，已标注 |
| P2-C solver_opt.exe 未入 manifest | **已消解**：v0.5.2 起 solver_opt.exe 整体移除出包（spec"禁裸exe资源"），manifest 无此文件属正确状态；未来若恢复 exe fallback 必须先入 CHAIN_MANIFEST |
| 攻击手 4 项（07-27） | 全部核实关闭：①虫洞误伤=B5 已修✅ ②保密参数=白名单过滤已上线 + 本次 v0.5.3 加 ham_result 存储前剪枝兜底 ③PRESIARA 无残留 ④族归属占位行已消失 |

## 三、新发现问题（已登记清单【一b】，均非阻断）

1. **会话内倒计时静态**：状态栏许可文本只在启动/操作后刷新，试用期间不逐分钟递减（观感）。建议 60s 定时刷新 status_text。
2. **双激活轨并存**（设计债）：LicenseManager 本地 Ed25519 轨 + auth.pyd 服务器轨、两套缓存（YS/license.dat vs YS_LICENSE/license.json）。长期维护与安全审计负担，建议路线图合并为服务器轨单轨。

## 四、改动文件与构建

- `goldbach_gui.py`：LicenseManager 重写三态加载/锚/钳制/原子写/留痕 + `_on_ham_result` 保密键剪枝 + VERSION→v0.5.3（其他逻辑零改动）
- `YUNSHAO_v0.5.3_test.spec`：自 v0.5.2 spec 复制，仅改 name（v0.5.2 spec 已还原未动）
- 构建：`PyInstaller --clean`（强制重分析，保证 01:48 补丁入包；exe 01:51）

## 五、卖前提醒（诚实边界）

- 试用锚是"抬成本墙"：三 DPAPI 存储同删仍可重置（客户端方案的理论下限，代码原注释亦自认"真正防篡改是服务端验证"）。双锚+钳制+fail-closed 已显著高于 v0.5.2。
- bug 清单原件被占用（Word 打开中），更新版另存为：`云韶求解器bug问题-v0.5.3状态更新-20260912.docx`（原件 .bak-20260912 已备）。
- 上架前建议：真机首次运行→试用→激活→删档→复启 全链路人工过一遍（我已自动化等价场景，人工过一遍更稳）。

**关联**：v0.5.2 分槽修复（09-09）未动，本次在其之上叠加。老版本 v0.5.2 exe 仍在桌面未删。
