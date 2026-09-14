# 非宗教囚犯、犯罪、赎金与惩罚原生 AI 树（CK3 1.19.0.6）

> 工作包：**G2-M6-PRISONER1-NATIVE-TREE**。
> 状态：**static-ready / research-only**；2026-09-15；未启动 CK3，未连接进程，
> 未实现 observer、bridge、MCP、action 或 planner。
> exact build：ck3.exe 95,206,008 bytes，SHA-256
> **2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86**。
> 机器可复验账本：
> ck3_autonomous_player/native_bridge/research/nonreligious_prisoner_management_native_tree_1_19_0_6.json。

## 结论与下一刀

当前 G2 已有一次 exact pay_ransom pending 的 production-live 拒绝循环，但那只证明通用 interaction
收件箱能够绑定、拒绝、跨 checkpoint 消失；它没有提供玩家的完整囚犯集合、赎金各角色、付款选项、犯罪理由、
惩罚合法性或费用。因此，现有 live primitive 不能当作“囚犯/犯罪能力完成”。

现实 P0 是私有只读 **player_prisoner_management_snapshot_v1**。它必须从当前玩家的引擎拥有集合完整枚举囚犯，
再为每个囚犯构造 allowlist 内的 finalized interaction preview，返回角色、可见选项、准确费用、Can Send、
原生失败理由，以及引擎最终的 imprisonment/banishment/execution reason。集合不完整、被 cap、角色重定向不明
或 option ownership 不明时都要 typed unavailable，readiness 不能变 true。

下一项唯一施工入口是
**implement_private_exact_build_player_prisoner_management_snapshot_v1_reader**。第一步定位 exact
Character.GetPrisoners/CourtWindow.GetPrisoners backing method、集合所有权和 full-ID resolver；随后复用已经冻结的
generic interaction context/final validator。私有 paused live 证明完整集合和至少两类最终结果之后，才设计动作或公开 MCP。

## 范围与宗教域排除

本专题覆盖普通 imprison、地牢/软禁、ransom/pay_ransom/ransom_me、无条件释放与非宗教释放条件、execute、
torture、castrate、blind 和 systematic maim 的机会、AI 权重与最终 legality 边界。

**宗教域排除**继续生效：不展开 faith、doctrine、tenet、conversion、vows、piety、human sacrifice、holy order
或通用宗教政策。release 的 demand_conversion/take_vows、execute 的 kinslaying/doctrine 与特殊 tenet 分支仍被
exact 原文件哈希覆盖，但只允许未来 observer 返回引擎最终 allow/deny 和 opaque reason，不能把这些分支复制进
planner。prison_break_contract 属 scheme 域，也不进入本包。

## exact-build 证据账本

所有相对路径位于 Crusader Kings III。verifier 会核对完整文件大小、SHA-256、必要锚点、定义边界、
AI modifier 数、hard-zero 数、tier cadence 与 send-option inventory。

| 原版资产 | size | SHA-256 | 使用边界 |
|---|---:|---|---|
| game/common/character_interactions/00_prison_interactions.txt | 201,766 | 3E05C94C...C658F22B | 1–8737 行全部 prison interaction 定义；本专题保留的十二个定义逐项冻结 |
| game/common/character_interactions/_character_interactions.info | 27,227 | F360C05B...940D5D10 | Can Send 权威顺序、AI targets 和角色选择语义 |
| game/common/script_values/00_interaction_values.txt | 18,763 | 47A24A4B...5B9E6BC | ransom、increased ransom 与 herd 的原生 value |
| game/common/script_values/00_basic_values.txt | 47,113 | 9268A54F...C4CB0096 | dread answer 值与 banishment tyranny gain |
| game/common/script_values/01_dynamic_values.txt | 44,999 | 049303EF...6D7064 | tyranny-war 财政门 |
| game/common/defines/graphic/00_graphics.txt | 60,198 | D276199C...1999619 | GUI prisoner grid cap；不能拿 GUI cap 代替完整集合 |
| game/common/scripted_triggers/00_scripted_triggers.txt | 14,623 | 490C3784...95B5E | basic/advanced allowed-to-imprison 门 |
| game/common/scripted_triggers/00_crime_triggers.txt | 1,563 | 879A7E08...23A2ABD | crime 辅助触发；信仰细节不展开 |
| game/common/scripted_triggers/00_interaction_triggers.txt | 8,713 | 2C77FDED...237C789 | ransom payment-shape helper |
| game/common/scripted_effects/00_prison_effects.txt | 59,488 | F745201E...1D26A66 | ransom 对账并 release；execution 的 death envelope |
| game/gui/window_court.gui | 23,731 | E730078C...2AD5135 | CourtWindow.GetPrisoners 与 mass ransom/release/execute 表面 |
| game/gui/window_ledger.gui | 252,225 | 11314E88...0C53BD5 | Character.GetPrisoners 的只读 GUI 消费者 |

