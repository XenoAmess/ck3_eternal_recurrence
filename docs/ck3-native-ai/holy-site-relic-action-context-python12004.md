# 圣物动作上下文的只读 MCP 合同

工具 `ck3_query_player_holy_site_relic_action_context_v1(expected_revision, holy_site_id, artifact_id)` 要求两个明确的完整引用。独立 CLI `--private-player-holy-site-relic-action-context-query` 与 `allow_private_player_holy_site_relic_action_context_query` 默认关闭，不能隐式开启其他宗教工具。这里只观察，不改变选择、刷新候选缓存、构造或提交游戏命令；`action_ready`、业务后验与受益者观察均保持 false。原版文本与许可 getter 会访问脚本上下文/TLS，深层 RNG 影响未知，所以 MCP 标注只读且非幂等。

规划器应分别读取原始 owned reference、character/holy-site owner 通道、player/site equipped-slot membership。单一 owner ID、候选资格或 CanEnshrine true 都不足以证明已供奉、未装备或能够安全执行。`permissions` 保持既有严格 DTO 的独立组件语义，显式 artifact 许可与当前按钮许可仍不可互换。

`destination` 先观察明确 slot 的原版兼容分支，再按需调用原版 picker。实际 effective slot 及其中将被替换的 artifact 可以与当前 selected slot 不同；无兼容位置保持 unavailable，不能变成 slot 0。自动 slot 不代表没有替换。`effective_slot_script_permission_independently_observed` 固定 false，不能把选址观察当成该最终 slot 的独立脚本许可。

三个 native text 字段只属于窗口当前实际选中的 artifact。请求与选择不符时保留 ownership/destination 可读部分，文本保持 unavailable/null，不能改选后冒称原观察。空的已读文本与未知文本分别保留空字符串和 null。

Python 逐组件验证 exact build、actor/date/capture、请求 fullID、原始 slot 绑定及 unknown/false 区别，再按 `RelicActionPreviewCanonical12004` 的固定字段顺序重算 SHA-256。Native Q 的控制字符全部使用小写 `\u00xx`，UTF-8、引号和反斜杠逐字节一致；不用默认 JSON 的换行短转义。Canonical 不包含瞬时 capture_epoch；当前查询仍独立验证 nested permissions 同次 capture。可读 hash 只证明当前组件一致，不提供行动或成功资格。

外置候选只保存小型 SHA 绑定增量，实际测试在 base bridge 初始化前把相同增量应用于内存中的原始 Driver/Service/MCP 模块；不复制公共模块、不修改主树。合入后测试直接加载普通仓库模块。原始输入只接受本域全新 C++ reader/serializer 的实际包；旧 permissions/context 资格不抵扣。人工变异维持原请求与原 frame，只用于验证拒绝，不是原生失败证据。Native fixture 依赖注入不提供真实 CK3 engine、脚本或实机证明。

实际资格：machine_id `4-8e1c2f1861`，观察时间 `2026-10-17T13:38:08.554272+00:00`。9 个本域新 C++ 包通过真实 Driver → Service → MCP ClientSession，4 项测试通过、零跳过；11 个人工变异被拒绝，含保持原请求/原 frame 的身份变异和 canonical hash/文本变异。UTF-8、换行与引号的 native canonical SHA-256 实际重算一致。第一次启动因 concurrent service.py SHA 变化在测试前被拒绝，显式 rebase 后通过，失败原件保留。[逐包证据与边界](holy-site-relic-action-context-python12004/consumer-qualification.json)。完整回执 SHA-256 `18dbca03ceacd01cc8229e29369b444d5f84db89c68624a03c8acd321a12fe40`。本结果不提供 CK3 engine、脚本、实机或动作资格。

实际资格：machine_id `4-8e1c2f1861`，观察时间 `2026-10-17T13:42:37.777604+00:00`。10 个含 faith 绑定的本域新 C++ 包通过真实 Driver → Service → MCP ClientSession，4 项测试通过、零跳过；12 个人工变异被拒绝（新增 faith 变异），含保持原请求/原 frame 的身份变异和 canonical hash/文本变异。UTF-8、换行与引号的 native canonical SHA-256 实际重算一致。第一次启动因 concurrent service.py SHA 变化在测试前被拒绝，显式 rebase 后通过，失败原件保留。[逐包证据与边界](holy-site-relic-action-context-python12004/consumer-qualification-faith-bound.json)。完整回执 SHA-256 `e3180f7ac46bfeb22ec76fad6f6760cefc58c69b818a2a8add3f04c8a9162aad`。本结果不提供 CK3 engine、脚本、实机或动作资格。
