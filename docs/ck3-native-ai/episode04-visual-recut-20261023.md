# 第四集棕黄风格与实机主画面重剪：实际交付

machine_id: `desktop-3fevhd2-1c74096080`。2026-10-23T01:13:31.183284Z，Root确认重剪版已可供审阅，[最终交付回执](evidence/episode04-visual-recut-20261023/ROOT-DELIVERY.actual.json)绑定实际媒体、来源、QA与客户端同步。用户指出的部分新增包装未沿用棕黄系列底色、卡片占比过高，已在本版调整。`human1x=false`、`user_signoff=false`，正式动态主题仍为10/11；R05实机未验收。

## 本次实际变化与产物

14份新增包装统一为棕黄系列：背景`#211813`、金色`#CBA56A`，品牌片头、六章、边框、字幕区和片尾一致；原生游戏UI像素不染色。保留原47段旁白与50138帧总时长，62cue均实际新编码，含品牌8秒、罗贝尔动态开场20.4秒、六章及完整结尾。`C01-01`是罗贝尔动态开场，47个机制段采用`N`编号。

最新文件：`C:/Users/1/OneDrive/CK3-War-AI-20260923/CK3-Episode04-Full-Working-Review-20261023-a02.mp4`。

| 字段 | 实际结果 |
| --- | --- |
| bytes | 171754888 |
| SHA-256 | `071ea89c78ccd9ecb8894a3e118737295e4c467ed35515395a5b324792331de3` |
| 画面与时长 | 1920×1080，30fps，50138帧，27:51.266667 |
| 实机主画面 | 38030帧，21:07.666667，占75.85065220%；旧版19.06737405% |
| 卡片主画面 | 12108帧，占24.14934780% |

[Root实际时间线核验](evidence/episode04-visual-recut-20261023/ROOT-ACTUAL-TIMELINE-VERIFICATION.actual.json)独立核对全部62段的编码原wait0、完整解码帧数及47段机制新编码。这里的占比按实机主视窗帧数计算，包含真实暂停UI和跨cue复看。20份原片的源区间并集为30132帧（16:44.4），另7898帧为跨cue复用，占实机视窗约20.77%；同cue内无源区间重叠。75.85%不表示新录制、连续动作密度或独立原片比例。普通规则卡最长12秒，R05明确例外为827帧（27.566667秒）。

## 实际校验与审阅范围

[整片完整解码](evidence/episode04-visual-recut-20261023/FINAL-FULL-DECODE.actual.json)读回50138视频帧，H.264 limited BT.709、48kHz双声道AAC；[全包时钟](evidence/episode04-visual-recut-20261023/FINAL-PACKET-CLOCK.actual.json)确认50138个精确视频PTS、单调DTS、音频连续PTS和80220800尾采样。[完整音轨统计](evidence/episode04-visual-recut-20261023/FINAL-AUDIO-STATISTICS.actual.json)未见采样削顶。原始[Root outer wait](evidence/episode04-visual-recut-20261023/ROOT-OUTER-WAIT.actual.json)为0，PID34528、FILETIME十进制字符串`134371882366051718`；339个原始子进程wait0/Job0的外置owner闭场Pin由最终回执保全。

独立[视觉观察](evidence/episode04-visual-recut-20261023/FINAL-VISUAL-OBSERVATIONS.actual.json)直接查看19张contact，共194个有限样本：全片62切点与新增源区间首/中/尾132样本。样本未见硬性黑帧、旧青色全屏海报、旧蓝决策面板、明显编辑文字碰撞或原生UI遮挡；contact末尾未使用的深色格子是拼图留白。Root另亲看[首轮9幅全尺寸preview](evidence/episode04-visual-recut-20261023/ROOT-PREVIEW-ACCEPTANCE.actual.json)、R05/R08、两张全片contact及R194/R215/R199 contact，并直接查看R194/R215中段全尺寸帧。

相似意大利地图、法国/诺曼底广角复看与暂停UI仍存在。有限contact不能证明全时长节奏、完整字幕可读性、动作密度或连续游戏推进；本轮没有完整人工1倍速听看片或用户签收。原生背景也不能为其上旁白的数值示例增加业务证明。

## 本地身份与客户端同步

