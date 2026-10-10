# 公共G4源码接线：STATIC_READY / NOT_RUN

基线源码HEAD：`b57d4ee9cf10306af0ea40b04bc49e514376f73c`。仅owned六路径修改，未提交/推送；ROOT统一review和集成。固定Source09/O8未改变。

新工具 `ck3_query_confucian_challenger_graph_v1` 复用现有GameplayBridgeService、validator和native provider。独立permission缺省false；全局manifest的 `host_features.confucian_challenger_readonly=true` 经公共Selection→host→原MCP子进程，设置既有 `allow_private_confucian_challenger_queries`。G2/G3开关不隐式开启G4。旧profile21/23/24、C++、service和DTO均未修改。

实际新增focused8项exit0，stderr为1803 B / `bbe6b481d2662370e2c3645f7a78bf4f91289349bf283b33140722a1f79f0994`：实际MCP参数模型extra forbid，strict revision，1–8唯一完整Faith selectors（tuple/string/bool/浮点/重复/sentinel拒绝，0与高代次合法），只读annotations、原service到native请求参数、权限关闭与跨帧拒绝、host父子透传、全局feature与待验capability声明。原native/profile及旧全套测试未重跑。stdout为空，其SHA在RESULT内；完整argv/exit/原stdio均已保全。一次git diff --check为0。

仓库适用host_features白名单只有Selection.build_argv，已更新；graphics-cache runtime key整体保存host_features，无第二白名单。依赖实际mcp2.0.0/pydantic2.13.5，AfterValidator已存在且本次真实模型测试通过。

共同manifest沿用 `ck3-mod-acceptance-shared-runtime-v1`。未来freeze须在保留其他字段的前提下增量声明本feature及capability `ck3_query_confucian_challenger_graph_v1`。文档片段source_build_ready/actual_live_qualified均false；这是待绑定声明，不把源码测试替代共同manifest/native资格。

现有Source09 producer `r48-source09-two-path-successor-sourceonly-20261010-001/produce_source09.py:23–24,91–92` 只准入两条graphics路径，不能原样用来冻结本包。未来共同源码successor需显式物化当前host与mcp_server两个修改blob，并更新source-index/host/provenance及manifest/runtime pins；公共入口修改由MAIN消费。若只投影本次Python增量，沿用既有合格native，仍需实际绑定native来源；本任务不创建该successor或新native资格。

新host/features/source改变既有shader seed的runtime key（graphics_cache.py:278–302），旧v2seed不能自动继承等价性。ROOT需独立决定新来源或有证据的兼容投影，不能因本次G4为只读就假称seed已可复用。

正式新Title/NPC、非空集合、saved旧owner-Faith与holder当前Faith join、拒绝/撤回/死亡清理/重载仍待合法实机；87/88保护不变，独立native effective doctrine仍UNKNOWN。无SDK/game/nativebuild/runtime/case/存档正文调用。

结果：`RESULT.actual.json`，5908 B / `857e76414f646c4992971f4ef3fc126b33c76813af176187eaadaee0f22fa3f1`。小原执行资料30日复核，摘要180日复核；无自动GC或重复大资产。
