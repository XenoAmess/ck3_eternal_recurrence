# 有界战争观察的独立 producer

`src/war_ai_promo/wartime_bundle.py` 只读已完成录像及 CASE-W 控制器的原始记录，另建
`war-ai-promo.bounded-wartime-observation.v1` bundle。它不启动 CK3、不操纵窗口、不录制、不改旧 attempt。
旧 paused-map producer 的同日要求保留；只有共用的录制完成检查和 PTS 抽帧入口增加可选验证器注入，默认行为不变。

开始和结束读回必须为暂停、同一 exact CK3 1.19.0.6、原版独立 profile、run/PID/generation/episode/actor，
结束日期必须增加。画面两端另有实际审图，期间保留原始查询、提交/返回时间、推进记录和操作者命令。
原生查询的 `unavailable`、`ready=false` 或互相冲突字段原样保全，不将它们解释为研究已闭合。

## 实际入口

先用既有 `package_gameplay_bundle.py probe-frames` 得到 raw 精确绑定的实际 PTS 报告。
动态录制器的初始快照是 `{at, body}` 投影，不冒充 MCP `CALL_COMPLETED`；动态入口负责识别该原始 shape。
以下命令中的路径需替换成实际新目录，不得覆写旧提取或失败 attempt：

```text
tools\.venv\Scripts\python.exe -B promo/ck3_native_war_ai/integration/package_wartime_bundle.py extract-frames --recording-dir <completed-recording> --frame-probe <frame-timestamps.json> --begin-seconds <actual-begin> --end-seconds <supported-exclusive-end> --output <new-extraction>
tools\.venv\Scripts\python.exe -B promo/ck3_native_war_ai/integration/package_wartime_bundle.py package --recording-dir <completed-recording> --case-dir <case-evidence> --session-dir <owning-session> --snapshot-after <completed-native-snapshot.json> --snapshot-pointer /body --review-json <actual-review.json> --recorder-script <actual-recorder.py> --operator-script <actual-case-controller.py> --output <new-bundle>
```

`extract-frames` 只产出 `pending-agent-image-review`，不形成 GREEN。端点是实际存在的 PTS，
结束边界为排他边界；不得用 metadata FPS 推算不存在的帧。VFR 原片不变，30fps 成片采样由现有导入器负责，
不能声称提高了源观察精度。

输入目录采用已经运行的 CASE-W 控制器约定：

- `recording-dir`：原始 `recording-{precondition,command,result}.json`、`snapshot-before.json`、
  `start-readback.json`、`foreground-monitor.json`、probe、首末桌面图、原始 MKV、stop 记录和 stdio。
- `session-dir`：`live-run-identity.json`、`preflight.json`、`command.json`、`session.jsonl`；
  case 引用的请求和返回必须来自该 session 的 `recovery-requests/`、`recovery-requests-responses/`。
  不扫描 shadercache 或任意其他存档目录。
- `case-dir`：各 `*.submitted.json`/`*.received.json` 原件；恰好一次 declaration、raise、move 的
  `<kind>-intent.json` 和 `<kind>-result.json`；一轮或多轮 `advance-*.json`；实际查询、观察和结束存档收据。
  成功动作同时检查精确请求/返回及后置 war/army/route，不把 `submitted` 当后果。
- `snapshot-after`：录像结束之后的真实 `CALL_COMPLETED` 快照；默认为 `/body`，允许显式 JSON pointer。
  最终日期必须等于最后一个推进片段的结束日期；完整原始推进时间保留，不只保存汇总天数。

## 实际图像审阅 JSON

由真正查看过两张提取图的人或 root 执行者填写实际观察。当前仅支持 agent 图像审阅，不产出人工成片签核。
所有 binding 都是实际 `path`、`bytes`、`sha256`；不能用示例值作运行输入。

```json
{
  "schema": "ck3-war-ai.wartime-frame-review.v1",
  "reviewer": {"kind": "agent", "id": "/root"},
  "reviewed_at_utc": "<actual timezone-aware time>",
  "review_scope": "endpoint-images-and-sampled-foreground",
  "span_id": "case-w-observation",
  "extraction": {"path": "<actual extraction.json>", "bytes": 0, "sha256": "<actual>"},
  "frames": [
    {"phase": "begin", "image": {"path": "<actual begin.png>", "bytes": 0, "sha256": "<actual>"}, "observations": {"gameplay_hud": true, "paused_map": true, "no_loading": true, "no_foreign_overlay": true}, "notes": "<actual inspected content>"},
    {"phase": "end", "image": {"path": "<actual end.png>", "bytes": 0, "sha256": "<actual>"}, "observations": {"gameplay_hud": true, "paused_map": true, "no_loading": true, "no_foreign_overlay": true}, "notes": "<actual inspected content>"}
  ],
  "native_readback": {"association": "bounded-wartime-not-frame-synchronized", "notes": "<actual relationship and limitations>"},
  "native_ai_causality_verified": false,
  "human_1x_review_performed": false,
  "signoff_granted": false,
  "frame_synchronous_query_proven": false,
  "continuous_visual_review_performed": false,
  "natural_ai_declaration_proven": false,
  "complete_target_score_causality_proven": false,
  "narrow_query_ready_conflicts_resolved": false
}
```

封装复制全部录制/case 原件、显式引用的请求/返回与精确 binding 依赖，再写来源映射、report、timeline、index，
最后调用现有只读 CK3 adapter。操作者 marks 保留 wall/monotonic 时间和相对启动时间，不转换成伪精确媒体 PTS；
只有审阅图像的实际 PTS 定义 clean span。结束 stop 的 wall-clock 也不冒充视频末帧时间。

GREEN 仅表示本 producer 的可导入有界观察证据；不证明自然 AI 宣战、完整目标评分因果、接战、连续每帧安全或人工 1× 成片签核。
所属 session 的旧 RED 不改写。缺证据在封装前拒绝；复制中失败保留已写资产和 `failure.json`，重跑换新目录。
