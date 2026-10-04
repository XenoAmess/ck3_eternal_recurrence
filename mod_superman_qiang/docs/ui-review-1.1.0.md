# 《超人强》1.1.0 可见界面审查

2026-10-04 用户明确否决查询性经验时弹出的事件大窗，要求使用通知气泡并检查整个模组的可见界面。初始设计将查询缩为“角色名＋次数”的原生通知，并拟把当前属性与累计净修正放入鼠标提示。R0021 实拍确认原生 `custom_tooltip` 实际直接显示在通知正文：六技能两排、健康单独一排及简短括号说明，因此当前公开文字改为“气泡显示次数、当前属性与累计净变化”，不以悬停作为读取前提。机制说明留在工坊与文档。

[R0019](live-R0019-health-1.1.0.md) 的健康20条机制案例及 [R0020](live-R0020-health-reload-1.1.0.md) 新进程保存重载已经通过。[R0021](live-R0021-normal-ui-1.1.0.md) 从0.5缩放调整到正常70%后，已取得玩家与NPC通知的读数、正文呈现、特质持有人记录及查看只读证据；此前“详情只在悬停”与小缩放候选按原样保留。root审阅同时发现一个500×210、只写“查看记录”的额外原生确认窗，违背用户的一步通知查看要求。运行时关闭该确认后，[R0022](live-R0022-compact-ui-1.1.0.md) 已验证普通存档自己与NPC一次菜单点击直接出气泡、无额外确认或事件大窗及查看只读。未重跑已通过健康矩阵，实际范围见 [1.1.0 增量验收汇总](acceptance-1.1.0-20261004.md)，正式发布仍待完成。

后续用户新增健康作为第七个随机吸取候选，因此目标版本为 **1.1.0**。早期外置 `ui-review-1.0.1/` 清单仅记录对旧22文件库存的只读检查，不改变历史验收或已发布1.0.0。六技能通知原型的所有候选仍保留；健康源已冻结为每笔0.00075原始修正点，界面读数保留五位小数。该数量级的推导见[健康设计](health-design-1.1.0.md)，不承诺每次固定一个月寿命。

## 实际可见界面库存

已按 `tools/product.py` 的明确22文件清单检查；没有独立自定义GUI窗口、决议页或额外选项页。只有下列实际入口、提示及展示需要本次改造。

| 文件或数量 | 可见内容与历史入口 | 1.1.0结果 |
| --- | --- | --- |
| `common/character_interactions/sxad_interactions.txt` | 角色右键“查看性经验”及说明 | 入口保留；选择一次直接向操作者发送气泡，关闭额外确认；查看不写计数或修正账本 |
| `events/sxad_events.txt` | 旧版唯一性经验详情事件大窗、人物立绘、“知道了”按钮；当前文件仅保留namespace | 已移除查询事件链及旧事件三个文案key，不用确认按钮阻断查看 |
| `common/traits/sxad_traits.txt` | 性经验特质，目录通用说明与持有人说明 | 持有人提示只显示其真实累计次数；通用说明一句话 |
| `common/modifiers/sxad_skill_balance_modifiers.txt` | 七项gain/loss，共14种修正提示及两种通用名称 | 已新增健康吸收/流失提示；沿用通用名称与原版属性名，数值由原版修正提示展示 |
| 九语 `localization/` | 以上名字、提示、详情及修正alias | 新通知采用两新key；其他可见入口短句化。外语仅格式检查 |
| `gfx/interface/icons/traits/sxad_sex_experience.dds` | 性经验特质图标 | 使用现有图标，不新增无实际入口的装饰按钮 |
| `common/script_values/sxad_values.txt` | 经验、七项当前属性及七个净修正账本读数 | 已增加当前有效健康与健康净修正；查询只读，两类值明确分列，避免称为基础属性 |
| 五份 `common/scripted_effects/` 文件 | 统计、候选检测、转移及两原版投影 | 没有额外模组页面；保留原版可见效果，不新增每次性行为的提示噪声 |
| `descriptor.mod`、`thumbnail.png` | 启动器/工坊标题与封面 | 不属于游戏查询页；发布1.1.0时更新版本，封面保留用户已选风格 |

初始22文件的精确摘要及六技能图标来源保存在 `D:/ck3-experience-drain-feasibility-20261004/ui-review-1.0.1/inventory-and-icon-source.json`。旧事件文件保留 namespace、移除详情事件定义；健康代码追加到现有文件，正式清单仍为22文件，由产品构建器冻结，不用本设计表代替正式manifest。

## 查询通知与提示

