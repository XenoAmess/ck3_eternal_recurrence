# 第三期围城：普通 claim 的城破、占领与战分（1.20.0.3）

本期可以用一场普通 `claim_cb` 证明：同一座城的围城结束、占领者出现，以及占领、战斗、俘虏、目标持续控制四项战分各自怎样变化。当前接口能读取原生四项整数和总战分；它尚未公开原生占领分母、目标控制比例、逐俘虏计分和小数 ticking 累计值。因此成片应围绕真实前后读数展开，不能把一次县首府城破自动解释成全县占领、80% 目标成立或必然俘获敌方主战者。

2026-10-02 离线研究基线：`D:/we3` HEAD `6a837a1ecd9b027170f607242f6f02724908dc14`；本机 EXE 101,039,736 bytes，SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。解释器显式为主工作树 `tools/.venv/Scripts/python.exe`（Python 3.14.7，pefile 2024.8.26，Capstone 5.0.7）。本研究没有启动、连接或注入 CK3，没有操作 Steam 或桌面，也没有新增 runtime 能力。

## 实际路径与证据等级

`.3` factory 先核对实际新 EXE SHA，随后复用已逐项比较的 `.2` ABI；对外身份仍为 `.3`。真实实现源文件保留 `ck3_12002*` 名称。[factory](../../ck3_autonomous_player/native_bridge/src/ck3_12003_adapter.cpp)、[迁移与历史实机边界](crozier-1.20.0.3-native-migration.md)、[原始复用账本](../../ck3_autonomous_player/native_bridge/research/ck3_1_20_0_3_abi_reuse.json)。

本次直接读取上述 `.3` EXE，冻结了 **24 个 PE runtime spans、64 条关键指令**，精确 SHA、字节和重新解码检查 PASS。永久窄证据和采样字段见 [episode03_occupation_war_score_12003_static.json](../../ck3_autonomous_player/native_bridge/research/episode03_occupation_war_score_12003_static.json)。`.pdata` span 可能只是逻辑函数的一段，证据不把单段边界冒充完整函数。外置反汇编、脚本及回执位于 `D:/ck3-war-episode03-20261002-a01/`，不修改旧 1.19 / 1.20.0.2 实机记录。本次新增结论是离线静态依据；本期 `.3` 的围城、落城及原版画面仍由新的 capture attempt 证明。

| 观察 | 现有 MCP / 路径 | 可以证明 | 当前边界 |
| --- | --- | --- | --- |
| 战争与目标城 | `ck3_take_snapshot`；`ck3_get_war_state` | full-generation WarID、玩家阵营、主战者身份、targeted titles、目标省及占领者 | `get_war_state` 是切片；完整日期、native revision 和连接绑定须同时保留 snapshot / diagnostics |
| 本城围城状态 | snapshot 的 `active_wars[].objective_province_states[]` | SiegeID、实际围城军队 join、work/progress、驻军、占领变化 | 丰富围城字段需要 paused frame；当前 `.3` descriptor 没有独立 province-local-siege capability，不能以 Python 存在同名 parser 声称已支持任意省 |
| 战分四项 | `ck3_query_war_termination_options(war_id, expected_revision)` | attacker-relative `imprisonment/battles/occupation/ticking`，双方绝对总战分、war age、实际 CB key | 名称含 termination，但本期只取只读分项；不发送任何战争结束命令，不讲和平条款 |
| 当前玩家俘虏 | 条件注册的 `ck3_query_player_prisoner_collection_private_v1(expected_revision, ransom_ordinal=0)` | 完整、最多 64 人的 custody ID 集与同帧 jailer 关系 | DLL 需 `XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1`，MCP 需 `--private-prisoner-collection-query`；均默认 OFF；无需打开 ransom/release 动作 |
| 双方主战者和前三继承候选 custody | `ck3_execute_step("query-war-prisoner-release-pairs-v1-<WarID>", expected_revision)` | paused、全双方 participant scan、主战者与 primary-title 前三 successor 候选、对侧 jailer pairs | 同一 private compile flag 控制 capability；只读 input graph，不是逐人战分 DTO；本期不使用其战争结束语义 |
| 原版战争总览画面 | vanilla `WarOverviewWindow` | 总数及四分项、各项 tooltip 的原版显示 | 现有 `ck3_query_ingame_ui_window_v1` 枚举仅 `character/army/combat/knights`，没有 `war` 或四种 war-score tooltip；有工具注册不等于 `.3` 已提供该画面路线 |

