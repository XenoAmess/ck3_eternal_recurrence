# 实际四字段 writer 原始记录读取器（1.20.0.4）

consume_writer_actual.py 补上真实 probe 的离线读取入口。它只读原 JSONL、Root ADMISSION.actual.json 与其独立配对的 cash/before 完整回包，不 attach、不调用 SDK、不推进时间。生产位置为 [consume_writer_actual.py](../../ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/consume_writer_actual.py)；没有接入通用智能体 runtime。

~~~text
<verified-python> -B -O ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/consume_writer_actual.py
  --repo <CURRENT_INTEGRATED_REPO>
  --raw <ORIGINAL_writer.raw.ndjson>
  --admission <ORIGINAL_ADMISSION.actual.json>
  --cash-response <ORIGINAL_ADMISSION_CASH_ENVELOPE>
  --before-response <ITS_ORIGINAL_INDEPENDENT_BEFORE_ENVELOPE>
  --output <NEW_WRITERS_PROJECTION.json>
~~~

这是 argv 展示；参数用数组传递或合成一条实际命令，不使用 PowerShell 续行。输出拒绝覆盖。Root 在 probe 确实结束后运行，原 JSONL 与输入字节保持不变。

读取器复用同目录 cold consumer 的 OFFSETS/require/integer，以及现有 validate_current_raw_context_v1、payment.normalize_journal 和 exact .4 identity。cold consumer 的旧矩阵不会被调用。Root admission 的 actor/session/window/epoch、当前 raw 叶、原 source packet SHA 与 actual start 逐项绑定；离线异机读取用证据原 machine_id，不把读取机器当原采样机器。现金缓存只作 admission 输入，不变成 wallet callback。

输出供下一步来源定位直接使用：

- qualified_writers：真实模式中，具有已 arm 的线程生命周期、正确 DR slot/地址/对象、完整稳定读回的写入。保留 thread/event/slot、RIP_after/RVA、寄存器与原始行号。same-value 写入保留。
- unknown_traps：读失败、对象变化或 arm/readback 未闭合；失败 after 值输出 null，不把 native 的占位0当真实读值。
- finite_window_reason、terminal、cleanup_proved：分别报告 timeout/hit_limit_partial 等有限窗口和实际 restore/readback/continue/detach。缺 live restore 即使 terminal 布尔为 true 也不提升清理资格；writer 投影仍可保留为 partial。
- writer_instruction_start 始终 null，source_status 始终 unknown，actual writer game date/触发相位未观测则保持 null/unknown。没有自动把 RIP_after-1 补成指令起点，也不自动读取 EXE。

状态 ACTUAL_WRITERS_SOURCE_UNKNOWN 表示该组原文件保留了合格 writer-PC；NO_QUALIFIED_WRITER_IN_FINITE_WINDOW 仅表示有限区间没有合格记录。存在未知行、缺终态或清理未证明时带 PARTIAL_。返回0说明完成读取和投影，可能仍是 partial；返回2表示输入不适用/不匹配且不生成成功投影。旧 synthetic/cold 原始记录被明确拒绝，不能获得 CK3 credit。

这不证明已支付军事维护费。所有输出 known_producer=false、maintenance_attribution=unclosed；Root 随后按实际 post-PC 做有限 .pdata/函数解码，才可能定位指令与业务来源。当前缓存值与 native 入场初值分别保留，差异本身不导致拒绝；不把暂停态 setup 查询造成的写入冒称自然结算。

本轮仅四项新行为资格测试：四字段 writer/同值写 + clean timeout；零命中 clean timeout；未知 after + 缺 restore；cold 来源不得取得 actual credit。测试全部使用明确 synthetic contract 输入，**没有本次 CK3 writer 实机验收**。原始回执见 [资格回执](acceptance/2026-10-16-maintenance-writer-actual-reader/QUALIFICATION.actual.json)，[合同测试结果](acceptance/2026-10-16-maintenance-writer-actual-reader/RESULT.actual.json)，[原始输入与输出归档](acceptance/2026-10-16-maintenance-writer-actual-reader/synthetic-reader-originals.zip)。这些合成输入中用于覆盖 actual parser 的 synthetic=false 字段仅属于合同测试，不能单独作为实机证据。

普通 clone 在 cold/freshcash 两依赖已整合后可运行同目录 [test_writer_actual.py](../../ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/test_writer_actual.py)：

~~~text
<verified-python> -B -O ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004/test_writer_actual.py --main-repo . --output-root <NEW_SYNTHETIC_TEST_ROOT>
~~~

本机封存测试时主树仍冻结，显式使用 --sealed-root 与 --cash-candidate-root 指向已封候选，只覆盖测试进程中的可选 leaf import；实际 argv 与来源 SHA 原样在资格回执中。没有改主树、没有构建/运行项目 EXE，也没有重跑原 cold 矩阵。
