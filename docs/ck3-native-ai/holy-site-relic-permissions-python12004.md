# 圣物候选与许可的独立只读 MCP 候选

此文档描述源码合同。未提供新 C++ reader/serializer 的实际输出包前，不声称 native 或 MCP 消费资格。

工具 `ck3_query_player_holy_site_relic_permissions_v1(expected_revision, holy_site_id, artifact_id=None)` 使用独立默认关闭权限 `allow_private_player_holy_site_relic_permissions_query`。Standalone CLI 为 `--private-player-holy-site-relic-permissions-query`；受管 host 的 case tool 同工具名。MCP 标注只读、非破坏、非幂等、closed-world：原版 getter 可分配并访问 TLS/初始化静态上下文，更深层脚本 RNG 影响仍未知。

规划器必须保留四种不同结果：窗口的旧 candidate cache、当前玩家原始 inventory 经原版 candidate predicate 的逐项结果、显式 artifact 的原版许可、当前实际选中 artifact 的按钮许可。任何 candidate 项未知时，最终 candidate ID 列表为 null；已知逐项结果、原始顺序与重复引用仍保留。空的真实 inventory 才能表示空列表。原版许可 false 是已观察结果，不能与缺少窗口、失效 fullID、getter 异常造成的 unknown 混淆。

`artifact_id=None` 不会代选 artifact；显式许可保留 `artifact_id_not_requested`。当前按钮独立观察，`context_matches_requested_artifact` 指明实际选中是否与请求相符，未请求或窗口未绑定时为 null。窗口可能选择其他 artifact；null slot 指针表示原生自动选择，不能推断不会替换。即使非玩家 inventory artifact 的某原版 wrapper 返回 true，`action_ready` 仍固定 false；不能从只读许可推导已取得行动能力或成功供奉。

Transport 严格验证 exact 1.20.0.4 build、完整 uint32 引用、请求 actor/date/site/artifact、所有 mandatory nullable 字段、每个组件独立 availability，以及未写入世界/选择/窗口 candidate cache 的披露。生产 getter backend 必须同时报告已验证 loaded-source pins。Fixture 的注入 getter 不提供 CK3 engine/TLS/脚本真实执行证明。public revision 与 native snapshot revision 分开绑定，线上请求使用实际 native revision。

公共 hook 仅以 `relic-permissions-common-hooks-a01.patch` 和 SHA 绑定的 replacements manifest 交付；不复制公共大文件。外置 consumer 在首次 base bridge `__init__` 前安装 source overlay，实际 Driver/Service/MCP 源码在内存应用与补丁相同的增量。基线 SHA 变化会拒绝导入，要求明确重新冻结，不能静默覆盖其他线程的改动。正式合入后这些小增量由主线程统一合并。

消费入口是 `ck3_autonomous_player/native_bridge/research/consume_holy_site_relic_permissions_native_packets.py`。输入仅接受计划中全新的 12 个 C++ 实际 command_result 包；期望文件名冻结于 `tools/relic-permissions-native-packets-contract-a01.json`，实际内容 SHA 和 MCP 请求/响应写入独占输出回执。未传新包时只允许 opt-in 静态检查，其余测试明确 skip。人工变异包只验证 fail-closed，不会被记作游戏失败或原生正例。旧 context 资格不重跑、不抵扣此能力。

实际消费资格记录：machine_id `4-8e1c2f1861`，观察时间 `2026-10-17T13:00:15.478589+00:00`。新 C++ reader/serializer 的 12 个实际包经过真实 Driver → Service → MCP ClientSession，4 项测试通过、零跳过；11 个人工变异包被拒绝。结果与逐包 SHA、public/native revision 见 [消费资格](holy-site-relic-permissions-python12004/consumer-qualification.json)。完整外置回执 SHA-256 为 `184c4637ff6f5b0cc1b4273ff285299dcdefb7126b32a2c5701f292acb963e24`。这是注入原生依赖的离线 fixture 资格，没有 CK3 engine getter、实机或动作资格。未重跑旧 context 资格。
