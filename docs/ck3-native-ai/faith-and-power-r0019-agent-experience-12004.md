# R0019：从核心教改走到跨宗教采用的操作经验

R0019 在独立机制实验中完成了这条路线：原版草稿选择 → 实际创建新信仰 → 独立读回新信仰与主流礼仪 → 明示角色准备 → 按正常要求采用纳杰夫。它为现有游玩智能体补上了一次完整操作实例；本场没有证明这些教义是最少、最便宜或适合普通战役的组合，也没有观察自然 AI 作出相同行为。

`machine_id: 4-8e1c2f1861`；场次 `4-8e1c2f1861--faith-and-power--R0019`；CK3 `1.20.0.4`，EXE 身份为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。操作观察约为 `2026-10-18T13:24:32Z–13:44:49Z`，本稿于 `2026-10-18T14:18Z` 后只读整理。原始包不复制，文件身份、观察时间与 JSON Pointer 见[小型来源表](faith-and-power-r0019-agent-experience-12004.sources.json)。其中带机器身份的闭场与现场复核记录用于绑定本场；来源表保留原件是否自带机器字段，不改写历史原件。

## 草稿由实际分支决定，名称不能决定创建什么

本场实际玩家 full ID 为 `31254`，原 Faith 为 `13`、Religion 为 `8`，草稿 source Rite 为 `0`；这里的 `0` 是有效完整引用，不是缺失值。基于当前信仰窗口打开草稿后，沿现有 `ck3_execute_player_rite_creation_action_v1` 的有限操作选择核心信条与教义。核心槽 `0` 选为 `tenet_islamic_syncretism`，另两个核心保留 `tenet_apostolic_succession`、`tenet_communion`。九次教义选择均有独立选择后态，键如下：

| 教义组 | 本场实际所选键 |
| --- | --- |
| `doctrine_pluralism` | `doctrine_pluralism_pluralistic` |
| `doctrine_marriage_type` | `doctrine_polygamy` |
| `doctrine_gender` | `doctrine_gender_equal` |
| `doctrine_clerical_gender` | `doctrine_clerical_gender_either` |
| `doctrine_clerical_marriage` | `doctrine_clerical_marriage_allowed` |
| `doctrine_clerical_function` | `doctrine_clerical_function_alms_and_pacification` |
| `doctrine_divorce` | `doctrine_divorce_allowed` |
| `monasticism_group` | `doctrine_monasticism_encouraged` |
| `doctrine_clerical_succession` | `doctrine_clerical_succession_spiritual_fixed_appointment` |

这些选择通过原版候选与完整许可进入草稿，不能给普通战役照抄为最优策略。本场未评估它们对婚姻、性别、司祭制度等方面的长期代价。五个名称字段也经原版 setter 写入并读回；名称只是草稿内容，创建类型仍须读取实际 `draft.actual_outcome_kind`。

最终原生预览给出 `actual_outcome_kind=create_faith`、`full_can.can_create=true`、`can_edit=false`，费用 `piety_cost_raw=520000000`、比例 `100000`，即 **5200 虔诚**。这是本场实际完整草稿的报价，不是所有教改的固定价格。读口为 `ck3_query_player_rite_creation_action_context_v1`；选择口使用 `select_core_tenet`、`select_doctrine`、`set_name_field`。后续存档应从当场快照取得 `expected_revision` 和 source Rite，并读取原生候选；本稿中的 ID、revision 和选择键只绑定本场。

来源：`CORE`、`D0–D8`、`NAMES`、`PREPARE`；关键指针为 `/plan/args`、`/result/rite_creation_action/draft`、`/result/rite_creation_action/selection_or_name_postcondition_observed`、`/result/rite_creation_action/full_can`、`/result/rite_creation_action/quote`。

## 打开确认窗之后，再取得可提交的身份

本场 `prepare_confirmation` 只打开原版确认窗。其返回包仍包含弹窗前的草稿观察，不能拿它当“已经创建”，也不能把其中的弹窗前身份直接用于最后确认。随后独立调用预览，读到 `modal.stage=confirmation`、`kind=create`、`active=true`、`same_draft_window_bound=true`、`native_can_accept=true`，完整 `can_create` 与 5200 报价仍成立。

两阶段的原生 opaque identity 确实不同：弹窗前为 `f6a3f466…922797`，弹窗后为 `4589cff7…3ec29e`。`confirm_once` 使用弹窗后身份、实际 source Rite `0` 和 `expected_outcome_kind=create_faith`，于 `13:31:38.690–13:31:39.025Z` 执行一次原版确认。返回的 attempted/invoked/可能入队只说明原调用范围；原件自身仍写 `business_outcome_observed=false`，最终结果必须另读。

