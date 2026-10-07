# R0021 .4 Confucian schema 与正常退出 admission 源码修复

2026-10-07，冻结来源 `9b068c8fc9bb45d69417bf6857dddd65abece7d6` / `C:/lr20s2` 的 R0021 在 attach、snapshot、SAVE 后，G2/G3 的 SDK 返回 `isError=true`，错误为 `native payload exact build/schema differs`；正常退出 context query 返回 `unsupported native gameplay step`。原 SDK5/6/7 及没有原生附件的 response 原件保留，见 [实际 RED cutoff](acceptance/2026-10-07-r0021-9b068c8-checkpoint-schema-red/)。这些 SDK 没有可据以伪造的 native payload/typed normal-exit receipt。

真实源码路径解释并由隔离 fixture 重现两处问题：

- Confucian native serializer 与 Python/reader 的固定语义 schema 均为 `ck3_12003_confucian_*_v1`，payload 的 build version/EXE/backend 则准确选择 .3/.4。`.4 Render12004BuildIdentity` 对所有 `ck3_12003_` schema 的替换把这三个语义名字也改成 `.4` 名，随后严格 `_common_payload` 拒绝。修复只在 `.4` renderer 内保留 G2、G3、G4 的三项 canonical schema，按已有 Army/Knights 的明确语义例外处理；没有放宽 DTO，也没有更改 reader/12AST/hash。
- `.4` descriptor 已声明 normal-exit capability，已有 handler 使用 .4 GUI revision 且核真实 episode/frame；但 `GameAdapter::supports_step` 的 normal-exit 分支仅接受 `.3` version/SHA，worker 在 handler 前返回 unsupported。修复保留原 `.3` 条件，额外接受 `IsCk3_12004Descriptor` 的精确 adapter/version/SHA tuple；最终仍要求 enabled adapter 与声明 capability。没有绕过 callback、签名、原 HANDLE、session、claim、source inventory 或同帧保护。

独立 detached 工作树 `C:/lr21rw1` 从 origin `3408351667e1f502e58bb19c18935989d1c1ea75` 创建。两项产品变更仅在 `src/ck3_12004_adapter.cpp` 与 `src/game_adapter.cpp`，冻结导出、主树、现场进程和旧证据未改。

ROOT 单独授权一个纯 C++ fixture。脚本从实际原/修复源提取完整 renderer 与纯 helper、normal-exit 实际分支和共有 capability lookup，保存源 ref 与片段 SHA。它只编译隔离 EXE，没有构建 runtime DLL、注入、进程/HANDLE、SDK、游戏、桌面或存档 body。8 项 admission 检查保留 `.3`、恢复 exact `.4`，拒绝 mixed SHA、错误 adapter、无 capability 和 disabled adapter。完整 G2/G3 惯性 envelope 经原 renderer 得到与现场相同的 DTO 拒绝，经修复 renderer 严格接受且 full-product credit=false；G4 仅验证 schema 保留，不授图观测信用。6 项现有 Python exact-build DTO 测试通过。

fixture 开发失败也保留：首次共有 return 字面断言失败、第二次 compiler 路径定位失败均发生在编译器之前；第三次编译 C1004 来自提取到了下一条 grant 分支的 `#if`。修正 fixture scaffolding 后，隔离编译和运行均 exit0；产品两处保护没有因这些失败放宽。直接 isolated compiler 未调用登记 hook，不宣称 fixture EXE 已被 Defender 排除。

可执行 fixture CLI（所有输出必须 fresh）：

```text
C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe -X utf8 ck3_autonomous_player/native_bridge/tests/run_confucian_semantic_identity_fixture.py --source-root <actual-fixed-source> --legacy-source-root C:/lr20s2 --output <fresh-isolated-output> --vcvars <actual-vcvars64.bat>
```

[小型 source/test 归档](acceptance/2026-10-07-r0021-native-semantic-schema-exit-fix/INDEX.json) 保存 patch、preimage、真实编译 argv、生成源、stdout/SHA 与失败回执。R0021 正常 GUI 关闭或原 HANDLE0 的生命周期事实由 ROOT 另行保全，不能改写为 typed normal-exit callback PASS。本源码还需新的 clean HEAD/export/native qualification/metadata/fresh cold 实机才能授运行信用；正式 I3b 与全模组继续 NOT_GREEN。源码发布采用 fetch→rebase→复测→普通 fast-forward push，无 merge/force push。
