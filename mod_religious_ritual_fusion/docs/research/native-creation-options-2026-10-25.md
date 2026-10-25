# 融合窗口补齐原生创建能力的接口研究

`machine_id: 4-8e1c2f1861`；观察时间：2026-10-25T09:39:28Z。来源为当前工作区原版参考树和 Steam 实际安装的 CK3 EXE；二者 EXE 本轮独立读取为同一 SHA-256。此次仅阅读代码和二进制，没有运行 CK3、操作 Steam、修改模组生产代码或进行实机验收。Empire Faith Gate 按用户确认作为原版版本基线。

## 可施工结论

1. 原版礼仪创建窗口的名称、颜色、美德罪恶、封臣预览不是独立通用表单。它们消费 `CRiteCreationWindow` 的真实草案，并由其原生 `CreateRite` 提交。把这些控件贴进现有 RRF 独立窗口不会让 `create_dynamic_rite` 获得相同能力。
2. 四项自由名称存在普通模组可用的完整候选通道：原版事件 text controller 把文字存到指定角色的 localized text；本地化通过 `Character.GetLocalizedText` 读取；真实 `set_rite_name` effect 接受名称、形容词、信徒单复数的动态描述。需要实机验证输入、取消、提交、冷读；本轮没有将该候选写成已经通过。
3. 在当前 EXE 没有找到可用于 Rite/Faith 的独立颜色脚本 setter；`create_dynamic_rite` 现有帮助也没有颜色输入。真实颜色选择可在原生草案中使用 `RiteCreationWindow.SetColor`。保留现有独立 effect 提交权威时，不能给用户一个只会变色块、结果地图不变的“地图颜色”控件。
4. 完整复用原版元数据与真实改信预览的优先研究路线，是把双来源融合规则接到真实原生草案选择与提交上；这涉及提交路径迁移、分歧分支、原生知识与费用守卫以及终态观测，不能仅改窗口标题和按钮文字。
5. `create_dynamic_rite` 明确跳过 `on_rite_created`，原版创建后的领地／朝廷传播和接受者处理不能由现有 effect 入口自动得到。若维持独立入口，必须有自己的明确转换策略和同源预览；不能用显示双方原有信徒数冒充改信人数。

## 真实 GUI 数据模型

### 礼仪创建

`game/gui/window_rite_creation.gui`：

| 行 | 真实接口与作用 |
| --- | --- |
| 5–15 | `rite_creation_window`，1300×950，`Window_Background`、`Window_Decoration`。窗口上下文包含 `RiteCreationWindow.GetVassalConversionWindow`。 |
| 84–170 | 顶部名称、图标、地图颜色按钮；名称和颜色打开右侧编辑页。 |
| 190–247 | `GetTenets` 产生已选核心信条槽；可用真实 `TenetItem.GetSlotIndex` 打开信条选择。 |
| 271–280 | `widget_sins_virtues` 的模型替换为 `RiteCreationWindow.GetSins`、`GetVirtues`。 |
| 410–414 | `vassal_conversion_preview` 使用同一 `VassalConversionWindow`。 |
| 470、1631 | 编辑／创建原因由 `GetEditBlockers`、`GetCreationBlockers` 直接给出。 |
| 611–613 | 按钮 `enabled=CanCreateRite`，`onclick=CreateRite`；悬浮提示根据同一可执行状态选择具体 blockers。 |
| 660–727 | 四个输入框：`faith_name_edit`、`faith_adjective_edit`、`faith_adherent_edit`、`faith_adherent_plural_edit`。原文明确这些名字被代码引用，改名会破坏创建后的清空。四个 callback 为 `OnEditName`、`OnEditAdjective`、`OnEditAdherent`、`OnEditAdherentPlural`，每项最多 30 字符。 |
| 734–750 | 描述框 `faith_desc_edit`，`OnEditDescription`，240 字符。 |
| 780–782 | `colorpicker_simple` 的 `color=RiteCreationWindow.GetColor`、`oncoloredited=RiteCreationWindow.SetColor`。 |
| 867 | 图标选择 `SelectFaithIcon(FaithIcon.GetName)`。 |
| 1253–1255 | 真实教义选择 `SelectDoctrine(DoctrineItem.Self)`；选中态 `HasDoctrineSelected(DoctrineType.Self)`。 |
| 1475–1478 | 真实信条选择 `SelectTenet(TenetItem.Self)`；原生候选 `CanPick`；选中态 `HasTenetSelected(TenetType.Self)`。 |

`game/gui/window_faith.gui:1320,1364` 的入口为：

```text
OpenGameViewData( 'rite_creation', FaithWindow.GetSelectedRite )
```

这传入一个真实 Rite，供原生窗口初始化创建或编辑模式。它没有接收“两个来源＋任意已选 RRF 草案”的普通脚本参数。`RiteCreationWindow.GetRite` 在此窗口中的存在不能解释为已创建的新对象。

礼仪创建本地化 `gui/rite_creation_window_l_simp_chinese.yml` 明确：分歧达到 `NRite.RITE_CREATION_DIVERGENCE_FAITH_THRESHOLD` 时会创建新 Faith；未达到时可能在原 Faith 内创建 Rite。RRF 若借用真实原生提交，必须在提交前明确结果种类，不能让“同宗教礼仪融合”在原生分歧分支里悄悄变成另一种业务。

### 文化融合可借鉴的结构

`game/gui/window_hybridize_culture.gui` 同为 1300×950：左侧可编辑主体、顶部名称／颜色、页签（支柱、传统、美学），右侧 500 宽摘要。`:1054–1071` 根据 `CanHybridize` 显示 `GetHybridizeBlockers`；`:1288–1290` 的提交与禁用态消费同一真实模型。`:1335,1353,1371` 为三项原生文化名称编辑 callback，`:1403–1404` 为真实 `HybridizationWindow.GetColor/SetColor`。这些结构适合复用视觉节奏、明确摘要和就地阻断理由；不能把 `HybridizationWindow` 模型当成宗教模型。

## 四项自由名称：原版事件文字输入链

### 已有生产者

`game/events/dlc/tgp/tgp_dynastic_cycle_events.txt:1786–1792,2162–2164`：

```text
widget = {
    gui = "event_window_widget_enter_text"
    container = "dynamic_birth_name"
    controller = {
        type = text
        data = {
            key = new_realm_title_name
            # default ...
        }
    }
    setup_scope = {
        root = { save_scope_as = text_target }
    }
}
```

