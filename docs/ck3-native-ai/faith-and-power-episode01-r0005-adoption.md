# 第一期R0005：一次采用、真实付款与仍未激活的空站点

`machine_id: 4-8e1c2f1861`；实际编写2026-10-17T12:07:31.988477+00:00。本稿采用后态截止2026-10-17T12:01:37.316636Z、C冻结截止12:04:35.487269Z；正常闭场随后于12:10:12.274575Z释放现场，另附后继回执。C冷恢复/完整driver绑定与媒体QA尚未结算。CK3 1.20.0.4 / EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；本场PID12556/gen1、玩家15893、当前Rite15、Faith50、main Rite13、date_raw51394920。B冷载取得本场`ACTUAL_SAVED_CAMPAIGN_CURRENT_CONTEXT_BOUND`及实际身份查询；不继承R4旧进程或driver绑定资格。

[单场历史记录](evidence/faith-and-power-episode01-r0005/adoption-case.json)冻结前态、一次原版Confirm及独立after、精确回执SHA/帧和未观察字段。原件根为 `C:/workspace/ck3-faith-and-power-20261017/episode01/`。本lane只读owner包；没有游戏操作、重放动作或重跑旧静态/native fixture。

## 本场实际新增的事实

12:00:23.622344Z本场最终详情：actor/parameter/selected32一致，bypass0下普通CanConfirm=true、原生quote1000piety、affordable=true，采用冷却前态absent。12:01:34.566243–12:01:34.913859Z仅一次`ck3_confirm_holy_site_adoption_decision_v1`，原版Confirm实际尝试；返回仍是verification_pending，`business_outcome_observed=false`，不把ACK当成功。

12:01:35.840607Z独立HolySite后读：Faith50名单由 `[26,27,0,14,29]` 变为 `[26,27,0,14,29,32]`。同一full ID32/type nadjaf/barony6650成为本Faith普通站点，after对Faith51仍关联且为eminent。**本场before有Faith51关联，但没有捕获其eminent字段；只能证明关联保留、after为主要，不能补写同场等级未变。** 该普通默认等级也仅是本次结果，不声明所有版本/动作的引擎通则。

独立钱包从225000000降为125000000，scale100000，即实际扣1000虔诚，与本场报价一致；日期/actor不变。这次是付费采用，不把报价当通用费率，也不倒推free count=0。采用后详情真实返回`adoption_detail_definition_unavailable_or_different`，其cooldown/普通许可未观察；这是原版Confirm清详情后可发生的诊断，不能当作采用失败、无冷却或重试理由。

采用后C于12:04:06.638110–12:04:07.725651Z实际保存，50,209,844 B，SHA `0f1774d0be0f7652ce8dda22ce76a1eceeb36b6f9d42ae15422eae5bfd4cd18f`；12:04:35.487269Z冻结 `scenario/saves/C-nadjaf-adopted.ck3`，原生保存与copy收据SHA相等。driver仍unconfirmed/save_binding_mismatch；C冷载尚未执行。已保存不等于完整恢复绑定通过。

## 归属、Active与受益分账

| 账 | 本次独立前后态 | 边界 |
| --- | --- | --- |
| 站点与归属 | same32/nadjaf/barony6650；关联Faith `[51]→[51,50]`，50新增普通，51 after主要。 | 同barony的kufa35不是该实例；Faith51 before等级unknown。 |
| 库存 | 目标32前后三槽为空、artifact IDs为空；after owner为HolySite32。 | 空案不能验证已有非空圣物/slot/owner的保留，更不能证明不同Faith入口库存共享。 |
| 当前县主 | 15436 / Rite13 / Faith50未变；county6649。 | 土地持有者、当前玩家Rite、Faith圣地关系分别保存。 |
| 当前relic evaluation | county_holder_faith_associated从false到true，rarity sum仍0，is_active仍false。 | 采用确实入网，但本次空站点未因入网激活。不能从此推出所有固定效果或角色属性都为零。 |
| 缓存世界状态 | is_active=false、total rarity0；refresh_time_known=false、world_effects_applied_observed=false。 | 不把当前getter评估当世界效果已刷新；保留两套来源。 |
| 真实受益者 | beneficiaries_observed=false、beneficiaries=null。 | 不是“无人受益”；实际属性/修正、建筑启用和完整收益尚未验证。 |
| 冷却/free/kingdom | 冷却前态absent；after详情不可读，free数与used kingdoms没有本场完整前后读口。 | after保持unknown，不为补读重复采用或重启。 |

这给智能体一条可复用的工作顺序：先独立确认网络成员和付款，再判断激活与经营收益；不能因after详情消失而再次提交。没有after受益者就不将预计收益记入资源账。未来新局必须重新读当前许可/报价，历史案例不授权动作。

## 第一期还缺什么，可怎样取材

