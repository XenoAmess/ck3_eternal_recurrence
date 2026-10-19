# 原版建筑轨道开窗的有限增量

本候选叠加 V6 已冻结 Python a01，不改该原件。`machine_id: 4-8e1c2f1861`；来源与观察时间见同包交付清单。只新增 `open_building_track`，沿现有 `ck3_present_faith_power_ui_v1`、`navigate-ingame-ui-v1` 和 owning-thread 执行；没有新工具、native step、capability 或 flag。

请求固定为 `window_kind=holding`、当前实际 ProvinceID、`presentation_target=holding_building` 和当次原生 installed-row census 的 index0..127。tab/receipt 必须为空，不接受 potential preview 行。原版 GUIBuildingItem.OnClick 路线用于切换建筑轨道窗口，与 potential-item ShowDetails206 分开；不能据此发 Construct、Upgrade 或 Replace。

该动作可能在重复同一行时关闭已开的轨道，因此不具幂等性。ACK 必须来自实际原调用，并保留正确 subject、source_bound 和 target/index；仍是 verification_pending。结果未知后不自动重发。

独立 `ck3_query_faith_power_ui_v1` 可返回可选 `presentation_ui.holding_tracks`：原 owned tracks 的存在、root、实际可见性与选中类别/模式/动作/定义键。旧 a01 缺此字段或返回 null 时保持 unknown。只在原 owner/back-pointer/root 双读成立后记录对应观察；未闭合的选择字段保持 null。主 holding 窗口可见、空候选列表或一次 ACK 均不能代替 tracks 可见后态，更不能证明建筑业务完成。此结构也不授予 rendered pixels 信用。

本包只执行新增207与可选 tracks 的 Python 合同/Driver/Service/MCP 窄测试；快照和 transport 为合成注入，不宣称 C++ fixture、原生调用、实机或画面通过。原 frozen a01 的13项矩阵不在本增量重复执行。正式构建与真实后读由后续单独准入完成。

## P18与R32：installed正文已有像素，完整Construct仍缺（2026-10-19）

`machine_id: 4-8e1c2f1861`；本节追加截至2026-10-19T09:43Z的实际结果，不覆盖上文候选阶段范围。P18已沿既有目标实际编译／运行navigation fixture退出0；实际编译来源`98ee48319f947624654a8b73b58aedc15fb994da`，R32冻结`8efe5f985b78b1db1530e48a2f05da7c30bea89e`只沿逐pin源码等价复用，完整来源见[展示专题](faith-power-presentation-ui12004-v6.md)。R31 allocate后未启动即闭场，不能充作一轮建筑实测。

R30的next definition不是nullptr，而是精确canonical Null。P18只在可选位接受`[base+0x5D1E320]`的原版Null形状：vtable `0x48AC828`、magic `0x4E756C6C`、ordinalFFFFFFFF、hash0、size0/cap15、inlineNUL，保留source pin／双读及普通ObDG非空实体守卫；required definition仍拒绝。R32于08:42:30Z对Mecca6223的installed special index4悬停实际得到source_bound=true、dispatch=true和nonce，随后08:42:33完整建筑正文原图可用，原R30 definition-identity拒绝未再挡住该行。这是该来源路径及实际像素的通过，typed tooltip source/top-stack/cache join仍未取得GREEN，不由ACK推定全文读口合格。

同一Mecca行的207于08:53:29Z返回`presentation_original_callback_admission_or_dispatch_failed_do_not_retry_if_attempted`，native_dispatch_attempted=false；未打开tracks，不按九例反复重试，也没有取得potential候选或完整Construct条件窗口。空特殊槽位显示的“租户或事实上领主”只是当场局部阻因，不能当所有建造条件或特定目标可建许可。

R32最终[index-a02](C:/workspace/ck3-faith-and-power-20261017/episode01/live/4-8e1c2f1861--faith-and-power--R0032/ORIGINAL-GUI-CAPTURE-INDEX-a02.json)27,497 B／SHA `635e5d7ae96e29c8aa650116d6be85e98bdc75c0d4af2945a3a267f7c35bfb30`绑定八张原图及operator／Root的逐图审阅。本节仅读其小记录，没有重审图片。九目标的消费范围如下：

| 目标key | 原版目标名 | 本场来源与解释范围 |
|---|---|---|
| `holy_site_great_mosque_of_mecca_01` | 麦加大清真寺 | 08:42:33当前目标本体；不是Construct条件 |
| `hagia_sophia_01` | 圣索菲亚大教堂 | 08:54:48当前目标本体 |
| `hagia_sophia_02` | 阿亚索菲亚清真寺 | 未取得02本体／候选；用真实01作地点锚，另标源码规则 |
| `dome_of_the_rock_01` | 圆顶清真寺 | 08:56:20当前目标本体 |
| `temple_in_jerusalem_01` | 第三圣殿 | 未取得目标本体／候选；当前圆顶清真寺不能冒充第三圣殿 |
| `brihadeeswarar_temple_01` | 苾利诃地湿伐罗神庙 | 08:56:44当前目标本体；创新与宗教条件另据源码 |
| `parthenon` | 帕特农神庙 | 未取得目标本体／候选；08:57:11雅典现有诞神女教堂保留真实身份 |
| `palace_of_ctesiphon_02` | 泰西封大王宫 | 未取得复建02；09:06:04实际省份4796是废墟01，县都4828不当该地产持有人 |
| `etchmiadzin_cathedral` | 瓦加尔沙帕特主教座堂 | 未取得本体／候选；08:57:40仅亚美尼亚礼仪地产、空槽及局部禁用提示 |

因此是四个目标本体、六个现有建筑本体、七处地产；五个缺失目标以明确标注的源码规则图解补足解释，不制造未显示的窗口。[建筑来源范围a34](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v6-20261019/resume-20261019/authoring/building-rules-a34/BUILDING-SOURCE-SCOPE.a34.json)15,452 B／SHA `be9c28247be11b24a744fe9629d48b29d3a481cc5739e6824096405fa4e73892`保存九定义各phase及源行，原`00_special_buildings.txt` SHA `33322505fa7f79ca1a61fdc2682d3e0c36ec0a063cbafe95ba615479b5e3f8b4`。`is_enabled`、`can_construct_potential`、`can_construct`须分开；条目为空或宗教分支成立都不能免除外层普通建造规则。既有收益的主体仍是画面所示当地holding／county／holder，不是罗贝尔新收入或已付费建设。

[最终a35来源范围](C:/workspace/ck3-faith-and-power-20261017/episode01/revision-v6-20261019/resume-20261019/authoring/r32-final-lineage-a35/R32-FINAL-SOURCE-SCOPE.a35.json)2,190 B／SHA `073232f92b1d2274459ec8adf3e83f8b7645030101fe9507959d24527771b527`将八图封到最终index-a02，明确完整Construct=false；没有用first index或旧lineage给后补对象代签。R32无world Confirm、day、新存档或录制，原生GUI/retained OS0与host1 RED并存；正式影片编码、完整听审及1倍速观看尚未在这些素材资格中完成。
