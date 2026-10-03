# 战争与战争视频维护交接：2026-09-29

**2026-10-03 战争授权更新。** 项目所有者明确命令“取消任何的非战约束”，并要求研究战斗。原战争研究停止、nonwar-only、战争执行暂缓、战争只能交由其他维护者等现行限制全部撤销；战斗、军队、行军、围城、战争理由、宣战、防御战争、议和及相关原生 AI、只读 bridge/MCP、策略、实现和实机验收均可继续。不得仅因涉及战争再次要求授权。本文历史冻结配置的 OFF、旧尝试 RED、当时未提交动作与未实现能力保留原事实，不能继承为当前禁战规则，也不能把开放授权写成能力已经完成。继续保持罗贝尔 actor29829、episode `native-29829-2bc2d599f7f9` 的原 ordinary campaign 与自然继承线，原生 AI 研究优先、exact-build 绑定、ROOT 唯一实机/pipe/Git owner，以及最小化、无焦点、无桌面输入。当前续接身份和保存锚点以[最新接续记录](2026-10-03-g2-v33-resume.md)为准，本文较早 episode、PID 和存档仅供历史证据。

项目所有者要求把手上的工作收至可交接阶段后休假，停止开启新工作。本页记录截至 2026-09-29 20:57（北京时间）的历史事实与证据；当时没有执行新的游戏日期、行军、攻击、投降或活动开始。当前战争研究和执行授权按页首 2026-10-03 更新，不再继承本页旧停工或禁战安排；外部发布仍按其任务授权执行。接手者应先读 [2026-09-28 交接](2026-09-28-war-maintainer-vacation-handoff.md)、当前 `AGENTS.md`、对应 WAR 请求和各 Draft PR，再核对最新 `master` 与固定 OneDrive `C:/Users/1/OneDrive/WAR/`。

## 首要阻塞：R0271 / H3937 围城参与者

Robert 正式续跑仍 **RED**。H3937 原存档 SHA-256 `92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6`；actor `29829`、WarID `16777231`、日期 `53219928`、history `3937`。候选只读入口在本地隔离工作树 `D:/w/h3937_combined_a05_six`、HEAD `219477ac10a9cb74d24e386432fdcfebc566fbe6`；它只允许同一暂停帧六条读取，日期、行军和攻击门均关闭。两轮独立静审 GREEN，普通和 `-O` 的聚焦测试通过。它使用 #612 attempt03 的 Release DLL SHA-256 `F5E708FC554C377420B3D31D9B38B4FB6DE2D3A3B19C7D298DAA3DB61233793F`、injector SHA-256 `8E2115CBE43358DD6F47C12CC94A2E96BF8049DE70204E425B37B5CE825AFE5E`；[构建清单](D:/ck3-research-artifacts/h3937-physical-inventory-mailbox-attempt03/manifest.json) SHA-256 `D582DD7DF61663F4C40FD29FFF8E0E303E5353335E853E87AE9F7B37DCA66092`，217/217 构建、注册 CTest 1/1 和 fixture 通过。这些仅证明静态及构建条件。

