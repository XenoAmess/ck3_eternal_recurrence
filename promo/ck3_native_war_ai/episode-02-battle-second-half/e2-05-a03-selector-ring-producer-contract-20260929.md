# E2-05 a03 selector ring：静态 ABI 与最小 producer 合同

2026-09-29，只读审查。此文是新 attempt 的准入设计，不是 a03 实机结果。未构建 DLL、启动 CK3、占用屏幕或读取录像。a02 的 DLL `EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7` 早于 2026-09-25 的 selector ring 提交 `ea795fbfc1f619bc49afb3c8e80bc3face1f14e3`；a02 的 `managed_trace.trace` 没有 `knight_selects` 键。这是能力缺口，不是记录到零次抽签。

## 当前源码明确提供什么

| 边界 | 精确源码位置 | 事实 |
| --- | --- | --- |
| 固定 ABI | `include/xar_bridge/combat_phase_event_trace_ring_v1.hpp:257` | 环容量 64；每行 `side_index`、`native_event_load_index`、`candidate_count`、`selected_index`、`selected_candidate_word0/word1`、`counter_before/salt_before`、`counter_after/salt_after`。行内没有日期、CombatID、受管 token、原始 draw 或全部候选 ID。 |
| exact-build hook | 同头文件 `:45`；`src/combat_phase_event_trace_detour_v1.cpp:22,339,578` | CK3 1.19.0.6、EXE SHA `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；selector RVA `0x33E8D40`，15 字节 prologue `4C89442418488954241048894C2408`。installer 核 prologue 且必须安装/恢复 hook。 |
| 作用域与读口 | `src/combat_phase_event_trace_ring_v1.cpp:2014,2116,2269` | phase-fire side TLS 与原生 event root load index 都非负、ring armed、指针非空才留行；root index 从预绑定 loaded-event 对象表取得，选择器在原函数调用前读 `candidates+0xC` 和 `context+0x28` 指向的 RNG counter/salt，原函数返回后记 index、RNG 后态以及被选中条目的两字。无效状态和越界触发 failure bit，64 行溢出触发 capacity bit。 |
| 序列化 | `src/combat_phase_event_trace_wire_v1.cpp:775` | wire 键为 `knight_selects`；两字输出为 `selected_candidate_word0_token` 和 `selected_candidate_word1_token`，类型是 process-local opaque token，不是已证 CharacterID。 |
| 整体 trace | `src/combat_phase_event_trace_ring_v1.cpp:1868`；`src/combat_phase_event_trace_wire_v1.cpp:802` | selector 行从同一 ring drain 输出；受管日 token、前后 checkpoint、CombatID 和逐边界日期必须由包围它的 begin/finish 与 records 另行验证。单行侧别+event index 不能单独证明是哪一日、哪场战斗或哪名骑士。 |

本次只读源码指纹如下，均为工作树中的 SHA-256；它们只是未来构建候选的**已读基线**，不是新 DLL 身份：

| 文件（相对 `ck3_autonomous_player/native_bridge/`） | SHA-256 |
| --- | --- |
| `include/xar_bridge/combat_phase_event_trace_ring_v1.hpp` | `93A904EA4639DCEFD120DF956ED3A3D7A5A840E3CF82E7A173B4E00F87C49557` |
| `src/combat_phase_event_trace_ring_v1.cpp` | `F7DA4F8BA4593B1F1838C43C11175B717365F428A9B77823D3E64C422F353EDC` |
| `src/combat_phase_event_trace_wire_v1.cpp` | `050D607EFF49B1D93AB28ED815886EE1909DED5CAFE7A6E6D1746CFB0EAD0490` |
| `src/combat_phase_event_trace_detour_v1.cpp` | `0D4E10970CE0577895F0C18C52631C181D8EB67BDBE7436C5187E9CFE4B0B0F6` |
| `src/combat_phase_event_trace_managed_v1.cpp` | `8E52CCD0C5D089B0F420FC55FD8809C25E6AF5D4E166234FBDB46A7AB38A88F8` |
| `CMakeLists.txt` | `3D68DECB845ED3697449DE0065E7B55DEFA4EEB2EDAA1376064CC5828160C040` |

## 新 producer 的最小封存与准入

1. 在隔离构建树冻结源码 commit、是否 dirty、上述文件及所有实际编译输入的 SHA、MSVC/CMake 版本与配置、编译命令、产出的 DLL 和 injector 路径/字节/SHA。EXE 必须仍是上述精确 1.19.0.6 SHA；独立复核 RVA `0x33E8D40` 的 15 字节 prologue 与调用约定。不能只凭 DLL 内出现字面 `knight_selects` 放行。保留旧 a02 二进制及回执原样；新 DLL SHA 应写入 **a03 专用** helper/config 的硬门，旧 `remaining_live_step.py` 对 EB6435 的固定绑定不可临时放宽。
2. 构建后运行至少四项已有 CTest：`xar_ck3_native_bridge_combat_phase_event_trace_ring_v1`、`xar_ck3_native_bridge_combat_phase_event_trace_detour_v1`、`xar_ck3_native_bridge_combat_phase_event_trace_wire_v1`、`xar_ck3_native_bridge_combat_phase_event_trace_managed_v1`，并保存完整 CTest 列表、退出码、stdout/stderr 和测试二进制 SHA。现有 wire 测试仅用合成 `{side=1,event=11,count=14,index=8}` 行检查序列化，**不证明 a03 会得 14/8**；ring 测试当前没有 selector hook 的直接候选数、RNG 和溢出负例。新 DLL 放行前补 selector 专项离线夹具：正常原函数返回、空/坏指针、count 0 或大于 65536、返回 index 越界、RNG 状态不可读、64 行溢出、错 side/effect scope、hook 安装失败和恢复失败均应有明确 fail-closed 结果。错误 EXE SHA/错误 prologue、旧 DLL 无字段、错 DLL/injector SHA 也须被 a03 no-launch gate 拒绝。
3. 只有新的受管 a03 run 可以产生新事实：精确冷载 d26 存档、冻结 EXE/DLL/injector 与新 run ID；同一暂停帧只读 WarID `4`、ArmyID `18`、CombatID `16777218`、省 `2633`、actor `29829` 和 d26 `date_raw=53146848`。在受管 begin 回执确认本 run 的 token、战斗 ID 与 selector hook 已安装后，仅允许唯一一次 d26→d27 受管日推进；保全 begin、one-day、finish、d27 paused snapshot 的精确 bytes/SHA。finish、managed checkpoint 前后和每条 boundary record 的 token/CombatID/日期必须相符。若新 run 没有重现相同战局或事件，停止该叙事，不以 a02 的事件补位。
4. 验收 `knight_selects` 时，要求新 run 自身的非空数组、无 selector/capacity/trampoline failure bit、唯一匹配的 side 1 与原版 `knight_killed` load index 11 root/select、`0 < candidate_count <= 65536`、`0 <= selected_index < candidate_count`；同一份 trace 的第 5→6 边界须有本 run 自己新增且目标相符的战报。若同侧同事件有多条 root 或 select，现有行没有逐条调用 ID，必须保持歧义 RED，不能按数组位置猜配对。要说出“抽到了角色 34120”或重算 raw draw，还须取 a03 自身 V3 候选源顺序、原版 event manifest 身份、选中 token 的独立 ABI 映射和 RNG 算法同源对拍；旧 020/070/036→038 的 `14/8`、候选名单和 token 映射一律不能移植。不得从一次战报反推候选集或 RNG 值。

当前静态源码允许设计新读数，尚无新 DLL SHA、专项 selector 负例或 a03 原生回执；因此本合同的 producer 状态为 **未准入**，选择器数值与死亡状态都保持 unknown。即使未来 selector 行完整，原有最后稳定查询的 `failure_flags=1040` 仍要独立修复，不能将局部选择器成功写成完整 production trace GREEN。
