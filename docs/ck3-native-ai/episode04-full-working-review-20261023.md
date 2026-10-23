# 第四集完整工作审阅片：实际交付与来源

最新交付为[棕黄风格与实机主画面重剪a02](episode04-visual-recut-20261023.md)，OneDrive文件`CK3-Episode04-Full-Working-Review-20261023-a02.mp4`。下文a01保留历史生产与验收事实。

machine_id: `desktop-3fevhd2-1c74096080`。Root于2026-10-22T22:30:49.939851Z确认完整`FullWorkingReview`已可供用户审阅；[实际交付回执](evidence/episode04-full-working-review-20261023/ROOT-DELIVERY.actual.json)绑定产物、校验、来源及闭场。这是包含片头和片尾的完整工作片，`human1x=false`、`user_signoff=false`；正式动态机制主题仍为10/11，R05实机因果证据仍缺。

## 实际产物与同步

文件：`C:/Users/1/OneDrive/CK3-War-AI-20260923/CK3-Episode04-Full-Working-Review-20261023-a01.mp4`。

| 字段 | 实际结果 |
| --- | --- |
| bytes | 95584711 |
| SHA-256 | `65bc255463b3ba863c189973bc4b6ad0296df61d70a1472a06da16442f5798eb` |
| 画面与帧数 | 1920×1080，30fps，50138帧 |
| 时长 | `50138/30`秒，即27:51.266667 |
| 结构 | 62cue：品牌8秒、罗贝尔动态开场20.4秒、六个章节开场、47段新编码机制正文、完整结尾 |

这些帧数已由[整片实际解码](evidence/episode04-full-working-review-20261023/FINAL-FULL-DECODE.actual.json)和[全包时钟检查](evidence/episode04-full-working-review-20261023/FINAL-PACKET-CLOCK.actual.json)确认：视频PTS0、50138个精确帧PTS与单调DTS通过；音频78342包，1024采样时钟通过，尾样本80220800精确对齐。[全音轨统计](evidence/episode04-full-working-review-20261023/FINAL-AUDIO-STATISTICS.actual.json)未见采样削顶；连续音乐床与各段人声沿最终配方混合。

最终[原始outer wait](evidence/episode04-full-working-review-20261023/ROOT-OUTER-WAIT.actual-a05.json)为0；PID18560、FILETIME字符串`134371812453103542`，原tool session83833退出0。[owner闭场](evidence/episode04-full-working-review-20261023/FINAL-OWNER-CLOSED.actual.json)记录68个原始子进程wait0/Job0、剩余owned Popen为0。Root核对62个实际切点图的SHA，并直接抽审两张全片contact、罗贝尔动态开场、结尾及R05/R08特殊图；这不增加人工1×或用户签收信用。`C01-01`为罗贝尔动态开场，47个机制段使用`N`编号。

2026-10-22T22:29:07.707548Z的[OneDrive客户端回执](evidence/episode04-full-working-review-20261023/ROOT-ONEDRIVE-CLIENT-SYNC.actual-a02.json)确认`in_sync_state=1`，`on_disk=validated=95584711`、`modified=0`，FILEID十进制字符串`562949956005471`，本地完整SHA与交付文件一致。它证明当前客户端同步状态，独立远端下载SHA仍为null。22:25的[媒体metadata](evidence/episode04-full-working-review-20261023/ACTUAL-MEDIA-METADATA.json)中`PENDING_CLIENT_READBACK`保留原字节，后继a02同步回执补充之后的事实；没有改写旧回执。首次[a01探测原输出](evidence/episode04-full-working-review-20261023/ONEDRIVE-CLIENT-FAILED-PROBE.actual-a01.txt)的`placeholder_hresult=0x80070178`也保留，不作为同步成功或当前64位身份依据。

## 两阶段来源及最小参考档

[来源清单](evidence/episode04-full-working-review-20261023/SOURCE-MANIFEST.json)保全两个不同阶段的资格记录：[a04冻结](evidence/episode04-full-working-review-20261023/A04-SOURCE-FREEZE.actual.json)40534B/SHA `544ef2e779aca46a822a7c9268ad523597f61689dcb7e8ee47b4c84f998841db`负责实际62cue编码；[a05冻结](evidence/episode04-full-working-review-20261023/A05-SOURCE-FREEZE.actual.json)41690B/SHA `69afc78e329bd6438cf22e73c5b72687bb4e5cd2704288db13862b6ea666ffef`只读取已闭场的全部62cue，采用精确48K整数采样时钟重新生成整片、QA及交付副本，本次cue重编码为0。47段机制的新编码来自a04，未退回旧黄色47段产物。两代Root独立来源审记录分别保留；来源冻结不是未来执行准入卡。

| 参考档 | 内容与检查 |
| --- | --- |
| [a04参考档](evidence/episode04-full-working-review-20261023/a04-reference-sources.tar.xz) | 16件、原始311790B、归档59528B，SHA `e03791fa02cda7fd621074e9fef61ec383fd756c08ca64b03faa5212aac248dc`；6个冻结源、2个窄字段合同、4个片头来源JSON、唯一当前62cue配方及3份原检查记录。全解码、16成员SHA、8 AST/8 JSON通过。 |
| [a05差分档](evidence/episode04-full-working-review-20261023/a05-finalizer-delta.tar.xz) | 5件、原始26029B、归档8540B，SHA `9bdb522aeb96a1e53c1c7fb84c412e43e6c1814ab1fde902700abc73f20f2fdd`；4文件统一patch、完整finalizer及3份原检查记录。对a04的`working/`树实际check/apply双0，4目标字节数/SHA重建匹配，4 AST/4 JSON通过。 |

