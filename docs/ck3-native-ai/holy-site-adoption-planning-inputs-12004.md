# HolySite 采用的费用、免费额度与冷却输入

这是[原生采用专题](holy-site-adoption-native12004.md)的只读合同。`machine_id: 4-8e1c2f1861`；来源审阅时间 `2026-10-17 10:06–10:20 UTC`，源码研究基线 `e54c8c7456dc865f3d42af9cc92a115fbf631eb5`，exact4 EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。最初审阅仅读冻结源码、有限函数缓存和已有 GUI 定义；后续实现及合成原生夹具、真实 MCP 资格见末节。新增 getter 尚未 live 验证。

## 现有工具可以提供什么

`ck3_query_player_holy_site_adoption_detail_v1(expected_revision, holy_site_id)` 已提供实际详情定义、actor、controller 选中项、`selected_item` 字典、原版 CanConfirm、requirements bypass 原始字节和原版 Confirm tooltip。应先读这份当前详情，不因费用结构尚缺而丢弃已观测的原生要求。

R3 部署的 native serializer 明确写 `native_resource_quote_available=false`、`native_resource_quote=null`，当时 Python normalizer 也要求维持这份 unknown 合同。它没有通过类型转换隐藏费用，也没有把脚本的 1000 虔诚作为 live quote；下文的新候选才增加独立读取。通用 `ck3_inspect_gui_window_tree_v1` 无渲染文本/tooltip 选项；普通 keyed 决议接口仍要求原有列表准入，不应用来绕过隐藏采用决议。

R0003 在 `2026-10-17T10:14:10.974463Z–10:14:11.350171Z` 实际打开采用详情并读到 available=true、actor15893、参数/选中 HolySite32、index14/count21、bypass0、两个 CanConfirm=false。Confirm tooltip 原文只有泛化的“你未满足所有要求”，不能当作完整要求列表。原包 `episode01/live/4-8e1c2f1861--faith-and-power--R0003/root-native-receipts/r3-adoption-detail-a01.json` 的 SHA-256 为 `07c27e13db7fd09834bee6d53c4cbf1247256c4ef015157efcfd83aa2532b029`。

钱包有可复用的现有读口：`ck3_query_player_religion_conversion_outcome_v1(expected_revision, target_rite_id)` 的 `actor` 子对象包含 `piety_raw/gold_raw/prestige_raw`、`raw_scale=100000`。可把当前原生上下文实读的 Rite fullID 作为 target；这里取的是独立当前余额，不声称发生改宗。只在 `actor.available=true` 且其 frame/actor/identity 通过校验时使用；整体 state 不可用可以与独立 actor 观测并存。工具需既有私有 permission 与 case optin；本审阅未激活它，也没有证明当前 live 已启用或余额实读通过。

固定 mystical/confession 决议费用和新建信仰 draft 费用均绑定各自对象，不是任意采用报价接口。`ck3_query_white_player_business_variables_v1` 只允许固定八项业务变量并硬绑定 1.20.0.3，不能作为 exact4 Faith 额度查询。

## 最小费用读取路线

原版 `window_decisions_detail.gui:237` 直接显示 `DecisionDetailView.GetCostDescription`；本窗没有可直接拿来查询的 CostBreakdown datacontext。以下是精确 1.20.0.4 的原函数来源，不使用旧 1.20.0.3 地址平移。

| 原版入口 | ABI 与实际来源 |
|---|---|
| GetRequirementsDescription wrapper `0x1472150` → direct `0x1470BF0` | GUI 第158行的完整要求正文；`CString32* (detail RCX, fresh output32 RDX)`。原函数分别使用真实详情 `+0xE0` 与 controller virtual `+0x10` 返回的 owned context。实际 controller vtable `0x45A08F0+0x10` 指向完整 getter `0xB1DFF0`，须读回 slot 并 pin；相邻 `0x1470C80` 是效果描述。 |
| GetCostDescription wrapper `0x1472290` → direct `0x1470DF0` | `CString32* (detail RCX, uninitialized output32 RDX)`；使用实际 definition `detail+0xD0`、actor `+0xD8`、内嵌 ScopeContext `+0xE0`，调用 `0x310CCC0` 追加费用文本；只复制并析构本次输出 `0x856050`。 |
| DecisionCost `0x14706B0` | 从实际 definition 选择原版费用块；原 CanExecute caller 位于 `0x288D7FA`。两个可能的费用块为 `definition+0xA70` 与 `+0x1448`，必须让原版 getter 自己选择。 |
| Evaluate `0x310CE50` | `(cost RCX, actual ScopeContext RDX, out10×int64 R8)`；原版先清零 80B，再经 `0x310CEC0` 评估并复制全部 80B。返回数组由调用方拥有，不需要析构。 |
| Affordable `0x310B390` | `(cost RCX, actual ScopeContext RDX, actor R8, optional CString reasons R9)`；同源评估后调用 `0x310E6F0`。须区分正常 false 和读取/调用失败。 |

