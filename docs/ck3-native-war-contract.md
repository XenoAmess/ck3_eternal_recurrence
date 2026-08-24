# CK3 1.19.0.6 原生战争闭环契约

本页定义 `native-headless` 的战争状态、命令和最小决策闭环。该路径只走注入 DLL 的 named pipe；CK3 窗口最小化时仍可运行，也不会回落到 OCR、键鼠或窗口聚焦。

## 2026-08-24 动态目标与军队运行态

- `game.state.war-objectives` 发布 `targeted_title_ids` 和按目标头衔 de jure 层级解析出的
  `war_objective_province_ids`：男爵领目标取自身省，伯爵领目标取首府男爵领省，公国/王国目标递归发布全部
  de jure 伯爵领首府省。`enemy_primary_default_raise_province_id` 只保留为历史/诊断字段，不再作为可自动
  行军的目标；完整 row map 中只有
  `occupation_observable=true` 的省逐省覆盖 legacy 完成推断，unknown 省保留旧推断。仅当全部 exact 行的占领
  都可观测时，planner 才只处理真实 exact 目标，并在全部占领后停止使用默认集结省。默认集结省不是 war goal。
- 军队运行态使用 `army_state` / `army_state_code`：`combat=2`、`sieging=3`、
  `retreating=6`、`moving=7`。`combat` 只允许有界接触推进，`sieging` 推进围城，
  `retreating` 的 30 游戏日只是整体恢复期限；每个 observation slice 最多一日。超过期限后仍以有界 `life-advance`
  等 CK3 释放军队，不能在暂停地图上以 `selected_step=null` 自锁。
- 每个 `life-advance` 结果持久保存 paused-to-paused 的 `war_progress_before/after`，包括目标省占领与
  exact siege 的 fixed-point work。四个目标省 capability 各自独立 gate；字段出现但 capability 未广告时
  planner 不使用，`null`/`observable=false` 也永远不是零。每个可观测省只有当前占领者属于已知玩家侧
  CharacterID 才完成 exact 目标；目标被夺回会重新进入候选。不可观测省继续保留“离开 `sieging` 且涨分”推断。
- 玩家确实参与 active siege 时，`life-advance` 使用 7 日上限；running snapshot 按契约不读
  `CSiege`，所以运行帧中的 `siege_observable=false/active_siege=null` 不会被误判成围城结束。暂停后的同一
  `siege_id` 若 7 日内 `current_work` 与 `progress_fraction` 均未增长，或原生
  `besieging_strength < garrison_size`，当前省被拒绝并立即轮转到下一个 exact 目标；相等仍可推进，
  有增长则继续围城。
  全部 authoritative exact 目标完成后，planner 只做有界结算推进并等待战争状态改变，不恢复追逐可见敌军。
  legacy 快照仍将同省接触限制为 14 日或两次 probe；一次明显败退（分数下降至少 20）使对应敌军/省进入
  90 日冷却。
- `move_deferred` 不再每 turn 重试：同一目标按 7/14/30 游戏日退避。已接受且仍在
  `moving` 的 exact 目标继续 `life-advance`，不重复提交 move；若 exact 运行态已回到
  `regular`/`sieging` 等非行军状态且原生路线为空，旧 move intent 立即失效。

以上状态均来自最小化 CK3 的 native snapshot/command history，不需要 OCR 或恢复窗口。

## Snapshot

顶层 `active_wars` 是数组；每场战争包含：

- `war_id`
- `player_side`: `attacker` 或 `defender`
- `primary_opponent_character_id`: 玩家对侧的 primary war leader；完整 `CharacterID` 已按 generation 重新解析，过渡帧无法解析时为 `null`
- `player_is_primary_war_leader`: 玩家是否正是本方 primary war leader；它是 `enforce-demands` 的必要前提
- `targeted_title_ids`: 该场战争 `CCasusBelli.targeted_titles` 的完整 `TitleID` 数组
- `war_objective_province_ids`: 每个目标头衔按原生 de jure 子头衔顺序展开并稳定去重的可围城目标省。男爵领取自身省；伯爵领取 `+0x240` 首个 de jure 男爵领的省；公国、王国及更高层级递归到全部 de jure 伯爵领并取各自首府。每场战争最多解析 4096 个 generation 匹配的头衔，递归深度最多 8；任一目标的层级出现失效 ID、非法 tier、无首府或越界数组时，该目标的整组省份不发布，但保留 `targeted_title_ids` 和其他可完整解析的目标
- `objective_province_states`: 与 `war_objective_province_ids` 同序的 additive 省份状态；下述四个 capability 分域公布，未知 build、partial adapter、过渡帧或超出共享预算时保持空数组/不可观测，不能把 unknown 当成零
- `enemy_primary_default_raise_province_id`: 对方 primary 角色的原生默认集结省；无法解析时为 `null`。它不是解码出的 war goal、首都或真实行军目标；当前只为诊断与旧 adapter 兼容而发布，不是 planner 的自动目标
- `player_relative_war_score`: 相对玩家视角的整数战争分
- `allied_armies` / `enemy_armies`: 当前能从原生对象读取的军队数组

顶层 `player_armies` 保留玩家仍在场的可控军队。它不能只从 `active_wars` 临时推导：战争结束后的下一帧必须还能看见残留军队，planner 才能发出解散命令。

### Exact 目标省状态

每一项 `objective_province_states` 的稳定 JSON 形状为：

