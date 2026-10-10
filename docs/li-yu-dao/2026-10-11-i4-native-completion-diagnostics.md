# 2026-10-11 原生 keyed query 完成拒绝诊断

[R53](2026-10-11-i4-r53-native-binding-refusal.md)在第28天返回 `pipe_completion_keyed_query_binding_changed`，原结果没有说明三个内部谓词中的哪一个失败。此变更为下一次共享运行补充失败证据；不放宽守卫、不重放失败查询，也不把历史 RED 改成通过。一期仍为 **75% / NOT_GREEN**。

原生守卫仍按原顺序只读取一次 completion Snapshot，然后短路比较 Snapshot 与 revision。拒绝先保存原 `available=false`、`frame_verified=false` 和原因，再以 `try/catch(...)` 尝试诊断；新增分配失败仅关闭诊断，不绕过原拒绝。

失败 DTO 的可选 `completion_diagnostics` 记录首个失败谓词、实际读取结果、expected/compared/post-guard revision，以及27个顶层 Snapshot 成员中变化的字段名。未执行的比较和 revision 为 null；没有读取成功时不解释部分 Snapshot。复合成员按实际完整相等比较，保存字段名，不输出整份 Snapshot。成功与其他旧失败的 wire 字节保持原样。

定向测试扩展现有 `xar_ck3_ingame_decision_outcome_contract_v1_test`，覆盖四条短路路径、27成员与嵌套集合、未知值、uint64及诊断捕获异常。serializer 测试使用完整函数投影，额外脚本在每次 CI 比较该投影与实际生产函数；这不代表已运行整个 worker 或新 DLL。已有测试保持，新增测试使用异常检查，Release 也不被 NDEBUG 静默关闭。

2026-10-11 03:18–03:20 CST，MSVC 19.51 实际配置、编译3份 TU 并链接该目标，随后原 EXE 运行 exit 0，新增测试与既有 outcome 检查均完成；生产 serializer 投影核对实际 exit 0。[12份小原件](acceptance/2026-10-11-i4-native-completion-diagnostics/INDEX.actual.json)共31,089 B。EXE 为104,960 B，SHA-256 `fc5d283351a6a08f1bf7eac1ad438aa2046658145c65b5af60861f7f88d934f9`。

构建 wrapper 原 exit 1 保留：[实际 build result](acceptance/2026-10-11-i4-native-completion-diagnostics/native-msvc-result.actual.json)明确 `build_succeeded=true`，失败来自管理员 token 下 WMI Add 返回“常规故障”。[精确路径登记回执](acceptance/2026-10-11-i4-native-completion-diagnostics/defender-settings-failed.actual.json)为 `settings_failed`，缺少实际生效读回；不能声称该新路径已完成永久排除。没有重跑编译、重复 Add 或撤销已有设置。

预约005限定128MiB，实际闭账后未来预约0；本次明确 build 与3个命令回执目录共17,421,872 B、1,792项 metadata，未做全仓扫描或PE/SAVE复制。缓存Oct17、配额Oct12原截止不变；新 build 按策略于Oct24复核，物理分配量和历史峰值未知。`open_kaishek` 为 not-applicable：本包检查 C++ DTO/序列化/异常行为，没有 CK3 script 子集。

并行[只读资格准备](acceptance/2026-10-11-i4-native-completion-diagnostics/common-native-readonly-REPORT.original.md)确认 MAIN 已有G2/G4真实provider与MCP注册，O11冻结注册仅含G3；下一份共同source须实际带入注册、已有native flags和host feature，并取得自己的metadata、build和实机资格。新的共享 DLL、完整生产 TU 编译与实机诊断尚未完成；本次定向测试不授予这些信用。
