Faith／人物窗口的 exact 1.20.0.4 展示候选

此通道让游玩智能体把已核实的人物、信仰关系展示在原版窗口中。它不改变信仰归属、圣地等级、资源或游戏日期。候选默认关闭，编译选项为 `XAR_ENABLE_RELIGION_UI12004_PRESENTATION=ON`；源码与离线夹具通过仍不等于实机资格。

本轮来源机器 `machine_id: 4-8e1c2f1861`，记录日期 2026-10-17，源包冻结于 13:15 UTC 左右。来源是本轮保留的不可变 EXE 分段缓存与实际安装的原版 GUI，零新增 EXE 物理读取。精确版本为 1.20.0.4，EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。其他机器须重新核版本、加载字节和实机结果。

| 固定入口 | 请求与独立后验 |
|---|---|
| `ck3_open_character_window_v1(character_id, expected_revision)` | 请求完整 CharacterID；独立 `ck3_query_ingame_ui_window_v1('character', ...)` 读实际选中人物、原窗口根和有效可见性。 |
| `ck3_open_faith_window_v1(faith_id, expected_revision)` | 请求完整 FaithID，0 可为真实 ID，FFFFFFFF 无效；独立 query 的 `window_kind='faith'` 读实际选中 Faith、关联 Rite 与原窗口根。 |

两种 open 都复用现有 `navigate-ingame-ui-v1` owner-thread 邮箱，查询复用 `query-ingame-ui-window-v1`。原 actor／revision／connection generation／暂停地图／TLS／application owner／GUI owner／modal 守卫继续生效。公共接口只接受固定类型及完整 ID，不接受原生地址、RVA、控件名、view enum 或鼠标坐标。`native_dispatch_attempted` 仅代表消耗了一次原版调用机会；返回 `acknowledged_verification_pending` 后必须另行查询，不能重复提交结果未知的操作。

原版来源链已分别闭合。人物 `DefaultOnCharacterClick` 注册到 A9AC10，经 ABC320 抽取 Character Any，再到 A7AE30／AF2DE0；原版 AF2DE0 以 A05DE0 构造内联 DWORD Character Ref Any，并调用 `AF39E0(handler, 8, Any40*)`。本候选使用这段固定 typed OpenGameViewData 路线；不继承 1.19 的人物点击 RVA。Faith 原版 `shared/buttons.gui:1518` 使用 `[OpenGameViewData('faith',Faith.Self)]`，B19AD0 产生 Faith Ref Any；B07E50 的窗口工厂写入 handler+270，对应索引 3B。两种 Any 的类型元数据、内联完整 uint32、原版复制、析构及实际虚表边均校验；AF39E0 把值复制进自有 history，未保留栈参数引用。

人物原窗口 handler+D8、主/副虚表 451BA18／451BAE8，实际选择字段 C8。Faith 原窗口 handler+270、主/副虚表 45648D8／45649F0，实际 Faith 字段 E8、Rite 字段 258。Faith setter 14C5D00 由 Rite+8 写 258、由 Rite+4B8 写 E8，二者不可混用。查询核对完整 generation ID、Rite magic 与 Rite→Faith 归属、原 SetData／MatchesData 虚表边、window+A0 handler backlink、window+60 root 与当前 GUI owner 下同名根的同一性，再两次读取选择和可见性。人物打开还保留原 SetData 对人物+1A4／+1A5 的排除条件。窗口所属 GUI owner 与被选中的人物不是同一个“owner”概念，本通道不填写 Army／selected Unit owner。

智能体的规划顺序是：先以原生业务快照确认土地→县主完整 CharacterID→人物 FaithID，再打开对应人物和信仰窗口。比较同一圣地在不同信仰中的普通／显赫等级时，应使用圣地业务快照中按完整 FaithID 绑定的成员与显赫集合；窗口仅提供展示后验，不能从图标、行号或开窗 ACK 推导等级。每次切换目标后，以新的 revision 另读实际选择；若 ID、owner、根节点或可见性不稳定，保留 unknown 并重新规划。

本轮尚未闭合 Faith 的 `SetActiveTab('tab_holy_sites')` typed setter，因此 Faith open 不保证已切至“圣地”页。本候选也不声称已读取 Faith 圣地 DataModel 行、页面像素或任何实机通过。现场资格需保存完整新 DLL／版本绑定、原生开窗 ACK、随后独立 query 和实际画面；19 个 C++ 核心夹具、24 个 Python normalizer 夹具只证明新增的离线边界。

可重建来源位于本机外置 `C:/workspace/ck3-faith-and-power-20261017/episode01/native-candidate/presentation-source/`：`presentation-native-source.json` 包含完整小函数／已明确标记的前缀、19 个 loaded pins 与原版 GUI SHA／行；`integration-patch-manifest.json` 固定七个共享文件的输入 SHA 与未应用补丁；`FINAL-MANIFEST.json` 固定本模块、夹具及回执。原始缓存和构建只因本次待合并、待资格任务限期保留，复核时间见存储回执。
