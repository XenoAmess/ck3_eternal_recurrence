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

## 2026-10-05：Main R15 冷加载与正常自退

R15 在新进程中实际加载 R14 的 checkpoint；原00完整18项资格通过，新 episode、暂停D1、532金币。Root 实际审阅7个保留设计页、自定义廷臣及6项特质提示，未再次购买。原生退出到桌面后独立句柄实际读得exit0，先于 finish_hold；随后旧harness强制向已退出进程取样而记录RED，保留8成功/finish1失败，不改写旧结果。实际thread/cleanup/treegone/job0/库存空，keeper3123后CAS3124 done。

证据见[Main R15专题](../ck3-1.20.0.3-eternal-recurrence-readiness-2026-10-05.md)、[冷加载清单](C:/workspace/ck3-upgrade-20261005/main-r15-cold-evidence-append-agent-01/r15-coldload-thin-evidence-manifest-01.json)及[闭合补记](C:/workspace/ck3-upgrade-20261005/main-r15-cold-evidence-append-agent-01/r15-closeout-thin-addendum-02.json)。Main正式发布仍待无继承人业务及其他剩余门禁，正式完成仍4/10。

## 2026-10-05：Main R16 原 00 开局资格失败与真实关场

R16 使用当前 1.20.0.3、source04 / DLL70 / harness95ff、生产86文件与原 NoHeir fixture12；原 `one_life`、完整18项资格和43阶段输入没有放宽。Root 在原生 GUI 实际核三项规则为 `xar_on` / `xar_inherit_100` / `xar_score_growth`，Apply 关闭后以罗贝尔实际 Start 一次。此规则证据来自 Root 原图，不能称为本场完整90项 applied规则 DTO 回读。

原 00 在 `06:48:30.501098Z → 06:48:45.157315Z` 返回 MCP campaign-root 错误；底层为 `stage=wait / wait_result=executor_failed / executor_enter=false`。callback 实际开始并完成一次，而 campaign DTO reader 尚未执行，因此完整18项和90规则均未取得。前后快照保持同角色31254、暂停D0（date raw53144328），但 active_event 从空变为 instance1 / 两选项；实际日志 import→opening flow→offering pact。源码要求入口快照整体相等，active_event 参与比较；这是开局竞态的证据方向，但回执未细分内部 guard，不能唯一断言故障字段，也不能据此说新启动路线已经修复。

R14 已实际通过的语义罗贝尔 Start 是 `xar_off` / inherit100 / growth 加 ERVAstandalone。R16 的 `xar_on` 开局与 NoHeir 输入是新增覆盖，不能外推 R14 的 full18。现有 semantic Start 只等待同 actor/date/PID/generation 的后续暂停 pump，随后仍调用一次完整 root；并未提供独立的契约事件稳定门禁。新 R17 输入仅作待执行准备，actual 尚未取得。

R16 harness 于 `06:48:47.400146Z` 真实 RED 关闭；managed thread finished / cleanup_ok 均 true，CK3 tree gone / job final0 / inventory[]。native session 为受管 stop，CK3 exit code1，不能称正常 GUI 自退0。keeper final3145 / thread exited，Root 取得 keeper exit0 后，screen CAS3146 于 `06:55:52.091311Z` 实际 done/resources[]。原 after-start capture 因 PID 已 gone 没有生成地图原图；不能把原目录或一次 capture 请求写成地图截图存在。

NoHeir 的原01→43业务、真实死亡及八项渲染值仍未跑，旧 R15 原生退出0及随后 HRED、R14 GUI16/16、writer33/reader12 等各自范围保留，不增加本场产品或发布信用。

