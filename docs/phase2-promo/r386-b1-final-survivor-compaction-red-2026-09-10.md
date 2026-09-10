# R386 B1 final-survivor compaction 产品 RED

## 判决

R386 证明 R384 的持久名单计数修复有效：B1 从 state 3 推进到 state 7，并在完整 74 人域上得到
`target=recount=22/45/7`。但最后一条 `.122` reopen 回调到达时又有一个 weak Character row 失效；
resolver prune 后把 roster/processing 从 74 压到 73，却未重验 quota/agenda，仍然发奖并发布 state 8。
这是产品一致性 RED。随后出现的 `requires a paused snapshot` 是独立的只读 probe 发布竞态（harness RED），
不能覆盖或降低产品 RED。

## 不可变证据

- 唯一实机轮次：R386 / PID `108812` / connection generation `1`；R385 warm-up PID `58692` 已死亡。
- GREEN 前态：`date_raw=53587608`，state 7 / closure 1，roster=processing=agenda=74，
  target=recount=`22/45/7`，generation=1，无 quota anomaly。
- RED 终态：`date_raw=53587920..53588400`，state 8 / closure 4 / finalized / rewards，
  roster=processing=73、agenda=74，target=recount 仍为 `22/45/7=74`；持续出现
  `quota_target_processing_mismatch` 与 `quota_recount_processing_mismatch`。
- `debug.log` 在最后一条 reopen callback 内按顺序记录 prune → finish → publish；scoreboard 同时以固定
  `max=80` 排序 73 行持久名单并产生 range error。
- report：`_runtime/p2r385-b1-roster-fix-live/r386-b1-one-row-drift-red-report.json`，SHA-256
  `9C40F1B9D74C18B718F0A6CC9C4D39F8663BC7FB583CC6BED2D410B8305DE255`。
- park：`_runtime/p2r385-b1-roster-fix-live/r386-b1-one-row-drift-red-park.json`，SHA-256
  `CB2C1F1AA4383B940D0AB85D1E8225CCE2550E2A52EEA799CF9073EF563EE3ED`。
- driver state：SHA-256
  `FF5321591D026382B8751E36608A1462806D4E0667CDCA001D63E8497E3854AA`。

## 最小修复合同

最后一个 reopen barrier 已经满足 `pending=0` 且 `processed=expected`，因此允许只压缩已失效 row，
不丢弃其余 73 人的合法结果，也不因非绩效事件重排幸存者：

1. resolver prune 后先重计幸存档位；发生最终 row loss 时把 target 收敛到幸存者实际 recount。
2. 不调用 state-5 quota rebuild、不调用 rerank、不写 `pending_grade`，也不递增 rebuild generation；只递增
   quota book revision，并把 roster amendment receipt 收口到当前 audit version。
3. 以 pruned `processing_subjects` 为唯一域重建 `agenda_subjects`、agenda 数量、reviewed/skipped/changed/minutes
   与 hash；保留幸存者原 `processing_order`，使 M360 的 member hash 使用同一域。
4. 重封 board/reward hash、checksum 和 pending reward expected count，再运行 conservation。
5. 只有 subject=processing、quota 守恒，且非禁用 agenda 的 reviewed+skipped=agenda=processing 时才允许 finish；
   否则保持 state 7 RED，不发奖、不发布。
6. scoreboard 的持久 roster 排序上限改为当前 `zg361_cohort_n` 并最高钳制 80，禁止固定 80 越过实际长度。
7. Python probe 仅精确接受 `native ZhongGuo B1-cycle query requires a paused snapshot` 作为最多四次、零状态写的
   publication rebind；稳定四次仍 RED，未知错误立即 RED。

当前修复只到 `static-ready`。生成器、B1 双模式、quota model 双模式、B1 MCP contract 双模式、scoreboard
双模式、本地静态与 release 9/9 / reproducible check 均已通过；deterministic ZIP SHA-256 为
`c55b9e32cd69918e052ad96af73942dfda6b26cf024f34b255c6d44b91ea40f0`（manifest 含 source revision，随最终
commit 改写，不在同一 commit 内自指冻结）。游戏脚本变化要求清理 R386 后从同一冻结
checkpoint 启动递增新轮次 fresh replay。
公共 MCP schema/API/ABI 未变，open_kaishek 为 `NO-CODE-CHANGE`。T0 P1 未签收，P2 视频硬锁未触碰。
