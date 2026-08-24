# CK3 1.19.0.6 原生 Assault Fort 契约

更新时间：2026-08-24；目标镜像：CK3 `1.19.0.6`，SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

本文冻结原版围城窗口 **Assault Fort / Stop Assault** 的只读逆向结果及其已实现的
exact-build adapter、snapshot 和 command 契约。稳定的上层语义与逐版本 ABI 必须分离：
本文中的 RVA、vtable、对象偏移和 command bytes 只属于上述精确 EXE，不是跨版本接口。

## 证据状态与边界

当前证据包括：

- 对精确 `ck3.exe` 的离线反汇编、MSVC RTTI、vtable 和 xref；
- 原版 `game/gui/window_siege.gui`、英文本地化与 `00_defines.txt`；
- 已有 rich siege snapshot 的历史实机数值，用来说明决策还缺什么字段。
- 版本专属 C++ fixture、完整 MSVC 构建/CTest 与精确 EXE 离线 anchor 扫描。

以下内容均为 **静态与 fixture 确认**：原版 GUI 入口、Start/Stop command 生命周期、validator 条件、
breach 字段语义、每日 assault 进度和伤亡计算入口、bridge schema、严格 step、bool queue ACK 与
原对象销毁。以下内容仍为 **未实机**：真实 Start/Stop 提交、当前存档的 `breach_level`、原生每日
投影值以及 53 天内完成围城的结果。本轮没有连接、读取或操作 CK3 进程，也没有提交任何游戏命令。

因此本页可证明 exact adapter 的离线 capability 与 fixture 已闭环，但不能被引用为实机通过。
实际用兵仍须完成可恢复的最小化实机后置条件验收。

## 已实现的稳定桥接契约

精确 adapter 只广告三项稳定能力：

- `game.state.war-objective-assault`；
- `game.command.start-assault-N`；
- `game.command.stop-assault-N`。

动态 literal 严格为 `start-assault-<full-generation SiegeID>` 与
`stop-assault-<full-generation SiegeID>`；ID 必须是无符号十进制正 `int32`，不接受符号、空串、额外
分隔符或尾随字符。它不是 ProvinceID、公开 ArmyID 或低 24 位 slot。

paused rich-siege 的 `active_siege` JSON 内新增：

```json
{
  "assault_observable": true,
  "breach_level": 1,
  "assault_in_progress": false,
  "can_start_assault": true,
  "can_stop_assault": false,
  "assault_daily_progress": {"raw": 340000, "scale": 100000},
  "assault_daily_casualties": 16
}
```

这些值是一个原子子域：running snapshot、无 active Siege、generation/alive/backlink 失败、非法
`breach_level`、非法 active byte、缺少任一 binding 或任一每日投影失败时，
`assault_observable=false` 且其他六项全为 `null`。完整 validator 的 `false` 是可观测 eligibility，
不是读取失败。`breach_level=0` 时不调用会以 `breach_level-1` 索引 defines 的 casualty routine；公开
每日进度与伤亡严格为零，两个 eligibility 仍来自完整 validator。

Start 的 native enum 为 `start_submitted | submission_failed | no_played_character |
siege_not_found | assault_already_active | validator_rejected | unavailable`；Stop 对应
`stop_submitted | submission_failed | no_played_character | siege_not_found | assault_not_active |
validator_rejected | unavailable`。只有两个 `*_submitted` 通过 pipe 返回 `ok=true`；它们仅是同步 clone
进入 locked queue 的 bool ACK。其余结果 fail closed，且 ACK 后主动发布的一帧也不能被当作 applied：
上层必须等待后续 paused consistent snapshot，再执行本页的一日后置语义。

## 原版 GUI 与 reflection 入口

`Crusader Kings III/game/gui/window_siege.gui` 的围城按钮使用：

```text
datacontext = "[SiegeWindow.GetSiege]"
visible     = "[And(SiegeWindow.GetSiege.IsPlayerInAttackerSide,Siege.ShowAssaultButton)]"
enabled     = "[Siege.EnableAssaultButton]"
tooltip     = "[Siege.GetAssaultButtonTooltip]"
onclick     = "[SiegeWindow.StartStopAssault]"
```

