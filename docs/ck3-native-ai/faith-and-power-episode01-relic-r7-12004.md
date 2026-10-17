# 第一期圣物实拍：供奉激活、撤回失活与选择上下文（1.20.0.4，R7）

R7 将玩家拥有的神器237供奉到纳杰夫32，独立读回确认所有权转到圣地、槽0装入237、Active由false变true、有效圣物稀有度0→4。随后按原版合法按钮撤回，所有权回到玩家、槽0清空、Active回到false、稀有度4→0，钱包实际减少500。撤回是另一次有成本的操作，不能当作回滚。

`machine_id: 4-8e1c2f1861`；run为 `4-8e1c2f1861--faith-and-power--R0007`，PID `20256`、create_time `1792250472.7258115`。原生观察覆盖2026-10-17 15:37:04–15:50:31 UTC；离线投影时间15:54:39 UTC。版本1.20.0.4/build25734779，冻结source `b8be8ca6cb9cc01297a2a6bd318c9b6e09847c2c`；DLL SHA-256 `13126d50051490c29f1c82cf2fd3f1050d8e501c727805f78daf22140a6987ef`。玩家live ID15893、个人rite15、Faith50，日期51394920且暂停。精确回执时间、调用参数、EXE/DLL/C2输入与source-review SHA见[证据投影](faith-and-power-episode01-relic-r7-12004.evidence.json)。

本场沿用用户批准的独立机制实验：“允许独立机制实验存档，明确标注准备内容（推荐）”。累计额外+5000虔诚、个人改Maliki的准备已在C2来源披露；本段接[主要圣地重规划P链](faith-and-power-episode01-replanning-r7-12004.md)实付2000之后的2250钱包。供奉神器237使用实际玩家库存，无预加圣物或修改原版供奉/移除规则；R7启动配置为空mod列表。本段不记作普通长局自然积累或整个产品完成。

| 独立读回 | 供奉前 | 供奉后 | 撤回后 |
|---|---|---|---|
| 虔诚钱包 | 2250 | 2250 | 1750 |
| 神器237 character_owner_id | 15893 | null | 15893 |
| 神器237 holy_site_owner_id | null | 32 | null |
| 玩家完整库存引用IDs | [188,189,237,267,277] | [188,189,267,277] | [188,189,237,267,277] |
| site32库存IDs | [] | [237] | [] |
| site32槽0 | null | 237 | null |
| site32槽1、2 | 均null | 均null | 均null |
| cached Active | false | true | false |
| cached有效圣物稀有度 | 0 | 4 | 0 |
| 原版当前计算 Active / 稀有度 | false / 0 | true / 4 | false / 0 |
| site32关联Faith IDs | [51,50] | [51,50] | [51,50] |
| public/native snapshot revision | 5/4 | 5/4 | 6/5 |

三阶段 `cache_evaluation_disagreement=false`，即保留的缓存值与新调用原版rarity producer所得当前值一致；并非仅根据界面预览推断激活。county/barony/holder也一致：barony6650、county6649、holder15436，县主持rite13/Faith50，`county_holder_faith_associated=true`。本段只重新核实site32的关联名单，没有重读所有其他圣地的完整等级/库存或全信仰T/E/R。

神器237的rarity level为4，显示名为“穆罕默德的斗篷”。供奉后 `sanctified_faith_ids=[]`，但原生 `recognition_for_player_faith` 与 `recognition_for_county_holder_faith` 对Faith50均为true，`recognition_semantics=native_dynamic_sanctification_or_template_trigger`。因此，空的动态圣化名单不能直接当作“非圣物”。本次没有独立拆解模板trigger，也没有读Faith51对此神器的认可；关联到同一站点不能替代逐Faith认可/收益查询。

本次实际MCP路径如下，均以原生身份和新查询约束：

1. `ck3_query_player_holy_site_relic_context_v1(32)`读空库存与Inactive；permissions/action-context对237读到玩家所有权和库存成员，指定神器的can_enshrine=true。此时selected_artifact=null，当前按钮can_enshrine=false，preview不可用。局部permission不能直接授权提交。
2. 单次 `ck3_select_holy_site_relic_artifact_v1(32,237)` 后独立fresh action-context确认selected237、当前can_enshrine=true；自动选槽分支实际调用原版picker，effective_slot_index=0、replacing_artifact=null。预览SHA为 `1538fef7242c09a65fc471740b2ae49c482818978be76ea1a809ddcf04bb904d`。
3. 单次 `ck3_enshrine_holy_site_relic_v1` 绑定该预览、expected_replacing_empty=true、expected_effective_slot_index=0。实际时间15:42:20.999512–21.392255 UTC。之后分别取snapshot、relic-context、action-context，得到表中供奉后所有权、库存、槽与Active后态。
4. 供奉后原版清空神器选择；单独选择槽0后，独立context读到 `selected_slot_index=0/selected_slot_artifact_id=237`，同时 `selected_artifact_id=null`。指定237的can_remove=true，但当前按钮can_remove=false、无preview，不能提交撤回。
5. 单次显式重选237，实际15:50:02.660473–03.192967 UTC，随后fresh action-context确认selected237、slot0仍237、当前原版can_remove=true，取得新预览SHA `ad4754581874c94cd7615fde6666681444a97c8ba11f167e90d1cb7d3ee62c1c`。
6. 单次 `ck3_remove_holy_site_relic_v1` 绑定该新预览及empty-replacement约束，实际15:50:29.039474–29.458696 UTC。之后另取三份独立读回，最晚15:50:31.292255 UTC，确认表中撤回后态。无代码修补、强行bypass或盲目重试。

