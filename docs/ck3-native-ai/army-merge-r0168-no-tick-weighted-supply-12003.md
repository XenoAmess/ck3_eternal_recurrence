# CK3 1.20.0.3：R0168 同日合军的真实补给加权与完整兵团继承

2026-10-05。Root 使用 exact `ffc29e7c6f616592c0186f18570759eb36f30206` / a07 DLL SHA `7fcd53d122c7ee9eeecb1230a7659f7116a9831fd49462caee1589ab3a994d8c`，原始7f Jan11 checkpoint，在同省1506实际执行 `merge-armies-0-with-16777220`。游戏1.20.0.3、EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`；人物33388、episode `native-33388-8baabd4dc94f`。这是本期第一次紧邻完整 D/S 数值合军实例，独立于R0161半拆、R0165补员、Robert旧会合及A/B/C试验。

[原始证据索引](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0168-merge/index.json)归档十份实际public packet，另保全Root actual admission/sdk-ready、独立结果与action-before、既有只读分析器及其真实执行报告。[review报告](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0168-merge/merge-review-report-a01.json) SHA `503459aa61f3a92a493dd43e468487ba1b95b4f8fd1edf25f6fe87bb99f5f24e`；执行exit0、全部required checks verified、status `OBSERVED_RECEIPTS_MATCH_WITHIN_DECLARED_ROOT_BINDING`。原public source中game_version/executable_sha256的null没有补写；exact build经Root单独证据绑定，分析器不attest正在运行的进程。

## 紧邻暂停帧及完整身份

before snapshot、Strength、两军Commander和bracket全部同raw53147376（Jan20）、paused/map_ready、public26/native25/`native:25`；独立after同rawdate、public27/native26/`native:26`。演员和episode相同，query frame/bracket及action提交方向、owner、province、全controllable set一致。post保留D public/native0，S public/native16777220从完整己军roster消失；没有再query已经消失的S。

| 实读 | 合前D0 | 合前S16777220 | 合后D0 |
| --- | --- | --- | --- |
| 实际人数/最大人数 | 5660/5660 | 1086/1087 | 6746/6747 |
| 完整regiment数 | 13 | 14 | 27 |
| 库存raw / scale100000 | 8299737 | 29122808 | 11651751 |
| 容量raw / scale100000 | 10000000 | 30000000 | 30000000 |
| 当前统帅 | 原生absent、ID null | 27357 | 27357 |

D团ID `[0..12]`，S为`[50..62,82]`。两个pre集合disjoint，post正好是27个完整ID并集，每个团的current/max逐ID相等，含0人数团；各完整行sum等于各自原生verified整军aggregate。D nativeCArmy0保留，S全部14团转移至D。完整逐团列表和异常集合输出均在review，missing/extra/changed集合为空，不能只凭6746人数总和声称团身份守恒。

## 真实原生定点数值

复用[角色权重观测](army-merge-role-weights-observer-12003.md)和[原生执行树](army-meeting-merge-supply-inheritance-12003.md)。目的角色D使用合前该军新原生 `merge_supply_destination_weight_raw=566000000`，本例恰等于自身5660×100000，不构成所有军队或未来场景的恒等式。被吸收角色S使用同一合前S已由原生getter与完整团sum核验的1086×100000=`108600000`；不能误用S作为目的角色时的字段`108100000`，也不能换用post权重。

| 顺序 | 原权重raw | 原库存raw | trunc(weight×100000/674600000) | trunc(share×stock/100000) |
| --- | --- | --- | --- | --- |
| D先 | 566000000 | 8299737 | 83901，除法余数385400000 | 6963562，乘法余数34037 |
| S后 | 108600000 | 29122808 | 16098，除法余数289200000 | 4688189，乘法余数63184 |

两阶段截断贡献依次累加，`6963562+4688189=11651751`，严格匹配合后实读库存（116.51751 supply单位）。share合计99999，不人为补齐或重归一成100000，也不改为一次浮点平均。新容量30000000直接来自post Strength；Commander27357独立post实读，不从quality猜容量，也不把100与300相加/平均。本例`preclamp11651751 < postcapacity30000000`，为**真实非截断加权实例**；upper-clamp实例标志false，不能声称已实证上限截断。post monthly raw−877192/scale100000（−8.77192/月）是当前省getter，未把两军月值相加。

## 供给时钟观察边界

| 字段 | 合前D | 合前S | 合后D |
| --- | --- | --- | --- |
| +188 storage64 | 300333821678253472 | 300064531523761328 | 300333821678253472 |
| +188 date raw | 53147040 | 53146800 | 53147040 |
| +190 storage64 | 300061168564366016 | 300061194334169936 | 300061168564366016 |
| +190 date raw | 53144256 | 53144400 | 53144256 |
| actual bucket phase | 0 | 20 | 0 |

post实读全部等于preD、与preS不同。这支持本次D历史标记保留的端点事实，不重构未观察的内部transition，也不声称合军重启宽限、发生新的成功补给更新或新统帅承担了旧日期全部历史。

## 尚待完成

本例闭合不同库存、角色权重、两阶段fixed顺序、新将领/实际容量与27团完整转移的同日合军核验。仍需独立真实`preclamp > postcapacity`上限截断正例；Commander更高quality候选排序的所有分支、特殊大数native域不因本例全验。原始录像、TERM10多选warning/mergebutton像素、continuous clean spans及人工1×审阅由Root/capture lane另验，文件review没有新增执行或影片签核信用。

Root随后保存的Jan20 postmerge共同候选为72,572,576B，SHA `dcd54f1270e4c5e18af2d2a8adb5b9d2af2cd5af60ae3d71330b782adf122260`，保存后public28/native27；本包只记录Root提供的候选定位，未把新save归入上述无tickmerge窗口。A/B/C两处正补给地点、两条合法route和三独立同档回放仍待筛/执行；保存本身不赋A/B/C完成信用。

显式主venv Python3.14.7用于现有只读分析器；20个历史fake fixture不重跑。`open_kaishek`为not-applicable：本工作包处理已保存public DTO和compiled native定点语义，没有CK3 script语料/改写。日/周字段分别记录actual receipt readiness、完整D/S及27团、raw权重/库存/容量/中间截断、实际post统帅与anchors、非clamp/剩余clamp门槛、原片/TERM/clean span/1×审阅状态，不能由素材分钟或单一PASS计算正式完成百分比。
