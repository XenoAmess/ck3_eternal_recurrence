# R293–R294 promotion source 实机捕获（2026-09-08）

## 结论

R294b 已从 fresh product 的真实 `zg361pp.147` paused frame 捕获 promotion/compensation 来源存档。捕获结果为 `GREEN / captured-real-promotion-source`，使用 CK3 1.19.0.6、玩家 `32904`、同一 final PID `150452`，全过程 restart `0`、fixture/OCR/坐标/控制台均未使用，捕获窗口的增量 blocking diagnostic 为 `0`。

canonical source registry 因此由 `0/4` 推进为 `1/4`。仍缺 `capture_projects_metrics`、`capture_incidents_operations` 与 `capture_cross_cycle_endgame`，所以 registry 仍不 ready，T0-P1 也仍未完成；该证据不能解锁最终宣传视频。

## R293：真实产品 RED 与最小修复

- R293 在同一产品时间线上完成 B1 closure，并把 `zg361.5` 55-scope exact contract 纳入已知事件；tooltip scratch 旧错误保持为零。
- 继续推进到 `zg361pp.146` 后，真实 tooltip/description 产生三条阻断诊断：`zg361_pp_m146_receipt_owner` 缺失、由其取得的 scope link 未设置、比较右值无效。R293 generation 末 report SHA-256 为 `54CEFE2A28E5CD38946A4F80A03AE6595489FAB37D94335FBC3DB58C587F2D49`。
- checkpoint 冻结在 `.146`、date raw `53245488`、player `32904`、event instance `271`；89,423,360 bytes，SHA-256 `4F88450951055FD588194785F39E007B181CE119A0FD40C3DB10FB493CFF5AE4`。
- 根因不是 Route C 回执写入，而是 46 个 mechanism consumer 在 tooltip 上下文内先把可能不存在的 `var:receipt_*` 传给 full guard。生成器现把五元组存在性检查放进 lazy `trigger_if`，只有五项都存在才调用 full guard；否则严格返回 false。
- 49 个生成产物重建，25 个 lifecycle shard 有预期变化；runtime normal/`-O` 各 `66/66`、generator check、`validate_local.py`、release test `9/9` 与 1,031-file reproducible build 均 GREEN。修复提交 `0188395` 已推送。

## R294：fresh product 恢复与 harness 修复

- fresh projection 为 `phase2-full-release-r294-0188395`，共 1,031 files；projection manifest SHA-256 `2EAF07360C4B111157B4C00BE787C2F05D96E7DD493FD6C3A50040A30FD9574D`，ZIP SHA-256 `6A8E5747929D86A24B237B56DDE812DC169475DBD65B4D006372D44FE1E6EB27`。
- 首次 R294 已证明 `.146` 的 receipt-owner 三条旧诊断在 fresh product 中归零，但 production entry 把可恢复的初始 `.146` 错误拒绝。`bde61ea` 令入口接受 `.146`、已知中断和 clean-boundary special event，仍不接受未知事件。
- R294b 使用唯一 final PID `150452` 恢复上述 `.146` checkpoint，loader 与产品门均 GREEN；选择 option 1 后在 D+1 到达真实 paused `.147`，date raw `53245512`、event instance `272`、player `32904`。initial report SHA-256 `C184122C7B8C47C65BCED920C65B9F608CC29A3AD3D5D5809F2A74B2D91E81CB`。
- 第一次 reconnect 的唯一 RED 是 lineage 写成非 canonical session kind；`63337e7` 改回 `managed_product_session`。第二次 reconnect 的唯一 RED 是原生保存发布新的 snapshot/revision，被捕获器误判为跨帧；`4d7f24e` 允许 revision/native revision 单调前进，但继续冻结 date、player、generation、event instance 与 option count。正向同事件 revision 前进和反向事件漂移测试在 normal/`-O` 均 GREEN。

## 最终 capture artifact

- artifact：`_runtime/p2r294bresume3/04_promotion_source_checkpoint_capture_v2.json`
- artifact SHA-256：`75CB49FD38FAD0D28923D08452FD73B1CF7CCDB049066B528B46FC6B86E63AC8`
- resume report SHA-256：`6DA96F9094BC02D957DD0CA9CBA466D458CE5034E4322C9A16418FC560672003`
- archived checkpoint：`_runtime/p2r294bresume3/promotion-source-checkpoints/01-phase2-promotion-compensation-zg361pp-147-d4f625c84e900966.ck3`
- checkpoint：89,342,845 bytes；SHA-256 `D4F625C84E900966E0B70CA8FD65CD33D63205B479A3CBC15BC0DF4B02B319F0`
- source/post-save revision：`2 -> 3`；date/player/event instance 保持 `53245512 / 32904 / 272`。
- captured handler：`capture_promotion_compensation`；missing handlers：其余三项。

## 清理与边界

CK3 已通过 native session stop queue 正常退出，PID `150452` 与外层恢复进程 `204504` 均已消失，实时 CK3/injector 槽为空。没有强制杀进程。

本轮捕获推进的是 registry evidence，而不是新的 strict business scene 或 full-tree stage；因此 T0 `50%`、strict `4/361`、full-tree definitions `106/626`、stage `8/11`、T1 `90%`、T2 current horizon `100%` 与总体 `67.5%` 保持不变。宣传 footage `0/8`、MP4 `0/2`；T0-P2 继续 `LOCKED`。

下一工作包是从 canonical 顺序的第二项 `capture_projects_metrics` 开始，先复用现有 provider/assembler 合同建立 no-launch readiness，再串行取得对应真实 paused source frame。
