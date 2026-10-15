# 未覆盖原生选项的首个可用选择

用户于 2026-10-15 明确要求：未知且必须解决才能继续正常操作的窗口，先记录原生窗口/实例、当前帧和完整选项，再经 MCP 选择最左上的可见 enabled 可选按钮；单项直接选。未知业务意义不再作为阻塞理由。已知专用策略优先，轮后异步分析必须落实到有来源的持久知识。不能用 OCR、鼠标或猜测坐标替代 Native。

`mandatory_choice_policy_v1.py` 提供纯选择器。Generic 窗口消费 Native 的真实 `blocks_simulation` 或 `exclusive_modal_blocks_input` 证明、有界完整候选和动作 token；独占输入不等于引擎暂停。过滤不可见、禁用与非选项控件，按原生 bounds 的 `(top, left)` 排序；单个 eligible 项不要求 geometry。完整原候选、排除项、去重、排序理由、token 和 frame 原样留证；冲突身份、过期帧或 Native 机制缺失如实返回 unavailable。`is_choice` 指可执行 UI 候选，不要求已知业务语义。

既有事件和交互继续此前全部未覆盖弹窗的用户授权，不伪造 mandatory 证据。事件无坐标时使用 Native `rendered_index`；交互复用精确绑定的原版 GUI 顺序与当前 Native legality。Native index `N` 始终映射 public `option_number=N+1`，不能把 native0 当作 public0。

事件 fallback 现在先过滤 shown+enabled 再取最小 rendered index。AUTO715 的原件 SHA `7df4f3dcd6d9bd48347546f6c97ca3c7610822ca86e8c418391f8c1412758710` 中，event42 `pam_secular_faith_events.0058` 前两项禁用、后两项可用；派生夹具保留该事件的完整 Native window/context/options，正确选择 native2/public3。随后同 Game P07 已有两次实际 MCP 选择和 old-instance 后验：

| 完成回执 | 选择与实际后验 | 回执 SHA256 |
| --- | --- | --- |
| `continuation40-cold-prep/p07-responses/0010-1-result.json` | event42，public3/native2，旧实例清空，`postcondition_verified=true` | `67c8fefacbba0a611803c8dca46e3ad500eba9bf7eaccefc835eddfb880f3141` |
| `continuation40-cold-prep/p07-responses/0018-1-result.json` | event43，public4/native3，旧实例清空，`postcondition_verified=true` | `5aa6d5015c0fb82f9e07c180aa234406b44e3a672ce3f82851310b25d64ad746` |

两次都写入完整 before/after，`event_instance_advanced_verified=true`；这证明原窗口实际推进，不能由此声称所有事件效果或全部通用窗口都已验收。

交互适配允许未知请求在左项禁用、右项 Native legal 时选择右项；专用已知 clerical-chastity 策略仍优先。after 验证分别绑定 accept→accepted、reject→rejected、acknowledge→acknowledged，必须是原 pending ID 实际清空/变化且暂停。ACK、source-reviewed known 与 material success 分别记录。此交互叶 SHA `85b55916895942c63f478289e51cc83afe029d6e104fac6ccd8a20ce289415e7` 尚未进入 P07、尚未实机；仅有离线定向验证。

Generic Native producer/执行和 SDK 接线仍由对应候选推进，本文不宣称所有未知窗口已可运行。既有事件/交互批次 collector 和 source registry 保留；真实 durable-known worker 与跨冷恢复命中仍在独立核验，不能把“已采集”或纯选择器通过写成“离线知识闭环全部完成”。

便携测试包含实际715派生夹具，以及明确标为 synthetic 的横排/竖排/两行、禁用首项、单个 native6、公有映射、去重、过期帧、交互左禁用右合法和 ACK/原ID后验负例。测试不需要本机游戏安装、外置 D 目录、MCP 或桌面；受影响的已知策略优先测试同时保留。
