# 《CK3：信仰引擎》第二期 V7 休假交接

本记录对应用户“温和地收尾手上的每件事，然后编写交接文档到docs”的实际闭场：停止拍摄、研究和制作，正常关闭 R0036、释放现场并停止全部八个子线程。**V7 没有成片；最后可播放交付仍是用户已提出修改意见的 V6 黄色版。** 接手时先解决容量与新场次准入，再补核心镜头，不能把作者候选、卡图或软件通过写成新版视频完成。

**随后用户取消休假，要求继续任务。** R0036 的正常退出及无半程存档已实际发生，保留本记录，不重新解释旧场次；Root已恢复后继容量与新场次准备。下文“全部completed／future0”等为20:41:59Z闭场截点，不代表恢复工作后永远没有新任务。后继进度见[用户反馈制作记录](../../promo/ck3_faith_and_power/episode02/docs/review-v6-feedback-2026-10-22.md)。

本文事实所属机器为 **`machine_id: 4-8e1c2f1861`**；现场闭场观察截至 **2026-10-22T20:41:59Z／北京时间2026-10-23 04:41:59**。`tools/ck3_live_run_id.py machine` 本轮实际返回相同 ID。安装、Steam、磁盘与实机事实不外推到其他机器。小型精确索引见[本次交接证据](../ck3-native-ai/evidence/faith-engine-episode02-v7-vacation-handover-20261023.json)。前次交接保留为[10月22日 V6 历史截点](2026-10-22-faith-engine-episode02-v6-vacation-handover.md)。

## 1. 接手先看这些

- 工作包根目录，下文简称 **R**：`C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261022-a01`。
- R0036 live，下文简称 **L**：`R/live/4-8e1c2f1861--faith-engine--R0036`。
- [R0036 完整闭场](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261022-a01/FILMING-R0036-VACATION-CLOSURE.actual.json)：实际业务截点与退出证明。
- [最终存储闭场](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261022-a01/storage-preparation/VACATION-STORAGE-FINAL.actual.json)：预留已释放，旧准入不能再消费。
- [V7 作者候选总入口](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261022-a01/v7-authoring-preparation-a01/V7.REVIEW-INDEX.candidate.json)：卡图、声音、字幕、时钟、缺镜与生产输入的唯一候选入口。
- [镜头→旁白区间提案](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261022-a01/traits-observation-checks/V7-SHOT-CUE-INSERTION-PROPOSAL.actual.json)：七条 cue、八段 take 上限及十四处长卡插入点，均区分现有与待拍。
- [用户反馈及机制勘误](../../promo/ck3_faith_and_power/episode02/docs/review-v6-feedback-2026-10-22.md)：V6 逐段时间码、补镜理由和原版来源。

最后可播放文件为 [V6 黄色完整审阅 MP4](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/yellow-revision-a01/sample/build-a01/native-run/derived/direct/episode02-review.mp4)，24:30.067、2560×1440、30 fps。它仍有本轮用户指出的内容问题；未被新卡图覆盖，未取得内容签收。机器交付偏好仍为[本地交付](../maintenance/machine-preferences/4-8e1c2f1861.video-delivery.json)，未上传 OneDrive 或视频平台。

## 2. 现场已经怎样关闭

R0036 冻结源码为 **`036600913ea7d735ceed15fafa6d457ae0fa0892`**，CK3 PID `6996`，创建 FILETIME `134371720336365726`。本场实际版本 `1.20.0.4`，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；来源是本场原生快照和退出前原始画面，不冒充新一次 Steam 安装校验。

