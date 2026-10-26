# 囚禁时长：1.20.0.4 原版角色、阈值与原生读取缺口

2026-10-25T21:50:15Z；`machine_id: xenoamess-full-tower-eb9d2c1186`。本题为 Resume61 G2/M6 的独立只读机制分支，M6 owner 已确认不与其 Activity DIAG/Open mailbox 施工重叠。没有游戏、SDK、Native 调用、动作或新 provider；不改变已有释放、赎金优先级，也不作为首场前置。

## 来源与新增问题

已有[囚犯决策树](prisoner-disposition-native-ai-tree-12003.md)证明 sender 使用 `time_in_prison`，而[普通释放消费者](prisoner-release-formal-service-12004.md)保留 duration/personality 质量缺口。本题没有重做已闭合的 custody、十三选项、recipient answer、释放后命名 opinion 或 worker latch。具体问题是：**同一囚犯在不同发起角色的互动里，时长究竟从哪个角色读取；这能否直接用既有 custody 字段或游戏日差代替？**

本轮直接读取当前安装的 `Z:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/character_interactions/00_prison_interactions.txt`：222958 B，SHA-256 `1bb43b3c2061212af8d41b11314ff4e569af2a3506319f820d05877a7762abc5`，9186 行，与旧受审 script pin 完全一致。这是当前文件读取的实证；不是旧 .3 EXE ABI 的复用许可。

当前安装元数据 witness02：`D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/formal_release/INSTALLATION-WITNESS02.json`，3032 B/SHA `49f08808eb15dd2eb2d24d05f400c7dd68cf1d4d7de14741e2efbbd7417c339c`。本岗核了该小原件。它记录 CK3 1.20.0.4/build25734779，沿精确文件身份复用 EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；本岗未读或重哈希 EXE，不声称游戏已加载它。

## 十二处调用，时长属于囚犯

| 原互动与 sender 条件 | 当前 source 行 | `time_in_prison` 的实际 scope | 这项输入的作用 |
|---|---|---|---|
| 狱主发起 `ransom_interaction` | 2452 | `secondary_recipient`，被赎囚犯 | current-gold 支路与 payer gold≥25 合取，影响 sender 的 +100；不是所有赎金的硬门。full/extortionate gold 有独立 OR。 |
| 第三方发起 `pay_ransom_interaction` | 3337、3378、3497、3524 | 四处均为 `secondary_recipient`，被赎囚犯 | 分别参与基线 +100、首继承人 +10、lustful lover +100、loyal relation +100 的 current-gold 支路。这里不读取 payer 本人的囚禁时长。 |
| 囚犯自赎 `ransom_me_interaction` | 4178 | sender 当前 scope；其 AI target 为 self，4161–4163 | current-gold/extortionate-current/herd 子路读取本人时长；`impatient` 与脚本 `>1` 并列 OR。单位尚未定位，不能补成所有自赎的等待门。 |
| 狱主 `release_from_prison_interaction` | 6559、6569、6580、6591、6610 | 均为 `recipient`，被释放囚犯 | 分别是 child `>1`、高 compassion `>1`、非 playable `>3`、非 playable `>5`、近亲非 playable `>1` 的独立 +10 sender modifier；只确认字面阈值。 |
| 同一释放互动的 struggle 子式 | 6673 | 显式切到 `recipient`；外层 personality/catalyst 是 `puppet_or_actor` | compassion>0 与囚犯脚本 `>1` 是 +200 支路的一个 OR；compassion>50 有独立支路，且仍有催化剂/greed等原条件。 |

这十二处使用的 duration 主体一直是被囚禁的人；payer、狱主及发起人角色会变。读取时须在 final redirect/role 之后确定完整囚犯 ID。交互的 `recipient` 在普通赎金与释放里不是同一语义角色，不能统一按名取它。

释放的五个 duration modifier 是相邻独立 `modifier`，不构成互斥的 1/3/5 档位。同一场景可能同时满足多个；本题仅确认 authored 条件结构，不在未观测 personality/playability/kinship 时计算总分。6615–6624 的“自己的非 playable 子女” +40 分支**没有 duration 条件**，不得给它额外补时长等待。非战争条件只包住所示 compassion/family 正向分支，不等于所有释放在战时非法或 sender 总分归零。

这些都是 `ai_will_do` 的 sender 评分输入。最终 `CanSend`、recipient answer 和玩家是否值得释放仍是不同边；不能把 sender 的时长加分当作玩家合法性或实际释放成功。