右键入口仍为 **查看性经验**。说明缩为“以通知查看某人的性经验与属性”；选择入口后直接出气泡，不再要求确认。此前短句“查看某人的记录”触发额外原生确认窗的实际结果保留为R0021审阅发现，不能将该空窗当作新查询页面。查询目标是交互的 `recipient`，不能读成操作者或玩家自己。

修复仅使用当前原版 `_character_interactions.info:282–285` 的 `needs_confirmation` trigger：未指定时默认确认，false时选择后立即运行on_send/on_accept。当前源将此字段标为deprecated，未来补丁可能移除；本次仅绑定1.20.0.3来源，并经R0022实际一步操作验证，不外推后续版本。该只读查询不改变游戏数据，不增加新的确认或权限流程；25个本地化key保持不动。

通知标题为：

```text
[recipient.GetShortUIName] · 性经验 #V [recipient.MakeScope.ScriptValue('sxad_experience_value')|0]#! 次
```

标题只承载目标身份和次数。使用 `send_interface_toast` 与原生中性通知样式；人物图标指向选中的角色。`custom_tooltip` 承载当前属性与累计净修正；R0021 已证明它直接展开为通知正文，不再触发人物事件窗口，也不依赖另一个悬停页面。

通知正文的六技能排为两行，每行三项，健康放第三行，格式统一为“原版图标＋原版属性名＋当前值（累计净修正）”：

```text
外交 12 (+1) · 军事 9 (-1) · 管理 11 (+0)
谋略 8 (+0) · 学识 13 (+2) · 勇武 10 (-2)
健康 5.00075 (+0.00075)

括号内为本模组累计净修正点。
```

上面数字只说明排列方式，不能作为游玩结果或宣传截图。实际标题及提示始终读取角色数据：六个当前值用 `sxad_<skill>_value|0`；六个账本值用 `sxad_<skill>_balance_value|+0`，正负号可直接区分吸收、流失与零。净修正不是基础属性，也不是两次面板值之差；原版百分比和取整仍会影响当前有效数值。

原版六个 `@skill_<skill>_icon!` 及 `$<skill>$` 名称已经核对，来源为实际1.20.0.3 `game/localization/english/game_concepts_l_english.yml` 第733、737、741、745、749、755行，SHA-256 `ae7ebd881fe5b4222220c5dd9cf4b56b5d848202af2e5db9f5c90b479f455dd7`。不使用未核实的 `@diplomacy_icon!` 简写。

健康在六技能下面单独一行。标签引用原版 `$game_concept_health$`，图标为 `@health_icon!`，当前有效健康使用 `sxad_health_value|5`，净修正账本使用 `sxad_health_balance_value|+5`。两值保留五位小数，能显示0.00075单笔差额；前者不是基础健康，括号内不是剩余寿命。准确行如下：

```text
@health_icon! $game_concept_health$ [recipient.MakeScope.ScriptValue('sxad_health_value')|5] ([recipient.MakeScope.ScriptValue('sxad_health_balance_value')|+5])
```

原版名称来源为 `game_concepts_l_english.yml:505`，图标来源为 `message_filters_l_english.yml:26`（SHA-256 `f790486931b553d44de990c852a42e89532d84c4ec750b9c6ea2b508164ef5ad`）。原版没有小写 `$health$` 名称key，不能照搬六技能引用方式。健康行不出现“一个月寿命”的承诺。

## 特质与属性修正提示

性经验特质持有人提示只保留：

```text
已记录性经验：#V [SCOPE.ScriptValue('sxad_experience_value')|0]#! 次。
```

此处的 `SCOPE` 是被悬停特质的持有人。无角色上下文的特质目录回退为“已记录的明确性行为次数”。移除年龄、启用时点、概率、上限及百分比等长规则段，不把特质悬停当作规则手册。

14种技能/健康修正沿用统一吸收/流失名称与原版属性标签。健康gain/loss两个新alias分别引用 `$sxad_absorbed_skill_modifier$` / `$sxad_drained_skill_modifier$` 与 `$game_concept_health$`。永久修正和净转移账本保持原机制；本次界面调整不增加按钮、开关或独立修正页面。

## 九语文案交付与历史保全

六技能原型使用23个key：旧24个key去除 `sxad.1.t`、`sxad.1.desc`、`sxad.1.a`，新增 `sxad_view_experience_toast_title` 与 `sxad_view_experience_toast_details`。四个原key改为短句：通用特质说明、持有人说明、互动说明及确认提示；其余 **17个原key译值保持不变**。

本地化代理只提供外置完整九语JSON，不编辑共享 `runtime_data.py`、`gen_runtime.py` 或GENERATED输出。运行时代理将其写入统一权威输入 `tools/ui_localization.json` 并生成九语。JSON中的换行是实际换行，由生成器统一执行CK3转义，避免二次转义成可见的 `\\n`。