ck3.exe 内有唯一 ASCII reflection 锚点：GetExecuteReasons 在 **0x40CEDD0**，
GetBanishReasons 在 **0x40CEDE8**，GetImprisonmentReasons 在 **0x40CF0E8**，
GetPrisoners 在 **0x4107BA8**。这些字符串只证明 exact build 暴露相应反射名；它们没有证明安全 method RVA、
返回容器布局、生命周期或线程条件。实现前仍须闭合这些 unknown，不能从字符串直接调用。

## 通用 interaction 管线

本专题复用 core-diplomatic-proposals 已冻结的 exact-build substrate：

| seam | RVA span | SHA-256 |
|---|---|---|
| interaction database getter | 0x831890..0x8318E7 | 954B2668...532C2 |
| two-role context constructor | 0x2C3EE50..0x2C3EFF9 | A9CDB970...9CE83A |
| finalize context | 0x2C40B20..0x2C40BFE | 1A6393A2...72661 |
| final Can Send validator | 0x2C43F00..0x2C44070 | 3B9A75EC...86ED54 |

stock schema 给出的 Can Send 顺序仍是权威：角色完成、外交距离、special is-shown、is_shown、重复 pending、
is_valid_showing_failures_only、has_valid_target_showing_failures_only、can_send、is_valid、
has_valid_target、special can-send，最后才判断是否需要以及是否能获得 AI 接受。囚犯菜单里的“按钮亮了”
不能替代 finalized context，也不能把 ai_will_do 当作 recipient ai_accept。

prisoner 集合和 ransom 特殊角色 payload 尚未闭合。ransom 的 actor、recipient/payer 和 secondary prisoner
不总是普通二角色；所以这里只复用数据库、stable definition、finalize 与 final validator，不声称现有 constructor
已经能安全构造所有赎金形状。

## 逮捕原生树

imprison_interaction 的 stock AI 从 vassals 与 courtiers 取候选；barony 不检查，county cadence 36，
duchy/kingdom/empire/hegemony 为 10。ai_will_do base -100，有 19 个直接 modifier 与两个 factor=0；
ai_accept base 0，有 25 个直接 modifier。interaction 可以在预计拒绝时发送，所以 recipient answer 表示成功概率，
不是发送合法性的同义词。

ai_accept 主要输入是双方 intrigue、hook、vassal refusal treason、prison perk、目标 rank、dread、军力比、
rival/nemesis、court grandeur、legalistic culture 与若干地区内容。sender tree 对合法 imprisonment reason
大幅加分；战争、可玩强敌、低军力与低财政风险大幅减分；lover/friend/child/spouse 和缺乏实际惩罚动机可降到
-1000。grand activity 对 count+ 目标、以及未满足 eviction 条件的 landless adventurer 是 hard zero。

~~~mermaid
flowchart TD
    A[AI cadence + vassal/courtier candidate] --> B{ai_potential 与 basic/advanced imprison gates}
    B -->|失败| Z[无机会]
    B -->|通过| C[构造 exact imprison context]
    C --> D[final Can Send 与 tyranny/reason]
    D -->|无效| Y[保留原生 failure reason]
    D -->|有效| E[ai_will_do base -100]
    E --> F{hard-zero state}
    F -->|是| Z
    F -->|否| G[reason + risk + relation + struggle 权重]
    G --> H[recipient ai_accept 成功概率]
    H --> I[stock AI 决定是否尝试]
    B -. prison collection / evaluator RVA 未闭合 .-> U[unknown]
~~~

未来自动玩家不能只读 has_imprisonment_reason 就发命令。它还需要完整候选、最终 Can Send、预计成功、
显示的 tyranny 后果、资源/战争风险和明确后置条件；本包只定义 observer，不设计动作。

## 赎金三种角色形状

### jailer 发起 ransom

