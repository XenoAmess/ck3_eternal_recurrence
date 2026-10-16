# G2 接续维护者休假交接（2026-10-13，第二次交接）

> 2026-10-17 更新：[Native21／SDK27 实机截点](2026-10-17-p27-native21-continuation.md)记录当前代际、录制、已完成批次与连续窗口中断；本页以下事实保持历史身份，旧上限和启动脚本不得当作当前规则复用。

> 2026-10-15 续录更新：本页保留 10-13 休假收口的历史事实；最新 N39 游戏、录制、性能修复和宣战查询月冷却，请先阅读[当前续录交接](2026-10-15-n39-performance-and-declaration-cooldown.md)并核对实际现场。[P11交接](2026-10-15-p11-recording-continuation.md)已是历史。不要复跑本页的旧启动脚本。

## 先看结论

本页接续同日的[第一次交接](2026-10-13-g2-native-maintainer-vacation-handoff.md)。用户再次要求休假交接，故已停止演示和研究，关闭本轮拥有的游戏、悬浮窗及独立录像，停止 keeper，并释放屏幕占用。**没有正在运行的受管游戏或待继续收回的 SDK 请求。** 不要接入 fresh09/fresh10 的旧 pipe 或重新执行它们的启动脚本。

已完成多批 Python/Native 修复、定向验证和线性 master 推送。新 1066 罗贝尔已在 fresh06/07/08 实际选中，首都镜头和初始 SAVE 配对通过。但是完整普通规划器的首个回合仍被窗口树读取阻塞：**有效普通回合 0、日期推进 0、选定战争目标 0、获胜战争 0。** B12 已实际冷载，但尚未在地图内验证其修复效果。G2 总体、稳定战争、跨代整局及用户要求的完整演示均未完成。

本页编写前源码基线为 `master = origin/master = 70fd8182667c684042b5415f24e6739d674cf6c4`，无源码残留。本文提交后 HEAD 将前移；最终交付 SHA、远端一致性与 clean 读回写入外置 `R/resume06/ROOT-CONTINUATION-VACATION-DELIVERED.json`，不能用文档提交反向改写旧 runtime 的 source HEAD。

接班的第一件业务工作是：核容量、准备独立 fresh11 或新的 attempt，尽快完成录像审图、固定 Robert 开局、初始 SAVE 和首个普通回合，取得 B12 的实际完整树结果。**不要再次用整轮静态研究代替这一步，也不要重复已经通过的旧矩阵。**

## 用户要求与执行约束

- 从头自动选择 `bookmark_rags_to_riches_duke_robert`，使用完整 ordinary planner，处理治理、外交、建设、宣战、防御、军队、战斗；不能恢复 `--nonwar-only`。
- 首次演示上限仍为 30 turns、每 5 turns 检查并保存；录像原上限 1200 秒/1 GiB。每个动作提交前展示实际选择理由，提交后读取业务结果。
- 用户要求 64 并发 M0–M7 研究，采用每组协调兼研究者加 7 专项。已多轮复用原线程；**分派 64 路不等于持续有 64 路实际运行**，capacity/stream 错误和部分未交付均已保留。交接时实际代理状态检查没有活跃子线程。
- Game 与决策窗放桌面1，不切换用户桌面2、不抢 foreground、不控制个人 OBS。唯一主线程操作游戏和屏幕，其余线程只读或在外置目录保存候选。
- 用户已经明确保证“我保证当前steam是离线”。本轮按用户保证沿用，未切在线；没有取得本轮新鲜 Steam 离线像素，不能写成亲审截图。
- **不得使用本项目禁用的 Windows shell**，包括环境默认 shell。所有命令显式使用 `cmd.exe`，Python 加 `-B -X utf8`。优先外置 `.py`；内联代码用 ASCII hex，中文用 Unicode escape。不要将含 `>` 的 Python 字符串直接交给 cmd；hex 后命令仍受 Windows 约 8191 字符限制。
- keeper 存活时，冻结 checkout 必须保持 exact HEAD、tracked/untracked 全部 clean。候选保存在外置目录；停止 keeper、CAS 释放后才修改、提交或推送。不能热换 DLL、改冻结 hardlink、写 pycache 或重放未知动作。

完整约束以当前 [AGENTS.md](../../AGENTS.md)、[任务总线](../codex-task-bus.md)、[统一存储策略](../storage-retention-policy.md)及原生专题为准。

