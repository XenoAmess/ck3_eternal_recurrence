# R465 `.1030` 实机关闭与 Stage 10 source 淘汰

日期：2026-09-12（Asia/Shanghai）

## 结论

R464 只执行 frontend warmup 并完成清理；R465 是唯一 gameplay 进程，PID `134852`、connection generation `1`。它从 R463 的 partial checkpoint `3F8629957AA0DC9002AB97417E450167B23708BB2B7492CBE00189C913CE09C4` 冷启动，未重放此前 110 天前缀。

`tgp_japan_yearly_events.1030` 的 authored1/native0 选择已通过实机 postcondition：旧 instance `343` 消失，active event 变为空，snapshot `native:3 -> native:4`、revision `4 -> 5`。因此 R463 的合同 RED 已关闭为 `production-live primitive`；选择前 RED 继续作为历史证据保留。

该存档随后没有在原始 120 游戏日边界的剩余 10 日内出现 Stage 10 `zg361cl.390`。没有签发 Stage 10 source receipt，也没有进入 Stage 11。此 source 按既定上限淘汰，P1 仍为 `6/9 = 66.7%`，P2 最终宣传视频保持 `LOCKED`。

## 证据

- 激活：`_runtime/p1-stage10-r463-partial-r464-r465-20260912/activation.json`，SHA-256 `38C93157FD3B1D73D6F6BA7FE73EA5F803EC77061BB875C279F43746D4852D40`；`max_advance_days=10`，声明绝对截止 `53219880`。
- R465 RED：`live-artifacts/terminal-stages-red.json`，92,865 bytes，SHA-256 `665CC017AA69346C352D3EBC36A6A1F49721F763EADE2348BDEFC9DEEFCA814F`。其中 `.1030` drain 为 GREEN，source route 因窗口耗尽为 RED。
- R465 最后观测日期为 `53219928`，比声明绝对截止晚 48 raw hours。原因是 speed-5 轮询在下一次 snapshot 被检查前跨过截止点；这是有实证的 harness 边界缺口，不能把该轮描述为“精确停在 10 日”。它没有改变 source 淘汰结论，但后续 source 路由必须先用最小修复避免再次越界。
- canonical cleanup：`live-artifacts/09_phase2_native_session_cleanup.json`，32,162 bytes，SHA-256 `6EF78586BADC85832DE610D0546D1EB5E53C85A311DDF6CA0FA73A22B9FA0F2C`。
- managed cleanup：`live-artifacts/terminal-stages-managed-cleanup.json`，33,765 bytes，SHA-256 `81E254D42A8AFAD609915C46BA16F5E99802E0E02E09BC5C5B353F32DC512190`。

两份 cleanup 均为 GREEN；当前轮次 R465 已终止，旧轮次 R464 已终止，CK3=0，Operator MCP=0。没有触碰视频物料。

## 影响面

本轮没有 DLL、游戏文件、启动配置、加载顺序或公共 MCP schema 变化。`.1030` 的新 postcondition observation 已加入现有只读 portable evidence bundle：281 个 evidence / 1,087 个 references，manifest SHA-256 `B9910108273AB057E4FC246E89FCE303D65C2986C42B8CF33ACC016CEC694D55`。open_kaishek 只需同步内容数量和 live 状态，不需要 Java 或 CK3 重测。
