# 《CK3：信仰与权力》第一期 V6 接手续作

按用户“去度假，编写交接到 docs，由同事接手”的指令停止制作。本交接替代系列入口中旧的开拍状态，保留历史记录。**V6 尚未成片；接手目标是完成缺图、剪辑和本地交付，同时继续沉淀游玩智能体知识及现有 MCP 能力。** 不要重新做已经完成的配音、字幕、采用实验或整套工具链。

编写机器 `machine_id: 4-8e1c2f1861`。2026-10-19T01:26:23Z 重新运行 `tools/ck3_live_run_id.py machine` 确认身份；各阶段实际观察时间、来源及停工回执见下表。本文记录本机，不授予其他机器安装、权限或实机资格。本文最后的“现场与容量收口”记录最终停止结果。

## 先读这些，再开始

1. [系列研究与讲解方法](../../promo/ck3_faith_and_power/docs/production-lessons.md)和[制作经验](../../promo/ck3_faith_and_power/docs/production-experience.md)：这是用户反复指导后归纳的方法，不只是本期措辞纠错。
2. [第六轮整改与实际进展](../../promo/ck3_faith_and_power/docs/episode01-revision-v6.md)、[当前逐句镜头单](../../promo/ck3_faith_and_power/docs/episode01-current-shot-list-v6.md)、[当前中文稿](../../promo/ck3_faith_and_power/docs/episode01-narration-v6.zh.md)。旧144句已归并为135段，不能照旧稿重新配音。
3. 本文的恢复顺序及 `S/authoring-deltas-a08/REMAINING-MEDIA.md`。后者列59对象组的逐章缺图，不需要重新审计全部历史媒体。
4. [根 AGENTS](../../AGENTS.md)、[公共验收入口](../ck3-mod-upgrade-fast-validation.md)、[存储策略](../storage-retention-policy.md)与[参数](../storage-retention-policy.json)。本项目禁用 PowerShell，Windows 命令用 `cmd.exe` 和 Python。

## 用户要交付什么

视频应让玩家明白某项选择适合什么局面：谁有权限、具体条件是什么、得到及失去什么、效果给谁、多久生效、反过来操作有什么后果。围绕玩家的问题组织章节、完整方案和转场；机制证据放在研究文档，讲解不能读成验收报告。

Faith、Religion、当前礼仪、主流礼仪、核心信条和个人信条分别定位。中文名称以该版本原版简中和实际窗口为准，不能自造“县主”“个人版本”等指代，也不随意缩写“智慧之地”。正文中每个“信仰／礼仪”必须有明确作用对象；已经做过154处“信仰”和31处“礼仪”的逐词核对，修改范围和来源在V6记录内。

每句旁白都要决定观众此刻需要看什么。讲具体信条要有对应核心信条原版正文，讲特殊建筑要有建筑本体／条件，讲库存和权力要有相应圣物、人物或窗口。原版画面可嵌入文字解释构图，短注负责强调关系；不能用大片空框和少数字替代对象。原图裁切保留名称、作用对象、状态、条件和操作区域，特别保留“未生效”“预览”等限定。连续旁白可延续同一有用窗口，无须为了句数制造截图。

双向跨宗教采用已获用户决定，**纳入第一期主线并整体重排**。用户允许明确标注准备内容的独立机制实验；已批准先交本地文件，无须等待 OneDrive。所有以后新录制都不出现左上蓝色旧智能体面板，旧素材无需因此重录。背景音乐必须复用 `promo/ck3_native_war_ai/assets/music/quiet-courtly-tension.wav`。

研究必须进入 `docs/ck3-native-ai/`，以规划和决策所需的输入、作用域、合法性、收益、风险及实际后态组织；优先扩充现有原生 MCP 和游玩智能体，而非另建拍摄专用旁路。不要把用户具体脏话和原句变成一份机械禁词表，要持续归纳造成问题的原因和下一次的判断方法。

## 当前完成度和交付边界

停止前最后一次对用户报告的总进度约 **75%**，这是对“V6整改后新成片”的工作量估计，不是测试通过率，也不代表75%的成片已审好。

