# R543–R545 manager source hidden-modal contract RED（2026-09-12）

## 结论

R543/PID `93664` 完成 Frontend warm-up 并清理，R544/PID `153636` 完成
前两个 clean spans。canonical player-manager source restore 随后正确回收 R544，
以同一 pipe 启动 R545/PID `89520`，证明 R542 暴露的 typed ACK 修复已生效。

R545 在任何 Stage 10 动作前停于 `scoreboard_visibility_provider_unavailable`。
原生响应已找到全部 15 个固定 widget，且 `zg361_scoreboard_modal` 明确为
`exists=true / effective_visible=false`；但该玩家源此时尚无 managed/received list
entry，整个业务 state/ACL 因而合法地是 `state_projection_unavailable`。source staging
只需要证明没有遮挡镜头的 modal，旧 capture helper 却把完整业务投影 READY 当成
清场前置。这是 Python capture-contract RED，不是 mod、source checkpoint 或 native
provider RED。

## 冻结证据

- plan：
  `Z:\ck3_mod_rewrite\_runtime\p2-capture-r543-r550-facb3a3-20260912\capture-plan.json`
  - `13,452` bytes
  - SHA-256 `BD64D6ACB921B9384CB48FDE52210565BF140FF709FDF882D2362F57525C69FF`
- report：
  `Z:\ck3_mod_rewrite\_runtime\p2-capture-r543-r550-facb3a3-20260912\capture\report.json`
  - `4,378,114` bytes
  - SHA-256 `702BC45CEFF33B4E5EAB344BE2651DE1CECE915745BD5EC312DCA0341EB8B959`
- restore outbox：
  `Z:\ck3_mod_rewrite\_runtime\p2-capture-r543-r550-facb3a3-20260912\capture_native_state\native-session\bridge\outbox\restore-798458d30dbd4e03ada696d3a62142b1.json`
  - SHA-256 `E4CC86A9C057C5E441DC50AFA0F43778EA1B11AC4FC23ACBE44E877B5BD78C8A`
- cleanup：
  `Z:\ck3_mod_rewrite\_runtime\p2-capture-r543-r550-facb3a3-20260912\capture\cell\09_phase2_native_session_cleanup.json`
  - `34,180` bytes
  - SHA-256 `510432B7D43813DA693490F3430CAD3239A14FDCA9F0199CB09AB945013F8CF2`
  - `result=GREEN`、`pid_lineage=[153636,89520]`、`failed_checks=[]`；
    cleanup-only 分支诚实保留 `restart_semantics_proven=false`。

本轮 81,098,524-byte MKV 是不完整 take。前两个 clean spans 不能脱离同一完整
八段 timeline 单独计数，因此 P2 仍为 `0/8`。

## 最小修复

根仓库提交 `f566633593347994ab564df97971f7662877a9e1` 只调整录制清场 helper：

- 完整 scoreboard state `available` 时行为不变；
- 仅当 top-level reason 精确为 `state_projection_unavailable`，并且 fixed modal row
  同时证明 `exists=true` 与 boolean `effective_visible` 时，允许使用该直接可见性诊断；
- modal 缺失、exists/visible 不可读、其他 unavailable reason 仍然 RED；
- 这项放宽只服务于 source staging 和 span drain 的遮挡判断，不把业务 ACL、fingerprint、
  action readiness 或 `production_live_ready` 宣称为 GREEN。

聚焦验证为 event choreography runner normal/optimized 各 `19/19` GREEN，另有
`py_compile` 与 `git diff --check` GREEN。没有启动额外 CK3，没有修改或重建 DLL。
响应 wire、schema、工具名和 endpoint 未改变，所以不触发 open_kaishek 实现同步。

## 当前状态与下一步

R543、R544、R545、FFmpeg 与 injector 全部终止，CK3 进程库存为零。P1 保持
`9/9 GREEN`；最终视频硬锁已解除，但 P2 为 `0/8`，剪辑、导出和发布继续等待完整
素材。下一次新的有界 capture 从 R546 warm-up 开始，随后进入 R547 gameplay；
任何 source restore 启动都继续按实际轮次递增记录。
