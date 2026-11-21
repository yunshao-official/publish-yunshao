# 外部AI问答器·使用说明 v1.0

> **摘要头**
> - 标题：外部AI问答器（DeepSeek / Kimi 一键任务脚本）
> - 日期：2026-10-26｜版本：v1.0｜状态标签：**工具·可用**（v1.0 已实测登录/填入/发送链路；提取器为初版按关键词截取，长回答建议直接 domSnapshot 人工读）
> - 依赖：ZCode 内置浏览器（browser-use 技能）；无体系常数
> - 一句话：把"给 DeepSeek/Kimi 发任务→取回答"固化成一个可复用模块，任何 ZCode 会话 import 即用；首次各需一次微信扫码登录，之后免登。

## 用法（ZCode 会话内）

```
const { pathToFileURL } = await import("node:url");
const { sendPrompt, collect, loginState } = await import(
  pathToFileURL("H:/理论存档/09-流程规范/工具/外部AI问答器-v1.0-20261026.mjs").href
);
await sendPrompt("deepseek", "任务文本");     // {ok:true} 或 {needLogin:true}(扫码后重试) 或 {queued:true}(Kimi拥堵)
const r = await collect("deepseek");          // 轮询；r.done===true 时 r.text 为回答
```

## 已知现实（2026-10-26 实测）
- Kimi 免费队列高峰限流（"聊天的人太多"），脚本自动退避重试 3 次；仍堵→换 deepseek。
- DeepSeek 免费无此限制，为默认首选。
- 登录态存于 ZCode 内置浏览器会话；ZCode 重启后需重新扫码。
- 你的 Chrome+AutoGLM 扩展链因谷歌商店不可达暂挂（细节见 daily 2026-10-26）；本工具不依赖该链。

## 登记
- 正本=同目录 .mjs 脚本+本说明；登记：daily 2026-10-26 / MEMORY / 工作区索引。
