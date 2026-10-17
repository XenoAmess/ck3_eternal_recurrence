# 第一期开拍研究：主要圣地满额后的实际重规划（1.20.0.4，R7 P）

R7 P 在同一暂停日期完成了“降麦加一档，再将纳杰夫升为主要圣地”：两次各实付 1000 虔诚，圣地总数保持 6，主要圣地数先由 3 减至 2，再回到 3。这条实机链证明了释放主要名额后可以重新满足升级条件；是否值得牺牲麦加的主要地位，仍需要另行评估收益。

本机记录：`machine_id: 4-8e1c2f1861`；原生观察时间为 2026-10-17 15:26:25–15:35:00 UTC；离线投影时间为 15:43:57 UTC。run 为 `4-8e1c2f1861--faith-and-power--R0007`，CK3 PID `20256`、create_time `1792250472.7258115`。冻结来源 commit 为 `b8be8ca6cb9cc01297a2a6bd318c9b6e09847c2c`，DLL SHA-256 为 `13126d50051490c29f1c82cf2fd3f1050d8e501c727805f78daf22140a6987ef`。安装基线为 1.20.0.4/build 25734779；精确 EXE、DLL、保存输入、冻结 argv 与逐份回执的路径/SHA 见[小型证据投影](faith-and-power-episode01-replanning-r7-12004.evidence.json)。

这是用户明确批准的独立机制实验：“允许独立机制实验存档，明确标注准备内容（推荐）”。C2 输入来自已披露的累计额外 +5000 虔诚、个人礼仪改为 Maliki 的准备支；此前独立采用纳杰夫付费后形成 4250 虔诚的 C2。R7 冷载 C2，配置 `enabled_mods=[]` 且配置哈希与冻结 argv 一致，原版条件/费用/效果保留。输入 `C2-nadjaf-adopted-funded.ck3` 为 50,210,503 B、SHA-256 `7bd48c5eb8c51a24badd02ba57cb030dba3526da4483479ae9adc231cea7ea7e`。原 C2、原 F/B/C 及 R5/R6 历史均作为输入或历史保留；本研究不将准备资源记作普通战役成绩。

玩家 live ID 为 `15893`；三阶段圣地查询均读到个人 rite `15`、Faith `50/sunni`，初始宗教查询读到 main rite `13`。三份独立 snapshot 均为 `paused=true/date_raw=51394920`。以下 T 为当前 Faith 的圣地总数，E 为其中主要圣地数，R=T−E；R 并非礼仪数。

| 独立读回阶段 | public/native revision | T/E/R | 虔诚钱包 | Faith50 麦加26 | Faith50 纳杰夫32 |
|---|---|---|---:|---|---|
| C2 冷载基线 | 3/2 | 6/3/3 | 4250 | 主要 | 普通 |
| 降26后 | 4/3 | 6/2/4 | 3250 | 普通 | 普通 |
| 升32后 | 5/4 | 6/3/3 | 2250 | 普通 | 主要 |

初始 `promote32` 的原生要求明确将“主要圣地少于3个”标为失败，`native_can_confirm=false`，`normal_requirements_can_confirm=false`，`bypass_requirements_raw=0`，且 `decision_confirm_invoked=false`。当时仍有 4250 虔诚、原生报价 1000 且 affordable=true。预算充足不能替代资格，普通圣地已经被采用也不能替代主要名额。

降26的原生 detail 为普通规则合法、bypass=0，报价 1000；独立 snapshot 实际减少 1000。降后重新打开升32的 detail，在新 revision 上读到普通规则合法、bypass=0，报价仍为 1000，再单独确认一次；新的独立 snapshot 又减少 1000。两次 confirm 的 ACK 都仅记 `business_outcome_observed=false`，附带 snapshot 也分别仍是 4250/3250 的前态；因此成功结论取自之后单独查询的钱包、Faith/site 关联和冷却，不能直接采用 ACK 或其附带旧 snapshot。

完整的当前 Faith 成员顺序三阶段均为 `[26,27,0,14,29,32]`，其中 `0` 是有效的 Jerusalem ID。三阶段六处 HolySite 的 type/barony ID、所有已读嵌入库存字段，以及完整 artifact ID 列表逐项相同：

| HolySite ID / key | 嵌入库存完整 artifact IDs |
|---|---|
| 26 / mecca | [60] |
| 27 / medina | [61,62] |
| 0 / jerusalem | [63] |
| 14 / baghdad | [64] |
| 29 / sinai | [65] |
| 32 / nadjaf | [] |