精确镜像中的关键入口为：

| 入口 | RVA | 静态语义 |
|---|---:|---|
| `SiegeWindow.StartStopAssault` string | `0x4146D50` | reflection 名称 |
| reflection thunk | `0x131E910` | 转发到实际 action |
| actual action | `0x131D770` | 按 `CSiege+0x44C` 选择 Start 或 Stop，构造并提交 command |
| `Siege.ShowAssaultButton` callback | `0xC2F2E0` | 当前 played Character 必须是 primary siege attacker |
| `Siege.EnableAssaultButton` callback | `0xC2F310` | 只走 siege 侧 Start/Stop gate，不含完整角色/kind gate |
| `Siege.GetAssaultButtonTooltip` callback | `0xC2F350` | 生成失败原因，或计算当日进度与伤亡 |

`EnableAssaultButton` 不是可替代 command validator 的稳定入口。实际提交必须重新调用完整
Start/Stop validator，因为后者还验证 played Character、command kind 与 primary attacker 所有权。

## Start/Stop command 对象

两条路径都是真实 Jomini command object，不是直接从 GUI 修改围城状态。完整对象大小均为
`0x30`：

```text
+0x00  primary vtable
+0x08  uint8 base flags，原版 GUI 写 0
+0x0C  opaque base dword，原版 GUI 写 0
+0x10  opaque base dword，原版 GUI 写 0
+0x14  opaque base dword，原版 GUI 写 0
+0x18  secondary vtable
+0x20  int32 command kind
+0x24  int32 full-generation played CharacterID
+0x28  int32 full-generation SiegeID
+0x2C  padding
```

### RTTI、vtable 与生命周期

| 项目 | Start Assault | Stop Assault |
|---|---:|---:|
| RTTI type descriptor | `0x54CD408` | `0x54CD628` |
| primary COL / vtable | `0x496FA68` / `0x432CB30` | `0x496F950` / `0x432CBC8` |
| secondary COL / vtable | `0x496FA40` / `0x432CB00` | `0x496F928` / `0x432CA08` |
| default heap ctor/factory | `0x26C69B0` | `0x26C6960` |
| full validator | `0x26BE8C0` | `0x26BEA90` |
| primary validator wrapper, slot 6 | `0x26BE4B0` | `0x26BEA00` |
| secondary executor, slot 1 | `0x26BE450` | `0x26BE9A0` |
| heap clone, primary slot 8 | `0x26C2FC0` | `0x26C30C0` |
| serializer type ID, primary slot 9 | `0x3163` | `0x3164` |
| scalar deleting destructor, primary slot 0 | `0x963C60` | `0x963C60` |

默认 ctor 分配 `0x30` 字节，安装两张 vtable，将 kind 置零，并把 CharacterID/SiegeID 都置为
`-1`。原版 GUI action 不调用默认 ctor，而是在栈上逐字段建立同样的 POD 布局，再走 class clone。
两个 clone 都重新分配 `0x30` 字节、安装对应 vtable，并复制 base 字段与三个 payload dword。

共同的 scalar deleting destructor 没有派生 owned payload；它复位 base vtable，并只在 delete bit
为 1 时释放恰好 `0x30` 字节。栈上临时对象不得使用 delete bit，queue 持有的 heap clone 则必须
按原生所有权路径销毁。不能把这条结论外推到其他 command class。

### Serializer schema

Start/Stop 的 primary vtable slot 16/17 共用 serializer `0x26BE4D0` 与 deserializer
`0x26BE570`：

| payload | offset | serialized key |
|---|---:|---:|
| command kind | `+0x20` | `0x340A` |
| SiegeID | `+0x28` | `0x2C3E` |
| played CharacterID | `+0x24` | `0x06EC` |

这既固定了字段顺序，也排除了把 ProvinceID、公开 ArmyID 或 local/network player ID 填入
`+0x24/+0x28` 的做法。

### 原版提交路径

GUI action 在两条分支中都写入：

