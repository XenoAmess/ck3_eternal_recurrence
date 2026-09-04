# B3 seed refresh：三轮 product runtime RED 取证（2026-09-04）

状态：**三轮正式失败证据 / product runtime RED / seed 未生成 / T0 不加分。** 本文承接
[`b3-explicit-and-seed-refresh-no-launch-2026-09-04.md`](b3-explicit-and-seed-refresh-no-launch-2026-09-04.md)
冻结的第一轮实机命令，并依次记录 `Z:\p2s10a`、`Z:\p2m\a` 与 `Z:\p2o\a` 的事实。本文只审计既有 artifact，没有修改产品或
再次启动 CK3。

## 第一轮结论

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

## 第二轮 current-byte / old-inventory RED（`Z:\p2m\a`）

第二轮把 clean source 固定到 `ae55180a1fd5933d1725a30d9b56083be0f77383`，并从该 checkout 重新复制旧 565 路径清单内的
全部 product 字节。它给出了两个必须同时保留的结论：

1. 第一轮的 93 条 B2 首用错误已经**完全清零**，说明真正的外层 lazy 改动已进入本轮 product 并解决了该故障；
2. 本轮仍为 `RED`，唯一项目签名是 `zg361p2c.7` missing。原因是 materializer 沿用旧 565-file inventory，漏掉了 current
   canonical 已有、B4 Route-B WAIT360411 新链路需要的 event shard。它是 inventory closure RED，**不是文件体量或加载性能 RED**。

### 唯一 loader 签名与旧 93 条归零

`02_loader_error_scan.json` 只有 1 个 match，category 为 scanner 的宽类 `parser_or_script`：

```text
[19:38:15][E][jomini_script_system.cpp:303]: Script system error!
  Error: trigger_event effect [ Event [zg361p2c.7] not found ]
  Script location: file: common/scripted_effects/zg361_phase2_central_009_stage11_workforce_endgame_effects.txt line: 45 (zg361_p2c_schedule_m360_resume_effect)
```

这是缺失 event provider，不是脚本 parse 失败。对完整 `02_loader_error.log` 复算，第一轮三种错误原文和代表变量的计数均为零：

| pattern | 第二轮计数 |
|---|---:|
| `Failed to fetch variable` | 0 |
| `Event target link 'var' returned an unset scope` | 0 |
| `Invalid left side during comparison 'var'` | 0 |
| `zg361_b2_m014_policy_debt_active` | 0 |
| `zg361_b2_pip_state` | 0 |

因此不能把第二轮的“1 条”与第一轮 93 条合并成同一种故障，也不能因总体仍 RED 而否认 B2 lazy 修复已被实机验证。

### inventory 缺口的逐路径证明

- `Z:\p2m\product-materialization.json` 明载 product 是 565 files / 28,210,018 bytes，其中 561 个路径从 current canonical
  复制、4 个 core 路径走同一 clean checkout fallback；但它的 inventory basis 仍是旧 manifest
  `241DB7B5E2DF451AADBFAEB4570B083C8563239BC0158530682B9A77DA2F4ACD`。
- `Z:\p2m\p.json` 的 565 个 `files[].path` 不含
  `events/zg361_phase2_central_003_m360_resume_events.txt`，`Z:\p2m\p` 内该文件也不存在。
- 同一路径在 clean source `Z:\p2m\w\mod_zhongguo_style` 中存在：7,947 bytes，SHA-256
  `A67714B8A0929BA910E8B7668811E022A2A9C7EF82EA49FA428B673F7E39822C`，并定义缺失的 `zg361p2c.7`。
- product 同时包含调用者 `zg361_phase2_central_009_stage11_workforce_endgame_effects.txt`。debug log 也只加载 central
  event shards `001` 与 `002`，没有 `003`，与逐路径差集一致。

换言之，本轮实现的是“旧 inventory 中各路径换成 current bytes”，而不是“从 current canonical 重新计算完整 inventory”。
**字节新鲜度和路径集合新鲜度是两个独立门**：前者 GREEN 不能推出后者 GREEN。下一轮不能只重抄旧 565 清单；必须由
current seed/B4 reachable closure 重新生成 inventory，并对新增与删除路径做集合差分。

### B2 三方字节门与实际 marker

`critical-b2-product-byte-equivalence.json` 为 GREEN，`mismatches=[]`；下列四个文件在 clean source、external product source、
实际 mounted product 三方逐字节一致：

