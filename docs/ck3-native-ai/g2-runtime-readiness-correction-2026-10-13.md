# G2 运行就绪状态纠正（2026-10-13）

**当前状态：未验收。现有证据不足以宣称 G2 可以稳定自动打战争或长期可靠地完成整局游玩。**

此前汇报把源码实现、离线资格、局部实机观测和历史里程碑累计放在一起，造成了总体能力已经就绪的印象。这超出了证据，是汇报口径错误。本页纠正当前结论；历史验收按其原版本、场景和合同保留，不倒改成功、失败或未观察的事实。

本次罗贝尔演示**未取得战争胜败结算**。修复已经推送，也不能据此把运行状态改成已修复或已验收。

## 五层证据分别报告

| 层级 | 可以确认的内容 | 不能据此推断的内容 |
| --- | --- | --- |
| 源码 | 指定改动已实现、审阅或提交；注明实际源码版本 | 代码已经在当前游戏进程生效、业务完成、持续可靠 |
| 离线 qualified | 指定版本和输入下的构建、schema、fixture 或 consumer 合同通过 | 当前实机合法性、完整世界覆盖、策略正确性、动作效果 |
| 当次实机 | 本版本、本角色、本场景的真实请求、响应或状态读回 | 一次 ACK 已产生业务效果、查询成功代表战争能力完成 |
| 完成业务 | 指定动作及独立后置、后续消费、存档或冷恢复达到该项合同 | 相邻能力、全部战争、其他角色或版本也已验收 |
| 稳定持续 | 在明确的版本、场景和持续窗口内，完整路径连续运行，成本有界，结果与失败可核对 | 从提交数、查询数、历史天数或单次成功推导总体就绪 |

每条能力结论都要注明证据层级和适用范围。进入下一层需要对应的新证据；`GREEN`、`qualified`、`ready` 必须带上其合同范围。当前总体运行就绪和稳定战争能力均为**未验收**。

## 旧 5/8、6/8 的真实含义

[G2 要求账本](../autonomous-agent-progress/g2-requirements-v1.json)的分母是八个 `visible_ooda_milestones`。历史 5/8、后续 6/8 是选定可见里程碑合同的完成数，账本明确 `percent_reporting_allowed=false`。这些计数不能换算成稳定战争能力的完成率。

- M0 的合同是同帧比较继续、白和、投降，提交一次并核对战后状态及冷恢复；已完成材料包含投降。它不证明能普遍选择战争、评估胜率或持续作战获胜。
- M5 允许选定外交或战争路径；历史关闭的是选定婚姻业务及其后置。名称中的“完整战争”不能代替本次完整战争验收。
- 历史“稳定交付 GO”也有明确主机、配置、配对点和运行窗口。它不能被移作当前新开局、当前版本或通用战争能力的验收。

定义与范围见[既有分层边界](../autonomous-agent-progress/g2-requirements-and-execution.md)、[历史交付账本](../autonomous-agent-progress/g2-delivery-ledger.md)、[整局交付计划](../autonomous-agent-progress/g2-whole-campaign-critical-path-delivery-plan-2026-09-15.md)及[旧 ready 审计](g2-readiness-audit-2026-09-02.md)。这些原记录保持历史身份；本页是当前状态入口。

## 本次罗贝尔演示证明了什么

下列数字按 Root 本轮操作回报记录。本页没有追加实机调用或验收，也不借用旧罗贝尔战果、存档天数或资格。

| 当次观察 | 当前结论 |
| --- | --- |
| 罗贝尔未胜未败；兵力观测为 1454 对 2757，并有 unknown 输入 | 已有局面观测，尚无本次战争结算；人数不能独自提供完整战力、胜率或策略正确性 |
| 宣战 252/256 未校准 | 宣战相关输入尚未校准；现有替代值不能独自授权新的宣战，也不能解释为可靠概率 |
| network 返回 0，未覆盖联盟 | 关系输入不完整；零项不证明没有盟友，也不证明联盟网络已经完整枚举 |
| 返回体积约 113/661 MB；MCP 侧约 4/6 KB | 底层返回和接口投影必须分列；短摘要没有证明完整响应或计算成本已经有界 |
| Driver 状态实际文件 262,104 B，其中 `command_history` 259,592 B、63 条记录；迁移回执为 187,730,046 B → 232,225 B | 已确认持久化体积变化，迁移使用实际 `os.replace`；不同时间点的文件量与 history 子项分列，不能替代端到端响应体积、耗时或可靠性的实机验证 |
| 一次 plan 约 175 秒 | 完整规划路径存在明显时延问题；尚无修复后持续吞吐、响应预算和完整业务结果的验证 |
| 监督器预算复核到期，受管清理使 Game exit 1，随后 109 pipe disconnected | 运行链条已中断；资源清理成功不等于战争胜败、正常 Game 退出或稳定运行验收 |
| 修复 `7d1…`、`9b4…` 已提交并推送 | 属于源码修复交付；实机尚未验证，运行就绪仍为未验收 |