供奉和撤回ACK均记录原版按钮实际enabled、frozen_preview_verified=true、dispatch=true，同时 `business_outcome_observed=false/verification_pending=true`。ACK内“after”的神器选择清空，槽内容仍可能是前态，不能作为神器所有权或库存转移的结论。两次成功都取自之后各自独立查询。撤回后的神器选择再次为空，槽0仍处于显式选择模式但内容为null；后续新操作必须重新取得其自身选择与预览。

选择语义已由[原版选择源码研究](holy-site-relic-r7-selection12004.md)闭合：供奉回调RVA17D5DD0于17D5E29清window+0x108；SelectArtifact的完整叶17D52B0只写+0x108，ToggleSelectedSlot的17D52F0只切+0x110。已装槽的原版GUI在926–927行连续声明SelectArtifact与ToggleSelectedSlot，931行高亮却是二者OR；因此高亮不能证明神器已选择。GUI SHA-256为 `23542c54dd73b0c349e008649f201b1459ef833070fb6071e089dcd210642fb2`。静态review原件SHA `512ce080d4f508d5eaae399a5884190e428164e68239ec88342c0bbd2af2a3dc` 已独立核对；它证明实现语义，本段实机资格由实际回执提供。

下表只记录原生effect预览，不授予收益实测信用：

| 预览内容 | 本次独立后验范围 |
|---|---|
| 供奉：伯爵领发展增长+4%、民众好感+4；Faith50信徒每月虔诚+4% | Active与稀有度实测；这些受益者数值没有独立读回 |
| 撤回：失去500虔诚和500奉献 | 钱包实测2250→1750；奉献总量/等级未测 |
| 撤回：预览1名宗教狂热、12名少数族群封臣各好感−20/10年 | 预览人数与效果文本已保留；角色关系及修正实值未测 |

三阶段 `world_effects_applied_observed=false`、`beneficiaries_observed=false`；不能将cached Active=true升级为“所有受益者修正已重算”。撤回不仅拿回物品，还会让本场唯一合格圣物离开站点并导致Inactive，应把这些机会成本与预览中的政治/奉献成本纳入新决策。

对游玩智能体的直接约束：

- 状态至少分别保存站点关联名单/等级、世界缓存Active/rarity、当前原版计算、逐Faith圣物认可、实际神器owner、玩家库存成员、已装槽、窗口神器选择与槽位选择。它们可能给出不同答案。
- 不把指定神器的can_*或槽位高亮当作当前按钮许可。供奉后本次指定神器的can_enshrine仍true；真正提交需当前selection一致、正确所有权/成员关系、正常按钮enabled、正确目的槽/替换对象及fresh preview。
- 选择改变后必须重新查询preview；供奉/移除会清神器选择，不能复用上一动作的preview。未知提交结果保留pending并独立查询，不自动重发。
- snapshot revision不能独自证明relic状态的新旧：本次供奉前后native revision同为4，但库存/owner/Active已变。读取新domain query的capture_epoch与实际字段，并绑定run/玩家/site/artifact身份；不可据revision相同直接复用旧圣物缓存。
- 只将实际钱包差计入已实现成本；奉献、封臣关系及月度收益保持“预览/待后验”。需要评估最优供奉时，还应比较失去个人神器所有权和装备收益的代价，本场未证明供奉净收益为正。
- 撤回属于新的有成本计划。比较策略使用保留母档或新保存分支；本次撤回后钱包已少500，不能称恢复原局。

本候选仅新增本段实机事实和规划规则。尚未声称公共完整规划器已集成、全部受益者验证、普通战役成绩、媒体质量、R7正常闭场或产品总验收完成。

后继补注（machine_id: 4-8e1c2f1861）：[R7正常闭场及媒体/业务边界](faith-and-power-episode01-r7-closure.md)与[小回执](faith-and-power-episode01-r7-closure.json)现已补齐。原生独立退出观察为2026-10-17T15:55:26.095433–26.352291+00:00，CAS11459于15:55:58.949475+00:00实际done/resources[]。public verify原exit2/research holder完成；四条raw正常收尾但未人审，whole-product仍未通过。本文原先“尚未闭场”的边界保留为建立时截点，后续事实只按该闭场来源追加。