## 本机路径与入口

这些是 `XENOAMESS-FULL-` 本机绑定，不是跨机器协议。

| 缩写/项目 | 路径或身份 |
| --- | --- |
| 仓库 | `Z:/ck3_mod_rewrite` |
| `R` | `D:/codex-ck3-background-spill/g2-remediation-20261013` |
| 最新已关闭 attempt | `R/fresh-robert10`；上一场 `R/fresh-robert09` |
| 本轮 Root helper/交付回执 | `R/resume06` |
| 第三、第四轮研究候选 | `R/resume03/m0` 至 `m7`、`R/resume07/m0` 至 `m7` |
| `C`，独立 OBS | `R/custody-recorder01`，录制目录 `C/recordings` |
| UI/OBS 控制依赖 | `R/recovery/runtime01/{ui-dependencies,obs-dependencies}` |
| Game | `Z:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe` |
| 本机任务总线 | `Z:/.codex-task-bus`，只读/操作 wrapper 为 `R/root_bus_summary.py` |
| 桌面1 / 用户桌面2 | `964b3ff9-3cf7-4ba9-881b-47444f31cfbe` / `11b2eee2-855d-4029-b35c-59adc9a19203` |

Game 实际为 CK3 1.20.0.4、Steam build 25734779，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。新启动时重新核对，不把旧哈希当当前文件证明。

Injector 为 `C:/codex-ck3-background/migration4-complete-domain-build/strict07/binaries-qualified-runtime10/xar_ck3_bridge_injector.exe`，SHA-256 `a99f71135e2ba4bceb9f87b497d2f8609c690effcd53e85d7a0ce5624c54383f`。

个人 OBS 的历史绑定为 PID114680 / FILETIME134356006183287804 / `Z:/SteamLibrary/steamapps/common/OBS Studio/bin/64bit/obs64.exe`。它是排除控制对象；不能据旧 PID 声称交接时仍运行。独立 OBS30.0.2 位于 `C/obs-portable`、端口4467。`C/ROOT-OBS-PROFILE.json` 和 fresh10 的派生 profile 含密码，**不得打印全文、入 Git 或写入交接附件**。

## 已落地主线的工作

逐项来源及首次验证见 [G2 接续专题](../ck3-native-ai/g2-continuation-2026-10-13.md)。下面只列接班需要区分的实现和边界。

| 组 | 已集成 | 仍未完成/不能授予的信用 |
| --- | --- | --- |
| M0 战争退出 | 接入既有守方白和、多战争已资格终局优先、终局材料摘要 | actual4 最终接收方通用 evaluator 的 TLS/init 来源未闭合；异步 `submitted_pending` 后续战争消失关联仍为候选 |
| M1 核心回合 | 接受核心完整而可选规则 unknown 的同帧 root；省去根查询完整 history 复制；liege/risk 实际形状修复 | 未完成 Native wire/history 独立成本量测；整个 Driver 文件大小不是 history 大小 |
| M2 自然事件 | `.1070.c` 理由和军队材料比较、普通提交前 feed；已有事件下一回合使用新快照 | 没有实际 `.1070` 增兵材料结果；`.1001`普通选项及拒绝后防御战后置接线仍缺；第四轮部分补丁只有 AST |
| M3 继承存续 | 生命周期真实字典；原 SDK 异步继承交接包装；显式 successor LIFE gate rearm | 没有自然继承、Continue/Close 或 successor SAVE 实机；旧 child-default episode 槽与三个 SAVE 消费者丢弃独立 Driver 回执仍待修 |
| M4 和平治理 | LIFE 配置透传/阶段处理、危险派系赠礼优先、已有 tier-one 建设优先 | 扩展目录 6080 候选覆盖问题未闭合；resolved gift follow-up 未接入普通回合；第四轮建设/gift 源码写入失败，不存在已交付代码 |
| M5 家庭外交战争 | 强攻传 `commands`、合法 ArmyID0、目的地专属拒绝继续候选、宣战原请求及 WarID 连续性 | 目标仍只取一个 `min`；逐 tuple 找首个 qualified 未实现；供给附件没有 Strategy 决策消费；非空开战来源仍 partial |
| M6 谋略制度活动 | 普通 Service 接入既有 Sway completion/termination/opinion 观察，startup session 顺序修复 | fresh 未到达 Sway/Feast/制度业务；不要重做已存在的 resolved→terminal writer；新 start 路径及活动跟踪缺口需实际输入 |
| M7 长期整局 | queue/application 双句柄、base Python 依赖隔离、pending 同 SDK 原 ID collect、录像关闭顺序和实际退出 | 目标冷恢复未验收，长局/跨代未验收；fresh06–08 Game 正常关闭仍失败，fresh09/10 菜单中关闭实际成功 |