持久化量测来源：Root 用 `root_driver_state_profile.py` 实际读取本轮 `state/native-session/driver-state.json`，取得上述文件量、`command_history` 量和记录数；迁移回执独立记录实际 `os.replace` 前后的大小。这些是持久化层事实，不是仅有 MCP 投影变小。

退出链现已核对：supervisor PID 79696 的回执记录 `root_resume_supervisor.py:44` 的 `guard()` 预算复核期限到期产生 `AssertionError`（回执时间 16:47:32）；其 `finally` 执行 `stop_tracked(handle)`，job active 从 1 到 0，`cleanup_proven=true`、`ok=true`，Game exit 1，随后发生 109 断连。此次退出由监督器清理触发，不是 native crash 的验收证据。supervisor 自身 exit 0 及清理成功均不证明 Game 正常退出、业务完成或持续稳定。

新的宣战资格与正在进行的战争内操作应分别验证。宣战缺口不自动否定所有既有战争操作；部分战争入口可用也不自动完成战争业务或稳定性验收。

## 汇报纠正与后续验证

后续汇报先写当前能力结论，再分别列源码、离线、当次实机、业务结果和持续窗口。提交、编译或离线通过不再自动升级运行状态；历史计数和保存天数不再代替用户要求的稳定自动游玩证明。

下一轮需要用实际采用修复的运行输入复核完整 planner，分别记录完整响应体积、MCP 投影、history 的存储与返回投影、耗时、请求结果和独立业务后置。缺失、未校准或未覆盖的数据保持 unknown；已发布请求的未知结果保留原件，不重发来制造成功。

持续验证沿既有合同记录版本、角色/种子、运行窗口、资源与响应预算、连续有效 turn、实际业务结果、checkpoint 和关闭结果。整局交付的主要域闭环、同目标冷恢复无重放及独立种子要求仍未由本次演示满足。先解决当前运行与观测缺口，再按相应范围验收；不预承战争胜利、M6/M7、整局完成或持续稳定。

## 本轮旧存档恢复诊断补录

**总体运行就绪仍未验收；本轮不是 fresh 1066 罗贝尔演示。** 本节核对的是 `R/recovery/runtime01/responses` 的既有原件，`R=D:/codex-ck3-background-spill/g2-remediation-20261013`。九个具名响应先经文件量核对，合计 134,326 B，未复制原件，也未追加 Game、SDK 或测试调用。006/009 的当前角色为 31254，episode 为 `native-31254-412540d0e4eb`、`one_life`，日期为 53145648；这些旧存档状态不转记新开局成绩。

| 原件 | 当次实际观察 | 证据范围 |
| --- | --- | --- |
| `004-core-army-query.json` | core 军队查询 3.1898336 s，MCP 3678 B；`ordinary_core_v1` 返回 `partial` | 四个 scope 中三项 available，army 76 为 `native_carmy_not_found`；不是完整军事覆盖 |
| `006-runtime-metrics.json` | native payload 5,070,392 B，上限 67,108,864 B（64 MiB），sequence 1；core profile、phase `not_requested`、cache scope 4；Driver 188,783 B | 本次指定 profile 的写入成功、缓存范围和状态文件量；不证明完整世界或所有请求都已稳定有界 |
| `007-plan-turn.json` | plan 0.993728 s，MCP 2412 B，阶段 `active_event_window_query` | 计划读取当前事件；不同 workload，不能与此前 175 s 直接换算受控提速 |
| `008-invalid-profile.json`、`009-runtime-metrics-after-rejection.json` | 008 实际拒绝 `army_strengths_profile_invalid`，`request_replayed=false`；009 后续 metrics 成功 | 拒绝保留，未重发；到009的局部会话仍可用，不能把008改成业务成功或推定长期无断连 |
| `010-auto-event-turn.json` | 事件上下文 query 7.7640633 s，MCP 32,966 B，`bookmark.1070` instance 1、三个选项 | 实际查询；effect preview 与 semantic decision 未就绪，不授权最优策略结论 |
| `011-auto-event-choice.json` | 实际选择 option 3（native index 2）7.5669457 s，MCP 29,988 B；accepted/submitted，`postcondition_verified=true`，旧 instance 1 消失为 null | 已有这一次提交及事件窗消失的读回；registry 的 `semantic_optimal=false`、`campaign_utility_ready=false`、`observable_postcondition=null` 保留，不自动授物质收益或M2整体资格 |
| `012-auto-next-turn.json` | war 4 termination 只读查询 1.8893467 s，MCP 19,670 B | 读取当前战争退出选项，未提交和约、投降或胜利；不是战争结算 |
| `014-auto-current-armies.json` | core 查询 3.8335956 s，MCP 4858 B，sequence 2、`partial`；army 76 仍 unavailable | 部分军队状态可读，未知项保留；不是联盟或全战力覆盖 |

