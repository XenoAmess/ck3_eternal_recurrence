# 机制合同

## 一期兼容合同

自动继任与禁止向上转封仍只对 `is_ai = no`、`top_liege = this` 且采用行政制、贤能制或天朝制的玩家开放。三份 succession appointment 覆盖文件保持原版 1.19.0.6 精确字节，只在五处候选分支加入玩家扣分。转封功能继续用 `xqol_no_vassal_transfer_guard` 标记本 Mod 对 `ai_should_not_transfer` 的所有权。

## 二期通用入口

二期决议使用 `xqol_human_ruler_trigger`：非 AI 且为统治者。各批处理不会绕过原版目标有效性、互动冷却、宗教保护、战争状态、囚禁状态或关系条件；没有合资格目标时结果数为 0。

### 自动召集防御援军

`on_war_started` 保存精确 `scope:war`，并在一天后向被宣战玩家发送隐藏事件；事件会重新确认开关仍开启、玩家仍是同一场战争的 `primary_defender`，再执行召援。延迟一日用于避开战争创建同帧尚未稳定的参与者状态。

候选来自盟友、领主、摄政、宗主、朝贡国，以及玩家确为家主时的同家系成员。免费关系 trigger 只接纳原版无需资源的同盟、强制服役领主、保证参战的宗主/朝贡关系、可参战摄政和同家系路径；战争 target trigger 排除已经参战、已经被召、敌方关系、宗主封臣冲突与其他战争冲突。通过后调用原版 `call_ally_interaction_event_effect` 的免资源防御核心；同一人物即使具有多重关系，也会因 `was_called` / 已参战检查只加入一次。

防御方调用不会支付资源。宗族成员召集、非家主的 coterie 家族召集、合同协助、议价效忠等存在威望、宗族威望、金钱、虔诚或其他代价的入口不在候选集合内；草原邦联已有原版自动参战逻辑，不重复调用。

### 批量改信

滑动条保存 `xqol_mass_conversion_threshold`，事件打开时只编辑 draft，取消不改持久值。确认后以 0–100 的 literal dispatcher 调用原版 `is_character_interaction_potentially_accepted`：廷臣使用 `ask_for_conversion_courtier_interaction`，领内统治者与朝贡国使用 `demand_conversion_vassal_ruler_interaction`。

通过门槛的人物收到内部异步互动；其接受值复用原版 `50 + religion_demand_conversion_default_modifier`，实际答复仍由 CK3 原版概率判定。每个答复递减 pending 并累计 accepted/refused；最后一个答复完成后显示统一气泡。运行期间禁止再次开始批量改信。

### 批量牵制索款与赎囚

牵制索款直接运行原版 `demand_payment_interaction`。足额模式要求 `gold >= golden_obligation_value`；现有款模式严格要求 `gold > 1`，原版 effect 会在不足时取目标当前全部整数金钱并消耗牵制。

赎囚直接运行原版 `ransom_interaction`，由原版 redirect 决定囚犯本人或其领主为付款人。足额模式按劫掠宗族传承决定使用 `increased_ransom_cost_value` 或 `ransom_cost_value`；现有款模式要求付款人至少有 1 金钱。只自动处理 AI 付款人，并在每笔同步交易前按实时余额重新检查。

### 批量附条件释放

七个内部互动覆盖 HRC、HR、HC、RC、H、R、C，其中 H=获得牵制、R=招募、C=要求改信。遍历顺序先最大化条款数，再按 H > R > C 作同规模排序。每个组合镜像原版三个选项的可用条件与接受分；第一个愿意接受的组合执行原版等价的释放、改信、招募和 favor hook 后果。

`tools/gen_xqol_phase2.py` 是 101 档阈值分派、101 个 scripted GUI setter、滑条 widget、两种改信包装互动和七种释放互动的唯一生成源；禁止手改带 `GENERATED FILE` 标记的产物。