```json
{
  "province_id": 2585,
  "occupation_observable": true,
  "is_occupied": false,
  "occupying_character_id": null,
  "fort_level": 2,
  "garrison_size": 500,
  "besieging_strength": 650,
  "siege_observable": true,
  "active_siege": {
    "siege_id": 16777217,
    "besieging_army_id": 83886341,
    "player_army_besieging": true,
    "progress_fraction": {"raw": 25000, "scale": 100000},
    "current_work": {"raw": 2500000, "scale": 100000},
    "total_work": {"raw": 10000000, "scale": 100000},
    "days_left": 12
  }
}
```

- `occupation_observable=true` 才允许解释 `is_occupied`。占领者来自 `Province+0x744` 的完整 `CharacterID`；非 `-1` 时必须按 generation 回查 Character storage，失败则整个占领域保持 unknown。未占领是可观测的 `false/null`，不是 unknown。
- `fort_level` 是 plain `int32`，零是合法值。它和占领状态都是 Province 直接标量 getter，可在 running snapshot 发布。
- `garrison_size` 与 `besieging_strength` 都是 plain 当前兵数，不使用 fixed-point scale；前者来自 Province wrapper `0x220E710`，后者来自 `0x220E580`。后者正是原生 `CSiege.GetSiegeMenBalance` 的进攻方分子，可用于判断“围城军少于守军/进度停滞”。这两个 getter 会进入可变 Holding/CUnit 子图，因此只在 paused snapshot 可观测。
- paused 行中 `siege_observable=true, active_siege=null` 明确表示 `Province+0x790 == -1`，即当前没有围城；`siege_observable=false` 才表示未读取或解析失败。running snapshot 不进入 CSiege storage，固定保持 `siege_observable=false`。
- active siege 必须依次通过完整 `SiegeID` storage roundtrip、`CSiege+0x08` full-ID、原生 alive gate 和 `CSiege+0x200 == Province*` 回指；任一失败都不发布部分 siege。`CSiege+0x208` 是内部 `CArmyID`，只有与本帧 generation-valid `CUnit+0x178` **唯一**匹配时，才映射为公开 `ArmySnapshot.army_id`；零个或多个匹配均保持 `null`。任一匹配属于玩家仍可令 `player_army_besieging=true`。
- `progress_fraction` 是 CK3 的 0..1 CFixedPoint 比例，`raw=100000` 才是 100%，不是 UI 百分数 100。current/total work 与它共用 `{raw,scale:100000}` 表示，但工作量本身不能重命名成兵数或天数。比例越界或工作量为负时整个 active siege 被抑制。
- `days_left=0` 合法；原生 `INT_MAX` 表示失效、停滞或没有每日进度，桥接为 `null`，绝不发布成 2147483647 天。
- rich state 使用全 snapshot 共享的 256 行预算：暂停时 heartbeat 仍每 250 ms 运行，不能让最多 4096 个目标省各自反复调用多组引擎 getter。按战争原子发布；一场战争的完整列表放不下时，该场 `objective_province_states=[]`，不发布截断前缀。fixture 构造 257 个完整郡首府单独钉死该边界，并覆盖目标树 4096 上限、running/paused 分界、无围城与 unavailable 区分、ID generation、alive、Province 回指、非法进度、停滞天数和内部军队 ID 歧义。

军队 canonical 字段为：

- `army_id`, `owner_character_id`
- `soldiers`: 非负整数；当前构建若尚未稳定解析兵力偏移，允许为 `null`
- `current_province_id`: 军队正在生成或销毁、原生对象暂时无省份时允许为 `null`
- `route_province_ids`: CK3 原生“剩余路线”数组，严格保持引擎顺序和重复项；不人为补入 `current_province_id`。每项都必须经当前省份表解析，整条最多 4096 项；任一非法项或越界容器都原子发布 `[]`，绝不发布部分前缀。完整数组只在 paused snapshot 读取；running snapshot 固定为 `[]`，此时表示“未做完整读取”，不能解释成“没有路线”
- `move_target_province_id`: 原生路线最后一个 `SUnitPathProvinceInfo` 的省份；无有效路线时为 `null`
- `move_target_observable`: 仅当 DLL 成功解析了非空原生路线末项时为 `true`；running snapshot 仍保留旧版单次末项读取，不遍历中间项
- `army_state_code` / `army_state`: `1 regular`、`2 combat`、`3 sieging`、`4 embarked`、`5 gathering`、`6 retreating`、`7 moving`、`8 raiding`、`9 bartering`
- `in_combat`: `CUnit` 关联的 `CArmy+0x128` 是否解析到 generation 匹配且存活的 `CCombat`；不是“与敌军同省”的推断
- `retreating`: `CUnit+0x170 > 0` 的直接投影
- `controllable`

Python 会拒绝类型错误的 ID、阵营、分数和数组，同时把早期 fixture 的 `soldier_count` 输入别名统一投影为 `soldiers`；MCP 输出永远使用 canonical 名称。`route_province_ids` 是 additive 字段，但 Python 的 army normalizer 必须显式复制并校验它；仅依赖 `**state` 不会保留军队对象内部的未知键。

## Capability 与具体 step

DLL hello 广告：

- `game.state.war-primary-opponent`
- `game.state.war-objectives`
- `game.state.war-objective-occupation`
- `game.state.war-objective-fort-level`
- `game.state.war-objective-garrison`
- `game.state.war-objective-siege-progress`
- `game.state.army-routes`
- `game.command.preview-move-army-N-to-N`
- `game.command.raise-troops-default`
- `game.command.move-army-N-to-N`
- `game.command.disband-army-N`
- `game.command.split-army-half-N`
- `game.command.merge-armies-N-with-N`
- `game.command.enforce-demands-N`
- `game.command.query-declarable-wars`
- `game.command.declare-war-N`

Python 根据当前 snapshot 展开为：

