# M1：成员继承开关不等于派系目标接续

`machine_id: xenoamess-full-tower-eb9d2c1186`；观察时间 `2026-10-25T21:52:46Z`。这是本机原版目录七份文件的源审，目标版本沿用 1.20.0.4/build25734779、EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。当前元数据见 `resume61/formal_release/INSTALLATION-WITNESS01.json`；其证据仅复用原全文件哈希并核文件身份，不是本轮重新散列 EXE 或 Loaded 实机资格。源 pin、边和未闭问题在 [plan90](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/m1_research/inheritance90/plan.json)，图与源表由它生成：[graph90](evidence/g2-m1-faction-inheritance-12004-resume61-graph-2026-10-26.md)。M3 已确认本轮没有覆盖此分支。

`_factions.info:305–311` 说的是**成员的继承人**：因继承发生 liege 或 tier 改变的 heirs 可以继承 faction membership，文档默认值为 yes。它没有说“原目标君主死后派系必定换成其玩家继承人”，也没有给出“哪位继承人、哪次 title 分配、哪个调用顺序”的 native 实现。不得用一个 `inherit_membership=yes` 同时证明成员转移、目标改换、领土连续或派系仍存在。

| 所核类型 | `inherit_membership` | 需要 county / character | 人类成员的定义差异 |
| --- | --- | --- | --- |
| independence、liberty、claimant | 三份定义无显式 override；仅 `.info` 文档默认 yes | 无显式 override；文档默认 no / yes | 沿各自公共和类型特定 gate，不能等同 AI 的加入意愿 |
| nation_fracturing | 无显式 override；文档默认 yes | 无显式 override；文档默认 no / yes | 沿 common validity，另有 ceremonial-liege 条件 |
| populist | **显式 yes**（1136） | **显式 yes / no**（62–63） | `player_can_join=no`；`is_character_valid` 同时要求 AI |
| escalated_peasant | **显式 no**（1832） | **显式 yes / yes**（1182–1183） | 显式允许玩家加入；persistent validity 没有普通 populist 的 AI-only 条件 |
| peasant | **显式 no**（766） | **显式 yes / no**（39–40） | 显式禁止玩家加入；leader 由 demand 效果准备 |
| nomadic | **显式 no**（575） | **显式 yes / no**（24–25） | 显式禁止玩家加入；county/holding 条件另有本类限制 |

这里的“文档默认”没有升级为当前 native loader/default 或当前 loaded mod 合并结果。未启动游戏、未查看当前已加载定义，不能把没有 override 的源码行写成当前对象已读回字段。

县与角色的存续条件也不同。普通 populist 的县须仍对当前 holder.top_liege 构成相应文化/faith/state-rite 的 grievance；玩家首都另受明确保护。其有地角色须为目标的直接 vassal、至少伯爵，并继续满足 grievance、无 joining block、未被囚。escalated_peasant 的县另要求 Dynastic Cycle、当前 top-liege 关系及非 nomad/herder holding；其 character validity 没有复制这些县条件。peasant 通常针对直接 holder，特定 restored-Rome 分支针对 top-liege；nomadic 针对 top-liege 并检查 nomad/herder 地产。不能把“某角色不再合法”自动外推为所有县成员一并失效。

这些定义明确允许若干县派系在没有普通角色成员要求时存在，所以“没有可送礼的角色”不授“没有派系压力”。相反，`inherit_membership=no` 也不等于“整个 faction 在该成员死亡时必定销毁”。实际 leader callback、县成员、特殊角色、war 关系和 native requirement 检查仍分别参与；本轮没有重做已闭合的 claimant 死亡→depose-war 分支。

`common_character_validity_trigger` 检查当前角色与当前 faction target 的 liege/active-contract 关系、tier、block、bloc 与 blood-brother 等条件。定义继承开关和这些 persistent validity 的存在，仍不能证明引擎先继承再验、先验再重定目标或在哪个更新点运行。该具体 native dispatcher/caller 是 graph90 的虚线入口，不拿 [88 的 GUI/AI/显式事件调用链](g2-m1-membership-callers-12004-resume61-2026-10-26.md) 补造它。

对当前 M1 接线的含义仅限数据口径：继承后必须以当前 actor、完整 source frame、当前 targeting faction 和当前县/角色集合重新判断。旧主体的完整集合可以保留历史来源；没有连续性资格时，不能把旧主体与新主体直接算成失县，也不能假定旧派系已消失。现有 Realm owner-continuity guard 保持原样，没有依据本页新增 DTO、查询、自动动作或新的 clock。

本轮实际执行 `native_research_plan.py check` exit0，核七份源文件；图中三条 definition/validity 边为 source-only static，三条 native 执行边保持 unknown，两个 runtime 案例 pending。检查只证明记录结构与文件一致性，不验证作者语义，不授自然继承或实机安全。无新增 Java/Python 生产实现、测试/构建/Game/Steam 操作；小型输出沿本轮 D 2 MiB/Z docs128 KiB 上限与 08:00Z 复核，未复用旧租约、未删除原件。
