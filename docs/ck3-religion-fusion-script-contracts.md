# CK3 宗教脚本组合的已观察合同

来源为 `mod_religious_ritual_fusion` 研究与首轮实现。机器 `4-8e1c2f1861`，观察日期 2026-10-24；CK3 1.20.0.4／build 25734779，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。用户确认 Empire Faith Gate 是该原版版本组成。接口帮助、注册和有限机器码证据见[原生合同回执](../mod_religious_ritual_fusion/docs/evidence/implementation-native-contracts-2026-10-24.json)，不是实机功能验收。

- `every_rite_tenet`／`any_rite_tenet` 的缺省项为当前 Rite 核心；附加 `status=core` 会按所属 Faith 主礼仪的立场再过滤。读取分歧 Rite 自己的核心集合时使用缺省枚举，避免漏掉它的独有核心。
- `create_dynamic_rite` 接受多个显式 `core_tenet_override_entry` scope。三项不同且有效的覆盖加 `target_divergence=0` 可构造确定性目标核心集；未选旧核心可能保留为 permitted，不能把“不是核心”表述为内容已删除。
- 原版 `can_pick` 的部分唯一性规则从 `selected_tenets`／`selected_doctrines` 读同草稿其他项。用于最终组合校验时须先自排除当前候选，再按原语义求值，最后恢复；否则可把候选自身误判为冲突。不得因此删除整个唯一性检查。
- 四项苦行核心的互斥条件需要对最终核心集判断；既有 Faith 的 `has_tenet` 与最终草稿不是同一集合。投影仅限已证实的互斥块，其余旧信条检查仍保留原语义。
- `rite_can_choose_tenet`／`rite_can_choose_doctrine` 验证既存 Rite 上下文，不自动构成任意新草稿的全组合合法性证明。没有 `every_rite_doctrine` 枚举依据时，可用源绑定定义目录逐项查询 `rite_has_doctrine`；目录更新需要重新读源和审查差异。
- `save_temporary_scope_as` 有原版纯 trigger／决策 is_valid 使用依据；未注册的 `clear_list` 不应编造使用。清空本地列表沿用原版 `every_in_list` 内 `remove_from_list`。

以上知识可用于其他宗教 mod 的研究和测试设计；具体产品的合法组合、GUI、收费和存读档仍须在绑定 build 上独立实测。本次没有修改共享运行时或替其他产品授予通过资格。