| 工作 | 停止时状态 | 下一项 |
| --- | --- | --- |
| 机制、文案和术语 | 约95%；135段a04已冻结，关键机制入docs | 随新增GUI核对图文对应，只有真实新事实才改稿 |
| 配音、双语字幕及声钟 | 100%生产完成；未完整人工听审 | 沿用现有声轨与460组字幕，成片阶段听审 |
| 实机素材 | 约75%；双向采用及主要动作已有 | 四种核心信条全文、九建筑实际页优先 |
| 构图和剪辑 | 约70%；现有标准输入及样板 | 补来源、ROI、实际像素及原片有效区间 |
| V6完整编码和最终审片 | 0%；没有V6最终MP4 | 内容ready后走已有正式链 |

声钟为 **42:41.067，30fps共76,832帧**。旧V5为52:33／144段／490组字幕，仍是历史审阅交付，不可改名充当V6。原先给用户的10月19日10:00、10:45、11:30及12:30–13:30节点在本次停工交接后失效。接手后从实际开工时间重估；若既有冷载路径通过，补拍和收图预计1–2小时、合成整理约1小时、完整编码45–80分钟，另留完整1倍速听看片和局部修正时间。新实机故障会改变这些估计，不承诺固定钟点。

## 目录与恢复锚点

以下是本机实际映射；跨机先重新部署、核身份和容量，不把绝对路径写入通用协议。大小和SHA按原生产回执引用；本次不重新哈希大原片或复制整个目录。

| 别名 | 本机路径 |
| --- | --- |
| `R` | `C:/workspace/ck3_eternal_recurrence` |
| `EP` | `C:/workspace/ck3-faith-and-power-20261017/episode01` |
| `V6` | `EP/revision-v6-20261019` |
| `P6` | `EP/production-candidate/value-v6-production-a01` |
| `O` | `P6/authoring/visual-v6-a01` |
| `S` | `O/successor-a02` |
| `P15` | `EP/runtime/religion-candidate-a15-cold-presentation` |
| `B` | `EP/runtime/management-candidate-a04/build` |
| `L25` | `EP/live/4-8e1c2f1861--faith-and-power--R0025` |
| `L26` | `EP/live/4-8e1c2f1861--faith-and-power--R0026` |

### 源码与本机原生资格

当前可复用P15编译资格绑定 **clean `707f456bd318ba1fe7bb94b3be10dd6e1c3e2326`**，不是本交接的后继docs提交。该提交官方 Windows CI `39180304707` 实际成功，2026-10-19T00:44:27Z结束；线性历史CI `39180304698`也成功。P15在2026-10-19T00:34:05Z封资格，Root在00:35:54Z独立读回。只证明实际编译、有限夹具和精确EXE排除，不证明新tooltip／关闭／建筑窗口已实机成功。

| 关键原件 | 大小／SHA-256 |
| --- | --- |
| `P15/qualification-a01.json`、同内容`final-source-seal-a01.json` | 9,044B；`cf7732df6aea800475ece31de11215ba533a1f92c95927ecc88ecfda3619f50b` |
| `P15/publish/xar_ck3_bridge.dll` | 14,647,808B；`d1b84da17b9db28b89c708f4424536e55c8e731aff60353cc590855d407b5965` |
| `P15/input-freeze-a01.json` | 992,874B；`d964c1c903f4fa63a4de54b4f2222497e599a57eb29c4c553f8880c8dad7fb34` |
| `V6/root/NATIVE-A15-ROOT-REVIEW-AND-CAPACITY-CLOSED-a01.json` | 2,836B；`c5c964e63fde99b55c694990087b618eaeb7de83e8993b97ab20f54bdeb365b1` |

P15沿原MSVC链Release／jobs8，仅两个目标，实际31个编译单元和3次link。原build session27967退出0，唯一现有navigation fixture退出0。新增两项Python聚焦检查也通过，实际生产MCP→Service→Driver消费，但底层snapshot／transport为合成数据。不要重复整个旧矩阵或为了docs提交重编DLL。B中的工作navigation EXE已被P15覆盖，不能拿P14旧哈希要求该路径仍是旧文件；P14发布DLL未改。