| path | bytes | SHA-256 |
|---|---:|---|
| `common/scripted_effects/zg361_b2_debt_consumers_effects.txt` | 17,369 | `48C6213F45D11B4FD7AD6B5B41FD5DF64205A81D324143B7F03BB39948D639BF` |
| `common/scripted_effects/zg361_b2_069_delivery_effects.txt` | 15,514 | `05641DADB150E5083C7509AF9988CB9966C5048F4A80DAE5A66F66C8DE7ED4FA` |
| `common/scripted_effects/zg361_b2_072_access_audit_effects.txt` | 6,860 | `4C6123E7921ADCFCFFB786E8D73A1DB59FE02F0F36F818C4566281C01BC1CF2A` |
| `common/scripted_effects/zg361_b2_081_projection_access_effects.txt` | 5,598 | `6C477FE7467AB64D818A282DCA178BF2EB237D35BBB00BD74E69AB514CBE54D1` |

实机随后写出 `ZGAP2SEED: load-safe bootstrap activation`、`ZG361B2: result-bound justice case prepared` 和
`ZGAP2SEED: waiting for witnessed delivery before B2 checkpoint`。这与旧 93 条归零互证：B2 首用链已经越过上一轮失败点；
但 loader scan 的唯一 missing-event 签名仍使 runner 正确拒绝产出 candidate。

### Frontend、native、路径和 cleanup

- Frontend-first warm-up PID `30752` 使用直接 `idler-marker` 模式；47.379 秒、934 polls 后命中
  `Setting idler 'Frontend'`，`idler_marker=true / frontend_gui_complete=true / fallback_ready=false`。warm-up cleanup
  `ok=true / tree_gone=true / job_active_processes_final=0`。
- final PID `68700` 于 `2026-09-04T11:37:28.346822Z` 启动；loader stage 为
  `GREEN / load_save / 303 database nodes / fatal_error_count=0`。missing event 出现在 `19:38:15`，而 Frontend idler 于
  `19:38:17` 出现，故该缺口没有伪装成 Frontend 性能失败。
- native readiness 为 GREEN；连续 3 个稳定样本均绑定 PID `68700`、`connection_generation=1`、
  `date_raw=53146920`、`local_player_id=1`、`paused=true`、`map_ready=true`。
- product 最长预期 mount path 为 154 字符，小于 250；完整 error log 中 `over 250`、`path too long` 与 `PhysFS` 均为 0。
  本轮没有触发 effect 拆分 A/B，也没有产生“单文件过大导致 RED”的新证据。
- cleanup artifact 为 GREEN，final PID 的 `tree_gone=true / job_active_processes_final=0`，watchdog 消失，control files 全部
  absent，contract errors 为空；审计时 CK3 进程数为 0。
- `Z:\p2m\r\candidate`、candidate seed contract 与新 `xar_checkpoint.ck3` 均不存在；原始只读输入
  `phase2_seed.ck3` 仍存在。故本轮**没有生成 seed，不给 T0/B3/B4 readiness 加分**。

### 来源、产品与不可变性

- clean source：2,748 files，tree
  `DBC79E041736D838ADC8E746612EB7E21794324F764DAEC3013468B977740141`；before/after manifest 均为 591,160 bytes、
  SHA-256 `1290BE611E486107E2C49AA3324C0FCAB9EB48AF92450C63C28EFE3B7CC68665`，runner 的
  `clean_source_unchanged=true`。
- source ZIP：83,801,744 bytes，SHA-256
  `5AE78C3138CFDA0F892046BB2AEB35F74102F268B7348FC73F57EBBEB1D0B5AD`；logical tree
  `8C0FE4CD8DC7C29B00B42C9B1E66721950556CC579A8333ED765BA576B346FBC`，与 clean source 等价。
- product：565 files / 28,210,018 bytes；source/mounted tree
  `A140B7CA9BC8DFF1476A3430FF5F57F97C21272AD990B75C776D3738683D9955`，formal overlay
  `0F928843F2976DEE81333CAC1041A9E6F29FDD4ED3F276589DF90D60298F4C1A`，file list
  `B91532AAA73B3DED3B1302D9DD343581C7EE2723F0BEFE003B5D709F3ADBF04E`；`runtime_unchanged=true`。
- source ZIP、旧 seed、CK3 EXE、原版 rules、bridge DLL、injector 与 product manifest 的 before/after SHA 全部一致，
  `external_dependencies.unchanged=true`。
- live 结束后的第一轮只读审计在 clean source 观察到 `__pycache__=0 / *.pyc=0`。随后另一个并发的非 live 工作在
  `11:43:06Z`（晚于 runner `11:38:35Z` 收口）才写入 ignored bytecode；它不在 before/after artifact 窗口内，不能归因于本轮
  外层命令。能力证据仍以 runner 的相同 before/after tree、external immutability gate 和该即时零计数为准。

