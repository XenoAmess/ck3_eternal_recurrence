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

## 窗口身份与展示礼仪分别确认

`window_kind='faith'` 的 `subject_id` 是 **Faith 完整ID**。窗口中央可以展示该信仰的某个Rite，不能因此把输入换成RiteID。D1中的Faith13与RomanRite0、D2中的Faith50与HanafiRite13分别属于两个ID域；开窗、切tab与tooltip均按容器的实际Faith绑定。既有开窗入口与两字段说明见[Faith／人物展示专题](religion-ui12004-presentation.md)。

其他消费者分别为：`rite_creation` 接当前草稿的来源RiteID，`holding` 接Province地图索引，`personal_beliefs` 接当前玩家完整CharacterID。普通窗口query的`subject_id=0`只表示观察当前选择；即使误传Rite0也可能读到当前Faith，查询返回成功不能证明输入域正确。动作与带target的tooltip后读必须匹配实际对象；其中0仍可作为真实Faith/Rite引用，不能一概当缺失。先从独立读回确认域与对象，再使用返回的当前容器行。

`machine_id: 4-8e1c2f1861`，只读核对时间`2026-10-18T21:17:19Z`，源码`90e1f983d6ad13349ad014757fc140a2c34bb85d`。新provider `faith_power_presentation_ui12004.inc:103–107`取`ReadSelection12004.subject_id`；`religion_ui12004.cpp:74–82,127`分别读窗口`+E8`的Faith与`+258`的Rite；`:64–65,93–107`从Faith存储解析输入并用原Faith Ref Any开窗。原setter的已保留指令`14C5D3D`将`Rite+8`写入`+258`、`Rite+4B8`写入`+E8`，来源为`religion_ui12004_source_pins.hpp`与既有展示专题。这次只澄清已有消费者和工具说明，没有新游戏调用、构建或实机资格。

ACK后独立query窗口／页签；hover后用receipt读实际source、stack、root和文本，leave用返回的新receipt后读。缓存文字与渲染像素分别取得，`rendered_pixels_observed`始终false。结果未知时先查询，不重发有toggle效果的动作。建筑207的当前行身份、非幂等行为及独立tracks条件见[建筑轨道专题](faith-power-building-track207-v6.md)。
## 实际原生检查的空tab修订

`machine_id: 4-8e1c2f1861`。a13在2026-10-18T20:53:10Z编译退出0；第一次真实导航fixture随后因合法`presentation_tab:""`断言失败（OS3221226505），原退出与stderr保存在一期外置`runtime/religion-candidate-a13-presentation/navigation-fixture-*`，没有发布资格或启动游戏。共享`JsonStringField`按原合同拒空；本路由却用空tab作为显式展示查询标记。后继仅在此路由解析空tab与四个既定tab值，保持共享helper、合法首条断言和其余selector语义；修复补丁SHA-256 `1045addfc8ecbb062df00fe7757c2a91d272e409fa5ce720dd3b98a39de975d9`。源码修复须由受影响target增量重建及新fixture结果确认，旧RED不覆盖，也不外推成实机通过。

2026-10-18T21:09:11.678630Z，实际00e9修订增量2TU／2link退出0；精确新EXE的SYSTEM排除读回verified，新fixture原PID23792的wait为0，stderr为空。新DLL14,609,920B，SHA-256 `ea408a8d09600eef308c729532b97f2dc2dde744228c7c972248c7c66a1931b6`，构建目录与新publish双SHA相同，a12未改。`qualification-a01.json`13,153B，SHA-256 `67ed11e54ff6e7b84da0ff80d6c759aa857cbf5d84ee032a8bcc2c81c598c334`；其中明确`live_presentation_qualified:false`和`business_pass:false`。旧RED与当时二进制保留；下一场仅沿公共入口取得真实窗口与独立后读，不以fixture的模拟对象取得实机或像素信用。

## R24实际展示范围与冷修边界

同机`4-8e1c2f1861`于2026-10-18T21:41–22:03Z实际加载上述a13，来源`90e1f983`。Faith50开窗及独立query、原编辑草稿和picker取得真实读回与原图；基督教综摄主义仅在草稿中正常选择，没有提交。准备A包含领地、资源、知识及条件性管理关系，详见[R24原始范围与证据](faith-and-power-r0024-original-gui-boundaries-12004.md)，不能把整场写成无世界准备的只读操作。

| 路径 | 本场实际结果 | 尚未取得的资格 |
|---|---|---|
| Faith容器查询、既有编辑／picker | 原窗口、身份与卡片可见 | 卡片名不等于完整信条说明 |
| typed核心悬停与独立tooltip查询 | ACK后source-null；原图仍为地图旧提示 | 目标完整提示未生成，不授渲染成功 |
| 个人信念、holding打开 | owner核验在派发前拒绝；独立query仍无窗口 | 未进入个人页或地产页 |
| 建筑ShowDetails／207与条件提示 | 因前置holding未打开，没有按九例重复提交 | 仅保留源码／离线fixture范围，无本场原卡或条件像素 |