- `raise-troops-default`: 有活动战争且没有可控军队时才出现
- `move-army-<army_id>-to-<province_id>`: 可控玩家军队与可见敌军当前省的有效组合；存在 exact `war-primary-opponent` capability 时，也始终展开有效的 `enemy_primary_default_raise_province_id`，即使敌军仍可见
- `disband-army-<army_id>`: 每支当前可控玩家军队各一个
- `split-army-half-<army_id>`：仅由 exact template 为每支当前可控 public CUnit 展开
- `merge-armies-<destination_army_id>-with-<source_army_id>`：仅由 exact template 为同省、distinct、
  `controllable=true` 的 public CUnit 展开两个方向的 ordered pair；已知 combat/retreating 的军队不进入候选，
  普通 moving 不在 Python 侧一概拒绝，movement-lock 留给 native validator
- `enforce-demands-<war_id>`: 每场当前活动战争各一个；planner 只在玩家视角战争分达到 100 时选择
- `query-declarable-wars`: 无活动战争时显式运行一次 CK3 原生 CB evaluator；该查询可能遍历很多角色，绝不放进 250ms heartbeat
- `declare-war-<declaration_id>`: 只从最新查询结果展开。`declaration_id` 是本代运行时的
  `target-cb-index-configuration-index` opaque choice，不是跨版本的 CB ID

占位模板本身不会暴露给 planner。若军队已在目标省或已经以该省为目标，相同 move step 不再广告，避免提交无状态变化的重复命令。

`preview-move-army-<army_id>-to-<province_id>` 只在地图已暂停时运行 CK3 原生路线规划器。成功结果为
`route_preview={status:"available",army_id,origin_province_id,target_province_id,route_province_ids}`。公开 `origin_province_id` 固定为同一 paused snapshot 中军队观测到的当前省；行军已进入省际边时，CK3 `ResolveMoveOrigin` 可能返回该 snapshot 剩余路线的首项。1.19.0.6 adapter 只接受“观测当前省”或“精确 paused route 首项”这两种 native effective origin，其他值 fail closed；两者不同时把 effective origin 插到未经简化的 A* 结果最前，保留回环与重复省。只有“目标省 = 观测当前省 = effective origin”才返回空路线；若正在省际边上而目标是观测当前省，仍须走完当前边后由 A* 返回。目标等于不同的 effective origin 时返回只含 effective origin 的单项路线且不调用 A*。它复用 move 的 mode/character/army gates，但只构造、复制并析构 caller-owned 临时路径，既不绑定/调用 apply RVA `0x2248450`，也不进入 command queue。worker-thread 静态审计确认规划调用只写 per-call scratch、未见 world/global/TLS 写；由于引擎没有为 world graph 获取读锁，unpaused 调用明确返回 `requires_paused`。

### Split Half 原生提交契约

`split-army-half-<army_id>` 中的 `army_id` 始终是 snapshot 公开的完整 generation-bearing `CUnitID`，不是
命令内部的 `CArmyID`。1.19.0.6 adapter 先按 `base+0x570CC80` 精确解析 CUnit，再读取
`CUnit+0x178` 的内部 `CArmyID`；同时使用当前 snapshot 的 played `CharacterID`。它随后调用原版完整 validator
`0x26B8030(kind=1, source CArmyID, played CharacterID, nullptr)`。validator 会重新解析
`CArmy → CUnit → owner Character` 并校验 actor/owner，adapter 不自行重写这套规则。

原生 `CSplitHalfArmyCommand` 恰为 `0x30` bytes：primary/secondary vtable 是
`0x432D5C0/0x432D658`，`+0x20=1` 为玩家 command kind，`+0x24` 为 played CharacterID，
`+0x28` 为 source CArmyID。公共 submit wrapper `0x973E00` 通过 primary vtable `+0x40`、clone RVA
`0x26C2270` 同步复制命令，再以 player flags `0x0E` 入队并返回 locked queue 的 `bool`；仅 `true`
映射为 `split_submitted`，`false` 映射为 `submission_failed`。两条路径都以 destructor
`0x963C60(command,0)` 清理原栈对象。序列化 RVA `0x26B7F10` 对 `+0x24/+0x28` 使用 tag
`0x28AA/0x296A`，schema/type 为 `0x2C0B`。这些布局和生命周期都属于 exact-build adapter，升级版本必须重新锚定。

完整 split-half gate `0x26B6A90(..., true)` 会拒绝非 owner、combat、raid、barter、retreat、
movement-lock，并要求至少两个总 regiment 和两个 live/nonempty regiment；它没有 in-war 或 active-siege gate，
也不把所有普通 moving 状态一概拒绝。bridge 对失败只返回 `validator_rejected`，不从本地条件猜是哪一条。

executor `0x26B73E0` 先经 `0x26B67C0` 调用原生创建路径 `0x27BF0A0`，得到拥有新 CUnit 的 distinct
sibling CArmy，随后才在 source/sibling 间分配 regiment。因此该命令具备产生可独立移动第二军的原生语义，
不是同一 CUnit 内部的 regiment 分组；但同步成功仍只称 `split_submitted`，绝不提前声明第二军已经出现；
队列拒绝则明确返回 `submission_failed`。
最小后置条件必须由后续 paused snapshot 验证：原 source ID 仍存在、玩家可控 CUnit 集合恰好净增一个 ID；
若需证明独立控制，只移动不承担围城的一支，并确认另一支留守且原围城继续。native C++ slice 与离线 fixture
覆盖 ID 映射、validator、clone/submit/destructor 和“不伪造后置状态”；2026-08-24 的实机结果另见下文。

