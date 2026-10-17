# 雇佣候选诊断与现有原生计时的紧凑投影

`machine_id: xenoamess-full-tower-eb9d2c1186`；本机静态验证时间：2026-10-17T22:12:33Z。机器身份由 `tools/ck3_live_run_id.py machine` 当次读回。本文记录公共源码和离线测试，不声明已部署到正在运行的 SDK 或取得新 Native 资格。

## 雇佣诊断

完整市场先经 `assess_mercenary_reinforcement_v1()` 选择，再由 `war_mercenary_observer_v1.project_mercenary_observer_v1()` 压缩全池诊断。直接 assessment API 和 canonical market 输入保持完整；计划与 durable pending 保存 exact `selected_candidate`、其余原 decision 字段，以及候选总数、合格数、各拒绝原因计数和 canonical JSON SHA。

非选中反事实明细明确不保留，SHA 不是已归档原件，也不保证可以完整重建。投影没有新增 archive writer、目录、物理配额或固定机器配置。已有原件的保留仍按其实际用途和通用存储策略处理。

当前已验证市场 query 的 history index、query_sequence 与 source frame 作为普通来源引用保留，明确 `immutable_archive: false`。宿主若已绑定 assessment 源 SHA，可通过 `driver.war_mercenary_assessment_source_sha256` 注入；未绑定时如实为 null。来源引用不参与动作授权。

`war_mercenary_consumer_v1` 在挂 plan 前应用该投影；typed submit 也覆盖接受旧完整 decision 的调用方，在 durable pending 前投影。公司 ID（包括合法的零）、推荐、当帧守卫、Native 提交字段、机器 reason、独立 presentation 与支出判断均未改。没有修改 strategy 或 Service。

一次 Runtime 大包不能全部归因 Native 传输。Root 提供的 AUTO40 诊断有 584 个候选，而实际 Native inner 仅 12,392B；它与强度 scalar 回包是不同来源。本改动防止全 candidate 诊断在后续 plan/pending 表示中重复扩张，尚未据此测得完整 campaign 的运行收益。普通非 hire Native history 是否逐 action 附带同一诊断取决于真实 consumer，不能从计划返回体大小独自推断。

## 既有五个 timing 标量

`bridge.army_native_timing_summary_v1` 只保留结果已经具有的 `read_total_ns`、`owner_query_ns`、`baseline_read_ns`、`rich_attach_ns`、`serialize_ns`。缺失或不符合既有五字段合同的诊断被省略，业务结果保持不变。

该投影由共享 `army_strengths_mcp_result._army_strengths_summary()` 使用，覆盖普通强度查询、execute-step 和 AUTO 的紧凑 text/structured 返回。不新增查询、定时器、日志写入或 Native 协议字段。计时是包含关系，不能相加成总耗时；不能拿旧 query 的读数拆解另一次 AUTO。

## 验证

本机使用 `tools/.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider` 执行 CI 现有 war 组的六个文件：

- `test_war_reinforcement_tradeoff_v1.py`
- `test_war_spending_epoch_v2.py`
- `test_siege_research_hold_continuation_v1.py`
- `test_combat_profile_research_v1.py`
- `test_siege_research_continuation_v2.py`
- `test_army_strengths_mcp_result_serialization_performance.py`

结果为 **49 passed，35 subtests passed**，`git diff --check` 通过。CI war step 已包含同一文件列表。

新增覆盖通过真实生产函数链验证完整 584 项市场的购买/不购买分支、选择与 finance 字段等价、输入不变、当帧 guard、公司零的实际 submit 参数，以及紧凑 durable pending。直接 assessment 仍返回全池；选中对象未截断。紧凑 plan decision 小于 16KiB 且小于该合成全诊断的 1/20，这是一项测试表示大小断言，不是实机速度结论。

现有注册 MCP 序列化测试验证强度查询与 execute-step 保留五个计时，并补充注册 AUTO 的同一回归；内部完整结果未改变。SEM fallback 与私有 forecast 的分流未在本次跨面修改，继续单独处理。
