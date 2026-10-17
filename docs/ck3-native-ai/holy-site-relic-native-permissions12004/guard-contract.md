# exact4 HolySite 许可与提交边界

machine_id: `4-8e1c2f1861`。本轮身份由 `tools/ck3_live_run_id.py machine` 逐次读回；精确观察 UTC、完整文件 SHA、代码字节 SHA 和来源路径见本目录 `source-pins.json`。目标 EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。

本轮只复用已有 `.text/.rdata`、named locator、xref 和 pdata 查询缓存作有限范围反汇编。没有读取或复制 EXE，没有更改共享缓存、主树、旧候选，没有操作游戏、屏幕、Steam 或 lease，也没有重跑旧资格。以下均为 `SOURCE_REVIEWED_STATIC`，不授 ABI live、供奉/移除业务或 action-ready 资格。

## 这轮只读 helper 可直接复用的 ABI

Microsoft Windows x64，地址均为 image-base 相对 RVA。

| 方法 | 施工 ABI | 原生语境 |
|---|---|---|
| `17D53F0` CanEnshrineArtifact | `bool(window*, artifact*)`；RCX=真实 CHolySiteWindow，RDX=已验证完整对象 | 显式 artifact 参数；site 来自 window+C8，actor 来自 DWORD 全局 `54DBC00`。读取 window+110 的 InventorySlot*，经 `22E42F0(site+28, slot*)` 转 index；null/找不到是 −1。栈构造 command 后调用主 vtable+30，tooltip=null。没有选择 artifact、改槽、克隆或 submit。 |
| `17D56F0` CanRemoveEnshrinedArtifact | `bool(window*, artifact*)` | 显式 artifact 参数；同样绑定当前 site 和全局 actor，栈 command 后调用原生移除 guard，tooltip=null。 |
| `17D5970` IsEnshrineButtonEnabled | `bool(window*)` | 只针对 **window+108 当前所选 artifact**。无选择/坏 fullID/magic 不对则 false；artifact+7C 已等于当前 site 时 false，再以 window+110 语境构造并验证 command。 |
| `17D5E40` IsRemoveButtonEnabled | `bool(window*)` | 只针对当前所选 artifact；要求 artifact+7C 等于当前 site，再验证移除 command。 |

请求 artifact 与窗口当前 artifact 必须分字段。若两者不同或窗口未选择，当前按钮 false 不能解释成请求 artifact 的最终拒绝。建议报告 `requested_artifact_id`、`window_selected_artifact_id`、`button_context_matches_requested`、`selected_slot_index`；后者只表示原生当前选择。不能为只读观测调用 SelectArtifact/ToggleSelectedSlot 制造 UI 状态。

调用前要核窗口原生类型/owner/root、窗口+C8 与请求完整 HolySite ID、显式 artifact 完整对象/magic、全局 actor 与当前 snapshot player；调用后再次读取这些身份和 snapshot/PID/generation/date。所有指针只在既有 owner callback 生命周期借用；不跨 reload 保存。UI 模型存在与可见像素是不同证据。

## 最终 command guard 的实际输入与条件

两个主 command 都是 0x30 字节，以下是 **command 起点**偏移：`+20 site_full_id`、`+24 artifact_full_id`、`+28 actor_full_id`；enshrine 另有 `+2C int32 slot_index`。不能把 secondary 接口偏移与主 command 偏移混用。

`29AB4F0` 的 ABI 为 `bool(command*, native_string_or_null*)`，第二参可为 null；此函数是主 vtable `4770930 +30`：

