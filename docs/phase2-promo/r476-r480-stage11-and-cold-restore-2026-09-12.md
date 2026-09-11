# R476–R480 Stage 11 与代表性终态 cold restore 收口

## 结论

本工作包把 T0-P1 九项硬门从 `6/9` 推进到 **`8/9 = 88.9%`**：Stage 11 与代表性终态 cold restore 均取得 production-live GREEN。P1 仍为 `PENDING`，唯一缺项是 Stage 10 `zg361mg.120` 的真实 provider terminal；P2 最终宣传视频继续 `LOCKED`，本包没有检查、更新或制作任何视频物料。

验收绑定 CK3 exact build `1.19.0.6`，EXE SHA-256 为 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，加载的候选产品树 SHA-256 为 `84443728419E390024936809778C98D4BF4B529747FF776DE0F2FD4DC97E58CE`。

## Stage 11

- 旧轮次 R476 是 frontend warmup，完成后终止；当前业务轮次 R477 是当时唯一存活的 gameplay 实例，PID `160144`、process-local connection generation `1`。
- R477 在 paused `date_raw=53366616`、玩家/owner `32904` 上读取 subject `31450`。真实 Workforce provider 返回 `terminal=true`、`terminal_kind=not_applicable`，AL case 为 cycle `5` / case `1` / state `7` / inactive；portfolio 为 closed/status `7`、`terminal_na=true`、`final_conservation_ok=true`。
- provider 的 owner、subject、case identity 与 same-frame readiness 全部为 true，因此 Stage 11 的合法 N/A terminal 满足产品门，不需要伪造 `.360` receipt，也不扩展为后续章节或跨周期长跑。
- 冻结 artifact：`Z:\ck3_mod_rewrite\_runtime\p1-stage11-r366-al-source-r476-r477-9b03ac7-20260912\live-artifacts\terminal-stages-green.json`，SHA-256 `F635739E08D8A7CD99A9CDD85E6F16219D81FA7B74313ECF3F851E2BC0E03855`。

## 代表性终态 cold restore

- R478 是 frontend warmup，完成后终止。R479 是源 gameplay 实例，PID `86544`；它从 R477 终态创建真实 `xar_checkpoint.ck3`。随后同一受管 lifecycle queue 关闭 R479，并以新轮次 R480、PID `77320` cold restore 该 checkpoint；两个 gameplay PID 没有并存。
- 源终态 checkpoint 为 `representative-terminal.ck3`，大小 `114788378` bytes，SHA-256 `306BCF913A4B8F859D7CFC365AEF1D52A149CEF222D85EA31C1B8E1F4B03E8A7`。R479 实际生成并由 R480 恢复的 `xar_checkpoint.ck3` 大小 `114788611` bytes，SHA-256 `0CCF17227AE070E715FB5DBE9BB4BEAA167C2987658F1E6DEA24E7D19396E57D`。
- 恢复前后均为 paused `date_raw=53366616`、玩家 `32904`。B1、AF5、Central 与 Workforce 四个业务域的 identity/state/receipt 回读完全相同，`four_domain_terminal_identity=true`。
- PID lineage 为 `[86544, 77320]`。两个不同 CK3 进程各自建立 process-local generation `1`，所以 generation lineage 合法值为 `[1, 1]`；跨进程不要求也不应伪造全局 `+1`。
- cold restore artifact：`Z:\ck3_mod_rewrite\_runtime\p1-terminal-cold-restore-r477-r478-r479-r480-8b06ecf-20260912\live-artifacts\terminal-cold-restore-green.json`，大小 `755472` bytes，SHA-256 `728E67D341F6F9A9510CD7A6F52F461A55E887C3F6B77EE5ADA782DA0FA6DE83`。

## cleanup RED、根因与修复

首次 cleanup consumer 错把 connection generation 当作跨 CK3 进程全局递增计数，要求 R480 generation 必须等于 R479 generation `+1`。实际 bridge 每个新进程从 generation `1` 开始，因此业务 cold restore 已 GREEN，而旧 cleanup 判定产生合同 RED。原始 RED 保留为：

`Z:\ck3_mod_rewrite\_runtime\p1-terminal-cold-restore-r477-r478-r479-r480-8b06ecf-20260912\live-artifacts\09_phase2_native_session_cleanup-red-generation-assumption.json`

SHA-256：`3CCF3EBCA1647B6CF28824C2AD3FF7B0B51FA7EA3BBB749147DAB86790D268BF`。

最小修复让 cleanup consumer 验证两个不同的正 PID，以及每个 PID 上与对应 frame 一致的正 process-local generation。它不改变 DLL、游戏文件、公共 MCP schema、启动配置或加载顺序。定点测试 `test_zg361_phase2_terminal_cold_restore.py` 在 normal/optimized Python 各 `15/15` GREEN，`test_zg361_phase2_formal_live_session_lineage.py` 各 `6/6` GREEN。冻结 R480 报告随后离线重放，无需再启动 CK3；修复后的 cleanup artifact 为：

`Z:\ck3_mod_rewrite\_runtime\p1-terminal-cold-restore-r477-r478-r479-r480-8b06ecf-20260912\live-artifacts\09_phase2_native_session_cleanup.json`

大小 `41893` bytes，SHA-256 `2C578FF4F8BB4D23DF10C1D01C4D0CEE80B3B31D0E48C58ACDFCF9BBD21A1F56`，所有 cleanup checks 为 true。R480 与 Operator MCP 随后均已终止，CK3、injector、Operator MCP 进程数和端口 `12437` listener 均为零。

根仓库修复提交为 `b9b24ce48243eb3618ffa9574d1e42e49e907f57`，最终 cleanup 合同与本文档前的测试流程记录提交为 `d0f471c5b7c8bacf2a81c9e01d15a86423e173ea`。接口语义变化已同步到 open_kaishek，提交为 `862c60acf45adc668761098a8db71abf4468b49f` 与 `66cc3191a1b284c8b384138e630bea548df3b2ef`；两边均已 push 并与各自远端同步。

## P1 账本与边界

权威中间账本为 `Z:\ck3_mod_rewrite\_runtime\p1-critical-path-assembler\pending-assembly-status.json`，当前 SHA-256 `E604D33E506EBEFE9A676BDEF52F06F2705D87DAA38B507761A657AEC92DF4CC`。八个 READY 组件的文件哈希均已逐项核对，只有 `central_stage_10_terminal` 仍为 PENDING；账本结果因此保持 `PENDING`，不能生成 9/9 最终签收 manifest。

代表性终态存档仍如实保留其 B1 业务状态；这不替代也不推翻 R430 独立 B1 修复门。下一步只对 Stage 10 的可达条件和最短有界来源做离线判定；未证明 source 合格前不启动下一轮 CK3，也不把单个 Stage 10 缺项扩大为永久长跑。
