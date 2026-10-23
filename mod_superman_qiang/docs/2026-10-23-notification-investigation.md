# 超人强：勾引后角色消息重复的专项排查（2026-10-23）

状态：**根因未证明，未提交通知修复，实机格子 0/32。** 本文和外置夹具把可以离线确认的事实与需要实机取证的分支分开。没有把计数覆盖扩展当成该报告已经解决。

2026-10-23T15:44:13Z同机补充：实际选中的date32/c03公共SDK没有HUD右侧消息列表读口。事件窗口context、待处理角色交互与普通HUD消息是独立通道；不能拿事件实例ID充当消息实例ID。当前诊断可以保存连续原始桌面截图观察实际可见通知及顺序，但它不提供原生消息type、subject ID、instance ID或隐藏队列全量；这些字段仍须保留缺口，不能补写。来源为本轮只读核对的冻结`mcp_server.py`、`gui_window_tree_contract.py`、`CaseClient`与bridge.cpp:5969–5997，均与选中source-index SHA匹配，未调用游戏API。

玩家于 2026-10-10 21:35（北京时间）报告：“似乎有点问题,勾引过后这个统计次数的功能可能会导致后续关于被勾引角色的消息重复出现.右边的xx怎么了弹窗每勾引一次就会多弹出一次”。[原评论](https://steamcommunity.com/sharedfiles/filedetails/?id=3812991990#comment_581684714275963017)，作者 `1668788452`。本轮没有玩家存档、截图、模组顺序或当时实际 CK3 EXE，故不能追认具体通知类型和触发次数。

## 已确认的源码边界

1. `sxad_record_pair_effect` / `sxad_record_unknown_effect` 不调用通知效果。当前生产代码唯一的 SXAD `send_interface_toast` 在“查看性经验”交互的 `on_accept`，每次交互只有一处发送；玩家描述的是其后的角色状态消息，不能仅凭“统计次数”四字认定为查看气泡重发。
2. 配对、选择及转移 helper 使用 `save_temporary_scope_as`。原版 `had_sex_with_effect` 的 `had_sex_root_character`、`had_sex_with_effect_partner` 本来就用 `save_scope_as`；它们保留原文，不是模组新加的持久角色登记。暂存 scope 的存在也不证明全局消息订阅增加。
3. 性经验特质由 `NOT = { has_trait = sxad_sex_experience }` 守卫；源码不是每次性行为无条件重新加特质。
4. 有属性转移时，会保存临时双方 scope，强制重算能力，修改净账本，删除旧 gain/loss 修正，再按新账本加一个方向的修正并重算。这条路径值得与等经验、仅计数路径隔离，但存在重建不等于已经证实泄漏。

代码入口在 `tools/gen_runtime.py` 的 `experience_effects`、`transfer_effects`、`probe_effects`、`interaction`；正式运行文件分别为 `common/scripted_effects/sxad_experience_effects.txt`、`sxad_transfer_effects.txt`、`sxad_probe_skill_effects.txt` 和 `common/character_interactions/sxad_interactions.txt`。通知排查没有改动这些生产文件。

## 本轮离线原生证据

机器身份为 `machine_id: desktop-3fevhd2-1c74096080`，由本轮实际执行 `tools/ck3_live_run_id.py machine` 取得。实际观察时间、读取路径、完整文件 SHA-256、指令跨度 SHA-256 与判断边界在[来源回执](2026-10-23-notification-native-sources.json)。

实际读取 EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，不同于旧运行投影固定的 1.20.0.3 EXE。原版 `00_romance_effects.txt` 则仍逐字匹配固定输入 SHA `a4a88fa0f36e95e865dcdd077dcb64f5985db1b9a441fcca1795494abda66211`。本子任务未读取实际 EXE 产品版本，不由脚本相同推断整个游戏版本相同，也不把以下地址用于别的 EXE。

实际 EXE 的 `force_character_skill_recalculation` effect 经 RVA `0x2CECC00` → `0x28C3BA0` → `0x28C3F40`；待重算队列存在按相同 modifier 指针移除与压紧的逻辑。`add_character_modifier` 的执行路径经 `0x1AFDB40` → `0x2491790`，非 stacking 分支先查同 modifier 定义。`remove_character_modifier` 经 `0x1AFB0F0` → `0x2491A60`，找到行后注销 timed-modifier 调度项并删除行。

这些读数不足以证明所有间接调用都没有问题，也没有测量角色消息订阅表。它们能排除“源码每次重建就必然留下一个修正或消息订阅”作为已证明结论。**pin/interest 分发、临时 context 的实际寿命及旧存档异常仍未实测。** 本轮没有启动 CK3 或操作 Steam。

## 原生外置夹具

模板为 [notification_fixture](../tools/notification_fixture/cases.json)，包含 6 个运行文件和候选格子 JSON；模板不属于产品正式运行清单。沿用现有 `prepare_live_fixture.py` 和公共 `tools/ck3_mod_acceptance.py` 的 fixture emitter/manifest 路径部署，不启用旧直接启动入口。本轮未新增 Python 编排模块或 Java 服务。

| 模式 | 重复的动作 | 用途 |
|---|---|---|
| vanilla-pair | 原版配对效果的私有别名 | 原版效果对照；仅改顶层名称，正文可精确恢复固定原件 |
| hook-equal | 生产配对 hook，双方初始经验 0 | 不经属性转移的配对流程 |
| hook-unequal | 生产配对 hook，初始经验 5 / 1 | 加上属性转移、修正与强制重算 |
| hook-unknown | 对通知对象调用匿名 hook | 单方计数、首次特质及原版匿名副作用 |
| helper-equal | 只调用 pair helper，初始经验 0 / 0 | 去掉原版性行为副作用 |
| helper-unequal | 只调用 pair helper，初始经验 5 / 1 | 直接隔离模组转移路径 |
| counter-only | 只调用计数 helper | 单方变量和首次特质 |
| modifier-rebuild | 只重建对象固定为 +1 的外交账本修正 | 不计经验的修正重建对照 |

每个模式分别 N=0、1、2、5，共 **32 个未执行候选格子**。modifier-rebuild 的 +1 账本只在该分支准备时赋值，N=0 不投影修正，是诊断输入，不冒称正常产品状态。counter-only 也仅是诊断分支，不算一次实际性行为。完整模式、事件 ID、经验预期、marker 与状态合同位于 `cases.json`。

自动入口在安排一次准备事件 `sxant.1`（新游戏后一天）后立即记录 `SXANT: FIXTURE_ARMED notification-investigation`，公共 case 仅以这个即时 marker 完成启动门槛，避免初始暂停时等待一天后事件而死锁。推进后创建一个 30 岁对象、固定其与操作者的情人关系，并停在 `sxant.2`。业务就绪 marker 仍是：

```text
SXANT: BASELINE_READY notification-investigation
```

`cases.json` 的既有 `automatic_start_marker` 与 emitter 回执的 `required_start` 仍保留该 BASELINE_READY 值；共享 `generic.prepare_case` 将其作为业务必需 marker。它们与 case 的 `required_startup` 分别控制业务与启动检查，不修改 emitter 或放松基线业务要求。

原生角色引用保存在玩家的 `sxant_ref_actor` 和 `sxant_ref_subject`，对象另有 `sxant_notification_subject` flag。此处不能把变量值猜成角色 ID，必须从实际存档或原生读回取得完整身份。

1. 只在受管外置诊断局中使用。按公共实机前置规则核验机器、实际 EXE、Steam 离线与现场资源；本夹具不替代这些门禁。
2. 在 `sxant.2` 的对象头像进入原生角色界面，手动执行关注/pin，并独立读回其选中状态；不得杜撰 `mark_as_interest` 脚本效果。清理准备阶段消息后，**在选择模式前保存共同基线**，绑定双方身份、关系、关注状态、模组顺序、机器和时间。若公共原生工具没有 pin 观测，保留原生 UI 读回证据和该能力缺口。
3. 每个候选格子都从上述同一存档重新加载，选择一个模式及一个次数。不得在一个已执行过的状态上接着跑第二格；夹具的阶段守卫也拒绝再次提交动作。
4. 动作结束停在 `sxant.4`，先采样经验、七项账本/修正、真实双方身份和动作阶段消息，再清理消息并冻结探针前清单。`sxant_stage=2` 仅表示动作阶段已提交，不表示行为覆盖正确或没有通知问题。
5. 明确选择探针选项后，阶段先置为 3，再令**同一个对象**执行一次 `death = { death_reason = death_natural_causes }`。结果未知不重复提交。记录对象真实死亡状态，并连续保存其后实际原版右侧卡片的原始画面、可见文字、出现顺序和观察时间。当前 SDK 没有 HUD 消息列表读口，原生 type、subject ID 和 instance ID 必须明确记为不可取得；可见角色文字不能冒充原生 subject ID，事件窗口实例也不能代用。
6. 分别对照同模式 N=0 与 N=1/2/5；实际可区分的合法消息类别分别计数，并说明类别来自可见文字还是源码推断。原版定义有 `lover_has_died` 和 `notable_has_died` 等，情人死亡也可能产生其他合法事件。**不能把全部消息相加后强行规定应只有一条。** 若基线在当前设置下没有可见角色死亡消息，先完成探针资格，不把“没有看到消息”当作不重复。只有实际看到并留存所选对象死亡卡片，才能确认本格探针取得资格；采样空缺或零张画面不能据此通过。
7. 如需进一步隔离查询交互，可在同一动作完成检查点重载后，比较“查看经验 0 次”和“查看 1 次”两条扩展分支；将主动查看气泡与随后原版死亡消息分别记录。冷重启对照也必须单独列为新执行记录，不算本轮已经覆盖。

选择死亡探针是为了触发引擎及原版角色消息的真实分发。直接 `send_interface_message` 人工发送一条消息会绕过可疑的角色消息接收者选择，因此本夹具没有这种直接注入。**死亡探针是否稳定产生目标右侧消息尚未实机取得资格**；它仅覆盖同类角色状态消息分发，不能未经取证代表玩家提到的每一种通知。

## 本轮实际验证与交付边界

共享结构扫描器检查了 43 个原生事件块、全部本夹具事件链接、32 格的精确动作次数与 marker、引用恢复和阶段守卫；原版别名正文可逐字恢复固定原件。两份本地化均有 UTF-8 BOM，使用仓库本地化解析器实际通过，键与事件引用齐全。首次结构检查漏掉了死亡原因 key：`death_natural` 是图标名，原版实际定义为 `common/deathreasons/00_natural_deaths.txt:6` 的 `death_natural_causes`。本轮已同步修正事件、格子合同与本文并重新取证。先前已物化的夹具应保留旧件，须从修正后的模板重新物化后才能用于实机；不得修改旧回执冒称其已经包含修正。来源 JSON 保留首次静态读数，并在 `fixture_static_validation_after_death_reason_correction` 记录修正后的文件清单、SHA 与实际时间。

现有 `test_build_release.py` 增加了 6 项专项 emitter 回归，实际生产者生成的 6 个原生运行文件与 `_notification_cells.json` 均逐字核对，清单含全部 7 文件、SHA 与大小，旁挂回执 JSON 序列化往返一致；拒绝覆盖目录/旧回执、产品内路径、bool/相等浮点索引和次数、假结果、缺字段及重复索引。全量该文件 **11/11 通过**，随后使用父执行环境对 `test_build_release.py` 运行 mypy（`--follow-imports=silent --check-untyped-defs`），**1 个源文件无问题**。该类型检查不外推为全部旧 producer 或依赖模块严格通过。机器、实际观察时间、命令环境及文件 SHA 见来源 JSON 的 `fixture_emitter_regression_validation`。

结构扫描只验证字符串和括号，不是 CK3 引擎语法、scope 或效果资格。**未执行 CK3、未操作 Steam、未跑 32 格、未观测通知次数、未实证任何修复。** 不关闭原玩家报告；后续真实结果应追加到独立实机回执，保留本次静态范围。

## 2026-10-24 追加：原生分发排查与启动修正

本次追加仍为同一机器 `machine_id: desktop-3fevhd2-1c74096080` 的离线工作；机器 ID 在合入时再次由 `tools/ck3_live_run_id.py machine` 读回。具体观察时间、当前 EXE 与原版来源 SHA、指令跨度 SHA、候选文件清单及保留期限见[精简原生结论](2026-10-24-notification-native-findings.json)。原始约 274 KB 指令回执留在外置候选目录，没有复制进产品或仓库。

| 已核实的路径 | 实际证据 | 可以支持的边界 |
|---|---|---|
| `save_temporary_scope_as` | factory `0x71FBA0` → construct `0x3770320` → vtable `0x49316C0` → execute `0x377ACF0` → setter `0x373AFC0`；setter 在 `0x373B370` 查 name ID，命中后 `0x373B438–0x373B44F` 覆盖 scope 和标志 | 同名临时 scope 不会仅因多执行一次就追加一个表项；没有证明所有 context 寿命或间接 UI 行为正确 |
| `add_to_list` | factory `0x71FC50` → construct `0x3770370` → vtable `0x49315F0` → execute `0x377AC60` → mutator `0x373B800`；`0x373B836–0x373B84D` 比较类型、子类型和完整 payload，已有则跳过插入 | 该原生列表写入去重；没有读到本次实机列表内容 |
| 正常 pin 命令 | `0x288EB45` 查成员，只有不存在且请求 true 才经 `0x288EB71` 追加；已存在且请求 false 才经 `0x288EB88` 删除 | 重复 pin=true 本身不累加；不能据此排除旧存档已被其他路径损坏 |
| 原版死亡收件人 | `death_management_events.txt:6–13` 排除已在 `send_death_management_0002` 的 actor；lover 与 pinned 收集均使用该 trigger，最终为同一 `else_if` 链 | 本夹具固定情人兼关注关系不会仅因两个身份自然排两份；不能代表未知的其他通知类型 |
| 单次 `send_interface_message` | 注册 `0x5C53D0` → construct `0x2CC6B80` → vtable `0x4837290` → execute `0x2CC9420`；有本地接收者身份守卫，正常路径一次调用 `0x2CCA2E4` publish；`0x2506B47` 将事件交给下游 handler | 单次效果正常路径只发布一次；没有测量下游 handler 订阅数，不能据此保证只渲染一张 HUD 卡片 |

这些证据收窄了可疑路径，**没有证明玩家报告是 scope 泄漏、pin 累加、修正重建泄漏或双重 hook，也没有证明任何修复已经生效**。属性转移与修正重建仍应按已有模式对照；计数 hook 重复调用与后续原版消息重复分发是两个不同的待测事实。

死亡探针还有一个时序要求：原版 `death_management_events.txt:614–616` 以 `delayed = yes` 排入 `death_management.0002`，随后通过 `00_death_management_effects.txt:1–10` 设置针对该死者的三天阻断变量。因此死亡状态或提交 ACK 不能代替消息已派发的后验，暂停同帧没有消息也不能计作“零次且通过”。在当前允许日数内若无法观察延迟派发，保留探针未取得资格的状态，不重放死亡动作。

本次合入的夹具修正只有三份 `.txt` 的 UTF-8 BOM、10 个可见事件的原版 `theme = marriage`、即时 ARMED 日志和公共 case 的启动 marker；`cases.json` 未覆盖。真实 theme 定义在当前原版 `common/event_themes/00_event_themes.txt:342`，完整 SHA 见精简回执。静态检查为 43 事件、10 可见事件、998 对括号、全部三份 `.txt` 有 BOM、原版别名正文仅 BOM 改变；它们仍不构成引擎语法或效果验收。

通知实机必须另开绑定同一保存输入的独立场次；32 个候选格子仍全部未执行，可先选择 N=0 和 N=5 分诊，再为出现差异的模式补 N=1、2。每次重载同一 `sxant.2` 保存输入并核完整 actor/subject PID，不连续累跑多个格子。优先比较 hook-unequal 与 helper-unequal，再用 helper-equal、counter-only、modifier-rebuild 和 vanilla-pair 定位副作用。实际 GUI 截图只能记录观察时间窗内的 `visible_card_count`、可见文字与顺序；当前 SDK 没有 HUD 消息清单读口，原生 type/subject/instance ID 继续保留缺口，不用事件窗口 ID 替代。启动检查通过只证明夹具已安排，不能给通知矩阵或根因判断授予通过状态。

按共同存储策略 1.0.0，外置原始指令证据按 `raw_evidence` 30 天评估，精简结论按 `record` 180 天复核归纳。精确路径、大小、SHA、实际使用时间与复核日期在精简回执中；期限不是到点无条件删除，也没有部署自动清理。仓库跟踪的结论通过正常内容维护复核，不进入本机逐文件删除器。

## 2026-10-24 追加：所选 N=0 / N=5 的可见卡片合同

`machine_id: desktop-3fevhd2-1c74096080`；2026-10-23T19:37:22Z 离线核对公共 case 与实际 `generic.root_phase` 消费路径。旧断言 `actual_n0_probe_message_instances_retained` 将 N=0 固定为必需结果，并要求当前 SDK 不能读取的原生消息实例。现改为所选 N=0 或 N=5 格子的实际可见卡片证据；`notification_baseline_probe_qualification_only` 范围不变，不授予重复通知根因、修复或完整矩阵通过状态。旧 prepared 和既有回执保留原文，必须用新合同重新 prepare，不能改写旧件补授资格。

公共 Root checkpoint 仍须保留完整 actor/subject 身份、动作前真实基线 SAVE、实际关系与通知设置、BASELINE_READY 业务日志及未执行范围，并逐项验证以下要求：

| case 断言 | 必需的实际证据 |
|---|---|
| `selected_cell_case_index_mode_and_n0_or_n5_repetitions_read_back` | 从真实存档或原生读回核对 case index、模式、N、双方完整身份及实际经验/阶段；不能只按所选按钮或预期日志推定结果。当前最小分诊为 hook-unequal 的 case 9 / N=0、case 12 / N=5，每场只提交所选一格 |
| `same_subject_original_death_probe_submitted_once_and_death_verified` | 核对动作完成、探针前 stage=2 且对象活着，记录一次原生探针选项提交及 stage=3、同一完整身份的真实死亡后验。保留 `death_natural_causes` 原版死亡路径，不直接注入消息、不重试结果未知的死亡动作 |
| `selected_cell_original_death_cards_actually_visible_and_sampling_evidence_retained` | 保留探针前已有卡片清单，以及探针后的连续原始画面和实际采样时间；至少一张属于所选死亡对象的原版右侧卡片实际可见。按可见类别记录文字、顺序和 `visible_card_count`，稳定留在多帧中的同一卡片只计一次。截图只证明观察时间窗，不能外推隐藏队列全量；没有可见卡片、派发尚未完成或无法区分卡片身份时，本格探针未取得资格 |
| `native_hud_message_type_subject_and_instance_id_gaps_explicitly_recorded` | 明确列出原生 HUD type、subject ID、instance ID 三项不可取得，保留选中 SDK 来源；本地出现序号、角色文字、源码候选 key 和事件窗口实例均不得当作这些字段 |

单独的 N=5 记录无需伪造一个 N=0 结果；N=0 记录也不代表 N=5 已执行。两场若各自创建角色，则分别绑定各自基线 SAVE 和实际完整身份，不能声称来自同一存档、相同 PID 的反事实对照。同一基线重载对照必须另有实际保存输入和身份核验。每个已死亡对象不能在同一加载状态再次作为探针，32 格候选的 `not_run` 只可随对应独立实测证据更新。尚未执行本次通知实机，以上修正只使公共合同与当前能力及计划所选格子一致。

夹具生产者的 `cases.json.required_final_readback` 也同步要求实际可见死亡卡片、文字、顺序、采样时间和 `visible_card_count`，以及当前 SDK 的原生 HUD type、subject ID、instance ID 三项缺口，不再要求不能读取的消息实例。32 格的身份引用、case index、模式、N、经验预期和 marker 不作改动。

修正前 `sxant.1012` 的 N=5 将五个 `had_sex_with_effect = { CHARACTER = scope:sxant_subject PREGNANCY_CHANCE = 0 }` 放在同一个隐藏 `character_event` 的 `immediate` 中连续调用；这只能诊断单父事件 context 的累积，未覆盖多次可见结算实例。该版本未执行，以下修正取代其 case 12 入口；旧物化件和回执保留原样，不得视作已包含新路径。

2026-10-23T19:46:13Z，同机离线追加：case 12 的隐藏入口现在只保存 5 / 1 初始经验、将 `sxant_confirmed_invocations` 初始化为 0，并创建第一个可见事件 `sxant.1201`。`sxant.1201` 至 `sxant.1205` 各有一个需原生确认的实际选项，打开窗口时不调用性行为效果；每次选择仅调用一次 `had_sex_with_effect`，随后将实际计数加一。第 i 次选项要求此前实际计数为 i−1、case 12、N=5、stage=1 且同一对象仍活着，旧步骤被重复提交时不再调用。只有第五次才记录完成经验、置 stage=2、产生原 `ACTIONS_COMPLETE hook-unequal N=5` marker 并进入仍需另行确认的 `sxant.4` 死亡探针。其余 31 格的原有动作流程、经验预期与 marker 不变。

Root 必须逐次保存这五个实际可见事件的原生定义/实例 ID、完整角色身份、实际选项和新的 revision，并仅对当前实例提交一次选项；不得用五个预计定义 ID 代替五个实际 instance ID，也不得把一次提交 ACK 当作五次完成。每次选择后核对下一窗口和计数 1、2、3、4、5；结果未知先读回，不能重复提交。动作完成后再核对 actor XP=10、subject XP=6、stage=2 和同一双方身份。`cases.json` 记录五个定义 key 及实际计数变量，最终读回保留五次实例和选项证据。

这扩展到**不同可见事件实例的结算路径分诊**，仍未执行五次完整勾引 scheme，也没有证明被调用效果内部原生 context 的全部寿命。若没有观察到累加，只能记录本次路径、模式和采样窗口的结果，不能关闭玩家报告；实际重复勾引完成路径仍需独立证据。新事件仅通过结构和 emitter 回归检查，不构成 CK3 实机或引擎语法验收。
