# R4 十二项产品变量诊断：当前 59 文件审阅与最小补丁

R4 的 10 条 used-never-set 与 14 条 set-never-used 是两次同样的校验输出：去重后为 5 项与 7 项，共十二个字段。旧错误原件、原分类及其 SHA 保持；本包不把 R4 RED 改为 GREEN。

当前 59 个正式运行文件逐文件 SHA 与十二项实际行号全部绑定于 `report.json`。结论是 **源码依赖闭合判断与补丁就绪**，下一冷载尚未执行，不能保证下一 `error.log` 为零。

| R4 字段 | 当前有效写入／消费来源（生成 runtime 行号） | 判断 |
| --- | --- | --- |
| `lyd_c3_claimant` | `lyd_c3_leadership_decisions.txt:10` → `lyd_c3_challenger_effects.txt:9` 实际 `add_character_flag`；写入在默认关闭的 native challenger probe 分支之前 | I3 已闭合真实 flag writer |
| `lyd_c3_claim_faith` | 同玩家宣告入口 → `lyd_c3_challenger_effects.txt:7`；`lyd_c3_leadership_triggers.txt:21–23` 与 on-death 实际读取 | I3 已闭合 |
| `lyd_c3_claim_rite` | 同入口 → `lyd_c3_challenger_effects.txt:8`；current-claim 与 before-migration 实际读取 | I3 已闭合 |
| `lyd_c3_proposal_owner` | `lyd_c3_leadership_decisions.txt:44` → `lyd_c3_council_effects.txt:48`，真议案锁；C2/C3资格及清理读取 | I3 已闭合 |
| `lyd_c3_recognized_leader` | `events/lyd_c3_leadership_events.txt:41` → recognition 后置成功分支 `lyd_c3_council_effects.txt:178`；`lyd_c3_migration_hooks.txt:18–28` 与死亡清理读取 | I3 已闭合，不是自动任命 |
| `lyd_c3_office_faith` | factory／recognition 设置；`lyd_c3_lifecycle_on_actions.txt:8,12` → death cleanup，`lyd_c3_lifecycle_effects.txt:70,91` 实际 Faith reconcile | 原 set-only 依赖已闭合 |
| `lyd_c2_latest_faith` | `lyd_c2_commit_effects.txt:51,91` 只有写入，没有实际消费者 | 删除两次冗余写入；实际 `faith`、返回 Faith、移动 Rite、计数与后置仍保留 |
| `lyd_c2_retired_teacher` | `lyd_c2_head_effects.txt:7` 只有写入 | 删除冗余复制；不删除原宗主人物或真实 `personal_teacher/students` 关系 |
| `lyd_c2_retired_head_title` | `lyd_c2_head_effects.txt:8` 只有写入 | 删除冗余复制；来源 title 快照、owned/owner/holder 校验、退休操作及保护后置不动 |
| `lyd_c2_previous_rite_head` | `lyd_c2_head_effects.txt:10` 只有写入 | 删除冗余复制；`source_rite_head` 原快照保持，不伪造恢复原生 HoR |
| `lyd_c2_teacher_character` | `lyd_c2_head_effects.txt:34` 只有写入，I3 个人教师未消费此字段 | 删除字段及其空包装；宗主任命不再写未生效的自动教师记录 |
| `lyd_c3_vacancy` | lifecycle/migration 写入、recognition 删除，没有实际读条件 | 删除三处写入和一次删除；职位空缺由原生 `religious_head/title` 状态检查，清理仍删除失效 recognized-leader |

## 根代理集成

仅合入 `candidate/mod_li_yu_dao/tools/` 下五份 authored 模板；逐文件补丁在 `evidence/*.diff`，前后 SHA 在报告内。不要直接复制 runtime 或覆盖生成器：根统一生成，完整 I3 单独拥有 shared hooks。

1. `school_consent_templates/common/scripted_effects/lyd_c2_commit_effects.txt`
2. `school_consent_templates/common/scripted_effects/lyd_c2_head_effects.txt`
3. `leadership_templates/common/scripted_effects/lyd_c3_council_effects.txt.in`
4. `leadership_templates/common/scripted_effects/lyd_c3_lifecycle_effects.txt.in`
5. `leadership_templates/common/scripted_effects/lyd_c3_migration_hooks.txt.in`

本轮没有重跑旧 102 套件；只对五个补丁做真实 AST 解析与受保护原生调用／权限／关系操作计数不变检查，并确认当前 59 输入在审阅期间 SHA 不变。仓库工具未找到硬断这六个冗余字段的测试，无需同步删除实际行为检查。更早模型里的 `retired_teacher` 是对原人物存续的模型记录，不是同名原生 `lyd_c2_retired_teacher` 玩法消费者；不能据它保留空写入。

源码中 legacy C2 shared-hook 模板仍是历史外置兼容输入，其 `vacancy` 不在当前 59 个正式运行文件的生成来源。正式根已有禁止 legacy shared 覆盖完整 I3 的门禁。需要今后单独试验旧 shared 路线时，应独立审阅该输入，不能把本包结论外推给它。

下一 R5 冷载需直接核对这十二项诊断是否消失。其他新 I3/I4 变量、原生类型、函数和生命周期不属于这份十二项定点审阅；本包没有给予它们实机 credit。退休人物与标题历史以实际存档和日志为证，不靠未消费 metadata 制造通过。
