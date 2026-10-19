# Native26 与新 SDK 的同场 cold 续行准备

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-19 UTC 源审；这是尚未执行的维护方案，
不是停 Game 指令或 cold 通过回执。原机器/响应时间和 SHA 固定在
[小来源索引](evidence/g2-m7-native26-cold-plan-2026-10-19.json)。M7 仍 `in_progress`，G2 仍 6/8。

## 当前可以复用什么

原 Robert `31254`、episode `native-31254-6271ac8cd441`、普通
`dynasty_continuity` 目标和 origin 保留，Game `214568` / birth `134368503807325674`。
`0150` closed 与 `0151/0153` MET 是 58 settled、累计 38 日、raw `53145240` 的历史锚；
154–156 的本地模板 pin 拒绝也是历史状态，不能当当前停点。最新自然 `0194` 的小型冻结
META 于 `04:35:29.426190Z` 记录：已有 **74 settled / 61 日 / raw 53145792**，
pending75/next195。194 的 existing-Sway 只读观察已发生，但后继双 callback 显示命名错误，
外层 SDK error，following ordinary dispatch 未发生。其只读前缀不等于整回合成功。
Root 正按原合同安排 194 精确清理，再到正常 saved/no-pending 边界；M7 不跳过 pending。

**最新已读正常 SAVE 是第 30 日的 `0142`，不是第 61 日。** 它对应 `0141` 暂停、无事件/
interaction 的帧，raw `53145048`、history index `91`、`68489298` bytes、SHA
`9321fd08c107079cf01dc8797e8a5c5006261b90a225a91dc8d9b503e4a4904b`，
driver replace 回执已核 save binding，但 scope 是 `WRITE_REPLACE_RETURNED_NOT_FSYNC`。
T0 的不可变 episode-seed 是另一个 SHA `381e832b…0aa88f4`，也不能用于保留当前进度。

因此按 Root 已定的自然、无 pending、正常保存边界维护：等现有 owner 清理本地 metadata、
正常取得覆盖当时实际日期的新 SAVE 和配套回执，再固定包。不能以 0142 或 T0 恢复冒充保留
61 日（当前相差 31 日）；本审计没有要求提前停 Game 或为研究另存一次。

Native26 已有同机器构建/离线资格：候选 `build/native26.dll`，`18442752` bytes，SHA
`eaee4443f083ae5055232b908fdb5c6555aa75084801fd24654224b090032184`。
[既有资格](evidence/native26-performance-build-qualification-2026-10-19.json)只支持构建、
ABI/JSON/回调及相关路由的离线结论；其 `production_DLL_loaded=false`，不授当前 provider、
提速或 Native26 业务信用。原 Native25 的实际结果继续属于原来源。

## 实际入口及提前排除的硬路径

优先沿用原 [native_session](../../ck3_autonomous_player/src/xar_autoplayer/native_session.py)
的 `native-session --cold-start-checkpoint` / `cold_start_checkpoint=True`，由 runtime owner
以**新 generation 的精确 NativeBridgeLaunchConfig**启动同一 prepared profile，加载
`xar_checkpoint.ck3`。这不是重新点击 Robert、新建 episode、加载 T0 或 `start-next-episode`。

原 `ck3_restore_checkpoint(expected_revision=...)` 也是既有实际入口，但它的生命周期请求
交给当前 daemon，按 daemon 持有的 config 重启；仅对旧 Native25 daemon 调用该入口不会
自动换入 Native26。本次换 DLL/SDK 应先准备新 owner/config，再由原冷启动及 Driver 消费者
核 exact SAVE。没有新通用迁移 API。

提前准备三处具体约束，避免现场逐条失败：

1. 当前 `root_native_build_binding_p37c.py` 的 `load_native_pin` 硬要求 DLL basename
   `native.dll`，而候选叫 `native26.dll`。在获存储准入后，可把**同 SHA**复制为新 generation
   的 `native.dll` 以保原契约，或准备只绑定精确 Native26 文件/五个 exports 的独立新 binder。
   不改旧 Native25 pin/DELIVERY。新 DLL pin、launch config、clean source、SDK freeze、
   SDK-binding 的 build label、DLL size/SHA、delivery/source-freeze pin、source root 和
   pipe 必须一致；原 binder 的历史 Native22/P37 文件名/状态与 P37C 固定路径不能直接当新包。
   当前 Host HEAD、业务 source commit、Native build 来源须分别记录。