费用描述是原生文本，不等于结构化金额。结构化结果应保留完整十项 raw vector；精确4 的 `0x310E6F0` 分派及资源拒绝字符串已证明 index `0=gold、1=prestige、2=piety、6=treasury`，其余六项在此合同中不命名。使用已有资源定点单位合同并明确 scale，不能从格式化文字反解析金额。

**详情自身的 `+0xE0` context 与 controller `+0x18` context 是两个对象。**报价前应独立读前者 root Scope 的 kind4/actor，以及 `detail+0xF8` named scopes 的唯一 `selected_item`：kind23、flags0、64-bit payload 等于请求 HolySite fullID 的零扩展。它必须同时与当前 controller 字典和实际 selected entry 相等。原版 `0x1471700` 曾将 controller context 合并到详情，不代替本次实际读取。保持 paused owner、actor/definition/root、frame 和两次稳定读取；不构造只含 actor 的旧 rootScope，不析构借用 context。

## 具体采用冷却

原 CanExecute `0x288D630` → `0x31034F0` → actor `+0x1C0` 的内部 state → `0x2957F10`，后者将 `state+0x430` 交给纯查询 `0x1A74790`。RCX 是实际 map；**RDX 是 definition 指针本身作为 64-bit key 值，不是 `&definition`**。callee 按 RDX 自身八字节计算 hash，并与 row key 比较；命中返回 `row+0x10` 的借用 `int32*` deadline，未命中返回 nullptr，不写入、不分配。不要释放或跨 owner callback 缓存返回指针。

原版以 `*(global0x5C68C50+8) < deadline` 判断锁。最小 DTO 可独立记录 `lookup_observed/present/deadline_raw/current_clock_raw/native_active`；未命中与读取失败必须分开。日历显示转换与计时单位未在本轮完整闭合，先保留 raw，不把差值命名为天或年。该 key 必须是实际 `adopt_holy_site_decision` definition；创建变量 `holy_site_creation_cooldown`、王权法时钟或别的圣地决议均不能替代。

## 免费额度与规划边界

脚本变量是 Faith 的 `free_holy_site_actions`，不是 actor 的通用旗标。现有专用 MCP 尚未提供其实际 presence/type/raw/value。精确4 adapter 已使用 `variable_context=0x370EAF0`、identifier table `0x3F8A7E0`、lookup `0x3F8A660`、name `0x3F8A6D0`；Faith.MakeScope `0x26C7240→0x26C7280` 证明 scope kind13、flags0、payload 为 Faith `+8` 完整 uint32 ID 的零扩展。变量 dispatcher 按实际 scope registry 找 getter；Faith 实际 provider 的纯读和生命周期还需闭合，不手填未知 Faith offset。

最小后续补强应扩现有 detail/mailbox/Driver/normalizer 合同，分别返回原生费用描述、typed raw quote、独立 affordability、Faith 额度、特定采用冷却，并为每部分保留 observed/unknown。费用为零不能反推尚有几次免费；有免费额度也不代表其他合法性成立；CanConfirm 在 requirements bypass 下返回 true 不能升级普通合法性。当前缺项保持 null，不写成 false，也不伪造 `action_ready=true`。

规划器先比较长期收益与真实支付成本、免费额度机会成本及当前决议锁。提交仍须重新读取当前普通原生 CanConfirm，并沿现有一次原版 Confirm；之后独立后读 Faith 成员、钱包净变动、额度与本决议冷却。只将观测记录为净变动，额外回调或同期效果的因果归属另外举证。

本轮生产审计位于外置 `episode01/native-candidate/cost-planning/production-audit-a01.json`，SHA-256 `0eeb9ca9ea87f0764f934f3e4f1040d0e1672528d582d000282661b5e2799842`；完整原版 getter/consumer/pins 在同根 `gui-source/` 与 `model-source/` 的 cost/cooldown 小包中。原件源缓存不代表已执行原版回调，函数静态闭合也不抵扣 native fixture 或 live 资格。

R3 期间已在外置隔离候选实现上述正文、费用、报价/affordability 和冷却读取；不修改当场 main/source/build/DLL。新增字段是 additive，旧六份 native 原包经候选 normalizer、生产 Driver/Service 和真实 MCP 协议重新消费通过，七份真实返回已保存在 `planning-legacy-mcp-a16.json`（SHA-256 `10564365e056b594a2e4d5431b36e80f526de2e92a897a040368d6cff28e4cad`）；新增原生夹具与新 live 资格仍待完成。免费额度继续 unknown。任何部分缺读不伪造为 false，详情正文不代表原版窗口已实际滚动/显示全部文字，`action_ready` 仍为 false。

