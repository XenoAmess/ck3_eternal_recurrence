# R485/R486 Stage 10 单玩家来源捕获 GREEN

## 结论

旧轮次 R485 完成 frontend warmup 并清理后，当前轮次 R486 作为唯一 gameplay 实例从已准入的 R159 单玩家 checkpoint 恢复。exact-build MCP 在同一 paused frame 将玩家从天朝 owner `32904` 原生切换为直属玩家经理 `29037`，随后重新确认其直属上级、爵位、政府和游戏规则，并原生保存新的单玩家 checkpoint。整个动作 `date_raw=53154120` 不变，没有 fixture、控制台、OCR 或坐标输入。

`zg361_stage10_player_source_capture_v1` 因而达到 production-live GREEN。它只关闭 Stage 10 v3 admission 的来源前置，不替代 `.120` 产品验收；T0 P1 仍为 `8/9`，P2 最终宣传视频继续 `LOCKED`。

## 实机绑定

- 旧轮次 R485 warmup PID `40656`，完成 Frontend 门后由受管生命周期清理；当前轮次 R486 gameplay PID `56316`，connection generation `1`。两者没有重叠。
- source binding：玩家 `32904`，paused/map-ready，`date_raw=53154120`。
- target binding：玩家经理 `29037`，直属上级 `32904`，非独立，primary tier `4`，`celestial_government`，规则含 `zg361_on`，同一 PID/connection/date。
- 原生保存 checkpoint：`62,103,190` bytes，SHA-256 `C11AFCF42FD431612F57916CD8B7C5FD053C8686B06C3376CB3F661862421BFA`。
- MCP cleanup 请求 `r485-r486-stage10-source-cleanup-1` 只发送一次。canonical/managed cleanup 均 GREEN；当前轮次 R486 与旧轮次 R485 均已终止，CK3、Operator MCP 和端口 `12439` 为零。

## 离线复核与通用资产增量

通用 topology 检查器对新 checkpoint 给出 `meta_number_of_players=1`、唯一 `played_character/current=29037`、`offline_single_player_ready=true`，并复核 `29037 -> 32904`。为了满足 v3 receipt 对真实直属有地封臣 ID 的要求，检查器在既有 count 旁增加排序后的 `direct_landed_vassal_character_ids`；本来源为 `[26268, 26936, 27051, 27963, 28088, 28216, 29575, 30594]`。normal/optimized 解析测试各 `2/2` GREEN。

这一字段来自同一次通用 save 拓扑解析，不绑定 R486、账号或机器；离线结果仍只用于 prelaunch admission，不能替代 exact-build live MCP。

## 冻结证据

运行目录：`Z:\ck3_mod_rewrite\_runtime\p1-stage10-source-capture-r485-r486-4c49425-20260912`

| artifact | SHA-256 |
|---|---|
| native session start | `7F1E725A6899E589FDEB5BE0EB545AAC4EF851EA5F297174CBD4F6D4181DBC16` |
| native readiness GREEN | `802F9908F6C86DE20830882BD25C2DF8C9A8E8A0551855A5ED05922BE1EA8DF5` |
| loader gate GREEN | `9159212F3B540BC32F518BC893434208A8FE997E75BA61C7C1C9BDB7A38FB06F` |
| live source GREEN | `EFCFE5DD5545C190E045A07D7DBEA0B5B23CC5B2AC6CB1949D77C01FC0FAE2CA` |
| player-manager checkpoint | `C11AFCF42FD431612F57916CD8B7C5FD053C8686B06C3376CB3F661862421BFA` |
| offline topology GREEN | `43B163CA95F9D82BBB91BE67096D64E12D349A8FC7EBB8B7D48EB66185726B17` |
| canonical cleanup GREEN | `29DA6E8F9475F1C5C5C8A513ECC44F366BC455C6CFE3614E8809B994FDF34321` |
| managed cleanup GREEN | `38C1EA15CDEA8D0E72ECABA636C2CC7ED97039B8DB030EFEC665CEE78CEDE498` |