关键提交（完整范围用 `git log` 查，不把其它产品并发提交算 G2）：

| 提交 | 用途 |
| --- | --- |
| `aaee94ba` | 首批 ordinary 故障、生命周期、SDK custody 修复 |
| `ceb12975` | base interpreter/venv 模块与实际双进程短检查 |
| `f312e9eb`、`042a64a1` | release 输入排除本地 `.idea`，100 allowlisted 文件事实纠正 |
| `4c90e76b` | overlay 实际 image 与 OBS profile ready |
| `bd89a154` | fresh startup、LIFE、镜头跟踪及 B9 来源 |
| `9d8682f3` | 已完成 LIFE gate 的显式 successor rearm |
| `cedaece5` | fresh06 证据、Native owner-tree 失败诊断 B10 |
| `014b6e56` | 私有有界完整 owner-tree helper、12 场景、B11 |
| `70fd8182` | 根据实际大树证据扩大私有预算，B12 |

## 镜头故障：已证和未证

fresh05 的左上阴影确实存在，不能归为用户预览误差。当时没有在开局后调用初始 camera。现在 Service 从当前 CampaignRoot 首都选择和平 fallback，隔离 profile 设置边缘滚动禁用，开局固定序列增加 camera4。

fresh06 实际首都 Province2619 → `b_trani / c_apulia`，current/target `[1898,0,2444]`，zoom174/index4，settled。Root 亲审 sample012 和后续 sample016；fresh07 sample003、fresh08 sample014 均显示清晰 Trani/Apulia。初始定位和暂停中保持有实际像素证明；**日期推进期间的热点切换、战时稳定性仍未验证**。profile 字符串与 launch 路径已核，未读取运行时设置 getter，不能据 profile 单独证明最终运行设置。

## 实机账本与最新关闭状态

固定开局得到的实际 actor 是 **31254**，日期 raw53144328（1066-09-15），不是旧存档 ID29829。actor ID 是本场 runtime 身份；书签 key 和独立 root 一致，不另造历史人物 ID 映射证明。

| attempt | 实际到达 | 停止原因与结果 |
| --- | --- | --- |
| fresh06，B9 | Robert Start verified 27.55s、相机、semantic5、SAVE6 | AUTO9 blocked `war_declared_overview unknown`；keeper 因瞬态 dirty 停止；Game force exit1；原录像 failed，独立 OBS 实际 exit0 |
| fresh07，B10 | Start 28.66s、相机、初始 SAVE | 完整树 2048 widget 预算耗尽；普通回合0；录像完成143,371,631B/238.566s；Game force |
| fresh08，B11 | Start 26.32s、相机、初始 SAVE | 完整树16384预算仍耗尽；普通回合0；录像完成607,243,400B/1010.666s；Game force |
| fresh09，B12 | 实际冷载、独立录像、主菜单亲审、route1/New Game2 | Start3 **未发送**：`not_submitted_admission_closed`；不能记开局成功；SDK 两代际 exit0、Game 正常 exit0 |
| fresh10，B12 | 实际冷载、placement/overlay、独立录像 | 用户要求交接后关闭；**SDK_NOT_STARTED，零 frontend/游戏动作，未审图准入**；Game 正常 exit0 |

fresh07 的实际失败：

```text
war_declared_window_read_failed:widget_budget_exhausted;at=908;queued=2048;edges=2048;matches=1;count=3;child=2
```

fresh08 的实际失败：

```text
war_declared_window_read_failed:widget_budget_exhausted;at=8711;queued=16384;edges=16387;matches=1;count=5;child=1
```

已经遇到一个窗口不能提前停止遍历；剩余图尚未验证时既不能授 absent/hidden，也不能证明唯一性。B12 的实际地图内完整读取仍未发生。