| 事项 | 实际终态与时间（UTC） | 证据 |
| --- | --- | --- |
| 活动 | 用户要求休假，Root 拒绝继续关键镜头 checkpoint；业务为 `PARTIAL_ROOT_CAPTURE_CHECKPOINT_REJECTED` | `L/case-output/ordinary-pilgrimage-result.json` |
| 自动存档 | 原生取消 `should_save`，Root 直接看过原始未勾选画面；没有退出存档 | `R/screenshots-a04/04-normal-quit-unchecked.jpg`、`root-r0036-vacation-exit-disable-after` |
| 游戏退出 | 原版 GUI 回调依次打开菜单、继续、取消存档、退出桌面；每个提交一次。保留句柄实际 wait0／exit0，20:39:08.721137 | `R/commands/root-r0036-vacation-normal-exit-observer.actual.json` |
| Native 与 host | native 进程退出0、树清理已证；host 20:39:47.519765 结束，`cleanup_ok=true`、无 host error | `L/case-output/normal-close-result.json` |
| 公共 run | 原 Popen 实际 exit0，19:46:54.868115→20:39:48.788666；`business_pass=false` | `R/commands/run-a07.exit.json` |
| 显示 | 20:39:55.475893 实际恢复 1024×768、32 bpp、60 Hz，设置与读回均成功 | `R/DISPLAY-RESTORE-R0036.actual.json` |
| keeper／录制服务 | 合作式 STOP；两线程实际退出，failure／entry_error 均为空，完成 takes 为空 | `R/keepers/a04/report.json` |
| allocator | 原 Popen 实际 exit0，20:40:11.958098 | `R/commands/allocate-a07.exit.json` |
| 屏幕 | exact-CAS **13388→13389**，task 已 done、resources 空，20:40:32.694137 | `R/SCREEN-RELEASE-a06.actual.json` |
| Steam | 后台原生新回执 `status=offline`、`offline_mode=true`，20:40:23.996328；未激活窗口或截图查询 Steam | `R/STEAM-OFFLINE-FINAL-R0036.actual.json` |

原 `prepare_confirmation`／`continue_preparation` 曾先返回 `dispatch_unknown_claimed`，随后独立 query 才看到下一层；没有重复提交。最终 confirm 的 ACK 也没有被当作退出，保留句柄观察确认后才闭场。`normal_close_qualified=true` 只说明退出合格。

最终扫描未见全机 CK3，未见命令行包含本 R 的其他进程；原退出码另由保留句柄及原调用等待证明。八个子线程 `hajj_relationship`、`icon_inventory`、`pilgrim_bonuses`、`v7_filming_entry`、`v7_native_binding`、`v7_runtime_qualification`、`v7_source_preparation`、`v7_storage_preflight` 全部 completed，无自有后台 writer／测试／监测。未接管或修改其他任务的历史总线记录。

## 3. R0036 实际拍到了哪里

母档仍为 `episode01/scenario/saves/A-hanafi-prepared.ck3`，50,214,831 B，SHA `8cadd902d3360995ecfb1541013a72b80408ff041e25b9627592553e2cf9f662`。角色 `15893`，初始日期 raw `51394920`，Faith 50／Rite 13；只准备过额外 2000 虔诚，不能计作普通战役成绩。起初没有朝圣者、朝觐者、宗教学者、神秘主义者。

本场只提交一次 Start；独立读回主办活动 `activity_id=0`（合法零值）、host15893、`activity_pilgrimage`、尚未完成。实际最终报价 182 金币、钱包同日 1398→1216，仅证明活动报价和首次扣款，不是旅程总成本。

自然推进最终 **224 个游戏日**，raw `51400296`，对应最后一份 `faith-e02-journey-001-day-0139.json`。文件序号 139 是请求序号，不能当作游戏天数。到达实例 **10／`pilgrimage.3101`**，显示两个选项：native0“我会全心全意、至诚至敬地完成受戒仪式。”、native1“呃……貌似没人会清楚我有没有掉链子吧。”。Root 未选择，先留下小型原始画面，再按用户休假指令返回 aborted。

**未完成受戒或后续仪式，未观察授予朝觐者／朝圣者，未返乡、未双特质共存，没有新的旅程存档。** 本场未遇到 R0035 的 `pilgrimage.2002`，所以不能宣称该事件的实机修复已验证。

本轮新增 **3 张游戏原图、0 条 raw take**，另有 1 张退出证据图：

