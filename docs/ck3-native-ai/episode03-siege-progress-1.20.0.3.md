# 第三期围城：1.20.0.3 进度、总工作量与日速

2026-10-02。状态：**exact-build 静态研究完成；本专题没有 1.20.0.3 实机观测**。本期只研究录制现场选定的一场围城；省份、WarID、SiegeID 和 ArmyID 由现场快照绑定，不借用历史 fixture 身份。

原生剩余天数来自“剩余工作量 ÷ 当前普通日速”，并做固定点除法和整数向上取整。城防既影响总工作量，也可能因攻城器械等级不足而降低日速。普通日速不是当前 bridge 的 `assault_daily_progress`；后者是强攻预测。视频需要把同一暂停时点的 native 工作量、剩余天数与原版围城 tooltip 对齐。

## 精确输入与证据层

本次仅读取安装文件和仓库源码，使用显式解释器 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`（secondary worktree 没有相对 venv；该解释器已确认可 import `pefile`、`capstone`）。没有启动游戏、读游戏进程、调用原生函数、连接实机 MCP 或操作桌面。没有改变版本 pins、历史证据或运行时。

| 输入 | 本次绑定 |
|---|---|
| CK3 版本 | 1.20.0.3 Crozier；本机版本登记的 Steam build 25652598 |
| 安装 EXE | `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`，101039736 bytes |
| EXE SHA-256 | `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`，本次独立重新计算 |
| 研究 worktree 基线 | `D:/we3`，`6a837a1ecd9b027170f607242f6f02724908dc14` |
| 原版 defines | `game/common/defines/00_defines.txt`，SHA `8e430d77eb6e8767030f34b1c53d5dae84277fb354bd73cc42f93dc500be8982` |
| 原版 GUI | `game/gui/window_siege.gui`，SHA `8236d9d1ca373dc19d9e138948864b84887a4516756e1b293f26e2cd88c6b0b9` |
| 原版简中文本 | `game/localization/simp_chinese/gui/siege_window_l_simp_chinese.yml`，SHA `d332a17e5facc1d231bf22ae1241c405bc1ae2fe1f2f399c9915755ff7844b59` |
| 外置研究根 | `D:/ck3-war-episode03-20261002-a01/` |

外置 `siege-offline-static-check.json` 绑定 13 份冻结源码/原版定义、13 个 province 签名及 24 个语义指令片段；这些旧 .2 anchor 的字节均直接对照**本次 .3 EXE**通过。另保全 6 个跨 split-unwind 的有限指令区间及 total/daily/fort 函数反汇编。检查只证明指定字节相符、覆盖及文件完整性，人工阅读承担下面的语义判断；不证明所有 .3 ABI、调用安全或实机行为。

`.3` 的独立 adapter 先核验 `.3` SHA，再显式复用已审 `.2` binder。旧 binder 的 `.2` pin 原样保留。仓库已有 [ABI reuse 输入](../../ck3_autonomous_player/native_bridge/research/ck3_1_20_0_3_abi_reuse.json) 声明 `target_live_verified=false`；本次不将 [旧 .2 围城实机](ck3-1.20.0.2-r3-war-and-siege-live.md) 或 1.19 实机证据升级为 `.3` 实机结论。

## 暂停读数链与身份

[Province reader](../../ck3_autonomous_player/native_bridge/src/ck3_12002_province.cpp) 的有限链为：

1. 从 `GameData` 的 province array `+0x140` / count `+0x14C` 取得省份；核验省份 ID `+0x10` 和 magic `+0x85C = 0x50726F76`。
2. 从 Province `+0x788` 取 full generation SiegeID。`-1` 才能证明当前没有 active siege；旧 `+0x790` 不适用。
3. 从 siege storage slot RVA `0x5D1EC88` 解析组件，核验 SiegeID `+0x08`、magic `+0x0C = 0x53696765`、Province back-pointer `+0x200`。
4. 在暂停的 owning-thread rich snapshot 读取 current/total/progress/days；内部 CArmyID `+0x208` 只在唯一 public CUnitID 匹配时公开为 `besieging_army_id`。

`siege_observable=false` 表示不可观测，不能转成“没有围城”；`true` 加 `active_siege=null` 才是上述 `-1` 的真实空样本。`days_left=null` 也不能写成 0 天。非 rich / 运行中 snapshot 仅保证 occupation/fort 的有限读数，不承诺完整 siege graph。

| 量 / 调用 | 当前 .3 RVA 或字段 | 本专题证据 |
|---|---|---|
| 当前工作量 C | `CSiege+0x3D0`，int64 fixed point | .3 exact bytes + reader contract |
| 进度分数 P | getter `0x251C9C0` | 312-byte 有限 span |
| 总工作量 T | getter `0x251DD20` | 616 bytes，区域 SHA `ce9c6f82b0505efe53266b38607f3e88719279d6a0fe3658e01aa063f2b51050` |
| 剩余天数 N | getter `0x251CB00` | 502-byte 有限 span |
| 阻塞判断 | `0x251CF70` | 128-byte 有限 span |
| 普通日速 D | `0x251F170` | 3044 bytes，区域 SHA `dbbd82904d3959e6f2d4278b893f2c1f95563cc463f054a1213935a2b1338563` |
| 城防日速因子 F | `0x251FD60` | 798 bytes，区域 SHA `b4480a3707a7f9265ce8e74d16293051ce2ea7f1f2137482baab5045247865a0` |
| 当前守军 G | Province getter `0x247F370` → holding getter `0x2468D60` | .3 signatures + 88-byte holding span |
| 合格围城兵 B | Province getter `0x247F1D0` | .3 signature；不等于全军人数 |
| 有效攻城器械工作 M | Province getter `0x247ECE0` | 727-byte 有限 span |
| 当前强攻额外工作 A | `0x2520730` | 189-byte 有限 span；`+0x44C` 未开启时为零 |

## 有限数学定义

以下是本场讲解所需的非负、正常游戏量级路径。原生 fixed point scale `S=100000`，`mul(a,b)=trunc(a*b/S)`、`div(a,b)=trunc(a*S/b)`；函数另有大数溢出规避分支，不把 Python 浮点或下列标量展示式宣称为覆盖所有极值的原生模拟器。JSON 本身带 `{raw,scale}`，计算时始终读取实际 scale。

### 进度

当 `T_raw>0`，`P_raw=div(min(C_raw,T_raw),T_raw)`；总工作量为零时 getter 返回零。bridge `progress_fraction.raw` 范围是 `0..100000`，**它是分数，100000 才是 100%**。字幕百分比为 `100*raw/scale`，不是 `raw/scale`%。原版 GUI progress bar 另使用百分数 binding（`Siege.GetProgress`，max 100）；两者需在同一暂停时点核对。

### 总工作量

`0x251DD20` 读取 Province `+0x730` 的基础守军容量，叠加 `+0x710` 上下文的 effective modifier（helper `0x246BBE0`、enum `0x1D8`），按整数截断，再与 `NHolding.HOLDING_MIN_GARRISON_COUNT=25` 取最大，得到本 getter 使用的有效最大守军 `G_max`。该 modifier 的完整名称/所有生产者尚未闭合；本期采用原生 `total_work`，不从建筑文本拼装伪精确容量。

非零守军路径的标量展示式为：

```text
r = min(1, G / G_max)                 # 先作原生固定点比例
T = 100 + 75 * fort_level * r         # 最后乘法同样有固定点截断
```

`G==0` 或 `G_max==0` 的分支返回基础工作量 100。`100+75*fort_level` 只在有效满守军比例达到 1 时成立；总工作量 getter 会按当前输入重新计算，不能把开始时的 T 当作围城全过程永不变化的常量。

基础 100、每城防 75、最低容量 25 的原生 define accessor 分别是 `0x2396060`、`0x23961D0`、`0x23A2E60`，与当前文件值互证。

### 普通日速

当前 `NSiege` 的相关值为：基础 1，最终最小 0.5，多余合格围城兵每满 200 人增加 0.01，fort thresholds `[4,6,11,16,31]`，每个缺失攻城等级乘 0.7。

人工阅读 `0x251F170` 可把普通日速表示为有限输入合同：

```text
E = 0.01 * floor(max(0, B-G) / 200)
D = max(0.5, fixed_mul(fixed_mul(1 + A + M + E + X_add, X_mult), F))
```

`M` 是 native eligible siege regiments 的当前有效 `siege_value × 归一化当前规模` 之和。`0x247ECE0` 调用 effective stat getter `0x26344C0`，再调用规模 getter `0x2634720`；后者在正常正值路径返回 `trunc(当前人数 × 100000 / type.stack)`，**不是原始人数**，两项再作固定点乘法。不能用 stock 单位定义和名义团数代替有效值/当前规模。原版 onager 定义为 `siege_tier=1`、`siege_value=0.2`、`stack=10`，但 `engineered_for_destruction_perk` 等可改有效 siege value，实际当前人数也会变。若某组确有 60 人、stack=10、有效 siege value=0.2，则此项为 6×0.2=1.2；这是条件算例，不证明本场器械型号或有效属性。

`X_mult` 包含疾病等级（CSiege `+0x3E0`，当前定义 10% / 20%）、character modifier 与 CSiege 缓存 modifier `0x11E`、条件路径的 modifier `0x120`；`X_add` 包含同一条件路径的 `0x11F`。缓存项 tooltip 标签为 `ACCLAIMED_KNIGHTS_IN_ARMY`。上述 enum 的完整名称、character 角色与条件路径仍未全部闭合，**未知项不能置零后宣称精确复算普通日速**。现场应保存原版日速 breakdown，而不是为本期扩大运行时改动。

fort helper 读取 `0x247EFC0` 的当前合格最高 siege tier `K`。对于原版有序 thresholds，每个满足 `fort_level>=threshold[i]` 且 `K<=i` 的 0-based 项都顺序乘 0.7，因此正常非负 K 的展示式是 `F≈0.7^max(0,number_of_reached_thresholds-K)`；精确 F 是逐次固定点截断结果。**最终最低日速 0.5 在城防乘法之后应用**。原版 define 注释残留 `.5*.5` 举例，与该行实际 0.7 不符；本次直接跟 accessor `0x2396EA0` 和 native loop 核对为 0.7，不沿用注释数值。

### 剩余天数与阻塞

`0x251CB00` 先核验 siege magic/存活 ID，并调用 `0x251CF70`。无效或阻塞时返回 `INT_MAX=2147483647`，bridge 将其公开为 `days_left=null`。

通过校验后，它解析 CSiege 内部 army，从 CArmy `+0x120` 取 CharacterID 作为日速函数第三参数，第四参数为内部 army ID，第五参数 tooltip breakdown 为 null。`+0x120` 的确切角色名未在本专题闭合；不因此写成已证“指挥官 modifier 路径”。

正常正日速、非负剩余工作量路径：

```text
R_raw = max(T_raw-C_raw, 0)
q_raw = trunc(R_raw*S/D_raw)
N = q_raw // S + (1 if q_raw % S != 0 else 0)
```

这是先截断到 `1/100000` 天，再向上取整；正常量级可讲为“剩余工作量除以当前日速向上取整”，但接近零或整数边界时不能把无限精度 `ceil(R/D)` 当作完全等价的原生实现。`N` 也不能反推出唯一 D。极端零日速 fallback 不作为本期可用读数解释。

阻塞 span 明确包含 `B<G`（`jl`，不是 `B<=G`）与 Province getter `0x247DC20` 返回 `-1`；后者完整 movement/combat 分支尚未闭合。原版 UI 有兵力不足、移动/战斗阻塞说明，本期需保存实际 blocker tooltip。即使未阻塞，N 仍是当前输入的条件预测；兵力、守军、修正和强攻变化会使它改变。原版“最多持续”文本也注明围城事件可令结束更早，不足以证明整个余下围城有无条件时限保证。

## 本期可讲的事件与日速差异

当前原版 `BASE_SIEGE_PHASE_LENGTH=20` 天；breach 等级对应 phase timer `-10%/-30%`，starvation 一次性工作增量定义为 total 的 `5%/15%`，disease 改普通日速 `+10%/+20%`，desertion 增加 5 工作量。该分类同时见当前原版 defines 与简中 tooltip。这里未完整逆向 phase 更新/随机选择生产链，不声称已独立证明每次事件实际写入或发生概率。

因此“20 天一跳”是基础事件间隔输入，不是普通围城每 20 天才推进；`military_engineer` 的 `siege_phase_time` 修正作用于事件间隔，不能直接写成每日进度按同百分比提高。不同事件必须由本场录像/tooltip 回读区分；没有相邻实机样本，不把工作量跳变都叫作日速。

## 当前命令能力与缺口

[.3 descriptor](../../ck3_autonomous_player/native_bridge/src/ck3_12003_adapter.cpp) 继承 [.2 capabilities](../../ck3_autonomous_player/native_bridge/src/ck3_12002_adapter.cpp) 的 `game.state.war-objective-occupation/fort-level/garrison/siege-progress/assault`。本场应从 `active_wars[].objective_province_states[]` 的 `active_siege` 采样。

源码已有 MCP `ck3_get_capabilities()`、`ck3_take_snapshot()` 和 `ck3_get_war_state()`（均无参数，MCP 参数对象为 `{}`）；最后一项是 snapshot 的 war/army slice。优先冻结完整 snapshot 保留 build、episode/revision/date 等外围身份。现场仍须核对当前进程加载的 DLL、capabilities 与工具列表，源码登记不代替实际 `.3` advertisement。

`query-province-local-siege-v1-N` 仅在历史 1.19 descriptor 发布。其 parser/port 编译存在不能外推为 `.3` capability；本计划不调用它。当前标准 snapshot **没有普通 daily_progress 或其完整输入 breakdown**。`assault_daily_progress` 是强攻预测，且 breach/assault_observable 有独立边界，不能当作普通 D。

source descriptor 虽列有 pause/resume/speed、start/stop-assault 等动作，本次研究未执行；本计划只定义暂停只读观察，不用动作 ACK 证明 siege 业务状态。若今后确需公开普通 D，优先单独审 `.3` exact-bound owning-thread getter 参数、图生命周期和 normal/blocked fixture；本期并不因为定位到 RVA 就宣布该新端口可用或直接调用它。

## 给录制执行者的有限采样合同

先完成项目既有 Steam 离线、桌面鲜度、录制 attempt 和实机独占流程。由 root 的第三期已授权运行窗口选择实际目标围城，绑定当前 DLL / EXE SHA，再运行本专题 [plan](episode03-siege-progress-1.20.0.3.plan.json) 的 `check --for-observation`。工具检查不授予实机操作权限、不证明语义正确。

每个暂停 endpoint 最多保存两次快照以核对状态稳定，再保存一组独立 GUI tooltip。字段缺失或身份不匹配即记为该 endpoint 不可比较；不盲目重试旧命令或直接调用未审 getter。

| 采样组 | 需要保全的实际内容 |
|---|---|
| 外围身份 | 实际 schema/build/EXE SHA、adapter/backend、loaded features、episode/session、revision、native date_raw、暂停状态、录像 frame/time 与 JSON 原字节 SHA |
| 目标绑定 | full WarID、target title IDs、province ID；full SiegeID；nullable public army ID；player_army_besieging；对应 player army 状态、位置、moving/combat 和实际兵力 |
| 省份 | occupation_observable/is_occupied/occupying_character_id、nullable fort_level / garrison_size / besieging_strength、siege_observable；后三项 observable 是内部 reader flags，公开 JSON 以 null 表示不可观测，不额外返回这些 flags |
| active siege | `{raw,scale}` 的 current_work / total_work / progress_fraction，nullable days_left；assault_observable、breach_level、assault_in_progress、assault_daily_progress / casualties，并保存原始 null |
| 原版 GUI | `SiegeWindow.GetSiegeProgressTooltip`、`GetDailyProgressTooltip`、`GetTimeLeft`、`GetFortLevelImpactTooltip`、`GetNumberOfTroopsTooltip`；攻城器械当前数量/有效值/最高 tier 能看到的实际 breakdown；事件 history、phase timer、disease/starvation/breach tooltip |

GUI 定位来自 `window_siege.gui`：progress tooltip 354 行；progress bar 485/502；剩余时间 538；fort impact 605；兵力 658；普通日速 tooltip 862；器械列表 993/1049；phase 1092/1201；history 1232。简中 `SW_DAILY_PROGRESS` 把普通 D 显示为 1 位小数，所以从画面复算要允许显示舍入，不能据 1 位显示值判 raw 分数精确相等。本专题只定位原版 binding/文本；没有找到并验证 GUI callback 注册路线，不能当作现成原生查询端口。

root 若在独立授权的录制运行中推进日期，可选取 A/B 两个暂停 endpoint 做一日增量：必须同 EXE、同 episode、同 full SiegeID、同省份，确认 native date 差的时间单位及经过一天，记录所有事件/强攻/兵力与输入变化。**本暂停观测计划本身不授权推进时间**。若期间事件跳变、T 改变、对象完成/替换、reload、blocked 或日速变化，`(C_B-C_A)/Δdays` 只是区间实际增量，不能命名为 getter D。干净、无事件且输入稳定的相邻日样本才可与当时普通日速相互核验。

围城结束需再保存原生 occupation、active_siege 消失和本场界面/录像后置状态；进度 100%、动作 ACK 或预测日期单独都不能证明占领完成。没有实际 `.3` 样本时，以上 cases 继续 pending。

## 文件与验证入口

本专题 graph 由 [同一 JSON 记录](episode03-siege-progress-1.20.0.3.plan.json) 经 `native_research_plan.py render` 生成：[观测图与证据表](episode03-siege-progress-1.20.0.3.graph.md)。未知 live 对齐、完整 modifier/事件链保持虚线 `unknown`，没有 counter-policy 改动。

外置报告：`D:/ck3-war-episode03-20261002-a01/research-siege-progress.md`。原版/源码冻结副本在 `offline-siege-sources/`，反汇编与精确字节在 `offline-siege-functions/`，本次 exact-byte 检查在 `siege-offline-static-check.json`，当前计划检查在 `episode03-siege-plan-check-02.json`；第一稿及 check-01 保全在外置目录。过程资产原样保留。

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe D:/we3/tools/native_research_plan.py check D:/we3/docs/ck3-native-ai/episode03-siege-progress-1.20.0.3.plan.json --for-observation
```