### 外层执行与冻结命令的两处偏差

冻结的 `AUTHORIZED-LIVE-COMMAND.txt` SHA-256 为
`D15E02A0B2133007283C99AEE2EA116D17AAE4DDE038330345FAC9BCF793F6CF`。实际外层执行并非逐字节复现它：

1. wrapper interpreter 漏了 `-B`；
2. outer result 从授权名 `Z:\p2m\f\relay-live.json` 改为
   `Z:\p2m\f\default-desktop-live.json`，前者不存在，后者存在。

这两处都必须记为 **execution/provenance conformance 偏差**。但实际 sidecar 记录的 child runner、工作目录和全部 child argv
与授权内容一致；漏 `-B` 没有在 live artifact 窗口内写入 clean source bytecode，result 文件名也不改变 child CK3 run、product
mount、loader/native/marker/cleanup 或其哈希。因此它们不推翻上述能力证据，但冻结命令不能声称被逐字节执行。下轮应直接复制
冻结命令，恢复 `-B` 与授权 sidecar 名称，消除此类审计噪声。

### 第二轮核心 artifact

| artifact | bytes | SHA-256 |
|---|---:|---|
| `Z:\p2m\f\default-desktop-live.json` | 2,629 | `970E19218CB52E94334EF5EC3D93FD72E5256DCB3E39734225682000C461644F` |
| `Z:\p2m\f\live.stdout.log` | 372,291 | `595A46FA07E4C86207550ACF715D75ADE753A2FC4168C4D31561E4B7AE5E6EA1` |
| `Z:\p2m\f\live.stderr.log` | 0 | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |
| `Z:\p2m\a\runner-report.json` | 372,047 | `C7942D9E3C5992B17A0B1DB1A6CEA07A07CD731855135EF9FCA057306AA6E0B8` |
| `Z:\p2m\a\01_loader_native_readiness.json` | 35,892 | `B6E2A834C6487CFB7822C66917D013FA456ED69F179A0BE22E87716642E29756` |
| `Z:\p2m\a\01_phase2_loader_stage_progress.jsonl` | 291,923 | `73318A51A7611D2FE72EAB7A513DEEEE29EA072B9447FF1800F7A1AD5CC21ED4` |
| `Z:\p2m\a\02_loader_error_scan.json` | 2,718 | `E780CA11F2BC062A8B42AB15C69EB12E8419717B65183AADFBFB6ADBE42178FA` |
| `Z:\p2m\a\02_loader_error.log` | 3,630,670 | `06C6BDEE8FCE8EB894B62373290F6D2FB0C88D3DA39170C545BFFFCD8A50C673` |
| `Z:\p2m\a\critical-b2-product-byte-equivalence.json` | 5,068 | `F817C62CC96892DAB04A5531683A21B67BFA09CDBB52B542DDE39854087BCDEB` |
| `Z:\p2m\a\09_phase2_native_session_cleanup.json` | 25,757 | `88B1D22FCEDF898DDDB980D3799032C123595EE4D83AA9192540F33AF1D9AFB7` |
| `Z:\p2m\a\ck3-logs\debug.log` | 354,604 | `5076D82D349BB09FCB42A6AC001ECB1C85D11DBBFCA6484DE54ABF41009719EB` |
| `Z:\p2m\a\source-tree-manifest.before.json` | 591,160 | `1290BE611E486107E2C49AA3324C0FCAB9EB48AF92450C63C28EFE3B7CC68665` |
| `Z:\p2m\a\source-tree-manifest.after.json` | 591,160 | `1290BE611E486107E2C49AA3324C0FCAB9EB48AF92450C63C28EFE3B7CC68665` |
| `Z:\p2m\freeze-manifest.json` | 5,257 | `FD97A71FD54B59B13725EA2187F7B96140050A772B6600F4D6F4D41775CD65AF` |
| `Z:\p2m\product-materialization.json` | 928 | `B9F437E1BBCAC92A8A401947C74AA3ACBE79AF5C354D25E2AF46C6AE030195CB` |
| `Z:\p2m\p.json` | 120,372 | `7A456704A55E5326BFBCEE9DF58C1DD5C08B5155E461C1F57B3DE73D064BC590` |

## 第三轮 fresh-closure / vanilla-event RED（`Z:\p2o\a`）

第三轮使用同一 frozen commit `ae55180a1fd5933d1725a30d9b56083be0f77383`，但不再只更新旧 565 条路径的字节。
`closure-expansion.json` 从 product 真实缺口重新做一轮 closure：补入
`events/zg361_phase2_central_003_m360_resume_events.txt`，并补入 promotion PIP 所需的 9 个语言文件。相对第二轮路径集合为
`10 new / 0 removed`，最终得到 **575 files / 28,438,735 bytes** 的 fresh product。

