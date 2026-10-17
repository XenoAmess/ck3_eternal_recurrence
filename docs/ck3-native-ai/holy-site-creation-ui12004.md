# 圣地创建界面：typed UI 与规划后读（1.20.0.4）

machine_id: 4-8e1c2f1861。2026-10-17 UTC后继；精确时间、来源及SHA见[小型资格索引](evidence/holy-site-creation-ui12004/closure.json)。基于冻结3d7a9f11与独立query候选，原版EXE SHA为98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518。

此接口补充[原版创建候选及只读合同](holy-site-creation-native12004.md)：只打开当前玩家实际Faith，或改变原版类型、地点、圣物选择。没有Create提交，也没有实际付款、冷却、免费额度或新圣地业务资格。完整DLL链接和实机界面开窗/选中尚未验收；本轮原生端执行是离线DTO合同资格。

| MCP工具 | 固定输入 | 原版调用/选择范围 |
| --- | --- | --- |
| ck3_open_holy_site_creation_window_v1 | expected_revision | 当前玩家实际Faith；不收actor/Faith override |
| ck3_select_holy_site_creation_type_v1 | type_key、expected_revision | 仅当前原版候选中精确且唯一的key，按原生CanPick |
| ck3_select_holy_site_creation_barony_v1 | barony_title_id、expected_revision | 当前地点model的完整Title ID |
| ck3_set_holy_site_creation_artifact_selection_v1 | artifact_id、selected(bool)、expected_revision | 先读完整选中集合；已达desired时不toggle |
| ck3_query_ingame_ui_window_v1 | window_kind=holy_site_creation、expected_revision | 原版root runtime/tree及完整选择后读 |

独立native开关XAR_ENABLE_HOLY_SITE_CREATION_UI12004默认OFF；Python由--private-player-holy-site-creation-ui及allow_private_player_holy_site_creation_ui显式开启。只读候选查询另用--private-player-holy-site-creation-context-query，不会暗中开放这些界面动作。kind8/op14–17保持Root分配，不占用relic域100–103。

仍使用现有暂停、owner/TLS、实际build、帧revision及动作modal守卫；不通过鼠标、OCR、任意widget名、RVA或调用方指针开窗。当前玩家宗教Context来自实际ReadPlayedReligionContext12004，并在调用前后核actor/date/Faith/rite等绑定。原版typed Faith Any、AA窗口路由、选择函数及模型布局的静态依据回链前述SourceContract。

独立后读要求完整原版模型和选中元组、真实holy_site_creation_window root、原版widget runtime与无截断tree、两次owner/宗教/模型一致。原始payload未取得真实capture_epoch时context=null；不能把默认actor=-1/date0填成当前观察。

| 结果 | 智能体应如何理解 |
| --- | --- |
| ui_selection_verified | 原版调用返回，且独立界面后读确认本次目标选择；不代表创建完成 |
| already_selected_verified | 独立后读确认已达目标，native_dispatch_attempted=false；不重复toggle |
| verification_pending | 已尝试但后态未闭合，保留原ACK及unknown；下一帧只查询，不重复提交 |
| unavailable且未尝试 | 保留真实前置/候选/窗口诊断，重读相应条件；不伪装已选择 |

selection_verified只证明请求的类型、地点或圣物成员关系达到目标。类型变更可能重置地点；满槽加入圣物可能移走首项。因此每步后都要重读完整元组和集合，再规划后续选择，不能推断其他项不变。完整model只是当前原版窗口缓存的完整列表，不证明producer刚按当前actor重新枚举；缓存报价仍不授新鲜支付资格。

最小后继采样链为：暂停帧及当前实际Faith→只读creation context→打开一次→若pending，在下一帧query UI/context→记录三类候选、完整选择、原生拒绝全文、最终按钮值与bypass→可选一次原版CanPick=true的类型并独立后读。没有圣物候选仍可解释拒绝，但不能外推玩家全库存为空。所有live字段须使用新加载DLL与同场实际原生回执，不能借R5采用成功或R6其他圣地动作授此资格。

本轮新增资格分层保留：

- 原7个必要生产TU在/W4 /WX下编译通过；DTO-only完整target链接31个旧native执行依赖为RED，原件保留，未追建完整runtime。
- 25个生产parser/validator/serializer/envelope定义逐字节摘录，源完整SHA、起止行、字节范围及函数SHA绑定；177个实际项目header形成闭包SHA。未加入native stub或手写结果JSON。仅原合成DTO harness和摘录TU两份编译/链接通过。
- 唯一新fixture执行7个拒绝和10个新请求的parse/validate/build-scope检查，生成原生产envelope/serializer包；可见、owner、选中值均为明示合成输入，未调用Execute/Open。
- 真实生产Driver→Service→MCP Client保存19个新结果：10个上述原包、9个显式突变拒绝；public revision2/native37，高位barony2147483681/artifact4026531849与selected=false保持完整。default OFF及严格参数拒绝均未发送UI动作。

这些结果证明新参数及数据通路保持合同；不能抵实机开窗、界面选中、原版Create或世界后验。既有query25结果和旧矩阵没有重复运行。
