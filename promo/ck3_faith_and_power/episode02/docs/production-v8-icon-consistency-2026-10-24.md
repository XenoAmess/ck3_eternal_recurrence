# 第二期 V8：图标一致性修订交付

2026-10-24，`machine_id: 4-8e1c2f1861`。已统一19张卡片中的同页同级图标，并同步62处重复引用。当前审阅片为 **[V8图标修订版：29分30.933秒、1440p](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/v8-clarity-20261024-a01/icon-consistency-a01/sample/build-a01/native-run/derived/direct/episode02-review.mp4)**。[双语字幕](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/v8-clarity-20261024-a01/icon-consistency-a01/sample/build-a01/native-run/derived/direct/text/episode02.bilingual.srt)、[讲稿](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261023-a02/v8-clarity-20261024-a01/icon-consistency-a01/sample/build-a01/native-run/derived/direct/text/episode02-script.md)及[机器可读记录](production-v8-icon-consistency-2026-10-24.json)配套交付。本机沿用既有本地交付偏好。

| 用户重点 | 已完成的统一 |
|---|---|
| 主虔诚 | C02右栏及C03三个阶段的右栏补同一虔诚图标，与左栏一致。 |
| 最终经验 | C05右栏补同一经验图标，与左栏一致。 |
| 朝圣者收容所 | M01四建筑行均有同源图标，统一96px行高。 |
| 老道的朝圣者、高效的朝圣者 | C06三档标题均有朝圣者基础图标，经验档位继续由文字区分。 |
| 鼓励、强制 | C06三栏各自配相同教义图标，共补四个缺槽。 |

上述7张旧页共补14个缺槽。全图配置检查还发现8张费用焦点页存在同类缺项：N20-multipliers-3、N20-humility-law及N20-later-1..6，新增16个行内图标；并统一C08、F01、D02、SUP-MECCA-INITIALIZATION四张条件／对象卡。C08和SUP-MECCA的同级条件值均配图标，类别标签保持相同样式；F01三个条目和D02四个条目均配对应对象图标。既有页首身份图例保留。

审计范围为实际路由的135张不同图片：74份焦点页配置检查，审计agent实际查看61张旧图／混合UI图及3张原焦点图；Root逐张实际查看全部19张重建PNG。**没有将135份配置审计写成135张原图全部人工看过。** [全图审计](../../../../docs/ck3-native-ai/evidence/faith-e02-v8-clarity-20261024/icon-consistency.audit.actual.json)保存范围与19张新图pin；[旧页规格](../../../../docs/ck3-native-ai/evidence/faith-e02-v8-clarity-20261024/icon-consistency.legacy.spec.json)、[焦点页规格](../../../../docs/ck3-native-ai/evidence/faith-e02-v8-clarity-20261024/icon-consistency.focused.spec.json)及[条件卡规格](../../../../docs/ck3-native-ai/evidence/faith-e02-v8-clarity-20261024/icon-consistency.conditions.spec.json)保存重建输入。

图标沿用原版DDS颜色、比例和既有GUI裁帧。事件折扣使用有来源的事件主题图，神王AI使用曼荼罗政体对象符号；它们不冒充专属变量图标。法律、当地仪式、凝聚力、通用旅行／圣地／头衔等来源绑定见[原版素材与定义核对](../../../../docs/ck3-native-ai/evidence/faith-e02-v8-clarity-20261024/icon-consistency.sources.actual.json)。原技能perk.hill已按owned帧裁切，本轮没有把原有裁帧误报为新修复。

本轮只替换N07、N08、N20、N21、N24、N26、N27、N28、N30、N31、N32、N33共12个cue内部的62处image pin。33段音频、请求、字幕文本、所有时钟与visual frame interval保持不变，无新TTS或游戏素材。新片的中文、英文、双语SRT及讲稿均与上一轮V8逐字节一致，三种字幕各258组。前轮六项内容修订、英文技能别名与机制边界继续见[原V8制作记录](production-v8-local-review-2026-10-24.md)。

