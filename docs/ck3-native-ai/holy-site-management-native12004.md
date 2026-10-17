# 四种圣地决议的原生接口

本专题在[采用接口](holy-site-adoption-native12004.md)及[费用与冷却读取](holy-site-adoption-planning-inputs-12004.md)上增加晋升、降级、放弃。`machine_id: 4-8e1c2f1861`；GUI 来源审阅记录时间 `2026-10-17T12:52:38.329134Z`，隔离接线观察时间见末节 a25 原件，源码基线 `50dfea0612211a97250232b7b87674acc9fdfa0d`，exact CK3 `1.20.0.4`，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。新增 native fixture 与原包经生产 MCP 消费的离线资格已完成，详见末节；三种新动作的 live 资格尚待完成，R5 采用成功不外推为另外三种动作通过。

## 固定动作与原版来源

| public action | 唯一原版 decision key | 原版 picker 来源 |
|---|---|---|
| `adopt` | `adopt_holy_site_decision` | realm county → 每县 holy site → 当前 Faith 未关联的站点；另有 `is_item_valid` |
| `promote` | `elevate_holy_site_decision` | 当前 Faith 的非 eminent holy sites |
| `demote` | `demote_holy_site_decision` | 当前 Faith 的 eminent holy sites |
| `abandon` | `abandon_holy_site_decision` | 当前 Faith 的非 eminent holy sites |

`promote` 是公共动作名，不能猜成 `promote_holy_site_decision`。没有任意 decision key、角色覆盖、原始指针、RVA 或调用方指定 child path 的接口。四种决议均使用原版 `select_scope_object` controller 和 `selected_item` HolySite Scope；picker 只是候选来源，最终要求与收费由当前实际决议详情的原版 getter 决定。

原版 `window_holy_site.gui` 的三处快捷入口位于第576/588/600行，均经 `MakeDecisionTypeWithParam(key,'selected_item',HolySite.MakeScope)`；对应第581–582/593–594/605–606行按顺序调用 `OpenGameViewData('decision_detail',DecisionTypeWithParams.Self)` 和 `HolySiteWindow.Close`。采用仍复用此前已审的原版入口。脚本文件 `50_holy_site_decisions.txt` SHA-256 为 `80ad6a6045bdafdce514cbccf59a9cd1370eaef6749d510adcec759468065fb4`；晋升 picker 第119–145行、降级第276–300行、放弃第424–450行。不能把采用特有候选过滤复制到其他决议。

## 原版入口的参数绑定

晋升和放弃共享 regular visibility predicate `0x17D6360`，会同时可见；其标准点击回调签名也相同。采用原来依靠独占 visibility 与唯一 receiver 的守卫因此不能直接推广为“第一个按钮”。新接口先读取实际绑定按钮的第二个参数 `Self`，再区分原版 key。

入口保留当前 HolySite 窗口 fullID、可见性、root/parent/gui-owner、exact4、paused owner 与 modal guard，标准 mode 选择真实 `+0x3F8` 或 fallback `+0x338` 回调组。检查 `3AA30E0→3A9F960`、原版 `A79540→1031E60` 顺序，要求回调 `+0xF0` 就是当前实际按钮。第二 argument 必须独立来自其自己的 receiver index、declaration 与 runtime DecisionTypeWithParams class ID，不能拿主表达式最终 receiver index 代替。

Self 为原版 `CAB1C0`；其借用 params 指针必须与同源 widget 的 typed cache 完全相同，随后验证 definition 原生 type/magic/full key、唯一 `selected_item`、Scope kind23/flags0、64位 payload 等于请求完整 uint32 HolySite ID 的零扩展，以及实际 HolySite storage 对象 fullID。缓存/继承链、已选回调组和参数均双读稳定，并在原 dispatcher 前再次比较。

