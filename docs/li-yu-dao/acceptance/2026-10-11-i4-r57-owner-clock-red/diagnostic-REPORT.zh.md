# R57 day0004 有界功能诊断

实际失败为 `/steps/9`，id=`case-natural-day-0004`：
`RuntimeError: campaign pause readback owner, clock or rejection state changed`。

原失败 row 只有 id/plan/started_at/ok/error/finished_at，没有 result、before/after 或 typed predicate/context。`plan.allow_event_boundary=true` 是准许参数；实际是否发生 event boundary 未保存，不能据此判为事件边界终止。ROOT 已知 day0003 date=53144736、完整自然24小时通过；day0003没有第二读。

冻结 Source15 `C:/csr15/ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py:1461` 先取得严格 current binding；1465–1467 的完整拒绝条件如下。本次每项实际布尔值均未落入失败row，保持 UNKNOWN：

| 失败谓词（原 OR） | 本次实际值 |
| --- | --- |
| not identity_matches | UNKNOWN |
| current.rejections != source.rejections | UNKNOWN |
| current.date < source.date | UNKNOWN |
| current.revision < source.revision | UNKNOWN |
| current.native_revision < source.native_revision | UNKNOWN |
| current.pump < source.pump | UNKNOWN |

该异常说明至少一个拒绝条件成立，不说明具体哪个成立。此 raise 未附新诊断属性；preflight(1931)及postpause(1780)均调用它，本次实际调用点未保全在本投影中，不能推断已提交速度/恢复/推进或本日完成。

`native played_character stress_points is malformed` 在 `/steps/8/result/before/diagnostics/last_rejected_state_snapshot/error`、对应running_successor/after及最终diagnostics均出现。拒帧历史字符串本身不能证明day0004有新增拒帧。1935–1952的预动作readmission仅允许initial.rejections=0、observed.rejections=1等完整条件；连续新日继承非0计数可能不适用是源码假设，本次没有保全1→2实际值，不作因果结论或放宽guard。

最小后继接点：保持1465原OR/时点/error不变，拒绝后保存六项精确谓词、source/current核心binding和调用点，让外层失败row落盘。当前只有诊断建议，没有MAIN/source修复、测试、native构建、SDK/游戏动作或业务信用。

读取事实：第一次投影过宽导致cap失败，exec39bd5a/exit1，原combined tool output及源码pins保留；原工具未分别采集stdout/stderr，字段明确NULL。ROOT明确授权一次纠正读取，exec3463dc/exit0。第二次只读同终态965315B report一次；没有第三读，没有第二次读day0003。

READ.actual.json记录第二读实际SHA、FileID、mtime及读前后稳定性。该字节来源是ROOT已报告host wait1/publicrun2终态的原件；不授GUI正常退出。EXTRACT是JSON值投影，指针指向该原件，不冒充raw lexical slice。

同一第二读raw缓冲已调用原project_native_cleanup.project，原report没有重开；生成native-cleanup-projection.actual.json(≤8KiB)，ROOT可复制到RUN供行政闭场。此清理投影与功能诊断相互独立，不把host/native清理改写成GUI或自然日成功。
