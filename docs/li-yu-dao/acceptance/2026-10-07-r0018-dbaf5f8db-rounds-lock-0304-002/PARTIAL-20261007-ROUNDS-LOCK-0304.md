# R0018 两轮自然 NO、SAVE72 恢复及 R3 未决锁：PARTIAL

本追加快照的实机截止点为 `2026-10-07T03:04:00Z`，冻结运行来源仍为 `dbaf5f8db2067419838b814e278d962f428dc33c`，PID `5920`、generation `1`、session `9cdca47579f54d3191efdecdb7400374`。整体 **NOT_GREEN**；没有 formal、新 T、C3 或 I4 信用，正常退出在本截止点仍 **UNVALIDATED**。ROOT 后续正常 close 应另写 CLOSED 追加记录；本文件不覆盖首个 430 报告，也不吸收截止点之后的退出结果。

两轮原 STATE 中 rite `169` 的 school 均记录 `total=2`、`yes=1`、`signed=0`：人类 `31254` 为 `was_player=1/player_yes=1/vote=1`，NPC `65865` 为 `was_player=0/vote=0`，保留自然 NO。这里“2/1”指选举人数/YES 数；R1 的原 serial/nonce/phase 为 `1/2/2`，R2 为 `2/4/2`。两轮尚未够 quorum，pending 本来不是正式通过。

两份 `TYPED-PROTECTION.json` 均有 87 项检查且 `protection_checks_match=true`，只提供本阶段保护信用。两份 STATE 原 `observation_checks_match=false`、`assessment=OBSERVED_CONTRACT_MISMATCH`、实际通过字段 null 均保留，不以 typed 87 项替换整体原评级。R2 STATE 原 SHA-256 为 `13062d7242beaf1897c23de67f9425d68d7fd43b3b46ab089968439353eecf98`，typed 原 SHA-256 为 `42f43a6219162ace5ee26f16d16a2a25343d7e679730e6ef1ed2ea8009628707`。

`formal-r1-cancel-001` 与 `formal-r2-cancel-001` 的实际结果均为 `EXPLICIT_STEP_ACTUALLY_COMPLETED`；四次调用的原 provenance、最后 native confirmation 和实际 final snapshot 已保存。取消后的 frame 分别为 revision/native `16/15` 与 `25/24`，active event 均 null，仍是同一 PID/generation。取消完成不等于制度提交或完整产品通过。

SAVE72 的原 SDK 保存与 G2/G3 链保持既有来源。首次 source002 materializer 原执行 exit `1` 保留在 `r18-root-B3-r2-pending-materialize-execution-20261007-001/RESULT.actual.json`，原 stdout/stderr 的来源与 SHA 也仍在该原 JSON 中。source cp003 仅补既有白名单中的一个诊断路径 `last_heartbeat.snapshot_observer_12002.last_read_ms` 及合同 SHA pin；原 `HOTFIX-SOURCE-PROJECTION.actual.json` 记录既有 native/save/G2/G3/SDK/descriptor 与业务 frame 检查未变。

后续独立 materializer002 已真实执行，exit `0`，RESULT SHA-256 为 `210d49c6f44f7fe4b14f43689948722a96ac90c5bb550fdae7c8475aecae428a`。R2 author001 已真实执行；执行 wrapper RESULT SHA-256 为 `06f50ab7f4f7a60be373222270e5186910768fe83c086857ca9a73bcd13c9c69`，其产生的输出 RESULT SHA-256 为 `78fa21f32367a29acccdebb18906a31e85b6ad343b210da9cb3109b1b966a64b`，输出原 `game_calls=0/save_body_reads=1`。两个 JSON 层次分别保存。这是一段保留同一 live PID 的纯 Python materializer/author 恢复；原 author 只解析一次已保存正文，本报告代理没有再次读取正文。不能用 source-only INDEX 的准备状态代替这些实际执行，也不能把恢复记为 formal 成功。

R3 的三次错误必须分层：

| SDK sequence | 原状态与 reason | 层次 |
| --- | --- | --- |
| 80 | `RED`；`_NativeCommandRejectedError: native gameplay step failed: exact_alive_paused_decision_action_binding_changed` | 首次 native 绑定校验在派发前拒绝 |
| 84 | `RED`；`BridgeUnavailableError: decision action already claimed with an unresolved result; no retry at any revision` | Python 未决 decision-action claim 锁 |
| 88 | 同上 Python reason | cleanup SAVE86 后仍有同一类 Python 锁 |

SDK84/88 的 `native-01.json` 文件名和统一 receipt schema 不能把 Python 拒绝变成 native 再次派发；此前摘要的“native 重复拒绝”层次表述以这里的原 reason 纠正。原 SDK envelope 的 `isError=false` 也不能覆盖内层 `status=RED`。本归档没有重新调用或尝试解除锁。

cleanup SAVE86 的原 ROOT RESULT SHA-256 为 `65caeb188cc601c3d650b9e68095487953af8bde311a1cefea6860ed3babe6c6`，保存成功后 frame 为 revision/native `26/25`；随后 SDK88 的 before frame 也是 `26/25`，仍返回 Python 未决锁。因此换 revision 或 cleanup save 没有在本次链上解除锁，不能补写为可重试或已恢复。

cp003 的原 INDEX SHA-256 为 `21b9a523efc42f86b9ca406d0cae80de268b4bd7bd8e27ed5de1fd620cd00c9f`，保留其最初 source-only 标签；materializer/one-body 的实际信用仅来自后续执行结果。capture004 的 INDEX SHA-256 为 `f0b8012f6b3e91ea7156253695a5ad0fa05e0f5296ebbcc8e5c5d6df733fa9c7`，仅是 future source preparation，**没有实际 capture**。这些源准备材料单独归档，不作为退出、formal 或新 T 的实际观测。

选定的既有 JSON 原字节收在 [ROUNDS-LOCK-0304.original-json.zip](ROUNDS-LOCK-0304.original-json.zip)，每个成员的原路径、SHA、冻结来源与证据层次见 [ROUNDS-LOCK-0304.inventory.json](ROUNDS-LOCK-0304.inventory.json)；[ROUNDS-LOCK-0304.facts.json](ROUNDS-LOCK-0304.facts.json) 保留上述原评级及错误层次。没有复制可执行文件、存档正文、全部运行树或整份源码；原外置 attempt 留在原处。

报告代理只读取现有 JSON，并向独立 worktree 的此新后缀目录 create-only 写入；主树、SDK、游戏、进程、存档正文、CI、重测及提交推送操作均为零。ROOT 当前执行链不因本包被重启或重解释。

首次报告归档把 author execution wrapper 的 SHA 错用于 author 输出 RESULT，复制阶段因此停止，原目录 `2026-10-07-r0018-dbaf5f8db-rounds-lock-0304/FAILED.authoring.actual.json` 和部分 ZIP 原样保留。此新独立后缀包改正引用层次，没有重跑 author、重复正文读取或改写任何 runtime 结果。