首次六key七语候选保留于 `D:/ck3-experience-drain-feasibility-20261004/ui-review-1.1.0/toast-six-skills-A0001/`。当前源定稿后，将唯一变动的互动“以通知查看”短句补充小批次翻译，并机械统一两排纯token布局；中英文以运行时数据为唯一源。候选只用于字符串翻译；非中文只做key、BOM/header、解析、图标、scope、数值格式与转义检查，不宣称语义、母语或游戏内检查通过。

六技能原型完整九语输入已交运行时代理：`toast-source-freeze-A0002/ui_localization.json`，SHA-256 `fbdc12cba03df8d2c8b1052387d5500a773d2f3a4c2c6b60bdd46c3b7cc564be`；绑定 `runtime_data.py` SHA-256 `bc63abeff767867cc259ab84f6c2209500b74002a7e3e6873e995a6052170b6d`。每语23个key及全部保护token格式通过，七语17个原key译值逐值保留。新界面六key候选共42条，随后互动描述的单key源增量共7条；两排技能布局仅机械同步。该输入还未包含健康行，其历史字节及报告不会由后续健康版本覆盖。

健康完整输入已另存为 `toast-health-A0003/ui_localization.json`，SHA-256 `c58b35effce13ab1a2fffdbaf5c423af53bc2ff1dcd4f4b5d7062faa67bcfac4`，绑定运行时数据 SHA-256 `a5ac79b55e74fafe279f8bf2ea14cc2d1c5c74ccb2b9252a623135aeeaba9f1a`。当前每语 **25个key**；只在通知details插入准确健康token行并派生两health alias，其余 **22个原key逐值保持**，所有语言的footer也保持原样。九语key/图标/名称引用/scope/五位小数/转义格式检查通过，新增MiniMax请求数为0。随后 R0019/R0020 已验证健康机制与重载，R0021 已验证通知读数与特质来源，R0022 已通过取消确认窗后的一步操作及只读复验。历史候选与格式报告保留各自当时状态，未新增外语检查。

## 工坊与截图修订范围

已查看[工坊介绍](../../workshop/superman_qiang_description.bbcode)、[当前媒体清单](../../workshop/superman_qiang_screenshots.md)、[宣传图片要求](promotional-media.md)及README。三张插画与规则示意讲述属性转移和经验累计，没有独立查询页，不因通知方案重做成不存在的界面。

未发布的media-v2及其经验详情大窗保留为历史候选。正式v3前三张为插画与规则示意，第四张保留正常勾引成功事实，第五张采用 [R0022正常查询通知](../../workshop/superman_qiang_media/v3/05_notification.jpg)。阿梅利娜真实累计1次的性行为与存档来源保留；新run加载正常存档，经普通菜单一步查看取图，最终通知图仅裁切为785×364，已由root直接审阅。界面设计示例数、人工设置计数或测试夹具截图不用于宣传。

工坊“每个角色，都有自己的情场履历”段明确右键操作后气泡直接显示次数、当前属性与累计净变化，健康五位小数。初稿“悬停查看”已按 R0021 实拍更正；规则留在工坊正文，不塞入气泡。1.1.0新增健康后，“六种可能”、六属性列表、玩法细节及兼容说明按[健康设计](health-design-1.1.0.md)同步，不写固定实际寿命变化承诺。媒体清单、版本、README与独立Steam更新说明由主任务按正式发布范围同步，旧media-v2素材及首发截图记录继续保留。

## 中文实机结果与范围

R0021 已验证70%设置下的玩家与NPC通知，正文显示全部三排属性及括号说明，目标读数与被选角色一致；特质说明读取持有人。其实际通知及额外确认窗审阅证据都保留。R0022 在新生产包下验证自己与NPC一次菜单点击直接产生气泡、无额外确认或事件大窗；查看前后双方真实经验1、全部七项账本与修正投影、基础健康、六项基础数组、特质及玩家原生当前健康均相同。最终NPC原图已由root直接审阅。只以简体中文做真实界面检查，外语不追加语义或布局门禁。

正常经验1截图已由 [R0022报告](live-R0022-compact-ui-1.1.0.md) 绑定新22件运行包和真实普通存档，原图SHA-256为 `7b74e180a0bccf2bfdad678bff7bf363d77b57c37e9329de0283fa9f1a8840c6`；中文气泡没有事件大窗、无测试菜单或控制台。本设计与候选格式通过不能替代该实机证据，正式上传及公开媒体回读另行完成。