该 check 验证记录结构、采样条件自洽与引用文件 SHA，不自动证明上述数学语义，也不证明任何实机 case 已观测。本场 live 对齐、普通日速 GUI breakdown、一日增量及完成后置状态须由 root 另存新证据并追加日期记录；历史证据、失败 attempt、版本 pins 保持原样。

## 2026-10-03 勘误：器械人数需先按 stack 归一化

此前第 85 行把 `0x2634720` 的返回量简称为“当前合格人数”，遗漏了单位类型的 stack 除数；若直接用原始人数乘 siege value，会把器械贡献错误放大。现已修正该句，保留此次有日期的勘误；旧外置 editorial source 和原观测 plan/graph 保持历史字节，不重写已冻结来源。

本次重新核验同一 `.3` EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。`0x2634720..0x263478C` 的 108-byte 有限区间 SHA 为 `522935ebe968430fb1f88758ee9d652a38015bb2a4a30d598b9ca09505b160cd`：读取 regiment `+0x38` 当前 count，读取 `+0x18` type 的 `+0x70` stack denominator，正常正值分支返回上述 Q100000 当前规模。该区间覆盖本次所用的除法/return，不宣称覆盖整个函数的溢出 fallback 或可安全动态调用。

另复核 `0x247ECE0` 的 727-byte eligible sum（区域 SHA `0dc8648056516b8c413a85b42f1d607ad9db4e1f36c6f3214e419f6b9c3ff7e4`）：`0x247EEC4` 调 effective stats、`0x247EED4` 取返回结构 `+0x10` siege value、`0x247EED8` 调归一化规模，再作固定点乘法。完整外置窄证据为 `D:/ck3-war-episode03-20261002-a01/one-day-real-review-a01/count-normalizer-static-proof.json`，文件 SHA `a0f7b661ce92f00f9205d8fdabb4aac40918caed414576a1622a8fe790fe6c02`；修正前本文精确字节也已独立保全。

这条静态勘误只修正量纲。60 人与新购 9 人是否属于同一场、同一参与军队，具体 unit id、当前有效属性及是否实际合军，仍须本场快照/UI 证明；不得仅凭日增量相容倒推出器械型号、有效值或增援归属。没有修改 frozen runtime、版本 pins、历史实机记录或已冻结观测计划。
