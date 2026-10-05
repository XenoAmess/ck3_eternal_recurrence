# CK3 1.20.0.3 fixture 当前角色资格（2026-10-05）

`native_campaign` 的原生快照没有 `episode_identity_pending`；旧 harness 要求它 `is False`，导致等待条件持续不满足。外置修正版 `95ff0dca…b57d` 在已资格化的 `native_campaign` 中核对实际存活、暂停、地图、角色、日期、PID、连接 generation 和精确 build；默认 `one_life` 保留原严格谓词，不补造 flag 或 episode。

QOL 的完整 campaign-root 返回 `held_title_partition_unavailable`，代表全头衔读取聚合失败。具体分支仍未查明；源码支持 hegemony tier 6，不能据此认定该政体不受支持。

付款 R7 的实际 startup scope 将动态角色 34422 / `han_8052` 与 PID 18580 / generation 1 / 1.20.0.3 绑定。开局通知未及时关闭，首次资格等待超时；Root 仅关闭该通知一次，在同一进程内恢复检查。原始超时、`FAILED_AFTER_SINGLE_START_NO_RETRY` 和完整 runner RED 均保留。

热恢复先完成 before / markers / after 三项只读检查，再执行原五步付款计划，仅将第一步的四个资格引用替换为本场实测值。实际推进 24 小时，日期 raw `53144328 → 53144352`，角色、PID 和 generation 不变；10 项付款标记各一次、三类 FAIL 为零，新增 scope 三标记各一次、scope FAIL 为零。最后实际暂停、地图就绪、无事件；会话于 `2026-10-05T00:45:00.956256Z` 关闭，清理及线程退出均通过。付款业务范围通过不授予完整领地 DTO、宗教、防御或全产品发布信用。

证据：

- [实际作用域与三项热资格](C:/workspace/ck3-upgrade-20261005/qol-payment-r7-hot-recovery-agent-01/guarded-payment-actual-qualification-receipt-01.json)，SHA `c17e1c696fa8ec4e16159fc90808db456f6ab45c87c957979ab3fcc6856467d0`；使用的 QOL harness 为 `bc55f233…4ad88`，不是基础 `95ff` 原文件。
- [当前 owner pump 两次递增](C:/workspace/ck3-upgrade-20261005/qol-payment-r7-hot-recovery-agent-01/actual-hot-verified-pump-pair-01.json)，实际 `93297 → 94221`，同 owner/current TID 15792。
- [一次关闭通知的坐标回执](C:/workspace/ck3-upgrade-20261005/xqol-payment03-close-startup-event-once-01.mapping.json)与[关闭后实际原图](C:/workspace/ck3-upgrade-20261005/xqol-payment03-close-startup-event-once-01-settled.png)。
- [原五步及闭合范围收据](C:/workspace/ck3-upgrade-20261005/qol-payment-r7-hot-recovery-agent-01/closed-r7-product-scope-PASS-harness-RED-01/closed-r7-thin-product-harness-split-receipt-01.json)，SHA `0dba697915b3ededfcd1341487eceb7c04b2285525fef5b6a94c7e7a7771a3c3`。
- [当前三块完整 error 正文](C:/workspace/ck3-upgrade-20261005/qol-payment-r7-hot-recovery-agent-01/closed-r7-current-error-three-full-bodies-01.json)：新增外置 scope 文件缺 UTF-8 BOM，以及两条 `zqa120_ticks` 未使用提示；保留原始报告，后续新夹具遵守 BOM 要求，不覆盖已用输入。
- [宗教R8限定D0闭合](C:/workspace/ck3-upgrade-20261005/xqol-religion06-live-monitor-agent-01/religion-r8-limited-closeout-01.json)，SHA `646aee4fd2d43b1d39e6e5c6437c593d69ddf617008825ac2135389868bc3770`：15项各一次、两FAIL为零，同一原生角色和连接；原四步及另三项只读查询完成，正常hold到期GREEN并清理退出。完整领地DTO仍unavailable，实际67个日志块另存完整分组，未用GREEN代替日志归因；不授予实际改宗、任命交互或全产品发布信用。

重跑使用新的冷 profile 与当次身份。正式上传仍须分别完成正式 staging、产品实机验收、完整公开 Change Notes、缓存核对及永久 changelog 提交推送。
