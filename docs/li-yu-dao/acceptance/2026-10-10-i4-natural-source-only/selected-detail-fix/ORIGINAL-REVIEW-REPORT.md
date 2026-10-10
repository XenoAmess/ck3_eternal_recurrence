# I4 公共接口只读审阅

审阅对象为 HEAD `6d4ae66f82ad81cd148bae9a2a2c50942f5299c7` 下本轮五条 authored working-tree 路径及其 FOCUSED-002 精确源码 pins；不把 HEAD 当成这五条工作树内容已提交或已实机。复用原回执：17项离线检查 exit0，未重复测试。没有启动 SDK、游戏或 runtime，没有读取大存档、EXE、wire，没有修改 MAIN。

## 发现：合法 later-selected 返回会被误拒

`tools/ck3_mod_acceptance_cases/lyd_i4_natural_expiry_adapter.py:262` 同时要求 `postcondition_verified=True` 和 `selected_after_verified=True`。

固定 Source09 的实际文件 `C:/csr9/ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_decision_item_action_contract.py:29–35` 仅要求原 ACK 的 `selected_after_verified` 为 bool，允许 `acknowledged_verification_pending`。同树 `native_driver.py:6831–6859` 随后读取实际 keyed model，6841–6850 使用 `actual_selected_detail(later, binding, decision_key)`，实际成功后6855–6859设置 `postcondition_verified=True`、`verification_pending=False`、`status=verified_selected_detail` 和 `later_actual_observation`，不重写原 ACK 的 `selected_after_verified`。

因此官方支持的返回组合是原 ACK `selected_after_verified=False`、后续真实验证 `postcondition_verified=True`；I4 line262会拒绝它。不是所有实机会必失败，但这是一条明确的合法成功形状，不能继续要求其同步 ACK 字段为真。最小适配是使用官方后置成功与实际 later-selected 目标/actor/frame 资格，不额外要求原 ACK 同步选中。紧随其后的 `observe_decision` 本身仍需通过严格的目标模型检查。

原17项测试仅覆盖 guard/parser 小样本，没有覆盖上述公共 select pending-ACK→actual-success组合。ROOT已将修复交回原 owner；本审阅不声称候选修复、后继测试或实机已发生。

## 其余实际接口核对

- MAIN `tools/ck3_mod_acceptance_client.py:237–269` 的 `execute_plan` 返回原行，含 `result` 和 `after_snapshot`；I4 `_call:157–162` 使用形状一致。队列/原步骤失败会停止，原 ID 不重放。
- Source09 `native_bridge/research/run_ck3_12002_mcp_live.py:2001–2028` 顺序调用工具并保存 `after_snapshot`，无返回层级误读。Source09 MCP `mcp_server.py:3458–3463` 确有 `ck3_inspect_gui_window_tree_v1(window_kind)`，没有虚构 revision 参数。
- Source09 `gui_window_tree_contract.py:17–41` 与 `frontend_gui_route_contract.py:250–345` 返回 I4使用的 `schema/window_kind/scope_root_name/read_only/accepted/status/root_available/truncated/widgets/child_path/runtime_name/child_count/effective_visible/enabled`。`enabled` 是实际原生布尔观察，不以模型 available 代替。
- I4 `confirm_enabled:118–154` 的 cost/back/tutorial-highlight 三锚点与footer7/regular3/custom2推导，对应 Source09 `native_bridge/src/ingame_decision_item_v1.cpp:304–331` 的实际 `ConfirmReceiver`。唯一可见确认leaf、完整树与歧义拒绝均有明确源码依据；未点击确认。
- I4两次SAVE分别在266–269、287–290。Source09 `native_driver.py:11228–11312` 返回真实 `checkpoint{status,path,size,sha256,date_raw,episode_projection}`；其固定路径会覆盖，I4 `read_saved:223–246` 首次读取的同一bytes先写入独立create-only路径，再提交第二次SAVE，避免初始保存被覆盖。每个新checkpoint在适配器中读取一次，不读原seed。共享SAVE自身已有物化/哈希读取，不能把适配器的 `save_body_reads=1` 宣传为整个系统仅一次文件读取。
- 既有 reader `tools/lyd_i3b_checkpoint_readback/reader/i3b_checkpoint_reader.py:213–249` 的 graph/raw_character 形状一致；raw_character 明确拒绝 living 段中的显式dead记录。I4同时要求 landed_data block、成员flag、Rite→Faith、headless及主Rite绑定；未发现 parser 字段确定不相容。
- MAIN CaseClient `advance_day:302–323` 与 Source09 host `advance:1554–1622` 匹配：真实 pause→speed1→resume→poll日期→pause；.4返回 `requested_interval_complete/event_boundary/elapsed_hours/before/after`。I4 `validate_day:183–197`、主循环274–286及verify323–336检查24≤hours<48、连续实际date差、身份、事件与累计366日上限。随机事件、角色变化、超时或到上限未enabled均会RED；7200秒固定hold不保证能完成观察。
- MAIN公共 `Selection.verify:529–545` 仍把业务结果与真实共享 `normal_close_qualified` 相与。适配器不授完整I4、fresh365、冷重载、I3b/C3或产品发布信用。

## GUI帧边界

I4 `frame_identity:91–99` 只包夹 PID/generation/actor/date；两个 keyed model另各自核对其提交帧的 native revision。Source09 `native_driver.py:7267–7284` 的树查询使用 `expected_revision=0` 和frontend身份路由，树normalizer不返回 revision/PID/actor/date。因此当前事实是**同一暂停身份与日期下 model→tree→model 的顺序观察**，不是树自身带精确 native_revision 的三结果join。不能把该树说成逐字段绑定同一native frame；目前没有实际串帧或异步故障证据，不据此制造新native阻断。

只读审阅结论：上述选择ACK误拒应修；未发现另一个确定不能运行的公共API/SAVE/parser/自然推进形状错误。运行时GUI刷新、随机事件及本次原0240冷却自然消失仍未发生。原测试不是live，所有业务信用保持未验。
