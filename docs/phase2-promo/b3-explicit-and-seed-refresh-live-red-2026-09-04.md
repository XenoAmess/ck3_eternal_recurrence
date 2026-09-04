# B3 explicit-AND seed refresh：首用变量 RED 取证（2026-09-04）

状态：**正式失败证据 / product runtime RED / seed 未生成 / T0 不加分。** 本文承接
[`b3-explicit-and-seed-refresh-no-launch-2026-09-04.md`](b3-explicit-and-seed-refresh-no-launch-2026-09-04.md)
冻结的唯一实机命令，只记录该命令执行后的事实。本轮没有修改产品或启动第二轮 CK3。

## 结论

本轮不是 Frontend、loader performance、长路径或 effect 单文件体量 RED。Frontend-first 预热已通过认证窗口回退门，
最终进程也完成 `load_save`、native binding 和暂停地图 readiness。外层最终 RED 的直接原因是 seed fixture 首次结果链在
同一秒触发 **93 条 ZhongGuo `parser_or_script` 签名**。

93 条不是 93 个独立缺陷，而是 **31 个未初始化变量读取点各产生一组三联错误**：

- `Failed to fetch variable ... due to not being set`：31 条；
- `Event target link 'var' returned an unset scope`：31 条；
- `Invalid left side during comparison 'var'`：31 条。

本轮实际挂载的 explicit-AND product 是从冻结的 r5 诊断树复制后仅替换 trigger provider 的外部产品；它仍携带
`05e1410bf21b6efdab1492a5919c76a047f2934f` 之前的 B2 首用字节。四个命中文件都直接读取未设置的 `var:`，没有
`has_variable` 门。因此本轮直接原因是 **冻结产品基线陈旧，已经做过的 B2 首用改动没有进入实际 materialized
product**，不是 clean source commit、文件数或路径能够代替的产品新鲜度证明。

同时，不能把下一步简化为“把当前 `05e1410` 文件复制进去”。当前 generator 的 `05e1410` 形态是在同一个 trigger
容器中并列 `has_variable` 与 `var:`，而
[`docs/grammar/pitfalls.md`](../grammar/pitfalls.md) 已由 CK3 1.19.0.6 r8/r9 实证同级条件不提供 lazy
短路。这个实证不由本轮重新证明——本轮根本没有挂载 `05e1410` 字节——但它足以说明重物化前应先把 current
generator 升级为外层 `trigger_if` 或等价 lazy 分支，再生成完整 cumulative product。不得为验证一个已知不可靠的
同级门再浪费一次 CK3 串行槽。

## 93 条的精确聚合

全部 93 条都在 `19:08:09` 产生，scanner category 均为 `parser_or_script`；引擎原文是运行时
`Script system error!`，不是文件 parse 失败。调用链来自 acceptance-only seed fixture：
`zga_phase2_seed_bootstrap_bridge_gui` → `zga_phase2_seed_maybe_begin_effect` → `zga_phase2_seed.100/.101/.102` →
`zg361_b2_on_result_frozen_effect`。

| 文件 | effect | 原始读取点 | 读取变量 | 三联错误数 |
|---|---|---:|---|---:|
| `zg361_b2_debt_consumers_effects.txt` | `zg361_b2_consume_due_policy_debts_effect` | 19 | `m014`、`m015`、`m016`、`m017`、`m069`–`m081`、`m358`、`m359` 的 `*_policy_debt_active` | 57 |
| `zg361_b2_069_delivery_effects.txt` | `zg361_b2_m069_open_business_object_effect` | 1 | `zg361_b2_m069_object_active` | 3 |
| 同上 | `zg361_b2_on_result_frozen_effect` | 9 | `m079_remand_active` 1 次、`m080_state` 2 次、`m015/m016/m017_object_active` 各 1 次、`b2_pip_state` 3 次 | 27 |
| `zg361_b2_072_access_audit_effects.txt` | `zg361_b2_m072_open_business_object_effect` | 1 | `zg361_b2_m072_object_active` | 3 |
| `zg361_b2_081_projection_access_effects.txt` | `zg361_b2_m081_open_business_object_effect` | 1 | `zg361_b2_m081_object_active` | 3 |

共有 28 个不同变量；`zg361_b2_pip_state` 被读取 3 次，`zg361_b2_m080_state` 被读取 2 次，其余 26 个各 1 次。
28 个变量的精确全集为：

