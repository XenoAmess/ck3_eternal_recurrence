# G2 自动游玩维护者休假交接（2026-10-13）

## 接班摘要

**用户本次要求写交接并交由同事接手。因此已停止新演示准备和子线程扩展，关闭本轮受管旧诊断游戏、SDK 与悬浮窗，停止 keeper，释放屏幕占用。没有启动新的罗贝尔游戏或录像。G2 总体、稳定战争能力和用户要求的重开演示均未验收。**

接班者应先读本页、[运行就绪纠正](../ck3-native-ai/g2-runtime-readiness-correction-2026-10-13.md)及当前 [AGENTS.md](../../AGENTS.md)，再核对实际工作树和现场。旧 [Native71 交接](2026-10-10-g2-native71-maintainer-vacation-handoff.md)与[原工作树残留诊断](2026-10-10-original-worktree-uncommitted-diagnosis.md)是历史来源；其中的旧存档、非战争限定、进度百分比和旧运行绑定不能替代下面的新要求与新证据。

交接前实现基线是 `master` / `origin/master` 的 `706819937af3a6f831a3a3573c731d34c81b0b75`，工作树无残留。本文交付后 HEAD 会前移；实际交接提交以本文的 Git 历史和外置交付回执为准，不能把旧 clean-source HEAD 改写成新提交来追认资格。

用户尚待完成的任务是：修复实际问题后，启动游戏、运行完整自动玩家和实时决策悬浮窗、录像，**从头自动选择 1066 罗贝尔，再自动游玩**。角色键是 `bookmark_rags_to_riches_duke_robert`；不得把旧存档恢复、旧 Driver episode 或旧战果算作重开演示。要处理政务、外交、建设、战争、防御、军队和战斗，禁止恢复 `--nonwar-only`。窗口须在桌面1置顶且不溢出屏幕，镜头跟随实际热点，决策展示应在动作提交前发布；用户继续在桌面2活动，个人 OBS 不得接管。

## 工作包与资源闭场

本页统一使用这些本机路径缩写。它们不是跨机器盘符合同，也不是永久保留承诺：

| 缩写 | 本机路径 |
| --- | --- |
| `R` | `D:/codex-ck3-background-spill/g2-remediation-20261013` |
| `N` | `R/fresh-robert01` |
| `O` | `R/recovery/runtime01` |
| `C` | `R/custody-recorder01` |
| 旧演示输入 `F` | `D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/fresh-robert-demo-20261012/attempt04-full-capability` |

2026-10-13 01:39 UTC（北京时间 09:39）闭场事实如下：

