# M7：Clan 建设窄分支（CK3 1.20.0.4）

2026-10-16。此增量复用原生建设与现金接口，仅拆开建设 scene；LIFE、战争策略和 Tribal 不扩。M7 仍未完成，无 Clan 实机资格、新游戏天数或实际收益信用。

实际安装为 Steam build **25734779**，depot1158311 manifest **5078208590259867811**；复用已验 EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，本包未读取或哈希 EXE。实际 stock：

- `common/governments/00_government_types.txt` SHA `f7f07123192eebf4053f917d8458639126ab42e2a7efa9176f43495a6275c86b`，Clan lines95–185：primary_holding=castle_holding，税槽为 clan_tax_slot。
- `common/governments/_governments.info` SHA `af825eb9fc59c3fde4cc74f11d2f9997419b9bd83bdf6a5dec8790d9d435b59a`，lines278–282：buildings 默认 yes。最终合法性始终由当前 native quote 决定。

原生链复用[已闭合的 .4 建设源](building-adopted-mcp-migration-12004.md)：当前 played full CharacterID、亲自持有 title 的 holder equality、barony/Province roundtrip；final CanConstruct2C77D30 使用 actor/Province/definition/slot，十槽费用2C247A0 使用 resolved actor。不会扩为替 AI 或所有封臣建设。

[建设 scene](../../ck3_autonomous_player/src/xar_autoplayer/construction_scene_scope_v1.py)先原样委托已有封建 helper，只为同帧真实 Clan key/flag新增 scene。consumer 对 Clan actual4 要求同 actor/date/native revision 的现金-v2：**NET=actual gross−complete expenses**，包含原生实际税务义务；不手算 Clan 税率，也不把 gross 当 NET。既有 gold-only quote、正著录经济增量、200金 reserve、当前月及战时全动员替代预算继续生效。著录值不是新建筑因果回报；开工、完工和实收仍独立观察。参见[现金与经济边界](construction-economic-consumers-12004.md)。

Clan 可选现金/quote缺失或只读拒绝会保留原推进步骤并记录延期。既有 pending、material、完成观察与 cold 路径不改；当前封建局不增加 Government composite 查询或停机门禁。

一次外置合成 compound exit0、10项：封建完整结果/查询等价；Clan合法正值进入 typed-submit **计划**，NET透支/缺失、错actor、非金币、缺合法性保持推进；Tribal不准入。仅执行 Python query合同、normalizer和selector，**0真实动作/0原生执行**。[公开测试](../../ck3_autonomous_player/tests/unit/test_clan_construction_scope_cash_compound_v1.py)的七个 Clan/Tribal case body 保持 AST 相同；封建改用已保留的步骤/查询投影及原 helper 返回相等。可移植测试先完成 AST 迁移检查；串行公共集成后，在当时最新 W 上独立执行一次10项 compound，1.011秒通过。该次验证包含新的封建投影断言，不能代替原完整旧 DTO 等价证据，不伪造完整旧 DTO fixture。

本次新增 stock 输入已重新预验：open_kaishek checkout `1643d03d3a8d2ae1547e352d724e2b1a721c98ba`，现有 kaishek-cli0.1.0-SNAPSHOT pure-Java lossless parser，命令 `java -jar <existing-cli.jar> parse --file <clan-block.txt>`；实际1903B corpus SHA `c9351275a82b5e8a59b325dcc083ce088b2f80f8385c2430a169d59acabcd3ee`，607 tokens/27 blocks/0 diagnostics/roundTrip=true。jar身份与checkout分别登记，未声称本次重建。Parser只覆盖语法；Python预算、native调用和 .4 政府实机语义没有对应 finite-runtime，另记 not-applicable。

下一门槛是未来实际获准 Clan 场景的一次必要 quote→submit→独立 material→next-turn/cold；当前连续30年无停机修复主局不等待研究、不切 ruler/seed。