新片93,195,477B，SHA-256 `5d8f5fee0373db2425620a713940f2139336472388b03dd9634df87c20a8bc29`。H.264、2560×1440、30fps、53,128帧；有效音视频1770.933333秒，容器1770.954687秒，视频首PTS为0.021354。AAC双声道48kHz，平均−22.6dB／峰值−3.7dB。真实公共 `episode01_formal.py plan/build` 使用单worker，document预算1,776,223,450B；原Popen于12:34:57.563685Z启动，13:11:56.839023Z实际wait完成，退出0，完整墙钟2219.275秒，无自动重试。[实际退出](../../../../docs/ck3-native-ai/evidence/faith-e02-v8-clarity-20261024/icon-consistency.build-exit.actual.json)与[公共完成记录](../../../../docs/ck3-native-ai/evidence/faith-e02-v8-clarity-20261024/icon-consistency.completed-review.actual.json)已按原字节归档。

完整AV解码、全部帧PTS／CFR检查、字幕与五个配乐窗口通过；真实 `xar_promo.project.load_document(check_files=True)` 验证109份manifest工件。[工件与文本核对](../../../../docs/ck3-native-ai/evidence/faith-e02-v8-clarity-20261024/icon-consistency.manifest-verify.actual.json)绑定本次实际清单。Root又从新最终视频实际抽取、逐张查看19张修订卡各一帧，确认同级图标一致，未见图标遮字、裁切或侵入字幕区；[19帧查看记录](../../../../docs/ck3-native-ai/evidence/faith-e02-v8-clarity-20261024/icon-consistency.final-frames.actual.json)保留逐项pin和实际时间。状态仍为 `ENCODED_REVIEW_PENDING`：单帧查看和自动检查不授完整人工1×听看或用户签收。

旧页复用保留的author／compositor，8张焦点页复用既有Java ClarityCards生产者；执行前核对源码、全部classes和jars，实际渲染命令退出0。没有新增生产实现、修改Java源码或重跑Maven；前轮严格编译与8项定向测试仍属于前轮证据，不将它们计为本轮重测或全仓CI通过。正式输入为外置 `icon-consistency-a01/V8.FORMAL-INPUT.a11.all-icons.render.json`，770,584B，SHA-256 `70c527a9450e8dc51ae69e060af4cb018919b5deffb0f3d03f4f75d2dbdf1985`。精确渲染源码为 `8bcff51b0d7767b69643e5ec77920c1c932abed5`，归档标签为 `archive/faith-e02-v8-icon-render-source-20261024`；后继集成HEAD单独登记，不追认参与本次编码。

本轮容量准备精确删除36份可重建／同SHA重复文件，Native allocation为269,025,280B：上一轮V8的33个中间cue视频及3份临时存档副本。保留同SHA母档、V7与上一轮V8最终片、原片、声音和来源；已删除路径现不可读，前轮109工件通过只证明其当时状态。另对370份已关闭keeper输出与2份JSON报告进行透明NTFS无损压缩，保留原路径、FileID、内容SHA及写入时间；372文件实际allocation减少196,591,616B，删除数0，不重置原到期日。精确计划／实际结果在外置工作根的 `retirement-a01/`、`lossless-keeper-compression-a01/`、`lossless-report-compression-a01/`，没有删除整棵目录。

存储延续原accounting origin、206行addback账本及11,594,943,480B addback，quota信用0。有限77GB上限仍于2026-10-24T15:00Z硬复核，不自动续期；G70足额渲染准入已由G71的64MiB审片／文档／Git尾项替代，禁止新增编码、TTS、游戏或回收。G70内继承的旧a04完成字段仅为历史，外置 `G70-SCOPE-CLARIFICATION.actual.json`已明确。正常提交推送后执行future归零；实际推送与闭账结果分别读取外置工作根 `SOURCE-DELIVERY.actual.json`、`CLOSED-ICON-CONSISTENCY.actual.json`及卷HEAD，本文不预写尚未发生的CAS。必要输入与保留母档限期保护到2026-10-30T12:00Z；新派生48小时、视频30天、小记录180天按用途复核，详见外置 `RETENTION.actual.json`，不声称部署了自动清理。

本轮未启动CK3、Native、OBS或新录制，未操作Steam与屏幕，不声明当前Steam离线，也不增加实机业务、G2或普通auto能力信用。