006/009、事件选择的相关日期读回及012的查询日期均为53145648。事件后的revision从2到3不能当作日历推进；上述材料没有新的实际日期advance或配对SAVE证明，因此不增加游戏日、saved days、cold或M7信用。011的执行和事件窗后置是新的限定实机材料，当前总体结论仍为未验收。

后续源码与验证状态也分别记录：

- B3仅Bridge构建的compile/link返回0，DLL标识为`029d…f96bab`、source为`f581…`（按Root本轮短标识）；cold-live仍pending，不能把构建产物当作已在当前游戏采用。
- B2 sampling query003实际返回unsupported；原外层predicate漏检三步。修复`db80d3fb`已推送，原失败保留；修复交付不自动升级采样实机资格。
- Endpoint两项新增真实pump测试PASS，`1133a56f`已推送。[具名回执](/D:/codex-ck3-background-spill/g2-remediation-20261013/acceptance/lane07/endpoint-01/receipt.json)记录returncode0、source稳定、`game_or_live_sdk_used=false`，范围仅这两项，旧247项未重跑。这是endpoint聚焦验证，不是Game业务或稳定持续验收。

fresh罗贝尔的完整coalition、8 sampler、Desk1 Game与text/record验收仍pending。后续必须继续完整普通规划流程，真实战争进入战争处理；本轮事件与战争只读路径不能替代新开局的完整业务和持续窗口，也不预报战果、M6/M7或整局完成。

本页只纠正能力状态和证据口径。机器使用、游戏占用及实机执行权限仍按最新用户指令与当次 Root 授权处理。

## 本轮修复与离线验证

普通军力查询现在显式请求 `ordinary_core_v1`，在 Native 序列化前省略九组保留研究历史；显式 `observed_history_full_v1` 保留实际观测及 null，不自动开启采样。MCP 的文本和 structured content 继续使用小型摘要，持久化保留 profile/coverage。缓存按角色、日期、public/native revision、连接、episode 和完整有序军队范围绑定，在发布时完整校验，读取时只比较绑定并独立复制。

最大的 GatheringDue 研究采样默认关闭，在复制 parent/manager 之前决定本次采样资格；关闭时仍调用原生函数一次并保留完整返回位。显式启停记录 epoch、在途捕获、保留记录和清理状态；忙碌或待清理不伪报清理成功，也不自动重试。进入 Native 启停执行后，超时、拒绝或损坏回执同样使旧军队缓存失效，不能将未知结果当成状态回滚。关闭会减少共享研究 mask 的证据，其他八类采样仍存在，不能据此宣称全部 producer 开销已消除。

离线结果：193 项既有本轮定向回归及 23 个 subtest 通过；另 54 项新采样控制回归通过。后者保留首轮缺 snapshot 的 fixture 失败、两项 capability fixture 修正及必要定向复验，未把失败覆盖成成功。C++ profile 宏 ON/OFF、实际 Gathering producer 与受控外部输入、采样 wire 兼容分别验证；这些都是限定源码与夹具的结果，不能算实机能力。

Root 的 build02 两个实际 owner TU（Bridge、Gathering）编译、链接退出码均为 0，DLL SHA-256 为 `3ed2b139fa334e8d2a50a7cdaae9f6c3048b1cdef32d2993b7dcc172a725ff96`，真实 frame 上限仍为 67,108,864 B。Runtime archive 保留 build01 的已编译适配器，不因新增独立采样状态改变公共 DTO 布局；实际 sourceDependencies 核对五个覆盖 header。此项是构建证据，尚不能证明实机返回体积和规划耗时达标。

精简回执位于当轮外置工作包 `g2-remediation-20261013/acceptance/ACCEPTANCE-PROFILE-SUMMARY.json`、`native-profile/GATHERING-GATE-MANIFEST.json`、`native-profile/build02/ROOT-BUILD-RESULT.json`。所有外置原件按统一存储策略和本轮准入期限复核，路径或哈希不是永久原件可读承诺。完整战前盟友与敌方可动员兵力上界、持续完整 planner、日期推进与战争业务结果仍须独立补齐。

## 新增修复包：构建及定向验证，实机仍待验收

八个额外军队研究采样器现在也默认关闭，原生调用、轻量时钟和正常游戏所需的状态继续保留。新的独立采样状态没有改变旧共享 DTO 或对象布局。这里记录的是源码默认值及限定测试，不声称当前旧诊断进程已经使用新模块，也不把研究采样关闭当作战争操作关闭。

