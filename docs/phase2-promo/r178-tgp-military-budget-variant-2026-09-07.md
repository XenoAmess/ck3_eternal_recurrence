# R178：TGP 军事预算续期变体

- 同一 CK3 PID `68028`、重启 `0`，先精确排空累计第 3 次
  `tgp_interaction_event.0015`，随后在 `date_raw=53163168` 停于
  `tgp_china_ministry.0100`。
- 当前帧精确 scope：`treasury_ruler=32904`、`steward` 为第三方角色、
  `military_budget=32904`。旧合同只记录了 `salary_budget`。
- 原版 exact-build 源在此位置明确列出 6 个互斥偏好名：celestial 的
  salary/ministry/military/hegemon，以及 meritocratic 的 salary/military。
  合同逐名列出这些变体，固定 authored option 2 / native index 1 以维持
  当前预算并终止事件，不接受任意 scope 名。
- 合同已迁至单用途财政部文件。聚焦测试同时发现并修复 manager reconnect
  没有递归重绑定 `scope_variants.character_scopes` 的 harness 缺口。
- 产品运行时阻断诊断数为 `0`；B1 仍 active，Central/PP 尚未 active。

证据：`Z:\p2r178promo_resume\report.json`。
