# M5 后继：独立、授独立与领土后果事实

本包继续[非主导战争范围研究](g2-m5-participating-war-threats-2026-10-19.md)，不重复军队 union。执行机器仍为 `machine_id: xenoamess-full-tower-eb9d2c1186`；来源是本任务调用 `tools/ck3_live_run_id.py machine`。本次原版来源审阅起点为 `2026-10-19T03:46:37Z`，来自时钟工具；精确后继观察、源 SHA、定义范围和本地测试记录见[机器可读证据](evidence/g2-m5-independence-consequences-2026-10-19.json)。这里读取的是该机器安装目录的脚本，不读取 EXE，不宣称它们就是当前 Game 的实际加载定义；其他机器和 mod 覆盖不能继承此资格。

## 已闭合的原版源合同

本次直接读取并全文哈希三叶：

| 文件 | SHA-256 | 已审定义 |
| --- | --- | --- |
| `common/casus_belli_types/00_civil_war.txt` | `a9f5d844413bd7acfd4d4b1611877ac34e78eb293f309c0e7a41f27aca3a0047` | `independence_war`、`independence_faction_war` 的胜利效果 |
| `common/scripted_effects/00_war_effects.txt` | `f811d12ccb11f3aae2f61b234e930e20880be9b7c065bb9f4557400bd711722b` | `change_liege_or_become_independent` |
| `common/character_interactions/00_character_interactions.txt` | `e66fc0ccaa69e84bb6b36c2c3a4cac1e8f8d871d70cf7234724a0150e2ff8a4b` | `grant_independence_interaction` |

效果主体和变化范围有三个不能混淆的区别：

1. **个人独立战争**：攻击方胜利时，只有 `scope:attacker` 调用 `change_liege_or_become_independent`。普通参战盟友不会仅凭同为攻击方就获得此效果。目标头衔列表不是这段效果逐项转移的清单。
2. **独立派系战争**：攻击方胜利时，优先遍历攻击者当前 `joined_faction` 的 `every_faction_member`；若没有该派系而存在 war，才在战争攻击方中筛 `should_become_independent` 标志。不能把所有攻击方参与者当作全部获得独立的人物，也不能把 primary attacker 一人当作全部效果范围。
3. **直接授独立交互**：`on_accept` 在 `scope:recipient` 上创建 `independency` change 并调用 `becomes_independent`，且设置 `add_claim_on_loss = yes`。它没有调用战争的逐级变更 helper，不能据交互名称猜成同一种行为。源码 `auto_accept = yes` 不是当前按钮合法、已提交或已经生效的证明。

战争 helper 先保存选定人物**当前**的 liege：如果这个 liege 的 `top_liege = this`，人物 `becomes_independent`；否则将人物 `change_liege` 给当前 liege 的 liege。因此，战胜一个自身仍有宗主的领主，脚本可能只向上移一层，不能一概写成退出整个 top realm。是否实际触发、当前层级、引擎解算后的辖境和头衔持有人仍需独立来源。

本页的“授独立交互”也不替代 P50 的 `faction_demand.1001` 民粹让步：后者调用 `successful_popular_revolt_outcome_effect`，包含同法理公国县扩展、占领及特殊政府/王国分支，见 [P50](p50-populist-loss-prevention-2026-10-18.md)。不能用本包较窄的独立战争规则缩小 AUTO193 的实际风险范围，更不重写首局损失归因。

## 当前事实消费者候选

独立纯叶 [`independence_territorial_consequences_v1.py`](../../ck3_autonomous_player/src/xar_autoplayer/independence_territorial_consequences_v1.py) 包含两层：

- `reviewed_independence_rule_v1` 只在相应文件 SHA 命中时返回上述已审条件规则，明确 `loaded_definition_verified=false`、`current_legality_verified=false` 和零动作授权。直接授独立目前只到这一层；没有为它伪造新的当前交互 DTO 或动作接口。
- `observe_current_independence_war_consequences_v1` 复用现有 snapshot 的 current `war_termination_options`，校验完整 WarID、暂停玩家、public/native frame、connection、episode、阵营、主导标志与战分；当前 CB 必须命中已审两种独立战争。可选消费**已有** `war_occupation_targets_v1` 结果，以原 normalizer 再核 actor、同帧、exact `.4` provenance 和双方主将身份，无新查询。

个人独立战争取得合格主将结果后，能把可能执行效果的 principal 绑定为 primary attacker 的真实 CharacterID。派系战争缺少当前 faction members / fallback flags 时仍保留主体集合 unknown。没有 occupation 结果、查询过期、角色不符时，不把旧主将或玩家本人补作效果主体。

已读 root 可以给出当前直辖目标**身份交集**。这与效果主体、可能辖境变化及解算后的头衔损失分别表示：`affected_title_ids=null`、`title_extent_complete=false`、`defender_realm_shrinkage_verified=false`、`title_holder_transfer_verified=false`。即使目标恰好命中玩家主头衔，也不能把这个交集当成精确丢失清单；没有交集也不能从中证明零辖境风险。当前源规则已说明影响主体可能超过或不同于目标列表，但本包没有足够的 source-bound 选定人物全辖境枚举来给出精确下界/上界。

后继最小缺口是把已有的角色、当前宗主关系和真正被 helper 选中的人物连到完整当前 subrealm title 集，再独立核引擎解算后关系与头衔。派系分支还需要源绑定的当前加入派系身份/成员或战争 attacker flags；现有 general snapshot 的军队拥有者不能替代这些政治角色。非主导 participant 的 CB/主将 reader 已经存在，不应把 consumer 缺口误写成缺少原生读器。

本候选**未接入任何规划或运行消费者**，没有改采购、投降、建设、事件选择或运行权限。它不给兵数胜率、精确失地数、可发送动作或“已保地”信用；当前新局不等待或采用本包。

## 定向验证与边界

11 项必要离线测试最终 `11 passed in 0.56s`，工具回执 `ac0ad8`、进程 exit 0。覆盖三种不同来源规则、helper 的非独立顶层分支、非主导原生主将、target 命中不等于失地、派系选择 unknown、错源/错帧/错连接/错角色、缺已有查询和输入不变。

首次 `985430` 为 2 failed / 9 passed：已有 occupation normalizer 将 EXE SHA 规范化为小写，而版本常量保存大写，候选误把同一 SHA 拒为 unavailable。实际独立 normalizer 读回 `33c5ed` 与常量读回 `462cbe` 确认原因；候选将预期常量同样规范化比较后通过，未放宽哈希内容或来源守卫。未重跑 G2 矩阵、没有 Game RPC、活 Driver/SAVE 或媒体读取，没有编译/部署 Native25 或修改冻结 SDK/COW。

执行通用存储策略 `1.0.0`，本包只写小源码、测试、文档及 JSON；没有重型写入、删除或新容量信用。源/测试资格与当前 Game 的加载和物质后验分离，原 M5 complete 保留，G2 分子不变。Root 统一集成，本代理未 stage / commit。