`game/gui/event_window_widgets/event_window_widget_enter_text.gui:11–12` 的输入框必须名为 `enter_text`，`ontextedited=EventWindowWidgetEnterText.OnEdit`。这个 callback 由该 controller 提供上下文，不是独立注册的 RRF scripted widget 通用的“写字符串到任意角色”函数。

同一事件 `:2270–2272` 对自定义输入分支调用 `set_title_name_dynamic = new_realm_title_name_entered_text`。它的本地化定义在 `localization/english/dlc/tgp/dlc_tgp_situation_decisions_l_english.yml:37`：

```text
new_realm_title_name_entered_text: "[ROOT.Char.GetLocalizedText('new_realm_title_name')]"
```

另有 `events/accolade_events.txt:173–178,305`：文字写入 `scope:acclaimed_knight`；`localization/english/accolades/accolades_l_english.yml:849` 从 `[acclaimed_knight.GetLocalizedText('new_laamp_title_name')]` 消费，证明不必把文字固定写给事件 root。

### 已有结果写入 effect

当前 EXE 文件偏移 `0x484c618` 为精确 `set_rite_name`；`0x484c638` 附近的 NUL 终止帮助说明可更改已有 Rite 的名称、描述和信徒名称，参数：

```text
set_rite_name = {
    name = key/dynamic description
    desc = key/dynamic description
    adjective = key/dynamic description
    adherent = key/dynamic description
    adherent_plural = key/dynamic description
}
```

RRF 候选实现为给创建者保存四个专属 localized-text key；在新 Rite 已创建但尚未宣布成功前，用四个专属本地化 key 将它们写入新 Rite。本地化应明确读取保存的 `rrf_actor`，不能在 Rite root 下继续用 `ROOT.Char`。示意（尚未实机）：

```text
scope:rrf_new_rite = {
    set_rite_name = {
        name = RRF_ENTERED_NAME
        adjective = RRF_ENTERED_ADJECTIVE
        adherent = RRF_ENTERED_ADHERENT
        adherent_plural = RRF_ENTERED_ADHERENT_PLURAL
    }
}
# RRF_ENTERED_NAME: "[rrf_actor.GetLocalizedText('rrf_custom_name')]"
```

四个命名事件按顺序输入能够直接使用现有原生单 text-controller。一个事件同时放四个 controller 是否各自独立初始化、是否写入各自 key，尚需实机；不能仅凭改四个 label 宣称已工作。需测试编辑、取消、回开、空值、超过长度、不同创建者、不修改来源，以及保存重载。普通 `GuiScope.AddScope` 接受 scope、`AddValue` 接受数值，本轮没有找到可靠的任意字符串参数通道；不得发明 `GuiScope.AddString`。

## 地图颜色的实际边界

原生草案的颜色编辑接口是确定的，但仍绑定该草案。当前 EXE 的有界精确扫描没有发现 `set_rite_color`、`set_faith_color`、`set_rite_icon` 或 `change_color` 名称。`set_color` 子串只有 `set_color_from_title` 及其帮助；它作用于 Title。相关 effect RTTI 只命中 `CSetConfederationColorEffect`、`CSetColorFromTitleEffect`、`CSetTitleColorEffect`，没有对应 Rite/Faith effect。此处是当前扫描的否定结果，不声称数学上排除了所有内部或替代命名实现。

`create_dynamic_rite` 的真实帮助列出 `save_scope_as`、`convert`、重复 `core_tenet_override_entry`、重复 `doctrine_override_entry`、`target_divergence`、`include_unknown`、`override_tenets_first`，并无 color、icon、name 输入。先前 effect 工厂／参数解析证据见 `../binary-observations-2026-10-24.md` 和 `../evidence/binary-observations.json`。不能把未知参数塞进去、忽略错误，再用 UI 色块假称地图颜色已应用。

如果改走真实原生草案创建，则应保留原生 `SetColor → CreateRite → 新 Rite.GetColor` 链，并对创建后地图／存档颜色读回；在这个链闭合前，颜色仍是未完成项。

## 封臣和至亲改信：实际链与预览

### 原生预览的来源

`window_rite_creation.gui:8,1069–1233`：

- `RiteCreationWindow.GetVassalConversionWindow` 产生真实 `VassalConversionWindow`。
- `GetVassalList → CharacterSelectionList.GetList → CharacterListItem.GetCharacter` 产生人物。
- 每行的 `CharacterListItem.GetText('acceptance')`、`GetText('acceptance_desc')` 是真实接受度和原因。
- `GetNumberOfVassalsToConvert/GetNumberOfVassals` 以及 subordinate 对应计数来自同一模型；`GetConversionActor(index)`、`IsSubordinateConversion(index)` 解释关系。
- 原生文案说 realm priest、close family 会转换，封臣／僚属显示会接受的人数。仅照抄这些句子不代表 RRF 自己的 effect 已执行了相同转换。

另有已有对象的真实转换窗口：`window_faith.gui:1335` 用 `OpenGameViewData('faith_conversion', FaithWindow.GetSelectedRite)` 打开；`window_faith_conversion.gui:3` 同样得到 `GetVassalConversionWindow`，`:167–170` 用 `FaithConversionWindow.ConvertFaithAndRite/CanConvertFaithAndRite` 提交。它可以给一个**已存在**的目标 Rite 做真实转换预览，不能凭空预览尚未创建的 RRF 新 Rite。创建结果再打开此窗是一种两阶段产品设计，会改变创建／采纳、收费、取消和孤立结果语义，不能暗中替代本次需求。

### `create_dynamic_rite` 跳过的原版后续

`common/on_action/religion_on_actions.txt:418–456`：root 为创建者，`scope:old_faith`、`scope:old_rite` 为旧身份；`:442` 明确说 `create_dynamic_rite` 跳过 `on_rite_created`。

原生按钮在代码中发送创建时转换邀请；已接受 AI 封臣会先得到新 Rite，on-action 接着对新 Rite 的信徒执行：

1. `pam_on_conversion_effect`，移除 `religious_reformer_modifier`。
2. 对实际持有新 Rite 的每个角色调用 `pam_convert_court_to_rite_effect={RITE=root.rite}`。
3. 已落地且最高头衔≥伯爵者调用 `pam_convert_domain_counties_to_rite_effect`。
4. 给新 Rite 设置 `pam_rite_grace_period` 和一年 `pam_rite_founding_window`。
5. 后续还有传奇、改革等处理；本轮未把整条 on-action 当作可直接无条件重发的 RRF helper。