## 当前 reader 的边界与准确下一入口

本轮直接读取两份既有 production source：

- `ck3_12004_prisoner_collection.cpp`，15497 B/SHA `90545bf882d658a061ba25b881d4d79eaf9c590582b27cd90f715915674ded4a`。它从玩家 land-state prisoners 集合取得完整 ID，再核目标 extension/custody relation/jailer；这里没有 duration 输出。
- `ck3_12004_prisoner_retained_target_state.cpp`，7828 B/SHA `c235cc583cfc904f1d026638d52de846ba037d5182165252ec3b65382bfeb5d4`。它在目标活着时从 extension `+0x288` relation 读 `+0` jailer ID，独立保留 held-by-player/held-by-other/free/dead；这里也没有入狱日期或 duration。

`relation+0` 的 jailer 身份不能证明邻接字段就是入狱时间。当前读取能力不能区分同一狱主连续关押、跨狱主累计时长或释放后再入狱的计时重置；这些问题须追原生 `time_in_prison` producer/getter/trigger，而不是用首次看见日期回填。字面 `>1/3/5` 的原生单位、比较、日历换算及边界取整尚未定位，不能先写成“年”或固定 365/1095/1825 天，也不能用 JS number 时间替代。

下一步已向 native_protocol_identity 请求**已有 held current-build 触发器/名称 catalog 的精确 `time_in_prison` 条目**，再交 b64 唯一执行者按真实 locator 决定是否需要窄窗口。当前没有 RVA，不发明地址或全 EXE 搜索。闭合 callable/字段及实际调用者、生产触发/失效后，才考虑在既有 selected prisoner collection 中补相同角色的只读值；不另造查询、赋值、计时器或新权限门。

## 原版 GUI 新线索与单位纠正

2026-10-25T23:46:19Z 更新；`machine_id: xenoamess-full-tower-eb9d2c1186`。本次只读查询限定在当前安装的 `game/gui`，未扫描或重哈希 EXE，也未启动游戏、读屏或调用原生方法。

直接读取 `game/gui/window_court.gui`：23731 B，SHA `e730078c5f671e7e564c6e7799215d9fabda0546d38ba615f26302b122ad5135`。283 行把囚犯页绑定到 `CourtWindow.GetPrisoners`；405、574 行在 `MAX_PRISONER_COUNT_GRID` 上下两种布局中，都使用 `CharacterListItem.GetText('imprisoned_time')`。这是可追查的具名 presentation key，不能冒充 raw duration 字段、确定的单位或已资格化 callable。

`native_protocol_identity` 已确认当前共享函数边界/索引没有这个具名 key/context 的精确注册原件；这只是现持资料的定位缺口，不证明引擎没有该 getter。下一步可用该 key 缩小已有注册资料的查找范围；在取得真实 locator 前，不新增 EXE 窗口，不从格式化文字解析数值，不猜邻接 timestamp。

旧稿把脚本字面 `1/3/5` 写成“一年/三年/五年”，缺少本轮原生单位证据，现已收紧为脚本阈值。角色、十二处调用和独立 modifier 结论不变。原 plan01/check01 作为历史记录保留；当前计划为 `prisoner-duration-plan02.json`，见[更新后的生成图与证据表](prisoner-duration-role-and-thresholds-12004-resume61-graph02.md)。

现有 `native_research_plan.py check/render` 对 plan02 实际 exit0，校验5份原件；本枚举4条 static-confirmed、3条 unknown、3个案例 pending。检查仍明确 `semantic_correctness_verified=false`、`live_execution_performed=false`；offline-only/producer unknown 不满足 live observation 方案。文件校验只证明记录与字节，不证明原生 getter、单位或运行语义。

## 入狱、释放与维护回调不能替代计时原件

2026-10-26 静态续研；`machine_id: xenoamess-full-tower-eb9d2c1186`。本段直接读取同一安装的三份原版脚本，没有 EXE 新读、游戏启动、原生调用或生产代码修改：

| 原件 | 字节数 | SHA-256 |
|---|---:|---|
| `common/on_action/prison_on_actions.txt` | 12493 | `e46f66ed9ab72f7c210842a2fac7cf432f60a8fa11e1ff0ae26f41d4eed5dbf5` |
| `events/prison_events/prison_events.txt` | 43917 | `4a9311641df34eedf885c3c0af093e1d2c14d1a01c7e64d7389dd9dded23bac6` |
| `common/on_action/yearly_on_actions.txt` | 147319 | `14c97f3845138d74a2c2552c5dd3c95de1da035014a5cdf31c92540aae3390fe` |

