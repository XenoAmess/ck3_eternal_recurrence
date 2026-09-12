# R540–R542 source restore lifecycle contract RED（2026-09-12）

## 结论

R540 完成 Frontend warm-up 并终止，R541 作为唯一 gameplay 实例完成了
`phase2_fact_quota_calibration` 与 `phase2_receipt_appeal_pip` 两段 clean span。
在第三段前，canonical player-manager source 被逐字节恢复，supervisor 正确回收
R541/PID `116916` 并启动 R542/PID `136832`。源 checkpoint、owner/player、日期、
同一 pipe 和新 PID 都已通过底层验证；Stage 10 动作尚未开始。

上层 `GameplayBridgeService` 随后把两个 CK3 进程各自合法的
`connection_generation=1` 错判为不连续，因为新加入的 source-restore consumer
要求跨进程满足 `g(new)=g(old)+1`。这是 Python 验收合同 RED，不是 mod 业务 RED、
源存档 RED 或 native restore RED。整条 take 不完整，两段素材不单独计数，P2 仍为
`0/8`。

## 冻结证据

- capture plan：
  `Z:\ck3_mod_rewrite\_runtime\p2-capture-r540-r547-9b38bd4-20260912\capture-plan.json`
  - `13,452` bytes
  - SHA-256 `7A592A4307A6130B1A5C23F4490B9A730F6E6113179E203BF857BD59A5E557F5`
- RED report：
  `Z:\ck3_mod_rewrite\_runtime\p2-capture-r540-r547-9b38bd4-20260912\capture\report.json`
  - `4,377,173` bytes
  - SHA-256 `733307D9F6948CDDB10F55EA77F278912120817DA1AD5131B4A98A9567E42D97`
- 原始 cleanup RED：
  `Z:\ck3_mod_rewrite\_runtime\p2-capture-r540-r547-9b38bd4-20260912\capture\cell\09_phase2_native_session_cleanup.json`
  - `33,533` bytes
  - SHA-256 `0C37F58CC3AD8C4DC114359EB71FBF6B59EAB2DB726CF61BA682C7ADFE212D4C`
- supervisor restore outbox：
  `Z:\ck3_mod_rewrite\_runtime\p2-capture-r540-r547-9b38bd4-20260912\capture_native_state\native-session\bridge\outbox\restore-ab142420691d4574bf20458b61133fa6.json`
  - `908` bytes
  - SHA-256 `BF26F42A1C9A5C45B5E9F927359EABBC20BD792C5656387E6BF52ED60DBD1402`
  - 明确记录 `lifecycle_intent=restore`、`previous_pid=116916`、
    `pid=136832`，以及 checkpoint `65,244,992` bytes / SHA-256
    `50B713F2B479E92386302A45B5790A327ABC7862F55CF0E000EC0943DB7AC7E4`。

R542 的 driver state 同时记录 checkpoint `status=registered_source`、
`date_raw=53155680`、player `27181`、owner `36354`、lineage
`zg361-stage10-player-manager-50b713f2...`，并把 bridge PID 更新为 `136832`。
`cell/manager-stage10/stage10-player-subject.json` 不存在，证明动作未越过恢复门。

## 最小修复

根仓库提交 `67a9dad2109e850b82b920fdd28a9c134bc4a4b0`：

1. source restore 与 Workforce Route-B 的 service consumer 继续要求 old/new PID
   都为正且不同、两侧 generation 都为正并写入 typed receipt；跨 CK3 进程的先后
   关系只由 PID replacement/lifecycle ACK 证明，不再比较 generation 数值。
2. 如果业务编排在重启后、完整语义 lineage 落盘前 RED，cleanup 使用 supervisor
   已观察到的 restart count、每个 retired shutdown、final PID shutdown 与全局零库存
   证明进程清理。该分支显式输出 `restart_semantics_proven=false`，只把 cleanup 判为
   GREEN，不改变原业务 RED。

验证严格限于受影响范围：source-restore service 测试 `5/5` GREEN，promo capture
合同脚本 GREEN，`py_compile` 与 `git diff --check` GREEN。原始 R541→R542 session
report 离线重放后的 cleanup 为：

`Z:\ck3_mod_rewrite\_runtime\p2-capture-r540-r547-9b38bd4-20260912\capture\cell\cleanup-recheck\09_phase2_native_session_cleanup.json`

其大小为 `34,195` bytes，SHA-256
`10043247A37FBBEDCD1A92E14ACCD5FDA098B94CD349642C5B4557FAD270D3A6`，
`pid_lineage=[116916,136832]`、`failed_checks=[]`，同时保留
`restart_semantics_proven=false`。没有为这项 Python-only 修复重启 CK3 或重建 DLL。

接口语义影响已同步到 open_kaishek，提交
`f99556b70efca37ddfdadca162d3bca2044c3cd1`。公共 MCP wire、工具名、endpoint、
Java/profile/adapter、依赖与 Operator MCP `1.1.0` 均未改变。

## 当前状态与下一步

R540、R541、R542 及 FFmpeg/injector 均已终止，当前没有 CK3 实例。P1 保持
`9/9 GREEN`，最终视频硬锁已解除；P2 因没有完整八段 take 仍为 `0/8`，剪辑、
导出和发布继续受素材门约束。下一次只执行一个新的有界 capture：R543 warm-up，
随后 R544 gameplay；若恢复路径进入新 CK3，则按实际启动继续递增轮次。