冷修已将原窗口Jomini归属与独立GUI查找归属分开：当前Jomini→gfx→handler、handler+40、window+98/A0按原factory／ctor关系核验，root仍由实际GUI查找返回值绑定。这个源码修复尚未获新构建或实机结果。悬停状态写入与原每帧tooltip查询／工厂／呈现又是不同消费者；后继沿真正生成路径实现有限语义悬停，不以接受null、改文字或一次缓存填充代替原版画面。原Army合同与typed路由的目标匹配分别保留。

R24的原游戏、public、host和keeper均实际正常退出，CAS11953已释放。后继必须使用新source seal、实际DLL资格和unused输入，在新会话独立后读；以上结果不授当前Can、自然AI或整产品业务通过。

## R24 提示实测失败与原版生产链补注

`machine_id: 4-8e1c2f1861`；静态复核为 2026-10-18 UTC，原版 EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。R24 的 Faith50 核心卡 0 悬停返回 ACK，但其独立查询报告 `tooltip_stack_entry_source_null;capacity=1;count=1;hover=bound;index=0`。原图 `operator-frame-20261018T214730Z.png` 仍是地图提示，没有目标信条提示。因此 ACK 和 `context+F0` 匹配都不证明原版提示已出现。小型来源索引见 [生产链证据](evidence/faith-power-tooltip-producer12004-v6.json)。

原 `3AA6020` 维护 hover 和进入、离开事件；真正每帧生产者 `3AB26B0` 从输入服务取得位置，并按原模式、门槛和真实时间差调用四个固定原策略。`3BFF080` 再按该位置遍历原控件树、派发 tooltip 查询，由原模板和工厂建立提示，经过 `3AA81D0`、`3AA8D90` 登记、更新实际栈。它不会因为仅写入 `+F0` 就改用该对象生成内容。原 fallback provider 还允许登记 `source=null` 的地图提示，先前的严格读口因此读到了真实的非目标条目。

最小后继仍复用原展示 opt-in、step、3 个 MCP 工具和既有枚举。冷启动只在 exact4 的四处已核 E8 安装有限 near relay；每个原调用的策略、GUI context、时间差和原工厂保持不变。只有同一实际主线程、暂停日期与角色、窗口及 owner、当前 source/path、hover 和 receipt 都有效时，才以该控件的原生尺寸及原 `3A75EA0` 几何变换计算位置。它不移动桌面鼠标，不使用截图坐标，不注入描述文字或提示栈。离开、窗口/主体/日期/角色变化、owner 停止或源读回失败即停止覆盖；没有有效目标时传递原参数。原生延迟和策略继续生效，查询必须等待实际更新及完整源、栈、文本读回，随后还要独立取图。

默认 Army 合同仍拒绝 null source。仅本有限展示路由可观察原版合法的非目标 null 条目；目标成功仍须唯一完整 source、栈顶、未锁定 root、可见性和文本缓存双读一致。离开后的独立查询须证明目标关联已消失，且旧 root 已隐藏，或被同一稳定栈明确改作另一 source 的提示；后一种情况不能授予原目标的文本或像素信用。此前从未观察到目标 root 时，保留未知诊断，同时停止位置覆盖。信条网格中的图标也不再重复列为普通教义载体。

候选增加现有 navigation fixture 内的生产 frame 读口检查、默认 Army/null 对照及同生产 emitter 的宿主 RX ABI 检查，不增加新测试目标。宿主检查只证明参数、真实时间差、寄存器、栈和返回路径的有限合同，不代表 CK3 原工厂、截图或所有异常路径已经验证。此补注封包时尚未编译、执行新 fixture 或通过新实机；原 R24 RED 保留。个人信念匿名 tooltip 载体的 definition join 等原有精确缺口也不由本次修复外推为完成。


## 建筑条件提示的有限载体补注

`machine_id: 4-8e1c2f1861`，2026-10-18 UTC 静态复核，exact1.20.0.4。安装栏 `holding_building`、预览行的 ShowDetails `holding_building_preview` 与新 `holding_construct_conditions` 分别保留原用途。新载体来自原 Construct 按钮的 `GUIPotentialBuildingItem.GetTooltip`，不是 ShowDetails 那句按钮说明；仅限普通观察、悬停、离开及带 receipt 的后读，不能用它执行 ShowDetails、打开 track 或建造。原按钮禁用时仍可观察其条件提示，禁用状态如实返回，不能据 tooltip ACK 宣称满足建造许可。

新 census 以实际 owned tracks树、tracks_grid/header祖链和原2callback元数据定位匿名按钮，读取当前 owned potential row/definition 双读；每个header出现两个匹配载体即拒绝歧义，不按屏幕、名称文本或硬编码索引寻找。提示的位置生命周期区分main holding root与owned tracks root；两者仍用既有owner与回链读口校验。完整 source pins见[建筑条件载体证据](evidence/faith-power-building-conditions-target12004-v6.json)。

