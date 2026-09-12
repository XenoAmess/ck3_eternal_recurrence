# “自动升级建筑”三期：资金来源选择需求与开发计划

状态：**三期实现与 R0025 实机验收 GREEN；正式发布收口中**

候选版本：`3.0.0`

产品目录：`mod_auto_upgrade_buildings/`

Steam Workshop item：`3800124956`

研究基线：CK3 `1.19.0.6 (Scribe)`、维护版 `2.0.0`

## 1. 需求结论

三期只改变自动升级的**金币来源策略**。玩家打开并执行【启用自动建造】时，应在同一个决议面板中选择：

1. **只用国库**；
2. **只用个人金钱**；
3. **优先国库**：国库不能完整支付本次金币费用时，改由个人金钱完整支付。

该需求在纯 CK3 数据 Mod 中可行，且不需要自制 GUI 或额外事件弹窗。CK3 1.19.0.6 的
`common/decisions/_decisions.info` 明确提供 `decision_option_list_controller`；原版决议使用
`decision_view_widget_option_list_generic`、`show_from_start = yes` 和多个 `item`，并在决议 `effect` 中以
`scope:<item.value> = yes` 读取玩家选择。三期应复用这条原生路径，让三个选项直接显示在决议详情面板。

总体可行性：**高**。建筑发现、605 条升级边、升级方式、15 日循环和后置扣费均不需要重做；主要改动集中在决议选项、角色资金策略、
生成器的支付资格判断与扣费分派，以及相应测试。

## 2. 当前 2.0.0 基线

- `common/decisions/build_decision.txt` 当前在确认决议后直接添加 `enable_auto_build`，再排队 `auto_build.0003`；没有设置选项。
- `tools/gen_auto_upgrade_buildings.py` 为每条升级边生成 `treasury >= cost OR gold >= cost`，因此 605 条边全部固定为同一种资格逻辑。
- `aub_pay_gold_building_cost_effect` 在目标建筑成功出现后再次判断：国库足额则调用 `remove_short_term_treasury`，否则调用
  `remove_short_term_gold`。这就是当前“国库优先、个人兜底”的实际来源。
- 当前生成结果有 165 条建筑链、605 条升级边；每条链每轮最多升一级，升级成功后才扣一次费用。
- `scope:aub_payer` 是当前真人玩家，国库和个人金钱都从同一角色作用域读取。多人局可因此按玩家分别保存策略，无需全局策略变量。

三期不得手改带 `GENERATED FILE. DO NOT EDIT.` 的
`common/scripted_effects/build_scripted_effect.txt` 或 `common/scripted_triggers/aub_building_triggers.txt`；支付逻辑必须从生成器改动后重建。

## 3. 冻结的三种资金语义

| 模式 | 金币支付资格 | 成功后的金币扣除 | 另一资金来源 |
| --- | --- | --- | --- |
| 只用国库 | 当前角色存在国库，且国库可完整覆盖本次金币费用 | 只扣国库 | 无论个人金钱多少，均不回退 |
| 只用个人金钱 | 个人金钱可完整覆盖本次金币费用 | 只扣个人金钱 | 无论国库多少，均不使用 |
| 优先国库 | 国库可完整覆盖时成立；否则个人金钱可完整覆盖时成立 | 国库足额时只扣国库，否则只扣个人金钱 | 保持 2.0.0 行为 |

共同规则：

- **不拆单。** 例如费用为 100、国库 60、个人金钱 60 时，三种模式都不能把两者合并成 120；该目标本轮跳过。
- “优先国库”按**每一次建筑升级**独立判断，不是先把整轮预算从某个账户预留出来。
- “只用国库”在当前政府没有国库资源时允许被选择，但会安全地跳过所有需要金币的升级；选项说明必须显式警告这一点。
- “只用个人金钱”在个人金钱不足时必须跳过，即使国库足额。
- 三种模式只控制费用中的**金币部分**。金币加威望、金币加虔诚和 scripted cost 仍必须同时满足其非金币资源；威望、虔诚继续由角色本人支付。
- 资金不足、非金币资源不足、建筑资格门槛不满足或升级失败时，建筑和全部资源均不变化。
- 不改变二期“成功后扣费、瞬间完成、每链每轮最多一级”的合同。

## 4. 决议面板交互

【启用自动建造】使用原版通用选项列表组件：

```text
widget
  ├─ 只用国库
  ├─ 只用个人金钱
  └─ 优先国库（默认）
```

