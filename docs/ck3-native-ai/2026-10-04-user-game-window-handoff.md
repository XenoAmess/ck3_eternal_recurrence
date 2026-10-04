# Robert campaign: user game window handoff

Recorded 2026-10-04, Asia/Shanghai. The user requested CK3 for personal play.

## Desktop and runtime ownership

Root normally stopped its isolated R0028 CK3 process 57052 at 06:41:01.922114 UTC. Managed controller session 97602 exited successfully. All SDK sessions are closed. The user owns the game window now. Do not start CK3, rebind, run live acceptance, inject, or send game input until the user says personal play has finished. Offline files and reports may continue.

This temporary desktop handoff does not restore any nonwar constraint. Combat and religion remain authorized. Keep independent work parallel and use minimized background instances when live work resumes.

## Last normal saved campaign

- Robert 29829; episode `native-29829-2bc2d599f7f9`; ordinary campaign, XAR off, no pact.
- R0028 canonical `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0028`; execution `fe1155b8-cbee-447c-bc9c-126703932f52`.
- State: `Z:/ck3_mod_rewrite_process_assets/g2-robert-mainline-12003-v55-20261004/state`.
- Normal checkpoint h7123, raw date 53251464, 95107672 bytes, SHA-256 `5fa096c5a155a14ae5a88e4e46c511584e6474b8b9eb21ffd158c9c9ff062ee4`.
- Last closed capture: `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v56/actual-r28-gather-finish-pre-stop-sway-four-01/result.json`.
- Saved calendar 4464; resumed 1311; October 4 increment 439. Eight new normal days each closed and saved. Natural succession 0; G2 5/8 and NW2 2/4 remain unchanged.

## Actual current military state

War 129 ended after one white-peace offer and three ordinary days, independently verified absent and normally saved. The reply type itself was not observed. Subsequent standdown completed.

Event 25 `bookmark.1071` option 2 started attacker war 117440524 against 35991. The three port objectives are 470, 3711, and 472. The source AI tree was frozen before the choice. Current score is zero.

- Army 184549452: actual 3000/3000, 24 regiments, regular at capital 2619; supply 99.9985/100, monthly change -4.54545, attrition zero.
- Army 301989997: eight-day gathering completed; actual 3681/3884, 41 regiments, regular at 2619; supply 300/300, monthly change -4.54545, attrition zero.
- Enemy 268435597: actual 2459/4702, 41 regiments, moving from 510 toward 470 along the observed 12-province route.
- The two player armies remain distinct. Summed current strength 6681 is not a merged army.
- Commander 34867, quality 28, was the highest current legal candidate and was assigned to 184549452 with independent readback. Robert's higher quality 33 had CanAssign=false and no published reason.
- Army 184549452 has a verified route preview 2619 → 8651 → 1038 → 472, but no movement order. Target supply limit 4025, initial used supply zero; no published ETA or embarkation quote.

Original Sway 134217986 against 34333 remains active. The four pre-stop queries are archived at raw date 53251464: continuation true, chance 45%, three attached empty rings without gaps. The previously verified beneficial +25 loop remains qualified; whole-scheme lifecycle and natural succession remain pending.

## Offline preparation and next live entry

Combined source `f3f365c53d3708f520e0142a1b81a484b0c31df3` is published and frozen in `Z:/g61`. It includes current-person/knight identity, primary levy damage, the Python P1 frozen tick adapter/runner, and the actual-build current cash reader.

The single all-four-target strict Release build, jobs 64, compiled successfully in 77.746665 seconds. Actual build plan, CMake cache, and compile definitions prove 115 flags, 65 on and 50 off, including WAR_CASH. The earlier stdout count 64/51 came from baseline preparation before the selected flags were applied. Official exact-head static CI run 37183133742 succeeded.

Binary freezing hit a real inventory KeyError for generated `white_business_exact_pins_v1.inc`. The offline repair must register the actual generated compiled input with its own hash and generation provenance, then freeze the already successful build. No recompilation is needed. R0029 has not been allocated, prepared, rebound, or launched.

