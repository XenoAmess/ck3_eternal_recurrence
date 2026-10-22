# M7 剩余交付：复用已有 Clan 路径

`machine_id: xenoamess-full-tower-eb9d2c1186`；本轮只读核对始于 `2026-10-22T11:13:42Z`。同刻实际执行 `tools/ck3_live_run_id.py machine` 读回该 ID。本文只更新施工认识，不改原路线图、状态 JSON、冻结运行图或历史结果。当前依据 [10 月 22 日交接](../handover/2026-10-22-robert-source32-a41-recovery-vacation-handoff.md)保留 **G2 6/8、M7 in_progress**；本文不增加游戏日、政府或 seed 资格。

## 原合同与剩余范围

[原要求](../autonomous-agent-progress/g2-requirements-v1.json)和[已冻结解释](evidence/g2-m7-p0-original-acceptance-contract-2026-10-19.json)要求：多个 rulers、seeds、governments 的真实资格，并在 checkpoint／自然继承后恢复同一高层意图。原合同没有要求全部 18 个政府识别键，也没有固定代数或指定必须第二种 adapter family。

必须分别记录 `government_key` 与 `adapter_family`。`feudal_government`、`clan_government` 都映射 `core_landed`；真实 Clan 场景可补另一个政府键，不能称为新 family。`tribal_government` 对应 `core_tribal`。表中 `core_supported` 只表示实现适用性；具体正式政策、原生合法动作与结果仍需实际证据。[政府表及边界](g2-government-seed-qualification-12004.md)为 2026-10-07 的源码结论，本轮只复核该表与公共消费者，未在目标机器重新查询政府。

| 项目 | 已有证据及其时效、机器 | 本轮结论／仍需核对 |
| --- | --- | --- |
| 本局真实新开局与初始来源 | [2026-10-19 新局小证据](evidence/g2-m7-v20261019-fresh-campaign-zero-day-2026-10-19.json)，观察 `03:09:14Z`，外层 machine 为本机；单独 RPC 原件仍标 `unknown`，通过实际 launch／PID／birth 的明确供给关系关联 | 1066 selector、Start、首暂停帧、`native-31254-6271ac8cd441`、初始 SAVE 均已存在；不是因 `episode_seed=null` 就没有初始来源。初始 SAVE 为 68,936,116 B，SHA `381e832bb3122b1c544d5bcd505eb86b4d40456a4d37969bcf208714d0aa88f4`。本轮未读 SAVE 或重新计算其 SHA |
| 本局自然继承及以后普通 goal 消费 | [3851 自然转换](evidence/g2-m7-p0-natural-successor3851-2026-10-19.json)、[后继 goal 消费](evidence/g2-m7-p0-successor-goal-consumed-2026-10-19.json)，2026-10-19、本机；[执行专题](robert30-v20261019-execution.md)保留 31254→40526、同 campaign／origin／goal、SAVE3862／SEM3863／普通 AUTO3865 | 该自然转换子链已有实证；同一次转换的多份回执只计一次。继续同局增加连续性深度，不自动增加政府键或独立 seed |
| 真实冷恢复 | [Native26 实际 cold](evidence/g2-m7-native26-actual-cold-adoption-2026-10-19.json)，2026-10-19、本机，197 SAVE→新 Game→198 SEM／199 CAP；后续实际冷恢复由 Root 的闭件保存 | 已有同局高层意图保留。最终 M7 汇总应从现有正常维护闭件选出精确后继 SAVE／配套 Driver→实际新 Game→后来普通 plan 的来源链；本文不重读大正文，不将 SDK 轮换算新 Game，也不要求为本文额外重启 |
| 另一独立初始来源 | 历史 clean campaign `native-31254-8d3a8440eb30` 的[自然后继小证据](evidence/p50r1-natural-successor-actual-2026-10-18.json)，实际观察 `2026-10-17T19:30:18Z`、本机；另有旧 Murchad、Clan 记录，见下节 | 不同 campaign ID 或 PID 本身不构成独立 seed 证明。旧 clean campaign 的真实 NewGame／初始 checkpoint 来源、本局与旧局的汇总去重仍待从已有小证据核清；不因此重开当前 Robert |
| 另一政府的有用普通结果 | 公共 [Clan scene](m7-clan-construction-scene-12004.md)于 2026-10-16 已实现并记录合成验证；机器记录为本机，真实 Clan 动作未验收 | 未来一个实际 Clan cell 复用现有实现；不重复实现 scene、现金 provider 或资格平台 |

