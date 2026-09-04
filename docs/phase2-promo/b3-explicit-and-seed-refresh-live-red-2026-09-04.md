# B3 explicit-AND seed refresh live RED（2026-09-04）

状态：**正式失败证据 / product runtime RED / seed 未生成 / T0 不加分**

本页冻结 `Z:\p2s10a` 的一次完整实机失败。它承接
[`b3-explicit-and-seed-refresh-no-launch-2026-09-04.md`](b3-explicit-and-seed-refresh-no-launch-2026-09-04.md)
中的唯一命令；没有改写或删除 no-launch 证据。失败发生在旧 seed 存档进入 B2
result-freeze 业务链之后，不是 Frontend loader 超时。

## 冻结输入与物理边界

- source commit：`9cd921674e192a118ea27c376fd41dfbb4bab327`。
- explicit-AND product：
  `Z:\ck3_mod_rewrite_process_assets\zg361\b3-r5-exact-and-wrapper-4d3c284-20260904T095828Z\product-source`。
- product 身份：**565 files / 21,607,199 bytes**；tree SHA-256
  `D94C2D5D23E9AD254F4B20988FBF3C8E08408BAA61070BD85F42B2D2FCBEA35D`。
- 本轮 prospective/mounted 最长路径为 **154 characters**，低于既定的 250-character
  边界。
- 输入旧存档 SHA-256：
  `BFC73FD9E7E80145CDF39AABC66BC2D731881122ADAB0CC0BA675FA07D1E6733`。
- attempt：`Z:\p2s10`；artifact：`Z:\p2s10a`；relay/result root：
  `Z:\p2s10f`。

## 实机时间线

1. frontend-first warmup 使用同一 isolated profile 与冻结 product/fixture，CK3 在
   **109.396 s** 到达 authenticated responsive Frontend。`End loading history`
   与 `frontend_gui_complete` 均为 true；本轮没有发生 loader-stage timeout。
2. warmup 进程被受管回收后，final PID `9240` 绑定冻结 named pipe，并明确加载旧
   `phase2_seed`。
3. 旧存档进入 result-freeze 链。`debug.log` 在 `19:08:09` 记录
   `ZG361B2: result-bound justice case prepared`。
4. 同一时间点，产品脚本读取首次尚未建立的 optional variables。runner 的
   `loader_error_scan` 按合同 fail-closed，最终为
   `RunnerError: 93 ZhongGuo-attributed loader error signature(s) found`。
5. runner 在 seed capture 前停止；
   `candidate/zg361_phase2_seed_contract.candidate.json` **不存在**，因此没有可晋升的
   checkpoint 或 contract。
6. managed cleanup 为 GREEN；最终 CK3 inventory 为空（CK3 count `0`），watchdog
   与 control files 均已清理，source/runtime trees 未变化。

## 93 条诊断的精确构成

93 条全部被分入 `parser_or_script`，但不是语法解析失败。它们是 **31 个逻辑上的
optional-variable 比较，每个比较固定产生 3 条 Jomini 诊断**：

1. `Failed to fetch variable ... due to not being set`；
2. `Event target link 'var' returned an unset scope`；
3. `Invalid left side during comparison 'var'`。

也就是 `93 = 31 × 3`。31 个比较涉及 28 个唯一变量，按文件分布如下：

| 文件 | 逻辑比较 | 日志条数 | 首次状态 |
| --- | ---: | ---: | --- |
| `common/scripted_effects/zg361_b2_debt_consumers_effects.txt` | 19 | 57 | m014–m017、m069–m081、m358–m359 的 `*_policy_debt_active` |
| `common/scripted_effects/zg361_b2_069_delivery_effects.txt` | 10 | 30 | m015/m016/m017/m069 `object_active`、m079 remand、m080 state（2 次）、PIP state（3 次） |
| `common/scripted_effects/zg361_b2_072_access_audit_effects.txt` | 1 | 3 | m072 `object_active` |
| `common/scripted_effects/zg361_b2_081_projection_access_effects.txt` | 1 | 3 | m081 `object_active` |

四个 effect 文件都是 generator 产物；产品修复入口是
`mod_zhongguo_style/tools/gen_361_b2_runtime.py`，不得直接手改生成文件。该归因只要求
把 optional-variable 比较放到真正 lazy 的存在性分支内，不要求合并 effect 分片，
也没有触发新的文件体量例外。

## 冻结 artifacts

| 证据 | 路径 | SHA-256 |
| --- | --- | --- |
| runner report | `Z:\p2s10a\runner-report.json` | `77E4927BB84F304245CF2987125E30D5B55D5E3CB29D87BAB558CFB702D51BCB` |
| loader/error scan | `Z:\p2s10a\02_loader_error_scan.json` | `7958C5A40C8721195A67BABE46F1AC92D24E1BECA1878DF868BA57B6AF4EFF5B` |
| frozen full error log | `Z:\p2s10a\02_loader_error.log` | `377B7B5DB1C1CCA169209212872BB7ED0D683EAFE72878DA9A35F727E791CA87` |
| outer relay result | `Z:\p2s10f\default-desktop-live.json` | `2D96AE47C431F95A1E38D2DC4F2FCEAF279CF8B840EA96E4EAE84F8D7E6CDCAC` |
| cleanup | `Z:\p2s10a\09_phase2_native_session_cleanup.json` | `55284995C4636A292885778B5C4C1D6736D8A4CF422764C928F436C4DC8C42C5` |

## 结论边界

- 这次 565-file / 21.6 MB product 在 109.396 s 到达 Frontend，随后实际进入旧存档的
  result-freeze 链。它进一步否定“文件大或文件数本身就是此次启动问题根因”的解释；
  本轮可复现 RED 有更早且更具体的业务脚本首错。
- 154-character 最长 mounted path 与本轮 Frontend GREEN 相容，支持后续继续使用短
  physical roots。该单轮证据不单独证明“缩短路径必然修复所有启动问题”。
- 本轮不是 pure loader-performance RED，因此不触发额外 effect 文件拆分。若后续在
  清除 material/runtime 首错后仍出现纯加载性能 RED，再按同条件 A/B 执行边界拆分。
- 候选 seed 未生成；**本轮不能解除** promotion source capture 的 HOLD，只有后续独立
  GREEN seed 证据才能解除。B3、完整 Phase 2、最终宣传视频和 T0 都没有因本轮获得
  readiness 增量。
