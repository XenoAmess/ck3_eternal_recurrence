# 礼仪改革扩展的自动兼容与宗族化密教

观察机器：`machine_id: 4-8e1c2f1861`。观察时间：2026-10-25T09:57:29Z；工作区 HEAD 为 `a4bdcaaa57f981d107fdfd7440b6d6eaf1d7e9e4`，同时存在本轮其他任务的未提交改动。此文是用户第 8 项反馈的只读研究，不代表组合已经通过实机验收。本轮没有修改生产脚本、Java、Steam 状态、游戏或 Git；只新增本文。

## 结论与施工建议

普通教义／教义组扩展具有复用原版数据模型的路线；任意 GUI 修改没有自动合并保证。原版礼仪创建窗口的 `GetCategoryHelper('main_group').GetCategory` 会按真实教义组生成当前项，组内 `DoctrineCategoryWindow.GetDoctrineItems` 再生成候选。宗族化密教恰好采用这个标准扩展点，没有覆盖原版 GUI，因此保留原生创建／编辑模型时，它的新组可以沿用原生流程。

RRF 当前的静态 catalog 不会自动接纳新模组定义。单纯把候选改成运行时全枚举也不够：它还必须正确识别隐藏元数据、组内互斥、组创建资格、锁、当前选择组合和角色知识。不能为了“自动”而让未知教义绕过这些条件。

建议优先保留不覆盖原版 `window_rite_creation.gui` 的设计；在确实能够保留单一提交权威、满足原生入口资格的地方复用原生模型。若最终仍采用 RRF 独立草案／脚本创建，则将“自动发现”和“可安全编辑”分开：运行时发现外部内容；有效定义图和扩展合同提供分组、显示、选择、锁及后续生命周期语义。未能解释的新扩展应显示缺口，不能假装已完整兼容。原生创建入口的自身资格限制见同目录 `native-creation-options-2026-10-25.md`；本研究没有找到公开的任意草案初始化／导入接口。

针对宗族化密教的最小行为合同为：两模组同时加载时提供“无／宗族化”单选；默认沿用源 A 的当前选择；双方都为“无”时仍允许主动选“宗族化”；取消不创建宗族；选择“无”不产生宗族化业务；选择“宗族化”只作用于融合后新 Rite，两个来源和历史绑定保持不变。此项是可选的改革扩展，不作为“两来源独有贡献”的必要条件。

## 宗族化密教的实际接入

当前源码没有 `gui/`、`common/scripted_guis/` 或 `common/game_rules/` 生产目录。它的选择入口是标准教义定义，业务接入为普通 on-action 和 scripted effects：

| 对象 | 实际定义 |
| --- | --- |
| `des_dynastic_membership` | `category=main_group`、`divergence=category`、`doctrine_lock=none`、`is_available_on_create={ always=yes }`。不占核心信条槽。 |
| `des_doctrine_none` | 组内 `index=0`，分歧与虔诚费用均为 0；表示“无”。 |
| `des_doctrine_dynastic` | 组内 `index=1`，分歧与虔诚费用均为 0；携带 `des_dynastic_membership` 参数。 |
| 旧 Rite 初始化 | `des_initialize_rite_effect` 仅在两值都缺少时补“无”，不覆盖已有明确选择。 |
| 角色知识 | `des_teach_doctrines_effect` 给存活可玩角色加入两项 `add_known_doctrine`。因此不应另要求先知技能。 |
| 新局与旧档 | 新局经 `on_game_start`／`on_game_start_after_lobby` 初始化；旧档另有原生决议 `des_initialize_decision`。不能用“源目录存在”假称目标存档已初始化。 |
| 创建／更新 | 追加 `on_rite_created`、`on_rite_updated` 的子 on-action；没有替换原版整条 `effect`。 |
| 改信／出生／生成 | 追加 `on_rite_change`、`on_birth_child`、`on_character_created`，出生／生成后另延迟一天同步。 |
| 有限修正 | 持久 Religion 上的每 30 日维护队列；另有年度 watchdog。扫描真实 Rite，能发现其他脚本创建的动态 Rite。 |

“加载顺序在下面”应落实为 DES（及其他改革扩展）在前、RRF 在后。它本身不会把 RRF 固定的生成 catalog 变成运行时可扩展列表，也不会合并同路径 GUI。

## 提交后的宗族化时序

