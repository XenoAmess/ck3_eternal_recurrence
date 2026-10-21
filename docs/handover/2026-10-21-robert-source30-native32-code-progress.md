# Source30 与 Native32 代码交付进度（2026-10-21）

machine_id: xenoamess-full-tower-eb9d2c1186  
observed_at_utc: 2026-10-21T01:16:40.195180+00:00
本篇记录本机源码、离线产物与运行边界；其他机器需重新核验安装、部署、容量及实机状态。

Source30 canonical 已实际生成：`2fd0412acf2357e8ee08ed8355e2a4a816ebfaef`。双 generic export 与 BASE 于 01:05:18Z 完成，每视图 1465 文件、59,299,236 B；8 个新增唯一文件和 1461 个已有共享文件分别记账。`COMPLETE.json` 为 2027 B / `3849217dd04ab5d127cdfc31dace540beb521026cb7f7d3776baf7364386f6ca`；BASE 为 403040 B / `5d159608105afa5ffe61169375158057a0fca84e707569bc08dbd0707bc8ed97`。来源为本机 `source30-sdk-prep01`，anchor 为 6671 B / `71524c0b8757bcbf3d783d3a578b70649576b6b01ac603b8bf716b5529042ccf`。

Source30 两份物理视图各实际 35/35 distinct tests 通过，共 70 次执行；每视图均实际绑定 513 个 SDK origins，无 RAM 源码替换、skip、RPC 或 scratch。Root 小型实证入口 `ROOT-SOURCE30-ACTUAL-DUAL-BASE01.json` 为 2699 B / `2f8f8e117f79fa40fcc413d9a267e12a85e299f9f40c26e583c581d2b0f3d8b0`。COMPLETE 仍明确 `SOURCE_READY_NOT_LOADED`，BASE 的 `actual_native_loaded=false`、`runtime_admitted=false`、`new_campaign_credit=0`。Source31 仅 RAM 61 项资格，尚未物理导出。

本轮公共包包括共享 launcher/背景字段合同及 keyed FilePin 回归、生活方式 metadata 精简、lean snapshot/战争缺口处理、cached native clock summary、Native32 builder 和 runtime journal adapter。Driver 与 exact-clock 大型历史模块仅记录修改函数的 AST 类型资格，不称整文件 strict 通过。旧 exact payload 上限仍为 8 KiB，新增 summary 组合为 16 KiB；`active_hook/state` 未在线上传输。公共新源码不会自动替换已冻结运行输入，对应关系以各自精确源码和 anchor/BASE 为准。

本轮新增测试实际组合通过：cached 6 + lifestyle 12 + keyed 9 = 27；runtime adapter 独立 7；builder recipe 独立 9，共 43 项。keyed 使用真实仓库 producer/reader 和受限 realFS 夹具；runtime/builder 组不调用 Game、RPC 或编译器。27 项的 195 次采样 native 高水位 8680 B，加 128 KiB FS/pending 守卫在保留的 1 MiB 内；专属夹具根已清理读回 absent。主组 34 文件及 runtime、builder 各 3 文件的实际 strict/strict-equality、follow-imports=skip、no-incremental、cache-dir=nul 均为 0 错误。未重跑旧 89 项；其口径仍为 86 realFS + 3 个稀疏缺项的精确 HEAD blob RAM 补验。

workflow 仅改原步骤39，保留143步骤与原55/94索引、命令，新增永久入口、独立候选组及显式 MYPYPATH。源码 75549 B / `eddeaa1568e2ea64ac5923c7843973e4a5d86a2d4c139515818bd53bc4709342`，原位写入保留 FileID，native 正增4096 B。R08 SaveGate 旧夹具补齐现代 retained/native 身份：4431 B / `5205ede019a6820510f1a41836e6cd037c07f8fc7a34e7ab16619169bea858a8`；原8条断言保持，未知 Save/独立后验两分支均只提交一次、禁止重放；实际测试及整叶 strict 通过，生产守卫未放宽。

Native32 已完成本机离线编译/链接资格。[原始离线报告](../ck3-native-ai/evidence/native32-production-2026-10-21-xenoamess-full-tower-eb9d2c1186.json) 严格复制 `D:/codex-ck3-demos/2026-10-21-native32-passive-build01/PRODUCTION-RESULT01.json` 原字节：16886 B / `aace13ba74f871d7dd99c7b1b77bd2338f4f9a41c25402ef90e3f59b85dde81e`。首轮 link 超帽失败与续接来源均保留；4个 header 消费 TU 已重编译，最终 DLL 为19535872 B / `6c3a2e961c9c92225f1225252e08a73bd7fe67b1b280a1dd0132100b5e39c1cc`。DLL/MAP 不进入 Git 源码包。

`partial_bytes_unreadable_after_overwrite=true` 只表示没有独立 partial 副本，不能扩大为四份原 body 全部变化或不可读取：DLL/MAP 前后字节不同；LIB3076 B 与 EXP1513 B 的前后 SHA 相同。原报告不为勘误重写。报告明确 `OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED`、`DLL_loads=0`、`Game_calls=0`、`runtime_qualified=false`、`performance_goal_qualified=false`；离线资格不授 Native32 实机准入。

截至观察时，本包未提交或推送。公开基线 `9592cefdda846fc0242430d8fef1fef1f58c81a0` 的 [Official CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39523039689/job/118971178265) 为 step20 旧 SaveGate 夹具失败；19通过，22/39/55/94跳过。[Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39523039722/job/118971178172) 通过。本轮修复和新接线须等待公开后精确新 SHA CI，不能借旧结果称通过；CI 机器未核实时为 `machine_id: unknown`。

双包实际资格入口 `SOURCE30-ACTUAL-DUAL-ORIGIN-QUALIFICATION01.json` 为3699 B / `1f2ed2ed34ccdead14a8635b64350ce3077b9daf59a785726637916436f3bf2d`（01:13:12Z，本机）；逐项可用性勘误为本机 Native32 `metadata/ROOT-PARTIAL-CONTENT-AVAILABILITY-CORRECTION01.json`，5582 B / `d7a55a95e53b78eb5f8bd95cc8135d2f1cb84d666d2b0ca4e812da7edd6f38ba`。LIB mtime 不变，EXP mtime 改变，不影响两者前后内容 SHA 相同的事实。

下一次 Native32 冷启动要求 Source31/1466 的精确来源合同，不以 Source30/1465 别名或旧回退替代。当前 adapter 三叶已按此合同完成软件测试与类型检查；这一点仍不授部署、原生加载或实机准入。

原局累计信用仍为 **5429/10950日，G2 6/8，1秒/日未达**。离线构建、导出、软件测试与CI不增加游戏天数，不完成M6/M7，不重置原 campaign 墙钟。