现有智能体应继续沿持久 once intent 与保留结果通道工作。结果未知时收集原请求结果，不能更换 request ID、revision 或 preview token 再确认。既有只读收集入口是 `ck3_collect_player_rite_creation_action_result_v1`，本场不以其存在声称发生了额外收集动作。

来源：`PREPARE`、`MODAL`、`CREATE`；关键指针为 `/result/rite_creation_action/modal`、`/preview_identity`、`/native_once_claimed`、`/action_id`（后四项均位于 `rite_creation_action` 内）。

## 先读新世界，再安排管理角色

最后确认之后、明确角色准备之前，独立快照与宗教查询读到：

| 观察 | 本场实际结果 | 现有公共 MCP 入口 |
| --- | --- | --- |
| 钱包 | 20000 → **14800** 虔诚，减少 5200 | `ck3_take_snapshot` |
| 身份 | 新 Faith `103`，Religion 仍为 `8`；当前与主流 Rite 均为 `150` | `ck3_query_player_religion_context_v1` |
| 核心 | 当前与主流 Rite 的 `tenet_islamic_syncretism` 均为核心状态 `4` | `ck3_query_player_religion_tenets_v1` |
| 布尔参数 | 当前与主流 Rite 的 `islamic_syncretic_actor=true` | `ck3_query_player_religion_doctrines_v1` |

这组读回发生在角色准备前，因而不能把新核心、参数或钱包变化归给后面的准备事件。这里证明的是当前及主流礼仪中的核心和相应参数，不能用个人信条同名项替代，也没有把静态脚本许可当成本次运行时读数。

随后通过 `ck3_query_current_event_window_context_v1` 确认 `xar_cross_v5.2`、实际实例 `1` 与玩家 ROOT `31254`，再以 `ck3_select_event_option` 选择明示的角色准备项；本场 `option_number=1` 对应原生 `option_index=0`。其来源仅安排管理所需神学角色关系，并无资源、核心或圣地写入。选择后钱包仍为 **14800**。这是获准独立实验的明确准备步骤，不是智能体在普通战役自然取得管理权限，也不是原版采用要求被绕过。

来源：`BASE`、`WORLD`、`RELIGION`、`TENETS`、`PARAMS`、`ROLE_EVENT`、`ROLE_SELECT`、`ROLE_AFTER`、`ROLE_SOURCE`。关键读回：`/result/played_character_piety`、宗教包的 `/result/{faith_id,religion_id,rite_id,faith_main_rite_id}`、核心包的 `/result/{current_rite,faith_main_rite}/core_tenets`、参数包的 `/result/boolean_parameters`。准备事件的静态效果与实际选择分别列源，不互相替代。

## 正常采用后，同时检查新增关联与原有共享状态

纳杰夫为实际 HolySite `32`。先用 `ck3_open_holy_site_window_v1` 打开该站点，再由原版选择详情进入固定 `adopt` 决议。`ck3_query_player_holy_site_decision_detail_v1(action='adopt', holy_site_id=32)` 于 `13:37:36Z` 给出 `parameter_and_selection_match=true`、`normal_requirements_can_confirm=true`、`native_can_confirm=true`、`bypass_requirements_raw=0`，原生成本向量与虔诚报价均为 **0**、`native_affordable=true`。应按这一实际报价规划，不能机械套用静态通常成本；也不能仅从钱包未变倒推免费次数的具体值。

`ck3_confirm_holy_site_decision_v1(action='adopt', holy_site_id=32)` 于 `13:37:40.288–13:37:40.843Z` 执行一次原版确认。独立快照及 `ck3_query_player_holy_site_v1` 随后证明：

- 新 Faith `103` 的列表 `[0,1,3,2,4]` 变为 `[0,1,3,2,4,32]`，即 **5 → 6**。
- 纳杰夫新增 Faith `103` 关联，`eminent=false`；原 Faith `51` 关联仍在，`eminent=true`。
- 同一个 HolySite 库存 `artifact_ids=[76]` 前后相同，站点 owner ID 仍为 `32`。该读口明确 `artifact_objects_resolved=false`，本场由此仅证明库存 ID 列表保留，不推导物品的完整实例所有权、认可、Active 或收益。
- 钱包保持 **14800**，与本次原生报价 0 一致。