fresh06 瞬态 dirty 来源：M1 子线程在 cmd 内联源码中使用未转义 `>`，误生成仓库根 `601295421440+65536`，2249B，mtime06:39:58.3983982Z，随后仅删除该文件。creation/删除精确时间未测，和 keeper06:40:24Z 停止有时间相关性，尚不能冒称独立因果证明。原线程工具 chunk6f0504/0f6528/204fac 没有外置原件。

fresh06 初始 SAVE 为68,948,462B，SHA-256 `567106ae5e77037960cca9bdca458114680f3198a9c1984be641baf2a2075869`，history_index3；Driver 独立回执 `WRITE_REPLACE_RETURNED_NOT_FSYNC`。仅授初始 SAVE 配对，不授 fsync、自然继承、successor SAVE 或冷恢复。fresh07/08 各自初始 SAVE 原件不可混用。

最新两场闭场细节：

- fresh09 Game237092 / creation `20261013085116.950750+000`；SDK queue279128 / FILETIME134363561769956276、application228068 / FILETIME134363561787890927，两原句柄实际 exit0。keeper3977停止，CAS释放3978。录像 session `efd338de-0a2e-49a6-a69d-b3386b8c4249`：658,799,710B、1096.400s、SHA-256 `52f689ea30929bc48d4e075bac6d14d1ffb0335f24ad6c97598af168c4a8dfae`，COMPLETED、inputs_unbound、OBS正常exit0。首帧回执里的 growth=0 是错误路径扫描（视频在 job 目录旁），不能当增长证明；原件保留，以实际成片核验为准。
- fresh10 Game64560 / creation `20261013091326.697297+000`，09:25:59.603536Z supervisor closed，tree_gone、exit0；SDK未启动。overlay201980 已有 CLOSED 回执，keeper最后3985、failure=null/thread_exited=true。Root 以3985 CAS释放，返回3986、resources=[]；因 claim 已过期，bus 把它登记为 waiting/expired-own-claim-released/business unresolved，**不是普通业务完成**。
- fresh10 录像 session `580b2350-ad06-4de3-8d8c-11a49c621cff`：124,944,729B、207.833s、SHA-256 `c57f863b104502f1f74beb17285b626ed98bac4f87b0404bed9def3df7483ae1`，COMPLETED、inputs_unbound=true、独立 OBS engine exit0。第一次 record CLI 因 profile 仍为1GiB而 argv 为600MB，在 preflight 拒绝，**没有启动 worker**。Root 另建只降低 `max_output_bytes` 的派生 profile，保留原 argv/错误，正确的 record 只启动一次；未改个人配置。

逐响应、实际退出及媒体核验见 `R/fresh-robert{06,07,08}/ROOT-FRESH*-ACTUAL-CLOSED-EVIDENCE.json`、`R/fresh-robert{09,10}/ROOT-ACTUAL-CLOSED-EVIDENCE.json`；原 response、Driver、cleanup、completed/failed 继续保留。视频路径为 `C/recordings/<session-id>.mkv`，**不是** `<session-id>/video.mkv`。

## B12：可复用构建，不是业务通过

```text
R/native-profile/build12/native.dll
18269696 bytes
SHA-256 28c01334e474a712180c94782d72c0880d7360e49296dbc82e73e23e9416b648
```

`ROOT-BUILD-RESULT.json` 证明 compile/link 各一次 exit0。仅重编 direct c0339、保留 B9 archive **全部612成员**和其它混合来源对象；没有全树重编。B9 旧文档“保留611/612”说的是当时重建一个 member，不要外推到 B10–B12。

当前生产 helper `native_bridge/include/xar_bridge/war_declared_owner_tree_v1.hpp` 为6596B、SHA-256 `2fb29e51ff65a298e9c2d8a696fa2c23478b23dfe821ce582a296879a89ee4c5`，完整树上限262144 widgets/1048576 edges；通用 GUI 导出2048限制未变。使用有界 vector/set，全部可达图读完才发布结果，截断/坏边/重复/环/多目标继续 unknown。

测试 `native_bridge/tests/war_declared_owner_tree_v1_test.cpp` 调用同一生产 helper，共12场景。B11首次通过；B12改预算后同12场景复验通过，**0新增独立场景**。Root 用外置 DLL wrapper 调用原 fixture main，未新建项目 EXE。证据 `R/native-profile/owner-tree-focused{01,02}/RESULT.json`，构建脚本 `R/resume06/root_build12_owner_budget.py`。B11初次 missing-header 编译 RED 原样保留，后续单 header include overlay 修正后 GREEN。

