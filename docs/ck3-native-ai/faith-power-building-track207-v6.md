# 原版建筑轨道开窗的有限增量

本候选叠加 V6 已冻结 Python a01，不改该原件。`machine_id: 4-8e1c2f1861`；来源与观察时间见同包交付清单。只新增 `open_building_track`，沿现有 `ck3_present_faith_power_ui_v1`、`navigate-ingame-ui-v1` 和 owning-thread 执行；没有新工具、native step、capability 或 flag。

请求固定为 `window_kind=holding`、当前实际 ProvinceID、`presentation_target=holding_building` 和当次原生 installed-row census 的 index0..127。tab/receipt 必须为空，不接受 potential preview 行。原版 GUIBuildingItem.OnClick 路线用于切换建筑轨道窗口，与 potential-item ShowDetails206 分开；不能据此发 Construct、Upgrade 或 Replace。

该动作可能在重复同一行时关闭已开的轨道，因此不具幂等性。ACK 必须来自实际原调用，并保留正确 subject、source_bound 和 target/index；仍是 verification_pending。结果未知后不自动重发。

独立 `ck3_query_faith_power_ui_v1` 可返回可选 `presentation_ui.holding_tracks`：原 owned tracks 的存在、root、实际可见性与选中类别/模式/动作/定义键。旧 a01 缺此字段或返回 null 时保持 unknown。只在原 owner/back-pointer/root 双读成立后记录对应观察；未闭合的选择字段保持 null。主 holding 窗口可见、空候选列表或一次 ACK 均不能代替 tracks 可见后态，更不能证明建筑业务完成。此结构也不授予 rendered pixels 信用。

本包只执行新增207与可选 tracks 的 Python 合同/Driver/Service/MCP 窄测试；快照和 transport 为合成注入，不宣称 C++ fixture、原生调用、实机或画面通过。原 frozen a01 的13项矩阵不在本增量重复执行。正式构建与真实后读由后续单独准入完成。
