# A05 M6 离线证据提取

`machine_id: xenoamess-full-tower-eb9d2c1186`；本轮实读 `tools/ck3_live_run_id.py machine`，观察时间 `2026-10-20T04:44:02.288196Z`。本包只准备离线观察工具，没有启动游戏、Task、MCP 或 RPC，没有修改 Source26 的 12 个冻结 SDK 输出。

[工具](../../tools/g2_saved_campaign/inspect_c23_a05_m6_v1.py) 26914 B，SHA-256 `8a11c462b327ded0b1b40ba4e6b47ea7e1cc83190df5e736dd3ce16b70c4d543`。13 项 RAM 检查通过：拒绝旧 UUID gain、跨 episode receipt、Game PID 不匹配、旧 following、错误 root 日期、extent SHA 变化及半行；真实 extent reader 只保留所选行，未读后缀。RAM 编译通过，不生成 pycache。

Source26 [原资格](../../tools/g2_saved_campaign/candidates/m6_reused_sway_opportunity_20261020/SOURCE-QUALIFICATION.json) 的 32 项 synthetic PASS 保留，不重复跑旧资格。复用只解除机会选择被已清除槽位阻塞的问题；新 UUID 仍需当前完整合法空槽读回，并独立取得自己的 baseline、具名 gain、自然终态与更后普通消费。

实际只重读 [closed ledger](evidence/m6-sway-closed-ledger-2026-10-20.json) 21864 B／`edfd6027bf508bda9ea9183c8820a18014192d20789f6ae929b4e0c503c63580`。工具输出保留两个独立 UUID：旧 actor31254→33946/fullID2/gen0 与 actor40526→34973/fullID83887164/gen5，各自历史 gain25；两个 terminal 和 following candidate 都为 false。后者 `storage_slot_reused=true`、终态未观察，不能补成自然完成。单独 ledger 缺少完整当前帧、Game 出生时间、episode 和 receipt source，全部保留为 binding gap。M6 未完成，G2 不新增信用。

调用 `python -B tools/g2_saved_campaign/inspect_c23_a05_m6_v1.py --self-check` 可做 RAM 检查；`--manifest <explicit.json>` 默认只输出 stdout。manifest schema 为 `xar.c23-a05.m6-inspection-manifest/v1`，须写来源 `machine_id`，可写 `campaign_id`，提供 `sources` 与 `selections`：

- JSON source：`path/format=json/closed=true/bytes/sha256/frozen_at_utc`，完整小件上限256KiB。
- JSONL source：`path/format=jsonl/closed_extent=true/offset/length/sha256/frozen_at_utc`。只读 owner 冻结的精确范围，上限8MiB，逐行上限2MiB，范围首尾必须为整行。不扫描目录，不自动发现或复制 trace。
- selection：`source/pointer/kind`，kind 为 `ledger_episode` 或 `ordinary_auto`。JSONL 另填 `line`，从该 extent 的第1行计数；pointer 使用原件实际 JSON Pointer。ordinary_auto 选返回 body，默认保留其 planning_source_frame。
- 可用 `frame/root/runtime` 分别引用原件 `{source,line?,pointer}`。runtime 对象须有 `machine_id/campaign_id/Game_pid/Game_creation_filetime`；也可用 `runtime.fields` 将这四字段逐个绑定到真实原件指针，无需复制或改写来源。

measurement 与 following 的实际帧分开选取并保留指针。root 按生产合同核 available、玩家/alive、snapshot_revision 和 date_raw；receipt 的 before/after、原生完整 instance/gen、当前 episode、Game PID/birth 均保留。工具不跨 Game 或 episode 合并，不推断自然原因、有效结果或完整 M6，也不把 `next_turn_consumed=true` 单独当消费。缺少帧或原件时保留 gap，等待原正常批次的封闭证据。

本包文件共用 Root 的 source40KiB／artifact8KiB 限额；实际 artifact 写入0。存储策略1.0.0，执行额度截止 `2026-10-20T06:30:00Z`，未续期。保留工具及此来源说明供 A05 新样本复核；复核日期 `2026-10-22T04:44:02Z`。没有删除或读取活 Driver、SAVE、原片或大 trace。
