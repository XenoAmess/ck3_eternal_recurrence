# R0019 启动、首 attach RED 与后续 snapshot：04:35 PARTIAL

证据截止 `2026-10-07T04:35:00Z`。主执行来源冻结 `465595b67efa8f72dfc97bc0de218302c75e3bfd`；游戏 PID `19980`、创建时间 `1791346683.45508`（`04:18:03.455080Z`），native session `172caf27cc8b44549ea94ed2f306cfe0`、generation `1`，Client session `5b11bc8186974854aa695cf2704e8866`。本追加记录已经发生的启动和同连接 native snapshot，整体仍 **NOT_GREEN**，不授予 attached_verified、formal、新 T、C3 或 I4 信用；正常退出在此截止点尚未验。

ROOT 的新鲜 Steam 画面原亲审于 `04:17:04Z` 明确记录“离线模式”，绑定 `steam-moved.png` SHA `8dd90aa90bef0c9ecf9ed0b72167639a4f66be069409146588e86854de032c8b`；原窗口位移 freshness receipt 和原图已保存。launch 原件记录实际 game_started=true/native_injected=false，状态 `GAME_CREATED_REQUIRES_NATIVE_LOAD_READBACK`。ROOT 随后保存 PID/创建时间/HWND `24315052` 的 window identity 和 live binding。`PREPARED.json` 仍保留其阶段原状态 `PREPARED_FILES_AND_ROOT_LIVE_PROFILE_ONLY`、native_attached=false；不反向把准备 ACK 写成实机验收。

既有 SDK metadata 原 capture 为 SDK `2.0.0`、pydantic `2.13.5`，default/read-only/challenger/full 为 `21/23/24/28` 项，来源也是冻结465。该 metadata 原阶段 `runtime_acceptance=NOT_RUN` 保留；后续实际 snapshot 信用来自下列独立原件，不由旧 metadata 标签代替。Client ready 原状态 `CLIENT_CONNECTED; bridge NOT_ATTACHED automatically`，automatic attach/retry 为 false，原 Client/source/live binding 已保全。

| 实际阶段 | 原件与结果 |
| --- | --- |
| 首次 attach，SDK sequence2，`04:25:42.488464Z` | 原 `native-evidence/.../0001-attach.json` 为 **RED**；reason=`BridgeUnavailableError: native game state is not available yet; CK3 may still be loading or may not have entered a map`。injector 本身 returncode0，与 attach RED 分层保留 |
| 同连接后续 snapshot，SDK sequence3，`04:30:08.362389Z` | 原 `0002-snapshot.json` 与 official native0003 均为 `native_snapshot_verified`；public/native revision `2/1`，同 PID/session/generation |

首次 attach ROOT RESULT SHA `43e58032b437166f999cfcb2120ec86157ce16c4030fe052a55812163a79d0d6`，SDK envelope SHA `88f21ae1cfb0646e9b0dcc13bf81cde06b93d3decc28cf8aa62039ec6c19d1d6`，原 native receipt 及 official copy SHA 都是 `75d41e2683b991f2f167267401559e5a45a37937c357c51f5b7aacd8864d33a7`。原 envelope `isError=false` 不覆盖 inner RED，attach-claim 原件仍保留，没有重新注入或回填成功。

后续 snapshot 原件及 official0003 copy SHA 都是 `141e6b2c8dec62da1f884002f7a0327228378a5dd802006c8861689c02d48ef0`。它实际读到 date `53144712`、paused/map_ready=true、actor `31254` alive、stress0；gold/prestige/piety raw 为 `104300000/220000000/315000000`，scale `100000`，对应 `1043/2200/3150`，active event 和 pending interaction 均 null。首 attach 失败不等于这个后续 snapshot 失败；后续 snapshot 成功也不等于 attach producer 已生成 `attached_verified` 或完整业务通过。

此前 [实际 native 构建](../../../ck3-native-ai/acceptance/2026-10-07-r0019-exact-head-ci/BUILD-ADDENDUM-20261007-035120.md)的 compilation=true/native5 PASS 与原 outer exit1/Defender settings_failed 都保持独立事实，不能把构建或此次 snapshot 记成整体 GREEN。465 DLL/injector refs 继续由既有构建和本次 profile/attach 原件绑定。

04:35 之后的标准 debugpy 基础准备位于外置 `r19-debugpy-recovery-20261007-001`，后续 late-attach 源候选位于 `r19-late-attach-production-repair-20261007-001`；这些属于另一截止点和恢复链。本包没有预写 DAP evaluate、源码 overlay、hotfix 成功或新的 attach 成功 receipt，也不把后来来源覆盖原启动 RED。

原对象以原 bytes 收在 [STARTUP-0435.original-evidence.zip](STARTUP-0435.original-evidence.zip)，来源、SHA 和 frozen refs 见 [STARTUP-0435.inventory.json](STARTUP-0435.inventory.json)，选定实际字段见 [STARTUP-0435.facts.json](STARTUP-0435.facts.json)。没有存档正文、EXE/DLL 或全 runtime copy；原外置 attempt 不移动、不删除、不改写。本代理只读已保存对象，在独立 docs worktree 写入报告/日报并做正常 master 交付；不触碰正在修改的 `C:/lci18w1` 文件，不更新冻结主树，不调用 SDK/进程/bus，不做新截图、测试、CI 查询或实机动作。