- `show_from_start = yes`，玩家打开决议详情时立即看到三个选项。
- 三项顺序固定为用户指定的“只用国库 / 只用个人 / 优先国库”。
- “优先国库”作为默认选项，以保持旧版认知和最小误操作成本；玩家仍须能明确改选另外两项。
- 每个选项都有独立名称和说明，明确是否回退、是否拆单，以及复合费用中的威望／虔诚不受该选择影响。
- 点击最终确认后，决议在同一 `effect` 内读取瞬时 `scope:<item.value>`，先保存策略，再添加 `enable_auto_build`，最后沿用
  `auto_build.0003` 建立或复用唯一全局循环。
- 选择资金策略本身不产生费用，也不立即升级建筑；首次扫描时序继续沿用当前入口。
- 三期不增加“运行中切换资金策略”决议。玩家要改变策略时，先【禁用自动建造】，再重新【启用自动建造】并选择新策略。

建议的简体中文选项说明：

| 选项 | 说明草案 |
| --- | --- |
| 只用国库 | 每次升级只从国库支付金币；国库不存在或不足时直接跳过，不使用个人金钱。 |
| 只用个人金钱 | 每次升级只从个人金钱支付金币；个人金钱不足时直接跳过，不使用国库。 |
| 优先国库 | 国库可完整支付时使用国库；否则尝试由个人金钱完整支付。两者不会合并付款。 |

日常实现阶段只创作并审阅简体中文与英文。法、德、日、韩、波、俄、西七语只在用户明确要求正式发布时补齐，不把英文占位称为翻译完成。

## 5. 存档状态与兼容方案

推荐只增加两个角色 flag：

- `aub_funding_treasury_only`：只用国库；
- `aub_funding_personal_only`：只用个人金钱；
- 两者都不存在：优先国库。

不需要为“优先国库”再增加第三个持久 flag。这样能把旧存档天然映射到当前 2.0.0 行为：已经带有
`enable_auto_build`、但没有任何三期 flag 的角色继续按“优先国库”运行，不弹迁移事件、不重建循环、不改变下一次扫描时间。

每次确认启用时先清除两个覆盖 flag，再按选项最多设置其中一个，因此正常路径永远不会产生冲突状态。禁用时同时清除两个覆盖 flag；
重新启用会重新显示三项并保存新选择。若第三方 Mod 或异常存档造成两个 flag 同时存在，运行时采用“只用国库”优先的确定性规则，
避免在含有国库禁用意图的歧义状态下动用个人金钱；下一次正常禁用／启用会自动归一化。

必须继续保留以下公开兼容合同：

- `enable_auto_build`；
- `auto_build.0003`、`auto_build.0004`、`auto_build.0005`；
- `aub_auto_build_loop_started` 单实例 seed；
- 已排队旧事件在启用时汇入同一循环、禁用时零副作用的行为。

## 6. 推荐实现结构

### P0：原生决议选项

- 在 `build_decision.txt` 的启用决议中加入 `decision_view_widget_option_list_generic` 和
  `decision_option_list_controller`，不新增自制 `.gui`。
- 三个 `item.value` 使用 `aub_` 命名空间；默认选择为“优先国库”。
- 在决议 `effect` 中立即把瞬时选择投影为两个持久角色 flag，再执行原有启用入口。
- 禁用决议清除启用 flag 和两种资金覆盖 flag。

### P1：集中式支付资格与扣费

- 在 `tools/gen_auto_upgrade_buildings.py` 中生成一个参数化的
  `aub_can_pay_gold_building_cost_trigger = { GOLD = ... }`，统一实现三种资金资格。
- 605 条生成分支只调用该 trigger，不再各自内联固定的 `treasury OR gold`；全部原版 gate 和非金币资源检查保持不变。
- 改造现有 `aub_pay_gold_building_cost_effect`，按相同模式与相同优先级选择扣费来源。复合费用 effect 继续复用它，再扣威望或虔诚。
- 资格判断与扣费分派必须使用同一套模式顺序，禁止出现“资格按个人通过、实际却扣国库”或反向切源。
- 保留升级成功后才扣费的结构；特殊建筑失败回滚路径仍不得收费。

### P2：静态验证与构建

- 校验决议恰有三个唯一选项、顺序正确、优先国库为默认，且所有分支最终都设置 `enable_auto_build` 并复用 `.0003`。
- 校验两个持久 flag 互斥、禁用时清理、无 flag 时等价于旧版优先国库。
- 对全部 605 条边逐条验证：调用统一资金 trigger，费用参数与冻结 inventory 一致，复合资源门槛不丢失。
- 校验生成结果中不再残留 605 份固定 `treasury OR gold` 模板，支付 effect 不存在跨模式回退或拆单路径。
- 继续通过 165 链／605 边／4 条 Great Project 排除、生成可重复、静态本地化、release allowlist、manifest 和 deterministic ZIP 门禁。
- 若只修改既有决议、生成器、生成文件与本地化，正式 staging 仍应保持 15 文件；任何文件数变化必须由明确的新运行时文件解释。

### P3：抽样实机验收