2026-10-23T01:10:37.829004Z，[Root同句柄Native核验](evidence/episode04-visual-recut-20261023/ROOT-LOCAL-DELIVERY-VERIFICATION.actual.json)分别锁定本地whole/CAS及独立OneDrive副本，完整SHA一致；OneDrive FileID为十进制字符串`562949956014693`、links1。01:11:13.597998Z的[客户端同步读回](evidence/episode04-visual-recut-20261023/ROOT-ONEDRIVE-CLIENT-SYNC.actual.json)为`in_sync_state=1`、`on_disk=validated=171754888`、`modified=0`，身份与mtime均先规范为十进制字符串。本地完整SHA和客户端状态已核验，独立远端下载SHA未观察。

01:03的[原始metadata](evidence/episode04-visual-recut-20261023/ACTUAL-MEDIA-METADATA.json)仍保留`PENDING_CLIENT_READBACK`；后继同步回执追加之后的事实。01:06首探测的`0x80070178`及wrapper缺少`file_id`触发KeyError历史保留在同步回执内，未作为成功证据或当前身份依据。

## 最小来源差分与可用性

实际生产使用[a03来源冻结](evidence/episode04-visual-recut-20261023/SOURCE-FREEZE.actual-a03.json)，50350B/SHA `d9b0f4758e265c87d017e243f9b77f79a3ad52468754eb48151225395169cce3`；[Root来源审核](evidence/episode04-visual-recut-20261023/ROOT-SOURCE-REVIEW.actual-a02.json)独立核7源与13输入。a02末审发现PNG缺少显式30fps，尚未启动媒体；a03窄修`-framerate 30`及消费者检查后，原focused9组/strict7文件均wait0。旧a02只属历史候选，不追认为实际媒体来源。

[来源清单](evidence/episode04-visual-recut-20261023/SOURCE-MANIFEST.json)说明重建依赖与原始Pin：[重剪差分档](evidence/episode04-visual-recut-20261023/recut-source-delta.tar.xz)29772B、8成员，SHA `b538aca1068fcb42059daff48b80c1ab115511f447b51459a8ac006d73849fb1`。它基于已入库a04参考档和a05差分档，仅增加5文件LF patch、两文件原CRLF恢复合同、两个新源、强类型v2镜头表及原检查记录；未复制旧未变源或236244B展开配方。[本次归档验证](evidence/episode04-visual-recut-20261023/SOURCE-DELTA-VALIDATION.actual-a03.json)实际check/apply双0，5个目标原字节SHA全部匹配，7 AST/5 JSON通过。

另保留[4180B Native回收参考档](evidence/episode04-visual-recut-20261023/exact-recovery-native-reference.tar.xz)，仅含本次task-local窄修入口、原strict及真实双link哨兵回执，依赖见来源清单。两档合计33952B，均为历史来源参考，未新增仓库生产模块、runtime导入或自动回收部署；未来执行仍须新的用途、精确身份和容量准入。未把cue/whole、194图、完整CSV或完整执行树抄入Git；[交付证据清单](evidence/episode04-visual-recut-20261023/DELIVERY-EVIDENCE-MANIFEST.json)保留大记录的外置Pin。

旧a04全62cue及两份本地whole、另一批readonly48派生文件已实际回收，合计Native426594304B；[旧入口可用性补注](episode04-full-working-review-20261023.md#2026-10-23可用性补注被取代的本地派生媒体已回收)保留两批实际回执和原名不可读事实。两份旧OneDrive交付、raw、voice、recipe、源码和必要小证据继续保留。历史SHA不证明已回收原件仍存在。

## 业务边界与下一步

本轮没有新增Game/SDK/Film/RunID，序号仍243。R05只为规则说明，`R05_actual_acceptance=null`、`R05_business_qualified=false`；自然stock<10、同次callback至正向物理扣兵的连续实机因果链仍缺。R08仍只授同次净结算军费分量抵扣的有限事实，不授独立扣款、付款人或完整周期。正式动态主题10/11保持，`formal_final47_release_acceptance=false`。

下一步是用户实际审阅及完整人工1倍速听看片，不能用媒体自动QA替代。按[通用存储策略](../storage-retention-policy.md)，下次用途复核2026-10-24T10:00Z，必要活跃输入保护至2026-10-29T10:00Z；不无限保留全旧树，也不由本页授权删除用户交付文件。
