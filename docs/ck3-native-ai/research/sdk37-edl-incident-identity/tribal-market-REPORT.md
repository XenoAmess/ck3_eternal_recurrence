# M7：一个部落集市村落的输入与结果真值

当前权威G2为6/8，未达项是M6/M7，M5不重做。本轮只拆原路线图中一个具体部落建设机会，不运行Game、Native、MCP、SDK服务或旧测试，不访问Driver/SAVE/video，不新增provider、平台、准入门槛或生产补丁。

先纠正已过时施工入口：Clan建设scene及cash-v2约束已在公共`904a5ab2`实现，现有`construction_scene_scope_v1.py` SHA291061fe...；冻结SDK37没有该leaf，仍用封建scope。这是部署范围差异，既不表示公共实现缺失，也不授予Clan实机资格。本包没有重写它或重跑其十项合成验证。现有cash-v2与monthly budget也已提供个人gross、complete expenses、NET及reserve计算，不能再写成净收入provider不存在。

本轮标本是原版`common/buildings/00_tribal_buildings.txt:593`的`market_villages_01`。其潜在地产必须有`tribe_01`或更高，holder不得为Wanua，并有`building_requirement_tribal`。通过当前`00_building_values.txt`的精确别名链，著录基础成本为75金币、200威望，省份无条件月收入为0.40（40个hundredths）。这些是**源码基础值**，不是本场Native最终折扣报价、当前可负担额或玩家实收增量。

|输入/消费面|已有实现|仍缺的真值或限制|
|---|---|---|
|报价|现有Native建设查询保留十槽`cost_raw_native`及final legality|没有此Tribal实际同帧报价；不能按脚本`cost_prestige`猜Native哪个槽是prestige|
|余额|现有actor resource及SDK语义快照已含typed prestige，另有gold/cash-v2|没有本标本同actor/date/native revision的实际gold+prestige；无需先造新的prestige原始getter|
|收益|省份/个人收入、完成与经济结果consumer已有|`market_villages_01`不在当前Native和Python正著录收入表；Python返回未知后跳过。不能将Native未列为正值理解为此建筑实际收益为零|
|scene|公共只增加Clan建设，封建既有结果保持|Tribal未准入，不能通过扩大政府白名单假装已支持|
|动作|Python selector和Native submit binding都明确只接受金币槽非零|Native提交端还检查`stock_cost_raw_native[1:]`全部为零；仅改Python无法安全启用此标本|
|结果|原动作UUID、slot/queue/完成、following/cold消费者已有|现有gold-only回执不能写成已独立验证200威望扣款或多资源事务|

下一次真正自然机会的最小消费条件：当前实际角色已被同帧Root观察为Tribal，且其本人拥有符合该标本条件的闲置tribe地产。沿已有只读建设查询保留完整barony/province/building/slot/occupant、final CanConstruct、完整十槽报价与资源槽来源；配对同帧实际gold和prestige、cash-v2及既有承诺/储备。没有该行或被有界扫描截断就保留unknown，普通游戏继续。**当前只能观测，不尝试穿过现有gold-only Native guard提交。**不为寻找该场景切换统治者、新开游戏或增加每日Government查询。

将来只有在typed非金币报价/预算/提交合同实际收口后，动作验收才检查：原始唯一动作及独立queue/slot身份；金币和威望分别按实际typed quote扣款、其他资源保全；自然完工及有用材料；下一普通turn消费、匹配checkpoint/cold恢复且零重放。源码0.40、省份有效税、个人gross/NET、独立建筑因果回报分别记录，不相互替代。

`SOURCE-AUDIT.json`包含当前stock、公共provider及冻结SDK37源码SHA，以及有限别名/守卫检查。没有新Tribal报价、动作、收益、政府资格、M7完成或游戏日信用。新局前门、录制和自动玩法不依赖本研究。