```text
kind       = 1
character  = current played CharacterID
siege      = SiegeWindow 当前 full-generation SiegeID
queue flag = 0x0E
```

clone 后调用 queue wrapper RVA `0x341D990`；该调用的 command-manager/global target 为
RVA `0x57621F0`。`kind=2` / flags `7` 属于不同控制通道，不能用于玩家围城，也不能作为失败
后的 fallback。queue 返回或 command result `submitted` 只证明进入提交路径，不证明 executor 已应用。

## Validator 与 executor

### Start Assault

完整 Start validator `0x26BE8C0(kind, character_id, siege_id, error_context)` 依次要求：

1. `CharacterID` 能按完整 generation 解析为 live/alive Character；
2. RVA `0x26B26A0` 接受该 Character 使用 `kind=1` 的玩家 command；
3. `SiegeID` 能按完整 generation 解析为 live Siege；
4. `CSiege+0x44C == 0`，即尚未 assault；
5. `dword CSiege+0x3D8 != 0`，即至少已有一次 breach；
6. eligible besieging strength 不少于 current garrison；
7. Province 的原生 besieger/actionability 选择结果不是 `-1`；
8. RVA `0x26BE5F0` 解析出的 primary siege attacker CharacterID 与 payload CharacterID 精确相等。

第 6、7 项由 `0x229BF10` 汇总。第 6 项比较 `0x220E580(Province)` 与
`0x21F7B70(Province+0x620)`；攻击方小于守军时失败。第 7 项调用 `0x220CEC0`，失败路径的
原版本地化键精确为 `SW_MOVING_OR_IN_COMBAT`；兵力失败键为 `SW_TOO_FEW_SOLDIERS`。
breach 失败键为 `SIEGE_CANT_ASSAULT_NO_BREACH`，其原版文字明确要求城墙已被攻破。

因此“兵力约 1600、守军 500”只说明当前数值通过 `strength >= garrison`，不能绕过 breach、
移动/战斗、角色控制权或 primary attacker 条件。bridge 不应在上层复制一套近似 validator；
公开 `can_start_assault` 必须来自这个精确版本的完整原生 validator。

Start executor `0x26BE450` 从 secondary subobject 取 SiegeID，重新解析 Siege，并只写：

```text
CSiege+0x44C = 1
```

它不在 command dispatch 内一次性完成围城。实际进度和伤亡发生在后续游戏日 tick。

### Stop Assault

完整 Stop validator `0x26BEA90` 同样验证 live/alive Character、玩家 command kind、live Siege
与 primary attacker 所有权，但 siege 侧只要求 `CSiege+0x44C != 0`。停止 assault 不要求仍有
breach，也不重新要求兵力不少于守军；这使 Stop 成为已开始 assault 的原生退出动作。

Stop executor `0x26BE9A0` 只写：

```text
CSiege+0x44C = 0
```

## `breach_level` 的稳定公开语义

`CSiege+0x3D8` 不是任意 bool。静态调用链证明：

- Siege 初始化将 `+0x3D8` 及相邻 siege-action counters 清零；
- siege phase action RVA `0x229BC90` 按 action index 更新计数，breach 是 index 0，因此每次
  breach 递增 `dword [CSiege+0x3D8]`；
- casualty calculator `0x229F410` 读取该值，并以 `breach_level - 1` 索引
  `BREACH_ASSAULT_TICK_PERCENTAGE_CASULATIES`；
- 1.19.0.6 的 breach timer 与 casualty define 都只有两级。

exact-build adapter 可以把它投影成稳定字段：

```text
breach_level  0 = intact
              1 = small breach
              2 = large breach
walls_breached = breach_level > 0   # 可选派生值，不取代 level
```

只接受 `0..2`。任何负值或大于 2 的值都表示对象/版本/布局不符合当前契约，整个 assault 子域
必须 fail closed，禁止 clamp、按非零当 true 或继续调用 casualty 数组。读取只允许发生在 paused
snapshot，并必须先完成：

1. full-generation SiegeID storage roundtrip；
2. Siege alive gate；
3. `CSiege+0x200 == Province*`；
4. `Province+0x790 == full SiegeID`。