源绑定：[adapter capabilities](../../ck3_autonomous_player/native_bridge/src/ck3_12002_adapter.cpp)、[MCP 工具及默认关闭参数](../../ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py)、[prisoner transport](../../ck3_autonomous_player/src/xar_autoplayer/bridge/player_prisoner_collection_private_transport.py)、[participant / successor reader](../../ck3_autonomous_player/native_bridge/src/ck3_12002_prisoner_war_retention.cpp)。实际捕获前必须读取当前 hello/capabilities 并匹配 `.3` 身份；这张表描述已有源码入口，不代替当次 tool discovery 或实机查询成功。

## 城破后的占领分怎样形成

`ReadObjectiveProvince` 读取 province 的原生 occupied getter 和 `+0x73C` 占领 CharacterID，只有完整代数 ID 可解析才发布占领归属；`active_siege=null` 还必须伴随 `siege_observable=true`，才表示确实没有围城。[Province reader](../../ck3_autonomous_player/native_bridge/src/ck3_12002_province.cpp)、[JSON wire](../../ck3_autonomous_player/native_bridge/src/bridge.cpp)、[Python null / observable 合同](../../ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py)。

真实原生 occupation getter 是 RVA **`0x2C0DDB0`**，不是客户端根据省数拼出的值。此次 `.3` 反汇编确认：

1. 按实际战争阵营，读取相对方主战者和 participants，再经 native territory collector 与角色/领地关系筛选。`0x2C0D5B0` 单独递增 eligible 分母与 occupied 分子；占领者要通过完整 CharacterID 和本方 participants 核对。这里的计数集合不是 snapshot 的 target province 数。
2. 使用 Q100000 算术计算占领比例，加上每个已占男爵领的附加量，乘以该阵营 **加载后的 CB scale**。
3. 对这部分先夹到 `[0, CB occupation cap]`；再根据 CB capital policy、敌方实际 realm-capital province、占领者是否属于本方，加首都项；最后向零截断为整数。
4. 若 CB 的 full-occupation 特殊分支成立，返回 packed authoritative `100`。生产 breakdown 和总战分都有对应提前返回分支，不能继续把其他分项叠加。

普通非特殊分支可写为以下复算框架；这里的 `n/N` 必须来自原生相同 collector，不能用目标省列表替换：

```text
Q = 100000
R_raw = trunc((n * Q) * Q / (N * Q)) + n * per_barony_scale_raw
B_raw = clamp(trunc(R_raw * cb_side_scale_raw / Q), 0, cb_side_cap * Q)
O_side = trunc((B_raw + qualifying_capital_bonus * Q) / Q)
```

`n=0` 的 base 为零；`N=0` 不是可以自行填一个分母的情况。反汇编还包含 native overflow fallback，以上式子仅表示通常非负输入的算术路径。用同一组原生原始值复算必须保持其每步截断，不能只对最终浮点数取整。

本机原版 `claim_cb` 明确设置 attacker war-goal threshold **0.8**、双方 occupation cap **150**；未在该 CB 中重写 occupation scale / ticking rates。本机 NWar 定义 occupation scale **90**、per-barony scale **0.04**、首都 bonus **10**。[普通 claim 定义](<C:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/casus_belli_types/00_claim.txt:813>)、[NWar](<C:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/defines/00_defines.txt:726>)。本次还沿 define-key 的 native 读取路径，把 per-barony 和 capital 对应到 getter 使用的具体存储；它们是加载后的运行时值，并非在 EXE 文件中直接存着 0.04 和 10。

