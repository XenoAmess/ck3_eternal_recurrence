# R146 同日 GUI 激活脉冲（2026-09-06）

## 实机结果

- frozen source：`7e45c5beff64976a2dfbc4d9b466f7c413da74da`；源码 ZIP SHA-256：`D12FC874B2BFA260B3AAF5B655CB0EB2F5611EFE59DB33CB896F09B7054594D8`。
- no-launch preflight GREEN；R130 产品投影和关键 B2 effect 字节等价门保持 GREEN。
- CK3 PID `187940`、玩家 `32904`、默认 5 速、存活保护一次；未发生 owner terminal。
- runner 再次完成两个朝贡窗口的 exact drain，并在 `date_raw=53154144` 取得 B1/Central/PP 全 false、review-now true 的 clean boundary。
- clean-entry scripted GUI 已具备 loaded-fixture modifier 栅栏，但在暂停状态等待 1 秒仍未产生 `zga_phase2_manager_seed.1`。
- `manager-cycle-recovery.json` SHA-256：`B45240E26AD519DD5B88FA65224B54F732B26CD3C9CF323653314D4BE3DC24F1`。
- `runner-report.json` SHA-256：`689918BF9A7388F8E2F73E0CC7E8FDB396A0B9CAC2F6E03710267E7F71588865`。

这排除了“仅仅是存档产品 flag 恢复前提前消费 state”作为完整解释。连续 R145/R146 证明：该 invisible GUI scripted state 在 clean 条件成立后仍需要至少一个运行帧，纯暂停 wall-clock 等待不会执行其 `on_start`。

## R147 runner 修改

fixture 与 R130 产品字节保持不变。seed-capture runner 在 clean boundary 先暂停等待 1 秒；若仍无事件，只发送一次 `resume-map` 作为 GUI activation pulse，并保持 speed 5。安全边界不是 Python 猜测：`maximum_date_raw` 与 `expected_event_date_raw` 都绑定刚刚实证的 clean date；只有 `zga_phase2_manager_seed.1` 在同一日期出现才可继续，任何日期增长都会由既有 maximum-date gate 立即暂停并 RED。

该脉冲会写入 `manager_continuation_activation_pulse_started` 证据，包含 date、speed、same-date-required 与 exact event key。它只解决验收夹具的 UI update 时机，不触发产品 review、不清理产品变量、不写产品 receipt。