这些归档是不可变历史来源参考，没有新增生产模块或接入仓库runtime/CI。a05未重复未变的3份源及近同164868B展开配方；两档也不重复[首包19份来源](episode04-r0241-r0243-and-core47-source-20261023.md)。103项媒体实体、视频、62张QA图、完整协议CSV、第三方依赖和前代执行树均未抄入Git；[证据清单](evidence/episode04-full-working-review-20261023/DELIVERY-EVIDENCE-MANIFEST.json)保留原路径、大小及SHA。这里只验证归档和字节往返，没有重跑历史业务或全仓矩阵。

## 失败历史与能力边界

a03完成四cue后，[实际失败](evidence/episode04-full-working-review-20261023/A03-FAILED-PRESERVED.actual.json)为整片精确视频PTS覆盖/单调DTS检查失败；后继同源a04的[1182帧小clock实际接受](evidence/episode04-full-working-review-20261023/ROOT-CLOCK-ACCEPTANCE.actual.json)只属于小诊断。a04再完成全部62cue，50138帧视频检查通过，但[实际失败](evidence/episode04-full-working-review-20261023/A04-FAILED-PRESERVED.actual.json)为音轨连续PTS门禁。Root的[完整CSV分析小回执](evidence/episode04-full-working-review-20261023/ROOT-A04-AUDIO-FAILURE.actual.json)绑定原3096775B CSV：19个包PTS比期望少1采样，duration有19对1023/1025，按实际duration无空隙、尾80220800精确；原strict1024仍失败，原outer1、139个孩子wait0/Job0、未写OneDrive。浮点算术根因当时仅为候选；a05改整数采样时钟后实际全包1024通过，不改写前代失败。

R05在本片为规则说明：自然stock<10的入场值、同次callback到正向物理扣兵的连续因果证据及正常实机闭场仍未取得。新R05准备仅`static-ready`，新Game/SDK/Film/RunID/Savecopy均0，不因本片生成而授业务资格。R08仅证明同次净结算中军费分量抵扣后净加1.11391金币；不授独立扣款、付款人或完整周期资格。详细金额及R0242/R0243失败/修复见[首包事实入口](episode04-r0241-r0243-and-core47-source-20261023.md)。

## 首包CI与时效

首包精确`06d3102baa5f8f56c9973da24f7f833a8d1011a0`的Linear39853399164成功，[Official39853398947](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39853398947)最终失败。job120085223604的step40在`CiBootstrap.java:346`收到`NoSuchFileException`，缺少`packaged-source-…/classes/org/xar/ck3/control/contracts`。既有`ProjectionDeploymentProofTest.java:197`生成该临时路径，源码blob在首包父提交与06d一致，首包18个修改均为docs；具体临时目录生命周期根因未确认。[最窄错误与归因](evidence/episode04-full-working-review-20261023/FIRST-SOURCE-CI-ATTRIBUTION.actual.json)、[日志来源/精确64KiB区间](evidence/episode04-full-working-review-20261023/FIRST-SOURCE-CI-LOG-RANGE.actual.json)及[Hosted身份说明](evidence/episode04-full-working-review-20261023/FIRST-SOURCE-CI-RUNNER-IDENTITY.actual.json)保留；未下载整套日志。Desktop机器ID属于观察者，Hosted runner的machine_id为unknown。后继上游已修改CiBootstrap/ControlBuild及测试，新交付HEAD的CI另据实际终态，不能从旧失败推断已修或仍失败。

依[通用存储策略](../storage-retention-policy.md)，下一用途复核为2026-10-24T10:00Z，必要活跃输入保护至2026-10-29T10:00Z。复核时核当前用途、引用、替代证据及容量；不无限保留全旧树，不以本页授权删除用户交付文件。原始媒体和日志的外置路径不构成跨机器资格。

## 2026-10-23可用性补注：被取代的本地派生媒体已回收

machine_id仍为`desktop-3fevhd2-1c74096080`。用户实际审阅后要求调整部分新增包装的棕黄底色，并提高实机主画面占比；新重剪的实际交付结果另记。上文生产与验收回执保留当时事实，但其中部分外置媒体路径已不可读取，不能据历史Pin推断文件仍存在。

2026-10-22T23:45:28.557556Z的[第一批实际回收](evidence/episode04-visual-recut-20261023/MEDIA64-ACTUAL-RECOVERY.actual.json)按独立精确计划删除64组、128个原名，Native回收281460736B；范围包括a04的62cue及两份本地whole，两whole只计一次。Root的[具体执行范围接受](evidence/episode04-visual-recut-20261023/ROOT-MEDIA64-ACCEPTANCE.actual.json)绑定61034B精确计划及原SHA；本包保留计划Pin，不重复逐名大清单。

2026-10-23T00:14:53.384353Z，另一份[实际回收回执](evidence/episode04-visual-recut-20261023/READONLY48-ACTUAL-RECOVERY.actual.json)确认readonly48清单中的48文件已删除、48原名均缺席，Native回收145133568B，203份保留来源前后完整SHA匹配；[Root实际核验](evidence/episode04-visual-recut-20261023/ROOT-READONLY48-VERIFICATION.actual.json)另存。先前“readonly48未删除”只属于更早截点。两批scope不重叠，实际Native回收合计426594304B，`unknown_stop`均为null，未改写为0。

这些旧本地原名现已不可读，没有制造同名替代证据，也没有删除未列资产或整目录。两份旧OneDrive交付（完整工作片及黄色机制审核片）、raw、voice、recipe、源码与必要小证据继续保留；两份用户交付的当前身份、大小与完整SHA在回收前后匹配。已入库来源档仍可读取；原媒体回执与清单只证明其历史产物身份，不能冒充仍可消费的旧本地cue/whole输入。后续素材用途、容量和限期保护继续按通用策略重新判断。