| 文件 | 实际用途 | SHA-256 |
| --- | --- | --- |
| `R/screenshots-a04/01-hajj-stage1.png`，4,579,184 B | 首次朝觐类型：朝觐可选，普通虔诚／世俗受限；Root 直接看过 | `d6ae6f6456d7f844582c4c82166929d0862ff73c7facbbe19379a4c3a056cecf` |
| `R/screenshots-a04/02-hajj-final-quote.png`，5,447,118 B | 当前麦加6223、182金、CanStart；Root 直接看过 | `5113b89c83a71aeb830c1a0bbbe87751021124cf25fca42b8550e7e5f71de8c6` |
| `R/screenshots-a04/03-arrival-before-vacation-stop.jpg`，594,359 B | 收场前受戒窗口原始桌面 JPEG，无缩放；不是仪式完成图。Root 未另作图像内容审看 | `9deb3539e5ccbd9cb275237d6e7ae863b644cc4e077ff1800abc62b6a20ef9aa` |
| `R/screenshots-a04/04-normal-quit-unchecked.jpg`，232,357 B | 退出前未勾选存档，Root 已直接审看 | `4995c7b314f5c05e18f4b5a2c46e6c9cd54e90984098e07a653e720a11b661a4` |

七个已选择事件实例3–9都有 ACK 与独立旧窗消失；四份离线知识 JSON 共25,848 B，存于 `R/event-analysis-r0036/`。3／4／5／8复用已有分析，6／7／9补充 `travel_danger.1007`、`pilgrimage.2060`、`intent.1050`。水源事件实际显示索引2、3，第一显示项为native2，不能硬编码native0；NPC结果、25年经验修正／神秘经验等未读字段仍未知。`registry_analysis_available=true` 与 unavailable 原因并存的生产字段问题已记录，未热改现场。实例10只保留输入与中止，没有伪造选择后态。

## 4. 已完成的制作与机制研究

### 图卡

**45 张嵌原版 DDS 的替换卡＋3 张补充机制卡＝48 张新卡**；另10张旧纯算术卡仅引用。当前55张基础卡映射与3张 SUP 映射分别在 `R/derived/material_card_candidates/dds-only-a01/REPLACEMENTS.V7-DDS.a02.actual.json`、`SUPPLEMENTS.V7.a02.actual.json`，[闭场索引](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261022-a01/derived/material_card_candidates/dds-only-a01/CLOSURE.actual.json)绑定来源。

特质、信条、文化、技能、旅行选项等正式对象现有相应原版素材；图集按 GUI 格位、星级和比例取材，保留原色。系列继续暖棕／金黄色，字幕区1140–1440留白，文字下限28。物理目录52张 PNG 含4张已被替代的 pilot，不能称52张有效新卡。Root 有限审看18个物理文件／14张所选逻辑卡，并非48张全部人工审阅；图卡没有进入新的完整视频。

### 应讲清的关系和收益

下表是限定1.20.0.4的来源规则；本轮 R0036 不提供结果实测信用。原始调用、行号、动态条件见[反馈第4–5节及第7节勘误](../../promo/ck3_faith_and_power/episode02/docs/review-v6-feedback-2026-10-22.md)和 `R/hajj-cooldown-source-followup/COOLDOWN-AND-ORDER.json`。