ransom_interaction 对 prisoners 运行；barony cadence 36，其余 tier 为 6。sender base 0、9 个直接 modifier、
3 个 hard zero；recipient base 0、11 个 modifier。合法全额/当前金额在长期监禁后加 100，greed 可继续加分；
rival -100、nemesis -300；对自己 vassal 要 favor 可加 100。actor 在战争、human payer 战争或拒绝标记、
active prison break 时 hard zero。

八个 authored option 是 extortionate_gold、extortionate_current_gold、gold、current_gold、favor、
influence_send_option、herd_send_option 和 mass-action invalid fallback。effect 根据最终 option 在 payer 与
imprisoner 间转移准确资源，最后 release 精确 prisoner。

### 第三方 pay_ransom

pay_ransom_interaction 从 family、spouses、scripted relations、liege，以及受限 neighboring/peer/top-realm
domicile 集合找机会。barony 为 0，其余 cadence 6。sender 有 17 个 modifier、6 个 hard zero；recipient 有 16 个。
它把被救者放在 secondary recipient，jailer 是 recipient，付款者是 actor。compassion 与亲属/关系决定是否值得救；
heir、钱款/有效 favor 增益；目标无关、option 无效、human jailer 战争/拒绝、prison break 会 hard zero。

### prisoner 自赎

ransom_me_interaction 的 AI recipient 是 self；barony/county/duchy/king+ cadence 为 72/24/24/12，
sender 有 7 个 modifier和 3 个 hard zero，jailer accept 有 15 个 modifier。它与第三方赎金共享若干 option key，
但 role identity 不同，不能用同一二角色 payload 猜测。

~~~mermaid
flowchart TD
    P[完整 prisoner row] --> K{interaction kind}
    K -->|ransom| R1[jailer actor -> payer recipient -> prisoner secondary]
    K -->|pay_ransom| R2[payer actor -> jailer recipient -> prisoner secondary]
    K -->|ransom_me| R3[prisoner actor -> jailer recipient]
    R1 --> O[枚举 exact visible/valid options]
    R2 --> O
    R3 --> O
    O --> C[materialize option + exact resource terms]
    C --> V[finalize + Can Send + recipient answer]
    V -->|有效| E[ransom effect: 对账后释放 exact prisoner]
    V -->|失败| F[原生 failure reason]
    R1 -. role/option ownership 未闭合 .-> U[unknown]
    R2 -. role/option ownership 未闭合 .-> U
    R3 -. role/option ownership 未闭合 .-> U
~~~

## 释放、处决与其它惩罚

release_from_prison 的 ai_frequency 固定 1，ai_accept base 0 有 33 个 modifier，ai_will_do base 0 有 21 个，
另有 prison-break hard zero。所有条件都为 false 时才是 auto-accept 的无条件释放。非宗教条件包括
renounce claims、banish、gain hook、become executioner、recruit、disfigure、blind、castrate 和 demand admin；
demand conversion 与 take vows 排除。sender 对各条件增加意愿，同时 revenge 会压低释放，compassion 和较长
监禁会促进无条件释放；feud、struggle 与部分文化输入继续由原生树决定。

execute cadence 是 barony 72、其它 tier 12；ai_will_do base 0，有 18 个 modifier和两个 hard zero。
合法 execution reason、sadistic/lunatic、继承利益、vengeance、rival/nemesis 与 struggle/nomad 输入提高意愿；
若没有 reason、rival/nemesis、配偶背叛、继承利益或 lunatic，原版直接 factor 0。kinslaying/doctrine 与特殊
tenet 分支只保留在 source hash，不进入策略模型。execution 的七个 option 也必须走引擎最终 legality。

torture base -25，只由 sadistic、family feud、escape attempt 三个直接正 modifier 推动。
castrate 和 blind base -20，各有上述三项加 Byzantine punishment emulation，共四个 modifier。
systematic maim 只在 kingdom+ cadence 60，base -50，直接考虑 sadistic、callous、feud、escape attempt；
它依赖 co-rulership/special legality，留在 P2。