不逐条实机运行 605 个建筑 key。建筑图谱没有变化，仍由静态全量检查负责；实机只验证资金策略这一项新机制及二期回归。

在同一 CK3 进程和一次性 `-userdir` 中至少覆盖：

1. 决议面板同时显示三个选项，默认高亮“优先国库”；逐项选择后保存的角色模式正确。
2. 只用国库：两边都足额时仅国库下降；国库不足而个人足额时建筑不变、两边都不扣。
3. 只用个人：两边都足额时仅个人金钱下降；个人不足而国库足额时建筑不变、两边都不扣。
4. 优先国库：两边都足额时仅国库下降；国库不足而个人足额时仅个人下降、国库不变；两边均不足时零副作用。
5. 国库与个人合计足额、但任何单边都不足时零副作用，证明没有拆单。
6. 任选一个金币加威望或金币加虔诚样本，证明资金模式只切换金币来源，非金币资源仍按原费用扣除一次。
7. 模拟旧存档的“已启用、无三期 flag”状态，确认继续走优先国库且不产生第二条循环。
8. 禁用后已排队检查零副作用；重新启用可选择不同策略，仍只有一条全局循环。
9. 成功样本仍只升级一级、只扣一次；项目相关 `error.log`／`debug.log` 诊断为零，产品树、fixture 和受保护用户资料符合既有隔离合同。

正式实机轮次必须使用该机器与本 Mod 的下一个递增编号；开始前取得 CK3 排他槽并证明 CK3 进程数为零。本次需求分析不占用 CK3 或屏幕。

## 7. 明确非目标

- 不新增个人优先／国库兜底、百分比预算、最低余额、单次上限或按建筑分类的资金策略。
- 不在自动建造已经启用时增加独立的即时切换决议；三期通过禁用后重新启用来改选。
- 不混合国库和个人金钱支付同一笔金币费用。
- 不改变 605 条适用建筑边，不新增空槽建造、住所、游牧／牧民地产或曼荼罗都城 Great Project。
- 不实现施工进度条、施工队列、取消或退款。
- 不改变 15 日轮询、每链每轮一级、原版资格门槛或成功后扣费。
- 本需求分析不修改 Mod、不同步 Workshop 缓存、不启动 CK3、不切换 Steam 在线状态，也不发布 Workshop。

## 8. 风险与控制点

| 风险 | 控制 |
| --- | --- |
| 把决议选项的瞬时 scope 当成可存档状态 | 在同一决议 `effect` 中立即转换为角色 flag，运行时只读取持久 flag |
| 资格检查和实际扣费使用不同模式 | 两者由同一生成器生成并以交叉测试验证来源一致性 |
| 旧存档无新 flag 后停止工作 | 无 flag 明确定义为 2.0.0 的“优先国库” |
| 只用国库在无国库政府下悄悄花个人钱 | 禁止回退，并在选项说明中显示“无国库则跳过” |
| 手改 605 个生成分支造成漂移 | 只改生成器，继续对 605 条边做确定性重建和逐边检查 |
| 新 UI 引入自制 GUI 兼容风险 | 直接复用 exact CK3 1.19.0.6 的原生通用选项列表组件 |

## 9. 预计工作量与完成标准

| 工作包 | 预计工时 |
| --- | ---: |
| 原生决议选项、模式持久化和中英文文案 | 0.5–1 小时 |
| 生成器支付资格／扣费重构 | 1–1.5 小时 |
| 静态检查、fixture 和构建回归 | 1–1.5 小时 |
| 一次抽样 CK3 实机矩阵与证据收口 | 1–2 小时 |
| **实现与验收合计** | **约 3.5–6 小时** |

正式发布另计约 1–2 小时，用于七语发布级补齐、正式 staging/tag、Workshop 完整 Change Notes、公开逐字回读、fresh-cache 复核和
Steam 离线恢复；只有用户明确要求发布时才进入该流程。

三期 implementation-complete 必须同时满足：决议三选一可见可用、三种模式行为矩阵通过、旧存档默认语义不变、605 条边静态回归
GREEN、抽样实机 GREEN。release-complete 还必须完成正式构建、Workshop 更新、订阅缓存复核、完整 Steam Change Notes 公开回读、
永久 changelog、tag、commit/push 和 Steam 离线恢复。

## 10. 依据

- 当前产品：`mod_auto_upgrade_buildings/common/decisions/build_decision.txt`、
  `mod_auto_upgrade_buildings/events/auto_build.txt`、`tools/gen_auto_upgrade_buildings.py`。
- 当前生成结果：165 条链、605 条升级边；`build_scripted_effect.txt` 中 606 次国库资格检查包含 605 条边和 1 个支付 helper，
  个人金钱资格检查为 605 次。
