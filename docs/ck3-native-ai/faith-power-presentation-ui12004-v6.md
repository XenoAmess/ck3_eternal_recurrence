# 原版宗教与建筑展示：1.20.0.4 V6 候选

`machine_id: 4-8e1c2f1861`。研究始于 2026-10-18 UTC；exact EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本页描述外置源码候选，未构建、未运行原生夹具、未向游戏发送动作，也没有新截图或实机通过。源起点 `9f5f413752a18fc57915b1986cadb17ecf48513c`；合包时逐文件 before/after SHA 以候选 manifest 为准。

目标是让游玩智能体查看真正的原版窗口、原版提示和建筑预览。供视频使用的画面仍须另由唯一 operator 取得；缓存文字、原生 ACK 和实际像素分别验。

## 已施工的最小入口

复用 `navigate-ingame-ui-v1`、`query-ingame-ui-window-v1` 及原 frontend owner mailbox，没有新 step、capability、macro 或私有开关。原 `XAR_ENABLE_RELIGION_UI12004_PRESENTATION=ON` 构建选项仍须实际开启；默认 OFF 不因新增选择器变为可用。旧请求没有任何 `presentation_*` 字段时，原响应不增加新 leaf。新请求只接受固定种类、枚举和索引；不接受 widget 名称、路径、RVA 或地址。

| 有限操作 | 原版入口及后读 | 资格边界 |
|---|---|---|
| `open_holding` | 原 `OpenGameViewData` 的 holding view 7，Province.Self Any；窗口 `holding_view` | 请求是省份地图 ID，非领地头衔或圣地 ID；打开不能算已看见 |
| `open_personal_beliefs` | 原 view `0xA9`，当前玩家角色 uint32 Any；窗口 `window_personal_beliefs` | gameview key `personal_beliefs_window` 与 GUI 根名不同；不能混用 |
| `select_presentation_tab` | 原 tab 匿名按钮的正常 ShortcutManager 回调 | Faith 仅 beliefs/holy_sites；个人窗口仅 tenets/doctrines；独立页可见性验当前 tab |
| `open_rite_core_picker` | 左侧当前 core 行的原按钮 | 原按钮依次执行 `ShowWindowSortList(slot)` 和设定右侧 `tenet_selection`；没有选择新信条或提交礼仪 |
| `hover_presentation_tooltip` / `leave_presentation_tooltip` | 原 `3AA6020` hover 事件路径，独立后读真实 hover/stack/root/缓存文本 | 不调用点击或富文本求值器；不把独立 owner epoch 当 GUI 渲染完成 |
| `show_building_details` | 仅接受 potential-building preview 种类 | 原 ShowDetails wrapper 已闭合，当前数据行 receiver→HoldingView/definition 仍未绑定，候选明确拒绝；不能改用 Construct、Upgrade、Replace、Cancel 或 Rebuild |

构造器及 provider 已闭：holding `12AAED0` → handler `+D0`，个人 `17E09F0` → handler `+5E0`。holding SetData `12ACA30` / Matches `12ACA70` 从窗口 `+D8` 的 Province 指针核地图索引与 `Prov` magic；个人 `17E0F60` / `17E1030` 从 `+E8` 核角色完整代次 ID。原 `AF39E0` 会复制精确 Any 载荷；holding 使用 const Province 指针 metadata `9F0B20`，个人使用 uint32 metadata `A05DE0`，后者不是“角色引用 Any”的类型名。两个已注册窗口若为 null 只报告明确缺席，候选不会创建未注册的原生窗口。

## 智能体怎样选可见对象

`presentation_ui.targets` 是当前原 GUI 的有限 census，每个 `(kind,index)` 独立。不能把机制数组顺序当 GUI 行序。没有原生定义关联或已读缓存名称时，`definition_key`、`label` 都是 null。

已施工的 carrier：Faith core 普通/紧凑行、Faith doctrine 原提示行、Rite 右侧 core 候选、holding 普通建筑**槽**。建筑槽不等于已建成建筑，空槽也可能有原 tooltip。左侧 core 行另以 response-only `rite_core_tenet_slot` 标识；它的索引只用于打开原 picker，不能当右侧 `rite_core_tenet_choice` 的索引。