- 旧受管 Game 为 PID `24012`，creation FILETIME `134363025952867701`，creation date `20261012181635.286770+000`。只向这一代际的唯一 CK3 窗口发送一次 `WM_CLOSE`；45 秒内未退出，随后请求原 supervisor 清理自己拥有的 Job。实际 Game exit **1**，Job active **1→0**、`tree_gone=true`、`cleanup_proven=true`；**不是正常退出**。证据：`N/ROOT-OLD-DIAGNOSTIC-CLOSE02.json`、`O/ROOT-SUPERVISOR-CLOSED.json`。该 Game 使用 B2，不能算 B6 已生效。
- 旧 SDK 写入 `O/sdk-session02/EXIT-SDK` 后合作结束。当前只读清点没有 `root_current_sdk_queue02.py` 或 `root_current_mcp_entry02.py` 存活进程，且所有 Python command line 都可读取。旧队列没有保留 SDK application 的内核进程句柄，因此**不声称获得 queue/application 配对 exit0**。新 harness 的这项缺口见下文。
- 旧 overlay PID `142564` 已合作退出；`O/ROOT-DECISION-OVERLAY-142564-CLOSED.json` 与当前进程缺席分别保留。未切换虚拟桌面、未启动录制；正常关闭尝试期间 foreground HWND 发生过变化，不能推断原因或宣称始终不变。
- 新屏幕任务 `g2-robert-fresh01-screen-20261013` 仅用于冷启动前准备。keeper 停止结果为 `thread_exited=true`、`failure=null`，最后有效序号 **3263**；Root 以该序号 CAS 释放，释放序号 **3264**，随后说明“演示 pending”的任务闭场序号 **3265**。证据：`N/ROOT-BOOTSTRAP-SCREEN-KEEPER-STOPPED.json`、`ROOT-VACATION-SCREEN-CAS-RELEASED.json`、`ROOT-VACATION-SCREEN-TASK-CLOSED.json`。该 task done 仅指屏幕 custody 收口。
- 任务栏修复会话结束已由用户明确确认：“那个会话已经结束”。其原屏幕 claim 的 seq3246 经 CAS 释放为 seq3260；任务栏业务仍保留 `unresolved_red`，没有借资源释放宣称修复完成。证据：`N/ROOT-ENDED-SCREEN-OWNER-USER-CONFIRMATION.json`、`ROOT-ENDED-SCREEN-OWNER-CAS-RELEASED.json`。
- Toolhelp 中仍列出更早的 CK3 PID **139512、127028、188168**。逐个 `WaitForSingleObject(handle,0)` 都返回 **0**，已观察到内核退出；它们的 `GetExitCodeProcess=259` 不应推翻等待结果，也不能单凭进程列表把它们当作正在玩。没有终止、接管这些记录。个人 OBS PID **114680** 的 wait=258，保持运行且未触碰。证据：`R/ROOT-VACATION-PROCESS-OBSERVATION02.json`；初次只列 PID 的 observation01 保留为不充分清点。
- 本轮父/子线程均停止扩展；两个尚未初始化的 M7 子任务已中断，没有取得验收信用。用户要求的高并发沿用，但本页不声称闭场仍有 64 个任务在工作。

接班者必须重新 `list/poll --ack` 并登记自己的 CK3/屏幕资源；不要接着 heartbeat 已 done 的 task，不要复用上述已释放的屏幕 admission。主任务 `g2-remediation-root-20261013` 将在本文实际 commit/push 后标记“交接交付完成”，释放其 `ck3:single-instance`；这也不代表 G2 complete。

## 已交付主线的修复

以下提交已进入 master。未新建归档分支来保存这些成果；本轮没有审计或删除所有历史 ref，不能据此声称全仓旧分支已清零。

| 提交 | 交付内容 | 当前证据层级 |
| --- | --- | --- |
| `ab9a7a06` | 返回 profile、研究采样控制、Driver/history 紧凑投影 | 源码与定向离线；B2 旧诊断观测范围见纠正页 |
| `db80d3fb` | 补外层 Gathering sampling 路由，保留 unsupported 原失败 | 源码交付，未授新的采样实机资格 |
| `1133a56f` | Endpoint restore 拒绝传播、真实读泵停止与原文件保护 | 两项新增真实 pump 离线测试 |
| `3b6920d8` | 九个研究观察器默认关闭；战前 v1/v2、SDK/Service/普通策略；窗口位置、独立录像、决策提交前回调 | 源码、B4 与定向离线 |
| `3963eb85` | actual4 类型化 diarch 与宗教 authority getter | 源码、B5 六个补编 job |
| `82919e40` | 固定“已宣战”窗口 Native/SDK/Service/Strategy；private declaration-node 只读查询；对应测试与就绪纠正 | 源码、B6 与新增定向离线 |
| `70681993` | 弹窗优先层恢复现有 `pause-map`，避免未暂停时恒阻塞 | 两项新 Strategy/Service 离线场景；未实机 |

交付回执位于 `R/ROOT-REMEDIATION-BUNDLE-DELIVERED.json`、`ROOT-TYPED-GETTER-DELIVERED.json`、`ROOT-POPUP-NODE-BUNDLE-DELIVERED.json`、`ROOT-POPUP-LIVENESS-DELIVERED.json`。普通推送、远端 exact SHA 和 clean 检查分别在这些实际回执中。实现目录是 `ck3_autonomous_player/`；不要误找不存在的 `ck3_agent_mcp/`。