无 Native 变更时只核实际依赖 pins 后复用 B12；文档提交不要求全量重编。若修改 Native，重编受影响 TU/重链，并安排新冷载，不能修改已关闭 attempt 的 `cold_loaded` 标记追认。

## Harness 接续方法

fresh09/10 的 `sdk-source` 为1277个不可变文件 hardlink，0新增物理源码字节；真实 source/freeze pins 在各自 `ROOT-FINAL-SDK-FREEZE.json`。它们是历史输入。接班必须新建 attempt、pipe、profile/state/requests/responses，并冻结当前 clean HEAD。

可参考 fresh10 的 Root helpers，但不要原样执行：

| Helper | 接续注意 |
| --- | --- |
| `root_fresh_supervisor.py` | 公共 prepare/launch、实际 Game Job/代际、180s CAS keeper、queue/application 双 retained HANDLE、独立录制先于 Game 关闭 |
| `root_bootstrap_recorded_runtime.py` | 顺序 launch→Desktop1 placement→overlay→录制；fresh10 的600MB profile不匹配路径曾失败，需在新 attempt 准备一致的 profile/argv，不复跑旧 bootstrap |
| `root_fresh_sdk_queue.py` / `root_fresh_mcp_entry.py` | lifecycle normalizer、`bridge_pid == hello.pid == actual launch.pid`、base Python `-S` 后只加载固定 venv 依赖、配对句柄确认后才 RPC |
| `root_run_fixed_frontend.py` | route1/New2/RobertStart3/camera4/semantic5 各一次；fresh09 遇 preflight response 没有 result 时 KeyError，应在新候选识别该原状态并停止，不重送 |
| `root_run_reviewed_loop.py` | Root亲审实际 post-camera PNG 后才 SAVE6、full_loop7；完整 ordinary、max30、checkpoint5；需要 reviewer `/root`、`at_utc` 和匹配实际代际 |
| `root_publish_request.py` | 原子新序号、一次一请求；真实目录为 `N/requests` 与 `N/responses`，不是 sdk-session/outbox |
| `root_pending_declaration_recovery.py` | 保留同一 SDK，只 diagnostics/collect 原 request ID；`observe_original_start` 仅观测，不清 HALT、不推进 frontend_done |
| `root_compact_decision_feed.py` | 提交前实际理由、16KiB上限；第四轮提交后材料 feed 只有外置未应用补丁 |

一次完整启动的预算是实际 Game1500s，录像原最大1200s；Frontend地图等待和 pump共享600s，MCP read最多720s并裁剪实际剩余时间；queue还预留录制/SDK清理。**在启动 Game 之前完成静态派工，录制开始后马上亲审最新主菜单帧并启动 SDK/固定序列**。不要先处理长轮并发消息，或一直查看旧 sample001；fresh09因此耗尽 admission，Start未发出。requested/started/进程存活都不能替代亲审像素及文件增长。

若实际宣战查询 pending，不发新 query、不重启 SDK，先原 ID collect 后重新规划。当前没有活跃 pending；新场才可能产生。私有 Node probe 为 `R/popup-sdk/root_prewar_node_probe_candidate.py`，SHA-256 `fc9d7745e887b11ce516003b9fa69daccf0554a3010511bab1c3cf98f26a50bb`；仅消费当帧实际 declaration tuple/sequence。所有 fresh 场次尚未取得该 Node，不能把工具源码存在当参战来源覆盖。

## 算法与研究下一步

优先顺序：实际 B12 普通回合 → 当次具体 RED 修复 → 合格暂停帧取得 declarable tuple/Node → 普通决策/战争结果。源码研究不必等游戏，但候选只有主线程在闭场后集成。