### 前两轮 material RED 已关闭

- callable closure 初始唯一 missing event 为 `zg361p2c.7`；加入 7,947-byte provider shard 后，最终
  `missing_effects=[] / missing_events=[] / missing_triggers=[]`，material definitions 为
  `3,703 effects / 986 events / 24 triggers`。closure report 为 GREEN，SHA-256
  `9F7B7E226B8D764724D930F43160524449240E0489B11298ABC80AF3FDC3BA1C`。
- localization closure 补入 English、简体中文与七个日常开发占位语言文件；English/简中为 authored，另外七语保持
  English placeholder，符合非发布阶段策略，不冒充完整翻译。
- `p.json` 明载 575 paths，source/mounted product tree 均为
  `361F4785BD626A42AE558F49DB32B79EED69247A0C4CEEF775C8390FADBB93EA`；formal overlay
  `B08ECBBE32E0742EC6CA32A263993CF761C73CCFC5E393F73B25F0A4EDB663CF`，file-list
  `EEC9A1CDBB13B5E9AFC6AA573C28E85B5E24055256C6A36824F7380DDC9CF09F`。
- `02_loader_error_scan.json` 为 **GREEN / matches=0**，quiet 16.364 秒。完整扫描日志中第一轮三种 unset-variable 文本、
  第二轮 `zg361p2c.7`、PhysFS/path-too-long 签名全部为 0。B2 四文件 clean/product/mount 三方字节门也继续 GREEN。

这证明第二轮记录的路径集合修复方向正确，也把第一轮的 stale bytes 与第二轮的 stale inventory 两类产品问题都关闭。
第三轮最终 RED 不再是 ZhongGuo loader/material/script 或文件体量问题。

### Frontend、load 与业务 marker 已通过

- Frontend-first warm-up PID `66072` 以直接 `idler-marker` 模式运行，50.066 秒、987 polls 后命中 Frontend；
  `idler_marker=true / frontend_gui_complete=true / fallback_ready=false`，warm-up cleanup
  `ok=true / tree_gone=true / job_active_processes_final=0`。
- final PID `29172` 于 `2026-09-04T11:45:58.029472Z` 启动；loader stage
  `GREEN / load_save / 303 database nodes / fatal_error_count=0`，native readiness 也以 3 个稳定样本证明
  `connection_generation=1 / date_raw=53146920 / local_player_id=1 / paused=true / map_ready=true`。
- debug log 已写出 `ZGAP2SEED: load-safe bootstrap activation`、
  `ZG361B2: result-bound justice case prepared` 与
  `ZGAP2SEED: waiting for witnessed delivery before B2 checkpoint`，说明流程越过前两轮失败点。
- 最长 mounted product 路径为 154 字符，小于 250；没有加载性能 RED，因此仍不触发 effect 文件拆分实验。

### 唯一 RED：原版可见事件先于预期 bootstrap surface

runner 在等待预期 `zga_phase2_seed.1` 时先观测到 active event instance `11`，exact definition key 为
`spymaster_task.0381`，两个选项均 enabled。暂停时先发生一次 revision race，runner 重读稳定 revision `84` 后正确记录：

```json
{"state":"unexpected_visible_event","expected_event_definition_key":"zga_phase2_seed.1","observed_event_definition_key":"spymaster_task.0381","event_instance_id":11}
```

该 definition 位于原版
`game/events/councillor_task_events/spymaster_task_events.txt:1746`，并由原版 spymaster council task/on_action 调度；它不是
ZhongGuo loader 诊断，也不是缺失 provider。runner 按 fail-closed 合同没有替玩家选择该原版事件，因此以
`SeedCaptureError: unexpected visible event before bootstrap: 'spymaster_task.0381'` 结束。这一轮没有进入预期 bootstrap event
选择，没有生成 `candidate`、新 checkpoint 或 seed contract；**seed 仍未生成，readiness 与素材均不加分**。

### 不可变性与 cleanup

- clean source 仍为 2,748 files / tree
  `DBC79E041736D838ADC8E746612EB7E21794324F764DAEC3013468B977740141`；before/after manifests 逐字节相同，均为
  591,160 bytes / SHA-256 `B285BC921C91104AB2402A108111386DFF7DF3FEB25189045331FB2EA1A09C71`，且直接复核
  `__pycache__=0 / *.pyc=0`。
