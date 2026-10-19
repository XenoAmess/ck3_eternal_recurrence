# 普通规划器的最近两个时间推进窗口

`machine_id: xenoamess-full-tower-eb9d2c1186`。观察时间由[小型资格回执](evidence/planner-battle-tail-lookup-2026-10-19.json)的 `observed_utc` 提供；证据来自固定 Git 源码、仓库 P18 已封失败投影和明确标注的合成历史。没有打开 Game、MCP、运行中 SDK 或 Driver 大正文。

`strategy._battle_control_turn_state` 原先枚举本进程 restore scope 内全部成功时间推进，然后只使用最后两个位置。现在从末尾找到这两个位置即停止。仍然调用原来的时间推进解析器，保留失败过滤、restore 边界、1-based 位置、同一批 pre/post query、sentinel 验证与后续战斗模型。没有修改战争意愿、候选、得分、原生评估次数或最终执行链。没有引入跨帧缓存，也没有删减历史。

固定基线为 `f5d26108b7fe26c0d27b1b1240850d2b62a1481e`。9 个离线场景的战斗状态和完整普通 chooser 结果逐值相等，输入均未修改，包括真实 P18 失败投影，以及合成的无推进、单推进、最近两个推进、失败新推进、auto-turn envelope、restore 和损坏 sentinel。资格生产器为 [verify_planner_battle_tail_lookup_v1.py](../../tools/g2_saved_campaign/verify_planner_battle_tail_lookup_v1.py)。

8857 行合成历史中，推进谓词调用 8857 → 4，单次战斗状态计算中位数 4.954 ms → 0.541 ms。无推进的完整扫描为 5.366 ms → 5.634 ms，略有回退。这是毫秒级局部优化，不能据此声称达到 1 秒/游戏日，也不能乘上未知的实机调用分布当作整局收益。

相关 battle 选择测试首轮 17 PASS、3 FAIL、2 subtests PASS。三项失败分别是既有调用夹具缺少 `driver`、缺少要求显式提供的 `CK3_PERSON_READONLY_HISTORY_PACKET`、旧 r0168 夹具预期 `active_combat` 而当前结果 `not_applicable`。在同一进程将唯一改动函数恢复为固定 Git 基线后，这三个测试仍逐项同样失败；没有为这些失败修改生产代码或放宽门禁。完整错误摘要保存在[验证补注](evidence/planner-battle-tail-lookup-validation-2026-10-19.json)。

更大的规划成本尚待实测拆分。旧 P49 小证据没有 `machine_id`，所属机器未核实；其 118 日窗口普通规划 union 为 29.275382 秒，内部 Native wait intersection 1.001551 秒、semantic snapshot intersection 2.611838 秒。它们互相嵌套，不能相加或把余量直接归因为 Python CPU。当前源码已经包含历史 root/faction 查找、过期 combat payload 拒绝及 construction 身份 pin 等先前优化，未重复实施。

为下一次合法源码冻结添加四层现有计时：`service.planner_capabilities`、`service.planner_history_rows`、`service.planner_choose`、`service.planner_public_plan_copy`。复用 `XAR_CK3_ARMY_TIMING_JSONL`；不启用 sink 时没有诊断 I/O，启用时只追加既有小型标量记录。没有新增快照、RPC、候选枚举或原生评估。这四层属于嵌套 wall interval，仍然不能相加或当成 CPU 时间。运行中的冻结业务源码未变。

一项新的真实普通 Service 软件对照复用保留的 Council DTO，验证开启/关闭 sink 时完整 plan 相等、原 snapshot/capabilities/chooser/root/final quote/submit/receipt 次数完全相同，四层新 stage 全部实际闭合且不输出正文。最终 1 PASS（1.49 秒）；最初缺少 `PYTHONPATH` 的收集错误仅补测试常规 src 引导，生产代码未为此改动。源码 pins、执行时间和精确断言见[小型回执](evidence/planner-stage-timing-qualification-2026-10-19.json)。没有从这个离线观察赋予实机吞吐信用。

本工作包仅新增小型源码与 JSON/文档，归通用存储策略 1.0.0 的研究共享限额；没有重型写入、清理或释放旧预留。回执按 `record` 的 4320 小时复核。