准确入口名是 `on_imprison` 与 `on_release_from_prison`。`prison_on_actions.txt:5–7` 将入狱者置于 `root`、狱主置于 `scope:imprisoner`；157–180 创建 `imprisoned` 记忆，保留儿童记忆标记，并允许成年后再次入狱时查询旧儿童记忆。因此，找到一条入狱记忆不能自动把其日期当作当前关押的起点；这些脚本没有给出当前关押与某条记忆的一对一身份关联。

释放回调前的代码回调说明（268–270）明确：囚犯死亡造成的离狱不触发它。301–310 又以 `escaped_from_prison_flag` 抑制普通 `released_from_prison_memory`，避免逃狱和释放记忆重复。其后的 `prison.0001` 在原狱主仍活着时才执行；普通释放分支清除 `imprisoned_me` opinion，并由狱主 `consume_imprisonment_reasons = root`，逃狱分支则改为过去式 opinion。它没有发布当前 custody 回执或原生计时值。因此，缺少释放回调/记忆不能推出仍在狱中，消费罪名也不能代替独立 custody 后态。

维护链同样不提供计时起点。`yearly_on_actions.txt:3365–3380` 的 `prison_maintenance_pulse` 先检查存在囚犯，再按字面 45/135/225/315 天安排四个维护子调用；本段尚未定位其引擎入口，不能据文件名推定额外调用频率。`prison_on_actions.txt:371–394` 在实际执行时重新枚举当前囚犯，按 house arrest/dungeon 分流，并再延迟一天排入对应事件池。两个池在执行时都检查 `exists = imprisoner`（400–403、432–435），以排除已经离狱的角色；这只核当前存在狱主，没有绑定排队时的原狱主身份。队列数量、维护次数和事件到达时间均不能当作 `time_in_prison`。

这条静态链闭合了脚本回调的角色、延迟与可见失效边界；原生计时单位、关押转移和再次入狱时的重置语义仍然未知。当前计划为 plan03，保留 plan02 原件；新增回调图边仍是源码结论，不增加 G2 实机或 Java 验收信用。

2026-10-26T00:15Z 的原 `native_research_plan.py check/render` 两步实际 exit0；校验8份原件，本图7条 static-confirmed、6条 unknown、3个案例 pending。检查仍为记录结构与文件完整性，语义和实机验证均为 false。见[plan03 生成图与原件表](prisoner-duration-role-and-thresholds-12004-resume61-graph03.md)。

## 逃狱标记的生产者与真实事件入口

同机后续直接读取 `common/scripted_effects/00_prison_effects.txt`：73376 B/SHA `ea8bb72426246692bf1f310ae7eb83715ae1b7314d046e3660df66443d486030`。`escape_from_prison_effect`（2514–2580）把当前角色保存为 `escapee`，先创建 `escaped_from_prison_memory`，再给同一角色添加 `escaped_from_prison_flag` 和 `block_for_prison_release_notification`，两者都明确写 `days = 1`，随后执行 `release_from_prison = yes`。这里的一天只属于两个脚本 flag 的期限，不能移作原生 `time_in_prison` 的单位或重置证明。

此前已固定的 `events/prison_events/prison_events.txt` 中，`prison.9001/9002/9003` 分别在 1525、1596、1676 行的 `immediate` 调用该 effect；其 `after` 分支移除通知抑制 flag。三个成功事件的释放 effect 位于 `immediate`，选项不能被当作首次执行释放的唯一原因。实际事件选择回执、窗口关闭与当前 custody 仍须分别观察。

`prison.9003` 另在 1673–1675 行先切到 `scope:prison_friend` 执行普通 `release_from_prison = yes`，才回到 root 调用逃狱 effect。因此，同行者的释放和 root 的逃狱记忆/标记不是同一角色的一个原件，不能混用。该源码关系解释了既有 release callback 中的逃狱去重分支，没有增加 getter、native clock 或实机资格。当前[plan04 图与原件表](prisoner-duration-role-and-thresholds-12004-resume61-graph04.md)补入此第九份源码；原 plan03 保留。

原 `native_research_plan.py check/render` 对 plan04 实际均 exit0：9 份原件、9 条 static-confirmed、6 条 unknown，3 个案例仍 pending；语义验证和 live execution 仍为 false。
