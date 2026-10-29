# YUNSHAO 哥德巴赫预测器 · GUI 需求规格（整理版）

> 来源：FEATURE_CHECKLIST.md（2026-07-04）+ TASK_GOLDBACH_2000.md + 早期 nine_grid.html/solar_ui.html 视觉风格
> 整理原则：剔除重复，不删改，越完善越好
> 知世裁决（04:32）：按以前的要求做，不看最终版（final_app.py 有问题），看早期版本
> 新增：超时继续跑按钮、CPU硬限制80%、2000位支持

---

## 一、界面框架

| 项目 | 说明 |
|------|------|
| ~~九宫格图片~~ | **知世06:00裁决：去掉，太难看了** |
| 窗口 | 启动即最大化，整个界面撑满屏幕，大字体大间距 |
| 选项卡 | 学生版 / 专业版 / 因数分解，三个独立tab |
| 输入框 | 支持2000位数字粘贴，monospace字体，Enter触发计算 |
| 状态栏 | 底部：版本号 + 许可状态 + CPU占用实时显示 |
| 视觉风格 | 深色主题（#000背景，#0a0a1a面板），YUNSHAO品牌，PRESIARA 2026水印 |

## 二、学生版

| 项目 | 说明 |
|------|------|
| 结果卡片 | N / p / q / 验证状态 / 位数 / 用时，卡片式布局 |
| 详情按钮 | 每行 [...] 按钮 → 弹出二级窗口显示完整数字串（2000位全展开） |
| 详情复制 | 二级窗口内复制按钮 |
| 底部复制 | N / p / q 三个独立复制按钮 |
| 验证标记 | ✅ PASS 大字（验证通过时） |
| 多余配对 | 最多显示4组，超出折叠 |
| 族标签 | 显示 Family A/B/C + mod24值，颜色区分（A绿/B蓝/C橙） |
| θ评分 | 每对显示 theta 置信度分数 |
| Λ比 | 每对显示 lambda 比值 |

## 三、专业版

| 项目 | 说明 |
|------|------|
| 复制按钮 | 所有数值行有 [C] 按钮或点击复制 |
| 显示项勾选 | checkbox 控制显示：p/q/offset/lambda/theta/verified/family/chi_range |
| 全选/全不选 | 一键切换所有显示项 |
| 滚动显示 | 鼠标滚轮滚动结果列表 |
| 多组分节 | 多组配对按 offset 排序分节显示 |
| 引擎标识 | 显示 engine=core_pyd 或 engine=goldbach2000 |
| 窗口信息 | 显示 window_used / workers / elapsed |
| 原始数据 | 可展开查看完整 p, q 数字串（不截断） |

## 四、因数分解

| 项目 | 说明 |
|------|------|
| 独立输入框 | 与预测器分离 |
| 结果文本区 | 显示完整 N / p / q / 验证 |
| 复制按钮 | 复制全部 / p单独复制 / q单独复制 |
| 友好提示 | 无法分解时给出提示（非报错） |
| 后端 | _gp.search_factor（旧.pyd内核） |

## 五、快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl++ | 放大字体 |
| Ctrl+- | 缩小字体 |
| Enter | 触发计算 |
| F1 | 快捷帮助窗口 |

## 六、许可系统

| 项目 | 说明 |
|------|------|
| 试用期 | Trial3h / Trial12h / Trial1d / Trial3d / Monthly |
| 到期状态 | EXPIRED 显示 |
| License路径 | 混淆存储 |

## 七、防破解

| 项目 | 说明 |
|------|------|
| .pyd核心 | 源码已删，二进制分发 |
| 反调试 | 被动检测，不阻塞 |
| 字符串加密 | 关键字符串加密 |

## 八、后端

| 项目 | 说明 |
|------|------|
| Goldbach预测 | 小N(≤300位)走 _gp.search_goldbach（旧.pyd），大N走 goldbach2000.predict |
| 因数分解 | _gp.search_factor（旧.pyd） |
| 后台线程 | 搜索在后台线程，不卡界面 |
| CPU限制 | import cpu_governor 自动激活，硬限80% |

## 九、新增功能（知世 04:32 裁决）

### 超时继续跑

| 项目 | 说明 |
|------|------|
| 超时行为 | 搜索超时（默认600s）后**不终止程序**，暂停搜索，显示已找到的结果 |
| 继续按钮 | 结果区显示"继续搜索"按钮，点击后从上次停止位置继续 |
| 状态保存 | 超时后保存：当前窗口win、已搜索偏移范围、已找到的pairs |
| 程序终止 | **只有关闭窗口才终止进程/清理资源**，超时不删程序 |
| 多轮累积 | 每轮继续搜索的结果累积显示，不清空之前的 |

### 2000位支持

| 项目 | 说明 |
|------|------|
| 输入 | 支持2000位十进制偶数粘贴 |
| 引擎切换 | ≤300位自动走旧.pyd，>300位自动走goldbach2000引擎 |
| 进度显示 | 大数搜索时显示当前窗口/已用时/已找到对数 |

---

## 十、变更日志（每次更新必回写此处，铁律）

> 知世 2026-07-27 03:45 指示：每次更新都得按这个软件规划文档写好加了什么功能、更新了什么，不要每次都忘。建立索引锁死。

### 2026-08-24 17:15 · 聆星 · 歌猜引擎激活缺陷修复+攻击手P0/P1加固（v0.5终版重打包）

- **缺陷（知世中午踩雷）：** 0817加固版GUI从未调用inject_constants——真实网络激活成功后歌猜仍报"未激活"。潜伏缺陷自0817打包时即存在，非level分级改动引入；当时36图回归用测试许可直调引擎、未走真实激活路径故未暴露。
- **修复主体：** goldbach_gui.py main() gate后新增_ys_activate_core()接线（常数blob+Ed25519签名XOR 0x5A混淆内置，注入失败弹窗退出fail-close）。keygen_v2.py+goldbach_private.enc重新定位成功（yunshao根目录），派生公钥b9c027b9与引擎嵌入精确匹配，签名验证通过。
- **攻击手全量审查（16:41）+修复：** P0×1 auth.pyd三处环境变量可覆盖公钥/激活/验证端点=授权体系整体可替换→三处os.environ.get删除改硬编码+auth.pyd重编（实测恶意env覆盖失效）；P1-A门禁模块缺失被跳过→main()补else fail-closed退出；P1-B/P2-A引擎import失败降级放行→return False拒绝启动。攻击手关闭确认：全部有效关闭、无新问题、verify_chain无回归。
- **验证：** 终版bundle 107个pyd无源码泄漏；12秒启动冒烟活；离线E2E真服务器激活student key→Ed25519验签→链互验干净→get_cached_level=student→引擎注入is_activated=True→51位大数predict complete 5对质数对全verified。修复后终版复验ALL PASS。
- **遗留跟进清单（今天不动内核，知世批准后做）：** P1-C注入验签失败=fail-fast进程崩溃无弹窗（需pyd侧返回错误码）；P2-B未注入predict实际抛ValueError与注释不符；P2-C solver_opt.exe未入CHAIN_MANIFEST；P2-D _on_ham_info无pro锁；P2-E旧token默认pro（有意设计）。
- **代码位置：** goldbach_gui.py（注释锚点"攻击手P0修复"/"攻击手P1-A修复"/"P1-B/P2-A修复"）；server_v2/auth.py（硬编码段）；交付物 dist_v05\YUNSHAO_v0.5_test.exe（97MB终版）。