`breach_level` 是可跨 adapter 保持的公共语义，`+0x3D8` 不是。未来 CK3 版本即使仍显示相同 GUI，
也必须由新 adapter 重新定位并证明内部状态如何映射到 `0..2`。

## 每日进度与伤亡

原版 tooltip 在 eligibility 与所有权通过后先取 `eligibleMen = 0x220E580(Province)`，然后调用：

| 含义 | ABI | tooltip callsite |
|---|---|---:|
| 当前每日攻击方伤亡 | `int 0x229F410(CSiege*)` | `0xC2F72C` |
| 未开始时也可用的每日 assault 进度投影 | `CFixedPoint* 0x229F610(CSiege*, out*, int eligibleMen)` | `0xC2F741` |

reflection getter `Siege.CalculateAssaultProgress` 走 wrapper `0x229F580`。该 wrapper 在
`CSiege+0x44C == 0` 时故意返回零，所以不能用于 pre-start projection；它只适合 active 状态。
pre-start 必须在完成 generation/backlink 和输入兵力检查后直接走 core `0x229F610`。

每日 siege tick 在 RVA `0x229E18F` 调用同一 progress core，并把结果加入 siege work；军队日 tick
在 RVA `0x27C006D` 调用同一 casualty calculator，再把损失分摊到实际参战军队。原版本地化
`SIEGE_ASSAULT_TT_INFO` 也把两者描述为“每天增加进度并造成伤亡”。

1.19.0.6 的相关 defines 为：

```text
BREACH_ASSAULT_PROGRESS_CHUNK = 100
BREACH_ASSAULT_PROGRESS_PER_CHUNK = 0.2
BREACH_ASSAULT_TICK_PERCENTAGE_CASULATIES = { 2.5 1 }
SIEGE_ASSAULT_SPEED_MULT_WITH_ZERO_GARRISON_SIZE = 5
```

`0x229F610` 使用向上取整的兵力 chunk，并读取 current garrison
`0x21F7B70(Province+0x620)` 与 max garrison `0x21F7B10(Province+0x620)`，按守军剩余比例在
1x 到 5x 之间插值。bridge 稳定层不得只抄 `ceil(men/100)*0.2`：那只是满倍率区间的一部分，
会漏掉当前/最大守军比和引擎 fixed-point 舍入。权威值应直接来自当前版本的 core。

`0x229F410` 按 breach level 使用攻击方兵力的 2.5% 或 1%。对 1614 名 eligible attackers，
静态首日量级约为 level 1 的 40 人或 level 2 的 16 人；下一日必须用损失后的真实兵力重算。
不能把首日 casualty 或 progress 常量外推到整场 assault。

原版没有被本轮确认的“Assault 完整剩余天数”getter。每日 progress 会随着攻击兵力、守军比例、
围城状态和其他引擎量改变；普通 `days_left` 又是未把尚未开始的 assault 当成持续状态的围城天数。
因此公共层最多发布当日原生 projection，并由一日闭环重新观测，不能把一次除法包装成 exact ETA。

## Snapshot 最小增量

在现有 `active_siege` 已有 SiegeID、Province backlink、current/total work、普通 `days_left`、
current garrison、eligible besieging strength 和 player primary-attacker 关系的前提下，安全的一日
Start/continue/Stop 决策最少新增：

```json
{
  "breach_level": 1,
  "assault_in_progress": false,
  "can_start_assault": true,
  "can_stop_assault": false,
  "assault_daily_progress": {"raw": 340000, "scale": 100000},
  "assault_daily_casualties": 40
}
```

字段契约：

- `breach_level` 只允许 `0..2`；它是是否可 Start 的必要条件之一；
- `assault_in_progress` 是 `CSiege+0x44C` 的 exact-build 投影；
- `can_start_assault` 必须调用完整 `0x26BE8C0(kind=1, played, siege, nullptr)`；
- `can_stop_assault` 必须调用完整 `0x26BEA90(kind=1, played, siege, nullptr)`；
- `assault_daily_progress` 是当前帧/当前 eligible strength 的 CFixedPoint projection；示例值只展示
  JSON 形状，不是本轮存档的实测数值；