Python/MCP 只在 hello **精确**包含 `game.command.split-army-half-N` 时，才为当前 snapshot 中每个
`controllable=true` 的 public CUnit 动态展开 `split-army-half-<id>`；partial/unknown adapter 不会得到
literal step。parser 只接受完整 ASCII 正十进制 int32，`0`、符号、空白、尾随内容、Unicode 数字和溢出都
fail closed，合法 split 也被 `is_native_war_step` 固定路由到 pure-native backend。MCP 的通用
`execute_step` 直接复用该路由，不增加专用 RPC。

Python driver 提交 primitive 前记录 `source_army_id`、`submitted_date_raw` 与排序后的
`player_army_ids_before`。primitive 成功后只读取一次当下已经到达的 snapshot，绝不等待：若 source 仍存在且
可控 CUnit 集合相对 before 恰好新增一个 ID，则回执为 `war_action.status=split_applied` 并附
`sibling_army_id`；没有即时 sibling、出现多个新 ID 或 source 已消失都仍返回 `split_submitted`，不当成失败。
该 primitive 不自动推进时间，当前 planner 也刻意不选择 split；它只能由显式 MCP 调用触发，避免在未知 regiment
分配与围城窗口中自动削弱主力。

### Merge Armies Python/MCP 提交契约

exact-build 的命令 ABI、factory/owned-array/deep-clone/destructor、完整 validator 与 executor 证据见
[`ck3-native-merge-contract.md`](ck3-native-merge-contract.md)。Python 只在 hello **精确**包含
`game.command.merge-armies-N-with-N` 时展开 ordered literal；partial、placeholder 或 adapter 自报 literal 都不进入
`action_steps`。parser 只接受两个 distinct ASCII 正十进制 int32，合法 step 由 `is_native_war_step` 固定路由到
pure-native backend；MCP 继续使用通用 `ck3_execute_step`，不增加专用 RPC。当前 planner 不自动选择 Merge。

提交前 driver 记录排序后的可控军 ID、destination/source 当前状态与提交日期。primitive 返回后只读取一次已经
到达的 immediate snapshot，不等待、不推进时间：仅当 destination 同一 public ID 仍存在且 owner/ProvinceID 均
不变、source public ID 已消失、可控军 ID 集合精确等于 before 减 source 时，Python 回执提升为
`war_action.status=merge_applied`；任一证据缺失、目的军移动/换 owner、source 仍可见或发生额外军队增减，都只返回
`merge_submitted`，不猜部分完成。这里的 `merge_applied` 是 Python 对一次即时帧的严格投影；native 同步 typed
success 仍只有 `merge_submitted`。

2026-08-24 的 exact-build、最小化、暂停态实机闭合了两条后置链。第一次对 `83886341`
执行 Split，native 回执为 `split_submitted`；两秒内、游戏日期未推进的 snapshot 保留 source，并恰好新增
可控 sibling `67108903`。把 sibling 合回后再次 Split 得到 `83886119`；随后 sibling 独立移动到 `2596`
并建立 `SiegeID=67108912`，original 独立移动到 `2585` 并建立 `SiegeID=83886106`，证明它们是可分别
控制的 public CUnit，而非同军内部标签。两次 Merge 都先只返回 `merge_submitted`，再由 paused snapshot
证明 source 消失、destination `83886341` 的 ID/owner/ProvinceID 保留；第二次发生在游戏日期
`53176104`、两军同驻 `2585` 时，合并后同一围城 `83886106` 仍存在并报告
`besieging_strength=1501`。这些证据验证的是后续 snapshot，不改变 ACK-only 的稳定 typed 语义。

## 命令后置条件

- raise：等待 snapshot 出现新的可控军队；否则命令超时并返回失败。
- preview move：纯查询，成功只返回完整原生路线，不改变 CK3 revision 或军队状态；Python driver 会把只读结果记录进 `native_command_history`，供下一 turn 的同日期、同起点 freshness 判定使用。任一 ProvinceID 无法解析、native A* tail 超过 4096 项或 native builder 失败时整次请求失败，不返回部分路线；mid-edge 归一化允许在该完整 tail 前额外补一项 effective origin。
- move：若 DLL 能观察 `move_target_province_id`，等待该军队的目标变为指定省或军队到达；若当前构建不能观察该字段，则以 native `command_result` 的 `accepted/submitted` 为提交成功，返回 `move_submitted`，随后由 `life-advance` 推动行军。
- disband：等待目标军队从顶层 `player_armies` 消失。
- split half：native 同步 `split_submitted` 仅表示 validator 接受且 submit wrapper 返回队列接受；wrapper 返回
  `false` 时明确失败为 `submission_failed`。Python 不等待，只把已经即时
  可见的唯一新增可控 CUnit 提升为 `split_applied`。其余情况保留 before ID 集合与提交日期交给后续 paused
  snapshot 验证“source 保留、玩家可控 CUnit 集合净增一”；缺少即时 sibling 不是失败。validator 拒绝时也不
  绕过原生 regiment/state gate。
- merge armies：native 同步 `merge_submitted` 只证明固定 ordered pair 已通过 validator 且 submit wrapper 返回队列接受；
  wrapper 返回 `false` 时明确失败为 `submission_failed`。Python 不等待，
  只按上面的 destination identity、source removal 与 exact ID-set 三重条件投影即时 `merge_applied`。缺少即时变化
  不是失败，也不会触发 `life-advance`；后续围城连续性仍需独立 snapshot 证明。
- declare：DLL 缓存查询得到的完整 choice；提交时按 target/CB 重新枚举，并要求 claimant、目标 title、configuration 与缓存完全相同。
  Python 等待 `active_wars` 增长；若原生命令已入队但战争尚未投影，返回 `declaration_submitted`，下一 turn 先推进时间而不重复宣战。
