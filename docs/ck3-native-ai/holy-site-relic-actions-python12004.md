# 四个有限圣物动作的 MCP 链

独立开关 `--private-holy-site-relic-actions` 在 MCP server 和受管 host 中默认关闭，绑定 `allow_private_holy_site_relic_actions`。它开启四个独立工具：选择明确 artifact、设置明确 slot 的目标选中态、供奉、移除。不会开启其他只读工具。供奉/移除必须传入 action-context 中实际观察的 preview SHA 和替换前提；slot 设置必须给出 Boolean 目标状态，不能暴露盲目 toggle。

四工具分别为 `ck3_select_holy_site_relic_artifact_v1`、`ck3_set_holy_site_relic_slot_selection_v1`、`ck3_enshrine_holy_site_relic_v1`、`ck3_remove_holy_site_relic_v1`。所有 fullID 必须是完整 uint32 且排除 FFFFFFFF，slot 限制 0–4095。不同操作的 wire 字段严格分开；remove 禁止 effective-slot/replacing-ID，必须明确 `expected_replacing_empty=true`；enshrine 的 empty 标志为 false 时必须提供替换 artifact fullID，为 true 时禁止提供该 ID。Preview SHA 为 64 位小写 hex。

受管 case 使用 `opt_in_holy_site_relic_actions: true` 才透传 host flag；默认 false，字符串和数字均拒绝。Case 必须把四个工具全部列入 `required_mcp_tools`，并与 `opt_in_read_only_mcp_tools` 分开。需要动作预览时另行声明只读 action-context 工具；此动作开关不会替它授权。

生产路径是实际 Driver `_execute_primitive_step` → 既有 `navigate-ingame-ui-v1` capability/native mailbox；不扩 existing UI contract 的业务枚举，不经过 decision 通道，不使用 OCR、键鼠或窗口 setter 替代回调。Python 在提交前、返回后验证 exact 1.20.0.4 build、当前暂停地图、存活角色、native/public revision 和连接 generation。Nested result 原样保留 native attempt、调用 ACK、当前按钮、冻结预览与选择前后态。选择的即时后验可以证明选中态，不能证明供奉/移除生效；`business_outcome_observed` 和 `action_ready` 保持 false。

供奉/移除的 ACK、callback unknown、超时或无法校验的返回都保留 pending intent。排重键包含 machine_id、实际 episode 或已验证 managed-run scope、actor/date、operation/site/artifact/generation、preview SHA 和替换前提；public revision 不作为解锁 nonce。另有跨 generation 的稳定 create-only pending 文件，driver 重启后也不能自动重发同一未解决 intent。仅明确 no-attempt 或选择后验匹配时解除；供奉/移除的 after-selection 和 ACK 不解除。没有自动 pending manager，也未实现自动业务后验解锁。

Managed scope 复用 `managed_campaign_title_map_navigation_v1_binding` 的现有完整校验，记录的是分配的 run/attempt，不能称存档内容 UUID。新 run 是不同 scope，不能据此宣称旧 unknown 已解决。Retake 恢复同存档、同暂停帧且 intent 相同时保守拒绝，需先另行查询实际 owner/reference/slot 业务后态；不能手删 pending 或改 revision 绕过。

每份 intent 收据重新读取 canonical `tools/ck3_live_run_id.py` 的机器 ID，附观察 UTC、来源 SHA，以及统一 `docs/storage-retention-policy.json` 的版本/SHA 和 `lifecycle.protection_max_hours`。保护截止和复核期有限，期限到达只触发复核，不自动解除 unknown 或永久续存。State 及原生返回均落既有 driver state_dir 的外置路径。

离线资格只消费新 C++ helper 与原生产 parser/formatter 精确 source bodies 生成的完整 command_result，不使用 Python 包装局部 DTO 冒充正例。完整 DLL 未链接、GUI/owner admission 与 engine callbacks 是明确的 owned fixture 注入；真实原版动作及游戏结果尚未证明。外置测试需要已交付 action-context overlay helper，生产动作 transport 自身不依赖打开只读工具。

实际资格：machine_id `4-8e1c2f1861`，观察 UTC `2026-10-17T14:01:40.615262+00:00`。本域 12 个 C++ 完整包通过真实 Driver primitive → Service → MCP SDK，5 项测试通过、零跳过，6 个人工变异拒绝；unknown 精确 intent 改当前 revision 和关闭重建同 episode Driver 均未重发。另对已捕获 R5 记录离线调用既有 canonical managed-run validator 通过，不把该历史帧当成当前实机证据。[逐包 SHA 与资格边界](holy-site-relic-actions-python12004/consumer-qualification.json)。完整消费回执 SHA `8b484b4f9b593d3cddf5395ca764b0103abb2bc927708f185459ad73a87d2c19`。