- source ZIP、旧 seed、CK3 EXE、原版 rules、bridge DLL、injector 与 product manifest 的 before/after SHA 全部相同；
  `runtime_unchanged=true / clean_source_unchanged=true / external_dependencies.unchanged=true`。
- final cleanup 为 GREEN：PID `29172` 的 `tree_gone=true / job_active_processes_final=0`，watchdog absent、control files
  absent、contract errors 为空；审计时 CK3 进程数为 0。
- 本轮按冻结命令原名生成 `Z:\p2o\f\relay-live.json`，post-run clean source 中也没有 pycache；现有 artifact 没有显示
  第二轮两项 execution/provenance 偏差重现。sidecar 本身不记录父 PowerShell 对 wrapper interpreter 的完整 argv，因此不把
  `-B` 的实际使用单独提升为已证明事实。

### 第三轮核心 artifact

| artifact | bytes | SHA-256 |
|---|---:|---|
| `Z:\p2o\closure-expansion.json` | 4,489 | `9F7B7E226B8D764724D930F43160524449240E0489B11298ABC80AF3FDC3BA1C` |
| `Z:\p2o\p.json` | 122,406 | `A62AA5B07CA0C29F3FFBA689FD0527BEDEC9D04314E48725AE3C2741A6EBBD4A` |
| `Z:\p2o\f\relay-live.json` | 2,629 | `D9198C5485920EBFA91FF595AD3F676E476F3FC7726BB594343601C6E371D166` |
| `Z:\p2o\f\live.stdout.log` | 438,896 | `705CE8B15C93F95CFFFA4B8E15A49B825E24EEC02B850E9EFB982BB047206270` |
| `Z:\p2o\f\live.stderr.log` | 0 | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |
| `Z:\p2o\a\runner-report.json` | 438,636 | `59F204C4D670314100B0290BA8E4C0EA16EB83A3EC1602BA5B1BC0EBF4379B43` |
| `Z:\p2o\a\01_loader_native_readiness.json` | 35,890 | `7CCFD8ADE4E3992663982C1AC4564F8553B33CD792D475AEFB77ED9F95D63868` |
| `Z:\p2o\a\01_phase2_loader_stage_progress.jsonl` | 282,532 | `D63AF98ED0F47238358973F6BE800479EE0439D041E929E58EE8D72FEE5C1333` |
| `Z:\p2o\a\02_loader_error_scan.json` | 11,365 | `90253F979C937921A1D1C9F571B72EC1F2FA0D96D4D8DC4E38F5CC0D839628A3` |
| `Z:\p2o\a\02_loader_error.log` | 3,577,842 | `7ACE1909B812D1953B8AF8C98493B380BD7661B076090A8D929E55B97A602997` |
| `Z:\p2o\a\bootstrap-event-wait.jsonl` | 248,375 | `AB61FE58A509DEE2DC4B549363FCD849919D0DE68D391598C5DE0706400C081C` |
| `Z:\p2o\a\critical-b2-product-byte-equivalence.json` | 5,068 | `7BF6DE0C4CC55731ED9F1F564A532613B1B6BA9128BC3D8BC5AEF03F96799893` |
| `Z:\p2o\a\09_phase2_native_session_cleanup.json` | 26,117 | `368277F653044AD987B126929409E64A9BE67E14507B9FDA1747801429723925` |
| `Z:\p2o\a\ck3-logs\debug.log` | 436,004 | `17922B7B1B03CA9D51938AAA759D1A448C84BA6F037790DC131FBD6331C0D30A` |
| `Z:\p2o\a\source-tree-manifest.before.json` | 591,160 | `B285BC921C91104AB2402A108111386DFF7DF3FEB25189045331FB2EA1A09C71` |
| `Z:\p2o\a\source-tree-manifest.after.json` | 591,160 | `B285BC921C91104AB2402A108111386DFF7DF3FEB25189045331FB2EA1A09C71` |

## 下一轮准入

1. 将 `spymaster_task.0381` 作为既有存档的真实前置 surface 处理；先读取 event context 与原版选项语义，再决定是使用无该
   pending event 的同树 seed 输入，还是在 seed runner 中增加可审计的原版事件处理。不得盲选，也不得把它列为产品 loader bug。
2. 重新执行 no-launch freeze，保持 fresh 575-path closure、短路径、B2 三方字节与不可变性门；随后才分配下一次独占 CK3
   seed refresh。
3. 下一次仍只刷新 seed。没有 expected bootstrap event、candidate checkpoint/contract 与 cleanup 全部 GREEN 前，不外推
   B3/B4 gameplay、promotion source、8/8 footage、双 MP4 或 T0 完成。