| 问题 | 已确认规则／视频必须修订的内容 |
| --- | --- |
| 朝觐者能否变成朝圣者 | 二者独立，没有自动转换。普通首次抵达授予 pilgrim；首次朝觐目的地阶段完成授予 hajjaj，时间早于返乡。 |
| 什么情况下共存 | 朝觐者→合法普通朝圣，普通授予不删朝觐者；已有朝圣者→合法首次朝觐也可另获朝觐者。后者仍缺本轮实拍。 |
| Hajj 与既有 Pilgrim XP | 结算按表现向既有、未满级 pilgrim 请求5／10／20／40基础XP；没有 pilgrim 时不能靠经验请求生成它。hajjaj 自身无朝圣者经验轨道。 |
| 类型解锁与冷却 | 强制朝觐礼仪先核 hajjaj 身份；其它 CanPlan／资源／冷却仍另核。朝觐一年记忆在目的地完成后的 on_complete 建立，五年检查针对同一圣地；不能据此要求普通朝圣必等一年或认定通用冷却为0。 |
| 不是所有朝觐者都实际走过旅程 | 开局／设计器持有麦加且满足礼仪可直接发特质；运行时月度补发另查麦加首都。不能见标签就反推旅程。 |
| 朝圣者学识 | 当前礼仪 `basic_pilgrimage_rewards` 条件下，XP不足50／50至不足100／100累计学识 **0／+1／+3**；V6漏讲。 |
| 文化额外属性 | 战斗祭司／僧兵的相应文化参数给朝圣者累计勇武 **+2／+5／+8**，朝觐者同参数为+2；不是所有文化默认享有。 |
| 诺斯替主义动态链 | **个人信条**具备参数，活人、三天冷却及获得触发满足时，获得 pilgrim 会处理宗教学者／神秘主义者：缺失则授予，已有则各请求10基础XP。两个本体各学识+1，满足资格可合计+2；宗教学者还核最低16岁等定义。不是每次升级触发，也不是朝觐者触发。 |
| 美德与其它文化 | 宗徒大事录／使徒行实／热忱传教的条件显示信条可把朝圣者列美德，weight15不是15经验／属性。当前宗教融合传统没有已查的这类朝圣者附加属性，不能外推其他版本。 |

名称统一为 **宗教学者**、**诺斯替主义**。旧文“经文研习者”已勘误；Root 曾在中间口头称“灵知主义”，该口头名称也不采用。等级名分支中的 `has_trait_xp value=20` 缺省比较语义未查明，撤回“恰好20”的推断。跨 Religion 改宗会在通用链删除 pilgrim，不走改宗保留 pilgrim 的捷径证明反向共存。随从与异常缺 `limit` 的重复抵达XP分支仍须独立核对。

### 声音、字幕与作者输入

N06／N07／N25／N29／N30／N31／N32 **七条新声音已实际生成，总语音242.760秒**；其余26条复用旧声音，保留 N02／N15 已修订版本。实际声线 XiaoxiaoNeural、rate−5%。原七次单流 provider 调用最终 exit2（N07／N25编辑单元划分不匹配）原样保留；随后只离线重划单元，复用原音频和实际 SentenceBoundary，7／7时钟可消费，没有重试 provider。probe／完整解码通过，人工听音仍待完成。[实际交付](C:/workspace/ck3-faith-and-power-20261017/episode02/v7-filming-20261022-a01/tts-seven-cue-production-a01/OFFLINE-CLOCK-DELIVERY.actual.json)。

作者候选14文件约0.98MB，Project／mechanism／subtitle／clock／FormalInputs.inspect 实际通过；**`content_ready=false`，七条新 cue 仍缺相应实机视觉**。1369.600秒／22:49.6含80秒阅读停顿，是候选时钟；最终PTS为空。206是视觉引用次数，现有仅4条不同旧MKV共20秒，不能说206条实机。没有新编码、全片AV／PTS检查或人工1×审阅。

七 cue／八 take 上限提案预计最多约145.9秒新动态，但该数是计划。N06可先用当前类型原图；N13的R0034星空事件图不能证明XP到账；N25反向“先 pilgrim→再Hajj”须单独实证或清楚标来源规则。当前GUI叠层只支持PNG／JPEG，不支持WEBP；旧WEBP证据不能直接冒充可输入的叠层。不要为了剪辑热改冻结执行图。

## 5. 共享软件已经交付到主线的部分

本场使用的源码提交 **036600913** 已普通推送到 master，含真实 fixture 外部对象来源／链接支持修复及持久CI回归。其前身临时提交d6426231e经rebase继任；旧证据不改身份。实际源码树、运行包和本次文档提交是不同身份，后续文档提交不把本场重新标为新源码实机。