### 2026-08-24 12:55 · 聆星 · level分级授权（学生版/专业版同EXE按密钥开功能）

- **需求（知世11:41-11:56锁定）：** 同一歌猜3tab EXE；学生版key=解锁歌猜两tab、哈密顿tab锁死；专业版key=歌猜+哈密顿全解锁。不走攻防（知世豁免：没额度）。
- **服务器：** license_server.py 加 level 字段(student/pro)：DB列+迁移(存量默认student)+create_keys(count,product,tier,level)+activate/verify响应与token带level+admin HMAC三级兼容格式(gen|count|product|tier|level|ts)。已部署华为云systemctl restart yunshao-license，验证GREEN。备份license_server.py.bak_20260824_level。
- **客户端：** auth.py verify/activate缓存写入token内level+新增get_cached_level()（本地Ed25519重验token签名+有效期，防手改缓存提权；旧token无level字段→pro兼容不降级）；goldbach_license_gate加get_level()；goldbach_gui三tab按level渲染（student→nb.tab(tab_ham,state=disabled)，Tk8.6冒烟过）+_on_ham_compute改level判定双保险fail-closed（替换旧is_activated，修复gate联网激活买家无license.dat会被误拦的暗雷）。
- **测试：** 服务器本机回环E2E三测全PASS——T1 student激活lv=student/T2手改缓存提权被拒/T3 pro激活lv=pro。测试密钥2枚已消耗即删。
- **打包v0.5：** build_chain_manifest回填歌猜manifest(11锚点)重编auth.pyd→YUNSHAO_v0.5_test.spec（加固版结构：引擎pyd化无裸exe资源+显式auth/goldbach_license_gate/goldbach2000/cpu_governor进包）→dist_v05\\YUNSHAO_v0.5_test.exe 97.4MB。bundle验证：10关键pyd在场+零.exe/.c/.cpp泄漏+solver_opt零残留；GUI冒烟激活对话框正常。**待知世过目定发布。**
- **收尾：** server_v2 auth.py/auth.pyd已恢复哈密顿manifest版(D03一致且带get_cached_level向后兼容)；备份auth.py.bak_20260824_level_hamilton_manifest。

### 2026-08-16 · 程序员+熵墟 · 优化版引擎改造+验证接口补丁

**背景：** 知世 2026-08-16 14:33/14:41 指示——歌猜1000位和哈密顿路径严格求解两个插件结合成一个可执行文件，按软件清单S01做优化版。

**改动（YUNSHAO_v0.4_test，5项）：**
1. **哈密顿引擎替换**：solver_opt.exe 替换为 hamilton_solver_cpp.exe（C++17严格引擎，163KB）。算法级联：结构判定→Warnsdorff→Pósa→谱系→回溯→虫洞兜底。
2. **新增 --verify 独立验证模式**：`hamilton_solver_cpp.exe --verify <in_edges.txt> <path.txt>`，输出 `VERIFY: PASS` / `VERIFY: FAIL (details: L=.. V=.. unique=.. breaks=..)`，退出码 0=PASS / 1=FAIL。独立验证器与求解器代码级分离（P0补丁，关卡F+R17⑦权力分立）。
3. **1000节点/1000位双层硬限**：哈密顿≤1000节点、歌猜≤1000位（GUI层+引擎层双层锁）。
4. **歌猜锁定C++引擎**：goldbach_core_cpp.pyd（大数）+ goldbach_predict.pyd（小N≤300位），Python fallback保留。
5. **G3假正勘误**：麒麟G3（g3_descend_prototype.py）自报"final_breaks=0/真边率1.0"全为假正（策略2 delta公式数学错误导致断边计数漂移，BA-200报出负数断边-10；熵墟亲验BA-100：自报0断边/独立验证17断边）。G3数据作废。

**验证：** 求解模式回归4/4 PASS（Petersen/Cycle-50/Grid-5x5 solved + BA-1001 error）；--verify 自测4/4（PASS/FAIL/空路径/空图）；求解→验证闭环 PASS。

**打包：** YUNSHAO_v0.4_test.exe（98.3MB）
**EXE：** C:\Users\Administrator\Desktop\YUNSHAO_v0.4_test.exe（SHA256=6785146DEE2E8568321226F35B534631E53BCFD8A6C7C9FA1F92EA82B1F171C0）

### 2026-07-30 21:01 · 程序员 · 修复大数"引擎未激活"（Session析构bug）

**背景：** 知世反馈数量一大就说"引擎未激活"。

**根因：** Session::~Session()调zeroize_constants()把g_activated清零。任何Session对象被GC回收后，整个引擎失活。常数是全局引擎状态，不是per-session的。

**修复（goldbach_core.cpp 1处）：** Session::~Session()删除zeroize_constants()调用。zeroize只在进程终止路径（abort/fatal/crash）执行。

**验证：** Session销毁后is_activated()=True；200位大数make_session→search 3.673秒出3对，verified全True

**重编译.pyd+重打包：** YUNSHAO_v0.1_test.exe，92.5MB，烟雾测试PASS

**EXE：** C:\Users\Administrator\Desktop\YUNSHAO_v0.1_test.exe（92.5MB，21:01）

---

### 2026-07-30 20:52 · 程序员 · UI反馈机制修复（状态栏+热梗+计时）

**背景：** 知世反馈切C++引擎后界面像死了一样——无状态栏更新、无热梗、无计时。原因：_tick_progress依赖self.session（goldbach2000会话对象），C++引擎session机制不同导致条件不满足。

**改动（goldbach_gui.py 4处）：**
1. _tick_progress重写：不依赖self.session，用self.searching+round_start计时。C++引擎用get_progress()轮询进度。超10秒轮播热梗。
2. _result_brief：删族标签，显示“完成·耗时Xs·找到N对”
3. _begin_search：小N状态文本显示“C++引擎”
4. _small_worker：C++太快时至少闪300ms“计算中”，不能无反馈

**打包：** YUNSHAO_v0.1_test.exe，92.5MB，烟雾测试PASS

**EXE：** C:\Users\Administrator\Desktop\YUNSHAO_v0.1_test.exe（92.5MB，20:52）

---

### 2026-07-30 20:42 · 程序员 · GUI切换C++引擎（goldbach_core_cpp）

**背景：** 知世反馈v0.1不能秒解，原因GUI还在调goldbach2000.pyd未切到goldbach_core_cpp.pyd。

