# CK3 1.19.0.6：墨西拿战斗五支军队的 UI 标题边界

结论：**目前不能给五支军队写出“游戏实际显示的精确标题”**。已证的链是“配对原生存档中的 army name seed → 原版省份／地产 key 与简中基础名”，以及“原版军队窗口／右侧列表 → `Army.GetNameNoTooltip`”。原版简中另有 `ARMY_NAME` 等标题模板，但缺少这五支军队在对应暂停帧中该原生 getter 的分支、`id=0` 到 `$NUM|O$` 的换算和 `Province.GetNameNoTooltip` 的实际返回。把种子与模板直接拼成屏幕标题会越过这三处缺口。

[独立 sidecar](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_army_ui_name_boundary_v1.json) SHA-256 `057CD813FA840CCA90FFA6E7249D1CFAB65AB2F023FB962469AB79C8693BED3D` 由[只读投影器](../../ck3_autonomous_player/tools/project_native_episode01_army_ui_name_boundary.py)逐文件校验第 11／21 日不可变原生存档、Rakaly 解码文本、原版 GUI、本地化、地图定义和 landed titles。它引用[双方人物与军队身份 sidecar](episode01-day11-day21-combat-human-names-2026-09-27.md)，不修改旧结论。五支军队在两日的保存 `name={id=0,province=...}` 均一致；第 11 日战斗进攻方只有前三支，第 21 日 `22` 才入列。

| ArmyID | 已证 owner 的安全称呼 | 存档 name seed 的 ProvinceID | 原版 barony key／简中基础名，**并非已证 UI 军队标题** |
| --- | --- | ---: | --- |
| `16777221` | 阿里的军队；内含 87 号穆巴里尊 | `2638` | `b_syracusa`／叙拉古。该存档相应 title 动态名为“塞尔古塞”，更不能只拿静态基础名拼标题。 |
| `16777231` | 塔米姆的军队 | `4578` | `b_mahdiya`／马赫迪耶 |
| `27` | 拉马丹的军队 | `2646` | `b_malta`／马耳他 |
| `22` | 穆尼斯的军队；第 21 日加入本场 | `4598` | `b_al-qasrayn`／卡塞林 |
| `18` | 罗贝尔的军队，战斗防守方 | `2619` | `b_trani`／特拉尼 |

原版 `gui/window_army.gui:333,462` 的军队标题和 `gui/hud_outliner.gui:737` 的列表标题直接用 `[Army.GetNameNoTooltip]`。原版 `localization/simp_chinese/core_l_simp_chinese.yml:107–111` 分别提供 `ARMY_NAME: "[PROVINCE.GetNameNoTooltip]第$NUM|O$军"`、劫掠队、交易团、无地角色与集结中的不同模板。这些文件说明**有多个可能分支**，没有证明保存的 `id=0` 本场必走普通模板，更没有证明零号对应第几军。原版 `ArmyComposition.GetName` 是另一个 getter，不能代替已选军队与右侧列表的 `Army.GetNameNoTooltip`。

下一次最小同帧只读取证：在无 mod、简中、精确 EXE 的第 11／21 日暂停帧，先用原生查询绑定 `CombatID 16777218`、日期／paused revision、五支完整 Army/CUnit ID、owner、存档 name seed 及当日 stored roster。再通过已注册的**原生 `Army.GetNameNoTooltip` getter**对每个仍存在的 ID 只读求值，记录 getter 的精确 UTF-8 返回、locale、调用状态、revision 和原始响应 SHA；游戏窗口／右侧列表的可见标题另存截图并逐 ID 对照。选择目标军队若改变 UI 选中状态，须在同一暂停日期重新核对 revision 与 ID，不能把看起来相同的一行猜配给某个军队。`22` 的“本场参战标题”只在第 21 日核对。getter 不可安全调用、ID 映射失败、locale 不符或画面和返回不一致时保留 RED。

在补证之前，视频字幕与智能体日志使用表中“阿里的军队”等**解释性称呼**，旁边保留 ArmyID；讲本场侧别时说“阿里一方，拉马丹指挥”与“罗贝尔一方”。不要写成“叙拉古第一军”“塞尔古塞第一军”等未经本场 UI 核对的原版标题。
