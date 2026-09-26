# CK3 宝物详情「历史」文案可定制范围

研究时间：2026-09-27。游戏本体为本机 CK3 **1.19.0.6 (Scribe)**；结论来自原版和本机工坊 mod 的静态源码对照，**未做本次实机注入验收**。

## 原版数据流

- `game/gui/window_artifact_details.gui` 的历史列表由 `[Artifact.GetHistory.GetEntries]` 提供。每行标题与正文分别直接绑定 `[HistoryEntry.GetTitle]`、`[HistoryEntry.GetDescription]`；角色头像来自该条记录的 actor、recipient。
- `game/localization/english/inventory/inventory_l_english.yml` 定义 `artifact_history_<type>_title/desc`。例如 `inherited_desc` 是 “Inherited by [HISTORY_ENTRY.GetRecipient...]”。日期、角色、地点在本地化中从 `HISTORY_ENTRY` 取值。
- `create_artifact = { history = { ... } }` 可设置首条历史；宝物作用域中的 `add_artifact_history = { type = ... date = ... actor = ... recipient = ... location = ... }` 可追加历史。`set_owner`、`reforge_artifact` 也能指定对应的 `history`，或通过 `generate_history` 控制自动记录。参见原版 `events/artifacts/artifact_events.txt` 与 `common/scripted_effects/00_ep1_artifact_creation_effects.txt`，以及 [Paradox Wiki 的 Artifact modding](https://ck3.paradoxwikis.com/Artifact_modding) / [Effects](https://ck3.paradoxwikis.com/Effects) 文档（本站可能限制自动访问；其归档见 [Artifact modding](https://github.com/jesec/ck3-modding-wiki/blob/master/wiki_pages/Artifact_modding.md) 和 [Effects](https://github.com/jesec/ck3-modding-wiki/blob/master/wiki_pages/Effects.md)）。

## 本机大型 mod 对照

工坊目录均以 `Z:/SteamLibrary/steamapps/workshop/content/1158310/<id>/` 为根：

| Mod | 观察到的做法 |
| --- | --- |
| Princes of Darkness `2216659254` | `common/scripted_effects/POD_artifacts/01_pod_artifacts_creation_effect.txt` 用 `created_before_history` 创建剑，并追加 `conquest`、`given` 等记录；`common/scripted_guis/POD_crafting_minigame_guis.txt` 给制作的宝物追加 `created`。 |
| A Game of Thrones `2962333032` | `common/scripted_effects/00_agot_artifact_crowns_effects.txt` 给伊耿一世王冠写入带日期、人物、地点的创建记录与连续的 `inherited` 记录；`00_agot_artifact_effects.txt` 的 `agot_add_artifact_history` 是对原生 effect 的脚本封装。 |
| Elder Kings 2 `2887120253` | `common/scripted_effects/ek_ep1_unique_artifacts_creation_effect.txt` 给独特宝物使用 `created_before_history` 或 `discovered`；其 `gui/window_artifact_details.gui` 仍绑定 `[HistoryEntry.GetDescription]`。 |
| LotR: Realms in Exile `2291024373` | `common/scripted_effects/00_ep1_artifact_creation_effects.txt` 依历史情形追加 `given`、`discovered` 等原生类型，并设置 actor、recipient、location。 |
| After the End `3192256710` | `common/scripted_effects/ate_artifacts_creation_effect.txt` 设置创建记录并用 `add_artifact_title_history` 导入头衔持有史。其 `localization/english/replace/inventory/inventory_l_english.yml` 虽包含全部 34 条原版历史标题/正文键，逐行比对与原版相同，不是逐宝物自定义文案的示例。 |

## 可做与限制

1. **可做：自定历史事实。** 可为指定宝物预填或后续追加多条记录，选择原生 `type`、日期、人物与地点；显示出的句子由该类型的本地化模板生成。这足以制作截图那样的传承时间线。
2. **可做：统一改写某一类历史措辞。** 在 mod 本地化中覆盖 `artifact_history_inherited_desc` 等键，就能改相应类型的文字与排版；这是**全局覆盖**，所有使用该类型的宝物都会受影响。`localization/replace` 可作为整文件覆盖路径的现成实例。
3. **原生 history effect 没有已公开的“这一条记录的任意文本”参数。** 文档列出的字段是类型、日期、actor、recipient、location；类型列为 enum。`create_artifact.description` / `set_artifact_description` 改的是宝物左侧介绍，不是右侧历史行。当前检查的几个大型 mod 也都复用原生历史类型，没有证据表明仅添加一个新的 `artifact_history_my_type_desc` 键，就能让 `type = my_type` 成为可用的新历史类型。
4. **若必须逐宝物写完全自由的故事句子**，可研究覆盖 `gui/window_artifact_details.gui`，在历史区域额外展示 mod 自己保存的文本/事件记录。它会是自定义 GUI 展示层，需要单独设计日期与角色关联，并做实机验证；目前不能把它当成已经证实可替换原生 `HistoryEntry.GetDescription` 的方案。

推荐先使用原生历史 effect 建立真实传承记录；只在确实需要逐条自由叙事时，才另做 GUI 展示。