2. MET110 有限暖 factory 硬限定 47/pending48、AUTO109/MET110 与 `same_pid_hot`。它只作
   历史暖恢复，不能用于后续新进度或新 Game cold；复用原普通 full-loop 的正常冷
   bootstrap，保当时已结算状态、下一唯一 sequence 和 classifier anchors。
3. 持久 pipe 在 Driver loader 和 cold validator 中均为 exact 键，不能随新 generation
   改随机 pipe。SDK/DLL 更新也不应顺带改 prepared profile 的 environment/lifecycle 或
   高层 goal。持久 lifecycle 含 environment SHA；本场当前为 `dbcb5ea6…f33b57`。
   如真要换环境，应走已有官方 ordinary rebinder 的适用合同，不能手改三处 lifecycle。
   若另有 resolved completion，rebinder 改过的 checkpoint 对象还会与旧 completion 的
   exact checkpoint equality 不同；它不是 resolved 证明的通用迁移入口。本次保原环境
   无需为了换 Python/DLL 走该迁移。

## 在自然保存边界固定的最小证明包

以下都是原 owner 已有输出或正常维护输出，不要求 M7 新发 RPC，不让子任务读取活 Driver/
SAVE 正文。大配对文件由原保存/冷启动消费者一次核验，索引只记录小回执。

| 类别 | 必须固定的输入 |
| --- | --- |
| 同场正常边界 | 当时 settled/no-pending 的 queue 小摘要、配对 SEM/MET、实际暂停日期与 actor/episode、原唯一 sequence 和未解决动作的真实状态。当前 metadata halt 应先按其原合同闭合。 |
| 最新正常 SAVE/Driver | 原 `ck3_save_checkpoint` 的 checkpoint SHA/size/date/history index、完整 `driver_state_replace_receipt`、pipe/Game/actor/episode/lifecycle/goal；相配的原 SAVE 与完整 Driver 不裁 history、不改 ledger 或 goal。当前 0142 只提供 day30 历史锚。 |
| 同一目标 | 完整 campaign ID、goal key、origin/current、reconciled-successions 与普通 lifecycle/environment SHA；T0 seed 文件单独保留，不能替代最新 checkpoint。 |
| 新旧身份 | 旧 machine/Game birth/image、原 SDK/Native25 来源；维护正常退出/旧进程已结束的小回执；新精确 SDK freeze/Native26 binary+exports+delivery，以及实际新 Game birth、同 `.4` EXE/build、新 DLL 注入与原生 hello 绑定。新 DLL 的实际资格独立取得。 |
| Sway 业务侧车 | 与本次最新 SAVE 边界一致的 `state/active-scheme-sway-formal-private-v1.json` 和 `state/ordinary-sway-schedule-v1.json`。day30 与最新 day61 的小冻结包均保留；旧副本不能覆盖较新的实际 ledger。 |
| 继承 UI（仅若实际存在） | 原 `successor-ui-pending-v1.json` exact bytes、原 `successor-ui-close-<transitionSHA>.json` 或 already-clear 独立 query、完整 full/title/goal 原验证、原 source epoch/Game birth、与本次正常 SAVE 精确绑定的 `successor-ui-completed-checkpoint-v1.json`。这些小原件均固定 SHA，保留 immutable 副本。当前本场没有已观测的 resolved 证据，不制造一条。 |

M6 owner 已核：两份 Sway 侧车本身不按 DLL hash/source epoch 迁移或拒绝，亦不能证明
exact SAVE/goal/Game birth；同场资格由外层上述包保证。因此不为 Native26 重写它们。
保留原 action `sway-88765ff2258b45f88acb5eeabc1f63c2`、actor `31254`、target `33946`、
full scheme ID `2` / gen `0` 和原 Start 的来源/date/revision，不重发 Start。
day30 的 next check raw `53145768` 是历史值；最新 194 已读 day61 调度为 `53146512`
（第 91 日），不清零。194 材料依旧为目标总 opinion17、两个命名 modifier observed absent，
不授 gain。旧 receipt/material/captureEpoch 保原来源，不改成新 Native 的计数，
不能把 UNKNOWN 改写为 applied。
新 Native ring 不承诺保存旧 terminal，后续
真实同 full-ID/gen 观察另行判定，不从构建或新 PID 补 gain/terminal 信用。