- enforce：只允许当前玩家是该战争的 primary war leader；native builder、validator 与 command queue 接受后，Python 等待目标 war 消失。

2026-08-23 实机验证使用 exact-build DLL 与 `native-headless`，在 CK3 窗口 `IsIconic=true` 时显式查询并提交
`declare-war-29097-11-0`。提交后并非只收到 command ack：下一份 native snapshot 实际新增
`war_id=16777290`、`player_side=attacker`、`player_relative_war_score=0`；CK3 进程继续响应且窗口仍保持最小化。
该路径未调用 OCR、截图、键鼠或视觉 fallback。

同一存档中的战争 `16777290` 给出 `targeted_title_ids=[2388]`：目标为
`d_spoleto`，其 `capital=2389`（`c_spoleto`），该郡首府男爵领为
`2390`（`b_spoleto`），最终省份为 `2585`。对手默认集结省 `2543`
属于 `b_firenze`；它确实由敌方持有且可围城，但不是该战争的目标省。
旧投影只返回目标头衔的单个首都省；exact 1.19.0.6 的新投影改走完整 de jure 子树，因此公国/王国战争不再被压缩成一个围城点。

2026-08-24 的静态逆向与离线内存 fixture 已闭合目标省状态链：围城 storage slot 为
`base+0x57BF1B8`，查找点 `0x1849BD0` 同时证明 Province 的 SiegeID、low-24-bit slot、0x10 stride、
object `+0x08` 与 full-ID 比较；围城进度/总工作/剩余日 getter 分别为
`0x229B960/0x229CCA0/0x229BAA0`。anchor scanner 当前验证 98 个唯一 signature 与 13 个 vtable prefix，
fresh MSVC Release fixture 覆盖上述投影。此处只声明静态与离线验收；exact-build 最小化实机值尚待后续读取，不把它写成已实测通过。

2026-08-24 的后续实机回放补齐了移动与解散。旧 bridge 从 AI/controller 调用点抄入了
`command kind=2` 与 queue flags `7`；这会在玩家军队的控制权校验处被拒绝。连续推进约 49 个游戏日、
更换目标省以及尝试停止集结都不能修复该问题，且运行时字段明确显示军队并未处于集结状态。玩家地图路径实际使用
`kind=1`、queue flags `0x0E`。改为该路径后，窗口保持 `IsIconic=true` 时
`move-army-83886341-to-2586` 返回 `move_submitted`；随后约 35 个游戏日内，同一军队的当前省从
`2619` 变为 `2606`，证明发生了真实行军而非仅收到 command ack。

以下两段是 `[historical-old-policy]` 实机记录，只证明当时命令与状态链可运行；其中追敌 current、legacy rally
fallback 和 30 日通用 slice 已被本页后续 counter-policy 取代，不能当作当前 planner 规范。

同日的后续最小化实机验证覆盖了跨 driver 重启的移动意图。driver 从持久历史读回旧的、已经
`accepted/submitted` 的 move 后，planner 选择 `life-advance`，没有再次提交同一 move。第一次推进将原始日期
`53168688` 推到 `53168784`（4 个游戏日），军队从省 `2619` 移到 `2618`；继续推进 7 个游戏日后到达
`2615`，再推进 6 个游戏日后到达 `2609`。新 DLL 在同一局发布的战争字段为
`primary_opponent_character_id=36108`、`player_is_primary_war_leader=true`、
`enemy_primary_default_raise_province_id=2543`。可见敌军目标仍为 `2591` 时没有重复 move；该敌军实际移动到
`2602` 后，planner 才进行一次重定向并得到新的 `move_submitted`。每个 turn 结束时游戏都重新暂停，且 CK3
窗口始终为 `IsIconic=true`；全程没有 OCR、截图、键鼠或窗口恢复。

同一最小化实机战争随后暴露了纯追击策略的实际价值问题：首战令战争分从 `0` 升至 `24`，但其后约 80 个游戏日
持续追逐移动敌军时战争分保持 `24`。继续追逐约 70 日后分数才升至 `41` 并保存 checkpoint，说明追击偶尔能再次
接战，但会长期被移动目标牵引。Python planner 因此只在玩家为进攻方、本方 primary war leader 且战争分已经大于
零时，把 `enemy_primary_default_raise_province_id` 固定为围城启发式锚点；若玩家军与任一可见敌军同省，则仍优先
原地推进战斗。该策略改动目前由离线 Python 契约测试覆盖，不把默认集结省宣称为已解码的真实 war goal。

已提交的 move intent 保留 90 个游戏日，覆盖真实跨省行军所需时间；intent 未过期且所跟踪目标未改变时，
planner 必须推进时间而不是重复下令。战争中的单次 `life-advance` 最多推进 30 个游戏日，提前停止只依据玩家/
盟军军队位置与战术状态、战争分、战争集合或待处理事件这些会改变下一步决策的信号；敌军逐日移动不单独造成一次推进提前
结束。驻地或围城军队没有活动路线时，driver 另外监控“非撤退敌军首次把当前省作为所在省、移动目标或已发布路线节点”这一关系；
关系首次出现便立即暂停，不等满 30 日，也不把无关的敌军逐省移动当作进展。追击模式下，推进结束后的新决策点若发现所跟踪敌军已经换省，才提交一次新的追击目标；围城模式下目标
保持为稳定锚点，敌军在异省移动不会造成重定向。两种模式共用相同的 90 日 move intent 与 advance 去重。