因此仅 `trigger_event=faith_creation.1020` 不会重现邀请。该事件 `events/religion_events/faith_creation_events.txt:1244–1268` 仅分派创建通知、比较差异，并延迟一日通知同旧 Faith 的玩家；`:1370` 也说明其他玩家事件只是旁观，转换已先发送。

### 普通脚本可复用的真实 helper

| 文件与行 | 作用及必须保留的限制 |
| --- | --- |
| `common/scripted_effects/pam_effects.txt:11818–11836`，`pam_convert_court_to_rite_effect` | 输入 `$RITE$`，遍历在场 courtier/guest 和 away courtier；只选 physically-able AI、与目标同 Faith、不同 Rite、无 `ai_will_not_convert` 的人。它不遍历至亲或封臣，不等于全家自动转换。 |
| 同文件 `:11789–11814`，`pam_convert_domain_counties_to_rite_effect` | ruler 的每个持有伯爵领、同当前 ruler Faith、不同目标 Rite；首都另保留异 Rite clerical-region 持有者和 puppet 特例。 |
| 同文件 `:11840–11856`，`pam_convert_court_to_faith_effect` | 需要 `$OLD_FAITH$` 和 `$FAITH$`；只转换上述 AI 朝廷成员且其信仰为旧 Faith。 |
| 同文件 `:11645–11705`，`pam_sway_to_rite_on_accept_effect` | 需要 interaction scope（actor/puppet_or_actor/recipient 等）；先改信 recipient；若是新 Rite founding window 内相连的已落地 ruler，带其领域与朝廷；否则仅满足邻接等条件时带首都。不能丢失作用域直接当“批量封臣改信”使用。 |
| `common/scripted_effects/00_religion_effects.txt:1148–1173`，`rite_growth_convert_court_to_new_rite_effect` | 以 `scope:source_rite`、`scope:new_rite` 为合同；只从 source Rite 选 AI courtier/guest、away 和首都 pool，排除拒绝改信 flag。 |
| 同文件 `:1216–1262`，`rite_growth_convert_ruler_to_new_rite_effect` | 用 `set_character_rite_with_conversion` 改 AI ruler，带源 Rite 领域、朝廷及特定 clerical region；原文警告改信可能让 ruler 死亡。它是 growth 机制，不是创建预览的接受度模型。 |

RRF 独立实现若选择直接给符合条件的至亲／封臣改信，应把政策写明并共用一份 eligibility predicate 生成“会／不会＋原因”的列表与最终提交。涉及玩家、其他 Faith、拒绝 flag、效忠／宫廷变化、死亡和新出生时，提交前必须重新计算；旧预览不能授权未知对象。不能为了“看起来原生”显示一套原生接受度，实际按另一套简单 opinion 阈值转换。

## 美德罪恶

`widget_sins_virtues` 的定义位于 `window_faith.gui:2134`；默认消费 `FaithWindow.GetSins/GetVirtues`，创建窗口显式替换为其**草案**模型。`VirtueOrSinItem.GetTrait` 和 `GetFullDescription` 分别提供 Trait 与详细语义。已有 Rite 的结果显示应使用真实对象对应数据，不能在选完新信条后仍展示 source A 的当前美德罪恶作为“融合结果”。

源定义 schema 明确：

- `_tenet_types.info`：`traits` 给信条额外 sins/virtues，信条优先于 religion。
- `_doctrine_types.info`：教义也可定义 `traits`，同一 Trait 已在 religion 有定义时，权重较大的优先。

因此只取两个来源的并集或只按三个核心信条列图标会遗漏基础宗教、教义、同 Trait 冲突与权重。独立草案若要精确预测，需要和实际有效定义／覆盖顺序一致的 evaluator；对外部 mod 新增或覆盖定义不能静默使用静态原版映射。真实原生草案的 `GetSins/GetVirtues` 是优先复用路线。

## 原生草案接入时的验收边界

接入候选必须实际完成以下链，才可称“原版礼仪改革能力已补齐”：

1. 用实际双来源候选构建选择表；同组教义单选，三核心不重复，双方各至少一项独有贡献。
2. 同步每次真实 `SelectTenet/SelectDoctrine` 到唯一 RRF 草案或由原生模型反向校验；恢复、取消、换来源、退出再进不会留下另一套不一致选择。
3. 原生知识／`can_pick`、分歧、唯一性、姓名、图标和费用原因与融合守卫同时满足；按钮、tooltip、摘要、最终确认使用同一有效状态。
4. 最终只能有一个提交权威；不能先 `create_dynamic_rite` 又调用 `CreateRite`，也不能同时收两笔费用。
5. 精确读回新 Rite/Faith 身份、三核心、每组教义、四名、颜色、实际扣款、转换者与未转换者、原来源不变，并保存重载。
6. 对 `3182367229` 实际版本在上、RRF 在下的有效文件图复查原生 GUI、doctrine/tenet 定义与 helper。仅声明 load order 不构成兼容验收。

以上运行验证在本轮均为 `NOT_RUN`；本报告只授予可实现接口的来源依据。

## 原始来源身份

以下为原始文件字节 SHA-256；行号按 UTF-8 解码后的原文件计数。记录只证明本机本时刻的实际来源，不能外推其他机器安装状态。