**改动（goldbach_gui.py 5处）：**
1. 引擎导入：try import goldbach_core_cpp→inject_constants自动激活→fallback goldbach2000（_USE_CPP标志）
2. FAMILY_GROUP：改从_engine取（兼容两引擎）
3. _small_worker：_engine.predict()替代goldbach2000.predict()
4. _large_worker：_engine.make_session()+search()，C++ Session无verbose参数
5. session复用：GUI侧_session_N跟踪（C++ Session无N属性）

**验证：** 100位偶数0.528秒，engine='goldbach_core_cpp'，verified全True

**打包：** YUNSHAO_v0.1_test.exe，92.5MB，烟雾测试PASS

**EXE：** C:\Users\Administrator\Desktop\YUNSHAO_v0.1_test.exe（92.5MB，20:42）

---

### 2026-07-30 20:05 · 程序员 · 最终交付打包v0.1

**背景：** 知世指示版本号改回v0.1测试版。goldbach_gui.py L242 VERSION="v0.1 测试版"。

**改动：** spec name改YUNSHAO_v0.1_test，无代码修改。

**打包：** YUNSHAO_v0.3_test.spec（name=YUNSHAO_v0.1_test），92.5MB，烟雾测试PASS

**EXE：** C:\Users\Administrator\Desktop\YUNSHAO_v0.1_test.exe（92.5MB，20:05）

---

### 2026-07-30 14:09 · 程序员 · P0安全修补：界面数值清理（χ/θ/Λ/offset/族分类全部不显示）

**背景：** 知世指示：界面只给结果。χ/θ/Λ/offset/族分类χ范围全部不显示。

**改动（goldbach_gui.py 6处）：**
1. 学生版结果卡片：删除族标签（Family A/B/C mod24=xx）+χ范围显示
2. 学生版配对卡片：删除族标签+offset行，只保留p/q/已验证
3. 专业版显示项：从8项（p/q/offset/lambda/theta/verified/family/chi_range）缩减为3项（p/q/verified）
4. 专业版渲染：删除family/chi_range/offset/lambda行，只渲染p/q/verified
5. 报告导出：删除χ范围+12族统计分布+offset行，配对明细只含p/q/验证状态
6. 欢迎窗口+F1帮助："12族自动分类+置信度评分"改为"素数对预测+验证"
7. 头部标题："12族分类·置信度评分"改为"素数对预测+验证"

**打包：** YUNSHAO_v0.3_test.spec，92.5MB，烟雾测试PASS

**EXE：** C:\Users\Administrator\Desktop\YUNSHAO_v0.3_test.exe（92.5MB，14:09）

---

### 2026-07-30 09:20 · 程序员 · 最终打包v0.3（全部改动一次打完）

**背景：** goldbach_gui.py已包含本轮全部改动：启动欢迎窗口（300ms弹出）+哈密顿专业版门控+Ctrl+A全选+清空按钮+120条网络热梗彩蛋（SEARCH_MEMES L247，_tick_progress超10秒每5秒轮播）+窗口标题v0.3+secrecy_filter补全+hamilton_solver常数隐藏。

**改动：** 无代码修改（GUI已由上游更新），仅重新打包。

**打包：** YUNSHAO_v0.3_test.spec，92.5MB，烟雾测试PASS（GUI进程10秒存活）

**EXE：** C:\Users\Administrator\Desktop\YUNSHAO_v0.3_test.exe（92.5MB，09:20）

---

### 2026-07-30 08:45 · 程序员 · 重新打包v0.3（哈密顿专业版门控）

**背景：** goldbach_gui.py 08:44更新：_on_ham_compute()加许可门控（未激活→状态栏闪“哈密顿路径求解需要专业版以上许可，请先激活”→return）；欢迎窗口+F1帮助哈密顿标题改“第三选项卡·需专业版以上”。

**改动：** 无代码修改（GUI已由上游更新），仅重新打包。

**打包：** YUNSHAO_v0.3_test.spec，92.5MB，烟雾测试PASS（GUI进程10秒存活）

**EXE：** C:\Users\Administrator\Desktop\YUNSHAO_v0.3_test.exe（92.5MB，08:45）

---

### 2026-07-30 08:38 · 程序员 · 重新打包v0.3（新增启动欢迎窗口）

**背景：** goldbach_gui.py 08:38更新：新增_show_welcome()方法，启动300ms后自动弹出欢迎窗口（功能表：哥德巴赫预测+哈密顿路径+快捷键，居中显示，“开始使用”按钮关闭，“查看详细帮助”跳转F1）。

**改动：** 无代码修改（GUI已由上游更新），仅重新打包。

**打包：** YUNSHAO_v0.3_test.spec，92.5MB，烟雾测试PASS（GUI进程10秒存活，欢迎窗口300ms弹出）

**EXE：** C:\Users\Administrator\Desktop\YUNSHAO_v0.3_test.exe（92.5MB，08:38）

---

### 2026-07-30 08:31 · 程序员 · 攻击手验收P0修补+重新打包

**背景：** 攻击手验收不通过P0×1+P1×2。hamilton_solver.pyd常数公开导出（ALPHA/ETA/KAPPA/LAMBDA_C/C_VIRT/C_VIRT_OLD全可读，solve_wormhole/predict_virt/classify_structure/v_dependent_p公开可调用）。

**P0修补（hamilton_solver.py→重编译.pyd）：**
- 常数改_前缀：_ALPHA/_ETA/_KAPPA/_LAMBDA_C/_C_VIRT/_C_VIRT_OLD
- 内部函数改_前缀：_solve_wormhole/_predict_virt/_classify_structure/_v_dependent_p
- 内部调用点同步更新（4处）
- GUI调用点同步更新（goldbach_gui.py L1273: solve_wormhole→_solve_wormhole）
- Cython重编译+验证：dir(hamilton_solver)无公开常数/内部函数，公开API（solve/generate_graph/verify_path等）完好

**P1-1修补（secrecy_filter.py→重编译.pyd）：**
- SECRECY_BLOCKLIST补：wormhole/虫洞/虚拟边/virt_edge/ANCHOR/anchor/C_VIRT/LAMBDA

**P1-2修补（goldbach_gui.py）：**
- VERSION = "v0.3 测试版"（原v0.1）

**重新打包：** YUNSHAO_v0.3_test.spec，92.5MB，烟雾测试PASS，bundle 10/10 .pyd全在

**代码位置：** hamilton_solver.py.bak_20260730 / secrecy_filter.py.bak_20260730 / goldbach_gui.py.bak_20260730

---

### 2026-07-30 08:12 · 程序员 · YUNSHAO v0.3打包（新增goldbach_core_cpp引擎+GUI 08:03更新）

**背景：** goldbach_gui.py 08:03更新（Ctrl+A全选+清空按钮+F1帮助重写）；goldbach_core_cpp.pyd生产版已编译（C++哥德巴赫预测核心，OpenSSL+GMP全静态）。知世尚未签名激活，本次打包用测试旁路版（-DYS_TEST_BYPASS_ACTIVATION）。