~~~mermaid
flowchart TD
    A[prisoner + current custody/reasons] --> B{选择 stock interaction}
    B -->|unconditional release| R[compassion/time/revenge/feud/struggle]
    B -->|conditional release| C[非宗教 option + recipient acceptance]
    B -->|execute| E[reason/inheritance/vengeance/struggle]
    B -->|torture/castrate/blind/maim| P[trait/feud/escape/special legality]
    C --> V[final Can Send + exact consequence]
    E --> V
    P --> V
    R --> V
    V -->|失败| F[保留 native failure / tyranny / reason]
    V -->|通过| G[只形成 observer 机会；动作仍未设计]
    C -. conversion/vows .-> X[宗教域排除]
    E -. doctrine/tenet .-> X
~~~

## crime/reason 的权威边界

crime 不是可以从 trait、secret 或 opinion 抄出的一枚稳定外部布尔值。stock interaction 同时消费
has_imprisonment_reason、has_banish_reason、has_execute_reason、temporary legality、tyranny effects、
recipient answer 与 special validator。最小合同必须发布引擎最终 reason result、final validity、Can Send、
原生 failure reason，以及引擎实际展示的 tyranny/资源后果。planner 不重写 crime 分类，也不猜信仰派生理由。

这同样解释为什么 observer 先于 action：若只能看到 prisoner ID 而看不到 exact roles、option、cost 和 final reason，
自动玩家无法区分“当前不能做”“会产生 tyranny”“对方拒绝”“可以做但不值得”。

## P0 observer 合同

**player_prisoner_management_snapshot_v1** 是 private、read-only、paused application-main 查询：

- 无 caller-supplied character ID；actor 永远绑定当前 played character。
- 完整枚举 engine-owned prisoner collection；只返回 full generation-bearing CharacterID。
- 返回 total_count、returned_count、collection_complete、稳定 copied order/source ordinal 和 typed unavailable。
- 每个 row 返回 alive/resolved、exact jailer equality、house arrest/dungeon/unknown、time imprisoned，以及能由同一
  exact reader 证明的 hostage/prison-break 状态。
- P0 preview 为 ransom、unconditional/nonreligious release、execute legality、move dungeon 和 move house arrest；
  torture 可作为便宜的 P1 附带字段。
- 每个 preview 返回 stable definition key、全部角色、shown/candidate/final-valid/Can Send、needs-answer/auto-accept、
  visible/valid option keys、准确资源 terms 和 native failure/answer reasons。
- demand_conversion 与 take_vows 永不进入 allowlist；religion 派生只保留 opaque final result。
- 同一 paused revision 完整采样两次，最后再确认 snapshot binding 未变；任何 raw pointer 都不能越过查询边界。
- GUI 的 MAX_PRISONER_COUNT_GRID 只是显示阈值。被 cap、截断或漏 row 时 collection_complete=false，
  readiness=false，不能静默声称完整。

~~~mermaid
flowchart TD
    S[paused current-player snapshot] --> E[exact engine prisoner enumerator]
    E --> C{完整且 full-ID 可解析}
    C -->|否| U[typed unavailable; readiness false]
    C -->|是| P[复制稳定 prisoner rows]
    P --> R[读取 jailer/custody/time/reason]
    R --> I[为每个 P0 allowlist 构造 finalized context]
    I --> O[roles + options + exact cost + Can Send + native reasons]
    O --> D[同 revision 第二次完整采样]
    D --> Q{两次结果与最终 binding 一致}
    Q -->|否| U
    Q -->|是| G[player_prisoner_management_snapshot_v1 ready]
    E -. method RVA / ownership 未闭合 .-> X[下一项逆向入口]
~~~

## readiness 与遗留 unknown

本包只把 stock tree 和 exact-build source/native substrate 冻结为 static-ready。observer 尚未实现，
paused live artifact 不存在，action 没有设计，public MCP 与 planner 都不 ready；G2 的囚犯/犯罪整项因此仍 absent，
已有 pay_ransom 拒绝 loop 继续作为通用 interaction primitive 证据。

必须继续闭合：

1. Character.GetPrisoners/CourtWindow.GetPrisoners backing method、容器布局、所有权与生命周期；
2. 完整 prison relation、custody kind 与 imprisonment duration getter；
3. imprisonment/banishment/execution reasons 的 exact native surface；
4. ransom 三种角色构造和各 option payload ownership；
5. gold/current/extortionate/favor/influence/herd/hook 的准确 resource-term vector；
6. 每种 punishment 的 final consequence/tyranny presentation；
7. 至少含一名真实囚犯、能得到两类 final result 的自然 paused fixture。

以上 unknown 是下一轮可施工入口，不是把缺字段长期输出 null 的许可。