已阅读全文拍摄交接、第一期README、镜头矩阵和导演第一期，核对三处live result slots。此次核心可支撑H01-07 / E01-L01及L03的**有界母案答案**；最终填槽仍需原片SHA/PTS和producer审核，未知free/kingdom/非空库存不可被口播抹去。H01-01/04可引用分开标识的R3 A拒绝、R4 B准备与本场许可，不剪成一次无缝单变量实验。

同场可优先补短只读画面：Faith50新增名单及普通等级、Faith51的当前主要关联、钱包实际付款、空库存与未Active、Baghdad14多Faith等级及32/35不同实例。完整Requirements与付款前后UI应有对应原生回包。县主/男爵/县民/领主与真实受益者的因果，不能靠一次采用代替。

定向综摄C、新建picker/实例、免费额度对照、晋降/放弃及圣物返还仍需独立合法场景和额外动作，未由这一次Confirm完成。E01-L02原稿明确是可省略的可恢复支线；不为凑镜头浪费母案，也不把缺原生动作通道说成游戏不合法。第一期完整审阅版、供奉/移除第二条试拍、配音字幕、影片与人工签核仍分别推进，本场一次采用不等于整期已完成。

## 持久规划知识与资格

既有`ck3_query_holy_site_planning_knowledge_v1(action="adopt")`新增`historical_case_evidence`，小型静态常量引用本页case路径/SHA，并携带范围明确的单场结果及unknown。当前规则仍按exact `allow_adopt_any_holy_site`：导演案旧多余`faith`拼写已作一处文本更正，不改变原版资源。

历史字段不会覆盖当前许可：顶层仍`qualification=source_reviewed_static/state_observed=false/native_legality=null/action_ready=false`；其他action和不支持build不携带本采用案例。回复深拷贝保留case不被调用者注释污染。新增验证只消费这份历史payload及其scope/immutable source绑定，不重做已合格的原生或静态规则矩阵。

统一存储策略1.0.0：仅小型来源记录/代码/文档，不复制原片、存档或大wire。记录2027-04-15复核，应用核验后的派生patch按48小时复核。闭场等后继事实另记，不覆盖此不可变case，否则MCP的record SHA必须同步更新。

## 后继闭场与本次新知识验证（实际追加2026-10-17T12:16:53.948627+00:00）

[闭场小回执](evidence/faith-and-power-episode01-r0005/lifecycle-close.json)实际核到同PID12556的原版GUI退出、retained HANDLE exit0及native cleanup_proven，原driver等待与keeper实际退出均0；screen CAS11345于2026-10-17T12:10:12.274575Z进入done/resources[]。正常关闭只结算生命周期：原回执business_pass=false不替代采用的独立after，也不授整期媒体合格。

公共verify原等待于12:13:59.815509Z实际exit2：research_holder_completed=true，但case/gui合同均未合格、business/product均false；scope明确研究/拍摄holder，实际采用和媒体证据独立审阅。此处不能写公共verify PASS。Root保留外置exit helper首个metadata在exactsteps predispatch拒绝的原件，未到native动作；修正后正常退出只提交一次，不抹去首个拒绝。

[新增知识口资格](evidence/faith-and-power-episode01-r0005/knowledge-mcp-qualification.json)在12:09:09.390120Z通过真实生产create_server与MCP Client：1项新测试、4次MCP调用，确认采用历史仅在对应action/build出现、深拷贝不受调用者修改污染，资格守卫保持。无游戏、旧native/fixture或既有静态矩阵重跑。证据绑定最终四份代码/数据SHA。

采用case及MCP历史截止仍固定于C冻结时刻12:04:35.487269Z，其中normal close尚未验证是该历史截点的unknown；本段后继证据已结算正常关闭，保留原case SHA以便复现。采用后的cooldown/free/used kingdoms、真实受益、非空库存保持、C冷载/完整Driver绑定以及媒体人工审阅仍未补证。

## 后继原片核验与有限保留

[媒体与存储补注](evidence/faith-and-power-episode01-r0005/media-and-retention.json)记录同机后继核验：R5原片93,233,721 B，120秒/2490帧，完整解码exit0、PTS严格递增，为VFR且无原始音轨。报价前态候选12.033–32秒、确认视觉链32–44秒、纳杰夫空库存后态55.033–74秒、巴格达对照96–116秒；这些是剪辑候选，不是clean span或人工1×签核。最终CFR输出须继续披露源片帧率与时间间隙。

Root已登记R5原片、C、live原始证据与F/A/B六组当前活跃输入的有限保护，统一在2026-10-24T12:17:24.991058Z人工复核、不自动续期。原片默认30日、checkpoint默认14日，真实闭场时间不因复制或扫描重置。2026-10-17T12:17:24.991058Z闭场容量核对仍满足已激活总预算；这不替具体整期编码作峰值准入。采用案例、后继生命周期与媒体证据保持分账，原case SHA不变。