- `assault_daily_casualties` 是当前帧原生整数结果；
- 任一调用或子图验证失败时，整个 assault 子域 unavailable/null，不发布部分真假混合值。

`max_garrison_size` 对一日控制不是必要字段，因为原生 `0x229F610` 已消费它；若需要解释或研究
离线多日模型，可以作为 additive 诊断字段发布，但不能替代原生每日 projection。敌军到达日数、路线
相交和撤离窗口属于 army/war snapshot，不属于 `CSiege` assault 子域。

## 一日安全切片与后置条件

Assault 是可由原生 Stop 命令退出、但会持续消耗军队的状态。策略必须使用 paused-to-paused 的
一游戏日切片：

1. paused snapshot 验证同一 SiegeID/generation/backlink，读取上述完整 assault 子域；
2. 只有 `can_start_assault=true`、预期一日伤亡在策略预算内，且下一暂停点早于敌军安全边界时才提交；
3. 提交后先验证 Start 后置条件，再只推进最多一个游戏日；
4. 重新暂停，重读 work、兵力、breach、active flag、每日 projection/casualties 和敌军 ETA；
5. 任一 gate 消失、伤亡/威胁预算不再满足或不能证明继续安全时，调用完整 Stop 路径并验证后置条件。

queue ACK、`submitted`、单次 work delta 或出现 casualty 都不能单独作为命令成功或围城完成证明。

### Start 后置条件

- **applied**：下一 consistent paused snapshot 仍是同一 full SiegeID、同一 Province backlink，且
  `assault_in_progress == true`；
- **no effect/rejected**：同一 Siege 仍存在但 flag 仍为 false；
- **completed during transition**：Siege 已消失，`Province.active_siege_id == -1`，且 occupation/
  war-objective 状态完整解析为玩家友方一侧；
- **unknown/failure**：Siege 消失但没有友方占领，军队移走/进入战斗、第三方接管、generation 或
  backlink 变化。不得把这些状态重标成完成。

### Stop 后置条件

- **applied**：同一 full SiegeID/backlink 且 `assault_in_progress == false`；
- **no effect/rejected**：同一 Siege 仍 active；
- Siege 在过渡中消失时，只有上述友方占领闭环才是完成，否则仍为 unknown/failure。

如果 paused 帧暂时出现 `current_work >= total_work` 但 Province/Siege 关系尚未完成结算，应等待下一
consistent snapshot，不能绕过 occupation 后置条件。

## Python / MCP 消费层（离线闭环）

上层只在 hello 广告完整 recovery bundle 时，才从当前 paused `active_siege` 展开 generation-bound
literal：Start 必须同时具备 `game.state.war-objective-assault`、`game.command.start-assault-N` 与
`game.command.stop-assault-N`；Stop 为恢复已存在的 Assault，只要求 state + Stop。`start-assault-X`、
直接广告某个 literal 或任何缺件都不会产生 Start。公开 MCP typed tools 为 `ck3_start_assault(siege_id)` 与
`ck3_stop_assault(siege_id)`；通用 `ck3_execute_step` 使用同一 parser 和后置条件，不存在旁路。

Python normalization 把 `assault_observable=false` 与合法的 false/zero 完全分开：不可观测时六个子字段
必须同时为 `null`；可观测时 `breach_level` 必须在 `0..2`，三个 flag 必须为 bool，daily progress 必须
是 scale `100000` 的非负 fixed point，casualties 必须是非负 int32。稳定层派生
`walls_breached = breach_level > 0`，但不会反推或替代原生 validator。

Start/Stop 收到 `*_submitted` ACK 后，driver 等待同一 war、同一 objective Province、同一完整 SiegeID
的后续 paused snapshot。只有目标 flag 分别变为 true/false 才返回 `assault_started` / `assault_stopped`；
超时、SiegeID/backlink 变化、子域不可观测或 flag 未变都报失败，不把 ACK 重标成 applied。

自动策略的 Start gate 同时要求：