宗族化不只是写一个教义。`des_sync_character_effect` 进入 `des_join_rite_dynasty_effect`，继而 `des_ensure_own_rite_binding_effect`；有效信徒才能创立／修复新 Rite 对应 Dynasty 和 House。Rite 保存 `des_bound_dynasty`、`des_join_house`，Dynasty 保存反向 `des_bound_rite`；随后按真实 Rite 同步信徒并维护背离处罚。不能复制源 A 的绑定变量到新 Rite。

原版 `religion_on_actions.txt:442` 明确：`create_dynamic_rite` 跳过 `on_rite_created`。因此不能仅依据 DES 订阅创建钩子就宣称 RRF 独立 effect 自动完整兼容；也不应补发整条原版创建钩子，它会包含领地、朝廷、通知等其他业务。

不过，RRF 当前实际顺序为 `create_dynamic_rite(convert=no)` → 对新 Rite 写入选定核心／教义 → 最后 `set_character_rite`。当前 EXE 的 `set_character_rite` 帮助明确“executing the effects for it”；`set_character_rite_history` 才是跳过效果的历史设置接口。DES 同时订阅了 `on_rite_change`，因而最终正常改 Rite 有望及时走其既有共享同步路径。`on_rite_updated` 的原版注释也明确区分 GUI 消耗编辑 token 与 scripted effects 的变化。以上是有来源依据的接入推断，仍需验证实际回调、顺序、唯一绑定和信徒同步，不能把推断记为本机已通过。

若实际回调不足，应优先修订明确、版本化的扩展生命周期合同；不能直接复制 DES 业务到 RRF，或将每 30 日补救当成创建当场成功。DES 自身其他机器的 R0013 证据只证明其来源机器当时的执行，不授予本机联合加载资格。

## 实际运行时发现接口

当前 EXE 没有发现 `global_tenet`、`global_doctrine`、`every_doctrine_global` 这些精确字符串。迭代器的登记根名为 `character_tenet`、`character_doctrine`，脚本使用 `every_`／`random_`／`any_` 前缀生成相应形式。不能凭猜测编造 `every_global_tenet`。

### 普通教义

`every_character_doctrine` 作用于 Character，支持：

```text
scope:rrf_actor = {
    every_character_doctrine = {
        knowledge_filter = all
        # 可选：rite_filter = scope:source_rite
        # 可选：faith_filter = scope:source_faith
        # 候选是实际 Doctrine scope
    }
}
```

EXE 文件偏移 `0x4650140` 的帮助说明：按角色教义知识枚举，`knowledge_filter=known|unknown|all`；可以按 Rite／Faith 是否采用过滤；同时提供两个过滤时 Rite 优先，Rite 过滤还包含其 Faith 的教义。原版 `pam_heresy_shared_effects.txt:62–65`、`pam_effects.txt:6450–6453` 有 `every_character_doctrine` 和 `rite_filter` 的真实用例。默认知识过滤的具体行为不能擅自当成 `all`，完整来源快照应显式传入。

它能够发现两个来源当前采用、包括其他 mod 新加的教义，但这不等于枚举所有新组的全部可选兄弟项。DES 的“双方均无仍可宗族化”尤其不能只靠双方当前采用值的并集满足。

### 核心信条

`every_character_tenet` 有对应的 `knowledge_filter`、`rite_filter`、`faith_filter`，以及 `status=core|permitted|prohibited|known|unknown`（有 Rite／Faith 过滤时使用）选项。EXE 帮助位于 `0x464fdd8`。`every_rite_tenet` 是已存在 Rite 的真实核心列表，帮助位于 `0x4650058`；两个来源核心的去重并集应优先从这里取得，不从空槽 UI 或数字槽位生成对象。

### 已发现但不足以替代完整草案校验的 trigger

EXE `0x4782570` 的 `rite_can_choose_doctrine` 帮助明确：检查该教义的 `is_shown` 和 `can_pick`，**以该 Rite 的 head 为参考角色**。对应 `rite_can_choose_tenet` 位于 `0x478265b`。这与 RRF 当前实际融合者可能不同；不能把源 Rite head 的资格当成本次玩家资格。

该帮助没有承诺检查教义 `visible`、组 `is_available_on_create`、所有锁、RRF 最终组合或扩展自有状态。当前有界研究也没有找到普通脚本下通用的 Doctrine → DoctrineGroup scope link／动态组相等比较。因此独立选择列表的同组替换与显示过滤仍需要有效定义元数据或明确扩展合同，不能用遍历成功替代。