## Clan bootstrap 的旧 RED 已有后继 GREEN

不能只消费需求索引中的 v14 RED。原生专题 [frontend selected model](frontend-1066-selected-model.md)保留完整先后关系：

| 历史场次／来源 | 实际失败或后继结果 | 2026-10-22 公共源码只读核对 |
| --- | --- | --- |
| 2026-10-02 v12；machine_id: unknown | runtime target 没接收到两个 Bookmark 编译选项，真实 hello 未广告能力 | `native_bridge/CMakeLists.txt` 的 runtime `foreach` 已含两个选项，并将定义传给 `xar_ck3_12002_runtime`；不能重写成仍缺 provider |
| 同日 v13；machine_id: unknown | Python binding 仅接受旧 build tuple，真实 `.3` hello 被本地拒绝 | `bridge/frontend_gui_route_contract.py` 已包含精确 `.3`、`.4` adapter／version／EXE tuple |
| 同日 v14；machine_id: unknown | 原生 installer 缺 frontend executor，提交在 queue publication 前拒绝 | `native_bridge/src/bridge.cpp` 的 `.3` 分支及 `.4` core installer 已绑定现有 `ExecuteFrontendGuiRouteMailboxV1` |
| 同日 v16；machine_id: unknown | **实际 Clan bootstrap GREEN**：126.633 秒、119 calls；Yahya actor32563、raw53144328、`clan_government`、ordinary dynastic goal、真实 h1 配对 | 历史 report SHA `5b5b4eb5c00c9f9a754f4fcdb475c1490a43efd17d3adb1ab998fb899af91792`。它关闭当时共同前门故障，不证明本机当前 `.4`／新部署已验收 |

v16 来源为 `artifacts/g2-maintainer-2026-10-02/resume-12003/m7-clan-preparation/actual-v16-d4f377d9-01/actual-native-bootstrap-01`（无扩展名 JSON），冻结 source `d4f377d97b7a4f97ac85151610adbc4d4df818f8`，CK3 `.3`。本轮只读已入库专题，没有重新检查外置原件的当前可读性；其机器身份未核实，不因路径相同追认为本机成功。此前“Clan 只有 bootstrap RED”的概括应由本节勘正；原失败继续保留。

现有 Yahya target/profile、模型读取、字符选择与 Start typed steps 仍位于 `native_bridge/src/frontend_bookmark_model_probe_v1.cpp`、`include/xar_bridge/frontend_gui_route_v1.hpp`。公共旧研究 runner 已有该 profile 与对应生产者测试；本文不执行它或把旧 runner 当未来启动授权。未来 Root 应将这些已有步骤接入当次受管准备和来源闭包，核实际加载能力。

这次没有发现可由旧 Clan RED 证明、仍未修的共享生产 bug，因此没有新增补丁或重跑旧测试。如果未来真实候选再次在该路径失败，最短回归须覆盖实际 CMake target／descriptor→真实 hello identity parser→原 installer／mailbox→正常 seed producer／独立模型后验；单独宏 fixture、伪造 hello 或局部 selector 不能替代整条生产链。

## 未来最短 Clan 实机 cell

当前 Robert 首个成功 FULL、正常 SAVE 和连续推进优先；以下是后续 Root 的串行实机工作包，不是当前局的新门禁，也不要求改变本局 ruler、政府或玩法策略。

