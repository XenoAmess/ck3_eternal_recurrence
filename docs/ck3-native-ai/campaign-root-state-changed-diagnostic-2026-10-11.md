# Campaign root 实际 state_changed 诊断（2026-10-11）

R92 Native75 的普通 campaign-root 查询在 2026-10-10 17:52:41 UTC 返回 `native gameplay step failed: state_changed`。原件为外置 `runtime-01/native75-r0092/managed/operator/gameplay-responses/490-r0092-native75-freshfields-000004-campaign-root-piety.json`。公开请求 revision 3 按既有 SDK 路径映射为 native revision 2；原响应未保留失败的 native before/after 或具体合取条件。这个差值不能证明 revision 误传，当前根因仍未知。原 RED 保持原样。

本次读源纠正了入口路径：实际 1.20.0.4 Bridge 在 `bridge.cpp` 的 `QueryKind12002::campaign` 分支调用 `ck3_12004::ReadCampaignRootContextV1`，生产 reader 是 `src/ck3_12004_campaign.cpp`，原三个失败位置为 904、910、954 行。`src/campaign_root_context_v1.cpp` 的 2054、2060、2096 行属于历史 1.19.0.6 reader，不是这条实际调用链，本次不改它。精确基线及保留源片段见外置 `continuation-63e/SOURCE-FREEZE.json`；实际 reader 基线 SHA-256 为 `df5b317f7d64b9b6376d994ac706ff90480d4a283f1f235591e9804ab2024d99`。

生产变化只将原有三个 guard 的失败结果记录到 caller-owned 的独立可选诊断中：首次 Capture false、expected/native revision 不同、末次 Capture false、after Frame 不同，以及第二次 Observation 不同。原返回值、`unavailable_reason=state_changed`、guard 顺序、Capture 次数与 double observation 均保持。诊断只复制已经得到的 typed Frame 和比较已有对象；不新增内存读取、native query、回调调用或门禁。Frame 差异列出七个已有 scalar 的具体变化；Observation 仅列已有 28 个字段组的变化名称，不输出内存或对象地址。

根 DTO 与严格 reason 枚举不扩展。已有 `HeldTitlePartitionFailure12002` carrier 增加独立 `campaign_root_state_changed` 可选字段，不改变原 held-title 字段语义。55 所有的 Bridge 通过现有 `snapshot_publish_diagnostic` 旁路发送 `campaign-root-state-changed-v1`；正常 command/root payload 保持。Capture 未成功时，对应 wire Frame 为 null；未执行的后续比较及 diff 为 null，不把初始化值或未比较结果当事实。

必要轻量 fixture 只首次验证新增生产 guard helpers 和真实 inline serializer：五种失败结果、原成功路径及缺省诊断指针行为。输入是明确的合成 typed Frame，不能用于认定 R92 的实际失败原因。离线资格、Defender 登记与后续实机返回分别记录。Native76 的已冻结输入不受本候选影响；采纳进入下一 production pin。实机原因必须由采用后的普通查询实际回执确定，诊断本身不声称修复 state_changed。