- policy debt（各 1 次）：`zg361_b2_m014_policy_debt_active`、`zg361_b2_m015_policy_debt_active`、
  `zg361_b2_m016_policy_debt_active`、`zg361_b2_m017_policy_debt_active`、`zg361_b2_m069_policy_debt_active`、
  `zg361_b2_m070_policy_debt_active`、`zg361_b2_m071_policy_debt_active`、`zg361_b2_m072_policy_debt_active`、
  `zg361_b2_m073_policy_debt_active`、`zg361_b2_m074_policy_debt_active`、`zg361_b2_m075_policy_debt_active`、
  `zg361_b2_m076_policy_debt_active`、`zg361_b2_m077_policy_debt_active`、`zg361_b2_m078_policy_debt_active`、
  `zg361_b2_m079_policy_debt_active`、`zg361_b2_m080_policy_debt_active`、`zg361_b2_m081_policy_debt_active`、
  `zg361_b2_m358_policy_debt_active`、`zg361_b2_m359_policy_debt_active`；
- object/remand（各 1 次）：`zg361_b2_m015_object_active`、`zg361_b2_m016_object_active`、
  `zg361_b2_m017_object_active`、`zg361_b2_m069_object_active`、`zg361_b2_m072_object_active`、
  `zg361_b2_m081_object_active`、`zg361_b2_m079_remand_active`；
- repeated state：`zg361_b2_m080_state` 2 次，`zg361_b2_pip_state` 3 次。

对应精确行号如下：

- debt consumer：`71, 85, 99, 113, 127, 141, 155, 169, 183, 197, 211, 225, 239, 253, 267, 281, 295, 309, 323`；
- delivery：`47, 123, 137, 138, 192, 193, 194, 197, 198, 199`；
- access audit：`47`；projection access：`47`。

文件维度总计为 `57 + 30 + 3 + 3 = 93`；effect 维度总计为
`57 + 27 + 3 + 3 + 3 = 93`。`02_loader_error_scan.json` 的 `matches` 数组逐条复算与这两个总和一致。

## 启动、路径和 readiness

- 外层 relay 为 `RED`，child exit `2`；它只反映 seed runner 拒绝 93 条项目错误，不能改写内部已通过阶段。
- Frontend-first warm-up PID `60080` 于 `2026-09-04T11:05:17.007652Z` 启动，`109.396s` 后通过
  `history_end=true + frontend_gui_complete=true + authenticated_responsive_frontend` 回退门；
  `status=ready`，warm-up cleanup `ok=true`。该门明确记录 `idler_marker=false / fallback=true`，因此不虚构直接
  `Setting idler 'Frontend'` 日志命中。
- final PID `9240` 于 `11:07:11.448447Z` 启动并加载同一 `phase2_seed`；loader stage 为
  `GREEN / load_save`，完成 303 个 database nodes，fatal error `0`。
- native readiness 为 GREEN，连续 3 次稳定观测：`connection_generation=1`、`date_raw=53146920`、
  `local_player_id=1`、`paused=true`、`map_ready=true`。
- 实际 product mount 有 565 个文件，最长完整路径 **154** 字符；fixture 最长 110；整个 attempt 最长仍为 154。
  日志没有 PhysFS `over 250` / path-too-long 签名。因此不触发 effect 拆分 A/B，也不能把这轮归因于单文件体量。

## 产品新鲜度与不可变性

runner 的 clean source 固定在 `9cd921674e192a118ea27c376fd41dfbb4bab327`，但 `--product-source` 是独立的外部冻结树。
`source_commit`/source ZIP 一致不能证明该外部产品已包含该 commit 的所有生成结果。

- 外部 product source 为
  `Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\product-source`；
  attempt/artifact/relay root 分别为 `Z:\p2s10`、`Z:\p2s10a`、`Z:\p2s10f`。
- 实际 product：565 files / 21,607,199 bytes，tree
  `D94C2D5D23E9AD254F4B20988FBF3C8E08408BAA61070BD85F42B2D2FCBEA35D`；projection manifest
  `241DB7B5E2DF451AADBFAEB4570B083C8563239BC0158530682B9A77DA2F4ACD`。
- 四个命中文件的实际 SHA-256 分别为
  `7135782C...B6CA`、`78BD461B...016E8F`、`68A49B0A...C075`、`899CA8DE...37FB`；这些值可在
  历史 pre-`05e1410` r9/r1 projection 中找到。实际文件在上述 31 个读取点均缺少首用 lazy 门。
- 与当前 canonical 同路径逐文件只读对照为 `515 same / 46 different / 4 candidate-only`；其中全部 20 个 B2
  first-use 生成文件都不同。这个总量用于证明“产品并非当前 cumulative tree”，不声称其余每个 delta 都是缺陷。
