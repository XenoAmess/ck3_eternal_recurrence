# M1：撤销头衔的拒命兵力估计由 AI 意愿消费

`machine_id: xenoamess-full-tower-eb9d2c1186`；观察 `2026-10-25T21:57:58Z`。本页续接 [成员与拒命战争调用链88](g2-m1-membership-callers-12004-resume61-2026-10-26.md)，补上其兵力估计的真实调用者，纠正初版没有 GUI caller 就称“预览”的措辞。目标仍为既有 exact 1.20.0.4/build25734779/EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；本轮只核五份本地脚本，不重新读取 EXE、连接或操作游戏。

实际源链是：`00_revoke_title_interaction.txt.ai_will_do` 的两个 modifier → `revoke_refusal_war_would_be_massive_trigger` → `revoke_refusal_war_rising_strength_value`。不是已证实的玩家 GUI 数值或玩家合法性前置。源 pin 与边在 [plan91](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/m1_research/refusal_consumer91/plan.json)，图由同一 plan 生成：[graph91](evidence/g2-m1-revoke-refusal-ai-consumer-12004-resume61-graph-2026-10-26.md)。

`00_revoke_title_interaction.txt:962–972` 声明 AI recipient 来自 vassals，`ai_potential` 要求可撤销头衔的 realm-law flag 和至少 county 主头衔。**`ai_frequency=0` 在此不表示关闭**：紧邻注释明确写由 code 调度，并指向 AI defines 的 `REVOKE_TITLE_TICK`。后者定义七个 tier 槽的检查间隔；注释还说成功撤销后、囚禁 vassal 后会在次日重新检查。本轮没有 exact .4 scheduler body，不能把这些配置注释外推为当前某 NPC 的实际检查日、缓存失效或必定评估。

实际兵力风险 consumer 位于 willingness 的两处 `factor=0` 分支：

- `1474–1488`：recipient 不是由 actor 关押的囚犯、不是男爵、不是 ecclesiastical，且 title revocation 为 tyrannical、massive-refusal trigger 成立。
- `1490–1500`：recipient 是 ecclesiastical、没有 excommunicated trait，并且同样满足 tyrannical 与 massive-refusal trigger。

这只是两条确定的脚本分支。没有重新构造完整 `ai_will_do`、随机调度或最终 native send chain，也没有以“原版谨慎”宣称已实现等价我方策略。

`00_interaction_triggers.txt:198–205` 的 massive trigger 把 liege 设为 root，并保存本次 `liege_temp/rebel_temp`；它要求没有 revoke-title reason、政府没有 `no_powerful_vassals` flag，然后比较 liege 当前军力是否小于 rising-strength value。后者在 `00_interaction_values.txt:525–536` 从 rebel 当前军力起步，只加 `every_powerful_vassal` 中通过 base + tyranny trigger 的当前军力。

而 `war_for_revoke_effect` 的实际拒命分支从 `every_vassal` 枚举，以多条关系/tyranny/好感 OR 过滤，并追加 bloc 同盟候选；最后才由 `vassal_join_rebel_war_effect` 加入 exact matching refusal war。两者在候选来源和条件上不等价：**这个 AI 风险估计不能被认证为实际参战者完整名单或完整总兵数**。本轮没有断言其低估或高估的方向，没有构造当前反例，也没有证明当前我方读了该数值；不据此增加新 guard 或替代估计器。

玩家 GUI、玩家动作 legality、AI willingness、实际成员/战争后态继续分开。收到 interaction ACK 不能证明这些 AI 分支已运行，读到当前 faction member 也不能反推拒命战争参与者来自普通 `ai_join_score`。新数据需求若进入自动玩家，仍须定位实际 native producer/caller 和当前帧输入；本页只提供可复用源树。

本轮按既有 `native_research_plan.py` 做记录/完整性检查与生成图；源边只标 static，实际调度和选择→拒命执行保持 unknown，零实机案例。没有新增生产模块、动作、游戏日、测试/构建或运行资格；正文/plan/图保持本岗 D2MiB、Z docs128KiB 小型预算与 08:00Z 复核。