库存身份为 `owner_kind=holy_site` 与对应 site ID，没有另造独立库存 ID；`artifact_objects_resolved=false`，这些读回只证明库存成员列表，不证明每件神器的全部对象字段。三阶段六处站点所有已读关联 Faith 的名单一致；除 Faith50 的26/32等级变化外，其余关联等级逐项相同。例如 Faith51 的纳杰夫始终为主要，Faith50 则由普通变主要。规划状态应按 `(faith_id, holy_site_id)` 保存等级，不能将“该地点是主要圣地”当成全信仰共享布尔值。相同范围内，降级未移除 Faith50 的麦加成员关系，也未移走库存60。

两份独立冷却查询分别读到：

| 决议 key | 观察时点 | present / active | expiry_raw / current_counter_raw |
|---|---|---|---|
| demote_holy_site_decision | 降26后 | true / true | 51438720 / 51394920 |
| elevate_holy_site_decision | 降后、升前的新 detail | false / false | null / 51394920 |
| elevate_holy_site_decision | 升32后 | true / true | 51438720 / 51394920 |

因此，本次降级进入冷却时，第一次升级仍可合法执行。冷却必须按实际 decision key 读取；共享“5年”时长的脚本值不等于所有操作共享一个锁。本次未证明同一日期可再降另一处，也未证明玩家之外的 actor 具备相同资格。原生回执明确 `calendar_conversion_observed=false`，这里只保留原始计数，不换算虚构到期日。

本次原版源码绑定为：

| 源文件（相对 game/） | SHA-256 | 与规划相关的定义 |
|---|---|---|
| common/decisions/50_holy_site_decisions.txt | 80ad6a6045bdafdce514cbccf59a9cd1370eaef6749d510adcec759468065fb4 | 升级条件25–59、费用/效果62–100；降级条件191–211、费用/效果214–265 |
| common/script_values/00_holy_site_values.txt | 946bf28d0c1f1a7966596dc8ba11772f98425e1007a63eb24a197506593182b7 | 13–27：配置时长5年，符合免费行动条件时决议冷却为0 |

源码将升级/降级作用于 actor 的 Faith；升级另要求目标已属于该 Faith、尚非主要、E低于本宗教上限、满足管理权及领地或领袖条件、伯爵领持有人同 Faith。降级检查自身主要成员、管理权及 E 高于下限。两者基础费用各1000，另有免费条件，并声明好感/角色修正等副作用。上述副作用只作为源码定义记录，本组回执没有独立读回其最终数值。免费行动剩余次数仍 unknown；本次两次付费和冷却实态不替代计数查询。初始 devotion profile 可读到总量6000、level4，但缺少两次操作后的独立 devotion profile，不能把钱包消费推成奉献等级下降。

供游玩智能体采用的规划约束：

1. 在目标处于普通且 E 已满时，将目标保留为候选，先确定其余升级条件与整条链的资源需求，再评估可牺牲的主要站点。上限应由当前宗教/原生要求读回，不能将本场3硬编码为所有信仰规则。
2. 降级是会付费、进入冷却并产生副作用的独立决策。选择哪处降级需要比较当前有效修正、圣物认可、持有人与好感等损失；本片使用麦加只验证可执行链，不能直接成为普通长局的推荐动作。
3. 每步确认后先独立读回，再使旧 detail 与局面资格失效并重新规划。当前可用顺序是 `ck3_query_player_holy_site_decision_detail_v1` → 单次 `ck3_confirm_holy_site_decision_v1` → 独立 `ck3_take_snapshot`、`ck3_query_player_holy_site_v1`、`ck3_query_player_holy_site_decision_cooldown_v1`。动作固定 enum 与 actor 限制继续生效；本期实验通过不等于公共完整自动规划器已接入。
4. 如果确认后无法辨明业务后态，保留未知结果并继续查询；不得按 ACK 直接报成功或盲目重复提交。计划级预算需覆盖整条候选链，本次实付合计2000；下一次动作仍需新报价，不能依据旧值预承诺免费。
5. 使用新保存分支或保留的 C2 重开比较其他策略。反向升级/降级会产生新费用、冷却和副作用，不能当作回滚。

本研究范围仅为本场两项付费原生操作及其已读状态差异。列表回执的 `active_state_observed`、`relic_recognition_observed`、`beneficiaries_observed` 均为 false；主要等级变化不证明站点已激活、空库存已产生圣物收益、所有受益者修正已重算，亦不证明麦加→纳杰夫具有正净收益。媒体质量、实机闭场及整个产品验收应引用其各自独立记录。机制背景继续见[圣地研究](faith-and-power-holy-sites-12004.md)。
