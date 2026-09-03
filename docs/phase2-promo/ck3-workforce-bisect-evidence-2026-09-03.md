# CK3 workforce 分组启动 A/B 证据（2026-09-03）

## 运行输入

- 变体：`Z:\ck3_mod_rewrite\_runtime\phase2-group-bisect-20260903\workforce`
- 隔离 product：152 个文件，12,906,558 bytes；另挂载 6,619-byte Phase2 seed fixture（product 数字不含 fixture）。
- CK3：1.19.0.6 / Steam buildid 23530548，正式 Steam EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- bridge：当前 matching Release DLL/injector；完整 pinned settings 与 warm shadercache。
- report：`Z:\ck3_mod_rewrite\_runtime\formal-phase2-workforce-20260903\report.json`
- 本轮不载入存档、不执行 gameplay、不点击协议/通知/商店、不购买或付款。

## 结果

- CK3 PID 6080 于 12:04:21（Asia/Shanghai）启动，窗口进程最终为 `Responding=True`，峰值约 11.9 GB working set。
- `debug.log` 于 12:05:28 到达 `Total of : 881`；在约 5 分钟观察窗口内没有出现 `End loading of history`、`Setting idler 'Frontend'` 或 bridge-ready receipt。
- 对可见窗口发送 WM_CLOSE，等待 8 秒后仍未响应；随后中断 disposable observer，由其清理逻辑回收受控进程树。
- 独立进程清单确认 `ck3.exe` 与 `xar_ck3_bridge_injector.exe` 均已消失。由于 observer 被中断，原始 report 的 `close`/`shutdown` 字段为空；本页记录独立 post-close 清理结论，不把该轮写成完整 Frontend GREEN。

## 判定

`workforce` 变体在 on_action 881 后仍出现长加载，当前 Frontend/native readiness 为 RED/未闭合。与旧 51-file 核心的 51.7 秒 Frontend GREEN 对照，新增 workforce 内容是候选负载来源之一；仍需按更小依赖闭包继续二分。