所以“攻下一个城固定给多少分”仍不能只由常量回答：新占领可能涉及不止一个 holding，native eligible 集可能变化，首都条件另算，integer truncation / caps 也影响差值。现有四项前后差值可以准确陈述，本城的独立公式值则需要 `n/N` 与 loaded CB policy。NWar 中 `SIEGE_WAR_CONTRIBUTION_MULTIPLIER=10`、monthly contribution `2` 属于 **war contribution**，不是给每座城加 10 战分。defines 的 0.04 行仍留有按 0.01 编写的旧注释例子；不能用那段注释替代 native 算术。

## 目标占领与 ticking

本期只选择同一 ordinary `claim_cb` 和一组冻结 targeted titles，优先用单一县级目标简化叙事；不用历史 Raiktor 特殊“easy war”或旧 WarID 代替新场景。

当前 `CollectObjectiveProvinceIds` 对县/男爵领返回 title-province，对更高头衔沿 de-jure children 递归，去重并约束 budgets；world snapshot 只投影这些省。[目标递归](../../ck3_autonomous_player/native_bridge/src/ck3_12002_province.cpp)、[world snapshot](../../ck3_autonomous_player/native_bridge/src/ck3_12002_world.cpp)。它没有读取 held-goal evaluator 的原生比例。CB schema 还存在 `use_de_jure_wargoal_only`、`check_all_defenders_for_ticking_war_score`、`ticking_war_score_targets_entire_realm` 等独立控制项；schema 中列出的示例值不能当成当前 claim 的实际 loaded 值。[CB schema](<C:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/casus_belli_types/_casus_belli.info:5>)。

原版概念明确：全县占领需要该县 **所有 fortified holdings** 均被占领，县首府总是设防领地。[原版概念，第 684 行](<C:/SteamLibrary/steamapps/common/Crusader Kings III/game/localization/english/game_concepts_l_english.yml:684>)。当前县级目标只投影首府，缺少同县其他堡垒的完整列表。因此一座首府从未占领变为已占领，可以证明本城城破，不能单凭它证明全县、原生 80% 阈值或全部 objectives 成立。

原生 ticking side getter **`0x2C0EE70`** 读取缓存累计值与有效标记：attacker `war+0x40 / +0x78`，defender `war+0xA0 / +0xD8`，然后向零截断为显示整数。当前 DTO 省略这些原始小数和 goal-held clock。原版日 rate 为双方 **0.055**，攻击方 delay **0 天**，防守方 **365 天**；这是默认参数，不是当前已经计时的天数。[NWar](<C:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/defines/00_defines.txt:727>)。

城破后一两天 ticking 整数仍为 0 可以是正常截断，不能据此宣称目标没成立。`war_duration_days` 是整场 war age，不是“目标被持有的持续时间”；不得用 `war_duration_days × 0.055` 复算 ticking。若本期要展示 ticking，保留即时落城读数，并在后续明确日期、目标仍保持的 paused frame 再读；只有 observed delta 或 native/UI held-objective 信息才进入字幕。

## 俘虏怎样影响这一场战争

原生 imprisonment 入口 **`0x2C0C310`** 经 side classifier `0x2C0B800 → 0x2C0B4D0` 工作。本次 `.3` 字节证明：

- 主战者的 imprisonment relation 必须由对侧 participants 扣押；成立时设置独占标志并直接返回 **100**。总战分入口 `0x249AC40` 优先使用该结果，攻击/防守对侧改变符号。抓到任意盟友、廷臣或普通 prisoner 不能替代这个条件。
- classifier 分别统计被对侧扣押的 direct vassals、是否存在被扣押 spouse，并扫描有序 cached succession list。继承人循环在首个满足对側 custody 的位置记录 ordinal 并退出，最终只加 **一项** heir table 值；不是把已抓到的三个继承人的分数全部相加。
- 本机原版 heir table 为 `{50,25,10}`；vassal / spouse defines 均为 0。顺位取决于当前原生缓存和加载后的表，不能只看姓名、血缘或 prisoner collection 数量。[NWar](<C:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/defines/00_defines.txt:737>)。

