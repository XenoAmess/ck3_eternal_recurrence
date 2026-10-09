# 2026-10-10 宗教头衔旧 holder 子行的 MSVC SEH 修复

共享 Source01（提交 `5e2f65740a28dd5df34ffa59862a47030048a1b3`，`C:/csr1`）的首次 build 在 `C:/cbr1/msvc-build.log:129` 实际报 `C2712`：`ck3_12003_religious_title_readback.cpp:69` 的 `ReadLegacyHolder` 同时包含 `__try` 和需要 C++ 展开的输出对象重置／字符串赋值。旧冻结源码与失败 build 不改写。

生产源码现在把 `ReadTitleHolderV1` 调用放进仅使用参数引用和布尔结果的 `CallLegacyHolder` SEH helper。原 `ReadLegacyHolder` 在 SEH 外处理输出；signed title ID 拒绝、reader 的 available/unavailable 结果，以及 native access exception 后清空输出并写入 `legacy_holder_native_access_failed` 均保留。公开签名、JSON、native bindings 和游戏行为没有修改。

一次定向 MSVC 14.51.36231 编译在 `C:/lci39rtseh1` 对修复后的生产 TU 和未修改的既有 fixture TU 分别运行 `/c /std:c++20 /O2 /MD /W4 /WX /permissive- /EHsc /UNDEBUG`，两项 **exit 0**、stderr 均为空。命令、输入 SHA、原始输出与原 C2712 日志在 [证据索引](acceptance/2026-10-10-religious-title-seh-compile/INDEX.actual.json)。没有生成 EXE，不涉及 EXE 排除登记或 CK3/Steam 接触。

现有 CMake target `xar_confucian_religious_title_readback_v1_test` 链接共享 `xar_ck3_12002_runtime`，本次验证时尚无该库产物。为了避免独立重建整库，本包只取得编译通过，**不声称 fixture 已执行或公共 runtime 已通过**。共享增量 build 完成后可用同一库继续链接、执行既有 target；全部现有断言保留。

`open_kaishek` 为 not-applicable：本次失败是 MSVC 对 C++ SEH/对象展开的编译约束，不涉及 CK3 脚本 parser、有限运行时或游戏语义验收。
