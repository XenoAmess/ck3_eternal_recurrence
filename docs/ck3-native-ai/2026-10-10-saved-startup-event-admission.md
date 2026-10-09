# 显式只读准入存档启动事件

共享 host 原 `saved_campaign_admission_frame` 要求 `active_event is None`，使包含合法当前事件的固定存档无法进入后续 hold。现有 campaign-root service/driver 查询允许 paused active-event 帧；无需修改 native、创建 episode anchor 或跳过真实 root 查询。

新参数 `--saved-campaign-startup-case-contract <path>` 默认关闭。普通 saved campaign 继续要求无事件。显式启用后，host 仍核验 exact 1.20.0.4、单次 `-loadsave` 的实际 PID/connection、paused native actor/date/local-player、完整 owner mailbox 与完成的 snapshot observer；先取得两个相同帧且 pump epoch 递增的观测，再查询真实 campaign root 并交叉核验玩家身份。

合同使用既有 fixture startup 的精确文件 pin、重复 key 拒绝、私有模块 namespace、只向 handler 传递深拷贝及调用前后 pin 复验机制：

```json
{
  "schema": "ck3-saved-campaign-startup-case-contract-v1",
  "state_dir": "<absolute allocated state>",
  "handler": {"path": "<absolute Python source>", "bytes": 1, "sha256": "<SHA-256>", "function": "admit_saved_startup_event"},
  "dependencies": [],
  "expected": {
    "event_definition_key": "<product event key>",
    "event_instance_id": 121,
    "root_character_id": 31254,
    "actor_character_id": 31254,
    "date_raw": 37791000,
    "native_option_indices": [0]
  }
}
```

数值示例不是 host 内置产品规则；产品提供完整真实 constraints、普通文件大小和 SHA。`root_character_id` 必须是该 saved actor，actor/date 必须与固定存档输入一致。

Handler 为 `handler(context, snapshot, typed_event_packet)`。`context` 含 `state_dir` 与合同 `expected`，packet 是原 MCP `ck3_query_current_event_window_context_v1` 全 envelope。返回六个 expected 身份字段原值、非空 `proof` 字典和 `business_pass: false`。Host 独立核对 current event instance、definition、typed character root、query snapshot/revision/date、native options 的 rendered/native index 与当前可用状态，再取得新 snapshot，要求完整事件和 paused owner/frame 未变。结果保存实际 option number/rendered index/native index、原 query 身份及 `selection_attempted: false`。它只观察并准入；选项、保存和产品业务均交由之后的 adapter。

定向 portable 回归 **11 tests PASS**，另 `--help` exit 0。测试调用真实 host `wait_for_saved_campaign`、pinned handler engine 及实际 `GameplayBridgeService.query_campaign_root_context_v1` 方法，transport/native frame 使用 synthetic fixture。覆盖默认无事件路径、显式只读路径、真实 root 前置、错事件/root/options/revision/readiness、调用后事件/日期/PID 变化、pin/state/bad proof、缺少两次 owner 帧拒绝，以及原 frontend proof reply 保持。测试命令、输入 SHA 与原始输出见 [证据索引](acceptance/2026-10-10-saved-startup-event-admission/INDEX.actual.json)。

本包不启动 CK3，不联系 Steam，不授 native qualification 或任何产品业务通过结论；公共入口的产品合同与实际带事件冷载仍需当次实机证据。`open_kaishek` 为 not-applicable：本包处理 Python host 准入和 typed MCP 帧绑定，没有新增 CK3 脚本语义。