现有 private collection 可以比较本玩家完整 custody 集的前后新增 ID；它不标记“此人刚因这座城被俘”，也不返回本场 score class / amount。participant/successor query 可补双方主战者、primary-title 前三候选及 jailer pairs，但它读取 primary-title succession（`+0x150`），score classifier 使用 CharacterLandState 缓存 succession（`+0x3A0`）。两者没有在当前 DTO 中做逐项同帧 equality，所以候选位次不能自动冒充原生计分 ordinal。

成片可以明确拍到“新增了谁、当前由谁扣押、imprisonment 分项怎样变化”。若没有新增有价值俘虏，则照实说该分项未增加；不能为讲计分机制制造捕获、替换 attempt 或预设抓到敌方领袖。原版 valuable-prisoner / ordinary-prisoner 概念提供分类语义，本期不展开其战后处置。[概念，第 2039–2042 行](<C:/SteamLibrary/steamapps/common/Crusader Kings III/game/localization/english/game_concepts_l_english.yml:2039>)。

## 一场战例的最小采样计划

所有采样使用同一 EXE/build、actor、episode、connection generation、full-generation WarID 和 targeted-title 集。每个 query 按 **public revision** 发起，由 driver 映射到该帧 native revision；保存返回 envelope 的 query sequence / snapshot revision。不要混淆两个 revision 域，也不要把 `ck3_get_war_state` 切片当成全部帧元数据。

| 阶段 | 必采字段 | 目的 |
| --- | --- | --- |
| `pre-fall`：最后一个 paused 未占领 frame | snapshot_id/revision/native_revision/date_raw，paused/map_ready、actor；WarID/player_side/primary opponent/target titles；province 的 occupation observable、false 占领、fort/garrison/besieging strength；active SiegeID、ArmyID、work、total_work、fraction、days_left、breach/assault；四战分和实际 `active_casus_belli_identity.canonical_key` | 冻结同一战争、同一省、真实未落城围城状态 |
| `first-observed-fall`：第一帧 observed 城破 | 同样帧绑定、WarID/目标集；`occupation_observable=true,is_occupied=true,occupying_character_id` 可解析；`siege_observable=true,active_siege=null`；四战分和总数；本方参与者归属 | 联合证明 occupation 与 SiegeID 消失，不靠 days_left=0 或进度接近 100% |
| `same-frame-after`：paused 再读 | 同一 date/actor/war/province；四项原生查询结果；完整输出 bytes/hash | 排除 transition/unavailable 和混帧拼接；同一 paused 稳定状态可以对应新 revision，按实际返回记录 |
| 可选 `held-objective-later` | 明确日期、原有目标占领未改变、ticking 整数及原版目标 tooltip | 演示实际持续控制变化，避免用整场 age 预测小数 |
| 可选 custody 前后 | `date_raw/played_character_id/total_count/returned_count/collection_complete`；每个 full prisoner ID/jailer ID/custody_relation_verified；同帧 participant/successor scan flags | 有完整 before/after 才谈新 custody；没有捕获也保留零变化 |

还需保留城破期间的相关 player/allied/enemy armies，以及其他 objective province states 的变化。若同时发生战斗结束、其他占领、captivity 或日期推进，四项 delta 能解释同期变化，但不能把整个 total delta 都归因给本城。

可直接复算的输出为：

```text
Delta_i = score_i(after) - score_i(before), i = imprisonment,battles,occupation,ticking
Delta_total = attacker_total(after) - attacker_total(before)
player_signed_i = i             if player_side == attacker
                  -i            if player_side == defender
residual = attacker_total - sum(four_native_components)  # 诊断值，不作失败门禁
```

