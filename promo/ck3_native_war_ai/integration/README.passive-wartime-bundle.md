# CASE-C 被动战时录像封装器

`passive_wartime_bundle.py` 是 CASE-C 独立只读 producer。它验证 R0005 同一游戏/进程/连接代/episode/玩家和 War4，68次正式快照、31个日期、30游戏日、3条被接受的 `set-speed-2 / resume-map / pause-map` 命令，以及因人物互动停止后的暂停读回。它核对原生命令历史无本窗口新宣战、招兵或移动；没有 `in_combat` 信号和实际 CombatID。这个结果只指该有限抽样窗口。

73条正式调用按原始 UTC 与 monotonic 双时间戳分相：**录像启动前**只有一次只读快照和一次 capabilities 查询，均须在启动前完成；**录像内**有71条调用，其中67次快照。录像内首帧正式快照须与 `observation-started.json` 绑定。准备调用仍保留其精确来源，但标记为 `pre-record-preparation`，不能当作录入视频的行为；任何跨越录像启动时刻的调用或双时间戳归属不一致都会拒绝封装。结果保留 `case-c-bundle-r1` 的失败证据，修订版应输出到新目录。

它复用 CASE-W 的完成录制、会话归属及正式请求响应原语；CASE-W producer 和旧暂停地图 producer 均不需要改动。原始录像、旧 RED、r1/r2 计划不变。封装只接受真正检查过的两张实际 PTS 端点图像，按选定的排他时间边界声明可用片段。日期推进及截图时间没有精确同帧映射；原录像有较长暂停等待，整段不能自动当作连续战斗画面。

先由现有 `package_gameplay_bundle.py probe-frames` 对原始录像生成精确 PTS 报告，再选实际存在的帧范围：

```text
tools\.venv\Scripts\python.exe -B promo/ck3_native_war_ai/integration/package_passive_wartime_bundle.py extract-frames --recording-dir <case-c-r1-recording> --frame-probe <frame-timestamps.json> --begin-seconds <begin> --end-seconds <exclusive-end> --output <new-extraction>
```

此命令只生成 `pending-agent-image-review`。root 实际查看首末图后，以新路径写一份下列 review JSON，再封装：

```text
tools\.venv\Scripts\python.exe -B promo/ck3_native_war_ai/integration/package_passive_wartime_bundle.py package --recording-dir <case-c-r1-recording> --case-dir <case-c-r1> --session-dir <capture-live-live-r5> --review-json <actual-review.json> --recorder-script <ck3_war_record_case_c_20260923.py> --operator-script <ck3_war_case_c_operate_20260923.py> --output <new-bundle>
```

review 必须使用 `ck3-war-ai.passive-wartime-frame-review.v1`，`reviewer.kind=agent`，`review_scope=endpoint-images-and-sampled-foreground`，合法的唯一 `span_id`，以及 `reviewed_at_utc`。`extraction` 和 `frames[].image` 均为 `{path,bytes,sha256}` 实值；两帧各需 `phase=begin/end`、具体 `notes`，以及实际看到的 `gameplay_hud=true`、`visible_war_map=true`、`no_loading=true`、`no_foreign_overlay=true`、`paused_map=true/false`。两端可以有不同暂停状态，不得猜测。`native_readback.association` 固定为 `bounded-passive-wartime-not-frame-synchronized`，另附解释性 `notes`。

review 的下列布尔值全部显式填 `false`：`native_ai_causality_verified`、`human_1x_review_performed`、`signoff_granted`、`frame_synchronous_query_proven`、`continuous_visual_review_performed`、`natural_ai_declaration_proven`、`complete_target_score_causality_proven`、`narrow_query_ready_conflicts_resolved`、`actual_combat_id_bound`、`native_battle_result_proven`、`new_operator_war_order_in_case`。这些字段是严格限制，不是由审图推断出的原生行为。

封装成功后的 GREEN 只表示所选片段的文件完整性、两端实际审图、会话身份和有界原生读回符合此 producer 合同。未完成审图时不得调用 `package`，本开发包没有制作实际 GREEN bundle，也不构成人工1×观片或成片签核。封装失败时保留输出目录及 `failure.json`，重试必须用新目录。