所以“成为我的圣地”与“变成我的主要圣地”是两个后验；一次采用没有抹去旧信仰的主要关联，也没有通过库存列表证明全体受益者。不要用圣地世界注册表当作当前合法候选集合，最终以原版选中参数、完整要求与当场报价决定是否可提交。

来源：`SITE_BEFORE`、`TERMS`、`ADOPT`、`WALLET_AFTER`、`SITE_AFTER`。关键指针为 `/result/current_faith_holy_site_ids`、`/result/selected_holy_site/associated_faiths`、`/result/selected_holy_site/inventory`；决议原件的 `/result/native_resource_quote` 与 `/result/bypass_requirements_raw` 独立列源。

## 复用时保留的边界

本场采用后第一次只读查询猜了 `expected_revision=5` 并报错；随后从实际快照读取 revision `4`，只重做独立观察，未重发采用。后验存在不表示命令总使 revision 加一。原错误完整保留，并最终使原 host 进程退出 **1**；公共 launcher/public wait 为 **0**；CK3 则通过原 GUI 正常退出，保留 OS handle 的退出码为 **0**，正常闭场资格成立。这几层结果可以同时成立，不能用外层 0 覆盖 host 1。

最终物理 checkpoint 已生成，`69030069 B`、SHA `de0f97b142ea88f13797d2f025380a52c5bab396b3d4986b8be6bf3ef653cc07`；原 `driver_state_replace_receipt` 仍为 `unconfirmed`、`save_binding_verified=false`，原因为 `save_binding_mismatch`。所以本次有已观察业务后态与物理存档，不授予该存档 restore 资格，也不宣称恢复链已经闭合。

这是已有完整游玩智能体和默认关闭的 exact-build 实验 MCP 的一次实机补强；普通规划器尚未因此自动选择这九项教义、准备角色或执行这条跨宗教路线。后继可复用字段、守卫和经验，再在实际局面中比较成本、权限与长期后果。本稿不重复旧研究或旧 fixture 资格；没有新增游戏、测试、媒体扫描或构建。

来源：`READ_RED`、`WALLET_AFTER`、`SITE_AFTER`、`HOST_WAIT`、`CLOSE`、`LIFECYCLE`、`SAVE`、`ROOT_FINISH`。原 host wait 无内嵌机器 ID，其精确文件 pin 由带机器 ID 的 `LIFECYCLE` 原件引用；机器关联依此记录，不仅凭路径推定。

## 后继重规划时，分别读取领袖身份与实际模式

Rite 的创立者、Rite 的领袖与 Faith 的宗教领袖必须分别判断。既有模型中 `Rite+4BC` 是 founder，`+4C0` 是 head；创建／编辑按钮的原许可不能靠“这个角色是一位领袖”概括。实际 `editing_owned_current_rite=true` 时，控制器首先取 `edit_rite` 分支；即使另一项 `native_create_faith_or_reform=true`，也不能把编辑解释为创建新 Faith。打开编辑草稿仍不代表原版最终许可成立，战争等独立阻点应从当场完整理由读取。

这是给后继局面使用的通用方法与旧文档字段勘误，不追加 R20 未发生的创建、编辑或采用结果。R20 正式记录链接待 Root 冷场入库后补；精确字段、控制器和原函数 pins 列在来源表的 `cold_doc_correction`，旧 UI source 文档两处误标签另附最小建议补丁，不修改当前运行源码。

## 制作与规划方法

**先确认操作真正会改变什么，再讨论怎么按按钮。** 本次同一教改草稿最终进入创建新信仰分支，结论来自原版实际模式、完整许可和独立新身份读回。讲解和规划都应保留这条因果链，不能用自定名称或某个选项已选中来代替结果；为了实验走通而选的九项教义，也应与普通战役的最优选择分开讨论。

**把不可逆按钮前后的观察分成两个阶段。** 打开确认窗之后重新读取身份和费用，只用当前确认窗的一次许可提交；提交后再看身份、核心、参数和钱包。只读观察失败时先回到实际局面版本，不能因为没看清结果就重做那个按钮。这样一次工具补强才会变成下一局可以复用的决策习惯。

**共享对象要同时检查新增部分和原有部分。** 纳杰夫新增了新信仰的普通关联，旧信仰的主要关联和库存列表却仍保留。讲玩家收益、损失或影响他人时，应分别核实关联级别、原有参与者和物品，而不是把“我得到了”讲成“别人失去了”。这些后态帮助解释范围，仍不能代替未观察的认可、活跃或收益分配。


这些方法同时维护在[系列制作经验](../../promo/ck3_faith_and_power/docs/production-experience.md)。