所有四项都是 attacker-relative；总数另有 player-relative / defender-relative 表示。[原生 ReadBreakdown / 总战分查询](../../ck3_autonomous_player/native_bridge/src/ck3_12002_diplomacy.cpp)、[DTO](../../ck3_autonomous_player/native_bridge/include/xar_bridge/game_contract.hpp)。总战分入口有 leader-captured / full-occupation 提前返回，以及正常路径 `[-100,100]` 夹限；所以 `residual != 0` 不自动构成异常。breakdown 必须是四项完整对象，`null` 代表不可观察，绝不是四项零值。[Python normalizer](../../ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py)。

## 原版画面与最小缺口

`window_war_overview.gui` 的真实 categories 是 `warscore_objectives`、`warscore_battles`、`warscore_occupation`、`warscore_prisoners`；handler 分别为 `GetTickingWarScoreTooltip`、`GetBattlesWarScoreTooltip`、`GetOccupationWarScoreTooltip`、`GetImprisonmentWarScoreTooltip`。occupation tooltip 另有 county/partial/capital/full-occupation 标签，prisoner tooltip 区分 leader/spouse/vassal/heir。[原版总览](<C:/SteamLibrary/steamapps/common/Crusader Kings III/game/gui/window_war_overview.gui:1978>)、[原版标签](<C:/SteamLibrary/steamapps/common/Crusader Kings III/game/localization/english/wars_l_english.yml:3>)。

本期最低可见证据是同一战争的原版总览总数和四项，以及本城实际占领画面。若要把独立占领公式或“80% 目标成立”也做成可复算画面，还需以下窄只读观测；不需要扩展战争结束动作：

1. 原生 `n/N` 与贡献的 exact holding/title/province、occupation side、loaded CB scale/cap/capital/full-occupation flags。复用原生 collector 的真实输出；不能从 target-list 长度猜分母。
2. 原生 held-goal ratio / 目标省集合 / clock，或同帧原版 ticking / occupation tooltip 全文。需要分别核实其集合与 current snapshot 的 de-jure 首府列表。
3. 如果本场出现俘虏分变化，补 score classifier 的 leader、spouse、vassal、cached heir ordinal、jailer participant 身份以及 native authoritative 标志；现有 collection 只证明 custody。
4. 若需要解释小数 ticking，补 side raw cache / validity；当前 integer DTO 足以讲观察到的整数变化，但无法分辨“尚未积到 1”与目标尚未成立。

这些属于已定位的只读 getter / 输出缺口。本研究仅冻结位置与采样合同，没有接线或调用它们；没有新实机证据时，字幕保持现有可观测范围。

## 失败边界与本次检查

- query unavailable、timed out、paused/core/WarID/actor 不匹配，或同帧前后图谱不稳定时，保存原 RED 与原始响应，在新 attempt 重采；不能填零、用旧结果补新帧或宣称城破已验。
- `occupation_observable=false`，或 `siege_observable=false` 且 `active_siege=null`，不能当成未占领或围城结束。目标 row 不完整、预算超限、stale full ID 都不能升级为完整县/目标控制证据。
- 俘虏 collection 不完整或超过 64，candidate scan flags 不全、两套继承名单未互证时，停止逐人 attribution；四项原生分值仍可以独立记录。
- 一次城破若战争同时失效、WarID 改变、主战者继承或 actor/连接改变，不能拼成同一场前后测。正常 pause/query ACK 和静态 ABI PASS 不能替代原版画面、实际落城、完整视频观看或成片签核。
- `.3` war/siege-specific 实机边界由当期新 attempt 决定。既有 `.2` attempt 21 只证明 siege work 增长、days-left 减少，不证明本期落城；`.3` nonwar primitive 验收也不外推成全部战争能力。[旧进度证据](ck3-1.20.0.2-r3-war-and-siege-live.md)。

本次必要检查已完成一次：精确 EXE SHA、24 个 span SHA 和 64 条指令的 bytes/Capstone decode 全部 PASS，源码与原版关键文件 SHA 已入窄 JSON。没有运行游戏、测试生成器、修改 shared native、提交或推送；根线程拥有本期采集与主线交付。