## 原版 GUI 的自动范围

`window_rite_creation.gui` 的标准入口为：

| 行 | 模型／条件 |
| --- | --- |
| 315、346、373、399 | 分别读取 `main_group`、`marriage`、`crimes`、`clergy` 四类的 `GetCategoryHelper(...).GetCategory`。类别键仍由 GUI 明确列出。 |
| 979–994 | `DoctrineItem` 提供 Faith／Rite／Doctrine／slot；打开原生当前组选择窗口。 |
| 1246 | `DoctrineItem.ShouldDisplay(TopScope.Self)` 决定该组候选是否显示。 |
| 1251 | `DoctrineItem.CanPick` 与原版 `pam_know_doctrine` 共同决定是否可选。 |
| 1253–1255 | `SelectDoctrine(DoctrineItem.Self)` 修改同一个真实草案，`HasDoctrineSelected` 显示其状态。 |
| 1409–1416 | `DoctrineCategoryWindow.GetDoctrineItems` 产生当前组真实候选。 |
| 1466–1478 | `TenetGroupItem.GetTenets`、`TenetItem.CanPick`、`SelectTenet`、`HasTenetSelected` 负责核心选择。 |

所以“在现有四类中新加标准教义组”与“创建第五个 category／替换整张 GUI／添加自有状态按钮”是不同兼容级别。后者不会因为 RRF 放在加载顺序下面而自动纳入现有四个 grid。完整原生草案还保存真实名称、图标、颜色、费用、美德罪恶及封臣接受度；脱离其上下文复制控件，不能产生同等业务。

## 静态生成器如何演进

当前 `CatalogReader.read(Path game, String machineId)` 只读取一个根的 scripted triggers、doctrine groups、tenets、doctrines；`CatalogGenerator` 依 catalog 生成候选初始化、同组替换、选择组合与已知内容识别。来源外的定义会被拒绝。将 97 个信条和 130 个教义称为“可自动兼容所有模组”不准确。

可施工的构建期扩展为：用 Java 强类型、版本化的 `LoadedDefinitionGraph`／`DefinitionSource` 合同传入有序的原版和 mod 来源；按 CK3 实际有效文件图及覆盖规则求最终定义；同名文件、同名对象、`replace_path` 和 helper 覆盖不能简单拼接。每条最终定义绑定来源 mod、相对路径、SHA、组、锁、可见性和规则 AST。然后由同一 generator 生成选择与验证，不新增一套宽松实现。支持新增标准项时不应手工维护另一张散落的 ID 表。

这属于“给定组合重建后自动适配”；它不是已发布 Workshop 载荷对日后任意新 mod 的无条件运行时适配。CK3 普通脚本没有在本轮证明可重新解析磁盘定义或自动合并任意 GUI。发布文案必须准确区分这些范围。

对于不能用标准 Doctrine 表示的新功能，建议预留统一的扩展协作点：发现／草案默认、选择校验、预览、提交前重验、实际新 Rite 已产生但采纳前、真实采纳后。扩展必须声明是否可取消、是否产生永久对象及后态验收方式；RRF 保持唯一创建与收费权威。采用 on-action 协作时，需要测试两模组均在、只有 RRF、只有扩展三种解析与运行状态，避免对缺席的 scripted effect／数据库对象留下不合法静态引用。这类需要扩展主动配合的接入不能叫任意模组零配置自动兼容。

## 必须补充的验收

1. 无 DES、只有 DES、DES 在上且 RRF 在下三种有效文件图；无 DES 时没有缺失数据库引用、虚假宗族化选项或错误日志。
2. 新局及已完成 DES 初始化的旧档；实际角色知道两项；双方都为“无”仍能选择宗族化，双方现有不同值时同组互斥有效。
3. 创建前编辑／取消／更换来源不建族、不迁人；新 Rite 选“无”不绑定新 Dynasty；源 Rite 选择和原绑定保持不变。
4. 选“宗族化”后：实际新 Rite 的教义正确、唯一 Dynasty／House 与双向绑定正确；创立者及实际转入封臣／至亲属于正确宗族；未改信人物不被迁移；无重复建族。
5. `set_character_rite`、`on_rite_change`、`on_rite_updated` 的真实时序；创建当场与下一日分别读回，不把 30 日维护补过当场失败。
6. 保存与独立冷载，核 Rite／Dynasty／House、开启／关闭选择、原来源和处罚方向；不得只看一个 doctrine 图标。
7. 同时加载 MTS v11＋DES＋RRF，RRF 最后；核心数 3–100 条件与真实内容过滤共用；MTS 的隐藏 selector 元数据不进入候选、贡献或美德罪恶。
8. 用新增标准教义组的最小组合输入验证通用接入；再用第五 category 或专用 GUI-only 扩展明确证明边界。静态 Java producer→生成脚本回归接入持久 CI，实机结果另记，不能互相抵扣。

