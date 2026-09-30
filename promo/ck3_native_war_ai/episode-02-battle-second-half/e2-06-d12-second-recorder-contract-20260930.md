# E2-06 d12 第二条原片：静态接线合同

2026-09-30；基于 #451 `d921dd3a0fdf627b342959b8ec86e047a923e459` 的只读审查。本页不启动 CK3、FFmpeg，不领取屏幕，也不认证 clean span。增援章目标 461 秒不同的原速画面；第一条 600 秒容器是否足够，须在完整原片 1× 审后决定。

## 当前代码的精确边界

- `record_bounded_gameplay.py record` 接受同一 `session_output.parent` 下新的 workdir，且会把第二条 raw 重新绑定原 d11 save/sidecar、preflight、native start readback 和 Steam 离线回执；它自身不验证屏幕租约是否仍有效，也不验证第二条开始时仍暂停在 d12。脚本说明仍称一次 attempt 只录一条原片，不能把参数可运行当成 d12 第二条的正式准入。
- `remaining_live_step.py` 的 d11 `advance` 只在**第一条正在运行**时接受 `d11-before` mark；成功后返回该 run 的 d12 snapshot/control。`post_mark_case` 要求第一条自身唯一 `d12-after` mark、原始响应哈希、封口后完整 journal 和 recorder 时间界。
- `remaining_live_step.py finish` 检查 attempt 中所有 recorder 已结束，但只对传入的**第一条**调用 `post_mark_case`，随后提交 `999-e2-06-d11-finish.json` 清场。提交 finish 后不能在同一受管游戏会话补第二条。当前没有第二条独立 d12 同帧查询、mark 及封口验证器。
- d11 a09 no-launch seal 只绑定 d11 冷载与现有 helper。它不授权第二 recorder、d12 原生值、录制或日期动作。旧 J-A01 没有同 recorder battle-control，仍不计正式增援时长。

## 最小安全增量（须在新的代码 HEAD 上重新静态审）

1. **先完成第一条。** d11 `observe`、唯一 `advance` 和第一条 recorder 的 `d11-before`/`d12-after`、`recorder-final.json` 必须满足现有 `post_mark_case`。d12 `advance` 结果须为 `ONE_DAY_ADVANCED_UNREVIEWED`，日期 `53146512`；其他结果或第一条 RED 时停止。此时**不调用** `finish`。
2. **第二条录前门。** 新的 create-exclusive d12 admission 绑定第一条封口 SHA、d11 `advance` 行与 intent SHA、同一个 `session_output`、原 d11 immutable save/sidecar、同一个 native-start-readback、d11 a09 对应的新 HEAD seal，以及确证未提交 `999-...-finish.json`。它须读取当时唯一 screen lease/心跳、当前 Steam 离线原始像素与桌面几何，并由受管启动者确认 CK3 仍是同一进程、暂停在 d12、没有其他 recorder。任一条件不明即 STOP；旧 d11 静态 seal 不能代替这些实时门。
3. **第二条自己的同帧来源。** 第二 recorder 真正启动后，另取 d12 paused snapshot 与 `ck3_query_battle_control_snapshot_v1` 原始请求/响应，按 `snapshot_case`、`battle_control_case` 的 wrapper/native revision 和 snapshot ID 校核 actor `29829`、War `4`、Army `18`、Combat `16777218`、province `2633`、date_raw `53146512`。这必须是第二条 recorder 时间窗内的新查询；不可借第一条的 d12 响应。新只读 helper 须把两次请求提交与响应读回的 monotonic 时间 create-exclusive 写入第二条 observation，不能只依赖文件 mtime 或 UTC。只读查询后在第二条 journal 唯一落 `d12-only-control` mark，绑定本次 control、report、原始截图的 bytes/SHA。它不执行 `life-advance`、不启动新 private trace、不改游戏日期。
4. **第二条封口。** 在同一受管 CK3 会话内自然结束第二 raw、FFprobe 并封 `recorder-final.json`；纯只读校验须核两个 recorder 工作目录不同、时间不交叠、第二条 `recorder-start` 晚于第一条 `recorder-end`、其 intent 的 `session_output`/source/preflight/readback 与第一条同源、600 秒上限、第二条 observation 的查询时间及单个 d12 mark 的 monotonic 时间均在第二条起止界内、mark 所绑三件原件仍逐字节相等、第二条 sealed journal SHA 与 final 一致。输出只能是 `ENCODED_UNREVIEWED` 或 RED，不能宣称 clean span。然后 d11 `finish` 才可读取两条精确封口并清场；第二条 RED 也必须允许受管清场，同时保持 RED。
5. **新 no-launch。** 上述代码一旦落地，重做 `capture_session.py` 静态 preflight、d11 admission seal/verify、第二条 read-only no-launch 计划与独立负例审查。至少覆盖错 session、错/重复 recorder、第一条未封口或缺 d12 mark、第二条借用第一条 control、同帧 revision/CombatID 漂移、mark 在录制窗外、finish 已提交、journal 或原件改字节、screen lease 丢失和同一日期二次动作。旧 a09 READY 不可继承。

## 当前结论

**LIVE STOP。** 现有代码可以造第二个 MKV，但缺第二 recorder 的实时准入、同帧原生查询及 finish 中的独立封口；本次静态审查时权威屏幕任务仍由 XQOL 持有，且 #451 的 screen fence 正在独立修补。先完成这些接线及当次新鲜 Steam 离线证据，才可决定同一 CK3 会话第二条；否则从真实 d12 save/sidecar 另开冷载（若没有，就从 d11 重新开始，并重核随机结果和卡）。无论哪条路径，最终 clean span 仍须原片完整原速人工审片。