此前 a04 因 300 秒原生就绪超时 RED，目标查询 0、游戏动作 0；[WAR v1 回件](<C:/Users/1/OneDrive/WAR/R0271-R3942-H3937-READONLY-RED-20260929/RESPONSE-WAR-ROBERT-R0271-R3942-H3937-A04-RED-v1.json>) SHA-256 `DC39BECFD3872DF18EA8DA51A255DF69C11D25759725EBE2ADF35449425E0BE5`，对应 [Draft PR #653](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/653) HEAD `0ebe9a62e`，静态 CI、CLA 通过，未合并；来源消费回读仍待确认。

本次 a05 官方无启动准入为 READY，清单在 `D:/ck3-research-artifacts/war-h3937-combined-no-launch-20260929/attempt-05/`：admission SHA-256 `86FAE45B641E5CC6E87C0D59DC42529A1C7D2EB1110ED567CAACD1460C9BE5DE`，operator manifest `8DF7489C75D132E2BCB35D73CE21A644B8BC0A154DE5DBDB9597103DC024D27E`。启动前两张不同随机码的原始桌面截图均经直接目视确认 Steam 显示“离线模式”；屏幕准备目录为 `D:/ck3-research-artifacts/war-h3937-combined-live-20260929/screen-attempt-05/`。GO 回执 SHA-256 `1AA70593C9B02EDC5197549A8077725F6153CBBD04E33365C807C269EEAF1F5C`，只授权这一轮只读尝试。

**a05 实际仍为 RED**：`D:/ck3-research-artifacts/war-h3937-combined-live-20260929/attempt-05/outer-report.json` SHA-256 `5B2514281736D2D489535152CCD777CAB5DEA59A7CF443CD6F763EA7046F24D5`。桥接传输已连接、原生适配器报告 ready，但 600 秒内未出现语义游戏快照；最后心跳 `date_raw=0`、`paused=false`、`executed_requests=0`。因此六条只读查询均未执行，`query_actions=0`、`gameplay_actions=0`、`frame=null`，没有围城参战集合或完整实体军队清单。`NativeReadinessTimeoutError: semantic game state unavailable` 是这一轮精确错误。截图 `readiness-timeout-desktop.png` 已目视检查，画面是 Codex 桌面而非游戏，不能据此推断游戏内状态。外层与 supervisor 均证明受管清场、原存档和配对资产哈希不变；完成回执 `completion.json` 指向同一外层报告。未来只能建**全新 attempt** 查明为何存档冷载未发布语义快照，不得把 a05 改写为 GREEN 或原地热重试。日期、移动、攻击和 Robert 正式续跑在该 a05 尝试当时没有执行；a05 的真实读取故障保留并按必要范围修复，不能将该历史 RED 继承为当前全局禁战或 Robert 续跑禁令。

本地 #612 的 a05 六读 HEAD `219477ac1` 尚未推到该 PR；远端 [Draft PR #612](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/612) 的已验证 HEAD 为 `9b54496a5e2cb4b57f4548926a72ed9d30299d46`。接手时先对比远端和本地提交，不要把本地实机 RED 当作已发布结论。R0271 先前风险研究表明场外敌军可能早于我方到达目标；现有首路点预览不能证明抵达时的参战集合。

## 其他战争侧在途交付

| 项目 | 已收口事实 | 未完成的门 |
| --- | --- | --- |
| 战时联合现金 R0266 | [Draft PR #449](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/449) HEAD `e30ca8fb0ff2e19eb3a1e5170fd711525fd46356`，官方静态 CI、CLA 通过；[固定 WAR 诊断回执](<C:/Users/1/OneDrive/WAR/R0266-H3937-WAR-CASH-20260929/RECEIVER-STATUS-R0266-H3937-REGISTERED-WRITER-DIAGNOSTIC-v1.json>) SHA-256 `8DEDF2CE6E73478EAA9F6DEE4103705FE52DDE40A7ECBD6513424FA2BF94F8A3`。 | 已登记写入者仅覆盖子集；五项正式现金数值和期限仍为 `null`，`formal=false`。H3937 `selected_step` 是显式 `null`，不能生成动作报价或声称费用为零。来源现金、最低储备政策及同帧正式回件待收。 |
| 可复用退出决策 H2743 | [Draft PR #448](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/448) HEAD `3841f830a0511c65f99043571f779c953f32ecae`；默认关闭的旧休战槽只读候选，普通与 `-O` 各 6/6、精确 EXE 校验、静态 CI、CLA 均通过。[WAR 追加回执](<C:/Users/1/OneDrive/WAR/H2743-EXIT-READONLY-V3-20260928/LOCAL-RESPONSE-EXISTING-TRUCE-CANDIDATE-PR448-20260929-v1.json>) SHA-256 `3E442ADA57DFCBF1343B6C913C3130C32CE601DD16001EE47B92B4D7967EA7E2`。 | 新 DLL / C++ 测试未构建，未实机读旧槽；投降后的休战期限、FP2 实际付款、完整效果与正式退出动作均未知，`complete=false`、`action=null`。不直接导致当前第 36 turn 停顿。 |
| R0368 军队角色依赖 | 源码候选分支 `research/r0368-actor-army-role` HEAD `4996e2763afa6185b7cbf590268b0e601c76983e`，独立静审 GREEN，普通与 `-O` 各 23/23。[WAR v6 回件](<C:/Users/1/OneDrive/WAR/NW-ACTIVITY-R0368-ARMY-ROLE-DEPENDENCY-20260929/RECEIVER-RESPONSE-NW-R0368-ROLE-QUERY-REVIEWED-SOURCE-v6.json>) SHA-256 `F7D3E8D11FFA3F8C113A9739AE66AD574EDE2C73FAB34C363C546BA914D4A87B`；旧 v4 为 RED。 | Release attempt001 因屏幕优先中断，约 15/915；[停机回执](D:/ck3-research-artifacts/r0368-role-build-stop-001.json)证实编译进程退出。attempt002 未启动。新独立构建、CTest/JUnit、DLL/injector 配对和暂停帧角色实测均待做；角色与安全卸任未知。 |

H2825 围城只读分区和战俘去留查询此前已交付，不应重新列为欠项；其消费仍须遵守对应同帧验证合同。

## 第二期战争视频

目标六章约 **29 分 50 秒**，分镜与事实核对在 [Draft PR #451](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/451) 及 `promo/ck3_native_war_ai/episode-02-battle-second-half/`。目前 13 个候选窗口为 6 个严格 RED、7 个待审；已认证 clean span **0 秒**，完整人工 1× 审阅 **0 次**，没有可交付的第二期成片或 OneDrive 上传。固定九窗的 `627.033` 秒只是条件性缺口，新终局支线补拍估计可达 `767` 秒，均不是已取得素材。

E2-04 d06 精确 UI 来源门源码 `5629d147f` 静审 GREEN，普通与 `-O` 各 9/9；[a02 无启动准入](D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d06-knight-preflight-20260929-a02/ck3-output/preflight.json) SHA-256 `EACE028F6AD8ACBEF29004FFF833722F82DF3E383C9814BFB6C1467C49C76488`，`ck3_started=false`。a03 Release [构建清单](D:/ck3-research-artifacts/e2-04-d06-current-knight-release-20260929-a03/candidate-manifest.json) SHA-256 `F8B1CDE428E14B3C20ED62D29C50B8A337C5E3E40D5F7E8E608017FE9A362CD9`；DLL SHA-256 `9B6EB4E8E77AB5EF8DFE211F5A2FAF20DC42A912887874E5D836C659DD75F1FE`，injector `90078D708C74F05FEDB29D6AA232902E3230282F48D32D6361742A797EF81735`，Release / CTest / JUnit 静态通过。第二会话操作器最终提交 `a4e180a8998e631397733e6161f36c31bd8ec89e` 独审 GREEN，普通与 `-O` 各 7/7，**尚未合入 #451 或实机执行**。#451 远端当前 HEAD `34239889eeefe04111d38f8dcfa06fbf3ffde8da`，其已有 CI / CLA 通过；合入任何后续源码后须为新精确 HEAD 重做准入。当前骑士数值、GUI 与可用画面未知。

E2-06 d11 a05 无启动准入保持 **RED**：a03 DLL 构建时 managed phase trace 为 OFF，缺必需 BEGIN / FINISH 标记，CK3 未启动；[RED 原件](D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-06-d11-recap-preflight-20260929-a05/ck3-output/entry-failure.json) SHA-256 `E75304606060417C012AD71DD372534019D6DEAAC85843731EB836347209F1A8`。修订静态门 `D:/w/e206_r0107_triage` HEAD `6eda3676794711a571b01a167015af855ad388c1` 已独审 GREEN，普通与 `-O` 各 9/9；[a04 构建脚本](D:/ck3-research-artifacts/e2-04-d06-current-knight-release-20260929-a04/build_release_candidate.py) SHA-256 `C822C4E1042CA48D089062342F913803FCD823669BA440CB8E69DFBBE6EE31F9` 已准备但 **Ninja HOLD，未运行**。没有 a04 DLL、CTest/JUnit 或新 no-launch / live 结果。接手后必须先完成新配对构建与独审，不能用旧 a03 DLL 去掉检查后重试。

宣传工具链本轮核对时最新正式 wheel 为 `xar-promo-toolchain 0.2.1`、SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`；这是 2026-09-29 11:44 UTC 的查询结论。接手者开始新 run 前仍须重新查最新正式 Release，按 `AGENTS.md` 更新精确 wheel 与解释器验证。所有旧 run、RED、原片和中间资产保留，不覆盖。视频将来仅在完成机器审计、人工 1× 对精确字节签核及获得成片后，按既有授权把**指定单个视频文件**放到 `C:/Users/1/OneDrive/CK3-War-AI-20260923/`；本次没有上传。

## 协作入口、机器状态和接手顺序

- WAR 固定交互目录是 `C:/Users/1/OneDrive/WAR/`，不再请项目所有者转述。最后只读 intake 快照 `D:/ck3-research-artifacts/war-intake-20260928/intake-1250.json`，对应 `origin/master=f9e1f05a6a891467c60a02e2b2cc776438544042`；截至 12:47 UTC 无新增 WAR 请求或来源回件。返回工作时先重新同步/核对 request、response、source ACK 和同帧消费验证，再排优先级。本轮停止轮询；`D:/w/.codex-task-bus` 的 `war-onedrive-intake-20260928` 已置 `done`、无资源。
- H3937 a05 supervisor 报 `ck3.exe`、`obs64.exe` 均退出，额外进程清单未见 `ffmpeg.exe` 或 injector；任务总线 `war-h3937-combined-readonly-live-20260929-a05` 于 seq `2407` 置 `done`，`resources=[]`。不留屏幕占用。原始录像、截图、RED 及所有外置 attempt 不清理。未来每次受管实机都重新取得唯一屏幕租约与当次新鲜 Steam“离线模式”原图；旧图只证明旧尝试。
- 下一位优先处理 **R0271/H3937 原生冷载语义快照缺失**，取得真实同帧围城参战集合或符合风险合同的可恢复方案；没有该证据，Robert 正式续跑继续停。随后补 R0266 的实际现金与储备来源、R0368 原生角色实测和 H2743 退出效果闭环。第二期视频在独立资源窗口继续 d06 / d11 准入、补拍、剪辑、审计和人工审片；不要把静态门、无启动预检或现有原片误写成成片验收。
- 主仓 `D:/workspace/ck3_eternal_recurrence` 的 `master` 当时落后远端且有其他任务的未跟踪 `detours.installed` 与 `docs/coat-of-arms-fit-artifacts/epsilon-*`。本轮未碰这些文件。各 Draft PR 和隔离 worktree 的 HEAD 是各自边界，不得混成一个已经在 `master` 的实现。