1. 按完整代际解析 site 与 artifact，并核 magic/非 FFFFFFFF，拒绝 default/sentinel 代理。
2. 调用 `2531200(artifact, site, null)`：按**县主持有者信仰**认可圣物，未附加该信仰必须已认 site 的 membership 测试。失败且提供 tooltip 时再调用一次带 tooltip 的认可函数，随后 false。
3. 若请求 slot 在范围内且允许该 artifact type/category，使用该 slot；否则调用原生 `2C805E0(site+28,artifact)` 取兼容 index。不能猜第一槽，原选择无效不保证无替换。
4. 调用 `22E44A0(inventory,artifact, allow_filled_slot, tooltip, already_owned_by_this_site)` 检查库存/装备槽许可。该函数的 HolySite 分支会检查目标 slot 类别并调用原生 slot eligibility helper `30FE7B0`；此嵌套 helper 的 trigger 实现未在本窄包展开。character inventory 分支是另一条路径。此层不是“玩家拥有 artifact”的独立证明，GUI 候选另外来自当前玩家 Inventory。
5. 从**实际生效的 slot**读取被替换 artifact fullID，调用 `1D64FD0(new_artifact,site,actor,replacing_id,tooltip)` 的 compiled `can_enshrine_artifact` rule。
6. 若旧 slot 有有效物品，还调用 `1D651F0(old_artifact,site,actor,new_artifact_id,tooltip)` 的 compiled `can_remove_enshrined_artifact` rule。

原 slot=-1 的自动兼容槽和替换对象不能由仅返回 bool 的 CanEnshrine helper臆造为已观察值；若本轮不新增原生 picker 观测，就保留 `effective_slot_index` / `replacing_artifact_id` 为 unknown/null。未来 action 才能在提交前按实际选定的槽位与替换对象精确冻结。

`29ABB20` ABI 同样是 `bool(command*, native_string_or_null*)`，主 vtable 为 `47707D0 +30`。它解析同样 site/artifact，调用 `22E4420(site+28,artifact)` 核实际库存成员，然后以 replacing=FFFFFFFF 调用 `1D651F0(artifact,site,actor,FFFFFFFF,tooltip)`。CanRemove 与当前按钮额外的 selected artifact/owner gate 应分别呈现。

脚本桥 `1D64FD0` / `1D651F0` 以 artifact 为 root，绑定 holy_site scope(tag23)、actor scope(tag4)、replacing artifact scope(tag31)，从 compiled rule 表取供奉/移除规则。原版脚本三种地域管理者权限、供奉额外要求 actor.faith 认 site，均仅是完整 command 的其中一层；不能复写成 Python 法律检查后宣称与 native guard 等价。

## 错误文字与查询副作用边界

这四个 bool helper 没有在本体中提交 gameplay command、刷新世界 Active 缓存或改变所选物品/槽。但它们不是纯内存 predicate：认可、slot trigger 和 compiled rule 会进入脚本上下文、分配/TLS；深层 RNG/任意载入 trigger 的副作用未完全核实。必须保留 `script_rng_effects_verified=false`、unknown，不授幂等提示或任意线程调用资格。应沿已经限制为 paused、application-main religion owner callback 的路径调用；此静态研究没有重新证明其他线程安全。

传 tooltip=null 时，native false 没有完整原因文字。可以报告原生 guard false 及独立观察到的前置状态，不能把静态推测原因写成引擎返回。用合法 native string 走 tooltip 的两条原版路径已找到：

- `17D5A60(window*, output_native_string*)` GetEnshrineButtonTooltip：无当前选择/当前已供奉有专用提示，否则生成 artifact 标题，以真实 slot 构造 command，调用 `29AB4F0(command,&temporary_string)`；false 且临时文字非空时附加原因。
- `17D5F60(window*, output_native_string*)` GetRemoveButtonTooltip：无选择/当前非本站供奉有专用提示，否则调用 `29ABB20(command,&temporary_string)` 并附加原因。

两者在 RAX 返回 output 地址。输出是 32 字节 MSVC/native string 语境，有 SSO/heap 所有权与销毁要求，不能把 Python buffer 或自造 tooltip 对象塞进去。它们显示的是当前 UI 选择，不能解释另一显式 artifact 请求；也不是完整效果/费用预览。若本轮 helper 不接已验证的 native 字符串生命周期，`failure_text_observed=false/value=null` 是正确边界。

## 克隆、排队与真正执行 receiver

`29AC540` / `29AC640` **不是 Execute**。它们的 ABI 是 `command_holder*(command*, command_holder* out)`：分配 0x30 字节、复制字段、写主/secondary vtable，返回 out。enshrine 主/secondary 为 `4770930 / 4770A90`；remove 为 `47707D0 / 47706D8`。

