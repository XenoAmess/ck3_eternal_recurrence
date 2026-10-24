# CK3 1.20.0.4 礼仪确认的已完成后继合同

此变更只维护共享原生 provider / Python SDK / MCP 传输，不新增 mod 业务 runner。普通创建和改革仍使用原版窗口、原版 Can、确认 command 和现有显式 opt-in。源码或模拟传输测试不能证明实机通过。

原先 `actor + source Rite + episode/managed state directory` 的持久 claim 阻止 UNKNOWN 被日期、revision、preview token、连接重启或新运行标签绕开，但一次真实完成后也永远挡住同源的合法后续修改。旧 `evaluate_independent_poststate_v1` 只比较身份与钱包，明确没有验证修改后的名字和教义，不能拿来解除这个限制。

新增只读 MCP 工具 `ck3_verify_player_rite_creation_action_completed_v1(action_request_id, expected_revision)`。它复用 `--private-player-rite-creation-actions`；默认关闭。宿主需要显式选择该工具，旧三个工具的默认要求没有扩大。该工具不接受客户端提供的 poststate，也不打开新草稿。它沿同一个 `player-rite-creation-action-v1` step 调用只读 `observe_current_rite`，读取已提交当前 Rite 的完整持久名字、core 槽位和有效 doctrine，以及实际窗口/modal 状态。无完整原生输入时保持 unavailable。

独立观察的 `source_rite_id_anchor` 严格回显原 claim 的 source，`rite_id` 独立来自当前持久身份；创建成功时二者可以不同，不能将原 source 冒充新 Rite，也不能要求创建后当前 Rite 仍等于原 source。

新 claim 使用 `xar.ck3-rite-confirm-once.v2`，在原生提交之前以 exclusive create + flush + fsync 保存完整已校验 `SubmittedPayload`。统一合同在 `ck3_autonomous_player/src/xar_autoplayer/bridge/rite_creation_action_private_v1.py`，包含五项名字、来源完整 ID、预期 outcome、core 有序槽和按 group 规范化的 doctrine；持久化统一用 JSON list，缺失、null 与空集合不合并，整数拒绝 bool/float。新的确认图与旧图只有日期、revision、连接、预览令牌变化时，不算新业务意图。

只有下列条件全部满足，才写独立 completed receipt：

- 原始 native packet 与 claim 的 request ID、版本、actor/frame、build、操作完整绑定，原生 `native_dispatch_attempted` 和 `dispatch_invoked` 都是 true。原结果仍未知时，仅允许收集原 request，不发新观察冒充已完成。
- 真实独立观察仍在原 game PID / connection，capture epoch 晚于原提交回执；actor 与 episode / verified managed state directory 相同。单纯重启或 revision 改变不提供完成证明。
- 当前 Rite 完整五名字、core 槽和 doctrine 逐项匹配提交图，实际确认 modal 和创建窗口均已关闭。修改要求同 Rite、同 Faith；创建要求新 Rite 和实际 founder；创建新 Faith 还要求 Faith 改变。

原 claim、原 native packet 均保留且不改写。receipt 固定这些文件和新的独立 native packet 的 SHA-256；每次考虑后继都重新校验原内容、绑定和独立观察，不只信 receipt 内的 `business_outcome_verified` 布尔值。旧 v1 claim 没有提交图，不能推测补齐或追认完成。

后继使用追加式 `<intent-key>.<previous-request-id>.successor.claim.json`；原 `<intent-key>.claim.json` 永存。所有同 actor/scope 的 claim 必须形成唯一有证据的链且全部已验证完成，新草稿必须明确改变 outcome、名字、core 或 doctrine 才能追加。同 actor/scope 的 UNKNOWN 也会阻止换 source Rite 绕过。任何链缺件、重复 request、分叉、内容改动或不完整输入均拒绝继续。

`cancel_draft` 是另一个有限原生操作，只处理实际未确认草稿；不释放 claim。取消 ACK 不证明窗口消失，仍需独立 `observe_current_rite`。已经提交后结果未知的动作不能靠取消、重新开草稿或重复 confirm 消除。

直接只读观察沿既有 `ck3_query_player_rite_creation_action_context_v1`，新增可选参数 `observation="current_rite"`；默认 `"draft"` 保持旧调用语义。这让未提交草稿取消后也能实际观察窗口，而不需要制造 confirmation claim。

验证范围：本次新增回归通过真实 `MCP Client -> existing server -> NativeHeadlessGameplayDriver -> existing primitive -> synthetic endpoint -> retained JSON -> independent verification -> successor` 链，覆盖连续关闭/启用式 doctrine 修改及新 Rite 创建、UNKNOWN、旧 schema、取消不释放、换 source、同图新 token、陈旧 epoch、错字段、缺字段、bool/float 整数和 JSON 往返。endpoint 是合成夹具，不能当作 CK3 实机证据。两个既有生产 Python 文件运行实际 strict mypy；其运行环境和实机验收按本任务带 machine_id 的闭场回执记录。