| 范围 | 实际验证 | 原件 |
| --- | --- | --- |
| 同流TTS维护 | 完整115测试、0跳过；六模块strict及两文件普通检查通过，维护提交5a5c0254a | 本轮历史制作器回执；不是7条声音人工审听 |
| 原生日程及公共case | 旧完整162测试、0跳过；旧类型债保持 | 原公共case回执，不改称新一轮162 |
| 新 retained fixture 来源／链接支持 | 完整持久CI step：producer21＋builder56＋link28＝**105测试、0跳过**，producer与其完整测试strict通过 | `R/source-checks/native-link-support-a01/COMPLETE-STEP.a02.actual.json` |
| 公共runtime消费缝 | ExactTree9＋SameRootHost16＝**25测试、0跳过**；四个文件完整静态检查及第五文件修改定义strict通过 | `R/source-checks/fixture-link-consumer-v2-a04/CHECKS.actual.json` |
| Native构建 | 实际27次CL、DLL链接、归档成功；后继四fixture实际compile／link／EXE均0，14 wire packets保留 | `R/source-checks/native-fixture-resume-a01/RESUME-EXECUTION.actual.json` |
| 原生事件消费者 | 43 Python＋CTest1＋新增SDK消费及静态检查实际0，范围见原回执 | `R/source-checks/event-saved-scope-consumers-a05/CONSUMERS.actual.json` |
| 新Q→公共runtime→部署 | metadata seal、独立qualify、公共build-runtime均0；CLI及SDK两个独立 `-I` 进程分别0，约16.50s／21.75s | `R/runtime-preparation-a05/RUNTIME-READY.actual.json` |

旧 builder 全模块严格检查仍314条诊断（原342、实际修改消除28、新增0）；局部strict不能写整模块全绿。旧719项验证保留其原来源／时间，不追认本次重跑。最早a01 v1错误文字漂移导致RED，实际修复后a02才通过，原RED未覆盖。

Native源码为DD5树，当前036中的相关Native树未变。原a05首次某fixture链接原等待未知，保留未知EXE／FileID，不冒充当时wait0；后继有限四fixture实际0，不重编全部27单元。并非从空树重新执行完整Native CI。

新可用Q为 `R/native-build-a05/native-a01/fixture_link_support_a01/PUBLIC-RUNTIME-QUALIFICATION.actual.json`，5,810 B，SHA `0c61730fec1e6ad37d1d898e1df50ff16c8e6d18d148b9885ff4e61ea49c3a91`。旧5,490 B Q保持原样。新增共享 `--seal-fixture-links LABEL` 只重封 metadata，不重新编译链接；255对象绑定中254借用原b21保留物，须核真实源码、compile index、实际RSP／OUT及原PLAN／INCREMENTAL／依赖。**普通 fresh Producer.seal/run 仍会先生成缺v2支持的Q；同类借用场景还须执行共享metadata-seal步骤，并非所有新构建已自动一键闭合。**

当前 runtime `R/runtime-hajj-a04/runtime.local.json`，13,188 B，SHA `2f306391a8baa52857132a798c7ad8bd253d6631d7adfd89d0cb93832ad5195c`；manifest67,872 B，SHA `3710c76479d8e114570e8de5c08849f8b2f543bb9915e203fa219d88a6e24f30`。七来源链到最终八链、833文件原生表、冻结a12来源均实际消费。两独立消费者无Java／Living实际依赖。录制overlay为 `R/runtime-recording-a05/runtime.with-recording.json`，只改变allocation.recording；限4×25秒／每段32MiB／总100秒128MiB，实际未使用。`normal_quit_automation` 在JSON中**缺失**，不要补成null。

官方 exact036 CI：Linear run39841661134 SUCCESS；Official runner39841661259 **FAILURE**，第40步Java bootstrap的Surefire临时文件 `NoSuchFileException`（CiBootstrap343）导致终止，后续Native42／43、pilgrimage45、shared111均 **SKIPPED**。不能用本地105／25／两个独立消费0称官方全绿；未在本轮拍摄／休假收场中接管Java修复。精确终态见 `R/runtime-preparation-a05/OFFICIAL-CI-036600913ea7.actual.json`。

R0035 `dummy_gender` 已保存角色缺identity的共享读取／序列化修复保留root、结构、高位守卫，使用既有 `character_scope_identity_unavailable`，没有伪造ID0。本轮新DLL已实际加载；**R0036未遇2002，所以这条事件业务复验仍未完成。**

