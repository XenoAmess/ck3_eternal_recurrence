# B3 manager central closure 修正版候选（2026-09-04）

状态：**GREEN_NO_LAUNCH / `static-ready-live-pending`**。本轮修复 production projection 的物料闭包，重新构建 exact-HEAD bridge/injector 并完成 no-launch preflight；**没有启动 CK3**，所以没有新增 provider-observed live claim。

## 首次 B3 live RED 保留与归因

首次 B3 live artifact 原样保留在：

`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b3-48da012-20260904-054011Z\artifacts-live`

| 证据 | SHA-256 |
| --- | --- |
| outer `report.json` | `B319F853623FF9443F3941F4078559D6E24CDBF0EF5D75BDCEBE269A5D961923` |
| `cell/report.json` | `8CCD24257185BB39529BCEC0FAE9F03ACAABCF281455CE55BC49D6C159E4AC56` |
| `cell/final_error.log` | `C52DC7DAA975A6EA8EB60CCEF5429E35B0299CCD4A090EEFBEE995EE491956CF` |
| `evidence-index.json` | `6BBBFCF8298AD7D56B2446AF304B34DFA89E1661DC9A2BAA1F3D8C955F15814B` |

该 attempt 的 cell 在 `310.617s` 后 RED，但 native cleanup 为 GREEN、进程树已清空。`final_error.log` 只有两条 concrete `Unknown effect`：

- `zg361_p2c_record_stage_effect`；
- `zg361_p2c_record_red_effect`。

两条 caller 都是产品中的 `common/scripted_effects/zg361_phase2_central_008_stage10_manager_governance_effects.txt`，定义均位于未投影的 `zg361_phase2_central_003_dispatch_control_effects.txt`。因此归因为 **material projection closure RED**，发生在业务/loader readiness 之前；它不是 loader-performance 证据，不触发 effect 文件体量 A/B，也不允许把超时单独归因于文件过大。

## 最小闭包修复与递归回归

修正版只在旧 B3 product-source 上新增完整 generated `zg361_phase2_central_003_dispatch_control_effects.txt`。该文件 `5,235 bytes / 9 effects`，符合每文件 1–10 的目标且未超过硬上限 20；没有复制整套无关 central stages。

freezer 新增从 `zg361_p2c_stage_10_manager_governance_effect` 出发的递归 custom-effect call graph 门禁。旧产品可确定重现四个 unresolved callees：日志中的 `record_stage`、`record_red`，以及递归发现的同文件依赖 `mark_lane_busy`、`schedule_pump`。修正版闭包为 **22 reachable effects / 9 provider shards / 0 missing / 0 duplicate**：

1. `zg361_case_kernel_001_shared_helpers_effects.txt`
2. `zg361_case_kernel_007_domain_f_manager_review_effects.txt`
3. `zg361_case_kernel_038_domain_ak_policy_version_effects.txt`
4. `zg361_manager_governance_core_adapters_effects.txt`
5. `zg361_manager_governance_dispatch_effects.txt`
6. `zg361_manager_review_effects.txt`
7. `zg361_phase2_central_003_dispatch_control_effects.txt`
8. `zg361_phase2_central_008_stage10_manager_governance_effects.txt`
9. `zg361_policy_intake_effects.txt`

单元回归同时证明：缺少递归 leaf callee 时 closure 必须 RED；首次 live RED 的两条错误、caller、缺失 provider 和 cleanup GREEN 也必须与冻结账本完全匹配。

## 新候选冻结

候选目录：

`Z:\ck3_mod_rewrite_process_assets\zg361\b3c-ce458af-20260904-0613Z`

- canonical 基线：`ce458af71a2a44decc085766720082a8b724edb8`；冻结源码提交：`793032d5d1e8280466234e9684b22d4dd1a092ff`。
- native source fingerprint：`7CD86640B2EA5A61A426DC8FA5B438FFF2F281BAB0E125E455328FFB239C2B8E`。
- bridge DLL：`2,352,640 bytes`，SHA-256 `18C783BCDF453E630EB2533D59AD182A4DEDF87692023E0B73E76E7D97FBE704`。
- paired injector：`39,936 bytes`，SHA-256 `35C8A9497CFF9FA68959BF6C9B641A0B683F11EA7AF70D16E9B434260005089E`。
- cumulative projection `phase2-b3-manager-central-closure-ce458af-r1`：`312 files / 12,573,430 bytes`；tree SHA-256 `FEE8F411920CACDB6F600D08B0FC9D2EC594CA492FDF951D90DC775FAE2C2FE9`；formal overlay SHA-256 `8FB069810BB6A8F1EA7973E30868B42C8B57FB906F79E42A7DF76BB277C8E3CF`；file-list SHA-256 `6B82BAFF1667C7B9FD8422C0E8FAB68105699B23E11FD011C237C32966F27CD3`。
- projection manifest SHA-256 `4F864DB001CC2F8DF86691A56FF84B39F3673E433246DAB93FCF8B6631EAEF71`；materialization receipt SHA-256 `B00034C8BF8C802434A7446A0BF3C8B5DB5C07280AC0BD91B186BAE102E28A58`。
- 相对 immutable B2 r10 是 `64` 个路径变化；39 个 case-kernel 分片、3 个 probation 分片及 7 个 B3 manager 用途分片均在门内。B3 manager 仍为 `43 effects`、单片最大 `10`；本轮 delta 超过 `20` 的文件为 `0`，两个旧 monolith 均不存在。

长 attempt 路径的首次 fresh build 因 MSVC object path 超限得到 C1083，失败目录已保留；最终候选改用短路径并从空 build 目录重建。这是已知 native build 路径边界，不是 CK3 loader 或 effect 体量 RED。

## 验证与下一步边界

- exact-HEAD native CTest：`92/92` GREEN；日志 SHA-256 `B895E9D988E702D6F073AB7B1D859B34B891099BDBB7B4D72F76111DB25ED0D1`。
- central generator `--check`、central tests normal/`-O`、manager generator `--check`、manager tests normal/`-O`、freezer regression normal/`-O`：8 项全部 GREEN。
- formal no-launch preflight：GREEN；日志 SHA-256 `839D6016F3B551DE186C2B609BD9A2176CB309A42EDF5B004F685AD4AFB3F2EA`。
- 机器可读 manifest 位于 `phase2-b3-central-closure-no-launch-attempt-2026-09-04.json`，并有 external 同字节副本 `attempt-manifest.json`；两者 SHA-256 均为 `5F219CD178BCD2C3AD1DA99FAD7C89118AEBF52E674CF380694F2809C671539A`。
- 唯一获授权的下一条 live 命令和 unique pipe 位于 manifest 的 `launch` 字段。只有该命令取得真实 paused provider-observed selector、直接下属身份和业务后置条件后，B3 才能从 `static-ready-live-pending` 提升。
