# R0176：selected93 的拆分、合军与角色微实验

机器 `desktop-3fevhd2-1c74096080`；源树 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`，a06 normal；CK3 1.20.0.4/build25734779。现场绑定 PID4992/create134365619855039955/gen1、actor31254、episode `native-31254-ab05e6628183`。原实际回执时间为 2026-10-15T18:51:38.763124Z（post-split strict 失败）与18:57:19.144439Z（post-merge 完成）。本页是其后离线复算，不新增游戏动作或执行资格。

原件与字面投影入口为 [actual-literal-projection.json](evidence/episode04-r09-selected93-12004/actual-literal-projection.json)。保留三份小 packet、原 strict FAILURE、post-merge RESULT、冻结卡及三份 fullraw 的尺寸/SHA 引用。fullraw 的读取与便携归档由独立 archive lane 管理；本次 reader 不打开其中的路径。

| 阶段 | 实际身份和实体 DATA | 实际统帅与角色 |
|---|---|---|
| baseline | CUnit93→CArmy85；四个 ArRg673–676，unique physical250/250 | 93当前统帅 absent；Army18有空DATA、cache1/1的ArRg59→Character34232 |
| split 一次 | fresh roster独立新增CUnit162→CArmy155；93保留；实体DATA值、persistent/chunk身份与ArRg occurrence全部守恒 | 93仍无统帅；162当前统帅34232；Army18仅移除空DATA ArRg59，Army18统帅31254保持 |
| 93←162 merge 一次 | 162独立消失，93→85存续；原四ArRg仍250/250，零新增空DATA1/1 | 93当前统帅34232；没有新增或移除选中cohort的Character1/1记录 |

三阶段日期都是53146632。94/95严格保持。全部 **available** 军队的 physical DATA 值与按ArRg记录的 occurrence 也守恒；这比只比较选中军队总人数更强。16777321在全scope查询中始终真实 `native_carmy_not_found`，只核了snapshot中的身份、owner、位置和原因保持；它的兵力仍未授资格，不命名未证单位类型，不填0，不能称为all-roster strengths通过。

原 post-split strict 检查因 Army18 cache1196/1196→1195/1195而失败。失败原件与 `strict_unrelated_freeze_pass=false` 均保留。离线后验只接纳唯一实际例外：ArRg59原为完整空DATA、cache1/1、native Character predicate true，解析Character34232、backlink与extension匹配；新162的独立current commander恰是34232。该变化与已闭actual.4 split调用 `296CD0A→28CC460` 清理旧Character关联后设置统帅相容。现场没有观察源PC执行，不能写成“实测该指令执行”、兵力补员、Character新生或Knight成员资格；也不泛化接纳其他角色差异。

可复用的pure reader为 `qualify_r0176_selected93_micro_12004`，位于 `ck3_autonomous_player/src/xar_autoplayer/bridge/episode04_r09_selected93_actual_12004.py`。它复算现有DATA/角色/独立commander合同，只接受这次具名例外。命令：

```text
python -B -O tools/validate_episode04_r09_selected93_actual_12004.py docs/ck3-native-ai/evidence/episode04-r09-selected93-12004/actual-literal-projection.json
```

四个新增定向测试覆盖实际投影通过、physical变动、统帅错配、stale frame/未知行伪资格拒收。投影是原生产normalizer与capturepacket的字面字段抽取，不提供第二套fullraw解释器。source packet SHA与外部归档证明原件完整性，pure语义reader与完整性资格分开。

视频可说：“本次选中军队拆分再合军，250实体DATA守恒；另一个1/1角色记录消失，同时其角色成为新军及合军后的统帅。”智能体可使用独立发现的 sibling162，不能从ACK猜ID；不能把1/1计入补员量，也不能自动重试未知动作。

**R09全卡仍未闭合。** 冻结 `EXPERIMENT-CARDS.md` 的R09还要求从原微实验baseline独立验反方向merge、完整stock/cap/weights前后对比，以及30–60秒split→merge→survivor/commander/queue/supply动态镜头。本次只授selected93这一方向的DATA/角色/身份后验；没有额外录制资格、全局兵力资格或全卡结论。
