# B3 manager 第四次 live RED 与 scripted-trigger 闭包 r5 候选（2026-09-04）

状态：**第四次 live 为 material-projection-trigger-closure RED；r5 为 GREEN_NO_LAUNCH / static-ready-live-pending。** 本文不把 preflight、schema 或测试冒充 live；新的实机 artifact 形成前，B3 仍未完成。

## 第四次 live RED

- artifact：`Z:\ck3_mod_rewrite_process_assets\zg361\b3f-1341251-20260904-070920Z\artifacts-live`
- 时长：317.408 秒；CK3 到达 Frontend，但未进入 Load Save/In Game
- outer `report.json` SHA-256：`55DF5DE1C6988C94E41358946F4DABADDA68A06B137A969668ADA30834098071`
- cell `report.json` SHA-256：`6C3A1EADAAA29DCA174E4B30B1DA911AC7DC34ADB6D189877F3A8B8993E8DF6E`
- `cell/final_error.log` SHA-256：`0B084D2B92B9673EBEEEF2AD1DB2CC3477E7AB8C0F083BF98B78011069D54B49`
- `cell/final_game.log` 为空，SHA-256：`E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`
- `evidence-index.json` SHA-256：`EF8C24429C874B0FF0E3E18E66E92457E6957FE5BE8CC3DD0DB0B79297DA96F7`
- cleanup：GREEN，`failed_checks=[]`；冻结 r5 前 CK3 进程数为 0。

`pdx_persistent_reader` 给出 6 条 concrete `Unknown trigger`：

- `zg361_p2c_m360_frozen_manager_exact_trigger` 三处，源行 86/102/118，外层定位 100/116/132。
- `zg361_p2c_m360_candidate_ready_trigger` 三处，源行 208/282/304，外层定位 213/287/309。

六处调用均位于 `common/scripted_effects/zg361_phase2_central_001_m360_source_effects.txt`，定义均在真实 production provider `common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt`。r4 已消除所有 Event-not-found，但仍有明确的 trigger provider 缺失，所以这仍是 material closure RED，不是 pure loader-performance RED；本轮不触发文件边界 A/B。

## 三态固定点修复

提交 `3d4dcb47dda4f61568842535eaed71bf6cf2e569` 将闭包节点扩展为 effect/event/scripted-trigger 三类：

- 解析 custom trigger 的定义、直接调用与 `*_TRIGGER = zg361_*_trigger` 参数实参。
- 从 B3 root 对 effect → event/trigger、event → effect/event/trigger、trigger → trigger 三类边递归求固定点。
- 对投影中所有已物化 effect/event/trigger 定义执行全 material unresolved gate，避免只检查本次走到的调用点。
- expander 只能从 exact canonical release 的真实 provider 复制完整文件，然后再次递归求闭包；不生成伪定义，不只补日志中的单个名字。

对旧 r4 product 的回归精确得到两个 reachable/material missing trigger，effect/event missing 均为 0。r5 固定点一轮加入完整 `zg361_phase2_central_runtime_triggers.txt`，其中包含两个 provider 及其递归下游；最终语义 reachable 为 1,868 effects / 560 events / 16 triggers，全物化投影为 3,698 effect definitions / 985 event definitions / 23 trigger definitions，三类 missing 与 duplicate provider 均为 0。闭包扩展证据 SHA-256：`C559E4EBCEEB88B7076AD16269BF20EC96E2B9F5ABB4941057FAD761105A3FE6`。

## r5 no-launch 候选

- canonical base：`fecd2f20b154b33c3c57ebc703564e21da5563da`
- exact source commit：`3d4dcb47dda4f61568842535eaed71bf6cf2e569`
- candidate：`Z:\ck3_mod_rewrite_process_assets\zg361\b3g-fecd2f2-20260904-073033Z`
- signed manifest：`phase2-b3-trigger-closure-no-launch-attempt-3d4dcb4-2026-09-04.json`
- manifest SHA-256：`DC2656A1238D0C67AF1A5755EE604A646649F65EAA9016400658D46E8A391967`
- projection：565 files / 21,607,125 bytes
- projection tree SHA-256：`50ECA1EF14D30C613F6A6E59CCD244BC3B92EE5A4AEDAF7BCCD191AF20B0475F`
- projection manifest SHA-256：`2052DADA087A91273A3B15587A34B00C861CCA543DBE14926026F3A2BA29B298`
- native source fingerprint：`590FAE6DE49B44F992DE48C4C4E16CFA2D1E3AF05E4A0C3EF1294B4F802FCC51`
- DLL SHA-256：`F3B7A6592F0EE75D2188844DD6FCA21BD9D7434513941EB6407C12ACB0B3ABA8`
- injector SHA-256：`3100800D06A99153CFCAB2AC8E183903C9B5246DAD0B8717B2772DB934EC13A2`
- fresh native tests：92/92 GREEN；ctest 日志 SHA-256 `6C07E4C761C1C4897F801D9FD5B0F7FC62344F3C6568976AD2562855FEA4A396`
- central normal/-O 38+38、manager normal/-O 49+49、freezer normal/-O 14+14、expander normal/-O 1+1：GREEN
- formal no-launch preflight：GREEN；日志 SHA-256 `1476F261B1C4CBE50F6A950D80AC67C8FFEEBCE6E0BF540216A50487EF92E3E7`

## 文件边界

r5 只新增一个 scripted-trigger 文件，没有新增或扩张 effect 文件。相对冻结 B2 r10 baseline，`delta_over_hard_max=[]`；B3 manager 保持 7 个用途分片 / 43 effects / 单文件最大 10。r4 已加入的 19 个 effect closure provider 也仍全部为 1–10 个 effect、最大 10；没有新例外。

唯一 live 命令已固化在签名 manifest 的 `launch.windows_command`。执行后必须用新的 paused/provider-observed artifact 判定 B3；此前保持 `static-ready-live-pending`。