当前纯读解析只接收已经 source-closed 的 direct mode0/1，Self argument kind2 且输出 Any slot=1；kind1 路线保持 unknown。原版 context 继承优先 definition `+0x108` override，否则 receiver `+0xE8` parent；不能随意跳到一个更远的祖先缓存。遇到未闭合 provider、表达式种类、source 变化或潜在第二个匹配 receiver 时拒绝 dispatch，返回真实 reason。`Self` return type raw 值只保存并比较，不为未闭合的数字猜名称。该候选尚未实读证明本存档快捷入口采用哪个实际 provider mode。

## MCP 与执行边界

保留旧 adoption 工具及原 wire；新增四个明确工具：

- `ck3_open_holy_site_decision_v1(action, holy_site_id, expected_revision)`：只打开原版详情，不发送 Confirm。
- `ck3_query_player_holy_site_decision_detail_v1(action, holy_site_id, expected_revision)`：读取当前实际 definition、完整要求/费用文本、结构化报价、普通 CanConfirm 与详情内冷却。
- `ck3_confirm_holy_site_decision_v1(action, holy_site_id, expected_revision)`：仅在新鲜实际详情完全匹配且普通原生 CanConfirm=true、bypass 已观测为0时调用一次原版 Confirm。
- `ck3_query_player_holy_site_decision_cooldown_v1(action, expected_revision)`：不依赖已打开详情，独立读取该实际玩家、该固定原版决议的冷却。

四者只接受上述四个 action。新增只读工具复用既有 `allow_private_holy_site_adoption_detail_query`、`--private-holy-site-adoption-detail-query` 与 religion context 编译开关；公共 case 仍须声明准确只读 tool literal。没有另起游玩智能体、游戏控制台、OCR 或鼠标业务路线。

原详情读取仍核实际 definition、GetPlayer、controller selected entry、controller dictionary、详情自身 E0/F8 context。generic 返回把 `requested_decision_key` 与实际观测的 `decision_key` 分开：不可用时后者允许 null，不能把期望 key 冒充已经读到的 definition。费用、正文、affordability 和冷却各自保留 observed/unknown，不从脚本常量补成 live 数值；只读字段 `action_ready=false`。

Confirm 会重读同一固定 action 的完整详情并保留原版自身再次 CanConfirm→构原命令→一次提交→清理详情的路线。拒绝、调用 ACK 与业务后验分别记录；发生未知结果不重复提交。请求“晋升”不会沿“放弃”的相同签名按钮执行。原版自身的最低/最高站点、eminent 上限、冷却、费用等条件都由当前原生要求决定，不在桥中硬编码猜数或解除普通合法性。

独立冷却每次通过现有 exact4 `DecisionBindings` 重新解析固定 key，拒绝 fallback、错误 type/magic/key 和变化的 registry/definition，复用原 bounded actor-state map/clock 双读；查询后再次解析同一 definition。无需缓存失效详情指针或开放泛内存。`current_counter_raw < expiry_raw` 保持原生比较，观察不到与观察到不存在分开，raw 差值不换算日历。免费额度 presence/type/count 继续 unknown。

## 智能体如何重规划

先读每个候选当前 Faith 关联与各 Faith 的 eminent 标记，再对拟操作的固定 action 打开原版详情并读取具体要求。若晋升被 eminent 上限挡住，保存完整原生拒绝和当前各站等级；不要提交 disabled 动作，也不因静态脚本“通常允许”覆盖 false。后续降级、放弃或改换候选是新的决策，各自重新获取要求、价格、冷却及收益，不能复用另一动作的 true 或旧 revision。

动作后独立确认当前 Faith 站点集合、目标与其他 Faith 关联/eminent、HolySite 实例/type、库存 slot/fullID、钱包净变动、原生 Active/认可及本决议锁。等级、共享关联、库存和激活相互独立；空库存继续 inactive 不是“采用失败”。动态锁和免费额度也不能从支付金额反推。最终受益角色与实际属性变化尚未读到时继续 unknown。

## 来源与资格

