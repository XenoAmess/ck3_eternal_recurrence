# M7后续需求评估：部落权威不等于王权改名

只读复用当前原版和既有realm-law源码，得到一个明确provider边界。没有新Law adapter、Native API、生产补丁、Game/SDK服务/MCP执行或新局门槛。

原版`00_realm_laws.txt:310`的`tribal_authority_1`属于`tribal_authority` group。0→1的`pass_cost`引用`increase_tribal_authority_prestige_cost`，当前数值仍须Native最终报价。其`on_pass`写入独立`tribal_authority_cooldown`，著录期限10年；0→1的`can_pass`允许`innovation_all_things`绕过“仍有该变量”的阻挡。因此不能把Crown变量/计时器重命名后当Tribal合法性，也不能只凭“变量存在”跳过Native final CanEnact。

既有只读realm-law DTO的`GROUPS`只有`crown_authority`、`succession_order_laws`；formal Python又要求Crown group与candidate前缀，Native action mailbox在181–182行也拒绝非Crown group/key。当前不足不只是普通policy少了两条字符串，而是该正式读写合同没有Tribal final terms/identity。其他raw title-law身份观察接口须各自核对，不能替代完整Tribal候选、合法性、价格和回执。

下一自然机会只能消费实际当前Tribal actor/frame与真实active law/group，适用的只读candidate/final CanEnact/reason、完整typed price/balance、Tribal自己的cooldown和创新条件。已有Crown行、deadline和真实旧动作均不沿用。不通过现Crown私有提交路径尝试Tribal law。未来若源合同收口，仍需原始唯一动作、独立law/resource/title/succession材料、following及匹配checkpoint/cold零重放。

可复用资源线索：既有1.20.0.2 law ABI已明确十槽名称，prestige位于index1；这可以指导下一源码核对，不能自动提升为1.20.0.4 construction/Tribal现场槽资格。typed prestige余额getter本就存在，不重建原始getter。部落权威1的`can_change_succession_laws`等flag也不等于已移除分割继承或获得实际收益。

有限Source check已执行一次，来源SHA及确切合同见`SOURCE-BOUNDARY.json`。G2仍6/8，M7未完成；新局和录制无需等待这项更广政府机制资格。