“九个研究观察器默认关闭”是减少研究 producer 的正常运行成本，**不等于关闭战争操作**。公共 plan/auto 必须使用完整 ordinary planner。运行配置为 `one_life` 与 `ordinary_campaign_succession/no_pact`；`one_life` 要从实际 Driver 属性证明，不要发明 `--episode-projection` 参数。大返回只作为有界本地 Native/Driver 输入处理和精简投影，不将整份 raw/history 灌入大模型；完整 wire、MCP 投影、持久化和耗时必须分别量测。

## 构建与测试的实际范围

最新可供**下一次冷载**采用的 Native 是：

```text
R/native-profile/build06/repair01/native.dll
SHA-256 c78fc247eb1990e1a0c87ea4f6ff2aebf6d4a012661101a3a04fdcf85359cb18
18255872 bytes; Runtime archive 612 members
```

B6 首轮六个编译 job：五过、navigation 因 header 缺 `game_adapter.hpp` 失败。修正显式 include 后只补编四个 header 消费者，保留两个已成功 Node 对象；archive/link 返回0。原失败、计划、实际修复分别在 `build06/ROOT-BUILD-PLAN.json`、`ROOT-BUILD-FAILED.json`、`repair01/ROOT-REPAIR-PLAN.json`、`repair01/ROOT-BUILD-RESULT.json`。B1–B6 生产组实际文件合计 **998,978,759 B / 2 GiB 子预算**。这不是整树所有对象按最新 HEAD 重编，原 Robert 对象及 retained 对象的混合来源仍须保留。

B6 实际启用 `XAR_ENABLE_WAR_DECLARED_OVERVIEW_V1=1`、`XAR_ENABLE_PREWAR_DECLARATION_NODE_IDENTITY_V1=1`。CMake 默认 OFF 表示构建资格选择，不是用户禁止战争。B6 **未注入任何新 Game、未 cold-live**。旧 Game 只加载 B2，SHA `3ed2b139fa334e8d2a50a7cdaae9f6c3048b1cdef32d2993b7dcc172a725ff96`。

已执行的新增/定向检查，避免接班者重跑同一矩阵：

- 战前 ordinary 策略 **41** 单元用例；Gathering-off **6 场景/41 断言**；旧请求 parser **220 场景/377 断言**；custody **6** 与 OBS provider **12** 用例；共同采样独立 TU **6 场景/33 断言**。具体范围见纠正页和 `R/acceptance/lane06、lane08、lane09`。
- lane10 的 SDK v2 **12**、Service **8**、真实 MCP 提交前回调 **2**，合计 **22 个唯一新用例**最终通过。原 fixture 失败保留，只复验失败项。
- lane11 新窗口 parser 独立第一 include 编译、链接、执行返回0：内部 **42** 与真实完整五键 wire **54**，合计 **96 场景/192 断言**。这是 parser/header 闭包，不是实际 GUI Invoke。
- lane11 两个新 Python 文件首次 **27** 用例全过，3.46 s。两个终局场景补强真实 Service/零发送断言后，仅复验这两项；unique 仍为 **27**，不能加成29。
- 新 liveness **2** 场景最终通过。首轮将构造期 ping 混入规划发送断言，失败原件保留；分开启动期后仅复验两项。没有重跑旧27、旧22或完整矩阵。

lane11 关键回执：`native-compile01-receipt.json`、`native-run01-receipt.json`、`python01-receipt.json`、`terminal-delta02-receipt.json`、`liveness03-receipt.json`、`liveness04-receipt.json`。

新增 parser EXE 的实际 Defender 登记读回为 **admin_required_for_verified_readback**；helper 未调用 Add、未触发 UAC，不能称为永久排除成功。`lane11/PROJECT-EXE-MANIFEST.json`、`PROJECT-EXE-REGISTRATION.json` 及当前 EXE/OBJ/sourceDependencies 保留到原复核期限，以便走已有受保护 broker/管理员实际读回。授权是永久的，**实际设置验收未完成**。第三方 OBS、解释器、媒体工具不在该项目 EXE 授权内。

## 两个主要源码缺口

### 战前参战来源：普通非空脚本尚未闭合

三条普通宣战入口已消费 actual mobilizable lower、完整敌方/参战方 upper、同帧宣战选择及最终 stock `CanSend`；整数 **3/2** 是风险策略阈值，不是胜率。已集结和未集结分量未证互不重叠时取最大值，库存不能直接当可执行军力。