原版 `OnEnshrineButtonClicked 17D5DD0` / `OnRemoveButtonClicked 17D62F0`先重跑当前按钮 predicate，再调用 `17D7580 / 17D76C0`：克隆，调用 `37F06D0(manager@5CC1240, owning_command_holder*, flags=0xE, ..., output_holder*)` 提交一次，随后清所选 artifact；供奉提交 helper 还清 window+110。`37F06D0..37F07C9` 会将 command 所有权移入 manager queue（`880340`）；其 bool 成功只表示接收/排队，不是效果后态。

真正变更 receiver 是 command+18 的 secondary vtable **+8**：

| 业务 | secondary vtable+8 | receiver this 的偏移 |
|---|---|---|
| 供奉 | `4770A90+8 → 29AADE0..29AB4EA` | RCX 必须是 **主 command+18**；site 在 receiver+8、artifact+C、actor+10、slot+14。 |
| 移除 | `47706D8+8 → 29AB8A0..29ABB11` | 同样是主 command+18；site+8、artifact+C、actor+10。 |

供奉 receiver 重新解析对象/slot，调用 `2530300` 变更新 artifact 所属 HolySite，必要时 `252FDD0` 将旧物归 actor，再经 `22E4B50` 装槽，添加历史/执行供奉及替换移除回调。移除 receiver先核库存成员，添加历史/移除回调，再将物品归 actor，或在无有效 actor 时经 `22E5310` 从库存移除。它们是实质变更函数，绝不可被 readonly helper 调用。主 vtable+80/+88 是属性序列化/反序列化，不是 Execute。

本窄包未闭合 manager queue 的完整消费调度、其中每次 CanExecute 重验顺序、终端业务回执格式或最终角色效果落地。不能从上述 receiver 地址外推业务已发生，也不为这轮新增直接 command 构造、submit 或 receiver 通道。

## 补充：下一轮 typed UI 最小选择入口

注册名已通过缓存 xref 和实际指令边界闭合，两个 callback 都先验证 GUI Any 的参数类型，再调用 leaf：

| GUI 名称 | registrar 内实际 name-load / callback | leaf 行为 |
|---|---|---|
| SelectArtifact | `2D1AB9` / `17D8860..17D88F4` | `17D52B0(window*,artifact*)`：非空读取 artifact+10 写 window+108；null 写 FFFFFFFF。**不清 slot、不装备、不提交命令**。leaf自身不做 fullID/magic 资格守卫。 |
| ToggleSelectedSlot | `2D0E93` / `17D84A0..17D8534` | `17D52F0(window*,InventorySlot*)`：nonnull 与当前+110相同则清零，不同则保存该指针；**null 是 no-op**。不清 artifact，不提交命令。 |

`22E42F0..22E433A` 用 site Inventory 的真实 24B slot 数组逐项比较地址并返回 index，找不到返回 −1。未来公共接口应接 `(holy_site_full_id, slot_index, desired_selected)`，由内部对本帧当前 site 解析 slot 地址，不暴露任意指针；按当前选中状态决定是否需要一次 toggle，未知结果不得盲重放。SelectArtifact 与 slot 的 UI 后态仍须独立读回，不能把 callback 返回 true 当选中正确。

原版 SetSite 可见写会清 artifact，且经 `17D7810` 更新 slot/inventory view；本轮未证明深层 data-model 更新会清除所有旧 slot 指针。因此每次站点/代际变更都必须重新证明 window+110 是当前 site 的真实 slot，不能据上次选择沿用。

## 来源完整性与保留

使用的是有限 cache bytes。某些新地址的共享 pdata binary-search 记录缺 `145134`，六次函数边界查询都拒绝了 EXE fallback；随后只以明确 vtable/callback entry、已解码分支、RET/下一入口组成有标签的 bounded packet。初次 `toggle-slot-registration-tail` 起始落在上一条指令内部、`inventory-enshrine-guard-end` 起始也未对齐；两件仅保留为 superseded 探索，不作 ABI/语义依据，正式替代是 aligned/completed packet。泛用 dispatch 探索只按 bounded unknown 保留，不宣称完整函数。

复核期限为 2026-10-18 UTC；用于当前一期许可 helper 与 typed UI 后续施工，或原版 EXE/GUI SHA 变化时提前复核。整包不含新的 EXE/大段素材副本。