详情 `cant_construct` 是警告图标，其阻因也在另一个原tooltip，不是已经直接读到的完整文本。本最小增量先提供 Construct完整提示，不扩大第二个图标载体。原3个MCP工具、opt-in、step、操作枚举与测试目标均复用；新字段只是有限target值。此封包尚无原生编译、夹具执行或新实机结果，后续必须独立query与截图。

## a14 实际构建失败与最小后继

`machine_id: 4-8e1c2f1861`；观察 `2026-10-18T23:00:52.443544+00:00`。a14原configure实际退出0；原build实际退出1，未执行新fixture、封新DLL资格或启动新游戏。原退出证据`C:\workspace\ck3-faith-and-power-20261017\episode01\runtime\religion-candidate-a14-tooltip\build-original-exit.json`，188B，SHA-256 `8eb746c20a4c33e39ef91c54ce58d8d7c3fbb81ff575ae8b500c5bee3e803b24`，原日志保留在同目录`evidence-build-a01/msvc-build.log`。

失败是global fixture函数中的兄弟命名空间引用：`ck3_12004::kUiIdlerRootSlotRva12004V1`未限定`xar::`；所需header已由生产TU包含。后继只补全命名空间，并合入已审的有限Construct提示与tracks-root修正。当前仍是冷修源码，须沿同两目标做必要增量构建及现有navigation fixture，不能以Python投影检查代替C++或实机。

## R25实际边界与后继冷修

机器 `4-8e1c2f1861` 的P14编译/导航夹具通过没有覆盖恢复后延迟挂载路径的定位hook安装。R25实际保留个人页成功、地产source pin拒绝及提示未派发等分别结果；加载态ASLR语义、实际启动分支和有限个人正常关闭来源见[R25冷修专题](faith-power-r25-cold-corrections12004-v6.md)。后继op208源码已接既有MCP/owner通路，Python合同通过；新DLL、独立hidden后验及提示像素仍待实机。规划应按当次可用性选择路线，不能把历史成功或源码存在当作当前Can。

## R30 非零 Null 定义与锁定提示的原版清理（2026-10-19）

`machine_id: 4-8e1c2f1861`，观察于2026-10-19T06:57:18Z，exact EXE沿本页固定SHA。R30新鲜Mecca census下的单次有限只读探针为142读／3,946 B，双bookend相同，无原生调用、写入或输入。当前 `holy_site_great_mosque_of_mecca_01` 的普通ObDG、vtable、ordinal98与manager成员身份均有效；next却是合法的非零canonical Null，而非普通CBuildingType。该对象vtableRVA=`0x48AC828`、magic=`0x4E756C6C`、ordinalFFFFFFFF、hash0、size0/cap15、inlineNUL，精确来自`[base+0x5D1E320]`。原版`0x12B04EF`的7B RIP load绑定该global。

最小冷修只在optional定义位允许这个精确canonical对象，核原source operand、global、vtable和全部Null字段并双读；普通ObDG非空key路径保留。Potential/ShowDetails与selected实体仍要求真正非空定义，不将空槽或Null记作已选建筑。显式失败fixture覆盖仿造Null、七字段错、source pin错、required拒绝及真实实体仍通过。原探针和候选来源见外置`resume-20261019/research/r30-building-definition-a09/cold-fix-a02/DELIVERY-a02.json`，2,645 B／SHA `8888f3b238614321705b610fd1d4266c2456d4cd9a842147457ce09eb1f4d820`。R30原hover在派发前拒绝，仍没有建筑正文像素；修复源码不追认原场成功。

原 `leave` 只清hover，不关闭已锁定的其他提示。R30的继承说提示遮住own教士确认页，原open/query/close/hidden资格不能补足被遮挡正文。原版 `game/gui/preload/tooltip.gui` 的CloseAllTooltips动作注册链为 `0x36F21→0xAB5500→0xA8F4E0`；noarg bool wrapper只发延后清理，GUI update `0x3AB26B0`消费`+42C`并经`0x3AA8620`隐藏原roots／清count。新有限路由仍用既有faith-power query/present工具，`window_kind=tooltips,subject_id=0`，拒绝target/index/tab或任意GUI动作。先独立query取nonce，再一次`close_tooltips`，最后同nonce的更晚owner query必须读到deferred0/count0及原roots双读hidden，才称cleared。ACK仅pending，未知不重发；不会直接写GUI标记，也不降低typed tooltip source/top_locked/text join。

有限原字节spans与注册/MCP合同检查见外置`resume-20261019/tooltip-readback-research/r30-locked-tooltip-clear-a01/a02/DELIVERY.actual.json`，7,427 B／SHA `b404af7c1f341e17a1e32d9a66455c84016e7f4d7882373f8426912788626aa6`。两修复停场后已合入，27项Python/MCP检查实际通过（native transport仍为合成）。P18实际编译／唯一导航fixture和R31真实清栈／建筑正文均待完成，不能由静态源链取得新实机资格。