- 原版决议 schema：
  `C:\SteamLibrary\steamapps\common\Crusader Kings III\game\common\decisions\_decisions.info`，SHA-256
  `106977B58220107B66F537AADDA965F5A0602140DFB9BA7C79F3BA8BDD91CD9E`。
- 原版选项列表示例：`00_diarchy_decisions.txt` 和 `06_ce1_decisions.txt`；二者均使用
  `decision_option_list_controller`，并通过 `scope:<item.value>` 在决议 effect 中读取选择。
- 二期范围与现有实机合同：[auto-upgrade-buildings-phase-2-plan.md](auto-upgrade-buildings-phase-2-plan.md)。

## 11. 2026-09-13 实现与验收记录

三期实现已落在 `3.0.0`：

- 【启用自动建造】复用 CK3 原生 `decision_view_widget_option_list_generic`，按“只用国库／只用个人金钱／优先国库”显示三项，优先国库为默认。
- 只增加 `aub_funding_treasury_only` 与 `aub_funding_personal_only` 两个持久角色 flag；两者都不存在即优先国库，所以 2.0.0 旧存档无需迁移。
- 生成器集中生成 `aub_can_pay_gold_building_cost_trigger` 和同序扣费分派；605 条升级边全部调用同一个资格入口，不再各自复制固定的国库 OR 个人逻辑。
- 三种模式均要求单一账户完整覆盖金币费用；威望、虔诚和 scripted cost 的非金币部分保持原有检查与扣除。
- 九种语言已补齐 9 个新增／变更键；正式 staging 仍为 exact allowlist 15 文件。

静态与构建证据：

- `py tools/validate_auto_upgrade_buildings_static.py`：GREEN；165 条建筑链、605 条升级边，已安装 CK3 1.19.0.6 原版图谱逐字节一致。
- `py tools/test_build_auto_upgrade_buildings_release.py`：7/7 GREEN。
- `py tools/test_translate_localization_minimax.py`：26/26 GREEN。
- `py tools/build_auto_upgrade_buildings_release.py --check`：GREEN；实现提交 `1364537292f291735f315ceaceab06701d3e0c7c` 上的 manifest SHA-256 为 `20EC2930A507D7ADA8762F84B6764C80E0837C6C2CF899151E100F6D4B1EB375`，ZIP SHA-256 为 `933BA24CEF3F4F4BBB9985FC5DCFB1CDFC768CA1215614275CAAF7425D713A29`。

正式实机为 `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0025`，在 CK3 `1.19.0.6`、非 debug、隔离一次性 `-userdir` 中于 425.297 秒完成并 GREEN：

- 原生决议真实显示三个选项，纵向中心依次为 `689 / 774 / 859`；三项均实际点击，最终选择“优先国库”，再经二阶段确认执行。fixture 在任何自身 flag 修改前证明了 `enable_auto_build` 已设置且两个覆盖 flag 均不存在。
- “只用国库”在两侧足额时仅扣国库，国库不足时不回退个人；“只用个人”在两侧足额时仅扣个人，个人不足时不回退国库。
- “优先国库”保留旧版国库优先与个人兜底；国库 150、个人 150、单笔费用 250 时不升级且两侧余额不变，证明不存在拆分付款。
- 二期抽样回归继续通过城堡／城市／神殿／部落／曼荼罗神殿城塞主建筑、普通／公国／特殊建筑、金币加威望、金币加虔诚、scripted cost、原版资格拒绝、游牧／牧民 N/A、单级升级、停用与重新启用。
- 项目诊断为 0；产品树、fixture 树、源树和真实受保护资料均未变化；一次性 userdir 已删除，CK3 受控退出且最终进程数为 0。

持久证据目录：`D:\workspace\ck3_auto_upgrade_runtime\phase3-live-r1-20260913`（53 文件，116,273,013 bytes）。顶层 `report.json` SHA-256 为
`1314C1AD8E9B5AA2916892151932C42E6F75956AED7509D1C0F398F00092B706`；cell report SHA-256 为
`FE5D279ADD89D4C874381AD4E839BB1CCC257B5700F29D7D387372F43A405D7E`；实机加载的 production projection 树 SHA-256 为
`F03AF195BBDC6400CADCF107C19E2A8D0D151FD942DBB8517C448E7608178895`。

Open Kaishek 已成功由 GraalVM Java 启动并在 0.508 秒内返回报告，故本轮不存在 Java 启动器卡死或环境 RED。其 root parser 为 GREEN；产品专用 fixture 尚未被该工具注册、validator 尚未覆盖这些 CK3 opcode，因此适配器按既有合同将 `unknown-fixture / UNKNOWN_OPCODE` 记为 non-required semantic coverage RED；该结果不冒充语义验收，也不改变上面的 CK3 正式 GREEN。