- `walls_breached=true` 且 `can_start_assault=true`；
- 原生当日 progress 为正，daily casualties 可观测；
- 当日伤亡扣除后的 eligible besieging strength 仍不低于当前 garrison；
- 当前 Siege 仍由玩家军队推进，且没有非撤退敌军的 current/target/route 指向驻守省份；
- 全局没有任一 controllable army 处于 `moving`/state code 7，或仍带 move target/非空 route。即使军队
  同帧仍报告 `sieging`，移动 intent 也优先，禁止 Start。

Assault active 后，`life-advance` horizon 强制为一个游戏日。每个 paused 终点重新读取 Siege work、
eligible besieging strength、当日 projection/casualties 和敌军汇聚；上一切片只用同一 objective 的
`before_state`/`after_state.besieging_strength` 计算非负 `strength_loss`。它只是 eligible besieging strength
的帧间净变化，不能冒充精确伤亡；progress frame 中的 army `soldiers` 可为 `null`，若偶尔存在也只作诊断，
绝不成为继续下一日的门槛。上一 assault 切片不是恰好一日、work 未增长、strength change 不可观测，或
当前/下一日投影兵力跌破 garrison，都会退出安全预算。任一 gate 失败时先选 exact Stop；Stop 不可用则
阻断时间推进。
成功 `assault_started` 还会在 command history 中打开 lifecycle latch。只要同 war/objective 的 row 缺失、
siege/assault 子域不可观测，planner 与 direct MCP `life-advance` 都会阻断，不会因 review 为空退回 30 日。
同 SiegeID inactive、`siege_observable=true && active_siege=null`、不同的正 generation、war 结束、成功
`assault_stopped` 或 checkpoint restore 都会闭合/隔离旧 latch，避免卡住后来 Siege。Start 后最新一次
`life-advance` 若 `ok!=true`，由于可能已经 resume/推进但没有完整 postcondition，下一轮必须 Stop/阻断；
direct MCP 在发送 `set-speed-5`/`resume-map` 前执行同一检查。decorated `auto-turn` 优先读取根部真实
`assault_action`，不把 planner payload 当作 applied 事实。
策略只保留 `projection_horizon_days=1`，不使用普通 `days_left`，也不从当前 progress/casualties 外推
Assault ETA。

同一 horizon 还覆盖尚未进入围城的行军：paused 起始帧只要任一 controllable army 仍有非空
`route_province_ids`、正 `move_target_province_id`，或 army state 明确为 `moving`/code 7，`life-advance` 就
优先采用一日上限，而不是普通战争的 30 日或普通围城的 7 日。若 moving 帧因解析失败没有 target/route，
planner 直接等待完整 paused route，不允许 Start 或推进。原因是 running snapshot 不发布完整 route，不能
等待跨 hop 后才重新审计敌军改道。
到达并清空 route/target 后，若没有 active assault，horizon 才恢复到对应的 7/30 日规则。该门槛来自
`53176368` 的实机故障：`[2597,2596]` 的活动路线曾单次推进 12 日才因跨 hop 停止。

上述消费层由完整 Python 回归夹具覆盖；仍不替代本页要求的可恢复实机后置条件验收。

## 当前 1614/500 与 53 天边界

历史 rich siege 现场给出的相关量约为：eligible besieging strength `1614`、current garrison
`500`、剩余 work `382.084`、普通每日 work 约 `2.2395`，追兵安全窗口约 53 天。这些量不足以
授权当前 Start：本轮没有读取该 Siege 的 `breach_level`、max garrison、原生 assault projection 或
当前 command validator。

可以静态确定的边界只有：

- 若 `breach_level == 0`，完整 Start validator 必然拒绝，Assault 不可能成为这 53 天的完成方案；
- 若 `breach_level > 0`，`1614 >= 500` 只通过兵力门槛，仍须让完整 validator 返回 true；
- 在最低 1x 倍率下，首日额外进度的 define-only 量级为
  `ceil(1614/100) * 0.2 = 3.4`。即便错误地假定兵力不下降，与约 `2.2395` 的普通进度相加也需
  约 67.75 天；实际 assault 还会每日减员，所以这一路径不能支持“保证 53 天完成”；