证据：[R16 原00失败及受管退场](C:/workspace/ck3-upgrade-20261005/main-noheir-r16-readonly-monitor-agent-01/actual-R16-original00-failed-pact-event-and-closed-thin-02.json)，SHA `3f728f4df7d98c2d5f87794fa19317e21400f6e8a133f2bb3809d83e85a0a6be`；[独立 caller/source 与 CAS3146 补记](C:/workspace/ck3-upgrade-20261005/main-noheir-r16-readonly-monitor-agent-01/actual-R16-CAS3146-and-caller-source-addendum-03.json)；[Root 实际 release](C:/workspace/ck3-upgrade-20261005/main-r16-root-closeout-01/screen-release-01.json)。

## 2026-10-05：Main R17 真实 full18、D17 与受管闭合

R17 的 Root physical Start 实际一次，原生产86与 NoHeir fixture12 未借用旧1.19信用。pact实例1在新只读稳定门禁中实际两次一致；原00随后真实通过18项readiness，原生规则实际89项，D0/date raw53144328、角色31254、PID10748/gen1、episode `native-31254-a66de846d6b9`。89是本场campaign-root真实条数，不是R14 Main GUI90，旧R16 original00 RED及未唯一归因的竞态仍保留。[开局资格薄核](C:/workspace/ck3-upgrade-20261005/main-noheir-r17-readonly-monitor-agent-01/actual-R17-startup-gate2-original00-full18-rules89-thin-02.json)。

最终实际100/100 finished/ok、harness GREEN仅覆盖已执行步骤与管理清场。17次自然日各+24并暂停，末次D16/date53144712→D17/date53144736。真实log取得 `cca120.13 / NO_HEIR_DEATH_OPTION_READY`、`cca120.2 / PASS no_heir_precondition`；原生快照为instance5/两项enabled options，尚无typed event-definition身份，未执行`cca120.12`、death、结算八值或正常GUI退出。fixed hold到期使原06b15后的单独after观察未入队，不能宣称原43阶段全部完成。[关闭及业务边界](C:/workspace/ck3-upgrade-20261005/main-noheir-r17-readonly-monitor-agent-01/actual-R17-managed-closed-and-predeath-boundary-thin-05.json)、[有限推进薄包](C:/workspace/ck3-upgrade-20261005/main-r17-finite-delegate-agent-01/delegated-R17-final-stop-thin-packet-01.json)。

D16 checkpoint 68,894,815 B/SHA `01ae0701a7d30ef5c657d602171145b098abfdd43073f9cb58f6534449d30951`，不包含原场D17；后续R18仅是新epoch冷加载并自然重建一天的计划，不预填通过。writer33/reader12、Creator16、ColdR15已赚取的范围继续保留，不因本场未死亡而重复。

实际native受管stop/exit1，harness10:14:09.006399 UTC finished/error null/thread finished/cleanup_ok；treegone/job0/库存空。旧a56 keeper3335/thread_exited后，Root CAS3336于10:20:02.841015 UTC done/resources[]，不能称GUI自退0。[Root最终回读](C:/workspace/ck3-upgrade-20261005/main-r17-root-closeout-01/actual-final-readback-01.json)、[CAS3336](C:/workspace/ck3-upgrade-20261005/main-r17-root-closeout-01/screen-release-01.json)。

关闭后error.log实际4,900 B/38条`[E]`，SHA `38ad254a198784715466f043e7ebfc7b8979d4603e9b06c050a35a1dfdfa3840`；10条变量提示加28条formatter控制字节错误。原Main `project_error_lines` AST实际命中0，仅证明原`xar`/trait-star门禁未命中，不授予全局零错误或vanilla豁免；新增28条继续UNKNOWN_NOT_WAIVED。[精确原日志判定](C:/workspace/ck3-upgrade-20261005/main-r17-three-doc-append-prep-agent-01/original-project-error-lines-receipt-01.json)。原发布条款未把court58首caller调查列为必跑硬门禁，历史UNKNOWN保留，不据此扩成无止境验收；确定性新production错误仍须修复后另起验证。Main正式发布仍pending，累计 **4/10＝40%**，原完整Notes匿名回读、fresh-cache、正式构建及changelog master闭环不可省略。详情见[Main专题](../ck3-1.20.0.3-eternal-recurrence-readiness-2026-10-05.md)与[原门禁核证](C:/workspace/ck3-upgrade-20261005/main-release-hard-gates-readonly-agent-01/ROOT-CARD-01.md)。

