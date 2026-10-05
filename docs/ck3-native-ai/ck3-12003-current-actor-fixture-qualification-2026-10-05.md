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

## 2026-10-05：Main R13 取消前提停止与正式一天控制器限证据

Main R13 原严格 `one_life` / strict00 已按本场原生角色、episode、PID、generation 和精确 1.20.0.3 build 取得资格。Root 手动恢复时间后，下一实读已从 D0 到 D23，日期 raw `53144328 → 53144880`；gold 为 `100397101 / 100000 = 1003.97101`，破坏取消测试的资金前提。因此停止 GUI 业务，不执行 cancel，也不预写 FAIL；初始化仅 7/16，其余取消、119/default120/信仰/custom348 仍未证。

随后 Root 只提交一次既有正式 MCP `ck3_execute_step(step="life-advance-one-day")` 的六步诊断：fresh before → 完整 campaign-root → capabilities → 正式一步 → fresh after → 完整 campaign-root。六行均实际 finished/OK，同一角色 31254、PID 20328 / generation 1、episode `native-31254-9c363de52578`；前后 18 项 readiness 均 true，日期 `53144880 → 53144904` 精确 +24 小时，`requested_horizon_days=1`、`elapsed_days=1`、`timeline_speed=1`、`progress_status=postcondition`，控制器实际返回暂停且无事件。该诊断是 D23→D24，未修正资金、未重启、未换 episode，GUI 信用增加为零。

后续相同 original `one_life` 流程在新场 strict00 通过后，使用这项已经实际公开且执行过的正式一步控制器，再以新的 native snapshot 和完整 18 项 campaign-root 资格验证精确 D0→D1；不依赖手动恢复后等待截图来控制时长。保留既有身份、build、事件/终态、能力与硬 cap 合同，不新增或放宽参数。能力 ACK 和 D23→D24 结果不能替代新场 D0→D1 的实证，也不授权向 `native_campaign`、其他 actor 或其他 mod 外推。本场 ID 和 episode 不能填入下一场。

R13 于 `2026-10-05T04:17:03.752977Z` 正常 partial finish，原 harness GREEN/error null，线程及清理完成、CK3 tree absent、job final 0、最终库存为空；keeper final2991，screen CAS2992于 `04:19:25.876664Z` 实际 done/resources[]。GREEN 只证明限定诊断及收尾，不是 Main GUI 或产品 PASS。

完整 engine error 为 24115 B / 116 E：10 个既有生产变量警告、58 个与 R11 正文精确一致的 court 块仍 UNKNOWN，以及 48 个首次 Main-run formatter 正文 `Unknown formatting tag 'weak\b\u0015positive_value'`，原始 0x08/0x15 字节保留；formatter 只指向引擎输出位置 809，脚本/资源第一调用方仍 UNKNOWN。正文重复、后续场未出现或正常 harness GREEN 都不豁免这些未知块。

- [正式六行与完整 18 项资格实际结果](C:/workspace/ck3-upgrade-20261005/main-creator-r13-readonly-monitor-agent-01/actual-original-one-life-literal-D23-D24-sixrows-01.json)、[实际唯一 controller control plan](C:/workspace/ck3-upgrade-20261005/live/4-8e1c2f1861--eternal-recurrence--R0013/controls/main-r13-actual-one-day-control-diagnostic-once-01.json)。
- [R13 partial GREEN 无产品信用收据](C:/workspace/ck3-upgrade-20261005/main-r13-current-engine-log-boundary-agent-01/closed-r13-partial-GREEN-no-product-PASS-scope-receipt-05.json)、[116E 完整正文及 source UNKNOWN](C:/workspace/ck3-upgrade-20261005/main-r13-current-engine-log-boundary-agent-01/closed-r13-final-engine-body-source-and-runtime-boundary-03.json)。
- [实际闭合退场](C:/workspace/ck3-upgrade-20261005/main-r13-gold-precondition-stop-root-01/closed-actual.json)、[keeper final2991](C:/workspace/ck3-upgrade-20261005/main-creator-screen-keeper-a51-01/report.json)、[实际 screen CAS2992](C:/workspace/ck3-upgrade-20261005/main-r13-gold-precondition-stop-root-01/screen-release-01.json)。

## 2026-10-05：Main R14 原始 D0→D1 与廷臣 GUI 16 项实证