但是普通 claim/de jure/conquest 的 `on_declared_war` 与全局 `on_war_started` 包含**非空** helper。原有 count0/null 的 empty-only qualification 没有证明这些正常路径；不能凭 CB 名字、封建政体、结构完整或未知值转零来授权宣战。要继续补 concrete compiled operator 的 vptr/invoke、实际参数和 named callee、角色变换、trigger 分支及 event descendants，最后把对应参战/额外军队来源有界地接入正式 v2。

private Node 查询已实现并 B6 编译，但只用于取得下一步输入：

- step `query-prewar-declaration-node-identity-v1`，domain `prewar_declaration_node_identity_v1`，private/read-only/unadvertised。
- 直接 guarded 读取 `base+0x5C671F0` 的非空 CB DB 槽；null 保留 unavailable。**不调用** getter `0x8FC320` 的未知 null 慢路径 `0x3F8B640`。
- current DB index/key、actor/target、完整 declaration tuple 与真实 mailbox/request/frame 绑定，两轮完整 witness 比较；最多128 nodes、128 edges、depth16、32 KiB read bytes、2048 attempts，完整 escaped outer wire≤8192 B，超限整体拒绝。
- 已捕获的结构不证明最终 primary attacker/defender。`participant_coverage_complete=false`、`war_permission=false` 固定保留；正式 v2 没有因此放宽。

源合同：`R/fresh-run-plan/ACTUAL4-DECLARATION-NODE-IDENTITY-SOURCE-CONTRACT.json`、`ACTUAL4-CB-DATABASE-GETTER-PURITY-DELTA01.json`、`R/ROOT-NODE-SOURCE-DELTA-ADMISSION.json`。Reader/Mailbox 四文件总 **67,704 B**，具体源码在 `ck3_autonomous_player/native_bridge/{include/xar_bridge,src}/prewar_declaration_node_identity12004*`。

已有完整 potential confederation-members superset 可以覆盖**已匹配**的 MPO subset，不是“所有成员已参战”；additional 五个 family 的 aggregate 已实际 AND，不能再把 leaf 未写 AND 当作 bug。宗教无效 sentinel 保持 unknown，不能视为无人；不可用 self-authority 捷径已移除。`bookmark.1070 option.c` 的已读脚本仅 spawn250（125 levies、50 bowmen、50 horse、25 armored horse），没有创建战争；初始 pressed claims6 也不证明旧战争由该选项产生。

### 固定“已宣战”窗口：构建通过，尚缺当次效果

新 fixed-target `war_declared_overview` query/close 走原生 GUI owner Invoke，不用鼠标坐标、键盘或 CharacterInteraction ACK 冒充关闭。只认 `dismiss/button_close` 的已资格路径；top-level null 仍须完整 owner tree 零匹配（2048 nodes/8192 edges），否则 unknown。

真实完整请求为五键 `type/protocol=1/request_id/step/expected_revision`。Bridge 从实际 mailbox 在 Reclaim 前复制独立八字段 TOP 回执：request_id、ticket_sequence、executor_started_sequence、completed_sequence、pump_epoch、thread_id、date_raw、connection_generation。SDK 核对该独立回执、body、actual hello generation 与七项当前 lease。`native_handled` 是诊断；只有实际 dispatch/invoke、fresh post absent/hidden、稳定 scope 等条件全齐才是 `closed_verified`。already_absent/hidden 只记观察。

Service 在终局/继承之后、普通战争之前锁外查询一次，再用新快照规划；unknown close latch 跨 snapshot/public revision 保留，不重送。地图 ready、paused=False 时先走已有 `pause-map`；缺暂停能力或未知暂停状态仍 blocked。执行中 ticket 超时不可丢弃 context，必须保留到 safe Cancel/Wait/Reclaim 或拥有的 Game 关闭。实际冷载后还需验证窗口消失与战争处理继续，不可只展示“已关闭”的文字。

关键实现：`war_declared_overview_v1.hpp`、`ingame_ui_navigation_v1.cpp`、`bridge/war_declared_overview_{contract,transport}.py`、`ordinary_war_declared_overview_v1.py`、Service/Strategy。最新 helper SHA 为 `a5b29514e3ea5ce4c748cb3289d5bd7b8f68b0de921cfcb977ad89ff58eb05f3`。

