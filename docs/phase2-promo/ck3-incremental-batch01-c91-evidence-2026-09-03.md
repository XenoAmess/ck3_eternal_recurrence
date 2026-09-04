# CK3 Phase 2 incremental batch 01 (core-current) live evidence

实测时间：2026-09-03 15:03–15:06（Asia/Shanghai）。本轮使用唯一 CK3 槽，`native-observer-only`，未发送 UI、协议、游戏操作或商店/付款动作。

## 固定输入

- Clean export：`Z:\ck3_mod_rewrite\_runtime\phase2-preflight-c91a1d0-20260903\clean`
- Frozen git：`c91a1d01ee2708ae934591e4e8ae17e2f9bdf39b`
- Source ZIP：`source-c91a1d0.zip`，SHA-256 `7100FCC002126C0AEDA8DA953AF1D0F5F0B48F597F42DB07DEC3BAC70393005A`
- Product projection：`core-current`，51 files / 7,164,060 bytes，tree SHA `13af83df27de3dc3da5d6f1cec77ffc6347b5299a72cbc64969914865ff443ea`
- CK3：Steam 1.19.0.6，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- Bridge：Release freeze165b bundle；pipe `\\.\pipe\xar_ck3_bridge_zg361_9f3e6d4c2b1a0987654321fedcba9876`

## 结果

- Artifact：`Z:\ck3_mod_rewrite\_runtime\formal-phase2-incremental-01-core-current-c91-20260903\artifacts\runner-report.json`
- Report SHA-256：`1371E0C601253C555EF46DB5315779017D9BA278957C7BA88ED69D6726EA423B`
- CK3 PID 46140 启动，debug.log 在 15:04:20 到达 `Setting idler 'Frontend'`，紧接 `End loading of history`（行 2858–2859）。
- Native session cleanup：GREEN；WM_CLOSE 后 CK3 exit code 1，`tree_gone=true`、`cleanup_proven=true`，最终无 CK3/watchdog 残留。
- Runner 总结果：RED，`live_verdict=heartbeat_not_observed`（native observer sample_count=0），不是启动崩溃或加载超时。
- `error.log` 176 行，主要为 core-current 51 文件投影缺少二期 B1/B2/manager 等后续定义（Unknown effect / loc）；应标为 projection/parser RED。完整错误副本及哈希见 artifact `logs_copy`。

结论：本批次达到 **STARTUP_GREEN / Frontend GREEN**，但不能宣称 Phase 2 完整运行 GREEN；需按增量批次补齐依赖后复测。
