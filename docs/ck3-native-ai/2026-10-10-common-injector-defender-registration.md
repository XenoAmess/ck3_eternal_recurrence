# 公共 Source02 injector 精确 Defender 登记回执（2026-10-10）

本轮对 `C:/cbr2/xar_ck3_bridge_injector.exe` 的永久排除登记实际失败，状态为 `settings_failed`，不能标为已生效。已有公共 native build 成功事实保留；本轮没有重新编译或链接，也没有改变固定的 DLL / EXE 字节。

来源是 `af20455212ed75000ba6136b3be308a9288cb06e` 冻结的 Source02：`C:/csr2/ck3_autonomous_player/native_bridge`，已完成构建目录 `C:/cbr2`，候选身份 `common-runtime-20261010-source-af2045521`。源 archive 的 wrapper 没有主仓 Git-local opt-in，原 `native-msvc-result.json` 中 `defender_exclusions.status=disabled`；主仓当前真实 opt-in 为 true。本轮先保全原 configure/build/result、完整构建 stdout/stderr、构建输入及 runtime manifest，再补取 CMake File API 来源清单。原 13 个功能 define、`BUILD_TESTING=ON` 和 CK3 路径参数全部沿用。

| 固定产物 | 字节数 | 本轮前后 SHA-256 |
| --- | ---: | --- |
| `C:/cbr2/xar_ck3_bridge.dll` | 9459712 | `390506e486f5b19e298070523360d420de255a7811b5e79a5b279d5f9331dbbe` |
| `C:/cbr2/xar_ck3_bridge_injector.exe` | 39936 | `2e22a985ba3166ce50ca1732901f0bac0629e8ff0f068de73330fdd5d09c86a8` |

精确参数的 configure 退出 0，只生成 codemodel。随后 `Ninja -n` 显示 glob 检查及 CMake regeneration，诊断原因是 `VerifyGlobs.cmake_force` / `cmake.verify_globs` dirty，未列出 cl/link 命令。早期 `RESULT.actual.json` 因未见 `no work to do` 保守停下，其错误文本“would rebuild”过强；只读补充回执明确纠正为：这份 dry-run 不能判定 regeneration 后是否需要编译。该旧回执原样保留。

已有真实 build 0、冻结构建输入和当前产物 SHA 足以绑定来源，因此随后直接消费已生成的 File API 清单，未再运行 configure/build。`collect_manifest` 只含 `xar_ck3_bridge_injector` 对应的唯一精确 EXE；DLL 不在登记清单内。

2026-10-09 18:15:10–18:15:11 UTC，现有 `register_manifest` 按真实 token 运行一次：`admin_token=true`，走管理员 WMI 路由。唯一一次 `MSFT_MpPreference.Add` 在 `Add-invocation` 抛出 `SWbemObjectEx` 常规故障（`-2147217407`），设置读回 `before=[]`、`after=[]`，`verified_requested_paths=[]`，缺少请求的精确 injector 路径。最终 receipt 为 `settings_failed`，`partial_mutation=false`。没有重复 Add、UAC、broker 安装、排除范围扩展、EXE 执行或 CK3 / Steam 操作。

外置原件位于 `C:/workspace/ck3_lyd_runtime_20261004/r39-common-injector-defender-20261010-001`。实际设置 receipt SHA-256 为 `2476509b3f8af97286d7b88426a662ddcb0d9b87bf9644e9fcc6faf2425ea32f`。后续若修复系统登记问题，须另建 attempt，不能覆写本次失败或把授权、调用 ACK、构建成功外推为排除成功。

[证据索引](acceptance/2026-10-10-common-injector-defender-registration/INDEX.json) 固定 27 个原件及脚本，[证据包](acceptance/2026-10-10-common-injector-defender-registration/EVIDENCE.zip) 为 215367 字节，SHA-256 `47be133dea8c6c60451d3c1358cd5ffbebdb24987142a959d8533855cbb79157`。[实际校验回执](acceptance/2026-10-10-common-injector-defender-registration/VALIDATION.actual.json) 已逐项解包验证字节数和 SHA，并核对原 disabled、唯一目标、一次 Add、失败读回及固定 native 字节未变化。此校验通过仅表示证据一致，Defender 登记仍未完成。