个人已采用信条的 tooltip carrier 在原 GUI 中是匿名 hbox，且内部没有 Faith 模板的 `tenet_name` 锚。候选已能打开个人页面和切 tab，但不会凭相似名字发明个人 hover 目标。建筑 potential 列表位于独立 `holding_tracks_view`，并非 `holding_view` 普通 grid；ShowDetails 按钮文字同样匿名。两条未闭接线保留具体原因，不能以描述图卡冒充原提示。

原 `GUIPotentialBuildingItem.ShowDetails` 确切为 `12B3260`，不是 `Construct` 的 `12B3390`。前者经 `12B03F0` 设置 HoldingView 选择/预览 UI 字段并打开其 owned `CBuildingTracksView`；后者走 `12B0C40` 的建造命令。候选只读 tracks 的精确 RTTI、owner/handler、`HoldingView+C8` 与 `tracks+C8` 双向关系、`+60` named root 和原表达式 callback census。两根均实际可见时可观察有限预览按钮；它的普通 tooltip 是预览按钮说明，不能当成建筑收益提示。

后继若需从普通建筑槽打开 tracks，最窄新增操作是 `open_building_track`：原 `GUIBuildingItem.OnClick` 为 `12B2610→12A6390`，只 toggle/open tracks；相同 category/slot 时会关闭，不能把重复调用当幂等。它尚未加入本次 200–206 合同。执行前仍须实际 row.view/definition 与当前地产的绑定，调用后独立核 root/选择；不能直接执行内部建造函数补过界面。

## 提示后读

hover ACK 产生会话、版本、日期、玩家、线程、GUI owner、当前对象和 provider 私有路径绑定的 nonce。独立 query 必须处于更晚 owner epoch，当前 source/hover/top entry 一致，top 未锁定，root 实际可见，前后两次 stack、父链、上下文和缓存一致。禁用的可见信条可以悬停以显示原版限制原因，正常点击仍须 enabled。

缓存仅解码已闭合的原 `CTextbox` 类及其 `+390` 字符串：最多 2048 节点、64 层、64 段文本、每段 16 KiB、合计 256 KiB。未知 widget 类只导致 `cache_complete=false`，不推造文本。所有 `rendered_pixels_observed` 为 false。leave 消费上一次 receipt，返回新的 receipt；后续独立 query 使用新 receipt，验 source 已退出且原 root 已隐藏。

原 `3AA6020..3AA63A6` 完整体 902 B，SHA `d90611a741bebc3024b11f5d881490a68e5fe418b2bbca8243ff61c0ecee47ae`，会向旧/新对象及祖先发送事件再写 context `+F0`。局部体内没有直接 gameplay command 或 RNG 调用，不等于其传递事件的全部回调绝无副作用。Any getter 也可能初始化 TLS/static 状态。候选只允许已闭合的有限原版呈现对象。

## 后继准入与验证

Root 先审完整增量并在当前实机正常闭场后合入；新增构建、发布目录和实机另行准入。生产者是现 `xar_ck3_bridge`，既有 `ingame_ui_navigation_v1.cpp` 编译包含新 private inc；头文件变更可能影响 frontend/bridge/fixture 等，不能提前说只有一个 TU。必要离线目标为既有 `xar_ck3_ingame_ui_navigation_v1_test`；新 request/legacy/early-failure/有限 census case 加在同一目标，不重跑无关旧矩阵。原生编译及 fixture 结果尚待实际执行。

可复用旧 a12 元数据：DLL 14,478,848 B；上一轮单 TU+link retained 27,132,567 B（含 guard），来源 `runtime/religion-candidate-a12/qualification-a01.json`，SHA `99fc2e5a140820766a53199602d1612f4e4d523c705c77384a348d04f7e47d0b`。它不能证明本次头依赖的峰值。128 MiB 仅是早期未测估计，不能据此授实际预算；Root/runtime 必须用必要依赖 dryrun、实际 OBJ/PDB/DLL 元数据校正后再构建。建议新的 immutable output 为 `runtime/religion-candidate-a13-presentation/publish`，尚未写入。

后继最小实测：原 holding 打开→独立 selected Province/root/截图；个人打开与两 tab→独立当前页/截图；Faith 和 Rite 各一条原 tooltip→独立 stack/文本缓存/截图→leave 后验。失败、尝试、ACK、窗口可见和像素各自记实，不重复提交结果未知的动作。


