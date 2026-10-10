# 公共host的完整challenger/sponsor只读入口（2026-10-10）

公共MCP现可显式注册 `ck3_query_confucian_challenger_graph_v1`，直接调用既有 `GameplayBridgeService.query_confucian_challenger_graph_v1`、validator和exact-build native provider。它返回完整注册集合和challenger持有者当前Faith的sponsor scope；保存的旧owner-Faith仍是独立保存事实，不能由native集合认证。原profile默认21、readonly23及显式challenger24工具集不变。

未来共同freeze在现有 `ck3-mod-acceptance-shared-runtime-v1` 的全局manifest中增量声明下列字段；不得覆盖其他feature或capability。产品/case不能选择该开关，也不能借它选择host/source/native。缺省或显式false均不注册G4，G2/G3开关不隐式开启G4。

```json
{
  "host_features": {"confucian_challenger_readonly": true},
  "capabilities": {
    "ck3_query_confucian_challenger_graph_v1": {
      "source_build_ready": false,
      "actual_live_qualified": false
    }
  }
}
```

上述两个false是待绑定状态。共同版本发布者必须绑定实际host/source/native与必要源码验证，才能声明build-ready；实机资格另取实际收据，不能由清单或单元测试改为true。固定Source09/O8和其历史9项capability清单未改变。

现有Source09的 `r48-source09-two-path-successor-sourceonly-20261010-001/produce_source09.py` 只准入两条graphics-cache源码/测试路径，不能原样套用于本G4接线。未来共同freeze需另行明确物化本包host和mcp_server两个blob，更新source-index、host/provenance及manifest/runtime pins；不更改旧producer原件或旧Source09。该Python增量可沿用既有合格native，但必须实际绑定原native来源，不能用源码测试替代其资格。

着色器缓存的runtime key包含host、source和完整 `host_features`（`tools/ck3_mod_acceptance_graphics_cache.py:_runtime_key`）。本包的新host/feature会改变该key，因此旧v2seed的兼容性必须独立重新评估；不得默认复用，也不能把旧成功来源改写为已消费新G4版本。本任务不创建新freeze、seed或实机。

统一入口 `tools/ck3_mod_acceptance.py` 将全局feature映射为 `--private-confucian-challenger-readonly`，公共host将该flag传给原MCP子进程，仅设置既有 `allow_private_confucian_challenger_queries=True`。native必须已实际启用 `XAR_CK3_ENABLE_CONFUCIAN_CHALLENGER_GRAPH_PRIVATE_QUERY_V1` 及其既有依赖；本改动不构建或更换DLL。

参数对象只允许 `expected_revision` 和 `faith_full_ids`：revision为严格整数1..2^64-1；selectors为实际list，含1..8个唯一完整Faith ID，范围0..2^32-2，排除bool、字符串、浮点和invalid sentinel。保留完整代次，不截取低位ID。

```json
{"expected_revision": 123, "faith_full_ids": [107]}
```

示例revision只说明参数形状，执行必须读取当次实际snapshot。service继续核前后暂停帧、PID/generation、actor、日期、revision与完整DTO。未知或不完整集合不能被解释为空集合；查询不授业务成功。正式新Title/NPC、非空注册与saved owner-Faith join、拒绝/撤回/死亡清理/重载仍待合法实机；原87/88保护门槛保持。

新增离线回归位于 `tools/test_ck3_mod_acceptance_readonly_observers.py` 的 `ChallengerObserverTests`，公共选择器新增两项位于 `tools/test_ck3_mod_acceptance.py`。它们只验证新公共接线，不重跑旧native/profile验收。
