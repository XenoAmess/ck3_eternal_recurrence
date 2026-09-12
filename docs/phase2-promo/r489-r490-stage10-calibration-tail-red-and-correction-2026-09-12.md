# R489/R490 Stage 10 校准尾链边界 RED 与修正

## 结论

旧轮次 R489 完成 frontend warmup 并终止后，当前轮次 R490 作为唯一 gameplay 实例恢复同一份合格的单玩家经理来源。loader、exact-build native readiness、产品加载、material error scan 与运行时致命错误检查均为 GREEN；玩家经理 `29037`、直属上级 `32904`、tier 4、celestial government、`zg361_on` 与 v4 receipt 完全一致。

R490 从 `date_raw=53154120` 运行到 45 游戏日绝对截止 `53155200`，共留下 16 次 progress observation；每次都为 `B1=true / Central=false / PP=false / review-now=false`，`zg361mg.120` 尚未出现，故 action 和受管 wrapper 按合同保留 RED。没有原地重试，也没有继续延长该轮。

该 RED 仍是验收边界错误，尚无证据表明 mod 产品链失败。`debug.log` 已明确记录：

- `ZG361B1: exact quota bank closed with at most one unique same-function 3+4 pool`；
- 随后进入 `ZG361B1_DIAG: human pending/reopen route evaluated`；
- 更晚出现的 `stale common-superior bank ticket ignored` 是有效关闭后的重复延迟票据；同一日志中没有 `stale manager-calibration ticket`。

因此，R490 已经跨过 R488 尚未到达的共同上级合账点。45 天仍未结束，是因为上一版固定尾链计算漏掉了产品中已经配置、且该来源实际选择的 `m142=1 / m143=1` 两段校准延迟。

## 证据化尾链上限

从冻结来源的 B1 D+299 计算最迟可达路径：

| 阶段 | 最迟相对周期日 |
|---|---:|
| 来源；`.102` 已排到次日 | D+299 |
| `.102` / 30 日 shadow | D+300 → D+330 |
| 共同上级合账 / `.111` 校准入口 | D+335 → D+336 |
| `m142=1` pending watchdog | D+367 |
| `m143=1` post-seal reopen | D+397 |
| 玩家公示回调 `.90` | D+398 |
| F100/F101/F102/F103/`.120` 五张逐日票据 | D+399 → D+403 |

所以从 D+299 来源到 `.120` 的保守产品尾链为 **104 游戏日**。action 上限修正为 **120 游戏日**，只增加 16 天的调度余量；它不恢复完整 B1、不新开周期、不允许原地 retry，也不是永久长跑。

source receipt 升为 `zg361_stage10_player_publication_source_v5`。除原有单玩家拓扑、MCP 原生保存、产品树、R488 30 日 RED 与 `.102 +1d` 离线队列外，v5 还必须 hash 绑定 R490 的 45 日 RED，并逐字段绑定上述 104/120 日尾链合同。

## 冻结证据

运行目录：`Z:\ck3_mod_rewrite\_runtime\p1-stage10-player-publication-r489-r490-e58c222-20260912`

| artifact | SHA-256 |
|---|---|
| product projection manifest | `6BD1867A037CD2F30888A217E44F732A2B769D8E8EC801365E1B5FBB433D1CD3` |
| product tree | `B5C0ED99F0C87507E1B8D5DF7E48B96EDDD69DCD57908C0A2CF5D057404B5404` |
| loader gate GREEN | `CC0210824779940201E848C6ED074C96FD00A1BE56E0A05090D856B9E2990D2E` |
| Stage 10 direct RED | `46B7370EB6E6F05A2CFE6269CA3F455EF0591F56A4F8767B3BC7A9FF5C3294FA` |
| managed Stage 10 RED | `BA650714D9418FC2294F140B4438641113CBE243FBD821AD42644B51C29D3DFC` |
| archived attempt checkpoint | `BC365D3C4F3D750E2DBEE3B09C9EF9949ECF75BA848E57242A6ED7644B037AF0` |
| live `debug.log` | `DD6D6A8AA7A66C435B7944966338D3EF3276096035341511A82FA7CE8DB3904C` |
| offline melted source | `3F284C3F7D42638A90C3F9196D220E0CBC485F068655BD2BB915DE87AC5FAC18` |
| canonical cleanup GREEN | `83CC5847973EEA71A82738958ADB114109BC14D09FAAD9FB3453F0E0DA20D695` |
| managed cleanup GREEN | `E797858A3DBEBC6DC1955F6DC071840E0F7ADBE39F849A98AA4B4065C311D314` |
| v5 source receipt | `EFEB026B1161F6D29291E033307ECA8C96EE453955549EF28710BB52FA933BF4` |

MCP handoff、`run-stage10` 与 cleanup 各只提交一次。R490 gameplay PID `206968` 与 R489 warmup PID `88292` 从未重叠；两轮现均已终止，CK3、受管作业、Operator MCP 与端口 `12441` 均为零。

P1 保持 **`8/9 = 88.9%`**，唯一缺口仍是 `.120` 的 production-live terminal；P2 最终宣传视频继续 `LOCKED`。下一次只允许使用 v5 receipt，在递增的新轮次执行一次 120 日绝对上限 Stage 10。
