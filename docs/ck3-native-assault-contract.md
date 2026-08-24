# CK3 1.19.0.6 原生 Assault Fort 契约

更新时间：2026-08-24；目标镜像：CK3 `1.19.0.6`，SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。

本文冻结原版围城窗口 **Assault Fort / Stop Assault** 的只读逆向结果，供后续
exact-build adapter、snapshot 和 command 实现使用。稳定的上层语义与逐版本 ABI 必须分离：
本文中的 RVA、vtable、对象偏移和 command bytes 只属于上述精确 EXE，不是跨版本接口。

## 证据状态与边界

本轮只有以下证据：

- 对精确 `ck3.exe` 的离线反汇编、MSVC RTTI、vtable 和 xref；
- 原版 `game/gui/window_siege.gui`、英文本地化与 `00_defines.txt`；
- 已有 rich siege snapshot 的历史实机数值，用来说明决策还缺什么字段。

以下内容均为 **静态确认**：原版 GUI 入口、Start/Stop command 生命周期、validator 条件、
breach 字段语义、每日 assault 进度和伤亡计算入口。以下内容仍为 **未实机**：bridge 实现、
capability 广告、真实 Start/Stop 提交、当前存档的 `breach_level`、原生每日投影值以及 53 天内
完成围城的结果。本轮没有连接、读取或操作 CK3 进程，也没有提交任何游戏命令。

因此本页不能被引用为 Assault capability 已经可用或实机通过。实现后仍须分别完成版本专属
fixture 和可恢复的最小化实机后置条件验收。

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
本轮只冻结研究文档，没有修改 `ck3_1_19_0_6_anchors.json` 或生产代码。