M6 source owner 对 captureEpoch 的补充结论已闭合：`sway_formal_consumer.py:137–166`
只在**旧 applied 证据内部**核 `pre_capture < receipt.post_capture <= resolved.post_capture`
及同 action/full-ID/gen/`.4` EXE，不要求新进程的 captureEpoch 大于旧数值。普通月检走
completion → opinion，两种 DTO 本身没有 captureEpoch，不能声称“新 captureEpoch 已绑定”。
其当前新鲜性由 `bridge/g2_private_query_transport.py:26–101` 的新 UUID、当前 expected
native revision、暂停存活帧、请求前后 `_binding` 相同，再由 normalizer 核当前
actor/target/full-ID/native revision/date 与 hello 的 exact EXE/build。Service 更新
latest observation 的新来源，保留原 Start 与 first_gain。这个 `_binding` 不含 Game birth、
DLL 或 Python source epoch，外层正常 cold 包仍须承担同场 exact SAVE/新 owner 资格。
新读 unavailable/absent/reused 就保留真实缺口，不倒用旧 ring、不重 Start，不为此回旧 Native。

## 原 resolved lineage 如何接新 source/Native

[原 typed 叶](../../ck3_autonomous_player/src/xar_autoplayer/successor_ui_checkpoint_lineage_v1.py)
的 checkpoint 键没有 Native DLL hash；Python owner epoch 由其声明的源码文件计算。
**同 `.4` EXE 换 DLL 本身不是放宽旧证明的理由，也不是该叶的直接拒绝条件。** 新 Native
真实采用由上面的精确 binder/launch 证明承担；旧 Native25 的结果、帧和原证明不改标签。

原 Driver 的 `_adopt_bridge_session` 接受配对 state 后，首次 playable 冷帧进入
`_bind_episode_from_playable_snapshot`：核 checkpoint 文件 size/SHA、actor/date、原保存
history anchor，保 episode/goal、生成实际 restore lineage，持久写回后才捕获进程内 typed
cold projection。它会清空旧 succession expectation/reconciliation，让新物理帧正常重采；
不应把旧 native revision 硬接到新 Game。

若旧 UI 记录确为 resolved 且 Game/source 已变，原 App `ensure` 才消费该内部 projection：
核旧 Game 真已退出、新真实 birth/image、同 goal、原保存前帧、exact checkpoint/Driver、
原 full/title/Close 与独立 clear 后验；以旧 source epoch 重验原记录，形成只绑定当前 App
的退役计划。先 content-address 保存 exact 旧 ledger、fsync/readback，再退役 canonical。
旧 Close/完成证明保留；任何失败保原记录和真实诊断，不重放 Continue/Close/SAVE。
`_checked` 不改。客户端 JSON、Queue readiness 布尔、同 PID SDK 重连均不能签发 cold token。

`pending`、`handoff_unverified`、Close `UNKNOWN` 或缺独立 clear 后验不属于这条退役。
原普通 SAVE gate 本就拒绝未解决义务；保原游戏/原 owner 与证据，按原恢复合同取得真实
结果，不能靠新 Game、新 source、删除台账或补写 resolved 解决未知动作。

## 后续只收正常采用回执

维护真正发生后，由原 runtime owner 的正常启动/续行结果证明：新实际 Game birth 与 DLL26
绑定；SEM actor/date 等于**所选最新 SAVE**，episode 与高层 goal 保留；CAP 为
`cold_checkpoint` / `active_resumed` / restored true、无 rejection。`active_new`、
`same_pid_hot`、只有 ACK 或内部 `cold_readiness_verified` 不算 cold 通过。
原 restore-row 合同还要求 `previous_pid != pid`；真实 birth 不同不能替代这项既有条件。
之后取正常普通计划/结果中的目标消费及下一合法 checkpoint，不为 M7 造一次动作；若没有
旧 resolved proof，只记本次 exact cold/普通目标续行，不称已验证 resolved 退役或自然继承。
自然继承及不同政府继续各需自身实际结果，不重开整个 G2 合同。

本包源码修改、测试/编译、Game/Native/MCP/桌面调用和 SAVE/Driver 正文读取均为 0。
采用存储策略 1.0.0，仅小文档/索引，峰值限制 1 MiB；record 在 180 天后复核。
