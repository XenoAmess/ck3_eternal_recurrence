# R177：可重复 TGP 军事援助通知

- 同一 CK3 PID `68028`、重启 `0`，从 `date_raw=53159208` 推进至
  `53162688`；产品运行时阻断诊断数为 `0`。
- 已精确排空 `death_management.1000`、`ep3_emperor_yearly.2240`、
  `tgp_interaction_event.0015`、`birth.1010`、`tgp_decision_events.0101`。
- B1 在所有已观测帧持续 active；尚未到 Central/PP。
- `tgp_interaction_event.0015` 由可重复的原版军事援助互动触发。R177 同一
  bounded reconnect 内出现第二次，而旧合同每客户端只允许 1 次，因此在
  第二次通知处 fail-closed；累计 lineage 中这是第 3 次。
- 合同已迁至单用途 TGP 军事援助文件，实证上限改为每 bounded reconnect
  2 次。事件只有一个纯确认选项；仍逐次绑定完整 7-scope 身份后才提交。

证据：`Z:\p2r177promo_resume\report.json`。