## 6. 容量红灯、预留释放与保留期限

统一执行[通用策略1.0.0](../storage-retention-policy.md)及[版本化参数](../storage-retention-policy.json)。a05原始G `R/ADMISSION.scene-a05.actual.json`（SHA `4a3333383a7017760801f54e367108dbe856d66a8c2fe7569837db7d9e903ca9`）不修改；其历史expiry为2026-10-23T01:00Z。旧H rev5 SHA `d63f41c036807cda3046181e1123338ccb085b8ce14b71132e1976efbaae8393`已由正常闭场继任，不能再给新消费者沿用旧active字段。

最终本机协调头 `C:/workspace/.codex-task-bus/storage/volume-C-current.json` 由现有 `storage_short_commit.prepare/publish` 在本地writer协调中 **rev5→6**，状态closed、未消费预留为0。全扫描／哈希／容量观察都在全局锁外；锁内仅精确metadata CAS／原子改名，实际锁约0.001秒。没有新grant、提高配额或删除文件；旧G保持不可变，实际已占盘内容继续计占用。

| 20:41:59Z最终观察 | bytes |
| --- | ---: |
| R逻辑文件总量 | 1,159,997,881 |
| R文件／目录4KiB上界＋1MiB闭场尾量 | 1,229,869,056 |
| 卷实际空闲 | 90,248,720,384 |
| 本项目使用上界／有效配额 | 64,750,484,959／65,000,000,000 |
| 如继续完整旧预留的future／projected | 481,406,976／65,231,891,935（RED） |

20:29:19.355230Z监测实际exit2：当时物理缺61,738,598 B、projected超228,565,983 B；20:30／20:31／20:33独立复核仍RED。此前15秒卷free下降236,101,632 B而R只增1,478,656 B，R外增长的具体来源未知，未越权扫描或清理其他任务。固定935,352,720 B旧回收加回与external deletion credit0保持，不能再领删除收益。另有更早一次泛化RED的确切UTC未知，旧outer0曾掩盖内层失败，保留原缺口，后来的PASS不覆盖它。

手工cap1632MiB、退出trigger1568MiB从未自动执行，不得写“自动存储守卫已部署”。whole-report采用完整临时文件＋fsync＋replace，必须预算旧新报告共存峰值。实测完整窗口预测1,828,830,320 B超cap117,554,288 B；420／720天方案也有触发／容量问题，不能复用“首32天通过”作为全程资格。Root只采纳过下一个关键窗口或900秒阶段，后被RED和休假指令终止，不得继续沿它推进。

保留与下一次复核：

- 当前48张所选卡、7新声音与真实时钟、作者候选及直接依赖、必要Native/runtime来源输入，owner `/root`，用于未完成V7的后继制作，限期保护到 **2026-10-29T20:41:59Z**，无自动续期；先重核预算和用途再继续。
- 构建／checkpoint默认14天，raw原始日志／图像默认30天，小结180天复核；派生物默认48小时。不是整棵R都加7日保护，巨型对象仍应7日内评估。
- R0035唯一诊断主档 `R/hajj-prepared-a04/state/profile/save games/xar_checkpoint.ck3`，SHA `6024141f06da4361e995e58384efcca08b6181479632df32fe2d0864ea34198b`，既有保护至10月29日，未提前删除。原SDK `unconfirmed/save_binding_mismatch`保持；该档不是当前R0036结果或合格半程续档。
- 新产生的5个pyc共207,116 B保留，原因是分析线程未使用`-B`；它们不是236MB卷下降来源。最终存储回执字段`known_five_pyc`实际列了6项，其中`prepare_storage_candidate.cpython-314.pyc`为更早20,017 B旧文件；这是字段命名／集合勘误，详见机读交接。扫描返回的FileID／link_count零值不构成原生文件身份，未据此执行删除。
- 前面已经按精确清单回收两份R0035重复存档、五张旧图、旧失败构建／configure树、闭场profile副本与129个旧章节MP4。旧操作表已逐字节验证后无损gzip，现有可用性以 `R/storage-preparation/OPERATION-LISTS-GZIP-AVAILABILITY.actual.json`、`THREE-EXACT-RETIREMENTS-POST.actual.json` 为准。不可再读的原件不能制造同名替代品；旧蓝色MP4已在先前精确回收中不存在，V6黄色保留。
- 两个离场pilot MP4只有只读候选清单，**未删除**：`R/storage-preparation/OFFSCENE-V6-TWO-PILOT-REVIEWS.readonly-candidate.json`。本次休假闭场没有再执行回收。