**改动：**
1. 新建YUNSHAO_v0.3_test.spec（基于YunShao_Ed25519_full.spec，+goldbach_core_cpp.pyd+yunshao_client.pyd）
2. goldbach_core_cpp.cp314-win_amd64.pyd加入datas+hiddenimports（新C++引擎，测试旁路版1.2MB）
3. yunshao_client.cp314-win_amd64.pyd加入datas+hiddenimports（GUI第50行import，旧spec遗漏）
4. GUI默认走goldbach2000（稳定），goldbach_core_cpp作为可选引擎（后续知世签名后切换）

**Bundle验证：** 210个.pyd，10/10自研核心.pyd全在（goldbach_predict/goldbach2000/goldbach_core_cpp/hamilton_core/hamilton_solver/yunshao_anticode/yunshao_crypto/yunshao_client/sentinel/secrecy_filter），无核心算法.py泄露。cpu_governor.py是运行时工具（非核心算法）。

**烟雾测试：** PASS（GUI进程启动8秒存活）

**EXE：** C:\Users\Administrator\Desktop\YUNSHAO_v0.3_test.exe（92.4MB，旧版基准30.3MB→新版≥旧版✓）

**代码位置：** YUNSHAO_v0.3_test.spec / goldbach_gui.py.bak_20260730（备份）

**遗留：** 知世签名后换生产版goldbach_core_cpp.pyd（去-DYS_TEST_BYPASS_ACTIVATION，加-DYS_PRODUCTION+OpenSSL静态链接）重打包。

---

### 2026-07-28 07:52 · 程序员 · Ed25519加密方案·第一阶段（加密模块+keygen升级）

**决策链：** Ed25519非对称+功能裁剪替换HMAC对称。理由：HMAC密钥嵌入EXE可提取→自签激活码（攻击手P0-1证明HMAC是后门）。否决：HMAC-SHA256对称方案。依赖：[SOUL.md铁律12, AGENTS.md R13]。

**交付3文件（均在 C:\Users\Administrator\AppData\Local\hermes\workspace\yunshao\）：**
1. **yunshao_crypto.py**（新建·核心加密模块）：ed25519_verify(公钥硬编码占位待回填) / derive_aes_key(HKDF-SHA256,salt=YUNSHAO-AES-V1) / aes_decrypt(AES-256-GCM) / hardware_fingerprint(复用GUI逻辑) / verify_license(格式→Ed25519签名→hwfp→有效期→时钟回拨→吊销占位) / check_revocation(占位not_revoked) / monotonic_counter(%APPDATA%/YS/counter.dat防回拨)。
2. **keygen_v2.py**（新建·Ed25519签名keygen）：解密goldbach_private.enc(PBKDF2-SHA3-512/600k+SHAKE-256+HMAC,同goldbach_cpp.cpp)→seed=SHA3-512(p||q)[:32]→Ed25519→签YS2码→zeroize明文。支持--gen-enc/--pubkey/--fingerprint。
3. **test_crypto.py**（新建）：密钥派生/.enc round-trip/正确码/篡改/错hwfp/过期/占位公钥，全链路测试。

**激活码格式：** YS2-{tier}-{ts}-{hwfp}-{ed_sig_b64url}；签名消息 GOLDBACH|v0.1|{tier}|{expiry_ts}|{hwfp}；有效期测试版1年(365天)。

**测试结果：** 12 PASS / 0 FAIL（测试用100位素数，生产用1万位；密钥派生路径相同）。

**⚠️ 阻断项（需知世/主agent裁决）：** passphrase文件 C:\SoulGuard-architect\key\goldbach_passphrase.txt **解不开**现有 goldbach_private.enc（HMAC校验失败，已验证7种编码变体+round-trip证明解密实现正确）。即现有.enc与口令不匹配。需：①核对正确口令，或②用 keygen_v2.py --gen-enc 重新生成1万位(p,q)落盘。回填公钥依赖此步。

**公钥状态：** yunshao_crypto.py 的 _VERIFY_PUBKEY_HEX 为占位符(全零)，待(p,q)确定后回填。测试临时公钥 d040ae82...（100位种子，勿用于生产）。

**核心算法内核：** 未动（R_TABLE/Λ比/θ(p)/新常数零改动）。secrecy_filter.py 未动。

**代码位置：** yunshao_crypto.py / keygen_v2.py / test_crypto.py（均含文末【修改记录】双标记，铁律8）。

**待第二阶段：** 回填公钥→GUI集成(替换goldbach_gui.py 308-464行HMAC段)→.pyd化→重打包→攻击手验收。

---

### 2026-07-28 00:19 · 熵墟 · 代码审查报告12漏洞修复（许可/加密/求解器/过滤/指纹）

**背景：** 知世23:38指示"修一下"代码审查报告（12个漏洞：4严重+4高危+4中危）。程序员修源码→Cython重编译.pyd→PyInstaller重打包→攻击手验收通过。