## 2026-10-05：Main R18 death-once与exit0成立，生产八值GUI失败

R18冷加载R17的D16，在新PID15912/gen1、episode `native-31254-df4dce89cee9`重新取得原00/full18/89规则，再实际自然推进53144712→53144736、精确一天+24。旧R17 planned段保留历史，不重放旧epoch动作。[新资格](C:/workspace/ck3-upgrade-20261005/main-noheir-r18-readonly-monitor-agent-01/actual-R18-new-epoch-original00-full18-D16-rules89-thin-02.json)、[实际一天](C:/workspace/ck3-upgrade-20261005/main-noheir-r18-readonly-monitor-agent-01/actual-R18-saved-D16-D17-natural-day-and-new-ready-03.json)。

Typed query实际识别instance5=`cca120.12`/source角色31254，death-submit-once一次成功。原生公开结算ready、terminal played_character_dead、commit1/record_written=true；八值按最终分量/拒绝前分量/交易/拒绝/契约/旧纪录/候选/差值依次 **2.97/3/0/1/0/0/2/2**。这些native字段不能冒充渲染值。[真实死亡与结算](C:/workspace/ck3-upgrade-20261005/main-noheir-r18-readonly-monitor-agent-01/actual-R18-typed-death-once-and-public-settlement-thin-04.json)。

Root直接原图确认唯一widget/summary、死者31254、无玩家继承人及可用退出；实际八值全部显示0，三项零值一致、五项非零源值失配，结果为 **生产GUI RED**。原08两树仅结构413/65控件，无rendered-text信用；harness或native数据不能冲销这项故障。[原图判定](C:/workspace/ck3-upgrade-20261005/main-r18-terminal-original-root-01/actual-eight-values-root-observation-01.json)，SHA `0bed132c385c8eec548a92902d6015be6e258fe76b3ceb84f5d1c3cdcf050d9e`；[两树边界](C:/workspace/ck3-upgrade-20261005/main-noheir-r18-readonly-monitor-agent-01/actual-R18-terminal-trees-and-Root-GUI-native-difference-05.json)。

Root实际GUI两次点击后，OS/native于11:29:34Z正常exit0；最终harness14/14 GREEN/error null/thread finished/cleanup_ok，全树gone、job0及库存空。旧a57 keeper3393后CAS3394于11:33:24Z done/resources[]。死亡后运行中及退出后tutorial各两读，全部75 B/SHA `56300fb968e34e3383e5ecbd103face48efd05f15d54aa8966e17750a5166a64`、含`xar_hs_ge_2`，不授八值或新冷加载信用。[最终薄核](C:/workspace/ck3-upgrade-20261005/main-noheir-r18-readonly-monitor-agent-01/actual-R18-final14-native-exit0-HGREEN-with-GUI_RED-06.json)、[Root闭合](C:/workspace/ck3-upgrade-20261005/main-r18-root-closeout-01/actual-final-readback-01.json)、[CAS3394](C:/workspace/ck3-upgrade-20261005/main-r18-root-closeout-01/screen-release-01.json)。

现八getter读取GetPlayer角色shadow，修复路线改读已提交global源；GetPlayer是否null未实证。owner与独审后，R19计划冷加载同D16只复验受影响GUI/terminal/正常exit，尚无PASS，不重复writer33/reader12、Creator16或ColdR15。确定性显示故障仍是正式发布阻断；Main发布新增0，累计 **4/10＝40%**。详见[Main专题](../ck3-1.20.0.3-eternal-recurrence-readiness-2026-10-05.md)。