解散命令同样必须使用玩家路径：公开 ArmyID 只负责解析 `CArmy`，command payload 使用
`CArmy+0x178` 的内部 target ID，并先调用原生 validator，再以 `kind=1` / flags `0x0E` 入队。
同一最小化实机回放中，`disband-army-83886341` 返回 `war_action.status=disbanded`，下一份
snapshot 的 `player_armies` 已为空；该成功路径用于战争结束后的残军清理，不能推广成战时重置军队。

同局后续 checkpoint 的 `date_raw=53174208`、玩家战争分 `41`，军队 `83886341` 位于省 `2598` 且为
`sieging`。推进 30 游戏日后仍未进入 `combat`；战时尝试 `disband-army-83886341` 被原生 validator 以
`CK3 army is not player-controllable` 拒绝，军队状态未变，因此不得采用“战时解散再重拉”的自动策略。
向 exact 目标 `2585` 围城推进 60 日后，两支敌军的原生 route 都锁定 `2585`；仅在 `2585` 与 legacy
fallback `2543` 两点间轮转会同时受堵。公国/王国目标发布全部 de jure 伯爵领首府，正是为了给 planner
提供更多安全围城点，而不是继续在这两个已被封锁的点上试探。

同一 `date_raw=53174208` checkpoint 的定向恢复又复现了另一类实际失败：目标省 `2585` 本身没有敌军，
但玩家军队从 `2568` 提交到 `2585` 的原生路线经过敌军当前省 `2581`，推进仅 1 游戏日就进入 2v1
`combat`。因此“目标省安全”不等于“路线安全”；planner 提交 move 前必须审阅玩家候选路线的每个
`route_province_ids` 条目，而不能只比较双方终点。硬冲突包括：非撤退敌军当前省位于玩家路线、敌军 move target
位于玩家路线、双方下一跳相同、双方剩余路线共享任一未来省，以及双方以相反方向使用同一条边。共享省会记录
双方各自的 1-based hop；当前没有每段地形/速度 ETA，不能仅凭 hop 差声称必然错峰。缺少 exact combat
forecast 时，敌军位于非 objective 路线终点也必须阻断，不再存在“被追击敌军恰在最后一项”的豁免。该字段发布的是 CK3 已计算的剩余路线，不包含 bridge
猜测或最短路重建。

路线安全是全局时间推进门槛，不是“最强军队”局部提示。每次战争中的 `life-advance` 前，planner 会在
paused snapshot 审计全部可控军队的活动路线，威胁集合取全部 active wars 的非撤退敌军；任一完整路线
不可读或不安全，就不能推进所有军队。实际不安全的军队会优先改道；旧路线仍存在时，本轮只允许纯
`preview-move-*` 或真正的 `move-army-*` 替换命令，替代目标已在当前省、preview/move deferred、retry
backoff 都不能成为继续推进旧危险路线的理由。`game.command.preview-move-army-N-to-N` 只解决提交前查询，
自动 exact routing 还必须同时广告 `game.state.army-routes`，否则明确返回 unsupported，避免未来 partial
adapter 在提交后失去持续审计能力。

活动路线使用一日 paused-to-paused horizon 时，时间速度本身也是契约的一部分。2026-08-24 的最小化
exact-build 实机从 `date_raw=53175216` 恢复时间，旧 Python composite 固定发送 `set-speed-5`；由于 DLL
语义 snapshot 的 heartbeat 周期为 250 ms，首次满足一日停止条件时游戏已经到 `53175264`，实际推进
`elapsed_days=2`。因此一日 route/Assault slice 现在必须先成功观察 `set-speed-1` 再 `resume-map`；缺该
capability 就保持暂停并报错。普通七日 siege 与无 tactical route 的 active-war slice 使用速度 5；后者也以
7 日为上限，不能无观察跨过第一个敌军 target cadence milestone。该改动只处理上述已实证的真实 overshoot，
不改变路线冲突判定。

没有活动路线的驻地军队也不是自动安全。paused 决策帧会针对该军当前省单独检查所有非撤退敌军的
`current_province_id`、`move_target_province_id` 和完整 `route_province_ids`；敌军正在汇聚到当前围城点时，
planner 会在同一 `date_raw`、同一物理 origin 下依次补齐所有未阻断 exact 目标的 fresh preview；不能因为
native DFS / fort rank 较前的一条路线安全就立即提交。全部候选齐备后先排除冲突路线，再按
`(剩余 route hop 数, 既有 objective rank)` 选择：优先更短的安全撤离路线，hop 相同仍保持原 rank。
全部 exact 目标无解则保持暂停，不能继续围城推进。该全量收集只用于“驻守 exact 围城且当前省受到汇聚威胁”
的撤离分支；普通目标规划仍按既有 rank 逐项查询，不额外消耗 preview。驻地检查只保护当前省，不会把敌军
路线上的任意远端交叉省加入通用目标黑名单。

该驻地门槛必须覆盖**全部**可控军队，而不是只覆盖本轮最强或已经选中的军队。2026-08-24 的真实最小化现场在
`date_raw=53175960` 同时存在两支可控军：`83886341` 驻守 `2596`、没有 move target；敌军 `357`
从 `2581` 沿 `[2587,2597,2596]` 明确汇聚；`16777558` 则仍有一条安全活动路线 `[2600]`。
旧 planner 只审计后者并错误返回 `native_war_route_progress/life-advance`。同一控制流随后由 production planner
的确定性双军 fixture 复现，不依赖伪造归档或测试专用分支。修复后的决策优先级为：先处理 unsafe active route，
再处理受到汇聚威胁的 stationary `regular/sieging` 军队，最后才按兵力选择普通 strongest 军队；任一安全 active
Assault 的每日提前推进也必须等待全体驻地威胁审计通过。这样每轮仍只执行一个战争动作，但不会用另一支军队的
安全路线或安全 Assault 替受威胁的驻军放行时间。该修复已通过确定性 Python production-path 回归；本段不把它
称为修复后的新 CK3 实机闭环，后续仍需在同一现场重新观察 reroute/保持暂停的后置条件。