| 路径（参考树根 `Crusader Kings III/`） | 字节数 | SHA-256 |
| --- | ---: | --- |
| `binaries/ck3.exe` | 101040248 | `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` |
| Steam 安装 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/binaries/ck3.exe` | 101040248 | `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` |
| `game/gui/window_rite_creation.gui` | 45219 | `9476299fdbf0975e41923eac9b192d3fe0b2cd74a4da0d928d0da7974b7ea9f8` |
| `game/gui/window_hybridize_culture.gui` | 40856 | `7c02f13aba11962c30b86ae05dd3c3db56e4cbe41b08a3bdf71fd8f0cc3d5bbd` |
| `game/gui/window_faith.gui` | 150682 | `67924e58ccba26d95853ac48af35d91a774f5ce6d2e7f32a0a033de3b9d51521` |
| `game/gui/window_faith_conversion.gui` | 4029 | `3e52e3c75bd0f177714a52fafd76a7bfcd67925e37275994118842d2fc2eb78b` |
| `game/gui/event_window_widgets/event_window_widget_enter_text.gui` | 1064 | `641343f830afcfdafb4fec0121aa41d98943f5037a11f2fc54e526b683516ef4` |
| `game/events/dlc/tgp/tgp_dynastic_cycle_events.txt` | 73901 | `c2db00c1c245131dc78741c2bdac7232c97b22db2212205ffd327ca4cb0e3cb7` |
| `game/localization/english/dlc/tgp/dlc_tgp_situation_decisions_l_english.yml` | 22691 | `e2cdfe7b41460668be98d15b742dee9c423540a20345fd64fa93fff78ceec186` |
| `game/common/on_action/religion_on_actions.txt` | 59475 | `ef9367ddf5f89c912b895743f8b72441e88af3a5b03a5c1a9eddea0e5681ee2d` |
| `game/common/scripted_effects/pam_effects.txt` | 369911 | `fc4c77974a7844c31c1271dcc2ace24b17906620a832658919aa281e42a2b94f` |
| `game/common/scripted_effects/00_religion_effects.txt` | 41530 | `5bf6b0df3316f72f711507c310a349d508a3b83aef99373ea6440de20e4e4931` |
| `game/common/religion/tenet_types/_tenet_types.info` | 4799 | `aae8f7a94b0b5ae7a12d29ea6080941fd2e94842ea195905b9a1d8a14f2a9c25` |
| `game/common/religion/doctrine_types/_doctrine_types.info` | 11217 | `7a8f6f8e78f88f7c83de3c43239a5da2709777e9d56fed4ae031e98b76af2ffc` |

二进制精确名称位置还包括：`GetVassalConversionWindow` file `0x45651f0`；`OnEditAdherent` `0x4565178`；`OnEditAdherentPlural` `0x4565188`；`GetNewRiteName` `0x4564d80`。名称存在不替代 callback 注册、参数类型或运行期上下文验证。原先 `CreateRite` 真实登记与 thunk 链见既有 `binary-observations.json`：registration RVA `0x22a166` → thunk `0x14fb060` → method `0x14f5130`。

## 后续补查：融合后用原生编辑设置外观

观察时间仍为 2026-10-25，本机及 EXE 身份同上。用户要求的是“融合后新礼仪的四项名称、地图颜色”，因此可以采用**已有融合结果 → 原生编辑外观 → 同对象保存**的产品流程。这条路保留 RRF 独立创建权威，不需要在普通 Workshop 包里带 native provider，也不必重新实现颜色 setter。下面把已证实的执行链和仍需实际检验的前提分开。

### 确定的同对象编辑链

有界 Capstone 反汇编使用现存 `tools/.venv/Lib/site-packages/capstone`，只读同一 EXE。下面地址均为 RVA，按 PE section 实际转换文件偏移：

```text
EditRite callback registration 0x229d9c
  → thunk 0x14faed0
  → window confirmation method 0x14f49c0
  → CEditRiteCommand perform wrapper 0x29a2590
  → edit execution 0x29a2bd0
  → existing CRite update 0x24f75d0
  → at 0x24f7776: presentation destination = existing Rite + 0x510
  → copy presentation helper 0x14f0820
```

`CEditRiteCommand` RTTI descriptor RVA `0x5a16770`、primary vtable `0x4770498`、secondary vtable `0x4770530`；primary slot 6 是 `0x29a2620`，secondary perform 是 `0x29a2590`。执行从命令中的原 Rite ID 在真实 Rite database 查出指针，并把编辑后的 presentation 写到这同一对象。该路线没有调用 `create_dynamic_rite` 或 `CCreateRiteCommand`。

四项名称和颜色都在原生 presentation 中，而不是 RRF 临时变量：

- `SetColor` 登记 `0x22e3ec` → thunk `0x14fc600` → setter `0x14f6db0`，最后写 `window+0xb00`。
- 窗口 presentation 起点是 `+0x8e8`，故颜色位置是其 `+0x218`。
- `0x14f0820` 明确复制 presentation 的四名／描述等字符串，以及 `+0x218` 的四字节颜色；写入后的颜色为 `Rite+0x510+0x218 = Rite+0x728`。

因此合法的“设置名称与地图颜色”按钮确实可以打开现有结果的 `OpenGameViewData('rite_creation', resultRite)`，最终选择原生 **EditRite** 保存。不能把按钮接到 CreateRite；也不能在外观保存时再调用 RRF 的融合创建／收费 effect。

### `IsEditing` 的真实条件不是“创始者还活着”

`IsEditing` 的登记 `0x229668` → thunk `0x14facd0` → predicate `0x14f43e0`。后者读取当前玩家角色和其当前 Rite，然后检查：

1. `window+0xc8` 保存的目标 Rite ID 等于当前玩家的 Rite ID（character `+0xb4`）。
2. 该 Rite 的 `+0x4c0` 角色 ID 等于当前玩家角色 ID（character `+0x18`）。

`+0x4c0` 是 **head_of_rite**，不是 rite_founder。现有 `research/religion_rite_governance12002_head_native.py` 也明确记录该结构语义，但本轮结论的机器来源仍是当前 EXE 独立读取。仅凭 `create_dynamic_rite` 把玩家记作 founder 不足以保证进入编辑模式；必须实际读回 `GetHeadOfRite` 或对应脚本 `rite.head_of_rite`。本 EXE 有 `force_refresh_head_of_rite`（重新评选最佳领袖），未找到可直接强制任意角色为领袖的 `set_head_of_rite`／`set_rite_head` effect。不能为了开外观窗口就伪造领袖身份。

若用户不是新 Rite 的实际领袖，打开同一入口会落入创建模式；RRF 必须在入口前明确检查并说明原因，绝不能让“编辑外观”生成另一个 Rite。

### `CanEditRite` 守卫

`CanEditRite` → thunk `0x14faf30` → predicate `0x14f5030`。它构造真实 edit command，调用 `0x29a2620`；后者做内容／元数据重复性检查，并调用共享检查 `0x29c8cd0`；另外 `0x14f8910` 检查名称唯一性，编辑模式排除当前对象。

共享检查在 `0x29c8d90–0x29c8d98` 调用 scripted rule index 2。原版脚本链确认为：

```text
common/scripted_rules/00_rules.txt:24
can_edit_rite = { can_edit_rite_trigger = yes }
  → common/scripted_triggers/00_religious_triggers.txt:3022–3134
