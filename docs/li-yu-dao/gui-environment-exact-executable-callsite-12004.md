# R0022 .4 GUI 环境 exact EXE 参数修复

R22 原 decision readonly 原生回执仍保持 `available=false` / `exact_crozier_keyed_query_unavailable`，本包没有 SDK、桌面、进程、runtime DLL 或存档访问。当前实机需要后续新源码导出、实际 native 资格与新 cold；本次源码/夹具不授业务通过。

`BindZhongguoScoreboardNativeEnvironmentV1` 第四参数 `executable_sha256` 默认空；实际 .4 分支要求该参数与 `ck3_12004::kExecutableSha256` 精确相等。bridge 的五个礼与道 Native binder 调用只传 module base、true、`LydPrivateGuiRevision(game.descriptor())`，因此 exact .4 descriptor 仍在环境 admission 被拒。

最小修复仅为五个调用补传 `game.descriptor().executable_sha256`，覆盖 grant、normal-exit、decision open/select/query 所用 Native 环境。`BindZhongguoScoreboardActionDispatchEnvironmentV1` 的真实接口只有三个参数，保持原样；所有 outer descriptor/frame/owner、ABI/source、widget/dispatch 与 once guard 均未改，也没有新增 RVA。严格源码还原检查证明删除这五个新参数后 bridge 与原件逐字符相同。

ROOT 授权单个纯 C++ fixture 实际 compile/run 均 exit0。夹具机械提取生产 Native binder、exact .3/.4 descriptor predicate、GUI revision selector 和五组原/修复调用表达式，核对 25 项 callsite admission 与 3 项 empty/mixed SHA/false admitted 拒绝；旧 .3 行为保留。module base 固定0，地址 helper 若被执行即 abort，未执行任何 GUI callback。旧 case variables 仅作 metadata stub，这不是 .3 callback 或 .4 GUI provider 验收。direct compiler 没调用 Defender 设置 helper，不声明该新 EXE 排除成功。

随后实际 normal-exit query 独立暴露 `exact_gui_code_pins_changed`，此五参数修复没有把它标为已修。原 R22 错误原件保留，全模组 NOT_GREEN，正常关闭事实和 typed callback 信用分列。

[源码与单夹具原件索引](acceptance/2026-10-07-r0022-gui-environment-exact-exe-source-fix/INDEX.json)。历史 [R21 semantic schema/admission 修复](native-semantic-schema-normal-exit-12004-fix.md) 不变。


## 同场 normal-exit `exact_gui_code_pins_changed` 定向勘正

原 native 0007 的 `exact_build_verified=true` 属于 descriptor 身份检查；它不证明 Native 环境的 `exact_build_admitted`。`normal_exit_map_v1.cpp::Pins` 第一条件即检查该环境位，漏传第四 SHA 时在读取任何 pin 字节前返回 false，统一原因文本为 `exact_gui_code_pins_changed`。此前“另一个 code-pin 阻点待查”保持当时观察，本追加纠正其层级；没有编造第二个已证实字节失配。

本次只从已冻结本机 EXE 磁盘进行一次静态 PE 对比：101040248B、SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。依据现有 independently-qualified .4 GUI header 的 RVAs `0x3AAB0E0`、`0x3ABC4B0`、`0x3A78210`、`0x3AA0D20`，四段32字节与原 `kPins` 全部精确相等。生产代码本来按 revision 选择这些 .4 RVAs，并不读取 `.inc` 中旧 .3 RVA；无需 pin、RVA 或 guard 改动。

因此已发布五个 caller 参数修复同时覆盖该环境准入原因。静态前缀相等不代表实际 context callback、source inventory、frame、签名或 typed 退出已经成功；原 R22 unavailable/无dispatch/未typed退出仍原样，下一场须 fresh native 资格与实际运行。没有读取运行进程内存、SDK/游戏/屏幕动作或 DLL 构建。

[原 native、静态四段与实际 EXE/source refs](acceptance/2026-10-07-r0022-gui-environment-exact-exe-source-fix/NORMAL-EXIT-STATIC-PINS-INDEX.actual.json)。