After the user releases the game: complete the freeze-only repair; render the latest full saved pair and ten streams once; perform official prepare/verify/stage, retire R0028, rebind to the normal saved campaign, and preflight. Allocate and launch the next minimized instance. Capture the original four Sway queries before advancing, then make the one paused current-cash query. Continue the port war using actual army and supply state. New battle-loss fields and P1 tick remain static-ready until a real current main battle frame is sampled.

## 2026-10-04 R29 实际部署收口（窗口归还后）

用户游玩暂停已按历史事实保留；用户随后明确玩完并授权恢复 CK3 实机。Root 已将 R28 正常收口并于 07:02:25.249911Z 标记 superseded，R29 已实际启动。此记录复用 Root 已闭合的部署与查询回执，不读取正在运行的行军包。

候选源码为 `Z:/g61` / `f3f365c53d3708f520e0142a1b81a484b0c31df3`，四 target Release `/W4 /WX`、64 jobs 全构建实际 GREEN，77.746665 秒，115 flags / 65 ON / 50 OFF。97838 首次的 `.inc` inventory `KeyError` 是 freeze harness RED，原失败保留；native 编译已成功，随后 `ROOT-FREEZE-GENERATED-INPUT-REPAIR-RESULT.json` freeze-only 修复 GREEN，未重复编译。正式 CI `37183133742` / job `111379532891` success。DLL 9,108,992 B，SHA-256 `8545934beef798d95d4d63c2c8b6ec1fa1e01ba0adfa367073c4667ecb819dc2`；manifest 266,582 B，SHA-256 `d2586fe99c2a555db61b44fe054b90c864cb773f045da34ad637330cd99dcf66`。

实际 run 为 `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0029`，execution `69c953da-34f4-4d8d-a3a4-5c94bb1987e8`；allocated `07:04:44.815380Z`、launch-started `07:04:45.122017Z`。managed controller `54355` / game PID `38372` active。10 文件 stage、rebind `54057` 与普通战役恢复均已完成；环境 SHA-256 `898b68004f6b1173c49a5db049515919e68fd35012ed455c1570e84e08cf8a1b`。cold SDK `99233` GREEN，完整 history `7124` / save anchor `7123`，没有把正常恢复增加的 history 记成自然日。

原四 Sway、现金、指挥官与 route preview 的 SDK `53439` 已 CLOSED GREEN。其正常 SAVE 为 h`7127` / raw date `53251464` / 95,107,270 B / SHA-256 `a265c124196a8e289ef0512ab6721a45ea69654b13a25eb9857a93d42dc569d9`。current cash 实际 `available`、各 readiness 均为 true，现金只读观测达到 production-live primitive；current-person / loss / P1 的 ongoing live 资格仍待真实接触，不能仅凭新源码、部署或 schema 记成战斗 loop 完成。

本次部署记 0 日，闭合累计 `4464` / resumed `1311` / Oct4 `+439`；自然继承 `0`，G2 `5/8`，NW2 `2/4`。Root move `98187` 已 CLOSED GREEN，随后 8 日行军 SDK `14458` 仍运行；此处不消费该包、不增加行军日数。来源为 Root 既有回执与外置 `runtime-preparation/v56` artifact；当次部署闭合不依赖下一批 P2 / cadence 候选，也不将它们冒充当前 f3 能力。


## 2026-10-04 R30 实际部署收口（v57）

本条接续已采用的 R29 收口；用户此前游玩暂停已解除，R29 按实际回执保留为 superseded。R30 的 native / Python 统一冻结于 `Z:/g62` / `d1b7f18d200cffd302815a05a12c1d3e958ab2de`，游戏 exact build `1.20.0.3`。后续 g38 文档或源码 head 不是当前 active frozen source，不改写本次身份。