**修复清单（代码位置+为什么）：**
- **#1 许可循环论证**（goldbach_gui.py is_activated）：activate()存原始key串，is_activated()改取存储key直接verify，不再make_license_key重构（原"自己签自己验"可本地一键绕过）。
- **#2 密钥明文**（goldbach_gui.py LicenseManager）：license.dat改DPAPI加密（DPAPI1前缀+CryptProtectData绑定当前用户），fallback XOR。注：SIGKEY对称密钥客户端必可提取，DPAPI=纯客户端最优解，真正方案是服务端。
- **#3 BFS桥接visited漏洞**（hamilton_core.py _bfs_bridge_norevisit）：入口加 if v in visited: return None，防目标节点已访问时返回重复路径（BA图假阴性）。
- **#4 Ed25519私钥明文**（yunshao_anticode.py）：BestAvailableEncryption加密私钥，口令=DPAPI保护的随机32字节。
- **#5 nonce竞态+截断**（yunshao_anticode.py）：改{nonce:timestamp}字典+os.replace原子写+按ts排序截断5000，旧list格式兼容。
- **#6 保密过滤误伤**（secrecy_filter.py）：黑名单精确化（_method_/phase2a/structure_等内部字段形式），filter_text从整行替换改为只替换关键词本身。普通词method/structure/phase/alpha不再误伤。
- **#7 节点上限仅GUI层**（hamilton_solver.py + hamilton_core.py 两solve()入口）：都加 if n>1000: raise ValueError，防API绕过GUI限制。
- **#8 _descend空路径崩溃**（hamilton_core.py）：入口加 if not path 防御返回空路径+零值metrics。
- **#9 wmic弃用**（goldbach_gui.py + yunshao_anticode.py 两处hardware_fingerprint）：优先Get-CimInstance(PowerShell)，wmic作fallback（Win11 24H2弃用wmic）。
- **#10 性能**（hamilton_core.py _warnsdorff）：不改算法，Cython编译.pyd即解决，加注释标明。
- **#11 时序侧信道**（goldbach_gui.py verify_license_key）：指纹比较改 hmac.compare_digest 常量时间。
- **#12 广捕吞MemoryError**（goldbach_gui.py _ham_path_metrics）：改捕具体异常元组，MemoryError/KeyboardInterrupt/SystemExit不捕上抛。
- **额外修复 build_crypto.py 语法bug**：第16行DERIVED_KEY缺hashlib.sha256(开头（之前被脱敏写坏），已修；并恢复SIGKEY=_SIGN_SALT.encode()（build_crypto误改为_get_sign_salt()但未插入该函数导致EXE启动NameError）。

**打包：** hamilton_core/hamilton_solver/yunshao_anticode 三个.pyd重编译；YUNSHAO云韶求解器.spec重打包→求解器.exe（94MB）部署桌面。bundle验证5个核心模块全.pyd零源码泄露。

**攻击手验收（铁律23）：** 12条全修好，核心算法零误动（R_TABLE/α/η/θ常数原样），EXE烟雾测试启动8秒不崩。残留N1-N5均P2/P3（同用户文件可写信任边界内/精确化固有tradeoff），不阻断交付。建议下轮补N3（子求解器solve_warnsdorff/posa等加统一上限）+N2（内核字段命名规范）。

**铁律合规：** 核心算法内核（_warnsdorff/_descend降维/R_TABLE/Λ比/θ(p)/新常数）一字未动；加密三件套（Cython.pyd+HMAC激活+六档时长）保持。

### 2026-07-27 20:16 · 熵墟 · 哈密顿Bug修复（降维禁重复节点+EXE重打包+报告不泄常数）

**背景：** 知世指示晚上修哈密顿Bug，三项任务。

**① extract_hamiltonian_from_backbone 降维禁止重复节点：**
- 研究版 `H:\OpenClaw\workspace\yunshao_hamilton_v3_2.py`：extract_hamiltonian_from_backbone 返回前新增顺序去重终检（seen_final 集合），从结构上杜绝重复节点进入降维路径，深度同步修正。
- 生产版 `hamilton_core.py` 的 `_descend`（真正打进EXE的降维函数）：在 visited 集合去重基础上，返回前再加一道顺序去重双保险（知世指示：降维禁止重复节点）。

**② EXE重打包（旧版验证没有重复检查）：**
- hamilton_core.py 重新 Cython 编译→hamilton_core.cp314-win_amd64.pyd（20:15，135KB）。
- 用 YUNSHAO云韶求解器.spec 重新 PyInstaller 打包→求解器.exe（94MB），已部署到桌面 YUNSHAO云韶求解器.exe。
- 实测验证：8种图（BA100/500/1000、Grid20、ER100、K50、Wheel50、Cycle200）降维后实际重复节点=0，is_strict_hamiltonian 校验 unique_nodes==path_len。
- 生产事故红线核验：EXE bundle 内 5 个核心模块（hamilton_core/hamilton_solver/goldbach_predict/goldbach2000/yunshao_anticode）全为 .pyd，源码标记（def _descend/_warnsdorff/solve）count=0，零泄露。
- EXE 启动烟雾测试：进程存活8s不崩。

**③ 报告不泄露内部常数：**
- 研究版 report() 去掉 `α={ALPHA}` 显示（辐射行+辐射参数段两处），亏损率只给实测值不给内部常数 α。生产版报告本就不含内部常数（secrecy_filter 黑名单拦截）。

**代码位置：** yunshao_hamilton_v3_2.py extract_hamiltonian_from_backbone/report；hamilton_core.py _descend；YUNSHAO云韶求解器.spec

**验证：** 8图重复=0；EXE零源码泄露；EXE启动正常；研究版语法检查通过。

### 2026-07-27 08:14 · 聆星 · 方案A迁移+攻防对打修复（P0×4/P1×6/P2×3）

**背景：** 知世07:28指出合并EXE时丢了独立版功能（自定义输入/14种预设图/图信息按钮）。方案A：把hamilton_core接进合并版，加回3项功能。攻防对打skill（攻击手+程序员并行）发现4个P0/6个P1/3个P2。

**方案A迁移（搬回3项功能）：**
- 自定义邻接表输入（每行u v，hamilton_core求解）
- 14种预设图下拉（BA/ER/Grid/完全图/环/轮图/正则图/小世界）
- 图信息按钮（不求解直接看结构）
- 输入模式切换：随机图(n/p/seed→hamilton_solver)/预设图/自定义图(→hamilton_core)
- 8个预设图生成函数从独立版一字搬入

**攻防对打修复（攻击手+程序员实测发现）：**
- V1[P0]节点ID重映射：非连续ID(1-100/负数)→路径重复、指标撒谎。求解前重映射0..n-1，输出反映射
- P0-1布局重叠：自定义输入框和结果区同row=2遮挡→结果区改row=3
- P0-2权重错行：rowconfigure(1)→rowconfigure(3)
- V2[P0]畸形输入：GUI层拦截空边/��数/非整数
- V3/P2-1报告降级：预设/自定义模式补p/seed/avg_deg字段
- P1-1图信息用错生成器：随机模式改用hamilton_solver.generate_graph（和求解同一张图）
- P1-2负数节点拒绝：_parse_custom_edges加u<0/v<0检查
- P1-3不连通图提示：GUI层BFS算连通分量，>1时flash提示
- P1-4吞错提示：计数无效行，求解前提示"X行已跳过"
- P2-2删除HAM_PRESET_GRAPHS死条目

**代码位置：** goldbach_gui.py _build_hamilton_tab/_on_ham_mode_change/_parse_custom_edges/_on_ham_info/_on_ham_compute/_ham_worker_edges + HAM_PRESET_GRAPHS + 8个生成函数

**验证：** V1实测节点1-5环路径无重复real=100%；负数/非整数正确拒绝；14种预设图全100%；GUI渲染正常

**EXE：** dist\YUNSHAO云韶求解器.exe（94MB，08:15），已上桌面

---

### 2026-07-27 07:02 · 攻击手验收发现4项（非阻断，待修）

**发现1·虫洞误伤（高）：** secrecy_filter黑名单含"虫洞"/"wormhole"，但03:40变更日志批准wormhole_count对外。复制报告/二级详情经filter_text后"虫洞数"变"[已隐藏]数"——报告破损。主卡片直连Label未过滤所以界面正常，复制/详情才坏。
**发现2·保密参数无兜底（中）：** phase/method/structure/V_virt_predicted不在secrecy_filter黑名单里，靠手工不渲染。solve()返回dict实测带这些键且整体存入self.ham_result，未来新代码一旦格式化整个dict即泄露。
**发现3·源码残留（低）：** docstring(L4)/HMAC盐(L211)/XOR键(L340)仍含PRESIARA/云韶研究院。HMAC盐/XOR键是功能密钥不能删，docstring可清。客户可见面无影响但解包可见。
**发现4·哥德巴赫报告空壳行（低）：** filter_report_data剥离family/chi_range后报告仍打印"12族归属: Family ? (mod24=0)"占位行。

---

### 2026-07-27 07:01 · 聆星 · 哈密顿路径不显示BUG修复（生产级）

**背景：** 知世06:50反馈哈密顿tab求解后一个结果都看不到。攻击手只查代码存在没实际渲染，我反复验证数据流说"没问题"，实际GUI渲染层有致命bug。

**根因：** `_ham_path_metrics` 里 `for node in adj` 遍历的是list的元素（邻居集合set），不是索引。`adj[set]` → TypeError → 被 `except Exception: return {}` 静默吞掉 → 整个metrics返回空dict → 路径/度分布/叶节点全部不显示。

**修法：** 4处 `for node in adj` → `for node in range(n)`，`for start_node in adj` → `for start_node in range(n)`。同时把 `except Exception: return {}` 改为打印traceback不再静默吞错。

**验证：** GUI渲染测试确认路径100行出来（每行10节点），metrics 16个key全有。

**代码位置：** goldbach_gui.py L854/861/875/876/893/894（`for node in range(n)`）+ L896（except打印traceback）

**教训：** ①静默吞错（except: return {}）是GUI调试大敌，必须打印traceback ②验证必须到GUI渲染层，不是数据流跑通就算 ③攻击手验收必须实际渲染，不是grep代码存在

---

### 2026-07-27 06:14 · 聆星 · numpy无控制台崩溃修复

**根因：** PyInstaller console=False时sys.stdout/stderr=None，numpy导入访问sys.stdout.encoding崩溃。
**修法：** 所有import前加 `if sys.stdout is None: sys.stdout = io.StringIO()`
**代码位置：** goldbach_gui.py L29-35

---

### 2026-07-27 05:50 · 聆星 · 生产事故修复（核心算法.pyd化）+ 保密参数收紧

**背景：** 知世05:36发现生产事故——hamilton_solver.py/goldbach2000.py/yunshao_anticode.py三个核心算法以明文.py源码打进EXE，客户解包即裸奔，违反铁律11/R13。知世05:37指示写进灵魂。另：知世05:45指示——为证明算法有效性，暴露虫洞/虚拟边数量，但藏起能反推公司参数与整体思想的字段。

**改动1·核心算法全部.pyd化（生产事故修复）：**
- Cython编译 hamilton_solver/goldbach2000/yunshao_anticode 三个.py → .pyd（264KB/181KB/129KB）
- spec改：三个.py从datas删除，.pyd进binaries
- bundle验证：三个模块全是.pyd，datas零.py源码泄露

**改动2·numpy打包修复：**
- 根因：PyInstaller只收集numpy的.py不收集.pyd/.dll → EXE里import失败（提示"缺少numpy"）
- 修法：spec加 collect_all('numpy') 强制收集全部二进制+数据

**改动3·保密参数收紧（知世05:45指示）：**
- 从客户界面/报告/CSV拿掉：phase（级联策略）/method（算法名）/structure（结构分类）/V_virt_predicted/actual/err_pct（预测模型）/phase2a_time_s
- 保留（证明有效性且反推不回思想）：virt_edges虚拟边数量/real_rate/coverage/expansion/path_len/度统计/完整路径
- 原则：虫洞虚拟边的"数量"暴露（证明有效性），"怎么预测/怎么造/在哪造/用什么算法造"全藏

**改动4·版本号v0.1测试版 + 路径分段（每行10节点）+ 合并为单一EXE**

**代码位置：**
- YUNSHAO云韶求解器.spec（三个.pyd进binaries + collect_all numpy）
- goldbach_gui.py：_render_hamilton诊断卡片 / _build_hamilton_report_text / _export_hamilton_csv / _on_ham_result状态栏

**EXE：** dist\YUNSHAO云韶求解器.exe（94MB，05:50，含numpy+三.pyd+保密收紧），已上桌面

**加密机制现状（铁律11三件套）：** ①Cython.pyd✅（4核心模块）②HMAC-SHA256激活✅ ③六档时长✅

**灵魂已写入：** SOUL.md新增「生产事故红线」段（打包前必查清单5条）

---

### 2026-07-27 05:15 · 熵墟 · 两级报告结构 + 哈密顿BA-1000全解修复

**背景：** 知世 04:46 指示——跑完能点开每一项数值/给总数值，复制成报告可直接提取所有数字，不用一个个填；一级界面分开填，点详细从一级跳二级看所有数字。哥德巴赫和哈密顿都要。另：BA-1000之前只99.5%真边，知世 04:28 指示补上。

**改动1·哈密顿核心算法全解修复（hamilton_core.py → 重编译.pyd）：**
- 根因：`_descend` 桥搜索只到2-hop，BA-1000有5条虫洞BFS距离4-5，桥接不上→留假边
- 修法：新增 `_bfs_bridge`（BFS最短路桥，max_depth=6），替换原2-hop/3-hop硬编码桥接
- 结果：BA-1000 real=100.0% failed=0（膨胀率1.116→1.126，多插128桥节点换满真边）
- 已重编译 hamilton_core.cp314-win_amd64.pyd，验证加载的是编译版

**改动2·哥德巴赫GUI两级报告（goldbach_gui.py）：**
- 学生版（一级）新增「📋 查看详细报告」按钮 → `_goto_pro_report` 自动切专业版tab并渲染全部数据
- 哈密顿tab新增「📊 详细数据报告」按钮 → `_show_hamilton_detail` 弹二级Toplevel展示所有数字+「📋 一键复制全部」

**改动3·哈密顿独立版两级报告（hamilton_gui.py）：**
- 一级：求解后只显示6个核心总数值摘要（`_summary_text`）
- 「📊 详细数据报告」→ 二级Toplevel全部数字（含完整路径/求解诊断/插入失败虫洞明细，`_full_report_text`）
- 「📋 一键复制报告」→ 完整报告进剪贴板
- 缓存 last_result/last_elapsed 供二级报告用

**代码位置：**
- hamilton_core.py：_bfs_bridge（新增）/ _descend（桥接逻辑替换）
- goldbach_gui.py：_goto_pro_report / _show_hamilton_detail / 学生版+哈密顿tab按钮
- hamilton_gui.py：_summary_text / _full_report_text / _show_detail_report / _copy_report / _copy_text

**EXE：** dist\YunShao_Hamilton_v1000.exe（12.1MB，05:07打包，含新.pyd+两级报告）

⚠️ 遗留：哈密顿独立版一级目前是纯文本摘要，知世要求"分开填"（每数值独立复制+点开详情），待改卡片式。哥德巴赫EXE待重新打包。

---

### 2026-07-27 03:40 · 熵墟 · 报告数值保密收紧 + 哈密顿报告延伸

**背景：** 知世指示——报告数值只给现有数学体系研究需要的，不能让客户反推我们的公式。给太多反而有问题。

**改动1·哥德巴赫报告白名单收紧（REPORT_WHITELIST）：**
- 拿掉 `family`（A/B/C族标签）——能反推12族分组规则
- 拿掉 `chi_range`——能反推群结构
- 不给 `theta`/`lambda`——能反推θ(p)公式和Λ阈值
- 保留：N / digits / engine / elapsed / total_found / pairs(p,q,offset,verified)
- ⚠️ 注：§二学生版的"族标签/θ评分/Λ比"和§三专业版的"lambda/theta/family/chi_range"显示项，**对外报告不再输出**（界面内部展示逻辑另议，对外输出/复制/CSV一律过滤）

**改动2·哈密顿报告延伸标准图论指标（_ham_path_metrics + _build_hamilton_report_text）：**
- 原有：真边率/覆盖率/膨胀率/路径长度
- 新增：连通分量数 / 最大度 / 最小度 / 叶节点数+占比 / Hub节点数 / 虫洞数 / 度分布直方图
- 全部是标准图论指标，不涉及云韶公式

**反推检验（已确认安全）：**
- 客户拿不到：α=1/8、η=7/8、κ=1/32、θ(p)公式、Λ阈值、12族分组规则、G²升维机制、辐射序、descend算法、终极公式Θ(N)
- 客户能拿到的度分布/虫洞数/膨胀率均为单一数值或公开图论性质，无法反推公式

**代码位置：** `C:\Users\Administrator\AppData\Local\hermes\workspace\yunshao\goldbach_gui.py`
- 白名单：第149-156行附近 REPORT_WHITELIST / REPORT_PAIR_WHITELIST
- 哈密顿指标：_ham_path_metrics（约783行）
- 哈密顿报告：_build_hamilton_report_text（约939行）

---

## 十一、更新回写铁律（写死，每次更新必遵守）

> 知世 2026-07-27 03:45 指示锁死

1. **任何对YUNSHAO软件的功能新增/修改/删除，必须同步回写本文档§十变更日志。**
2. 回写内容：日期+改动人+改了什么+为什么改+代码位置。
3. 不许只改代码不改文档。改代码不回写文档=失职。
4. 本文档是软件唯一权威规划文档，FEATURE_CHECKLIST.md是功能勾选项，两者配套。
5. 每次启动软件相关任务，先读本文档§十看最近改了什么，再动手。

---

*整理：熵墟 · 2026-07-24 · 基于知世原始要求，未删改任何功能项，仅剔除重复*
*变更日志+回写铁律：熵墟 · 2026-07-27 03:45 · 知世指示*

---

## 十二、BUG索引（知世 2026-07-27 07:02 指示建立，所有bug如实记录+索引）

> 铁律：发现bug必须如实记录在此，不许隐瞒、不许淡化。修了的标✅，未修的标⚠️。

| # | 日期 | 严重级 | 状态 | 摘要 | 根因 | 修法 | 代码位置 |
|---|------|--------|------|------|------|------|----------|
| B1 | 07-27 05:36 | 🔴生产事故 | ✅已修 | 核心算法明文.py打进EXE，客户解包即裸奔 | spec把hamilton_solver/goldbach2000/yunshao_anticode当.py放datas | Cython编译三个.pyd，spec改binaries | YUNSHAO云韶求解器.spec |
| B2 | 07-27 05:33 | 🔴功能崩溃 | ✅已修 | EXE里numpy导入失败（"缺少numpy"） | PyInstaller只收集numpy的.py不收集.pyd/.dll | spec加collect_all('numpy') | YUNSHAO云韶求解器.spec |
| B3 | 07-27 06:14 | 🔴功能崩溃 | ✅已修 | 窗口程序启动后numpy导入崩（NoneType no attribute encoding） | console=False时sys.stdout=None，numpy访问sys.stdout.encoding | import前加sys.stdout/stderr兜底 | goldbach_gui.py L29-35 |
| B4 | 07-27 07:01 | 🔴功能丢失 | ✅已修 | 哈密顿tab求解后路径/度分布/叶节点全部不显示 | adj是list但for node in adj遍历元素(set)不是索引，TypeError被except: return{}静默吞掉 | 4处改for node in range(n)，except打印traceback | goldbach_gui.py L854/861/875/876/893/894/896 |
| B5 | 07-27 07:02 | 🟡高 | ✅已修 | 复制报告里"虫洞数"被过滤成"[已隐藏]数" | secrecy_filter黑名单含"虫洞"但已批准对外 | 移除"虫洞"/"wormhole"，改只拦内部机制术语 | secrecy_filter.py |
| B6 | 07-27 07:02 | 🟡中 | ✅已修 | 保密参数无兜底+filter_text只替换key不替换value | 黑名单不覆盖+正则只替换关键词本身 | 补7字段进黑名单+filter_text改整行替换 | secrecy_filter.py |
| B7 | 07-27 07:02 | 🟢低 | ✅已修 | 源码docstring含PRESIARA/云韶研究院 | 早期残留 | docstring已清（功能密钥保留） | goldbach_gui.py L4 |
| B8 | 07-27 07:02 | 🟢低 | ✅已修 | 报告"12族归属: Family ?"空壳行+12族统计"(Family ?)" | FAMILY_GROUP只映射偶数mod24，素数必奇数永远'?' | 删除空壳行+统计段去掉"(Family ?)"后缀 | goldbach_gui.py _build_report_text |
| B9 | 07-27 08:13 | 🔴P0 | ⚠️部分修 | 非连续节点ID→路径重复、指标撒谎 | hamilton_core对非连续ID路径重复 | GUI层重映射修了ID翻译，但BA图路径仍重复（内核_descend+BFS桥接问题）——待知世裁决 | goldbach_gui.py _ham_worker_edges + hamilton_core内核 |
| B10 | 07-27 08:12 | 🔴P0 | ✅已修 | 自定义模式输入框遮住结果区，用户看不到求解结果 | custom_frame和wrap同grid row=2重叠 | 结果区改row=3+rowconfigure(3) | goldbach_gui.py _build_hamilton_tab |
| B11 | 07-27 08:13 | 🟡P1 | ✅已修 | 图信息随机模式用_er_graph，和求解的图不是同一张 | RNG不同生成不同的图 | 改用hamilton_solver.generate_graph | goldbach_gui.py _on_ham_info |
| B12 | 07-27 08:13 | 🟡P1 | ✅已修 | 自定义输入负数节点/无效行静默吞掉无提示 | int("-1")通过+except pass | 拒绝负数+计数无效行+不连通BFS提示 | goldbach_gui.py _parse_custom_edges/_on_ham_compute |
| B13 | 07-27 08:14 | 🟢P2 | ✅已修 | 预设/自定义报告p/seed/avg_deg显示问号 | _ham_worker_edges只填了5个字段 | result补p/seed/avg_deg | goldbach_gui.py _ham_worker_edges |
| B14 | 08-26发现/09-12修复 | 🔴P0商用 | ✅已修 | 试用倒计时不递减、删/改license.dat即重置3h试用（知世："一直显示还剩3小时"） | LicenseManager把加载失败（删档/篡改/HMAC不符/DPAPI解不开）全当首次运行重发试用 | 三态加载：corrupt=fail-closed不重发；missing=双锚（.ys_anchor+注册表，DPAPI）恢复原倒计时；真首次才发放；时长钳制；原子写+事件留痕；13项沙盒测试全过 | goldbach_gui.py LicenseManager（v0.5.3） |
| B15 | 0727登记(B9关联)/0915修复 | 🔴P0 | ✅指标诚实化已修 | BA图哈密顿结果把带重复节点的walk标"严格解"（指标撒谎） | _run_solver_opt的solved判据=full_cover+all_real，不含节点唯一性 | solved补unique==n且path_len==n判据；result增unique_nodes/duplicates；状态栏改"辅助绕行（走行）·重复节点=X"；walk重复=引擎本质非缺陷，如实标注 | goldbach_gui.py _run_solver_opt/_on_ham_result（v0.5.6） |
| B16 | 0912-0916投诉/0916修复 | 🔴P0商用 | ✅已修(v0.5.7) | 未激活也能用歌猜求解（知世投诉，桌面BUG docx顶部）——两层根因：①goldbach2000降级引擎无is_activated+hasattr门禁fail-open（0825"已封死"声明实为未封）；②双激活轨脱同步：auth轨放行→_ys_activate_core无条件注入引擎→可求解，LicenseManager本地轨no_license→状态栏"未激活"，显示与执行不一致 | _ys_activate_core无条件注入+两轨无一致性检查 | 统一许可门禁_license_allows_solve（七分支单测7/7）+三worker双因子（许可轨∧引擎注入fail-closed）+哈密顿入口许可轨锁+降级留痕engine_event.log；修复前E2E复现投诉、修复后E2E拦截；不动注入接线（08-24事故源，留v0.6双轨合并） | goldbach_gui.py _license_allows_solve/_small_worker/_large_worker/_on_ham_compute（v0.5.7） |
| B17 | 0916攻防实锤 | 🔴P0 | ⚠️未修(需v0.6) | 歌猜引擎注入材料（预签名blob+sig）硬编码随EXE分发——pyinstxtractor解包→pyc抠料→XOR 0x5A→直调bundle的goldbach_core_cpp.pyd注入→零license永久激活并解题（15分钟攻击链全程复现） | Ed25519只证"材料来自厂商"未绑定license/hwfp，材料人人可得；引擎级防护仅覆盖GUI路径，直调pyd路径失效；0825审计"引擎级保护成立"只测了GUI路径（验收剖面不全） | 处方=注入材料不随包：服务器激活成功后按license+hwfp派生下发（在线供数）或引擎Native化；短期如实定位"客户端防线=抬成本墙" | goldbach_gui.py _YS_CORE_BLOB_HEX/_YS_CORE_SIG_HEX + goldbach_core_cpp注入接口（v0.6整改） |
| B18 | 0916攻防实锤/0916修复 | 🟠P1 | ✅已修(v0.5.8) | 本地授权轨有效期=纯墙钟time.time()判定，时钟回拨→短时长付费key无限续命；防回拨武器monotonic_counter/save_counter（DPAPI锚max_ts）在yunshao_crypto里一直是孤儿函数零调用 | 造好没接线（verify_license未接入锚） | LicenseManager.is_activated()接入_rollback_guard_ok()：DPAPI锚记max_seen，回拨超1h容差=拒+clock_rollback留痕，锚故障放行不误伤；六分支单测6/6 | goldbach_gui.py _rollback_guard_ok（v0.5.8） |
| B19 | 0916攻防实锤/0916修复 | 🟡P2 | ✅已修(v0.5.8) | 歌猜无显式1000位锁：1000~4300位输入进大数引擎长时间空转；>4300位靠Python int转换上限意外拒绝（报错文案差） | 产品口径"≤1000位双限"只在哈密顿侧有代码强制 | _on_compute加显式锁：len(str(N))>1000→"测试版位数上限 1000" | goldbach_gui.py _on_compute（v0.5.8） |
| B20 | 0916攻防实锤 | 🟡P2 | ⚠️登记待修 | 激活key明文落盘%APPDATA%/YS_GOLDBACH/license.key（_save_gate_key无DPAPI） | 存储层未加密 | 处方：DPAPI加密+首启明文迁移；缓解现状=key内含hwfp签名跨机无效 | goldbach_gui.py _save_gate_key/_load_gate_key（随v0.6） |
| B21 | 0916攻防确认(档案自认D03规格§七) | 🟠P1 | ⚠️登记待修 | 已激活license.json缓存复制到另一台机器verify仍过=一码多机 | 引擎验签未执行hwfp比对（签名消息含hwfp但引擎侧不查） | 处方：引擎verify_license强制比对hwfp | hamilton_engine.pyd授权链（v0.6整改） |
| B22 | 0916网络情报/0916登记 | 🟠P1 | ⚠️登记待修 | 内置Ed25519公钥可被patch替换→破解者自制注册机批量签发"合法"license（换锁攻击；CHIAN_MANIFEST哈希可一并改，链校验被一并击穿） | 离线验签的公钥必须存客户端，patch客户端即可换锁；业界公认离线授权固有面 | 处方：服务器在线复验模式（激活后周期性lease）/公钥与服务器指纹联动校验抬高成本；彻底解=在线供数（与B17同一整改包） | auth.pyd/yunshao_crypto.pyd内嵌公钥（v0.6整改包） |
| B23 | 0916真机E2E发现/0916修复 | 🔴P0回归 | ✅已修(v0.5.9) | 真码激活成功后求解仍报ERR_NOT_ACTIVATED（激活对话框只写auth轨，B16门禁只认LicenseManager本地轨→误伤真激活用户）；另状态栏左右双段文案不同步（左已激活/右未激活） | 双轨再次脱同步：激活流与求解门禁读写不同轨 | _license_allows_solve重构：本地现验→pro过期降级→auth轨get_level现验token（Ed25519+抗回拨）任一有效即放行；五分支单测5/5+B16回归7/7+B18 6/6；v0.5.9真机E2E：服务器现签1d pro码激活→求解PASS(101位5对) | goldbach_gui.py _license_allows_solve（v0.5.9） |

**索引规则：**
- 发现bug当场追加此表，不许等、不许忘、不许淡化
- 修了的改状态为✅已修，不许删行
- 每次软件任务启动先读此表看有没有⚠️待修项
- 知世 07-27 07:02 原话："把所有bug如实记录进你的软件文档，或者说附属文档里面，然后建立索引，不要再让我提醒第2次"
| B24 | 0917知世真机测试 | 🟠P1 | ✅已修(v0.6.2) | 激活成功且可求解，但状态栏（重启后依然）显示"未激活"——显示与执行脱同步的第二形态（B23修了门禁，状态栏还在读旧本地轨） | 状态栏status_text读LicenseManager本地轨，激活对话框写的是auth轨 | status_text优先问auth轨get_cached_level()（与B23求解门禁同一真源）：pro→"已激活（专业版·全部功能）"/student→"已激活（学生版）"；回归B16七分支+B18六分支全PASS | goldbach_gui.py LicenseManager.status_text（v0.6.2） |