## 2026-10-17 10:51 UTC 增量资格

`machine_id: 4-8e1c2f1861`；实际源树 `6fdbe14e8c182cf18ac9a2bf69b8c04350d50f51`。运行方在 R3 正常闭场后增量编译桥、detail 与受影响 navigation；本节更新了上节“新增原生夹具待完成”的状态，新增 live 资格仍待完成。没有创建另一套游玩智能体、放宽普通决议列表，或用脚本报价替代原生评估。

首次 `r4-increment-a01` detail 夹具 exit1 已保留：`0x2957F10` 代码 pin 写为 33B，超过既有 Pin helper 的 32B 上限，导致冷却观测不可用。修正提交 `2490464a444983e43a8d3f7db2330e9754520abd` 仅将它收窄为同一原始来源前 32B，未放宽校验器或更改冷却算法；20 个生产 pin 字面量的长度与来源前缀检查通过。不可变 a17 原件保留，另有一文件 a21 overlay。

新 `r4-increment-a02` 原生 detail 夹具实际 exit0，输出 `PASS checks=213 actual_reader=true actual_serializer=true synthetic_storage=true synthetic_callbacks=true live=false`，产生 17 份完整 command_result；navigation 同次 exit0。实际 DLL SHA-256 `05a2c7cc74008316040fe035bc08b6d11767668bdb2adb2b6006d31f5eb9c06b`。本 lane 随后于 `2026-10-17T10:51:44.006395Z` 从上述 main 实际加载生产 Driver、normalizer、Service/create_server，经真实 MCP ClientSession 完成 4 项测试、22 份返回、0 skip；17 原包在消费前后 SHA 不变。包括旧字段兼容、正文/报价/冷却独立缺读、活跃/过期锁、绑定变化、4 个明确手工畸形字段负例及异 build 拒绝；负例不算新的原生原包。

资格边界：生产 C++ reader/serializer 真正编译执行，但 fixture 的对象存储、代码/RTTI pin、回调和 episode/frame 均为合成输入；MCP endpoint 的 hello/frame 也是合成帧。没有在游戏内执行新增原版 getter、Confirm 或采用；测试文本、1000 虔诚报价、counter100/deadline172 均不能当作此存档的观测。

规划器继续调用同一个 `ck3_query_player_holy_site_adoption_detail_v1`，无需新增工具或 flag。先验证 `native_detail_context_verified`，再逐项使用 `native_requirements_description_available`、`native_cost_description_available`、`native_resource_quote_available` 和 `native_decision_cooldown_observed`：正文用于保留完整要求分支，quote 用于与同帧钱包比较，cooldown 用于区分当前 active、expired、observed absent 和 unknown。免费额度仍 unknown；零报价不推断剩余次数，`native_affordable=true` 不代替其他合法性，冷却 raw 差值不换算日历。任一缺读仍保留 null 与 reason；所有只读结果的 `action_ready=false`，后续提交须走既有 fresh 普通 CanConfirm 与一次原版 Confirm。

以下路径均相对外置根 `C:/workspace/ck3-faith-and-power-20261017/episode01/`；原件只 pin，不复制大回包入库。源码/资格未证明其他机器部署或实机通过。

| 证据 | 路径及 SHA-256 |
|---|---|
| 不可变源码 | `native-candidate/planning-freeze-a17.json` · `9bfafd817b8d6ac9fde980c2f584c3db3c0eb1e1cc0a2e1290232328d1825437` |
| 单文件修正 | `native-candidate/planning-pin-fix-a21.json` · `29dca6f700823a36de79f998c3e15a6953ceb61e530b1a0731d82d06e657ddb2` |
| 新增量真实原生资格 | `runtime/adoption-candidate-a03/r4-increment-a02/qualification.json` · `840ad9fcf718dfa5a14718b6831bb128e3014752cc84f9ed791ebf22698b3a34` |
| 真实生产 MCP 消费 | `native-candidate/planning-native-real-mcp-a22.json` · `d83c96bbe8b6dbaa998f46eef81ec10969af0d63e651f06c8cc1b51a60438485` |

保留当前原始来源、a01 RED、a02 原包与 a22 完整返回，以支持 R4 live 读回和故障追溯；按统一存储策略在 `2026-10-18T10:51:44Z` 前复核。该期限不自动删除正在引用的活跃输入，也不将过期资产永久保护。