- 但引擎按 current/max garrison 最多放大到 5x，单独的 `garrison=500` 又没有给出 max garrison；
  因此上述最低倍率计算也不能证明“已有 breach 时仍必定来不及”。

最终决策边界是：**当前旧 snapshot 不足，禁止提交**。只有补齐本页最小字段、完整 validator 为真、
原生当日 progress/casualty 进入策略预算，并采用一日切片重新观测，才能尝试 Assault；在真实占领后置
条件出现前，不能声称 53 天目标已经完成。

## Exact-build 解耦与迁移

上层稳定 contract 只应看到：

- `breach_level`、`assault_in_progress`、Start/Stop eligibility；
- 当前每日进度/伤亡 projection；
- `start-assault-<siege_id>` / `stop-assault-<siege_id>` 的 normalized result 与后置条件；
- unavailable/unknown 与可观测 false/zero 的区别。

以下内容必须全部留在逐版本 adapter：

- reflection/RVA、RTTI/COL/vtable、command size/layout；
- ctor/clone/dtor、serializer schema/type ID、validator/executor、queue wrapper/flags；
- `CSiege+0x3D8/+0x44C`、Province/Holding offsets、current/max garrison getter；
- CFixedPoint ABI、每日 progress/casualty calculator 与该版本的合法 breach range；
- 版本专属 fixture、anchor bundle 和实机 capability 结果。

CK3 升级时必须按能力族迁移：

1. 以完整 EXE SHA 选择新 adapter，旧 adapter 对未知镜像保持 unavailable；
2. 从原版 GUI/reflection 名称重新找真实 action，再用 RTTI 闭合两种 command class；
3. 重新证明对象大小、payload、kind、queue flags、clone/destructor/serializer 与完整 validator；
4. 重新证明 breach 状态和 active flag 的内部表示，以及 progress/casualty 与 actual day tick 共用关系；
5. 用版本专属 fixture 覆盖 Start/Stop bytes、full-generation ID、validator 拒绝、clone 后生命周期和
   unavailable/fail-closed；
6. 在可恢复 checkpoint 上完成最小化实机 Start → 一日 tick → Stop/完成后置条件；通过后才广告 capability。

任一 anchor、布局或语义关系不匹配时，只移除 Assault 相关 snapshot/command capability；不应关闭已经
迁移完成的 pause、event、checkpoint 或其他战争能力，也绝不在未知版本上扫描若干相似 pattern 后试调用。
当前 1.19.0.6 adapter 已加入版本专属实现、fixture 与 anchor；这里的“已实现”仍只表示离线闭环，
不替代上述可恢复实机 Start → 一日 tick → Stop/完成验收。

## 2026-08-24 离线验证记录

本轮在全新 `build-assault-fort-msvc-release-2` 目录使用 MSVC `19.51` 完成 Release 配置与构建；随后
以 Visual Studio 自带 CTest 重跑四项 native test，结果为 `4/4 passed`：game-access fixture、adapter
registry、suspended-injection fixture 与 running-attach fixture。后两项连接的都是仓库自带测试 target，
不是 CK3 进程。

game-access fixture 明确通过 `assault_snapshot=1 assault_commands=1`；adapter registry fixture 通过
`known_descriptor=1 adapter_capability_set=1 unknown_build_unsupported=1 future_adapter_registry=1`。
对目标 `ck3.exe` 的只读离线 scanner 通过 `112` 个唯一签名和 `19` 个 vtable 前缀，并再次匹配本文的
四个 Assault 函数入口及 Start/Stop 主、次 vtable；扫描期间没有启动、附加或操作 CK3。

该次 fresh build 的诊断产物 SHA-256 为：

```text
xar_ck3_bridge.dll          E34F848FA1525D2ED3F9FED9AB647B8AE4DC5D03A8000F78F763140334215327
xar_ck3_bridge_injector.exe 398105D40FFB46EABE52AFA48CE9649E9C945650035C0B460495700D1E57FE2F
```

这些 hash 只冻结本轮离线构建证据，不是发布通道或实机验收标记；build 目录本身不进入版本库。