## 7. 下一位执行者的具体顺序

1. 用户恢复工作后，先读本交接、最新主线AGENTS及机器偏好。核机器／实际版本／磁盘和统一台账；R0036已闭场，a05已释放，不重新启用旧G/H或原请求。核必要原件可读与SHA，重新评估到期／保护。解决全程容量、whole-report双份峰值和新的正式制作预留，再开新场。
2. 尽可能复用已通过的Native／fixture／wire资格和当前runtime，按新source／实际文件身份重新绑定公共入口。只因文档HEAD变化不重编Native全矩阵；真实依赖变化才做对应检查。若借用对象重新封包，执行已有共享metadata-seal步骤，不篡改旧Q。
3. 按 `tools/ck3_mod_acceptance.py plan / prepare / allocate / preflight / run / verify` 公共路线建立独立新profile／Prepared／冻结分配，逐步消费实际退出码。启动前fresh后台Steam offline，旧蓝色决策窗继续退役，不能由OCR／鼠标替代原生事件选项。不要把R0035诊断或未保存的R0036当作已获资格的接续输入。
4. 核心仍从合格母档完成：首次类型限制→麦加报价与Start→抵达受戒→连续仪式→真正hajjaj授予／7000结算→返乡及合格Save。`3101→3010(+20日)→3020(+15)→3030(+15)→3040(+15)→3001(+10)→阶段1周on_end授予→7000` 是来源顺序，不是本轮实测；9001返乡另记。录真实窗口变化，不能用当前静帧冒充这些take。
5. 再执行H06：同一已返乡人物的普通朝圣解锁、合法目的地、首次pilgrim授予并保留hajjaj。`R/h06-successor-preparation-a01/H06-LAUNCH-RECIPE.R0036.pending.json`只是**pending配方**，缺R0036返乡Save所以不能直接执行。4828才是巴格达，当前adapter只是prefer并可能fallback；Root要在实际destination checkpoint核4828。CanPlan／通用冷却现场查询，不能盲等一／五年。
6. 属性镜头B01（三级学识／文化勇武）与B02（个人诺斯替信条获得链）仍待实拍。`R/gnostic-filming-preparation/B02-EXISTING-ENTRY-ADDENDUM.md`明确当前没有现成Gnostic prepare命令，不能捏造入口／预授特质。现Native没有特质hover口，当前可用角色特质栏与字段；新能力如确实阻断交付，按共享能力与最新版Java迁移边界施工，不再建attempt专用Python生产模块。未拍到的规则用带原版图标的清楚规则图示。
7. 复用已经完成的48卡／7新声／26旧声，按七cue提案补真实画面；核一期R25旧图内容、可读性与来源后剪裁。开始新的工具链任务／run前查询独立仓库最新正式GitHub Release，验证wheel／解释器／help；本次0.3.0及wheel SHA `f59c4b62b89297e2ff7bb7df4354fc88c6447fa6b1b7eade28de2bc1e6dc974c`只重现本次，不能固定当作未来最新。
8. 新run单worker正式制作；旧129章节文件已回收，不能直接concat缺失文件。完成真实输入绑定后才能把content_ready改为true；按实际新声／片段重算时钟、字幕、阅读停顿，编码后检查AV、PTS、全片可读性与人工听音／1×审阅。最后提供本机实际MP4路径，不自动制造用户签收或平台发布。

本轮中间约60%的百分比只是工作估计，不是交付验收；闭场时没有继续运行中的进度或承诺完成时间。用户随后要求继续，下一轮先报容量、新场实际启动与第一个核心结果的节点，再根据真实推进速度给条件预计，避免把首32天或请求数量外推全程耗时。
