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

## 2026-10-05：后续失败边界与工具名守卫

QOL防御R9真实D1/24小时，required仅4/23，`reverse_candidates_missing`与`composite_relationship_setup_not_ready`各FAIL1；error.log为空不等于业务通过。原场partial finish后harness GREEN、清理退出，a48已CAS2900释放。Main R11真实90规则完整Apply一致、原strict00与D1通过、初始化7/16；随后Root外置计划误用不存在的MCP名`ck3_activate_ingame_decisions_v1`，原harness RED保留，正常受管清理、a49 CAS2931释放。此错误是本次Root调用错误，不是已证明的游戏崩溃或mod错误；cancel/119/default/custom348仍未证。68个engine块中10个与R10完整正文exact，新增58个court/12种完整正文仍UNKNOWN，不泛豁免。

source05 trace-only DLL已构建、11条纯合同通过；只新增失败详情，真实held-title具体branch仍UNKNOWN，不能据编译或纯夹具说缺口已修。外置queue NEW02在写入前核当场actual `mcp_tools`名字；valid/unknown/mixed三项纯tmp通过，未知或混合计划controls零写。旧场、旧源码、旧DLL及失败回执原样保留，新实机用新冷profile。

- [R9完整EOF及两条业务FAIL](C:/workspace/ck3-upgrade-20261005/defense-r9-current-log-boundary-agent-01/closed-r9-businessFAIL2-engineEMPTY-source-boundary-02.json)、[R9实际CAS2900](C:/workspace/ck3-upgrade-20261005/defense-r9-failed-fixture-root-closeout-01/screen-release-01.json)。
- [R11有限实证与未验GUI](C:/workspace/ck3-upgrade-20261005/main-creator-r11-readonly-monitor-agent-01/closed-freeze-01.json)、[原RED及68完整日志边界](C:/workspace/ck3-upgrade-20261005/main-r11-current-engine-log-boundary-agent-01/closed-r11-final-engine-body-source-and-runtime-boundary-01.json)、[R11实际CAS2931](C:/workspace/ck3-upgrade-20261005/main-creator-r11-root-closeout-01/screen-release-01.json)。
- [source05构建/11纯合同/实际branch未知](C:/workspace/ck3-upgrade-20261005/held-partition-trace-runtime-agent-01/FINAL-TRACE-ONLY-PACKET-05.json)、[queue NEW02与三项纯测试](C:/workspace/ck3-upgrade-20261005/root-control-tool-name-guard-agent-01/HANDOFF.md)。

## 2026-10-05：Main R12 决议 opener 的一次调用边界

Main R12 在同一真实 episode `native-31254-844af62e02bc`、角色 31254 / PID 12600 / generation 1 中，完成初始化 7/16 和实际取消零副作用第 8 项，required 共 8/16、fixture FAIL 为零。119 不足资金阻止、default 120 交付扣款、选择信仰及 custom 348 配置/重开/交付等剩余项仍未验证，不能据此写成廷臣 GUI 全通过或发布完成。

Root 第一次实际调用 `ck3_open_ingame_decisions_v1` 已领取本 episode 的一次 claim；取消后第二份计划又调用同一 opener，`native_driver.py:6766` 的 `claim.open("x")` 返回 `FileExistsError`，继而明确拒绝 `Decisions opener already claimed for this episode; no action retry`，该次未再次 dispatch DLL。原 harness RED 和异常保留，随后执行受管清理。这是 Root 重复调用一次工具的误用，不能把它归为游戏崩溃或 mod 错误；实际正常 GUI 退出仍未证明。

可复用边界：工具名存在和 schema 校验只证明接口资格。操作前还须核实际工具的 once/claim 合同；`readOnlyHint=false`、`idempotentHint=false` 的动作不能因为 HUD 已关就重复提交。已领取的 claim、旧 action history 和失败原片继续保留；后续重开 HUD 应由当前 sole controller 按当次原图与坐标映射合同执行真实 GUI 操作，不能删除 claim 或换 ID 重试同一动作。动作 ACK 仍须由新的实际状态或像素证明业务结果。

R12 于 `2026-10-05T03:42:28.062797Z` 实际闭合，线程及清理通过，CK3 tree absent、job active final 0、最终库存为空；keeper final sequence 2963、screen CAS 2964 均有实际回执。完整 error.log 为 2380 B / 10 E：只去首时间戳后，五变量各两次的全部正文 multiset 与 R10/R11 精确一致，新增正文为零。R11 的 court 58 块本次未出现，历史 UNKNOWN58 继续保留；本次 absence 不能证明它们是原版或 fixture，也不能清除原 RED。

- [R12 8/16、取消与原 RED 闭合](C:/workspace/ck3-upgrade-20261005/main-creator-r12-readonly-monitor-agent-01/closed-freeze-01.json)、[第二次 opener 的原异常片段](C:/workspace/ck3-upgrade-20261005/main-creator-r12-readonly-monitor-agent-01/second-open-exception-raw-tail-01.log)。
- [R12 完整 engine 正文、生产 source 与退场边界](C:/workspace/ck3-upgrade-20261005/main-r12-current-engine-log-boundary-agent-01/closed-r12-final-engine-body-source-and-runtime-boundary-02.json)，SHA `435538a82b1cb5cc437b221c74b248fe86573151e000f92161507e17280e6aaa`；指针保留原 6,011,118 B report，不复制或改写原报告。
- [keeper final2963](C:/workspace/ck3-upgrade-20261005/main-creator-screen-keeper-a50-01/report.json)、[实际 screen CAS2964](C:/workspace/ck3-upgrade-20261005/main-creator-r12-root-closeout-01/screen-release-01.json)。
