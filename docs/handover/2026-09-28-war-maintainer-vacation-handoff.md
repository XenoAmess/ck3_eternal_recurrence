# 战争维护交接：2026-09-28

本次按项目所有者要求，收完手上的 H2825 战俘去留请求后停止领取新工作。本页供下一位执行者从仓库和外置证据继续；它不是实机 GREEN 或囚犯动作授权。

## 已交付的可复核事实

- `WAR-ROBERT-H2825-SIEGE-PARTITION-20260928` 已在 master 交付只读规划器的围城兵力分区复验，见[正式响应](../autonomous-agent-progress/coordination/war-requests/responses/WAR-ROBERT-H2825-SIEGE-PARTITION-20260928.json)和[同源实机记录](../ck3-native-ai/h2825-readonly-partition-live-2026-09-28.md)。`native:3`、native revision `3`、日期 `53217624` 下，玩家军 `83886367`、围城敌军 `50331920`、场外敌军 `83886484` 各有明确位置。规划器完成五项只读查询，随后选择第一跳预览；没有发出行军、战斗、投降或日期推进命令。V3 当帧仍报 `planner_usable=false`、`active_attack_allowed=false`。
- H2825 精确源存档、driver、完整 sidecar、原 DLL 与配套输入已从 OneDrive 选择性同步并校验，外置只读副本在 `D:/ck3-research-artifacts/war31-h2825-20260928/source-verified-01/`，清单与哈希见[传输回执](../ck3-native-ai/h2825-onedrive-exact-input-2026-09-28.md)。`attempt-04/live-plan-readonly-04/read-only-result.json` SHA-256 为 `23558C5FAEA9A5C2A81154D3CDFE8AF2E2845F2DBAEF209710E0471CE8AC5C74`。这是独立只读复验；本机使用的 R0221 injector 与原 R0265 injector 不同，不能说整个原二进制组合完全一致。
- 同次正式只读查询确认 WarID `16777231` 的 CB 是 `individual_county_de_jure_cb`（database index `17`），玩家 `29829` 为 defender、主战分 `-24`。三名玩家所押囚犯 full CharacterID 为 `34486`、`44484`、`47028`，其中仅 `34486` 的 House 可读为 `2370`。这场战争对三人均不触发 FP3 `free_house_member` 分支；一般 PoW 配对仍需新查询实机读回，不能判为否定或零。来源、原版语义和接口见[战俘文档](../ck3-native-ai/h2825-prisoner-war-retention-source-2026-09-28.md)。
- 新增独立 `query-war-prisoner-release-pairs-v1-<WarID>` 原生只读通道，绕开已禁用的 loaded-effect preview，双采样读取双方参战者、主帅及前三继承候选、jailer→prisoner 通用效果配对；Python 驱动仅在暂停战局暴露对应步骤，并严格校验原生 revision、日期和完整扫描。source join 另把通用 PoW、FP3 House 分支、当前终战可达性分开；没有释放动作。源码已在 master `b164b0a3707c189b5cbb77dcc3601676445fd6ed`；四个改动过的 C++ 对象编译通过，Python 聚焦及战争终战合同测试 `14 passed, 27 subtests passed`，`validate_python_only.py` GREEN。**这项 producer 尚未完成整 DLL 链接，也未用新 DLL 对 H2825 实机读回。**静态交付的精确结论是 FP3 `not_applicable_cb`、一般 PoW `unavailable`，未计算赎金或三人完整扣留价值。

## 接口与接手条件