R14 使用新的冷 profile，在 CK3 `1.20.0.3` / EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6` 中绑定实际 episode `native-31254-60f522bf056d`，角色 31254 / PID 15064 / generation 1。90 项游戏规则的完整 Apply 回读一致，原 strict00 的 18 项 readiness 全通过；这两项资格本身不代替廷臣 GUI 或发布门禁。

原始 D0→D1 四行全部实际完成：before、capabilities、一次 `life-advance-one-day`、after。日期 raw `53144328 → 53144352`，精确增加 24 小时；`elapsed_days=1`、`requested_horizon_days=1`、`progress_status=postcondition`。工具实际执行 set-speed-1 / resume-map / pause-map，末态暂停、地图就绪、无事件，同一角色、episode、PID 和 generation；D1 外置夹具资金为 1000。此次有限推进不并入战争 lane 的累计日账，也不授长期自然运行信用。

决议 first-open 五行全部通过，`ck3_open_ingame_decisions_v1` 本 episode 只执行一次，实际 `verified_visible`；真实 query、select 及前后快照完成，select 为 `verified_selected_detail`。后续关窗、重开和业务配置由 Root sole controller 按当次原图及坐标映射进行 physical GUI 操作，没有重放 typed opener、删除 claim 或用通用 Confirm 替代 Main 控件。

独立日志回执在 `2026-10-05T05:05:21.066680Z` 核得 required **16/16 各一次、FAIL0**，包含初始化、取消零副作用、119 资金不足阻止、default 120 一次交付一次扣款、选择 Aluk 信仰、custom 348 配置保留/重开及一次交付一次扣款，最后 `ERVA: TEST DONE standalone`。默认交付后金币为 880，自定义交付后原生快照 raw `53200000 / 100000 = 532`；Root 原图直接显示 532 金币与“典造已成”、新廷臣已到庭。这里验证已有信仰/礼仪保持合同，不把夹具中的 non-default Rite 入口记成玩家可直接选择具体礼仪的新功能；该新增任务仍排在全部 mod 1.20 翻新维护之后。

当前 engine 完整原文为 19,795 B / 68 E / 17 种正文；仅去首时间戳后的全部正文及 multiplicity 与 R11 精确一致，相对 R10/R11/R12/R13 的新正文数为 0。其中 10 块五变量历史正文与 58 块 court 正文分别保留；court58 的首调用者与因果归属仍 UNKNOWN，不能据重复、文件名或频率豁免。R13 的 formatter48 本次观察未出现，历史 UNKNOWN48 继续保留，absence 不证明修复。R11 的未知工具名 RED、R12 的重复 opener RED，以及 R13 手动推进到 D23 / 1003.97101 导致取消前置不满足、仅 7/16 的 partial 范围均原样保留；R13 后续独立 D23→D24 一天和 partial runner GREEN 没有产品 PASS 信用。

本增量只确认 R14 的当前角色资格、精确一日和廷臣 GUI 范围。记录时原报告仍 `RUNNING/hold`、`error=null`，没有借此预填完整 harness 退场结果。**冷重载、NoHeir 真实死亡/八值结算、Main 正式发布仍 NOT_RUN**；正式发布闭环维持 **4/10 = 40%**，不新增产品发布信用。

- [R14 90 项完整 Apply 回读](C:/workspace/ck3-upgrade-20261005/main-creator-r14-readonly-monitor-agent-01/actual-rules-full90-mapping-01.json)、[原 strict00 18 项资格](C:/workspace/ck3-upgrade-20261005/main-creator-r14-readonly-monitor-agent-01/actual-strict00-qualification-thin-01.json)。
- [原始 D0→D1 四行实际收据](C:/workspace/ck3-upgrade-20261005/main-creator-r14-readonly-monitor-agent-01/actual-finite-original-D0-D1-fourrows-01.json)，SHA `e5758b30d251fc276288ca9c922bd6411176c4e0272e7a60be6b921d55e081bc`；[原实际 report](C:/workspace/ck3-upgrade-20261005/live/4-8e1c2f1861--eternal-recurrence--R0014/native-report.json)保存 first-open 五行。
- [廷臣 GUI 16 项独立薄回执](C:/workspace/ck3-upgrade-20261005/main-creator-r14-readonly-monitor-agent-01/actual-main-GUI-business16-and-custom348-thin-01.json)，SHA `b788eb5660c104dfb566fa99ffd6bccf497074d384ca78b896ad3ef382b87c7a`；[16 项实际 debug 原行](C:/workspace/ck3-upgrade-20261005/main-creator-r14-readonly-monitor-agent-01/actual-required16-debug-marker-lines-01.json)，SHA `f55f314a8dc557f4485715662af48d3d191de6b46f28f8a75a27a5ccb8c04b54`。
- [532 金币/典造已成实际原图](C:/workspace/ck3-upgrade-20261005/main-r14-window5-custom-purchase-once-01-settled.png)、[该次点击坐标回执](C:/workspace/ck3-upgrade-20261005/main-r14-window5-custom-purchase-once-01.mapping.json)。
- [R14 当前完整 engine 正文与 source 边界](C:/workspace/ck3-upgrade-20261005/main-r14-current-engine-log-boundary-agent-01/observation-002/full-body-source-thin-receipt.json)、[R13 partial GREEN / 无产品 PASS 范围](C:/workspace/ck3-upgrade-20261005/main-r13-current-engine-log-boundary-agent-01/closed-r13-partial-GREEN-no-product-PASS-scope-receipt-05.json)。

## 2026-10-05：R14 保存及实际收口补记

R14 的 MCP 保存四行均实际通过；存档为 68,460,590 B，SHA-256 `c13253b46d0dcb271c7ed59fb873313034d9be4539fa94ab6a3f9dceb15f1364`。保存前后暂停 D1、532 金币、同角色/episode/PID/generation；原存档和保存历史已外置冻结。

本场 05:20:25.665247Z harness GREEN/error null、清理完成，keeper final3054、screen CAS3055于05:24:18.375422Z done/resources[]。Root 原生退出桌面请求后的截图仍显示保存中，随后 finish_hold 实际触发受管终止（job before termination=1、CK3 exit code=1）；因此正常 GUI 自退尚未证明，下一冷加载场补验。最终日志仍68E，未知块不予豁免；16/16及保存通过不代替完整产品验收或发布。

证据：[保存及历史](C:/workspace/ck3-upgrade-20261005/main-cold-reload-manual-inputs-agent-01/actual-R14-save-fourrows-and-anchors-thin-01.json)、[实际关闭及终止边界](C:/workspace/ck3-upgrade-20261005/main-creator-r14-readonly-monitor-agent-01/actual-R14-closed15-and-managed-termination-thin-01.json)、[最终日志](C:/workspace/ck3-upgrade-20261005/main-r14-current-engine-log-boundary-agent-01/closed-r14-final-engine-body-source-and-runtime-boundary-03.json)、[实际 CAS3055](C:/workspace/ck3-upgrade-20261005/main-r14-root-closeout-01/screen-release-01.json)。
