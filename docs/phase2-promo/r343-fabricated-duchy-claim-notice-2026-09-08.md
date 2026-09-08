# R343 伪造公国宣称结果通知（2026-09-08）

## 实机结果

- R343 从冻结 R248 候选存档推进 cross-cycle/endgame source 路径；输入为
  `83,449,160` bytes / SHA-256
  `C7E5CA119F4DB4D9BFE738859DD5E32DEC6F9F1F804D91F9B26ED5D256E219DA`。
- 时间线在 `date_raw=53227008`、event instance `214` 暂停于此前未知的
  `court_chaplain_task.0313`；root/player/`duchy_holder` 均为 `32904`，只显示
  enabled native option `0`。
- 未知事件在选择前 RED；cleanup GREEN、failed checks 为空、最终 CK3 进程槽清空，
  原始输入存档未变。report / cleanup SHA-256 分别为
  `AB0A34BBB291330663CBA4D435AA2D34A33ACF10B482E403520F8BB1E04D7A81` / 
  `14A6B603DFC95A2FD813F769D27457079D163D1B947617EA353BE0AA7420FCEF`。

## 精确原版合同

该事件虽位于 `court_chaplain_task` namespace，但不是改宗或 faith 策略。CK3 1.19.0.6
原版 `events/councillor_task_events/court_chaplain_task_events.txt` SHA-256 为
`89C83B76EE40DCE0C78FCEA0C5B0A42407568EF760343C9DCC41635906DC423C`：
上游 `.0302.b` 已让第三方 claimant 支付成本、取得公国宣称并重置其 council task，随后
才向被宣称公国的 holder 发送 `.0313`。

R343 的完整 saved-scope 帧为：

- `councillor=56719`、`councillor_liege=28679`、`county_holder=30599`；
- `duchy_holder=32904`，与 root/player 相同；
- `province: province`、`county: landed_title`、`duchy: landed_title`；
- 七个 scope 名称、类型和数量完整，四名角色在本帧中两两不同；
- snapshot 与 rendered option count 都是 `1`，唯一按钮为 native `0`。

`.0313` immediate 只用 tooltip 重显已经授予的 claim；唯一 option 不再改变 claim、资源、
任务或事件链，只让玩家对 claimant 获得
`court_chaplain_fabricated_claim_opinion`。该 modifier 的原版文件 SHA-256 为
`E69C240C57D35ED5B87E7AE4DC7176FBB105D5E84863E7BCC4C473C49E5561EA`，
语义是 `-30`、decaying、10 年。合同因此只确认唯一结果按钮，完全不读取或决策
faith/doctrine/tenet/fervor/改宗字段。

## 验证与边界

- council-claim 专测 normal / `-O` 各 `1/1` GREEN；
- promotion source checkpoint runner normal / `-O` 各 `83/83` GREEN；
- `py_compile` GREEN；
- 并行只读原版审计与实现逐项一致，未启动第二个 CK3；
- 修复 commit `2023fb1df4eda0b8c7ae646e31ae114e13ec84a0` 已普通
  fast-forward push 到 `origin/master`，未 merge、未 force-push。

本轮只解除真实验收线上的政治结果通知，不扩展宗教域，也不增加业务 scene、definition、
stage 或宣传素材计数。canonical source registry 仍为 `3/4`，R344 继续
`capture_cross_cycle_endgame`。