本轮上述组合运行全部 `NOT_RUN`；没有把源码可达性、原版帮助、别的机器成功或更新 ACK 计为本机业务通过。

## 原始来源身份

以下 SHA 绑定上述机器、时间的实际读取。未复制游戏 EXE、完整安装树或存档；仅记录必要原文接口与摘要。本文不足 200 KiB，归入本轮 2 MiB 文档额度；按通用存储策略 `record` 期限复核，不为原始输入无限续存。

| 相对仓库路径 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `Crusader Kings III/binaries/ck3.exe` | 101040248 | `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` |
| `Crusader Kings III/game/gui/window_rite_creation.gui` | 45219 | `9476299fdbf0975e41923eac9b192d3fe0b2cd74a4da0d928d0da7974b7ea9f8` |
| `Crusader Kings III/game/common/religion/doctrine_types/_doctrine_types.info` | 11217 | `7a8f6f8e78f88f7c83de3c43239a5da2709777e9d56fed4ae031e98b76af2ffc` |
| `Crusader Kings III/game/common/religion/doctrine_group_types/_doctrine_group_types.info` | 2191 | `c7d8e667403b55666cde5efa66983e39f8004a4ae0e1239eea96fc9d5d72b7c3` |
| `Crusader Kings III/game/common/scripted_effects/pam_heresy_shared_effects.txt` | 22335 | `f6905cc0c6804b8e93df0180b3abbc67332e4c6fa234a7213bc917f137bcf46e` |
| `Crusader Kings III/game/common/scripted_effects/pam_effects.txt` | 369911 | `fc4c77974a7844c31c1271dcc2ace24b17906620a832658919aa281e42a2b94f` |
| `mod_dynastic_esotericism/common/religion/doctrine_group_types/des_doctrine_groups.txt` | 225 | `9817b4d229c24592c727b65aaec648bdc6d6be3a161da8034e2932f7bc143eba` |
| `mod_dynastic_esotericism/common/religion/doctrine_types/des_doctrines.txt` | 387 | `e117d09ebbe37dba74eb2395508236f63964f2f00fb89e1de07550191852365d` |
| `mod_dynastic_esotericism/common/on_action/des_on_actions.txt` | 3093 | `430d9e5c4a7a637acf4482f21dee9eb9f83617e4783571911fbe15a5fb7e0ca0` |
| `mod_dynastic_esotericism/common/scripted_effects/des_initialization_effects.txt` | 2015 | `59a5c07f5f71b429fd83b11311d62fb3dbbc85915f0198940566fc0f1b1f321c` |
| `mod_dynastic_esotericism/common/scripted_effects/des_binding_effects.txt` | 6675 | `f279cbc89b5f85433c81403964b0285c830095bf81f91f2c651177a51799e134` |
| `mod_dynastic_esotericism/common/scripted_effects/des_maintenance_effects.txt` | 3167 | `f83926ab7ca6a90b281a5562874dc1184c616b0ec0df80a82fd06ce5f1bca7cf` |
| `mod_dynastic_esotericism/common/scripted_effects/des_character_effects.txt` | 2639 | `a54faed9643296017d4a57239bb13c423b61ff8c6e739cab36cadd5721e94941` |

## 经 Root 授权后的最小实现交接

2026-10-25T10:29:37Z，`machine_id: 4-8e1c2f1861`。此前“只读”描述适用于上文研究阶段；本节起已按 Root 后续明确授权修改以下生产脚本。本节的 AST 回归已编写，尚未在子任务运行 Maven、CK3 或 Steam；Root 统一验证结果另记。

### 可选默认值的中立合同

DES 的 `des_register_optional_rite_creation_defaults_effect` 将实际 `doctrine:des_doctrine_none` 注册到全局变量列表 `xar_rite_creation_optional_default_doctrines`。注册前检查 `is_target_in_global_variable_list`，重复调用不重复加入，也不清除其他扩展注册的默认值。它不依赖 RRF 安装，不引用 RRF 私有函数／变量。