1. **战争目标选择**：当前只选一个 `min`。复用已有 power 排序稳定扫描完整 tuple，各 CB/config 独立资格；第一个 partial 不应遮挡后面的 qualified。pending 要保留原 ticket，不能被当终局失败继续发查询。第四轮只有 recipe/场景，没有集成补丁。军力阈值不是胜率。
2. **宣战连续性**：`strategy.py` pending 分支当前 `_latest_life_advance_index(rows)` 默认只算 successful。候选改 `successful_only=False`，避免时间已推进但暂停验证失败时再次推进；需新场景覆盖 `ok=False` 且实际推进，保留原 request，未应用/未测试。
3. **来源闭合**：非空 `on_declared_war/on_war_started` 继续 partial。下一静态 callee 为 callback5 `0x25B1B70`，receiver/context/附加输入/trigger与实际Node未闭合；不能放松正式 v2 qualification。M0 actual4 CPU搜索叶115B `0x3F90870`已闭合，TLS writer/epoch传递、`CF5950` 230B held body仍缺。第四轮发现的 scalar1早返回路径也无实际见证，不能启用通用 evaluator。
4. **移动**：B9供给附件已进入 Driver preview，Strategy未消费。第四轮纯观察 helper在 `R/resume07/m5/army_orders`，仅向 audit透传 current/target，不改变移动政策，target usage0不是抵达后安全。contact Q100000前缀原始时长在DTO丢失，候选见M0 continue-war。
5. **普通治理/自然事件**：M2 `.1001`接线候选、M3 child-default归档/独立SAVE回执、M4 旧槽显式后继优先的建设扫描及 gift follow-up，分别按真实输入实施。Service已有 pendingfocus恢复；outer native-auto-run LIFE gate错位属于未来冷恢复边界，**不是fresh MCP blocker**。

第四轮 `R/resume07` 有 capacity/stream失败、cmd过长未落盘、闭场晚于09:06Z等纠正。M0/M5协调者汇总文件写入失败；M4经济/gift候选文件不存在，即使早期 DELIVERY/bus写delivered也不能引用为已交代码。用实际文件、源码 pin和后续更正核验，不能自动应用目录内全部 patch。接班恢复子线程可复用原8协调者及其7lane，不要为了填满计数重复无变化验证。

用户单独要求的 [REA研究](../ck3-native-ai/rea-evaluation-2026-10-13.md)已入库：可试作静态 value-flow/证据侧工具，不替代普通规划器、TLS/RNG资格或实机。未安装/运行 REA，勿将它列为已部署能力。

## 存储、期限与接手检查

全部64任务和本轮 attempts 共享原8GiB，Native2GiB，没有追加64份额度。最新闭场清点 `R/resume02/ROOT-FRESH10-CLOSE-STORAGE-AUDIT.json` 为 **2026-10-13T09:46:33.845378Z**：

| 项目 | 实测 |
| --- | --- |
| 文件数 | 52,431 |
| 按路径 logical bytes | 8,170,897,253 |
| 按同文件身份去重 logical bytes | 7,563,729,667 |
| 组预算 | 8,589,934,592 |
| Native组 | 1,503,009,141 / 2GiB |
| D卷 available | 1,231,930,142,720 |
| 原 reserve所需 | 601,295,421,440 |

physical allocation未测；hardlink不得重复算新增物理占用。去重账剩余约1.026GB，**不能直接承诺足够再跑一场完整profile+1200s录像**。新重型写入前核新peak、其它reservation和用途，必要时按[统一策略](../storage-retention-policy.md)评估可重建派生重复件，精确计划/删除/回执；不能按失败attempt或目录名整棵清空。此轮没有GC或批量删除。

原 review **2026-10-13T16:58:39.018273Z**（北京时间10月14日00:58:39），重型新写入截止 **16:43:39Z**。交接没有延长；到期后重新评估用途、容量和限期保护，不修改旧admission日期。B12依赖/构建配方、当前冻结SDK/keeper、关键初始SAVE、GUI预算代表失败、原请求与媒体证据需在该时点复核保留理由；过期副本不得无限保留。

接班只读入口（在显式cmd.exe中执行）：

```text
git status --short --branch
git rev-parse HEAD
git ls-remote origin refs/heads/master
tools/.venv/Scripts/python.exe -B -X utf8 D:/codex-ck3-background-spill/g2-remediation-20261013/root_bus_summary.py list
```

新任务先register/poll --ack；新Game前重新核本机游戏数0、资源、当前文件hash、容量和独立运行编号。root task `g2-continuation-root-20261013`在本文交付后闭场，不接管其旧序号。screen CAS不能无expected-sequence续租。闭场后才能线性commit、fetch/rebase（必要时）、普通push master，禁止merge/force push。

完成标准仍是可复核的新罗贝尔普通游玩、实际日期推进和配对SAVE；若选择战争，需真实开战、军队/战斗处理及明确业务终局。关闭通知、API ACK、测试通过、源码提交和录像存在都不能代替这些结果。