## 新开局输入：准备完成不等于可以照旧执行

`N/ROOT-FINAL-SDK-DELTA02-FREEZE.json` 冻结 `sdk-final02-source/src`，实现 HEAD `70681993`：1251 个不变文件复用 immutable hardlink，只有6547 B helper 新增物理拷贝。旧 sdk-source、sdk-final-source 及原 freeze 保留历史。**不能原地改 hardlinked 冻结输入，始终用 `-B`，不要写 pycache。**

`N/ROOT-CLEAN-SOURCE-FROZEN.json`、`ROOT-LAUNCH-CONFIG.json`、`ROOT-FRESH-SCREEN-ADMISSION.json` 都是旧 HEAD/已关闭 custody 的历史输入。本文提交后，接班者需按当前干净 HEAD 新建 freeze/admission，并明确复核实现字节与 B6 编译输入是否改变；文档提交不自动要求整树重编，也不自动证明当前 HEAD 全部编译。

准备的本机绑定为：

| 项目 | 值/限制 |
| --- | --- |
| Game directory | `Z:/SteamLibrary/steamapps/common/Crusader Kings III`，实际新启动前复核 exact build |
| Injector | `C:/codex-ck3-background/migration4-complete-domain-build/strict07/binaries-qualified-runtime10/xar_ck3_bridge_injector.exe`，SHA `a99f71135e2ba4bceb9f87b497d2f8609c690effcd53e85d7a0ce5624c54383f` |
| 旧候选 pipe | `\\.\pipe\xar-g2-robert-fresh01-20261013`；新 attempt 应独立绑定，不能接入旧 operator |
| 桌面1 | GUID `964b3ff9-3cf7-4ba9-881b-47444f31cfbe`，实际读回后操作自己的窗口 |
| 用户桌面2 | GUID `11b2eee2-855d-4029-b35c-59adc9a19203`，不切换、不抢 foreground |
| 配置 | 新隔离 profile/state，`continue_last_save=False`、`load_save=None`、XARoff/no_pact；不复制旧 Driver |

`N/state` 和 `N/ROOT-ACTUAL-GAME-LAUNCH.json` 在本轮没有生成。`ROOT-LAUNCH-CONFIG.json` 的 `ADMITTED` 只说明源码输入检查，不证明 cold-loaded 或录制就绪；不要改写其中旧诊断未关闭字段去伪造新的运行事实。

以下外置 helper 仅 AST 资格，**未执行新 Game/SDK/录制**：

| Helper | 用法与仍缺的步骤 |
| --- | --- |
| `N/root_fresh_supervisor.py` | `--clean-source-freeze / --screen-admission / --launch-config`；走公共 environment prepare/launch、新 profile、最小化、不激活、实际 Game代际和拥有的 Job。导入 clean master 的公共入口，两个 runtime 文件必须与 frozen SDK exact 匹配。需要接班者补实际 SDK 配对句柄回执。 |
| `N/root_fresh_sdk_queue.py` | `--environment-manifest / --recording-job-root / --first-frame-admission / --deadline-utc`；新 inbox/outbox，前三个 frontend 请求 route/new-game/Robert-start 各一次，实际初始 semantic/SAVE 后才发控制命令 full_loop，最多30 turns、每5 turns 核 semantic/checkpoint；unknown、角色/episode 改变即停，不重放。 |
| `N/root_fresh_mcp_entry.py` | 指向 final02-source；实际初始化后才写 Driver mode，真实 before-submit callback 发布计划。Root private Node tool 的 PID guard 有一行待修，见下。 |
| `N/root_fresh_recording_argv.py` | 校验未来 actual launch/placement/overlay 后输出官方 `managed_decision_recording.py record` argv；仅 AST parse/compile。8029 B，SHA `c50d74b547a6fa3a1b7cdac8adc9f5198c62d2856a76ead894fc7ba0e70b95c8`，receipt `ROOT-RECORDING-ARGV-SOURCE-PREPARED.json`。 |