- 需求源：[WAR-PRISONER-RETENTION-H2825 请求](../autonomous-agent-progress/coordination/war-requests/requests/WAR-PRISONER-RETENTION-H2825-20260928.json)；交付状态以相应[响应](../autonomous-agent-progress/coordination/war-requests/responses/WAR-PRISONER-RETENTION-H2825-20260928.json)为准。非战争消费方只可在新交付进入 master 后，用**同一个** `snapshot_id`、public/native revision、日期、玩家 ID 与 episode 的私有囚犯集合做 join；帧漂移即 `unavailable`。候选配对不等于终战按钮可用或已经释放。此请求也不授权任何囚犯动作。
- 若后续需要实机证明一般 PoW，必须用新桥接 DLL、受管精确 source pair 创建**新 attempt**；先领取 `ck3-screen:acquired`，依据当次新鲜 Steam 画面目视确认“离线模式”，按仓库桌面恢复合同保存回执。仅查询 `query-war-prisoner-release-pairs-v1-16777231` 及相同暂停帧的囚犯/终战选项，记录原始 payload、结果、SHA 和退出/存档未变证据。不得恢复曾导致崩溃的 `query-war-termination-exit-terms-v2` loaded-effect preview。当前没有这项 live 证据；下一位不得把编译通过当作实机通过。
- 历史 WAR31 匹配检查点的一次投降授权只属于当时明确匹配的检查点，**不外推**到 H2825 或其他战争。其他战争、击杀/增援/终局研究与视频不是本次临走前新增范围；是否继续以届时的任务需求和证据为准。

## 机器与仓库边界

本次 H2825 只读复验在 CK3 已退出、save 哈希不变后结束，屏幕独占资源已释放。最后一次目视 Steam 离线截图是 `attempt-04/steam-desktop-recovery-07/probe-1/steam-moved.png`，SHA-256 `5F4AF9C4A71B61D6E96AA8A2469065A04DEC43A066F336FC4E3A6B7CD8BA407D`；它只证明**当次**离线，未来启动不能复用。外置 `D:/ck3-research-artifacts/war31-h2825-20260928/` 保存各 attempt 原件，不要清理或覆盖。仓库里现有的 `detours.installed` 与 `docs/coat-of-arms-fit-artifacts/epsilon-*` 是其他执行者的未跟踪文件，本次提交未触碰。

本机任务总线 `ck3-next-war-battle-ledger-research-20260926` 已设为 `waiting`，不持有屏幕资源；其下一步指向本交接页。没有后台 CK3 采集或编译流程留给接手者。

跨团队请求以 [`war-requests/README.md`](../autonomous-agent-progress/coordination/war-requests/README.md) 为准：`delivered` 只是战争维护者交付，消费方需单独写 `verifications/` 的真实匹配验证。接手时先 `git fetch origin master`、核对最新 request/response，再在隔离工作区复现；Steam 默认离线，OneDrive 客户端仍只允许已选择同步目录及精确文件，不能为了取其他资产启动无约束下载。

## 2026-09-28 续办补记：H2825 attempt-08

上文“尚无新 DLL 实机证据”及一般 PoW `unavailable` 是本页最初交接时的状态，保留作历史记录。续办者在独立 attempt-08 以新配对 DLL 从同一 H2825 checkpoint 冷恢复，完成通用 PoW、私有三囚犯集合及正式终战选项的同次暂停帧只读 join；三人 `34486/44484/47028` 均为 `generic_pow_pair_status=not_in_pairs`、`fp3_house_member_status=not_applicable_cb`。原始哈希和门禁见[attempt-08 精确摘录](../autonomous-agent-progress/coordination/war-requests/evidence/WAR-PRISONER-RETENTION-H2825-20260928.attempt-08-same-frame-green.json)，结论与保留边界见[更新响应](../autonomous-agent-progress/coordination/war-requests/responses/WAR-PRISONER-RETENTION-H2825-20260928.json)及[战俘文档](../ck3-native-ai/h2825-prisoner-war-retention-source-2026-09-28.md)。

当前只有投降选项可用，白和平与胜利不可用；CB 专用终战条款仍不可观测。三人的独立无条件释放预览均可发送且自动接受，但未提交释放、投降或其他游戏动作，未推进日期。较早 attempts 05–07 的 RED/部分证据仍保留；本次新响应和摘录须进入 `master` 后才可由非战争消费方正式引用，其 `verifications/` 仍由消费方另行填写。