v57 同一 exact head 的四 target Release `/W4 /WX`、64 jobs 全构建 GREEN，81.955581 秒；115 flags / 65 ON / 50 OFF，562 TU / 559 unique / 1088 compiled inputs。DLL 9,148,928 B，SHA-256 `91cc62d12eb7839582254fce443bf5dea8c5518402867f2cab28b27cbc6938b7`。正常 prepare 已收录 1 个生成 `.inc`，freeze supplemental 为零，复用同次 deps，没有再次 repair 或编译。官方 exact-source CI run `37188480128` success；只引用 Root 的 `runtime-preparation/v57/ROOT-EXACT-SOURCE-CI-RESULT.json`，不重读或重验。

Root 的 officialprepare / verify / stage ten streams / ordinary rebind / preflight 均实际 exit0 GREEN；R29 于 `2026-10-04T08:30:03.032047Z` 标记 superseded。R30 allocated `2026-10-04T08:32:19.319959Z`，launch-started `08:32:19.744377Z`。实际顺序继续采用 normalstop before officialprepare，并等待 rebind 完成后 preflight；失败历史随十条完整流保留。

实际 run 为 `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0030`，execution `72457e9f-d8f2-4350-b08c-0f5683d37e5b`；managed controller `69340` / game PID `120956` active。cold SDK `73336` 与原四 Sway / health / targets SDK `59491` 均已 CLOSED GREEN。环境 SHA-256 `b17543f45334043db6725c4183ae3ab2f59fa7645de4ec7443ffe303b7eb6a29`。

部署后已闭合正常 SAVE 为 h`7257` / raw date `53252424` / 95,804,561 B / SHA-256 `42fc6ddd48326ce2b1a07f32aeba416cb82b543efe3a4925bc905c4c65096ad6`。source anchor h`7252` / raw date `53252424` / 95,804,821 B / SHA-256 `8c8557def103f73519387fecd006b23336d1e3ac659249af7f468dedbb1c21fc` 仅作为恢复来源；不替代部署后最新保存。

原四 Sway completion / execution / termination / invalidation hooks 保持 FullID `134217986` / generation `8`，新 PID 冷读已完成，没有重发 Start。pre-stop 独立存档为 current continuation、Can=true、chance 55%；三 rings 均 `0/0`、empty、gap=false。health 当前三条 CArmy soldiers 为 player `3000`、new player `3693`、enemy `2459`；另两个 PublicCUnit 行返回 `native_carmy_not_found`，只记录 missing native，不据此推断 shadow 或舰船身份。

新 movement observer 已有实际只读 primitive：first edge `5.48572` days 是当前预测耗时，不是已经推进的自然日。部署闭合 cut 为 h`7257` / 累计 `4504` 日，部署记 `0` 日；h`7252` 仅为来源存档锚点。Root 的后续 6 个 normal bounded days 已开始，此文档 lane 不消费、不记行军日数；没有新增 P1 或自然继承信用。原自然继承 `0`、G2 `5/8`、NW2 `2/4` 的历史事实保留；新源码、cold GREEN 和只读字段不冒充完整 OODA 或自然继承完成。


## 2026-10-04 R31 实际部署收口（v58）

native / Python 统一冻结为 `Z:/g63` / `df6e5039a9dfa167c9f732a241cd60ca463df362`，exact game `1.20.0.3`；冻结时间 `2026-10-04T10:53:19.136324Z`，dirty `0`。四 target Release `/W4 /WX`、64 jobs 单次全构建 GREEN，75.388693 秒，115 flags / 65 ON / 50 OFF（WAR_CASH ON），563 TU / 560 unique / 1090 inputs。生成 `.inc` 沿正常 inventory 收录，没有再次 repair 或编译。官方 exact-source CI run `37196371137` 已 completed / success，HEAD 与本次 df6e 相同；只引用 Root 已给的 `runtime-preparation/v58/ROOT-EXACT-SOURCE-CI-RESULT.json`，资格限官方静态 CI，未重读或查询。

