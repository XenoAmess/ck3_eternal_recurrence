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

自动入口只安排一次准备事件 `sxant.1`（新游戏后一天），创建一个 30 岁对象、固定其与操作者的情人关系，并停在 `sxant.2`。就绪 marker 是：

```text
SXANT: BASELINE_READY notification-investigation
```

原生角色引用保存在玩家的 `sxant_ref_actor` 和 `sxant_ref_subject`，对象另有 `sxant_notification_subject` flag。此处不能把变量值猜成角色 ID，必须从实际存档或原生读回取得完整身份。

1. 只在受管外置诊断局中使用。按公共实机前置规则核验机器、实际 EXE、Steam 离线与现场资源；本夹具不替代这些门禁。
2. 在 `sxant.2` 的对象头像进入原生角色界面，手动执行关注/pin，并独立读回其选中状态；不得杜撰 `mark_as_interest` 脚本效果。清理准备阶段消息后，**在选择模式前保存共同基线**，绑定双方身份、关系、关注状态、模组顺序、机器和时间。若公共原生工具没有 pin 观测，保留原生 UI 读回证据和该能力缺口。
3. 每个候选格子都从上述同一存档重新加载，选择一个模式及一个次数。不得在一个已执行过的状态上接着跑第二格；夹具的阶段守卫也拒绝再次提交动作。
4. 动作结束停在 `sxant.4`，先采样经验、七项账本/修正、真实双方身份和动作阶段消息，再清理消息并冻结探针前清单。`sxant_stage=2` 仅表示动作阶段已提交，不表示行为覆盖正确或没有通知问题。
5. 明确选择探针选项后，阶段先置为 3，再令**同一个对象**执行一次 `death = { death_reason = death_natural_causes }`。结果未知不重复提交。记录对象真实死亡状态，并保存其后实际原版消息的类型、标题、对象和实例。
6. 分别对照同模式 N=0 与 N=1/2/5；不同合法消息类型分别计数。原版定义有 `lover_has_died` 和 `notable_has_died` 等，情人死亡也可能产生其他合法事件。**不能把全部消息相加后强行规定应只有一条。** 若基线在当前设置下没有可见角色死亡消息，先完成探针资格，不把“没有看到消息”当作不重复。
7. 如需进一步隔离查询交互，可在同一动作完成检查点重载后，比较“查看经验 0 次”和“查看 1 次”两条扩展分支；将主动查看气泡与随后原版死亡消息分别记录。冷重启对照也必须单独列为新执行记录，不算本轮已经覆盖。

选择死亡探针是为了触发引擎及原版角色消息的真实分发。直接 `send_interface_message` 人工发送一条消息会绕过可疑的角色消息接收者选择，因此本夹具没有这种直接注入。**死亡探针是否稳定产生目标右侧消息尚未实机取得资格**；它仅覆盖同类角色状态消息分发，不能未经取证代表玩家提到的每一种通知。

## 本轮实际验证与交付边界

共享结构扫描器检查了 43 个原生事件块、全部本夹具事件链接、32 格的精确动作次数与 marker、引用恢复和阶段守卫；原版别名正文可逐字恢复固定原件。两份本地化均有 UTF-8 BOM，使用仓库本地化解析器实际通过，键与事件引用齐全。首次结构检查漏掉了死亡原因 key：`death_natural` 是图标名，原版实际定义为 `common/deathreasons/00_natural_deaths.txt:6` 的 `death_natural_causes`。本轮已同步修正事件、格子合同与本文并重新取证。先前已物化的夹具应保留旧件，须从修正后的模板重新物化后才能用于实机；不得修改旧回执冒称其已经包含修正。来源 JSON 保留首次静态读数，并在 `fixture_static_validation_after_death_reason_correction` 记录修正后的文件清单、SHA 与实际时间。

现有 `test_build_release.py` 增加了 6 项专项 emitter 回归，实际生产者生成的 6 个原生运行文件与 `_notification_cells.json` 均逐字核对，清单含全部 7 文件、SHA 与大小，旁挂回执 JSON 序列化往返一致；拒绝覆盖目录/旧回执、产品内路径、bool/相等浮点索引和次数、假结果、缺字段及重复索引。全量该文件 **11/11 通过**，随后使用父执行环境对 `test_build_release.py` 运行 mypy（`--follow-imports=silent --check-untyped-defs`），**1 个源文件无问题**。该类型检查不外推为全部旧 producer 或依赖模块严格通过。机器、实际观察时间、命令环境及文件 SHA 见来源 JSON 的 `fixture_emitter_regression_validation`。

结构扫描只验证字符串和括号，不是 CK3 引擎语法、scope 或效果资格。**未执行 CK3、未操作 Steam、未跑 32 格、未观测通知次数、未实证任何修复。** 不关闭原玩家报告；后续真实结果应追加到独立实机回执，保留本次静态范围。