```

条件包括成年、和平、Faith 无进行中的 ecumenical council、特定从属伯爵的层级条件、特定 temporal/theological-agent 的 puppet 条件、当前 `rite.head_of_rite == root`、没有 `var:has_edited_a_rite`；未改革 Faith 还包含改革／圣地条件。当前 MTS 或其他 mod 可能覆盖这些源定义；应以实际加载图为准。

所以后置外观设置是真接口，但**不是所有融合者天然有资格**。对已有终身编辑锁、战争中、失去领袖或当前身份已变的用户，必须提供真实阻断说明；不能宣称“随时免费编辑”。若产品要保证每位融合者都能设置，则需要进一步限定融合前置资格，或设计只适用于严格外观编辑上下文的规则扩展，并证明无法借此修改信条／教义。无界解除原版 `can_edit_rite` 并不安全，也会扩大兼容冲突。

### 费用与一次编辑锁

`CalcPietyCost` thunk `0x14fb100` → `0x14f57a0` → `0x2c64bb0`。编辑模式走 `0x2c64710`：核心信条／教义只对不在原 Rite 中的实际变化计价。四名和颜色不参与这些差分循环，所以纯外观变更的**内容差分费用为零**。

但该路径还把角色 cost-add modifier token `0x223` 叠加，并经乘数处理；`CEditRiteCommand` 最终 `0x29a2cd2–0x29a2d22` 重算同一费用再扣款。未闭合此 modifier 在所有 mod 环境下必为零，不能把“内容差分零”写成任意角色都不会收费。产品按钮应读实际 `RiteCreationWindow.CalcPietyCost`，实机确认纯外观为零；非零必须明确展示实际报价，不自行退还或偷偷改钱包。

`common/on_action/religion_on_actions.txt:833–848` 的原文进一步明确：`on_rite_edited` 仅在界面提交**改变 tenets 或 doctrines**时立即触发；其 effect 才给 head_of_rite 设置 `has_edited_a_rite`。纯外观不应触发这把锁，但若角色此前已持有锁，`can_edit_rite_trigger` 本来就会拒绝进入。需要新实机验证纯四名／颜色改变后该变量、核心／教义与钱包都保持预期。

### 最小可交付路由与验收

1. RRF 完成一次融合并采用其真实结果；结果面板显示真实 Rite、四名、颜色、罪恶美德及实际改信情况。
2. 若结果仍为玩家当前 Rite 且玩家实际为其领袖，显示“设置名称与地图颜色”。由普通 GUI `OpenGameViewData` 打开该已有结果；原版或 MTS 自己的创建／编辑窗口提供真实输入与颜色选择。
3. 明确告诉用户此处只更改外观；要求界面实际 `IsEditing=true`，若不是则关闭并报告原因，绝不能调用 CreateRite。
4. 在原生窗口只改四名／颜色，确认当前实际费用；接受后比较 Rite ID／Faith ID、核心信条、全部有效教义、钱、`has_edited_a_rite`。必须保持同对象、内容不变、无第二次融合扣款，读回四名与颜色已写入，并保存冷读。
5. 为兼容 MTS，优先不覆盖它的原生窗口；但它把 cap 改到 100 时，该原窗口可能产生额外空信条槽。RRF 不能称这一步已经满足“无空白槽”要求，需结合实际 MTS 文件检验。若要严格只允许外观且消除空槽，可以只在 RRF 外观上下文针对性隐藏内容编辑区，必须基于 MTS 的实际有效文件合并，不能用原版窗口整文件覆盖把它的功能还原成三个槽。

这条后置编辑路由补齐颜色／四名的接口依据很强，比重写整个 native creation authority 的影响面小；实际资格、费用为零、原生窗口在 MTS 下的布局和保存后读回仍为 `NOT_RUN`。封臣至亲预览仍应由 RRF 转换策略和同一资格列表闭合；这里不把打开原生编辑窗口当作其改信功能已经实现。

## 图标、3–100 核心与不覆盖原生窗口的进一步约束

后续用户追加信仰图标选择、可减少核心、可选兼容宗族化密教，并要求尽量继承礼仪改革的新增项。以下是本次追加核对；这些条件使“后置原生编辑”不能作为覆盖所有合法融合者的完整方案。

### 图标

当前 EXE 精确 `set_rite_icon` 名称扫描零命中。真实 `RiteCreationWindow.SelectFaithIcon(FaithIcon.GetName)` 只能修改该原生草案，最后通过原生 CreateRite/EditRite 写入。没有发现可绕过 head_of_rite 守卫、仅把任意新 Rite 的 presentation 保存的独立公开 GUI action。后置编辑的实际资格限制因此同样适用于图标，不得声称任意融合者均已补齐。

### 原生选择与空槽

实际已闭合的调用：

```text
SelectTenet registration 0x229954 → thunk 0x14fad50
    → window method 0x14f4580
SelectDoctrine registration 0x229ad3 → thunk 0x14fadf0
    → window method 0x14f46f0
DoctrineCategoryWindow.ShowWindowSortList registration 0x228f2c
    → thunk 0x14fab90 → method 0x14f1e40
DoctrineCategoryWindow.ShowWindow registration 0x228e3e
    → thunk 0x14faa00 → method 0x14f1930