上述四个 helper 的交接时精确大小、SHA 与 AST 结果已核对，位于 `R/ROOT-VACATION-HANDOFF-VERIFIED.json`；后续应用 PID guard 或 SDK 句柄修复时应生成新的 delta/pin，不覆盖这个历史回执。本文最终 master commit、普通 push 与 clean 结果将记录在 `R/ROOT-VACATION-HANDOFF-DELIVERED.json`。

**接手前须修两项实际 harness 缺口：**

1. Root private tool 目前比较 `before['diagnostics'].get('pid')`，但实际 SDK key 是 **`bridge_pid`**，因此会拒绝有效新 Game。最小外置 delta 是 `R/popup-sdk/root-entry-bridge-pid-guard.delta.patch`，826 B、SHA `11cc5ba6286a4e099e9451918247e3322537531e0bfc9140e9eae8597efc34f2`；**未应用**。应保留 launch.pid 正整数和 `diagnostics.bridge_pid == raw_hello.pid == actual_launch.pid`，不能制造 Native 独立证明 creation_date 的事实。源码复核回执 `root-entry-bridge-pid-guard-receipt.json`。只有这个额外研究 tool 依赖该修正，不应为它绕过普通 SDK 资格。
2. 新 supervisor 要求 `N/ROOT-ACTUAL-SDK-PROCESS-GENERATIONS.json`、`ROOT-ACTUAL-SDK-PROCESSES-EXITED.json`。当前 queue **尚不生产**这两件：必须实际保留 queue 与 SDK application 进程句柄，记录各自 PID、creation_filetime、executable，在退出后观察各自 kernel signal/exit_code。wrapper exit0 或当前 PID 缺席均不能伪造 application exit0。补上这一机制再开始新 SDK，不能关闭资格检查来凑配对。

Root-only Node probe `R/popup-sdk/root_prewar_node_probe_candidate.py` 为15554 B、SHA `fc9d7745e887b11ce516003b9fa69daccf0554a3010511bab1c3cf98f26a50bb`，也**未运行、未 RPC**。它消费实际 declarable-wars 当前缓存的完整 six-tuple/sequence；先用 `ck3_query_declarable_wars(expected_revision=实际current revision)` 取得真实 declaration_id，pending 只用原 request_id 调 `ck3_collect_declarable_wars_result_v1` 收回，禁止再发 query。缓存缺失/失配拒绝。其≤8192 B 的精简 JSON 是 rendering，不是假称保存原始 wire bytes。

## 录像、决策文字与屏幕合同

独立 OBS portable 已实际准备在 `C/obs-portable`，来自安装的 **OBS30.0.2**，不是旧文档中的30.1.2。三个固定 distribution 前缀共1961文件、383,624,881 B，实际逐文件 source/copy 核对；没有共享个人配置或改个人 OBS。回执：`C/ROOT-OBS-COPY-ADMISSION.json`、`ROOT-OBS-INDEPENDENT-DISTRIBUTION.json`、`ROOT-OBS-PREPARED.json`。**OBS 未启动，尚无 job 或录像。**

端口4467，独立 profile/collection `ManagedWindowCapture-3bb8a456e47a4b288aabbfe76cdcb2aa`；控制依赖 `O/obs-dependencies`，输出 `C/recordings`。`C/ROOT-OBS-PROFILE.json` 含控制密码，只在本机由程序读取，**不要全文打印或提交**。4800 kbps、最多1200秒、1 GiB 录像子预算，含96 MiB停止预留；成片以实际 ffprobe/增长核对，不靠配置宣称码率达标。

官方入口是 `tools/g2_saved_campaign/managed_decision_recording.py`，底层 `tools/ck3_obs_capture.py`。实际 capture 必须来自当前 Game window texture 加实际决策文字源，不能录桌面2或用 gdigrab。未来 job 的 `receipt_root/before-recording-game.png`、`before-recording-scene.png` 必须由 Root **实际查看**并核录制 started、文件增长和 Game/recorder 代际，再写 first-frame admission。requested、ACK 或 `runtime_qualified=false` 不能授权角色选择。**在第一次 frontend 选择前录像已实际开始。**