本系列使用CK3 **1.20.0.4**，后继common manifest的EXE pin为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`（`EP/runtime/common-v6-d2-original-gui-a03/manifest.json`）。本交接没有启动或重新核验游戏安装，也没有切换Steam在线；下次启动仍要当次新鲜Steam离线画面、零CK3进程、机器ID及实际EXE绑定，不能用本文当新实机资格。1.20.1的规则不能直接套到本期0.4。

**后继master与P15冻结HEAD的关系：** 本交接提交及其他任务后继commit不追认P15为新HEAD编译。下一场优先在最新master明确核对相关native源码等价并重新绑定薄生产器，P15的真实编译commit仍保留707f，不能只替换旧qualification的commit，也不因docs变化重编DLL。已观察远端29f77da15相对707f只改共享“从未启动allocation闭场”入口及文档，新增`tools/ck3_mod_acceptance_unrun.py`，没有native源码变化；接手仍需核当时master实际差异。**旧707f allocator不能直接按新unrun闭场作为前驱，因此不要只detach707f就照旧启动。** 若为读冻结源临时detach，先确认干净且无人持有现场，用 `git show master:docs/handover/2026-10-19-faith-power-episode01-v6-handover.md`读本文，完成后回master。不要盲目新建worktree：B的CMake源目录和现有薄生产器绑定原R路径，换根须重新核路径；无需为此再建平台。

### 配音和字幕：直接沿用

| 输入 | 大小／SHA-256／用途 |
| --- | --- |
| `V6/editorial/narration-v6.continuous.zh.a04.md` | 35,824B；`55927d87bd5501a6ed40f1e3ef59e8e3c18802504a5ce245febc865bcfbc38fb` |
| `V6/editorial/voice-timing-a01/voice-authoring-catalog.measured.a01.json` | 263,753B；`5566a249e96d96de4adaa5747a70f4c316cc1814cc25b337009b90dffdbfe3b9` |
| `P6/voice/native-run/derived/direct/measured-narration.json` | 166,018B；`55791616b83d795a5313b3416845bee887eec3af79a3f869e164994a5bf3e181` |
| `promo/ck3_faith_and_power/docs/episode01-subtitles-v6.en.json` | 46,375B；`3ce0dfc249d92417dc090b2f520ca2695304b40f76dc62d434c8ca0493fec2a0` |
| `V6/editorial/subtitle-groups-a01/subtitle-groups.a01.json` | 144,994B；`9b1ab57771ffa928380fe6b5daef9f639e314b3256a68b42e6018d51723f1f08` |

134段新MP3加1段逐字一致的旧C13-04，共135段／17章；实测纯语音2500.056秒，编排2561.066667秒。worker／解码和135段字体检查通过，尚未取得整部人工听审。音乐设置：上述战争原件，旁白0dB、音乐−17dB、offset0、循环、淡入2秒／淡出8秒，不另normalize或duck。

### 当前作者输入：仍为pending

`O/VACATION-HANDOVER-a01.json`为作者线程最终状态，3,642B，SHA `27a4d1c365da22b2ae9f167da85b2541effcba712542c7b85f457881e868e2f9`，观察2026-10-19T01:09:03.549306Z。a11从未启动，未写producer、未生成新图、未创建输出目录；写入者和进程均为0。

| 当前文件 | 大小／SHA-256 |
| --- | --- |
| `S/inputs/formal-input.pending.json` | 1,436,073B；`ef04c987b0cdbfe1583eaa3129ec691ded39d571634d703196d972c6b63888b6` |
| `S/metadata-plan/formal-metadata-plan.json` | 4,011,606B；`cd76c741d69443c6da771bf3414f0765aa552d71535a129473a7f35314e0f2c2` |
| `S/authoring-deltas-a08/REMAINING-MEDIA.md` | 8,073B；`dba89f78b422ab71bfb07aee6b58caedfd7813d467f3dbec4be18f442a77f55e` |
| `S/authoring-deltas-a10/R25-SOURCES-ROI-PARTS.a10.json` | 26,652B；`272ab5b32ee95eb4ef6fb91f02a8e2b6f7769c4a10fdb23e7bc1b0a4b17b3b18` |

当前包含18条raw、26条短静帧、3种构图；125项claim已完成对应审阅，语义pending为0，但`content_ready=false`。`unbound_visual_seconds=0`只说明编排part存在，不证明每句已有合格原版画面。不能直接翻ready开关。

按a08→a06→a07／a09→a10阅读，不要从旧a01输入重新施工。a06的智慧之地创建预览三ROI及版式已经目读接受：SC22样图 `S/wisdom-4k-samples-a05/SC22-major-inactive-preview.a05.png`；它来自真实R0011、PTS91.867／frame921，来源目录误带R10字样。保留“创建预览／主要未生效”，不能解说成净学识或主要收益已到账。内部2560×1440放大到3840，不是原生4K取材。

SC11的a09实际PNG版式、身份和个人信条全文已目读接受；图内仍是旧标题。a10已将最终标题改为“核心信条与个人信条，先看所在栏目”，**最终新标题像素未生成**。a10还接了R25三张圣地／库存／替换预览来源与ROI，尚未审新的裁切／组合像素。原片`selected_interval`仍为null，不能把技术解码通过当剪辑区间已选。

## 实机素材与实际结果

双向采用已有R19／R22真实里程碑：创建新信仰与编辑现有礼仪属于不同实际模式，准备和报价不能混用。现有创建、采用、供奉、替换、退出结果均已归档，**不需要重演这些动作**。旧V5交付的具体索引从[历史交付](../ck3-native-ai/faith-and-power-episode01-value-v5-delivery.md)进入。

### R25：已拍的内容与未解决项

`4-8e1c2f1861--faith-and-power--R0025`／a26正常无保存闭场。public原session16564退出0，allocation30774退出0，CaseClient持有的原HANDLE确认OS0／normal_close_qualified，keeper退出0，CAS11987于2026-10-19T00:15:25.909666Z释放。证据为`L25/root-keeper-stop-proof-a01.json`及`root-screen-release-a01.json`。这不是R26的退出结果。

`L25/ORIGINAL-GUI-CAPTURE-INDEX-a01.json`共10张PNG，9张可按限定用途使用，1张加载图排除；12,062B，SHA `4d2817aa33c38e996387d795ae8f6f5b399c164c5948c1db96cc8782aba19dfd`。全部新图无已废弃蓝色面板。

- 232913Z：哈乃斐派／主流礼仪与“你的礼仪”、逊尼派信仰、左侧核心信条及右侧个人信念同帧。个人当前1/2，仍是“斗争与顺服”；基督教综摄主义是已知完整个人卡，**未采纳为个人信条，也不是核心信条全文**。
- 234206Z、234332Z：巴格达普通／未生效主要效果，圣物总稀有度2、库存3件和选择槽。关联信仰只露出景教一行，不能声称整张共享列表均出镜。
- 235442Z：替换预览，选中斗篷237，旧槽64的头巾将归玩家；列出其他信仰统治者的夺回CB及四名实际角色各−20好感、10年。**仅为预览**，下方缩放加成被裁切，不能当实际替换、净好感后态或完整收益表。
- 麦加地产原窗口确实出现，但typed后读失败；没有取得建筑census／Construct条件通过资格。核心信条悬停也未取得正文。

只在明确准备的D2实验执行原准备A一次；没有执行B的d_sunni转移／强制刷新，没有Confirm、推进日期或新存档。A包含c_kent授予、17750虔诚、100000奉献经验、按需已知基督教综摄、条件管理关系与debug flags；不能只披露“补了虔诚”，也不能称自然长局或最优教改方案。最终独立读回：暂停、date51394920、piety20000、actor15893、Faith50、Religion19、currentRite13／mainRite13。

两条原片：`V6/captures/d2-original-gui-batch02-a01/raw-gameplay.mkv`，88,516,740B／`11099991ddd327ce890ec8a002ef87cc85428ad71ea7bbcdbcc703320c831fdd`，120秒／1536帧；a02同名原片14,339,633B／`5cbcde8491a3e0a1bf926aa1f330fa19b1b3b15691ba6045643f4d7136e423a8`，18.633秒／217帧。均2560×1440、VFR、单video。原recorder退出0，严格解码及全帧PTS各检查一次通过。`V6/runtime/r25-raw-qa-a01/DELIVERY.json`、`CLOSED.json`保留来源及结论；不等于整段人工审片，第二段不能按墙钟26秒使用。

### 已修原因：下一场要验证什么

完整研究见[冷载修正](../ck3-native-ai/faith-power-r25-cold-corrections12004-v6.md)。R25只读probe为112次／2040B、零写入／原生调用／输入，总体`bounded_read_failed`，并非完整反射链实机通过。ASLR TypeDescriptor的首qword是重定位值，后缀及其余pin仍精确；个人正常关闭新增现有tool内有限op208；几何+114只检查原函数实际消费位置。长函数pin按≤392B连续分段，避免截断520／480B方法。这些修复已进入707f／P15。

还发现旧manifest把 `saved_campaign_inject_after_load=true` 传到实际argv，走恢复后注入，绕过`PrepareStartup`，四个E8位置relay没有安装。**应复用现有pre-resume启动路径**，最终common中该字段为false，实际冻结argv不带`--saved-campaign-inject-after-load`。不需要新hook算法，不能热挂后伪称primary suspended。

R26的a03新common已明确设false并通过public prepare／plan／preflight，但用户停止前从未启动游戏。下一次真实冷载优先验证完整核心tooltip可见、个人窗口正常关闭并独立读回hidden，然后取建筑条件；fixture、窗口出现和ACK都不能替代这些实际结果。

## 剩余最小拍摄单

四种**礼仪核心信条**完整正文：基督教综摄主义、伊斯兰综摄主义、顺应、Adoptionism（本天主教例实际动态名称“继承说”；其他语境可能义子论／嗣子论，按窗口原名）。个人同名全文不能替代核心。用正常选择／预览保留实际禁用理由，不确认教改，也不为了拍顺应强改原版条件。

九个建筑、七处地产：定位为静态province，必须新场查询实际fullID和阶段。已建、候选、升级、禁用分别解说；无法合法出现时用真实对象搭配源码短注，不能放置或改名伪造。

| 地产province | 建筑及边界 |
| --- | --- |
| 6223 麦加 | 麦加大清真寺本体／启用收益 |
| 496 君士坦丁堡 | 圣索菲亚大教堂01，与阿亚索菲亚清真寺02候选／升级条件分别取 |
| 5965 耶路撒冷 | 圆顶清真寺，与第三圣殿候选／禁用原因分别取 |
| 1115 Tanjavur | 苾利诃地湿伐罗神庙；文化创新与宗教启用分开 |
| 482 雅典 | 当前Theotokos不冒充帕特农；帕特农只取合法候选 |
| 4796 泰西封 | 大王宫历史01与目标02身份分开 |
| 5728 Etchmiadzin | 瓦加尔沙帕特主教座堂实际建筑卡／空槽候选 |

定位全文 `V6/visual/NINE-BUILDING-CAPTURE-LOCATORS-a06.json`，12,417B，SHA `503c6cbafeb81cb0ab170b7187b307841f269c3de880129665bc89a8793fbf89`。SC28–36尚未完成这些正文。现工具`holding_building`读取已建GetTooltip，`holding_building_preview`是ShowDetails，**不是完整建造条件**；`holding_construct_conditions`悬停真正Construct.GetTooltip，禁用亦可观察。`cant_construct`警告图标原因未纳入本次最小实现，不为隐藏每个AND条件扩成全矩阵。

相关人物、司祭任务、朝圣目的地奖励提示可在现有原生入口方便时顺带取，不是新平台施工前提；不能拿圣地页替代朝圣奖励，也不必制造AI自然偷取、七种忙碌、净学识、满额9/3或新战争。

### D2后继准备和D1来源

D2原物化源 `V6/runtime/d2-successor-plan-a02/materialize_capture_a04.py`，19,908B，SHA `781eff81a29c67ade42b371171c620f8f45455b1573a051fd4e5327f91f81965`；仅有新unused路径与false模式等最小差异，SAFE42／required46、原F、saved-only、holder和A-only不变。**a03目录及allocation ledger已消费，不能重跑此源覆盖同路径**；为同一明确范围衍生新的未消费输出并保留原冻结事实。R26退出结论不能预填为正常GUI退出。

R26的CAS释放原收据仅证明资源已释放，不是旧公共入口要求的正常host／CK3退出前驱。最新master新增`tools/ck3_mod_acceptance_unrun.py`可消费从未启动的原件，R26尚未生成其完整bundle。接手先沿此现有入口补纯metadata前驱：原ready／frozen／prepared、idle STOP、allocator实际wait、keeper实际wait、CAS和admin done。`operations/batch03-allocate-a01/original-exit.json`166B只含原Popen wait事实，不能伪造为含argv的历史command-result；若该入口需要另一实际command-result，应从原operations调用记录定位并记录适配缺口，不制造normal exit或重新分配R26。这个前驱接线不需要启动游戏。

D1只完成来源绑定：`V6/root/d1-capture-binding-a03/DELIVERY.json`及`HANDOVER.zh.md`。总6,749B，writer0；P15资格、DLL、索引和Root审阅已填，五个场景／准入字段和release前驱仍null。尚无D1新profile、prepare、grant、allocator或画面。

D1母档 `EP/runtime/v5-crossreligion-d1-retry-a02/state/profile/save games/xar_checkpoint.ck3`，68,958,787B，SHA `62d18fe254d658356671269f194319a316729394da6f38b32da0d503bae1cd58`。预期actor31254、Faith13、Religion8、currentRite0／mainRite0、event=null、paused；**Rite0是合法ID，全部须当场重读**。该来源已真实恢复过，别为补图再造新世界。

旧D1薄producer继承`common-v6-original-gui-a01/manifest.json`的after-load=true；a03 binding仅声明false要求，**不会自动修producer**。接手者在现有metadata物化步骤显式写false并重新pin，再核实际argv；沿D2现有最小变更复用，不另建runner。D1仅取Islamic／Adaptive／Adoptionism核心全文及必要身份／个人对照，不Confirm、不采用、不推进、不保存。D2现场彻底释放后再按新D1准入运行。

## 研究与智能体已有落点

先消费这些已入库专题；不重做静态调查，不把脚本结论和自然AI调度、实机状态混为一谈。

| 玩家问题／规划输入 | 文档 |
| --- | --- |
| Faith参数、主流／当前礼仪、个人信条 | [faith-rite-parameter-scopes12004-v6](../ck3-native-ai/faith-rite-parameter-scopes12004-v6.md) |
| 有效稀有度的实际计算、认可和共享 | [holy-site-rarity-calculation12004-v4](../ck3-native-ai/holy-site-rarity-calculation12004-v4.md) |
| 跨宗教采用条件、方向、完整教改路线 | [cross-religion-adoption](../ck3-native-ai/holy-site-cross-religion-adoption-12004.md)、[planning-inputs](../ck3-native-ai/holy-site-adoption-planning-inputs-12004.md) |
| 特殊建筑的宗教／圣地／相容条件分类 | [special-building-gates](../ck3-native-ai/special-building-religion-holy-site-gates12004.md) |
| 主要等级收益、9／3上限及原版扩容路径核查 | [grade-effects-and-limits](../ck3-native-ai/holy-site-grade-effects-and-limits-12004.md) |
| AI清理决议主体、门槛及保护条件 | [relic-ai-cleanup](../ck3-native-ai/holy-site-relic-ai-cleanup-conditions12004-v5.md) |
| 替换圣物的具体好感对象／分支 | [relic-opinion](../ck3-native-ai/holy-site-relic-opinion-conditions12004-v5.md) |
| 最后退出时的实际圣物收件人 | [abandon-recipient](../ck3-native-ai/holy-site-abandon-relic-recipient12004-v5.md) |
| 建筑207与原版呈现MCP | [building-track207](../ck3-native-ai/faith-power-building-track207-v6.md)、[presentation-ui](../ck3-native-ai/faith-power-presentation-ui12004-v6.md) |

容量核查已深入原版脚本、原生登记、getter和写入链：49个Religion定义均不覆盖默认总数9／主要3，主要包含于总数；未找到原版可用的决议、事件或effect提高最大值。Religion定义可被mod覆盖属于另一层，省掉行动费用也不增加容量，见上述专题。主要等级升降、共享、供奉、更换、退还及采用成本亦已入研究／稿件。多信仰共享必须区分同一地理圣地、各Faith关系等级、圣物认可／贡献，以及角色实际受益，不能用“占用的网络”含混概括。

现有知识代码 `ck3_autonomous_player/src/xar_autoplayer/holy_site_v5_adoption_knowledge.py` 已更新R19／R22真实里程碑与三项现有公共工具，旧“不能教改／双向未实测”已归历史。不要再次应用外置旧补丁。后续只把新实际观察补进同一知识和文档，当前Can、部署与ActionReady须当场读回，历史成功不抵扣。

## 合成、正式编码和交付

顺序是：收齐实际GUI来源→更新一次来源／ROI／claim绑定→审所需实际像素及原片有效区间→正常metadata plan→内容ready→新容量准入→正式整片编码→完整听看片与局部修正→本地交付。保持135段和76,832帧，不以补图为由改变声钟。

现成正式路径 `formal_episode.py → FormalInputs.inspect → admit_v3 → full.build`，不要新建runner。`V6/root/final-render-plan-a01/PLAN.json`（23,796B，SHA `d19f778b8e19fb86a17f7c39fb8eaefe85d88f7d557b8eb66ec327dc3ec0059a`）及`V6/root/final-render-bindings-a01/CONSUME.zh.md`给出消费要求。拟输出`P6/full-final-a01`，**当前未建立、未编码，也没有正式render准入**。原拟峰值3,591,592,278B、两worker、120分钟lease，接手需当时重算，不自动继承。

`producer_source_snapshots`必须是`{file: <pin>, utf8: <exact source>}`的选定模块集合，旧四个普通pin不满足现consumer；不能拿旧pending绑定直接跑最终片。共享`full-runtime-a01.json`752B／SHA `7c542c039b0cad90f048d4952f0947d3aadf01290f31544142a3149b042d4141`只提供静态路径；正式启动时fresh_runtime一次，不反复预热依赖。

不另产每段MP4或额外WAV；同cue保留链所需一份prepared及一份narrated，最终原子替换。检查声音、双语字幕、安全区、画面中的预览／生效身份、每个例子的对象及转场，人工完整1倍速审片仍必须完成。交付本地最终视频、字幕、讲稿、章节／素材／来源索引及实际SHA，不把技术QA当作内容已合格。

## 现场与容量收口

**R26最终停止：** `4-8e1c2f1861--faith-and-power--R0026`／a27只有allocate，从未启动CK3、native session或录制。原allocator session82851实际Popen wait0（01:03:15.972006Z），keeper实际wait0，原600秒idle STOP回执保留；`normal_close_qualified=false`、business=false，没有可声称的CK3退出码。Root实审`L26/root-unused-allocation-stop-proof-a01.json`及`root-screen-release-a01.json`，CAS **11996** 于01:33:41.166092Z释放，resources=[]；最终admin done序号 **11997**，原件`L26/root-admin-done-a01.json`。原a03 prepared和allocation ledger已消费，下次使用新未消费路径，不回滚编号。所有拍摄／作者／研究／QA工作已停止，无自动恢复。

Root容量收口 `V6/root/VACATION-CAPACITY-CLOSED-a01.json`，观察`2026-10-19T01:39:14.780389+00:00`，3,643B／SHA `2ba9b4487bceeccf8669f11610b3fc2ba14e1b0a3cec558c3c369083a5661c30`：仅统计本次四个精确新根，201项metadata、0.817秒，未读原片内容或扫描旧根。R26保守保留 **7,098,368B**（含262,144B收口回执余量），future0；raw／QA均未启动。原2,153,775,104B预留一次换成实际保留；作者未消费2,703,360B也关闭后，项目保守上界 **45,574,373,887B**，低于51,177,672,294B配额。没有执行删除、没有把授权取消算作物理腾空。Root只剩本交接文档收尾，commit／push后关闭自身协调任务。

存储只用[通用策略](../storage-retention-policy.md)，没有其他盘／外接／网络存储这一用户事实未改变。2026-10-19T01:28:58.312185Z以`shutil.disk_usage`观察卷511,776,722,944B、free115,752,644,608B；这是瞬时卷余量，不是某阶段回收量。本项目quota51,177,672,294B，安全余量21,474,836,480B、系统增长6,442,450,944B，其他任务未消费预留保守按整份quota计，不擅自当0。

作者32MiB阶段保守分配上界30,851,072B，future0；未消费2,703,360B停止授予未来写入，旧租约2026-10-19T01:27:32.448447Z到期，不自动续。P15原1GiB准入已按真实保留19,129,973B闭账，不再挂未来1GiB。R25准入也已按570,839,752B闭账；合并P15后、R26前项目上界45,569,978,879B，详见各Root容量回执。当前docs/source16MiB阶段沿`V6/root/DOCS-ADMISSION-a02.json`，仅收尾小文档，既有租约02:38:45Z到期；保守保留完整16MiB上界，不宣称整树物理精确释放，不授权以后媒体扩张。

当前必要输入与未解决RED有用途明确的限期保护，已登记复核不晚于2026-10-26；接手须查具体原记录，不因本文重新计时或自动续7天。可重建派生默认48小时，构建／checkpoint14天、raw30天；先查当前用途和[用户永久保留索引](../maintenance/user-permanent-assets.json)，不能到点整树删。

唯一已辨认可评估提前回收的作者旧派生是 `O/metadata-plan-a03/formal-metadata-plan.json`，3,936,665B，SHA `4b5edbde7d13eb58c0ad67c3f266051cfe9a4b82e25d36cdf4c58cbf984b4565`；已被S当前plan替代。**尚未删除**。若确需空间，解析精确根、核pin及当前无引用，单文件删除并留小清单说明旧派生已不可读取。不能删除O/current-a01旧作者输入、RED日志、S当前输入、原片、母档或样板；不为交接额外清理。

前期用户授权的两版魔戒、冰与火及UUII／大萌三过期验收清理已经完成并有独立读回；保护／防重现与实际边界见[本机清理记录](../maintenance/storage-reclaim-2026-10-17-machine-4-8e1c2f1861.md)。旧原件已deleted，不能要求同事再次读取或重复算回收。本文不扩展到其他机器、个人文件或其他任务新资产。

## 接手后照这个顺序推进

1. 读本文及系列方法，核本机身份、任务总线和现有owner；承认原租约结束，重新安排有限空间。先确认没有旧现场，复用P15来源策略，别先重编／重配声轨。
2. 同时铺开作者缺图整理、已有raw有效区间审阅、研究／知识查漏；游戏仅一个操作者，其他工作保持并行。恢复D2新未消费路径，沿公共prepare／plan／preflight／allocate／run，先fresh离线／实际argv，再做最小GUI验证与取材。
3. D2闭场回执真实完成后恢复D1母档，只补剩下核心正文。原片／截图单次收图并交作者；不重演已有世界动作。若遇同一已知拒绝，停止重复请求，按实际新原因补最小现有能力。
4. 合入实际来源、看必要新构图像素、选raw区间，完成正常metadata输入；以玩家理解、条件完整、具体对象及节奏审全稿和画面，不能以count或空binding数替代。
5. 新准入后正式编码及完整人审，交付本地文件；把本轮新经验、原生实测与智能体增量实时写回docs，正常commit→fetch→rebase→push。每次闭场释放资源，按实际结果报告进度与重估时间。

本交接完成后原执行者不自动恢复拍摄；后续由接手同事按上述恢复点继续。