- clean source manifest before/after 均为 2,735 files、tree
  `C5B2708FCF6A12C9C8BAC71F6F5998069D17C61931E64668D8EB3CD2018F3477`，两份 manifest 文件也逐字节同为
  `1CB1E5756C37ACE80AA0D5C9280AD724522A1DE1BEC139F39FC6827F051FBD63`。
- runtime product/fixture before/after 保持
  `D94C2D5D...A35D / 64B8C4B0...3D35`；`runtime_unchanged=true`、`clean_source_unchanged=true`。
- source ZIP、旧 save、CK3 EXE、原版 rules、bridge DLL、injector 和 projection manifest 的 before/after
  SHA 全部一致，`external_dependencies.unchanged=true`。
- 输入 `phase2_seed` 是旧 checkpoint 的逐字节副本，53,517,622 bytes、SHA-256
  `BFC73FD9E7E80145CDF39AABC66BC2D731881122ADAB0CC0BA675FA07D1E6733`。

## 清理与核心 artifact

warm-up PID `60080` 和 final PID `9240` 都由 job 清理到 `tree_gone=true / job_active_processes_final=0`；watchdog
消失、control files 清空、contract errors 为空。`09_phase2_native_session_cleanup.json` 为 GREEN，审计时再次读取系统进程
清单为 CK3 `0`。这是真实 cleanup GREEN；不改变 seed/capture RED，也没有新 candidate/checkpoint 可供后续复用。
具体地，`Z:\p2s10\candidate\zg361_phase2_seed_contract.candidate.json` 不存在。

| artifact | bytes | SHA-256 |
|---|---:|---|
| `Z:\p2s10f\default-desktop-live.json` | 2,824 | `2D96AE47C431F95A1E38D2DC4F2FCEAF279CF8B840EA96E4EAE84F8D7E6CDCAC` |
| `Z:\p2s10a\runner-report.json` | 368,799 | `77E4927BB84F304245CF2987125E30D5B55D5E3CB29D87BAB558CFB702D51BCB` |
| `Z:\p2s10a\01_loader_native_readiness.json` | 35,877 | `5D5CC41159E76AECB283FEB37500ED0C43D71835558C3906CD030A6505767977` |
| `Z:\p2s10a\01_phase2_loader_stage_progress.jsonl` | 383,739 | `3A3DF4DC81D1EBBBA99875E51C928B8B400D5660F457EEE8AF920B6702442A8D` |
| `Z:\p2s10a\02_loader_error_scan.json` | 59,598 | `7958C5A40C8721195A67BABE46F1AC92D24E1BECA1878DF868BA57B6AF4EFF5B` |
| `Z:\p2s10a\02_loader_error.log` | 3,737,679 | `377B7B5DB1C1CCA169209212872BB7ED0D683EAFE72878DA9A35F727E791CA87` |
| `Z:\p2s10a\09_phase2_native_session_cleanup.json` | 27,001 | `55284995C4636A292885778B5C4C1D6736D8A4CF422764C928F436C4DC8C42C5` |
| `Z:\p2s10a\source-tree-manifest.before.json` | 588,267 | `1CB1E5756C37ACE80AA0D5C9280AD724522A1DE1BEC139F39FC6827F051FBD63` |
| `Z:\p2s10a\source-tree-manifest.after.json` | 588,267 | `1CB1E5756C37ACE80AA0D5C9280AD724522A1DE1BEC139F39FC6827F051FBD63` |
| `Z:\p2s10a\ck3-logs\debug.log` | 441,235 | `AF516D90DA6E6627FFA4FD735DF87CF6E53203351422087E510039498E55E795` |
| `Z:\p2s10f\live.stdout.log` | 369,043 | `D78C33C02EDB6F9CC9E84BD2FE800C603BBCC92E979E406E3802EC7291BB3784` |
| `Z:\p2s10f\live.stderr.log` | 0 | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |

## 下一轮准入

1. 先在 `tools/gen_361_b2_runtime.py` 中把 20 个 B2 首用门改成真正的外层 lazy 分支，并运行生成器与对应 L0；不要手改
   `GENERATED FILE`。
2. 从该 current canonical 输出重新构造 cumulative B3 product；explicit-AND 只允许作为 trigger provider 的受控 delta，不能
   再以旧 r5 整树作为未审计基底。
3. no-launch freeze 除 tree/projection hash 外，至少核对 B2 20 个 first-use providers 与当前生成输出一致，并证明
   31 个已知读取点不再存在无 lazy 外层门的 `var:` 访问。
4. 上述门全部 GREEN 后，才分配下一次 CK3 串行 seed refresh；仍只刷新 seed，不外推 promotion source、B3 gameplay、
   8/8 footage、双 MP4 或 T0 完成。
