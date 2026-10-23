# 重诅咒代表场景：持续健康与不足余额扣款

此包为未来独立 `curse_representative` 场景，实机状态 **NOT_RUN**。只验证发布关键路径中的两个高风险代表；不替代完整内容矩阵、NPC、战胜事件、双件叠加、镇压期限、转赠、冷载或发布验收。

入口为 [adapter](../tools/curse_representative_acceptance_adapter.py)、[合同](../tools/curse_representative.contract.json)和供 Root 合并的[独立 registry stanza](../tools/curse_representative.registry_stanza.json)。公共 registry、host、allocator、Session 与四个 checkpoint 生产模块不由此包修改。

初始夹具仅创建物品、资源、引用和声明的初始词条。A、B 都使用原版已核来源的剑槽，A 带鲜血什一税 r3，B 带贵族胃 r3；均为 1 级、0 经验、无基础饥渴，初始异能选择不产生健康或金钱被动。初始钱包为20金币，压力输入非零。初始化时各调用一次生产 refresh 建立物品 modifier，之后装备、卸下、月结均不由夹具代做。四件普通材料只用于沿用既有 checkpoint 合同，不消费。

`machine_id: pc-20260924rtuf-f11af23c08` 的R18首份Save producer于2026-10-23T02:53:13.698415Z实际退出0，但在首次装备前真实发现初始化未清款：原生与首份Save均为276金，error.log明确拒绝负数`add_gold`。这是夹具初值故障，不是贵族胃月付业务FAIL。后继现有producer使用正值`remove_short_term_gold = gold`清除当前钱包，再加入声明的20金；首份实际Save及同帧原生钱包必须均为Q100000十进制`2000000`，否则在任何装备、库存打开请求或自然日之前BLOCKED并保留首份证据。retained evaluate使用同一初始守卫。原R18、冻结c19和旧Prepared不修改；新来源必须重新prepare。七保存、17日、420调用及五项业务断言不变，源码与离线回归不授后继实机PASS。

额外创建一件不写 schema/kind 的候选物。创建/换主回调可能在首个 Save 之前已经调用正式判定；夹具不删除其 schema，也不强制觉醒或失败。首个 Save 只记录实际已判结果，后续核对同一 item ID 的 kind、等级与随机词条保持。**不授予“实际观察了首次未判定→owner discovery”或掉率信用。**

| Save | 自然日期 | 实际路径与判定 |
|---|---|---|
| 1 | 1066.9.15 | 两剑卸下；保存原件身份、初始钱包/压力、A modifier、候选已判状态；独立 CampaignRoot 健康读数。 |
| 2 | 同一暂停日 | 原生正常装备A；保存原生 owner/slot 后验与物品 modifier；健康应相对 Save1 减少1.2。 |
| 3 | 同一暂停日 | 原生正常卸下A；独立装备后验，健康应回 Save1。物品保留其 modifier 定义是正常行为，不能要求从物品列表删咒。 |
| 4 | 1066.9.30 | 正常装备B后逐自然日推进；保存实际不足50的钱包，确认尚无扣款终值。 |
| 5 | 1066.10.1 | 正式日调度跨月；读实际 quote=50、`0<payment<50`、钱包归零及当月 `month_done`，压力实际增加。 |
| 6 | 同一暂停日 | 正常卸下/重装备B，正常管理决议→指引→管理→关闭两次；钱包、压力、quote、payment、month_done 严格保持。 |
| 7 | 1066.10.2 | 再走一天真实日调度；当月 marker/quote/payment 保持，证明本例未观察到同月重复结算。钱包和压力的跨日变化原值单列，允许合法世界收入或压力变化。 |

所有七次均使用现有 `Session.checkpoint_readback` 的真实 Save→Root 请求→strict melt→共享 callback 验证，再由本包读取同一 melted save 的额外原件与角色变量。原始存档、melted Pin、文件身份、机器、run、actor、日期和原生后态保持绑定；第三方 ACK 或 fixture 日志不授业务 PASS。

健康使用已存在的 `ck3_query_campaign_root_context_v1`，不新增 native getter。新 adapter 通过既有 `client.execute_plan` 发只读查询，沿用 Session 的预算和 bind，保留原始 row；验证 exact EXE、getter RVA `0x28C64E0`、角色/日期/原生 revision、same-frame readiness 和 Q100000 整数。健康与钱包64位值在持久化投影中用十进制字符串。若冻结DLL拒绝或当前健康不可用，健康项 **BLOCKED/UNAVAILABLE**；已观察的物品 modifier 与原生装备结果仍保留，其他四项可继续独立通过，不填造健康总值。

不足扣款使用生产脚本在真正月结中保存的 `xalw_content_appetite_quote`、`xalw_content_payment` 与 `xalw_content_month_done`，结合同暂停日原生/存档钱包和压力交叉读回。不能把初始20金币直接当作月结前实际余额，也不能把跨日钱包差额全归于诅咒。压力只核实际正增量与同日不重扣；本场不声称 CK3 调整后的数值必然等于脚本基础40。

原始装备 intent、事件实例与显示选项来源均重新消费；结果未知不再次提交。自然日证据重用现有共享投影消费者，不另建推进引擎。最多17自然日、420次预算内调用、7次 Save，未来固定 hold5400秒、timeout6600秒、正常关闭预留180秒；任何旧场次预算均不改变。正常退出继续由共享入口负责，adapter 的业务结果不替代实际闭场证明。

离线回归入口为 `python -X utf8 -m unittest discover -s mod_living_artifacts/tools -p test_curse_representative_acceptance_adapter.py -v`，纳入既有产品 discover。三个新增 Python 完整模块使用 `mypy --strict --follow-imports=silent`，`MYPYPATH` 包含仓库 `tools`、产品 `tools` 与 `ck3_autonomous_player/src`。测试只模拟 CK3/原生/官方 melter 环境边界，实际执行准备与部署闭包、Session、Root Save 生产者、全部保存消费者和 retained verify，不能算实机通过。