注册位于 `des_initialize_world_effect` 的一次性 `des_initialized` 守卫之前，并由既有 `des_maintenance_effect` 幂等补齐。原版没有本轮可证的 `on_load` 入口，所以不能说启动钩子一定会覆盖暂停旧档的新装版本。为此另定义中立 on-action `xar_rite_creation_collect_optional_default_doctrines`，仅追加子 on-action `des_register_optional_rite_creation_defaults`；消费者可以在实际创建前广播它，即使存档尚未拥有该全局列表也可注册。

原版 `_on_actions.info:104–117` 明确允许在多个文件声明同一 on-action，并以 `on_actions={...}` 追加子钩子，禁止直接追加冲突的 `effect`。RRF 的空 parent 与 DES 的子列表因此沿用原版合并合同；Root 负责消费者。新默认值只应应用于刚创建的新 Rite，不能应用到 source A、source B 或全世界。每个扩展的可选组应注册一个中性默认；同组扩展之间给出相互冲突的默认值不是本合同自动解决的情况。

DES 更新只修改现有三份载荷，无新增发布文件，因此无需扩展其显式文件清单。关闭宗族化时，既有共享 `des_sync_rite_effect` 已按 active gate 清理本产品背离状态／意见并停止强制加入；保留 Rite ↔ Dynasty／House 历史关系是其重新开启时复用同族的既有语义。新回归执行实际共享脚本，覆盖关闭后清理外部已迁出的背离者，同时保留其他来源的犯罪意见与历史绑定。没有擅自删除真实宗族、恢复旧 House 或消耗其他犯罪理由。

### 封臣真实原生预览与邀请

新增 RRF 两份独立文件：`common/scripted_triggers/rrf_conversion_triggers.txt`、`common/scripted_effects/rrf_conversion_effects.txt`。其入口仅针对玩家已经实际采纳且完成原生设置的新 Rite：`rrf_state=succeeded`、实际 `rite=rrf_last_result_rite`、该 Rite 的 `rrf_origin_founder` 为本人、`rrf_native_configuration_complete=yes`。Root 负责原生设置成功或明确保留默认设置后的完成标记。

| 入口／列表 | 业务含义 |
| --- | --- |
| `rrf_refresh_vassal_conversion_preview_effect` | 按实际 direct vassals 刷新原生可用性／接受度，不发送、不改信。 |
| `rrf_vassal_converts` | 唯一 AI 接受预测列表，直接供现有 GUI 消费，不另存第二份“actual acceptance”副本。 |
| `rrf_vassal_declines`、`rrf_vassal_ineligible` | 分别为原生不接受与当前原生条件不可用的人。 |
| `rrf_vassal_players` | 可发送但需要玩家自己回复的人；不按 AI 分数宣布其会接受。 |
| `rrf_can_invite_vassals_trigger` | 要求实际完成的结果与已显示预览身份一致，并且存在可邀请名单。 |
| `rrf_invite_previewed_vassals_effect` | 只消费点击时已显示接受者／玩家名单的快照；逐人重新检查同一真实 predicate。不会把刷新后突然出现的人偷偷加入本次发送。 |
| `rrf_vassal_invited` | 已尝试原生 dispatch 的防重放记录，**不是**已证实发送成功。写入先于原生 dispatch，未知结果不自动重发。 |
| `rrf_vassal_converted` | 仅实际当前 Rite 已等于新 Rite 的人。 |
| `rrf_vassal_pending` | 尚未观察到实际改信的已尝试者，包含尚未回复或未知结果；不冒称已证实存在 native pending interaction。 |
| `rrf_check_vassal_conversion_results_effect` | 重新读取实际 Rite 后态，不通过 ACK 判定改信。 |

`rrf_vassal_preview_result` 将上述列表绑定到一个真实新 Rite。只有结果身份改变时才清除旧轮名单与尝试记录；同一 Rite 的刷新、保存继续或再次点击不会撤掉防重放记录。

原生路由按当前实际 Faith 选择：同 Faith 不同 Rite 用 `sway_vassal_to_my_rite_interaction`，不同 Faith 用原版专供新信仰创建的 `ask_for_conversion_interaction`。前者只允许同 Faith，不能拿来覆盖 RRF 的新 Faith 分支。两者均保留原生 `is_character_interaction_valid` 和 `is_character_interaction_potentially_accepted`；前者也调用共享 `pam_sway_to_rite_variant_can_send_trigger`，没有复制 opinion 阈值、天朝接受度、原生拒绝 flag 或 AI 分数。

