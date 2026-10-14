# 原版事件批后分析与持久识别

未覆盖事件继续遵守用户的“原生留证 → MCP 选择实际第一显示项 → 继续推进 → 批后离线分析”规则。已有可执行专用策略优先；第一项禁用或没有原生选择通道时保留真实诊断，不改选另一项。

普通规划器在生成 `unhandled_event_fallback` 后，用现有 managed state 路径查询离线知识库。事件的原生 provider/build、定义 key、calculated ID、原生选项总数、原版源码 SHA，以及所有源码选项的名称、条件、scope 和效果语句必须完成绑定。源码缺失、解析失败或绑定不一致时保留 `unknown_unable_to_source_review`，不会凭未知 UI 文本制造 known。

后台分析器读取已完成批次的不可变 before/after 及 SHA，不读取 Driver 全状态，不调用 Game、MCP 或 OBS。它保留完整事件定义、每个按 native index 编号的 option、条件名称、trigger 和直接效果语句；条件和 scripted-effect callee 不在离线过程里求值。结果原子发布到 `state/evidence/event-source-registry/<fingerprint>.json`，完整 source-facts 固定在其 `facts/` 子目录。同一指纹跨批次和输出目录重用，不覆盖旧条目。

下一次同源事件命中后，规划器的 phase、reason、decision 与公开 metadata 显示 `source_reviewed_known`，`offline_followup_required=False`。选择仍由当帧实际显示顺序和原生合法性决定。已知事件仍保存动作证据，后续批次核验现有来源后不会再产生源码分析待办。批次 feeder 应透传 incident 的 known/followup 字段，并按实际 followup 计算 `offline_analysis_pending`，不能用“有 incident”代替“仍需分析”。

**source-known 不是 material success。** 它表示已审阅此来源并执行用户的第一项偏好，不表示专用 timeline contract 已通过、策略最优或与原生 AI 等价。原 registry 的失败检查保留在 before 证据。ACK、原事件实例推进、具体游戏效果分别记录；piety、stress、治疗或关系变化仍须独立后验，不能从源码或 ACK 推断已经发生。

通用后台入口是 `tools/g2_saved_campaign/offline_vanilla_event_worker.py`。在 `cmd.exe` 中运行，路径由本场配置提供：

```text
python -B -X utf8 tools/g2_saved_campaign/offline_vanilla_event_worker.py --sdk-src <frozen-sdk-src> --run-root <campaign-root> --game-root <CK3-game-data> --state-dir <managed-state> --output-root <offline-review-output> --stop-file <owned-stop-marker>
```

加 `--once` 可回填旧批次；省略时每三秒检查新批次，显式 stop marker 停止 worker。它不设置游戏或录制期限，也不关闭游戏。`--analysis-file` 与 `--analysis-sha` 可选地绑定外置候选；正常部署直接导入指定 SDK 的生产分析器。新知识条目可被已经加载消费者的同一 SDK 读取；尚未加载消费者的旧 SDK 需在正常 SDK 轮换时接入，不能把仅落盘称作运行时已识别。

定向测试为 `ck3_autonomous_player/tests/unit/test_event_offline_analysis.py`：14 项 synthetic portable cases，覆盖 unknown→known、不同来源/事件/选项/build 拒绝、禁用首项、不可解析来源、跨批次幂等、专用策略优先和无重复待办。另用真实冻结 health.1112 上下文及普通 registry 重放验证了同进程 unknown→source-reviewed-known；这是离线重放，不冒充实机新动作。受管长局的实际接线、来源 pins 与结果仍以当场回执为准。