DLL 9,154,560 B / SHA-256 `ef9e2711b32d110b07ad07aabb39f6e14579781b2064eabe4c1678ed2e8ac449`；manifest 267,070 B / SHA-256 `8c79ed66a5fc42ed59a5463c81bda073c9f83d0938a30cdbb483b1b4abe88eb3`。开发树中后续 pure horizon 工作不在本次 freeze，不作为部署 pursuit slot 与 siege levels 观测的前置条件。

R30 于 `2026-10-04T10:55:03.469006Z` normalstop，managed controller `69340` exit0；`2026-10-04T10:59:30.989016Z` superseded。单次 renderer full history/save h`7369` 与十条完整流 GREEN，随后 officialprepare / verify / stage10 / ordinary rebind / preflight 均 GREEN；维持 normalstop before officialprepare 和 rebind 完成后 preflight。环境 SHA-256 `ac949dbd42df143e5e1c6542a77b3edca71833a01864f677f06ecd7dde31abb6`，driver SHA-256 `8b7081d8a982041fd251ec54286890339e2d1b2545257eae2b2bda464a29e533`。

实际 run `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0031`，execution `0754bd1b-c2d6-401f-838f-f828169b151f`；allocated `2026-10-04T11:01:02.476890Z`、launch-started `2026-10-04T11:03:21.179943Z`，managed `84135` / PID `73976` active。cold SDK `54908` CLOSED GREEN，full history `7370` / save anchor `7369`；Robert 29829 alive、原 ordinary episode 延续，cold 恢复记 `0` 日。

首批冷读后正常 SAVE 为 h`7373` / raw date `53253264` / 96,371,960 B / SHA-256 `89e2f2afca6a96d30ba433f860d3ed42514f989691a5b82bd1e730e0192f6948`。来源 h`7369` / raw date `53253264` / 96,372,333 B / SHA-256 `f71dd8fa943c7d9f2d0e6630dbd4f4aac64713622d634d2c3c5ab17333837213` 保留为 source anchor。原四 Sway / health / levels SDK `64082` 状态为 `CLOSED_GREEN`；此 lane 只采用 Root 闭合字段，不读取 raw。

Root 唯一消费投影 `g2-resume-20261004/r29-route-actual/r31-first-phase-levels-once/ROOT-DELIVERY.json`（Root 给定 SHA-256 `fb9e3ff871c4b17ddc0f5a1a878e4ca65f985c16f97bc3a46f4dfab507de7030`）确认 native revision `2` / public revision `2` / generation `2` / date `53253264`。实际 `breach=0`、`starvation=0`、`disease=0`、`desertion_count=1`、`stalemate=0` 均存在，达到 production-live primitive；合法零值已区分于 missing。`prepared_enum=5` 是 actual no-due sentinel，不是未来事件。旧五项 literal 为 `D126385/Q L1800000/Q preparedL0 legalzero/counter12/CanAdvtrue`；当前 cache `projected_work=4420875` / `counter=13` / `missing=[]` / `stateadaptermissing=[]`。这些是实际只读投影，没有执行新的 nextday 或 event。

本次纸面切面明确采用已确认的 cold SDK `54908` / full history `7370` / source anchor `7369`；累计 `4539` 日，部署新增 `0` 日，自然继承 `0`，无新增 P1 信用。原四 FullID `134217986` / generation `8` hooks 已随首批 SDK `64082` CLOSED GREEN 完成新 PID 冷读，没有重发 Start；pursuit slot 修复仍按实际后续 pursuit 样本独立验收，不将 native 新源码或只读 primitive 冒充完整 OODA。

本条状态为 `DEPLOYMENT_READY_OBSERVATION_CLOSED_PRIMITIVE`。最新 SAVE 与 levels 采用 Root 最终字段及唯一消费投影，只读状态达到 production-live primitive，不代表下一日、未来事件或完整 loop 已执行。
