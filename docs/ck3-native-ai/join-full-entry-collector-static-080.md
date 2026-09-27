# 080 同帧 full-entry 私有采集器：静态实现合同

本文件记录 [join width 080 取样合同](join-width-production-and-fire.md) 的**采集器实现**，不是原生 join 规则的实机结论。历史 078/079 attempt 与三点战宽字段均保持原样；下一次受管实机必须使用新 attempt，不能把离线夹具提升为原生动态证据。

私有请求只有显式 `capture_runtime_join_width=true` 且 `capture_runtime_join_full_entries=true` 才启用。第二个字段缺省为 `false`，严格解析布尔；单独开启会被拒绝。采集器复用既有 `0x23040A0` wrapper 入口/正常返回钩子，先记录原有 079 战宽，再在**同一个实际 join 线程**只读复制 080 快照；第三个 side0 出伤宽度钩子不变。它不调用 `0x23CB840` 或其他 CK3 mutator，也不在钩内分配、排序、解析名称或解析组件存储。候选必须匹配 prearmed 完整 ArmyID 与 `CArmy*`，两次还须匹配 CombatID、原生日期和预登记对象。

可选 wire `runtime_join_full_entries` 的 `boundaries[0/1]` 是入口/返回。每条含两侧 `+0x98/+0xA0` 缓存、按原顺序的完整 ArmyID、两个 entry bucket 中按原顺序的完整 RegimentID/ArmyID/桶号/桶内序号、starting/current/soft/有效出伤/有效坚韧 Q100000，以及 incoming `CArmy+0x38` 的完整 RegimentID 顺序和逐条 `CRegiment+0x38` 基础人数。`entry_columns` 与 `incoming_columns` 固定 compact row 的列义；`joined_side_index` 在入口为 `-1`，仅在返回的 side roster 唯一确认后给出。`entry_current_sum_raw` 与 `cache_minus_entry_raw` 方便逐边界对账；非零残差**不会**被视为采集失败。

每侧最多 256 ArmyID、2048 entry，incoming 最多 2048 RegimentID。预登记对象失配、重复 ID、越界、容器结构错误和有符号求和溢出均使独立 `trace_capture_failure_join_full_entry` 置位、保存首个失败码；只有整条边界完整读完才发布 count，不截断成“完整”。原有 `runtime_join_width` 仍单独报告其三点、首个失败码和原始值。wire 的 900 KiB 上限仍生效；极大但有界的快照若超出该协议上限，序列化会整体拒绝，不能声称采集已交付。

离线夹具应覆盖默认 wire 不新增字段、二开关依赖、同线程同日入口/返回、加入侧延迟确认、陈旧缓存残差、incoming 基础人数、新旧完整 ID 比较以及重复 ID 的独立失败。所有离线测试只验证 collector 的内存 ABI 和闭合条件。真实 080/后续 attempt 仍需新鲜可读的 Steam 离线 UI、受管一步回放、原始返回 bytes/SHA、DLL SHA、配对回执和 clean exit；当前静态实现不满足这些实机门禁。

2026-09-27 静态构建：隔离 worktree `D:\wai`，新 Ninja/Release 目录 `D:\wai\ck3_autonomous_player\native_bridge\build-fresh-20260927T025104Z-572e2125`，私有 `XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1=ON`。rebase 到本轮最新 master 后，目标 `xar_ck3_bridge` 与 trace ring/detour/wire/managed/source-contract 可执行文件均重新编译链接成功；同源 DLL SHA-256 为 `1CC2AE965CD0EE897F918D50AF038F3DA874354DA7F3A57D2710B7BCCF44366F`。同源聚焦 CTest `-R combat_phase_event_trace` **5/5 GREEN**，包含新增同帧快照和重复 ID 拒绝夹具。最初尝试的全目标 `build_fresh.py` 在其他目标构建中停止，未取得其全套测试收据；本记录只声明上述目标与聚焦测试通过，不宣称全仓原生测试通过，也不宣称实机 GREEN。
