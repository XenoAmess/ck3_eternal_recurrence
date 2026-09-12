# R487/R488 Stage 10 固定尾链边界 RED 与最小修正

## 结论

旧轮次 R487 完成 frontend warmup 并终止后，当前轮次 R488 作为唯一 gameplay 实例恢复了已准入的单玩家经理来源。loader、exact-build native readiness、产品加载和运行时错误扫描均为 GREEN；玩家 `29037`、直属上级 `32904`、tier 4、celestial government 与 `zg361_on` 绑定一致。

单次动作从 `date_raw=53154120` 推进到原 30 日绝对截止 `53154840`，11 次暂停采样都显示 B1 active、Central/PP inactive，`zg361mg.120` 未出现，因此按合同保留 RED。没有 retry，也没有延长本次运行。

这不是新的 mod 产品故障。exact source 的离线事件队列显示当前日期 `1067.10.28`、玩家经理 `29037` 的 `zg361b1.102` 已排在 `1067.10.29`，即 B1 D+299 边界。产品定义随后还固定经过 `.103 +30d`、公共上级合账、经理公示回调和 F100/F101/F102/F103/`.120` 的逐日票据。原 30 日上限必然先于这条固定尾链结束，根因是 Stage 10 验收编排边界过短。

## 最小修正

- Stage 10 action 的绝对上限改为 **45 游戏日**。这个上限只覆盖冻结来源已经证明存在的 D+299 固定尾链；不恢复 400 日 B1 重跑，也不允许原地 retry。
- source receipt 升为 `zg361_stage10_player_publication_source_v4`。除 v3 的单玩家、拓扑、MCP 原生保存和产品树绑定外，还必须绑定本次 live RED 的初始 `B1=true / Central=false / PP=false / review-now=false`，以及 exact checkpoint 中玩家经理次日 `.102` 的离线队列证据。
- 新增通用只读工具 `tools/inspect_ck3_save_scheduled_events.py`。调用者提供任意 CK3 save 或 melted save、可选事件前缀和 root CharacterID；输出版本化队列、绝对日期、相对天数和输入哈希。结果明确是 prelaunch-only，不能代替 exact-build MCP 或产品后置条件。
- mod 游戏脚本、DLL、公共 gameplay MCP、Operator MCP 1.1、启动参数和加载顺序均未改变。

聚焦验证为 scheduled-event parser、Stage 10 action、Stage 10 operator 合计 normal/optimized 各 `10/10`，相关文件 `py_compile` 与 `git diff --check` GREEN。没有运行全量测试。

## 冻结证据

运行目录：`Z:\ck3_mod_rewrite\_runtime\p1-stage10-player-publication-r487-r488-fec55f8-20260912`

| artifact | SHA-256 |
|---|---|
| product projection manifest | `6BD1867A037CD2F30888A217E44F732A2B769D8E8EC801365E1B5FBB433D1CD3` |
| product tree | `B5C0ED99F0C87507E1B8D5DF7E48B96EDDD69DCD57908C0A2CF5D057404B5404` |
| loader gate GREEN | `514EA96FCB7600CD4F0B5EB6FB05763D060FFCB4A97603DCC7B87A56AB5C0390` |
| Stage 10 direct RED | `50BBD1202C49E4549FD4CECF1DD9CD4DB28DC84599C81A1F2B6ACE07A2D965E3` |
| managed Stage 10 RED | `06E7859BD69D80EF6C10AB499E06A1D29FBDC71613CCCFB8B5AF16F09CD1F8EA` |
| canonical cleanup GREEN | `A6D58DA686F4D9446966BF0C1A350AB91271BE403CAB17A48C817DE91A90A3E9` |
| managed cleanup GREEN | `328D8EE9DA13E83BBCC0BCB9950EEEA69A2B52715C48C8A9CF0CC052ACB9924C` |
| generic scheduled-event report | `FBE10CF5B5BCF9684E8569883CFEC0C9E7B362458C5683FBFF8B40B891B79D44` |
| v4 source receipt | `6202B129D962D3001045CB3912F05FC5BA6274647CEED260676F9134EA26047E` |

MCP cleanup request `r487-r488-stage10-cleanup-1` 只提交一次并返回 ACCEPTED；canonical/managed cleanup 均 GREEN。当前轮次 R488 与旧轮次 R487 均已终止，CK3、作业进程、Operator MCP 和端口 `12440` 全部为零。

P1 仍为 **`8/9 = 88.9%`**，唯一缺口仍是 `.120` 的 production-live terminal；P2 最终宣传视频继续 `LOCKED`。下一次启动必须使用 v4 receipt，在递增的新轮次中只执行一次 45 日绝对上限场景。