```

`SelectTenet` 接受真实 typed `TenetItem`；其 `+0x20` 是 slot index，`+0x28` 是真实 Tenet 指针。`0x14f4580` 检查 index 非负且小于 `window+0x784`，按 `index*0x70 + [window+0x778]` 定位所选槽，交由 `0xee0420` 替换。后者直接写 Tenet 指针，并没有“同一个信条再点一次就清空”的 toggle 分支。之后 window method 重建草案内容与预览。`ShowWindowSortList(index)` 是原版把候选绑定到目标槽的实际入口，不能随意假造一个 TenetType 充当 TenetItem。

原版 GUI 的读取关系：

- 已选槽：`RiteCreationWindow.GetTenets` → `TenetItem.GetTenet/GetFaith/GetRite/GetSlotIndex`。
- 可选核心：`RiteCreationWindow.GetTenetGroupItems` → `TenetGroupItem.GetTenets` → 同一 typed `TenetItem`。
- 普通教义：`RiteCreationWindow.GetDoctrineCategoryWindow` → `DoctrineCategoryWindow.GetDoctrineItems` → `DoctrineItem.GetDoctrine/GetFaith/GetRite/GetSlotIndex`。

源 `gui/window_rite_creation.gui:1246–1255` 用 `DoctrineItem.ShouldDisplay/CanPick`、原版 `pam_know_doctrine`、`SelectDoctrine` 和 `HasDoctrineSelected`；`:1475–1478` 用 `TenetItem.CanPick`、`SelectTenet` 和 `HasTenetSelected`。若对真实候选加双来源限制，应在这些实际选项上追加 RRF membership predicate，并保留原有 CanPick／知识／TopScope 检查，不能另放一套会绕过原生选择守卫的复选框。

没有找到 RiteCreationWindow 的 ClearTenet、RemoveTenet、SetTenet、DeselectTenet 注册。EXE 唯一 `ClearTenet` 字符串属于 **ActivityPlanner 的神学辩论**；原版源码明确在 `gui/activity_planner_widgets/activity_planner_tenet_doctrine_selection.gui:123` 和 `gui/window_activity_planner.gui:1862,1881,1900` 调用 `ActivityPlanner.ClearTenet(index)`，不能换类名当作礼仪草案接口。`RemoveTenet` RTTI 是已存在 Faith 的 script effect，不是 GUI draft action。

隐藏空槽本身可通过 `TenetType.IsValid` 做布局，另外只显示一个真正空槽的“添加”入口；这不等于存在从 N 个有效核心减少到 N−1 的接口。使用某个空 `TenetItem` 调 `SelectTenet` 也不能证明可清空别的槽，因为传入对象自带的 slot index 决定写入位置。新建 dummy Tenet、事后移除、只在画面上移除而 native 草案仍保留，都不能满足真实结果与预览一致的要求。

### 没有已证实的临时 Rite 清理 effect

精确 `destroy_rite`、`delete_rite`、`clear_rite`、`DestroyRite`、`RemoveRite` 对象操作均未命中；`remove_rite` 前缀只找到 `remove_rite_tenet`、`remove_rite_doctrine`、`remove_rite_culture`，对应 RTTI 也分别是去内容的 effect。不得据“无信徒”假设普通动态 Rite 一定会自动销毁。

`set_parent_faith` 的真实帮助确实说明：在替换 main Rite 时，**history 期间生成、没有 Rite type、没有信徒**的旧 main Rite 可以被销毁。这是带前提的内部清理；没有证明普通 `create_dynamic_rite` 临时草案具有该来源标记。把模组新建模板改为主礼仪再搬家，也会改变 Faith 结构，不能当作普通取消路径。

因此“先创建一个无信徒模板供原生窗口预填，取消或完成再删除”在本轮没有完整删除接口，不能作为已可交付方案。`set_rite_enabled=no` 或禁止转换只会禁用对象，也不等于删除。

### `GetRite.MakeScope` 不能访问原生草案

此点已直接核对 getter，避免依赖名字猜测：

```text
RiteCreationWindow.GetRite registration 0x22bf58
    → ordinary getter 0x14fbae0
    → ID getter 0xaeb2d0
    → actual Rite database lookup

same member's script-ID registration 0x22bfcc
    → 0x14fbb50
    → same ID getter 0xaeb2d0
```

`0xaeb2d0` 完整指令只有：

```text
mov eax, dword ptr [rcx + 0xc8]
mov dword ptr [rdx], eax
mov rax, rdx
ret
```

`window+0xc8` 在窗口打开方法 `0x14f3400` 的 `0x14f34c2–0x14f34d4` 被设置为传入的现存 Rite ID。`0x14fbae0` 用该 ID 查真实 Rite database（全局 pointer 地址 RVA `0x5d1e2f8`），没有返回 `window+0x8e8` 的内部 presentation／内容草案。

所以：

```text
GuiScope.AddScope('rrf_native_draft', RiteCreationWindow.GetRite.MakeScope)
```

实际上会把 **现存来源 Rite** 传给 script effect。对它 remove/add 信条／教义会真实修改来源，不是修改虚拟草案。该候选通道已排除，不能在模组里尝试当作不影响游戏对象的预填接口。

### 创建模式与命令资格要分开

`IsCreating` registration `0x2297d9` → thunk `0x14fad10` → predicate `0x14f4480`：目标 Rite 与玩家当前 Rite 同 Faith，且玩家当前 Rite 的 head_of_rite 不是玩家时，原版 UI 才呈现创建模式；其余情形可能是编辑或两者均不成立。

这只是原生 **UI 模式 getter** 的硬编码条件，尚不能直接外推 `CCreateRiteCommand` 永远禁止 Rite 领袖。`can_create_rite_trigger:3137–3247` 的脚本禁止 Faith 宗教领袖、已有 `has_created_a_faith`、战争等，但没有相同的 Rite 领袖条件。RRF 新增最终按钮直接调用 native CreateRite 是否能在这种模式下安全执行，仍需核命令／确认报价与终态；原生 `CalcPietyCost` 又按 IsEditing 切换计价，不能认为隐藏按钮后调用就天然正确。

综上，本轮找到了真候选模型、真元数据提交、真预览和同对象编辑链，同时排除了三个会误写来源或残留对象的捷径。满足“任意合法融合者＋减少到 3–100 核心＋不覆盖任何上层原生窗口＋未来改革新增项自动继承”的全流程，直接迁移原生创建方案还缺公开且已证实的**原生草案可变选项初始化／删槽**入口；没有将缺口写成已完成。后续研究找到的独立创建＋有界原生编辑会话见下一节，不引入 DLL 注入、直接写内存、隐藏来源改动或虚构删除效果。

## 补充：独立创建＋有界原生编辑会话

观察日期：2026-10-25；`machine_id: 4-8e1c2f1861`。本节沿用本文绑定的原版 EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，仅作静态研究；不代表脚本编译、实机提交或保存后冷载已通过。

前文 `IsEditing` 要求实际 head_of_rite 仍是事实，但这是窗口模式 getter 的条件。真实 Edit 命令并不再硬编码该门，因此存在普通模组可施工的路线：RRF 独立创建精确 3–100 核心集合并收取固定融合费，随后给**创建者本人＋实际当前融合结果＋有效 RRF 设置会话**一个有界原生编辑权限，使用真实 EditRite 在同一对象保存四名、颜色、图标与第三方教义。保留原版权限分支，不改来源对象或领袖身份。

### 编辑权限可扩展，真实失败原因可复用

```text
CanEditRite: registration 0x22a029 -> 0x14faf30 -> 0x14f5030
GetEditBlockers: registration 0x229f1c -> 0x14faef0 -> 0x14f50f0
EditRite: registration 0x229d9c -> 0x14faed0 -> 0x14f49c0

