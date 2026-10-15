# 原版事件批后分析与持久识别

未覆盖事件遵守用户的“原生留证 → MCP 选择展示顺序中第一个已启用项 → 继续推进 → 批后离线分析”规则。已有可执行专用策略优先；前面的展示项禁用时跳过，全部禁用或没有原生选择通道时保留真实诊断。

普通规划器在生成 `unhandled_event_fallback` 后，用现有 managed state 路径查询离线知识库。事件的原生 provider/build、定义 key、calculated ID、原生选项总数、原版源码 SHA，以及所有源码选项的名称、条件、scope 和效果语句必须完成绑定。再次遇到同一源码但新的 calculated ID 时，先优先查精确条目；只有 build、可执行文件 SHA、定义 key、源码及选项目录 SHA、原生选项数和当帧角色根作用域形状均核对一致，才复用旧源码事实并在回执记录 `fresh_binding`、`adapted_from`，原条目的历史 ID 不改。来源冲突或当帧绑定不足时仍标为 unknown，不会凭未知 UI 文本制造 known。

后台分析器读取已完成批次的不可变 before/after 及 SHA，不读取 Driver 全状态，不调用 Game、MCP 或 OBS。它保留完整事件定义、每个按 native index 编号的 option、条件名称、trigger 和直接效果语句；条件和 scripted-effect callee 不在离线过程里求值。结果原子发布到 `state/evidence/event-source-registry/<fingerprint>.json`，完整 source-facts 固定在其 `facts/` 子目录。同一指纹跨批次和输出目录重用，不覆盖旧条目。

下一次同源事件命中后，规划器的 phase、reason、decision 与公开 metadata 显示 `source_reviewed_known`，`offline_followup_required=False`。选择仍由当帧实际显示顺序和原生合法性决定。已知事件仍保存动作证据，后续批次核验现有来源后不会再产生源码分析待办。批次 feeder 应透传 incident 的 known/followup 字段，并按实际 followup 计算 `offline_analysis_pending`，不能用“有 incident”代替“仍需分析”。

**source-known 不是 material success。** 它表示已审阅此来源并执行用户的第一项偏好，不表示专用 timeline contract 已通过、策略最优或与原生 AI 等价。原 registry 的失败检查保留在 before 证据。ACK、原事件实例推进、具体游戏效果分别记录；piety、stress、治疗或关系变化仍须独立后验，不能从源码或 ACK 推断已经发生。

通用后台入口是 `tools/g2_saved_campaign/offline_vanilla_event_worker.py`。在 `cmd.exe` 中运行，路径由本场配置提供：

```text
python -B -X utf8 tools/g2_saved_campaign/offline_vanilla_event_worker.py --sdk-src <frozen-sdk-src> --run-root <campaign-root> --game-root <CK3-game-data> --state-dir <managed-state> --output-root <offline-review-output> --stop-file <owned-stop-marker>
```

加 `--once` 可回填旧批次；省略时每三秒检查新批次，显式 stop marker 停止 worker。它不设置游戏或录制期限，也不关闭游戏。`--analysis-file` 与 `--analysis-sha` 可选地绑定外置候选；正常部署直接导入指定 SDK 的生产分析器。新知识条目可被已经加载消费者的同一 SDK 读取；尚未加载消费者的旧 SDK 需在正常 SDK 轮换时接入，不能把仅落盘称作运行时已识别。

定向测试为 `ck3_autonomous_player/tests/unit/test_event_offline_analysis.py`，覆盖 unknown→known、新 calculated ID 同源重绑定、不同来源/选项目录/build/角色根拒绝、跳过禁用项、原生与展示索引不同、跨批次幂等及专用策略优先。外置完整 38 项测试与 P07 实际事件核验见 `D:/codex-ck3-demos/2026-10-14-robert-30year/unknown-choice-known-source-rebinding01/DELIVERY-FINAL.json` 和 `P07-KNOWN-EVIDENCE.json`。P07 原生事件 `pam_secular_faith_events.0058`（展示索引 2、公共选项 3）及 `stress_threshold.1701`（展示索引 0、公共选项 4）均在选择成功后经离线 worker 发布源码事实，并由冻结加载器对实际 before 原件回读为 known；两者均不声明材料效果或语义最优已证实。受管长局的实际接线、来源 pins 与结果仍以当场回执为准。