同一实机现场在玩家到达 `2604` 后给出了更强的完整路线反例：玩家回到 `2585` 的预览为
`[2603,2595,2598,2599,2587,2585]`，敌军 `357` 从 `2597` 去 `2604` 的剩余路线为
`[2596,2595,2603,2604]`。双方在 `2603` / `2595` 共享未来省，并在 `2603→2595` 与
`2595→2603` 形成反向共边，因此不得提交。到 `2596`、`2600` 的候选也共享 `2603/2595`；
到 `2568` 的候选 `[8759,2602,2591,2589,2579,2574,2572,2568]` 则与两支敌军当时的完整路线无交集。

2026-08-24 的后续 pure-native 回放首次把 rich 围城字段在真实 CK3 进程中闭环。精确恢复点为
`date_raw=53174208`、战争分 `41`，checkpoint 大小 `94,597,177` bytes、SHA-256
`187CA01BA0EF308B4ED88BB7CFE4FC8E7DAA09FB3B09735112E81B80A092A8D5`。玩家军
`83886341` 到达 exact 省 `2585` 后生成 `SiegeID=83886106`，`fort_level=4`、
`garrison_size=500`、`besieging_strength=1614`。同一 SiegeID 从 `53174808` 的
`progress_fraction.raw=559` / `days_left=178` 连续推进至 `53176104` 的
`raw=35,772` / `days_left=115`；期间没有重建 SiegeID、没有停滞，也没有把 null 当成零。
敌军 `357` 首次把 `2585` 设为 move target，路线变为 `[2572,2586,2585]` 时，driver 在该
时间片第 2 天提前暂停，没有继续吃满 7 日围城窗口。

该现场同时给出了单军轮转的能力上限。安全撤离路线 `2585→2596` 为
`[2587,2597,2596]`；到达后确实生成玩家围城 `SiegeID=100663312`，兵力 `1583` 对守军
`600`，但敌军同一 paused 帧已经把完整路线设为 `[2587,2597,2596]`，可用静止窗口为零。
随后的一跳 `2596→2600` 生成 `SiegeID=98`，兵力 `1468` 对守军 `600`、`days_left=217`，
敌军也在建立围城的同一帧把路线设为 `[2597,2596,2600]`。`2604` 到达后为
`army_state=regular` 且没有 `active_siege`，不能把“到达 exact 省”误记为围城进展；追兵则立刻
指向 `[2603,2604]`。这一轮战争分由 `41` 降到 `38`，没有任何新占领，证明“只在 exact 目标间
无限风筝”不是自动获胜策略。现场随后再次通过 `-loadsave=xar_checkpoint` 精确恢复到日期 `53174208`
与相同 SHA，保留 41 分基线且没有覆盖 checkpoint。

另一个锁边现场精确说明了为什么不能用 Halt 冒充安全撤离：玩家物理当前省为 `8759`，活动路线首项为
`2602`，敌军路线 `[2595,2603,8759,2602]` 也以 `2602` 为目标。所有 exact preview 都必须先走
`2602`，因此 planner 正确返回 `native_war_no_safe_exact_route` 并保持暂停。1.19.0.6 的原版
`CHaltUnitsCommand` 只会删除当前路线首项之后的 suffix；越过行军 commitment threshold 后，结果是
`[old_route.front]` 而不是空路线或倒车。它在该现场只能把路线裁成 `[2602]`，仍会撞上敌军，不能替代
checkpoint restore。未越过阈值时 Halt 才能把路线清空；这两种后置条件属于版本 adapter 的原生语义，
上层不得假定 Halt 总能原地停车。

restore 后的失败经验与游戏事实分层保存。driver 保留最新优先、最多两条的 checkpoint/episode scoped
`native_rollback_war_failures` advisory，并继续用 singular `native_rollback_war_failure` 投影最新一条以兼容旧
consumer。它们采用两段证据：被丢弃 epoch 末端必须仍有 unresolved active route，
证明 restore 放弃了整段；用于重试阻断的 target/route 则取同一 army 在该 epoch 中第一条成功、preview 日期
与 move 提交日期相同、且 preview origin 等于恢复 origin 的入口 move。末端 target/origin/route 仅保存在
`terminal_failure_*` 诊断字段中；没有 restored-origin 入口就 fail closed，不生成 advisory。恢复后的 factual
`native_command_history` 仍截到 `save-checkpoint` anchor 后再追加 restore；planner 不从已回滚命令推导围城、
分数或完成状态。列表仅合并同 episode/checkpoint/war/army/恢复 origin 的记录，按入口 target+route 精确去重并
在第三条出现时淘汰最旧项。planner 对列表中的每一项都只在同 scope 再次出现相同入口 target，且 fresh preview
的 origin 与 route 逐项匹配入口阻断键时排除；同 target 得到不同路线则允许，避免一次回滚把该省永久封死。
覆盖成新 checkpoint 或进入新 episode 会清空整个列表。旧 v2 仅有 singular 时先以它作为最新项，再从最多两个
**仍留存在 history** 的 completed restore epoch 补 distinct 旧项；确定性兼容 fixture 的顺序为较新
`2598→2568`、较旧 `2598→2585`。若旧代码已截断旧 epoch，scan 不会猜测或魔法恢复它；只能把另行
live-confirmed 的同 scope target/route 作为显式 seed，并省略不准确的 `terminal_failure_*` 诊断。该隔离、
双条持久化、无 terminal 诊断 seed roundtrip 和 restore-transaction 崩溃恢复已于 2026-08-24 通过确定性
Python 测试；尚未把它称为新的 CK3 实机胜利证据。