战前 v2 查询绑定当前完整宣战选择、实际主线程票据和前后同帧来源；普通策略的三条宣战入口使用真实可动员下界、完整敌方与参战方覆盖及整数 3/2 风险门槛。未证明互不重叠的已集结、未集结分量取最大值；库存不能直接当作可执行军力。缺源保留 unknown，v2 查询通过本身不授权宣战。目前 diarch、宗教 authority 的实际 getter 资格及完整初始参战覆盖仍有待闭合，不能据此宣称所有宣战路径已具备实机资格。

新录像实现使用独立 OBS 配置、进程代际、端口及容量期限，校验当前游戏与决策文字来源；个人录制不作为接管目标。桌面1固定窗口和新的决策文字源仍需当次实际位置读回、画面及录像验收。

本轮新增的已执行检查：

- 普通宣战策略 41 个单元用例通过，范围是实际 Python 消费者及合成的来源证据。
- Gathering-off67D 新源码定向检查 6 场景、41 断言通过。
- Native 请求解析 220 场景、377 断言通过；桌面及进程回执验证器 6 个用例、OBS provider 12 个用例通过。它们使用受控输入，不是桌面实测。
- build04 最初 26 个 TU 中 24 个编译通过、两个失败；修正两个 CPP 后，仅补编这两项。610 成员 Runtime archive 及 DLL 链接退出码均为 0，保留原 Robert 与实际宗教工厂对象。DLL SHA-256 为 `b03c705bc78a7bfdebe537a65882e9eab414d1d609b211d12b7dd8f084fb075b`，产物 18,165,760 B；本组实际文件 532,110,824 B，在 2 GiB 生产子预算内。它尚未冷载进游戏。
- SDK v2 transport、来源绑定及真实并发缓存 CAS 的新增 12 个用例通过；Service 新增 8 个用例最终通过。首轮 Service 3 过、5 失败，原因包括 fixture 的实际规划视图和 bridge version 资格，以及 partial 二次规划元数据的错误预期；修正 fixture 后只复验失败项，原件保留。另两个真实 MCP→Service 提交前回调用例通过，覆盖先发布决策和发布异常时零 selected submission。合计 22 个唯一新增用例通过，没有重跑旧矩阵。

外置回执分别位于 `R/acceptance/lane06`、`lane08`、`lane09`、`lane10` 和 `R/native-profile/build04/repair02/ROOT-BUILD-RESULT.json`。新增请求解析 EXE 的 Defender 登记读回为 `admin_required_for_verified_readback`，不是设置成功；测试通过也不能替代管理员实际登记回执。完整新开局、录像和持续游玩仍未完成。

## 具名参战关系 getter 增量

新增 actual4 的 Character→Diarchy→Diarch 类型化关系读取和具名宗教 authority 读取，使用完整 generation ID、原生输出指针回显、Core 对象重解析、SEH 叶和两次同帧独立比对。diarchy 的实际 ID=-1 可作为该叶的已观察空值；宗教返回无效 sentinel 时仍保留 unknown，不能把读失败当作“没有宗教领袖”。宗教追随者枚举移除了未经证明的 self-authority 捷径。这里的具名 GUI getter 资格不自动证明同名脚本属性或全部 join-war 角色资格。

新公共 schema、协议、SDK 和策略均未改。Root 从实际 sourceDependencies 选出五个消费者 TU，两个 MainThread owner 分别编译，因此实际补编六个 job；六项编译、610 成员 archive 和链接均退出 0。build05 DLL 为 18,169,856 B，SHA-256 `bcfff62ead6080c05238fb97f3a2da7b6829788353ff3908431e99da9e6e9e65`；累计生产组 753,458,107 B，仍在 2 GiB 子预算内。源码前后哈希稳定；尚未冷载、尚无该 getter 的实机业务资格。

共同采样策略新增独立单 TU 验证，六场景、33 断言通过，覆盖在途关闭、拒绝忙碌重开、禁止旧 epoch 发布及 drain 后显式清理；没有重跑既有矩阵。新 EXE 的 Defender 实际读回仍未确认。

普通 claim/de jure/conquest 的开战脚本含非空公共 helper，原先只认 count0/null row 的资格不能证明这些正常路径完整。正在补当次实际节点、调用方和参战源的只读投影；现有完整盟友和联邦成员 superset 可覆盖已核对的相应脚本子集，但不能据此吞掉其余未知节点。当前新宣战资格与完整重开演示继续标记未验收。

新增回执：`R/native-profile/build05/ROOT-BUILD-RESULT.json`、`R/acceptance/lane08/common-policy-01/receipt.json`；具名来源静态合同及增量分别为 `R/fresh-run-plan/ACTUAL4-TYPED-GETTER-SOURCE-CONTRACT.json` 和 `ACTUAL4-TYPED-GETTER-SOURCE-DELTA01.json`。它们均按原准入期限复核，静态读取和编译不代表实际部署。