`live_decision_overlay.py` 新实现用于 hidden desktop1 保持 alpha1、own-window 位置和提交前计划文字；旧142564进程没有采用该最终实现。`managed_desktop1_placement.py` 按实际监视器和 Game代际进行不激活的 fit/topmost，并核 Desktop1 GUID。镜头应复用主体智能体中的 title/army/map hotspot 能力；还没有本轮 fresh 画面/镜头验收，不能把窗口 placement AST通过当作完成。

现有 ffprobe 是 `C:/Users/xenoa/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.1-full_build/bin/ffprobe.exe`。使用前复核精确 hash与可读性，不重新安装无必要第三方工具。

用户明确保证：“**我保证当前steam是离线**”。本轮沿用这条用户保证，准备代码支持 user-attestation；没有新鲜 Steam 离线截图，不能写成已亲眼审图。不要再次要求同一确认，不要切在线。新实机仍应保存实际采用的保证/画面类型并执行账号与屏幕协议；若现场变化，记录变化而不是用旧保证伪造当次像素。

最新正式 promo wheel 本轮已通过官方 GitHub release 查询为 **v0.2.1**（release381034850），独立安装到 `N/promo-runtime/packages`，版本和帮助实际返回0，requirements 已匹配。该 wheel **没有项目 keeper**；旧准备脚本将“安装成功但不含 keeper”误判成失败的原件保留，纠正见 `N/promo-runtime/ROOT-PROMO-PREPARATION-BOUNDARY.json`。

keeper 使用保留的独立 stdlib 源文件 `D:/codex-ck3-background-spill/ck3-sdk91/promo/ck3_native_war_ai/integration/screen_bus_lease.py`，15997 B，SHA `4a8233bb640d0eeda67150da818f3898a1c9afb0229d54e4d0d39e7a932f27f0`。不是把旧 promo package 放进 import path。keeper 仅做续租，不领取或释放；Root 领取新 screen 后每180s CAS续租，最终 stop→核最后序号→Root CAS释放。新 run 须再次查询届时最新正式 wheel，不能把本页 v0.2.1 当永久最新。

## 存储、期限与后续清理

必须沿用[通用策略](../storage-retention-policy.md)和[参数1.0.0](../storage-retention-policy.json)。本工作包 `R/STORAGE-ADMISSION.json` 原复核期限为 **2026-10-13T16:58:39.018273Z（北京时间10月14日00:58:39）**，新重型请求截止为前15分钟 **16:43:39Z（北京时间00:43:39）**。**本次休假交接未自动延长。**期限届满后先重新核用途、容量、其他 reservation 和保护理由，再获新 admission；不能修改日期继续使用旧预算。

本轮总 peak8 GiB，native2 GiB、SDK/profile2 GiB、acceptance1 GiB、derived1 GiB、recording1 GiB、headroom1 GiB；OBS distribution 在 SDK/profile 的512 MiB子账内，不是额外释放空间。保留的他人/历史 reservation512 GiB、系统增长20 GiB、安全20 GiB未因休假自动撤账。

闭场 `R/ROOT-VACATION-STORAGE-CLOSE.json` 实际核到：D free **1,237,800,632,320 B**，旧公式所需 **601,295,421,440 B**；C free41,891,004,416 B、Z free184,002,932,736 B。这是本机当时值，接班不能复用为新容量证明。R 内有限清点 **12,599 文件/2,067,952,866 logical B**，无 scan错误、未跟 symlink；logical 按 hardlink 路径重复计数，allocated 未测，不应当作物理新增字节。

当前需在原期限前保留并复核的输入包括：B6及对象/link recipe、原 SDK91 与 keeper、final02 SDK freeze、旧关键 checkpoint与迁移 original、一个代表 oversized wire、未解决问题的最小失败集合、当前录制候选配置以及新增 parser EXE/OBJ/deps。保护须写明确理由与新 review，不得无限续存。

默认 derived48h、cache7d、build/checkpoint14d、raw evidence/delivered media30d、record180d 到期成为复核候选，不能仅按 mtime 或目录名字删除。先回收可从保留原件重建的派生重复件；只删精确计划文件，保留小清单、原因和可读性变化。**本轮闭场没有执行批量删除、C盘清理或全机自动部署回收器。**原 C清理线程的最终全量结果未在本次交接复核，不能报告“C盘垃圾全清完”。

