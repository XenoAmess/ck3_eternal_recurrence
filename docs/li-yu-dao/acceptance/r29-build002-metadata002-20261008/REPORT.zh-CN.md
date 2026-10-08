# R29 clean build002 与 official metadata002 阶段补充（2026-10-08）

R29 在实际源码 `487da05f6c1cf231490fd1fe480ccc704ed0a80f` 上完成新的 clean native 编译，六项 focused 测试全部退出 0；官方 SDK metadata 已取得默认 21、只读 23、challenger 24、grant 28 和 actor-cache 29 五组清单。原 build002 外层退出码仍为 1：Defender 对七个新 EXE 的登记记录为 `settings_failed`，不能写成排除已生效。native 编译与 focused 资格独立记录。

这是一份构建及 metadata 阶段补充，由 ROOT 在当前运行正常收口后导入。它不替代 ROOT 的整轮 R0029 实机报告，也不记载随后发生的游戏业务结果。整体保持 **NOT_GREEN**。

## 新 clean build002

实际 export 是 `C:/lr29s2`，新构建目录是 `C:/lr29b2`。源码前后未变，八个声明目标已产出；`BUILD_TESTING=ON`、原十二个 private native flags 为 ON，其他选项仍以原 RESULT 的全量 flags 为准。realm query/enact 与 player-control 为 OFF。RESULT 明确没有复用旧 object 或 DLL。

| focused 目标 | 实际退出码 | 原始 stdout 信息 |
| --- | ---: | --- |
| `xar_confucian_assembly_predicates_v1_test` | 0 | `PASS checks=70` |
| `xar_confucian_religious_title_readback_v1_test` | 0 | 空；以退出码为准 |
| `xar_confucian_challenger_graph_v1_test` | 0 | `PASS checks=1342` |
| `xar_ck3_main_thread_query_mailbox_v1_test` | 0 | `PASS checks=63`，真实 TrySubmit、install/clear 与 fixture callback 路线 |
| `xar_ck3_12002_event_window_context_test --numeric-value-scope` | 0 | 空；以退出码为准 |
| `xar_ck3_12004_army_route_binding_test` | 0 | 构造结束，current edge speed 保持 |

新 DLL 的原 RESULT 引用为 `C:/lr29b2/xar_ck3_bridge.dll`，9,046,528 字节，SHA-256 `bab8a2529d6c2b7c1546e126b82a8bcc427bfe874f5b8d0b4d1f0cb870edf9b3`。本补充只读取现成 JSON 中的引用，没有读取 DLL/EXE 字节。

build002 原始 wrapper 记录于 `2026-10-08T05:38:42.346628+00:00` 启动、`05:58:50.212524+00:00` 结束，退出 1。RESULT 的编译和 focused 标志均为 TRUE，Defender 为 `settings_failed`；原始错误及精确 manifest/receipt 继续保留，未补写登记成功。native qualification 绑定这个新 HEAD/export/build，用于 R29 的对应输入，不能授予未来 DLL、运行或业务资格。

## 官方 metadata002

原始 CREATE wrapper 实际退出 0，记录的 SDK 为 `2.0.0`、Pydantic 为 `2.13.5`。五组实际列表及其官方 SDK reference 逐组引用于 [EVIDENCE-REFS.actual.json](EVIDENCE-REFS.actual.json)。29 工具分支是 grant28 加显式只读 `ck3_query_profile_actor_cached_succession_v1`，bundle 为 `CONFUCIAN_CHALLENGER_GRANT_ACTOR_CACHE_29`；原 21/23/24/28 清单分别保留。

metadata RESULT 绑定本轮 clean export、编译 RESULT、native-clean qualification 和 3,904 个源码文件的完整 inventory。metadata 捕获阶段的 `business_callbacks=0`、`game_calls=0`、`actual_game_client_started=false`、`runtime_acceptance=NOT_RUN` 是该阶段原记录，不能当作当前游戏进程状态，也不能用 list-tools 成功替代 native 实机查询或保护项通过。

## 原失败及证据

build001（原 HEAD `8c0ddff7c477311e18f0a4517566df412e5f49c9`）的编译通过、focused 未全部通过，mailbox 原 stderr 为 `production actual4 Confucian registration missing`。其原件与既有失败 ZIP 保留。随后测试源码修正要求 actual4 assembly gate 同时包含 assembly 和 actor-cache；既有独立 63-check 正例、去掉 actual4 cache assignment 的负例退出 1 已封存，不在本工作包重跑，也不把 build001 改写为成功。

本阶段关键原件：

- `r29-native-build-20261008-002/RESULT.json`：1,069,197 字节，SHA-256 `b5ae742802f6802c4661d84e7a7fe36c5d2b42bcda6e8e326b71c9c281d13690`。
- `r29-official-metadata-actual-20261008-002/RESULT.json`：7,950 字节，SHA-256 `2caf207b09b1076667c5bbe31e6cf2e9041ff71dd9cb83c44f3a4e9dbab99627`。
- Defender receipt：4,070 字节，SHA-256 `4c8aa58e7d457d4551b580637777c6a287afe6df7c904e87743798f2e96bc304`。
- 原 build001 失败 ZIP：284,010 字节，SHA-256 `b1d06fc9ebf95c45e431f28d92527fb5cb0df859224bae30e4ef85612129c5e0`。

这些路径均相对外置根 `C:/workspace/ck3_lyd_runtime_20261004`，Defender 原路径在 evidence JSON 中单列。所有 argv、stdio、索引、sourcefix 和 native output 引用见 evidence JSON；二进制和源码 tar 不纳入此小型复制清单。作者只读现有 JSON/stdio/index 并生成外置候选文件，没有 MAIN/Git 写入，没有运行 build、tests、SDK、CI、OS 现场操作或存档正文读取。
