# R06：父链失败后的独立本地前缀续查候选

本候选基于冻结 `c743520929d4f9a82c17c908b218075018598e2d`，承接[R184原版source与实际诊断](episode04-r184-r06-local-prefix-12004.md)。目标只是在原8层父链失败时保留**独立稳定的本地definition/first-match entry**，取得具体provider slot2 RVA或完整本地无匹配事实；不解算最终receiver，不执行provider，不触发toggle/ADD。

准备机器 `machine_id: desktop-3fevhd2-1c74096080`；观察时间、来源/目标文件pins见 `ROOT-DELIVERY.actual-a29.json`。本包只读代码、已持source文本和仓内R184小证据；未读取原1MB tree/游戏save/EXE，未联系SDK/游戏/桌面，未构建。Root报告a28仍depth8/read51/pass1；本包直接消费的实际小证据是R184 a27，未伪造a28另一次原件核验。

## 原版来源先于新字段

已持完整 `3AC38C0` 在 `3AC3AD0..3AC3B34` 先按callback声明key查本地definition+90/+9C的stride50表、entry+48 first match，再调用 `3AC1C00`；到 `3AC3B55` 才进入父链 `3AC3EF0`。因此本地lookup是可独立完整记录的前缀。`3AC1C00` 的mode0/1是direct路径，mode>=2沿provider+0 vtable的slot2分派；读取此slot是下一唯一source候选，不是获得调用许可。

原reader已在父链之前读过本地前缀，但失败返回会清空candidate entries/index/key。R184 pass1的depth8诊断只说明**第8层当前context的definition尚未读取**，所以其presence/count必须null。它不证明definition不存在，也不能用51反推真实链布局或本地entry内容。现有20ms、4096次、64KiB、8层和每tree4capture守卫保持。

## 最小实现

仅修改现有reader/DTO、serializer、严格Python合同，加一个独立native fixture目标。没有新MCP、hook、native getter、表达式执行器或全局缓存。

`once`在完成depth0 first-match以及既有direct/provider标量读取后，保存完整private identity：callback/context、声明表/index/key、definition/table/count/active、已查key前缀、匹配entry/direct/provider/vtable/slot2等。first match之后的无关尾项不读取；raw地址仅作私有double-read比较，不序列化。

- 两次完整父链capture成功时，直接复用它们各自的local快照，不做第三次读取。
- 首次父链在local完成后失败时，先复制其原reason/diagnostic，再用**同一个load闭包、原reads/bytes/started时钟**做一次仅到local的复核。depth0之后立即返回，不读parent指针。两个local私有identity和结果完全相同才发布。
- local第一次未完成、复核不完整/改变或原共享预算耗尽时，新leaf为unavailable，稳定观测字段保持null、entries空；不借首pass partial发布。
- 第二次完整capture后续失败或两份父链不一致时，本地leaf仍只按两份完整local快照单独判定；旧candidate继续保留自己的原失败语义。

旧 `receiver_entry_candidates_12004.status=unavailable`、null index/key、空entries、stable=false和`failure_diagnostic`不会被新leaf改写。例如depth8/read51/pass1仍是原失败；新增复核的失败诊断只属于新leaf。

## 同一family的严格新leaf

路径为固定补员expression下：

```text
receiver_entry_candidates_12004.local_definition_entry_only
```

source固定 `native_gui_type635_local_definition_entry_only_12004`，scope固定 `local_definition_entry_only`，ancestor_depth固定0。它继承现有精确source pin、固定expression、owner-thread、frame/GUI-owner guard和每tree4capture准入；没有用callback+F0冒充最终MilitaryView。

available须同时有两次稳定本地读、type635声明/index、实际local definition presence/active byte和完整raw entry count，及明确bool `local_entry_present`。matched时至多一行depth0 entry，按现有模式发布mode/flag、direct/provider presence、模块内vtable/slot2 RVA和已有可选direct-owner标量；非模块内/未取得RVA为null，不补0。local complete empty为available/entries[]/present=false；这只排除**该本地表**匹配项，不排除ancestor。

unavailable要求reason、stable=false、空entries，index/type/count/active/presence均null。可选failure diagnostic是一次失败读的进度，不是稳定entry。旧leaf缺席兼容。`current_variable_table_observed=false`、`native_receiver_selected=false`始终固定；parent unavailable可以与local available同时存在，合同拒绝将二者混成selected receiver。

serializer共享原entry/failure格式；frame serializer保持原字节。Python复用原entry的width/RVA/owner验证，并额外拒绝非depth0、本地多行、available缺稳定证据、失败partial和未经允许的pointer字段。

## 真正解除的unknown与下一步

此口能解除“本地prefix因更深父链失败而无法独立取证”的观测缺口。若实际leaf有合法provider slot2 RVA，下一最小source动作是只围绕**这个实际RVA**建立有限`.pdata`/完整body计划，先闭参数与写入行为，再判断是否存在可接的纯getter。不能在取得RVA前猜callee，也不能直接调用3AC38C0/3AC3EF0或provider。

若local为direct，仅提供候选标量供独立身份验证；临时variables、pending-parent选择、`3E4BC50`及最终receiver仍unknown。若local完整为空或没有合法provider RVA，而父链仍必需，下一步才是单独授权的显式新profile设计；本patch不把8改成16/32，也不承诺某个深度能到达。

## 必要检查与未验收项

只执行四组新Python合同检查：实际R184旧failure保持不变并接受作者构造的独立local provider叶；available empty/unavailable/absent区分；不稳定或selected/失败partial拒收；越层/非法RVA/raw pointer拒收。它们验证生产normalizer接线，**新local叶均为合成数据**，不是R184或a28实际新观测。

已写独立 `BUILD_TESTING=ON` / `EXCLUDE_FROM_ALL` target `xar_test_gui_refill_local_prefix_12004`，不链完整bridge，覆盖五组新行为：

1. 稳定local+depth8/read51旧失败并存，以及完整本地无匹配；
2. 第二次mode、flag、provider私有身份（即使公共RVA相同）或slot2变化拒收；
3. local所需字段未完成不发布partial；
4. first match后不可读尾项仍不读取；
5. 首次父链失败后，额外local复核消耗原20ms预算而不授available。

fixture中构造的一种链也用51次读，并不声称它就是R184真实私有链。native fixture、reader/serializer执行、syntax compile、完整DLL和生产wire都**NOTRUN**；本任务禁止build，交由Root后续正常producer验证。只有新的同帧实际tree发布稳定leaf并通过严格consumer，才能写“取得本地provider来源”。当前没有新receiver、toggle、补员ADD或业务通过。