0x14f5030 constructs CEditRiteCommand -> valid 0x29a2620
command.valid calls shared checker 0x29c8cd0 at 0x29a2a5b
```

完整读取共享校验器 `0x29c8cd0–0x29c973c`：它检查实际 Rite／角色、脚本规则、实际编辑费可负担、教义 can_pick、四项名称合法性、图标与内容重复等。脚本规则索引 2 在 `0x29c8d90–0x29c8d98` 经 `0x1d65ae0` 调用。未发现该规则之外第二次 head_of_rite ID 硬比较。

`common/scripted_rules/00_rules.txt:24` 将 can_edit_rite 委托给 `can_edit_rite_trigger`，后者位于 `common/scripted_triggers/00_religious_triggers.txt:3022–3134`。可保留整个原触发器，再 OR 精确的 RRF 会话业务分支。不能扩大成所有玩家、任意动态礼仪或仅有任意 RRF 变量。

CanEditRite 没有先要求 IsEditing，GetEditBlockers 也调用同一真实编辑资格路径。它们可用作独立设置按钮的启用与禁用原因。原窗仍可能错误显示创建模式；会话期间 **can_create_rite 必须明确拒绝**，不能只靠 overlay 盖住 Create 按钮。

### 正确费用键与最终零下限

真实 modifier 为 **rite_creation_piety_cost_add／rite_creation_piety_cost_mult**；原版 `common/modifier_definition_formats/00_definitions.txt:2778,2783` 有定义。EXE ASCII 文件偏移分别为 `0x46cb400／0x46cb420`，费用代码读取 enum `0x223／0x224`。本次 EXE 没有注册 faith_creation_piety_cost_add／mult 字符串，不能使用旧版本印象中的名称。

最终费用调整函数 **RVA 0x2c62cc0** 将负基础值夹到 0，再按固定点 `100000=1.0` 计算 `base × (1 + script_mult + character_mult)`；末尾 `0x2c62e08 test rdx,rdx`、`0x2c62e18 cmovs rdx,rdi` 中 rdi 为 0，`0x2c62e1c` 存储最终值。因此最终下限是 **0**，不是 1 或 250。

GUI 报价链 `CalcPietyCost: 0x14fb100 -> 0x14f57a0 -> 0x2c64bb0` 根据 IsEditing 选择编辑基础费用 `0x2c64710` 或创建基础费用 `0x2c641e0`，加 0x223 后在 `0x2c64d46` 调最终调整函数，随后直接返回；没有再次加最低值。即使创建基础费存在最低值，也在 multiplier 前。

实际 Edit 执行 `0x29a2bd0` 使用编辑基础费，加 0x223 后在 `0x29a2d12` 调同一调整函数，`0x29a2d17–0x29a2d1f` 取最终值并取负进入扣款路径，也没有后置 minimum。

所以 RRF 已收固定融合费后，可用**只属于本人本会话**的足够负且不溢出的 rite_creation_piety_cost_mult，使错误创建模式的窗口报价与真正 Edit 的实际扣款同时成为 0。任意第三方正 multiplier 不能凭常数无限覆盖，实际仍须校验 CalcPietyCost、确认窗和钱包差额均为 0；不符合时拒绝完成，不能假报免费再事后退款。

原生确认窗确实使用窗口报价：`EditRite -> 0x14f49c0 -> 0x14f11b0`，后者 `0x14f128a` 载入 `RITE_CREATION_VIEW_COMMAND_EDIT_DESC` 并传入调用者的费用。这解释了为何必须同时解决错误模式报价和实际 Edit 费用。

### 同对象元数据提交与成功清理

执行函数 `0x29a2bd0` 解析实际 target Rite，于 `0x29a2d90` 调更新函数 `0x24f75d0`。更新函数在 `0x24f7776–0x24f7780` 把草案 presentation 复制到**既存 Rite+0x510**，包含名称、描述、图标与颜色；颜色 presentation+0x218 对应 Rite+0x728。该链不创建第二个 Rite。

成功收尾应追加 **on_rite_updated**，而非只监听 on_rite_edited：

- `common/on_action/religion_on_actions.txt:725–730` 明确 root 是实际更改的 Rite；cosmetic-only 仍进入 hook，只是不设置 scope:changed_tenets_or_doctrines；通过界面编辑才设 scope:consume_rite_edit_token。
- 同文件 `:833–837` 明确 on_rite_edited 只覆盖改变核心／教义的界面编辑，并立即触发；on_rite_updated 延迟触发。所以只改名称、颜色、图标也有成功入口。
- 更新函数 `0x24f7b90` 无条件调用 `0x24f98e0`，其原始函数名字符串是 FireRiteChangedOnAction（`0x24f9961` 引用）。首次调度 `0x24f9bdc` 不被内容改变条件包围；后续 `0x24f9be1–0x24f9bee` 才限制即时编辑通知为“界面 token 且确实改内容”。

RRF 可以在专用 on-action 追加自己的 hook，以 root 与登记结果完全一致、登记创建者仍有会话为守卫，清除**自己的**免费 modifier 与变量；保留原版既有 effect。脚本更改也可能产生 updated，不能凭任意一次更新清所有人的会话。

延迟 hook 有实际顺序风险：关闭窗口／确认窗并不证明排队的 Edit 命令完成校验。仅因 view 关闭就撤权限或减免，可能让已提交命令失败或变价。提交后应保留 pending、权限和减免至实际 on_rite_updated 成功；显式取消只在无 pending 时清理，并有合理有限时效／异常处理。不能把关闭 ACK 当成功。

### 独立 overlay 的合法边界

注册目录实际为 **gui/scripted_widgets/*.txt**，不是 common/scripted_widgets。原 `_scripted_widgets.info:1–9` 支持 `gui/file.gui = widget_type`，所有文件同时加载。parser `0x372a310–0x372a594` 只存两项 interned string ID（8 字节记录）；启动函数 `0x372a5a0 -> 0x372a5e0` 对所有记录使用同一全局 GUI root parent。没有已证实的 per-entry parent 属性，不能宣称注册外部 widget 就挂到原生 footer 子节点。

只有取得真正原生窗口 context 后，才可调用 CanEditRite、EditRite、GetEditBlockers。`IsGameViewOpen('rite_creation')` 是原版真实全局 predicate（如 gui/hud.gui 的 barbershop 用例）；它本身不证明外部 widget 得到了 RiteCreationWindow 实例。R0012 后来实际否定了本次独立编辑窗的这项前提，现行方案见下一节的原生窗口 graft。脚本规则仍须独立阻止 Create，不能把遮挡当权限边界。

### 四项名称回调可用于独立 editbox

四个 ontextedited 回调都接受事件传入的 string 参数，直接改真正原生草案；**不从原窗 FindChild 读取文本**：

| 回调 | 注册 thunk → 实现 RVA | 写入窗口字段 |
|---|---|---|
| OnEditName | 0x14fc020 → 0x14f38f0 | +0x918，dirty +0x938 |
| OnEditAdjective | 0x14fc090 → 0x14f39c0 | +0x948，dirty +0x968 |
| OnEditAdherent | 0x14fc100 → 0x14f3ae0 | +0x978，dirty +0x998 |
| OnEditAdherentPlural | 0x14fc170 → 0x14f3c00 | +0x9a8，dirty +0x9c8 |

thunk 将事件参数的 string 传入实现；实现读取 rdx 的 std::string，并复制到上述字段。后 3 项先核现存 Rite 的内部保护位，保留原生规则。`window_rite_creation.gui:660` 的固定控件名注释明确用于创建后清空；不是 OnEdit 的取值源。该结论证明了回调的字符串合同，没有证明独立 overlay 能取得接收回调的原生实例。现行 graft 保留原窗四个编辑框及其 native 初始化，避免另建输入副本。

全 EXE 精确 GetNewRite* 只有 **GetNewRiteName**；不存在已注册的 GetNewRiteAdjective／Adherent／AdherentPlural。独立输入可用实际结果 Rite 的 GetAdjective（有 NoTooltip 版本）、GetAdherentName、GetAdherentNamePlural 等已有 getter 初始化，编辑后保持 editbox 自身文本；重开会话应从实际结果重新初始化。不能虚构其余草案 getter，也不能因画面显示新字就推断已提交。

### 交付验收仍需真实环境完成

静态层面已闭合权限、零报价／零扣款、同对象元数据更新、cosmetic-only 成功 hook 与独立输入回调。仍需实机核脚本规则可加载、native blocker、四名／色／图标真实写入、MTS／DES 动态选项、overlay 布局、无第二对象、pending／取消／异常清理、成功后 modifier 清除，以及保存后冷载元数据不丢失。单一 ACK、窗口展示或源码分支都不能替代这些结果。

## R0012 实际失败后的现行修正：真实原生窗口内的条件 footer

`machine_id: 4-8e1c2f1861`，2026-10-25。R0012 保留图 `scene/screenshots/R0012/02-decision-group.png` 在任何融合提交之前就显示了空的“定制融合礼仪”外部窗口；实际虔诚仍为 6000、当前 Rite 仍为来源 150，未创建结果。后续 Root 的原生 UI 回执也显示 native-setup 可见、fusion 窗口隐藏。这是该独立原生 context 消费者失败的实机证据，不能解释为已成功创建。

当时 error.log 为 1902 B，打开 GUI 后仅新增 `21:15:45 jomini_custom_text.h:93` 的 character/GetActivityName 诊断，gui_warnings.log 为空；日志没有直接写出 RiteCreationWindow context 缺失。缺少原生实例是结合空字段、错误 visible 表达式、scripted-widget 全局 parent 与未找到公开导入 getter 所作的解释，不能把推断伪装成引擎报错。现行实现不再依赖这一未经资格化的外部 context。

R0012 已由 Root 正常关闭，native／保留 OS／host／keeper 回执结束后，`CAS 13872` 通过 `root-execution-a14/SCREEN-RELEASE.actual.json` 释放。之后才修改源文件；没有热改冻结运行包。

### 一条有来源的原生 GUI 覆盖

现行产品新增 `gui/window_rite_creation.gui`，保留真正 `rite_creation_window` root，由原生 game view 注入 RiteCreationWindow。删除 `gui/rrf_native_setup_window.gui` 及它的 scripted-widget 注册；外部 launcher、结果／恢复入口不再调用任何 RiteCreationWindow 成员。

基础来源：

| 来源 | 精确身份 |
|---|---|
| 当前原版 window_rite_creation.gui | SHA-256 `9476299fdbf0975e41923eac9b192d3fe0b2cd74a4da0d928d0da7974b7ea9f8` |
| 实际加载 MTS v11 同路径 GUI | 43,790 B；SHA-256 `0b4c9eeff1fe0f6948e4e09d03bbb96241c0b8449a401bfe3d1f728a62a8ceda` |
| MTS 源提交 | `XenoAmess/ck3_mod_more_tenant_slots`，`fae5b3bfda87f872f42052c5ab4d729efb3b4d19`，`more_tenets_slots_xa_dev/gui/window_rite_creation.gui`；对应 Workshop `3182367229` |

逐行比对证实 MTS 此文件的唯一实质变化是把核心区 hbox 改为高度 300 的 scrollbox＋三列 flowcontainer；唯一 mts_ 标识只是 `mts_tenets_grid_scroll` 控件名，没有 MTS 私有 trigger／doctrine／scripted-GUI／素材依赖。因此同一份基础适用于有、无 MTS，实际容量仍由加载的原生 define 决定。只纳入这一路径的必要兼容改动，没有复制任意其他 GUI。该来源按本次仓库任务授权使用。

### RRF 模式与普通模式

原生四编辑框、名称初始化、图标、颜色、罪恶美德、四个标准教义 category helper、真实 picker 与知识／can_pick 守卫保持原样。DES 的 main_group 扩展继续由原 helper 动态提供。RRF 会话 gate 接收原生 `GetRite.MakeScope` 作为 saved scope，要求创建者、实际当前 result、active 会话与请求目标全都对应。

仅在该会话内，新增 footer 用真实 CanEditRite、CalcPietyCost=0 和 exact-target mark validator 启用保存；先 mark 请求，再调用 **EditRite**，不调用 CreateRite。原 Edit／Create／Reform 按钮在此模式隐藏。独立 RRF 提交仍只收原 500／1000 一次，原生设置会话只更新实际同一对象；不设置领袖或改来源对象。

核心选择按钮在该会话禁用，隐藏原生无效空槽，保留已提交的实际 3–100 项；最终结果校验继续检查实际集合与双方来源贡献。原生错误创建模式的 adoption／creation blocker 说明在 RRF 模式隐藏，改用真实 Edit blockers；普通模式继续原生行为。

保留现有默认／延后生命周期：首次申请保存确认之前，可明确保留创建时的默认设置，并通过实际最终内容守卫完成；请求过保存后此入口禁用。延后或 X／ESC 关闭不清会话／减免，纯 scripted-GUI 恢复入口可重新打开同一对象。原生保存只有带 consume_rite_edit_token 的实际 on_rite_updated 及最终 ID／内容守卫才能完成清理。launcher 只消费一次 open flag，不因会话仍 active 重复打开或重置输入。

新增现有测试中的跨消费者检查覆盖正式 manifest、原生 root、保留四 callback、真实 Edit 回调顺序、exact-target 参数、零价资格、核心锁定、MTS 滚动和外部入口不含原生成员；脚本 AST 验证 session gate 与恢复／延后的状态。这些检查不假装拥有原生编辑实例，也不替代下一次真实 UI、保存及冷载验收。本轮按 Root 中央验证安排没有在子代理单独运行 Maven。