除上文明确列出的 checkpoint restore 外，以上移动、解散与围城观测没有激活或恢复游戏窗口，也没有调用
OCR、截图或键鼠；每次时间推进后的决策帧都重新暂停。

这些具体战争 step 即使运行在显式 `hybrid-fallback` 配置中也只允许 native 后端执行；native 未广告时不会转发到视觉后端。

## Known limitations

- `CSiege` 是 Province 全局对象；若多场 active war 共享同一目标省，当前 snapshot 不能证明该围城归属哪一场战争。
- 多军 planner 每轮仍只为一支军队选择一个动作，尚未形成围城目标分配与协同调度的完整闭环；但时间推进门槛会审计全部活动路线与全部 stationary `regular/sieging` 驻地威胁，并优先处理不安全路线和受威胁驻军，不再由 strongest 军队单独放行时间。
- `_stable_tactical_war` 固定优先 exact attacker、primary leader 与稳定 `war_id`，不会因首战目标已全占或另一战正在失分而动态切换；尚未形成完整 multi-war 闭环。
- 当前能力可以读出围城是否真实推进，并已具备受限的 split/merge 原子命令；但没有野战编成/胜率、可靠补员或
  雇佣评估，Assault 也尚无当前现场的完整安全验收，因此仍不能保证完成 115–217 天级围城。所有 exact 目标都被
  快速追踪后应明确停机或恢复 checkpoint，不能把无占领的轮转描述为获胜闭环。

## 一步 planner

事件仍优先处理。无活动战争时，普通待回复角色互动沿用既有处理；有活动战争时，未发布 interaction kind、WarID、
outcome 与完整条款的 pending interaction 一律不自动接受或拒绝，只有己方 100 分的 enforce-demands 保持更高优先级。
其后每次 `ck3_auto_turn` 只执行一个战争动作：

1. baseline checkpoint 完成且当前无战争/残军时，可显式 `query-declarable-wars`；现有 key/title-count 排序只选出
   一条诊断候选。由于 payload 不含同 epoch 的 power、Monte Carlo forecast、campaign cost 与 exit assessment，
   planner 固定返回 `native_war_entry_evidence_required` / `selected_step=None`，不得自动提交 `declare-war-*`。
   native query 缺失时也不回退到 legacy `war-declare-palermo` 视觉宣战；该命令名称不构成 power/forecast 证据。
2. 任一活动战争达到玩家视角 100 分：先执行 `enforce-demands-<war_id>`，确认该 war 从 snapshot 消失，不再无意义推进时间。
3. 有活动战争、无可控军队：`raise-troops-default`。
   若玩家是某场战争的 primary defender，raise 后必须先取得完整终止条款、对手接受态度与 campaign forecast；
   当前能力缺失时返回 `defensive_war_exit_evidence_required` 并保持暂停，不盲目继续，也不因 unknown 自动投降；
   primary 身份本身 unknown 也按此 fail closed，只有明确的非 primary 盟军战争不触发该退出门。
4. 玩家是进攻方、本方 primary war leader 且存在 exact `war_objective_province_ids`：从战争刚开始的 0 分起围攻 exact 目标。rich fort/garrison 可观测时按 `fort_level, garrison_size, native DFS tie-break` 优先选择更易目标；capability 缺失、值 unknown 或同值时保留 native DFS 顺序。这是有意的策略层重排，不改变 snapshot 的契约顺序。paused 状态先预览完整原生路线，再按上面的硬冲突审计；普通规划不安全才预览下一目标，受威胁 exact 围城撤离则先收齐同日/同 origin 的全部候选，再选 hop 最短、rank 稳定的安全路线。所有 exact 路线都不安全时保持暂停，绝不偷用 legacy fallback；恢复 advisory 命中的旧 target+route 组合也视为不可选。
5. 没有 safe exact 目标且没有 exact combat forecast 时，保持暂停，或仅执行已有 exact-safe 的 hold / rendezvous；禁止按 `soldiers` 选择最大可见敌军、追逐其 current province，也禁止把 legacy `enemy_primary_default_raise_province_id` 当作自动目标。
6. 军队已经在 exact 目标省或已有仍安全的 accepted/submitted move intent：只有全部可控军与全部非撤退敌军的完整 M × N route audit、全部 stationary `regular/sieging` 驻地威胁审计都安全，才允许 `life-advance`。任一玩家/敌军 tactical route、任一可控军 combat/retreat 或 active Assault 都强制一日 paused-to-paused slice；其余 active-war slice 最多 7 日，不得无观察跨过 7/14 日 target milestone。unsafe route 优先于普通目标推进；安全 active Assault 也不能越过全局门槛。running snapshot 先暂停再读完整路线；敌情变化后每次推进前重新审计，不把上一次 preview 当永久通行证。
7. 战争消失但玩家军队仍在场：逐支执行 `disband-army-<army_id>`。

Typed MCP 工具为 `ck3_get_war_state`、`ck3_query_declarable_wars`、`ck3_declare_war`、`ck3_raise_troops_default`、`ck3_move_army`、`ck3_enforce_demands` 和 `ck3_disband_army`。通用 `ck3_plan_turn` / `ck3_auto_turn` 使用同一份状态和 step，不另建旁路策略。纯 native 缺少任何 capability 时明确返回 unsupported；Python 不会回落到最小化窗口的视觉点击。
