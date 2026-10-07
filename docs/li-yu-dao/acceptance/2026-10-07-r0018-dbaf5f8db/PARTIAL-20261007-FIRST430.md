# R0018 首个 430：PARTIAL 快照

本报告仅冻结到真实 request 13 完成时刻 `2026-10-07T02:25:53.045489+00:00`。它是 append-only 的 **PARTIAL，整体业务 NOT_GREEN**；后续 runtime 结果应另建报告，不覆盖此快照。不赋予 formal、新 T、C3 或 I4 信用；正常退出在本截止点为 **UNVALIDATED**。

当前 cold 实例为 PID `5920`、connection generation `1`、角色 `31254`、session `9cdca47579f54d3191efdecdb7400374`。运行源码、编译 lineage 和 SDK profile 均冻结到 `dbaf5f8db2067419838b814e278d962f428dc33c`，profile SHA-256 为 `0189ab2c8ec4135b8b007d4a8254cb859ae970e5fe852de75015ca9846e3c404`。文档修复提交 `3475ba2eac392221321c9c83e62f918fd3339db1` 的 CI 成功属于文档提交；本实机输入没有以它重新解释。源码 export-002 与实际 SDK metadata 的原 JSON 随包保留；metadata 的 28 项工具清单属于既有源绑定事实，不替代业务验收。

既有 baseline author 的 `RESULT.json` 记录 `game_calls=0`、一次原保存正文解析；`STATE.json` 和 `TYPED-PROTECTION.json` 已产生，后者有 `87` 项保护检查并记录 `protection_checks_match=true`，即既有 87/87 匹配。此处只归档已经解析的 JSON，没有再读取存档正文或重跑 reader。STATE 的旧 schema/source-head lineage 和 `INCOMPLETE_NATIVE_QUALIFICATION` 原标签保持原样，不能把 baseline 保护检查改写为正式回合通过。

已完成的纯政治对照包含 `7` 个政治 title，`complete_political_AST_matches=true`；原报告 SHA-256 为 `86f1c86a25aa8a9b95830408e4f23793e57213b261b098940b7eebb438d8b5fb`。它证明原 0240 与 initial cold 的完整政治 AST/holder 对照，不能推断此前没有发生过动作，也不提供 C3/I4 或正式信用。

request 12 的实际 native query 确认事件定义 `lyd.430`、instance `101`。request 13 通过官方 SDK 执行 `select-event-option-3`，native option index `2`；原 SDK `isError=false`。native 原回执记录 `native_gameplay_postcondition_verified`、`postcondition_verified=true`：旧 instance `101` 关闭，后续 active event 为 null，revision `4 → 5`，同一 PID/generation，日期保持 `53144712`。这确认修复后的 native dispatch 在首个 430 的实际 SDK 路径上完成了事件后置读回，范围只限本次选择。

本次 native before/after 钱包保持相同：gold raw `104300000`、prestige raw `220000000`、piety raw `315000000`，scale 均为 `100000`；stress 仍为 `0`。它不证明 commit fee、完整制度生命周期、C3 或 I4 已闭环。

首个 430 的 native JSON SHA-256 为 `50ebcbfacd880194e643366ac11b4b2486befe5933260f5d5744459ed7792132`；对应 ROOT request `RESULT.actual.json` SHA-256 为 `9015ecae425047be51e0a18b7d0dca2bc152dc4a039bf97546dcfb3294f5f00b`。本报告依据 actual native 后置结果，不用 request/enqueue ACK 替代成功。

早期失败分别保留其层次：`root-preflight-001/RESULT.json` 原 `RED` 为 `R14 identity path changed`，发生于启动前路径身份检查，原文件记录未创建游戏、未注入；`root-preflight-002/RESULT.json` 后续仅完成 `ACTUAL_NEW_FORMAL_PREFLIGHT_ONLY_NO_GAME`，不是实机业务通过。`root-profile-request-001/RESULT.json` 原 `RED` 为 `ROOT must already have actual game HWND foreground before freezing`，属于 profile 冻结前的现场前台条件，不等同 native dispatch 故障。baseline 原 RESULT 还保留 `original_outer_exit_code=1` 和 compiler Defender `settings_failed` 的既有事实，不外推为全局 native build GREEN。

首次 source export-001 的指定位置没有可归档的直接 JSON 正文。按 ROOT 交接，原 stdout 保留在外置工具历史；本包将该项列为“未归档”，不猜正文、不补造错误或评级。

本包的 [FIRST430-PARTIAL.original-json.zip](FIRST430-PARTIAL.original-json.zip) 只含选定的现有 JSON 原字节；[FIRST430-PARTIAL.inventory.json](FIRST430-PARTIAL.inventory.json) 给出每个成员的原路径、SHA、层次与冻结 HEAD；[FIRST430-PARTIAL.facts.json](FIRST430-PARTIAL.facts.json) 是明确标为 PARTIAL 的摘要。没有保存二进制、存档正文或全量运行树；原外置 attempt 不移动、不删除、不改写。所有进一步结论仍须由 ROOT 在原 live 链上取得。

报告代理只做现有 JSON 读取和独立 worktree 的 create-only 写入；SDK/game/process/main mutation、retest 和 CI poll 均为零。ROOT 持有当前 live 执行链，报告归档与其并行；日报拓扑字段交由 ROOT 合并，避免编辑冲突。