以下小包相对外置根 `C:/workspace/ck3-faith-and-power-20261017/episode01/native-candidate/`，均含机器身份、UTC 与源字节：

| 证据 | SHA-256 |
|---|---|
| `management-source/gui-management-source.json` | `2448329ad798367057dc9c9fad15f6e6947d35c2e8b1a0bbe31e699c5c7aa6f5` |
| `management-source/model-source.json` | `72f3591446fa0fb49abe87cc245a9419f0473f2748a3be5345ae60c0a52b881d` |
| `management-source/detail-enum-review.json` | `cca78192e0c1281072bb99c97bf91d176f4cfecf9b3c55d747e6c9c2b5ba49b8` |
| `management-source/cache-sentinel-source-review.json` | `5dcfed2aa275f29c39cb983f94734f30eb8330e987d826f612e950ef8d62ac65` |
| `management-source/self-output-slot-source-review.json` | `824208475dec0d96df12e34e7e9e75dea58843cbff51ded2fe6c6f2b5744faf7` |
| `management-python-admission-a25.json` | `ffe16d2f8c03e5540203481b0324bf772caf26eebd5e92e3fdd639bb4423f163` |

新增11个 Python 文件 AST 通过；真实生产 create_server 与 MCP ClientSession 的两项新 schema/参数拒绝测试通过，native execute_step 请求0。此结果只证明新工具可发现且任意 key/指针/bypass 输入被拒，不是原生读取、开窗或三种新业务动作通过。

交叉源审在首次 native 构建前纠正了 cache end sentinel 与 Self output slot 两处问题：原 owning map 的额外末行是 `FF`，probe 企图进入该行时必须先拒绝原 lookup；Self 第二 descriptor 必须写 output Any slot1，不能将写到首实参的表达式当作第二参数。新增相应拒绝断言。它们是构建前 source-review 修正，不应捏造成已发生的实机或 native fixture RED。

新增三项 native fixture 已实际运行 exit0：detail 使用 `--management-only`，183项新检查、8份完整 command_result，未执行旧213项；独立冷却53项检查、9份完整 command_result；Self 参数解析夹具覆盖同签名动作身份、完整 generation、provider 边界、原生继承缓存所有权与双读稳定。实际原件见 `runtime/management-candidate-a04/qualification-a01.json`，SHA-256 `ae52ffbc96b4ab61d6c00ad3d6aa4b50818a5e5979875ed1252123e144f0431b`。其 native 源实际逐字节冻结于 dirty 集成阶段；不能只用当时的基线 `8ba965bb` 表示整份编译输入。

共享 Service 随远端合流后，在最终 clean main `3d7a9f11d8fae7ca6465509a55c3999f571f1970` 上仅重消费同17份原包：6项测试、20次实际 MCP 返回、0跳过，生产 Driver/Service/normalizers/create_server 均从该 main 加载。17份原包和31份候选源码在消费前后 SHA 均相同。资格观察时间 `2026-10-17T13:35:46.983243+00:00`，`machine_id: 4-8e1c2f1861`；原始回执 `management-native-real-mcp-a30.json`，SHA-256 `fa0a654d0a8fb142fdbc68c3991169aa30305e7de65cb5f23870928b9044ca1d`。其中三份明确标记的 action-key 变异仅用于 Python 拒绝断言，不增加 native 原包数量。此轮未重编或重新运行 native 夹具。

这些夹具的对象、code/RTTI pin、回调与 endpoint hello/frame 均为显式合成输入；实际 original GUI/open/Confirm 回调未在游戏执行。本节证明离线 reader/serializer 与生产 MCP 链路，并未证明三种新动作已实机开窗或生效。之后部署须以 runtime 的完整 native 源封签绑定最终提交与实际 DLL；本 MCP 回执不能替代部署或 live 验收。原 a29 dirty 消费及较早参数准入证据保留为历史，不冒充最终 clean 来源。
