# CK3 1.19.0.6：墨西拿战斗的军队、人物与双方称呼

[独立身份 sidecar](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_day11_day21_combat_names_v2.json) SHA-256 `9D9385F55B3FAC7A74CDDA4D2A51C8DB1FCE2E96EEFE4727460B372E53D81D9A` 由[只读投影器](../../ck3_autonomous_player/tools/project_native_episode01_combat_names.py)复核第 11／21 日不可变原生存档、对应 Rakaly 0.8.19 解码文本和原版简中本地化。存档与解码文本的逐文件 SHA、所用原版文件 SHA、每个对象块的行号及块 SHA 均在 sidecar。此映射沿用[87 号穆巴里尊的配对存档身份](maa-regiment-87-save-name-identity-2026-09-27.md)，不改写旧 v3 回执，也不把存档字段冒充同帧 UI 读回。

| 原生关系 | 第 11 日 | 第 21 日 | 可给观众看的解释性称呼 |
| --- | --- | --- | --- |
| `RegimentID 87 → ArmyID 16777221` | 兵团在该军 `regiments` 中；军队 `owner=31549`、`commander=31549` | 同一兵团、owner、commander | **阿里所属军队的穆巴里尊**。这里的“阿里所属军队”是解释标签，不宣称是游戏生成的军队标题。 |
| `CombatID 16777218` 的进攻方 | stored armies `[16777221,16777231,27]`；各军 owner 依次为 `31549/32725/34320` | `[16777221,16777231,27,22]`；新增 `22` 的 owner 为 `32231` | **阿里、塔米姆、拉马丹的联军**；第 21 日再加**穆尼斯的军队**。 |
| 同一战斗的防守方 | stored army `[18]`，owner `29829` | 相同 | **罗贝尔的军队**。 |
| 双方主要人物与战场指挥 | 进攻方 `leader=31549`，实际 `commander=34320`；防守方 `leader=commander=29829` | 相同 | **阿里一方，拉马丹指挥；罗贝尔一方，罗贝尔指挥**。不能把进攻方 leader 阿里称为本场唯一战场指挥。 |

人物名的证据链是存档 `CharacterID → first_name` key，再到原版 `localization/simp_chinese/names/character_names_l_simp_chinese.yml`：`31549 Ali→阿里`、`32725 Tamim→塔米姆`、`34320 Ramadan→拉马丹`、`32231 Munis→穆尼斯`、`29829 Robert→罗贝尔`。第 11／21 日逐一一致。存档还把阿里的 nickname key/text 冻结为 `nick_benavert`／“贝纳韦尔特”，罗贝尔为 `nick_the_fox`／“狐狸”；原版简中昵称文件也分别匹配。昵称、王朝与头衔在实际 UI 中如何拼接尚未实机读回，不把这里的名字组合说成完整 UI 原文。

统治者领地可进一步绑定：存档 TitleID `2111` 是 `c_siracusa`、holder `31549`，其**存档动态名**为“塞尔古塞”；TitleID `2141` 是 `d_apulia`、holder `29829`，动态名为“阿普利亚”。原版静态简中 `c_siracusa` 却为“锡拉库萨”，所以解释画面中的阿里领地时优先注明**这份存档中的“塞尔古塞”**，不能只按原版静态 key 翻译。`c_`／`d_` 可说明头衔层级，但文化、政体、昵称与 UI 模板下最终显示的“伯爵／公爵”等完整称号未在本证据中直接读回；视频可保守写“塞尔古塞领主阿里”和“阿普利亚领主罗贝尔”。

ArmyID `16777221` 的保存 `name={id=0,province=2638}` 在两日一致。ProvinceID `2638` 经原版 `map_data/definition.csv`、`common/landed_titles/00_landed_titles.txt` 指向 `b_syracusa`；本地化基础名“叙拉古”，这份存档的 TitleID `2112` 动态名仍为“塞尔古塞”。这只证明**军队名称生成种子**，没有保存实际渲染字符串；不得凭这些字段断言军队在 UI 中恰好叫“叙拉古军”或“塞尔古塞军”。

为避免同号误读，`CombatID 16777218` 是含 `phase=main`、`combat_results=16777218`、`province=2633` 的战斗对象；存档中还存在同数值的死者 CharacterID 和其他对象。投影器按对象类型、字段与缩进绑定，不能用一次文本搜索把它们混成同一人。若下一期要展示精确完整 UI 头衔或军队标题，最小补证是在相同暂停帧用游戏界面或受控原生 display-name getter 读回，并保存原始响应、对象全 ID、日期和画面；没有这项读回时沿用上述**解释性称呼**即可。