1. **选定真实输入。** 优先核旧 v16 h1／配套状态及原初始来源是否实际仍可读；机器身份、精确 build／部署可否合法接续分别核实。不能用 `.3` bootstrap 追认 `.4`。若旧配对不可用，由 Root 另排真实 Yahya NewGame；实际初始 checkpoint 自身可成为新 seed 来源，无需新造 RNG 数字字段。
2. **复用正常身份与意图。** 当次后台 Steam 离线准入、有限容量、来源闭包和受管 Game 生命周期沿共享流程。保留真实当前 actor、`clan_government`／flags、`core_landed`、原 campaign／origin／goal 和同帧绑定。模型中的政府不能代替入图后的实际政府；不为了记录元数据增加每回合 Government 查询。
3. **消费一个真实有用机会。** 已有 `construction_scene_scope_v1.py` 将同帧 Clan Root 接入普通建设消费者；`construction_formal_consumer.py` 复用 current-cash-v2。仅考虑当前玩家自己拥有的合法地产，使用实际 final legality、金币报价、当月 gross／完整 expenses／NET、既有承诺和军费储备。按正常政策选择，条件不足延期建设并继续推进，不为验收换差方案。
4. **保留真实结果。** 唯一 action／barony／province／slot／building 身份、原生报价、提交与独立项目及钱包后验分别记录；再保留以后普通 turn 对原结果的消费。若结论涉及完工或收入，必须等真实完工和相应材料，不能以著录增收值或开工 ACK 代替。已有 pending、结果未知动作保持零重发。
5. **复用必要维护边界。** 正常 SAVE 后，以精确配对和真实新 Game 验证同 goal、当前 actor 与既有项目恢复，随后普通 plan 继续。采证与下一批推进并行，只交给离线消费者已有小回执。该 cell 可补 Clan 的真实结果与另一初始来源；完整 M7 仍由原合同逐项汇总，不以一个动作自动宣布完成。

Tribal 不是更短替代路线。[已有研究](research/sdk37-edl-incident-identity/tribal-market-REPORT.md)指出 `market_villages_01` 有金币及威望成本；当前 Python 选择器与 Native submit 都保留金币限定，`.4` submit binding 会拒绝非金币槽。多资源余额、预算、提交和独立扣款／项目结果尚须同步实现并完整验证；不能只扩政府白名单。当前能力不因此被写成 Tribal 已可玩。

## 本工作包边界与保留

本机此次只执行 machine ID 读取和文档／生产源码只读核对，新增本文件一份，获 Root 限额 **16 KiB**；没有 Git、Task、财务、账本、Game／Steam／RPC、测试、构建或外置目录操作，未读实际 Driver、SAVE 或视频正文。按[统一存储策略 1.0.0](../storage-retention-policy.md)作为 `record` 于 **2027-04-20** 复核；不因本文引用自动续存历史大原件。本次是出处纠正与后续执行准备，不授新增 M7、性能或三十年成绩。

## 11:34Z 后继：注册普通服务的软件闭环

同机器于 `2026-10-22T11:34:44Z` 完成新增[注册 Clan compound](../../ck3_autonomous_player/tests/unit/test_g2_clan_construction_registered_service_compound_v1.py)：**2 tests、0 skip**；整新模块 `mypy --strict --strict-equality --follow-imports=skip` 实际 exit0，只授该文件，不外推导入的旧模块。

Feudal／Clan 均实际经过 CLI、注册 MCP、生产 Service／transport：现金及合法报价→唯一提交→同帧 pending 不重发→后帧独立项目／钱包材料→持久小账本的新消费者→普通后续消费。两场候选精确相等；另覆盖 Clan 缺 NET、错现金 actor、默认关闭及 Tribal 不准入。原生回复、进程身份和 baseline chooser 是显式合成 seam，没有真实 Game／Native 执行或 checkpoint 冷载。

后继实际结果在 Root 获准范围 `current-saved-a46-runtime-prep01/parallel-m7/RESULT-03.json`，新测试源 17,329 B，SHA `545483bb364cb3eb8263caf4c37c2c5afa5c9abce0205cb5447b7982be3056bc`。01 保留旧 fixture 缺 wait 方法的 RED；02 保留误将同帧 pending 期望为推进的 RED。只修测试适配和错误断言，生产守卫未放宽。后继 Root 负责持久 CI 接线及真实 Clan cell；这些软件结果不改变 M7 或本局日数。