## V6 a02 后继：原建筑行接线

a01 上文的206/207缺口保留当时身份；本后继新增有限 `open_building_track=207`，仍复用两条旧route、原开关和原ShortcutManager。206只执行ShowDetails，207只执行GUIBuildingItem.OnClick；后者相同category/slot会关闭，候选会在明确触发该toggle时拒绝，先读当前状态。没有Construct/Upgrade等业务动作。

两个GUI row不可混淆：Potential是 `view+E8/countF4` 指针数组、stride8，并要求row.view@0等于当前HoldingView；BuildingItem是 `view+100/count10C` 内联数组、stride28，另有原GetGUIHoldingBuilding固定行view+118，row[0]是group而不是view。收件人只接受当前原callback的零准备、chain0、kind3、精确wrapper/type、local ready mode1及owned membership，并双读。runtime registry `[base+5C6A9C0]` 的该type record E8/F0只要一项为null，原3AC4500就走mode1模型指针fallback；有完整converter/provider的路径仍unknown，不调用getter。

独立 `holding_tracks` 观察新增owned窗口/root/实际可见、原EF4 category、EF0 mode、DWORD EF8 action和当前selected building key。原 `GUITrackItem.GetSelectedBuilding=12B3A60` 完整8B `488b8168040000c3` 读track+468；track=view+1C8，所以是view+630，628仅候选。当前630实际有效definition、owned tracks可见且action1，才报告当前原UI preview；它不证明建造或特定请求成功。206 ACK给实际候选definition key，后读宜普通query并比较实际selected key；原候选按钮可能已隐藏。

补齐两条消费边：普通target query也重绑定有限实际carrier；frontend最后的snapshot/GUI-owner检查失败时，serializer取消leaf的source/cache/visible-tooltip/preview等正向资格，保留attempt和receipt诊断。新增生产reader夹具覆盖真实POD内存中的row/model/type/fallback边，只有原生编译、运行和后续新会话读回完成后才能升级资格；此补注没有实机信用。


## 主线集成后的MCP调用

2026-10-19同机集成a01、建筑a02及Python207增量；以上原生来源与候选形成时的边界保留。当前主线Python18项界面检查、2项规划知识检查及4项组合构图检查通过，snapshot／transport为合成注入；原生编译、实际加载和新界面后读仍待执行。未把测试退出0当作当前游戏支持这些操作。

| 工具 | 用途 |
| --- | --- |
| `ck3_present_faith_power_ui_v1` | 固定开窗、切tab、打开信条列表、悬停／离开、建筑分类与详情呈现。 |
| `ck3_query_faith_power_ui_v1` | 独立读实际窗口、subject、tab、有限carrier及可选holding_tracks。 |
| `ck3_query_faith_power_tooltip_v1` | 用同subject／target／index／receipt检查更晚owner的提示栈和已缓存文字。 |

Faith和Rite保留完整uint32，0有效；Character不可为0，Province是正int32地图索引。target/index来自当前窗口原生census，各容器的行序不互换。左侧`rite_core_tenet_slot`仅用于发现／打开picker，不冒作右侧选择行。未知定义和标签保留null。个人窗口只允许当前玩家；本包未实现个人已采用信条匿名carrier的悬停。

公共case使用两个query时，应分别加入`required_mcp_tools`与`opt_in_read_only_mcp_tools`，沿原`--case-read-only-mcp-tool`显式选择，默认仍为空；产品入口allowlist及shared-host choices同时包含它们。没有另建MCP host、native step或构建flag。

HolySite到地产的路线：读站点`barony_title_id`，经既有`ck3_query_title_holder_v1`取得稳定title key，再用`ck3_center_map_on_landed_title_v1`返回的`capital_province_id`打开holding。不能把TitleID、HolySiteID或type_key当ProvinceID。信仰页仍用既有`ck3_open_faith_window_v1`。

ACK后独立query窗口／页签；hover后用receipt读实际source、stack、root和文本，leave用返回的新receipt后读。缓存文字与渲染像素分别取得，`rendered_pixels_observed`始终false。结果未知时先查询，不重发有toggle效果的动作。建筑207的当前行身份、非幂等行为及独立tracks条件见[建筑轨道专题](faith-power-building-track207-v6.md)。
