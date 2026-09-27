# CK3 1.19.0.6 原调用优势分项：受管只读观测器（2026-09-27）

本诊断接续[来源链静态取证](active-combat-next-day-advantage-components-2026-09-27.md)，只适用于 `ck3.exe` SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。它捕获**游戏自己生成现役战斗缓存时**的分项返回值；不会在暂停帧主动重调将领、modifier 或 side helper，也不改变 RNG、战斗状态或原有 trace。此次只完成静态锚点、离线构建和合同测试，尚无本模块实机回执。

## 边界与线缆

私有 `experimental-combat-phase-event-trace-begin-v1` 请求可选 `capture_runtime_advantage_components: true`；缺省为 `false`。它沿用已有的恢复点、精确 build 准入、暂停主线程和「只推进一日」受管会话。Begin 在暂停静止点装四处 exact-byte 函数入口补丁：缓存生成 `0x2308D50`、side total `0x2307CB0`、将领 helper `0x2307680`、side 聚合 helper `0x2307230`。每处先验证原版入口完整字节，再保留原指令 trampoline；Finish 先卸载此观测器，再卸载其他可选 hook。补丁后发生无法证明安全恢复的错误时保留 trampoline 和 live-site 标记，受管命令触发 controlled stop，不能继续运行。

只针对目标 full-generation CombatID，缓存调用分配最多八条记录，并保存当前线程、当次 caller RVA、日期对象、base、resolved。仅在缓存调用的两次 side total 内收集：原版当前 roll、选中将领 full ID、`0x2307E88` 原调用的将领返回 qword、`0x2307EB5` 原调用的 side 聚合返回 qword、最终 side total。内层 hook 还要求原调用返回点分别为 `0x2308DB4/0x2308DCB`、`0x2307E8D`、`0x2307EBA`；不符合者继续原游戏调用，但拒绝本组证据。记录使用固定数组与 TLS 调用上下文，不分配游戏内对象；原调用和其参数保持原样。

Finish 的 `managed_trace.advantage_components` 只在显式开启时出现，`source` 固定为 `native_cache_0x2308d50_original_calls`。`available=true` 要求至少一条记录、每条恰好按 side0→side1 进入，两次 helper 返回完整，且所有 checked-int64 等式成立：

```text
side_total_raw = roll × 100000 + commander_raw + aggregator_raw
resolved_raw = base_raw + side0_total_raw − side1_total_raw
```

任一缺采、调用乱序、CombatID/日期对象代际变化、容量溢出、写回不一致或 hook 回滚不确定，诊断均不可用；Python `normalize_runtime_advantage_components_v1` 跨 JSON 边界再次验证原始整数、顺序和等式，并固定 `forecast_usable=false`。本项即使完整，也只是**已发生的缓存生成**，尚不能据此预测下一日非掷骰优势：人物 modifier、side 聚合、战场状态随日变更的来源叶子和转移仍需研究。现有胜率决策器不因此移除 `next_day_non_roll_advantage_sources` 缺口。

## 离线复核与下一次实机门槛

先用同 build EXE 执行 [`verify_advantage_observer_sites.py`](../../ck3_autonomous_player/native_bridge/research/verify_advantage_observer_sites.py) 的 `--exe <ck3.exe>` 检查 SHA、四处入口原指令及四个调用点；再执行 `extract_active_advantage_sources.py --exe <ck3.exe> --verify-components --expected ck3_autonomous_player/native_bridge/research/fixtures/active_advantage_component_sources_11906_v3.json`，复核 PE 函数边界及累加链。DLL 在 `ck3_autonomous_player/native_bridge/CMakeLists.txt` 构建；离线 C++ 门禁为 `xar_ck3_combat_phase_event_trace_managed_v1_test`，Python 门禁为 `ck3_autonomous_player/tests/unit/test_combat_advantage_components_contract.py`。进程内观测和补丁清场仍需按[受管 trace 合同](active-combat-next-day-advantage-sources-2026-09-27.md)另做 CK3 实机验收：记录一个普通日、事件日、增援日各自的缓存生产/消费调用点，核对 `available`、日期、两侧分项、原版最终缓存、DLL 完整卸载及 save/recoverable checkpoint。只有 live 结果匹配，才能称此诊断经过原版对拍；它仍非次日预测器。

**私有 DLL 构建必须显式配置** `-DXAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1=ON`；CMake 默认 OFF，即使上述 observer 源码被编译进 DLL，begin/finish 命令仍会被条件编译裁掉。101 的首次预检就因独立构建目录沿用 OFF 而在启动游戏前 RED。新 DLL 在交给实机前须运行 [`verify_private_combat_trace_dll.py`](../../ck3_autonomous_player/native_bridge/tools/verify_private_combat_trace_dll.py) 的 `--dll <xar_ck3_bridge.dll> --cmake-cache <CMakeCache.txt>`；它同时核验 cache 的 ON、DLL 中 begin/finish 命令、counter 与 advantage opt-in 字符串以及来源标识，并打印精确 DLL SHA。只有 `ready=true` 才允许进入实机预检。