## 接手顺序与完成标准

1. 检查当前 Git/原件可读性、统一存储 admission 与任务总线。保持 `cmd.exe + Python`，不执行 PowerShell。原生研究依照 [native README](../ck3-native-ai/README.md) 的 exact-build 原生树优先流程；不先猜策略再补证据。
2. 并行拆分普通非空开战脚本来源、SDK进程配对修复、当前窗口/录像现场消费，明确文件所有权与单一屏幕操作者。用户已要求高并发，无需再请求战争或子线程授权；不要派64个线程争抢同一个 Game、screen或构建账。
3. 在屏幕未占用时提交必要实现/定向验证，fetch+rebase 后普通 push master。准备新干净 source freeze、独立 attempt/pipe/profile/请求目录。保留旧 HEAD/失败回执，不热替换运行中 DLL、不修改 frozen hardlink。
4. 领取当次屏幕独占与 keeper；从公共环境入口冷启动 B6或实际更新后的合格DLL。核 actual PID+creation、DLL hash、hello exact build/gen/ready；其他 operator 的旧 PID 列表不能作控制绑定。kernel已退出的历史 CK3对象不应被误当运行中的账号/游戏；若公共入口因此拒绝，先修有证据的 inventory 缺陷，不隐藏过滤或杀个人会话。
5. 将自己拥有的 Game 与决策窗放桌面1、fit/topmost、不activate，启动独立录制并实际审首帧。保持用户桌面2/foreground，不接管114680。需要鼠标兜底时严格走 [坐标映射合同](../desktop-coordinate-mapping.md)，键盘先核英文布局与实际焦点；优先 typed MCP。
6. 录像资格达到后，route/new-game/Robert-start 各一次，核初始1066 actor/date及实际 SAVE，再进入完整 ordinary 自动回合。每个决定先展示实际可观测输入、选择和理由，再提交并读回业务结果。热点镜头、弹窗关闭、应战/军队调度都需实际画面与状态证据。
7. 同时记录 Native完整返回大小、MCP摘要、history持久化、各阶段耗时和持续有效turn；超过64 MiB的原件只做有界本地离线修复，不能临时1 GiB授权变成默认LLM上下文或永久预算。已发布动作未知时保留原 request ID收回，禁止重放 Start/Close/SAVE来制造成功。
8. 形成真实日期推进、战争处理/结果及checkpoint配对，才按对应合同授予信用。有界窗口结束后先保存，分别关闭 queue/application、录制、overlay/Game，核各自 kernel代际与退出；stop keeper、CAS释放，再修改/提交。forced Job清理与正常退出分列。

快速只读检查可用：

```text
git status --short --branch
git rev-parse HEAD
git ls-remote origin refs/heads/master
tools/.venv/Scripts/python.exe -B -X utf8 D:/codex-ck3-background-spill/g2-remediation-20261013/root_bus_summary.py list
tools/.venv/Scripts/python.exe -B -X utf8 D:/codex-ck3-background-spill/g2-remediation-20261013/root_bus_summary.py poll --task <接班者新task> --ack --limit 15
```

`root_bus_summary.py` 先核 source/installed CLI 字节一致；当前 CLI SHA 是 `B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE`，屏幕 CAS 的 pin须精确大写。总线位于 `Z:/.codex-task-bus`，完整协议见[任务总线文档](../codex-task-bus.md)。不要复制闭场 seq 或只看 tasklist 就继续启动。

当前没有 fresh战争胜利、fresh日期推进、完整首次录像或整局完成证明。M4/M6/M7 的时间承诺不能从本轮提交数、离线测试数、旧 saved days 推导；历史5/8、6/8是可见里程碑计数，账本禁止将其换算稳定战争能力百分比。后续能力/计划统一回链 [目标路线图](../autonomous-agent-progress/goal-and-roadmap.md) 与具名 native/实机证据。**接班的首要交付是可信的新开局演示及其结果，不能再把源码通过报告成“问题全修好了”。**