真实发送 effect 名为 **`run_interaction`**，不是虚构的 `send_interaction`。本轮 EXE `0x4864d10` 有精确登记及 “Execute/send the given interaction” 帮助；原版 `ep3_roman_restoration_events.txt:102–107` 对封臣采用 `interaction/actor/recipient/execute_threshold=accept`，注释明确复用新信仰创建转换行为；`00_culture_effects.txt:966–970` 有同类用例。发送必须在实际 actor scope 内执行，不能在 recipient scope 只填 actor 参数就假称已发送。

AI 通过真实接受度检查后使用 `execute_threshold=accept`；玩家分支使用 `send_threshold=decline`，不使用强制直接改 Rite。原版 `ep3_interactions_events.txt:3103`、多处 `10_dlc_tgp_scripted_effects.txt` 有该发送阈值用例；仓库 `interaction-notification-ack-live-fixture.md:205–209` 也记录过 human recipient 的真实 pending 发送，但它是其他历史场次，不抵扣本轮联合实机。

同 Faith 的 sway 是**逐人原生收费**：`pam_interactions.txt:3279–3290` 引用 `pam_sway_ruler_to_my_rite_cost_value`；该值位于 `pam_values.txt:9563–9599`，基准为 `minor_piety_value`，受位阶、herald、地产／灵性参数调整。不同 Faith 的 `ask_for_conversion_interaction` 没有定义 cost 块。实现每人提交前重新查询原生 available／valid，由原生最终校验、扣费或拒绝；不手扣虔诚、不预支、不假定免费，也不把上一人的 quote 当下一人的资格。原生具体费用、钱包变化和 pending／实际改信仍是实机验收项。

Root 需将两份新载荷纳入 RRF 清单并统一接 ScriptedGUI、结果页和九种语言。新增本地化键为 `RRF_CONVERSION_REQUIRE_CONFIGURED_RESULT`、`RRF_CONVERSION_REQUIRE_CURRENT_VASSAL`、`RRF_CONVERSION_NATIVE_UNAVAILABLE`、`RRF_CONVERSION_REQUIRE_PREVIEW`。逐人查看详细原生拒绝条件／费用时应使用实际目标的原生 interaction 上下文，不能仅用总人数代替原因。

### 新回归与验证边界

`OptionalReformAndConversionTest.java` 读取实际 DES／RRF 生产文件，经现有 `Clausewitz` 生产 parser 执行到达的 AST 子集；未知操作拒绝。八项覆盖幂等注册、暂停旧档中立 parent→child→effect 路径、关闭宗族化的真实共享清理、四类封臣名单、已显示名单快照和逐人可用性重验、玩家／未知结果不冒充成功且不重放、同／异 Faith 的实际路由，以及结果身份改变才重置尝试记录。测试中的原生交互返回是明确输入边界，不模拟原生 AI 公式，不授予游戏业务通过。

只读 `git diff --check` 实际退出 0；五份 CK3 脚本均保持 UTF-8 BOM、LF 且括号计数配平。这些是文件检查，不是引擎解析、Maven 通过或实机验收。

| 修改后来源 | 字节数 | SHA-256 |
| --- | ---: | --- |
| DES `common/scripted_effects/des_initialization_effects.txt` | 2771 | `f666725f9b4e9bc10b3184dcda0ebc7dbfe091634aa7664676451f5c02e541b3` |
| DES `common/scripted_effects/des_maintenance_effects.txt` | 3226 | `e377df47a9b047c0489cca34e371ed894ccefd252b6caec26f0b7d0e1e7d6f15` |
| DES `common/on_action/des_on_actions.txt` | 3493 | `f81f597c567034baeb7262664558228f906ed8f4db382466077c18f485b1576a` |
| RRF `common/scripted_effects/rrf_conversion_effects.txt` | 7268 | `820fc6ce3e1ddb6709591e16e7986c19df3587304b16434539f7897b14ce1e13` |
| RRF `common/scripted_triggers/rrf_conversion_triggers.txt` | 3046 | `63a362200a1cb5ee605bdbf62884b56ac1bcfb03617d170999d070b9e36d70e0` |
| RRF `tools/src/test/java/org/xar/ck3/rrf/OptionalReformAndConversionTest.java` | 26470 | `b4a7eee3f793961bf3ecc4800be41ca4398c240a38372ec429a328b52368ea85` |

