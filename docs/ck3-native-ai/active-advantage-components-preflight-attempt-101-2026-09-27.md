# 101：优势观测器兼容性预检 RED

101 原计划从 [099 第 12 日冻结存档](active-counter-output-day12-checkpoint-attempt-099-2026-09-27.md) 重放同一日界，以新 DLL 观测原生优势分项，并与 [100 反制输出](active-counter-output-cross-check-100-2026-09-27.md)对照。其候选 DLL 实际 SHA-256 为 `24D61CD42521A5B9457C56B7CF24F92E1A2B2CCB70D86DDDB5DC1ABE6C454835`，即本机重算的完整 **64 位**值。

受管启动器在**启动 CK3 之前**拒绝这份 DLL：`static-capability-strings.json` 显示 `experimental-combat-phase-event-trace-begin-v1=false`、`experimental-combat-phase-event-trace-finish-v1=false`；`capture.log` 记录 `Existing DLL lacks static strings`，并明确 `ck3_started_by_preflight=false`。后查明该外置 CMake build 目录将 `XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1` 留在默认 `OFF`，编译时裁掉了受管 begin/finish 分发。`cleanup-check.json` 的 `capture_returncode=1`、`cleanup_ok=false` 是预检 RED；没有游戏进程可清场，也没有任何第 13 日实机观测。Steam 离线视觉回执和全部预检素材保留在 `D:\workspace\ck3_native_war_ai_promo_work\episode01-active-advantage-components-attempt-101`，此 attempt 不覆盖、不改成 GREEN。

下一次试验须把优势只读观测器与已验证的受管 trace 能力编入**同一精确 DLL**，先跑相同静态 strings 预检，再从原始第 12 日存档建立全新 attempt。101 不可被引用为优势分项的实机验证。
