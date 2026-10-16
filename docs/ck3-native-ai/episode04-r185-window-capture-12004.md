# Episode 04 R185：十二日完成、可见人数变化与80秒录制未达标

`machine_id: desktop-3fevhd2-1c74096080`；run `desktop-3fevhd2-1c74096080--vanilla--R0185`，2026-10-16 UTC。本场完成 **12个自然日，date53148144→53148432**；取得 **46.466秒／1394帧**正常封装原片，完整音视频解码exit0、诊断为空，正常保存并退出。但完成逐日推进后，维持录像的hold阶段因新容量检查失败停止，**没有满足80秒最低录制要求，也没有录满120秒计划上限**。

三张原图中，Army18面板显示人数从1184变为1173，期间显示1%损耗图标、补给300/300。这是可见数值变化，未绑定物理DATA扣减与同次writer，不能直接归因为围城、县损耗或饥饿，也**不新增R03正例**。business、clean、完整人工观看及human signoff均false；研究仍 **6/14（42.9%）**、业务 **4/11（36.4%）**、合格动态 **0/11**。

入口为[原始便携事实](evidence/episode04-r0185-20261016/portable-facts.actual-a01.json)、[分层消费边界](evidence/episode04-r0185-20261016/decision-boundaries.actual.json)及[52份精确原件索引](evidence/episode04-r0185-20261016/source-index.json)。仅选择一份完整闭场snapshot入库，原片、PNG、存档、fullDefender、sdk-ready及其余完整身份/时钟响应仍在外置来源中；这不是完整可移植closure replay。其他机器复用方法与代码后仍须重新核验其安装、权限、离线、容量与实机。

## 精确来源与本场身份

runtime/native源均为 **`c743520929d4f9a82c17c908b218075018598e2d`**。14:19:30 UTC的[a28生产资格](evidence/episode04-r0185-20261016/A28-PRODUCTION-QUALIFIED.actual-a01.json)绑定同源构建、已运行fixture及实际SYSTEM权限出处；不复制大Defender回执。CK3为 `1.20.0.4`／Steam build25734779，EXE101,040,248 bytes、SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本场DLL12,994,560 bytes、SHA `48855df0fcdefe3152ce1d4518a4d642405ba49c6f98edb07438b7e45f11135a`；injector及host精确pin随资格回执保存。canonical bootstrap/recorder/deadline在此commit的Git字节SHA与CRC32见索引，不以未来改码解释旧场。

[allocator](evidence/episode04-r0185-20261016/ALLOCATION.actual-a01.json)、[prepare](evidence/episode04-r0185-20261016/prepared.json)和[film input](evidence/episode04-r0185-20261016/film-input.actual-a01.json)绑定独立R0185。本场从R184正常checkpoint接续：73,664,718 bytes、SHA `fe0ef524ec71a77f830faf1cce1d46167790799796f006eb5335a3637836f2b8`，起始date53148144；不是新的1066开局或ABC共同T0。

14:21:52 UTC的[离线审阅](evidence/episode04-r0185-20261016/steam-offline-reviewed.actual-a01.json)直接审阅两个不同新nonce与同图Steam离线文字；shell时钟仍停滞，没有宣称全面恢复。14:29:47 UTC的[运行身份](evidence/episode04-r0185-20261016/runtime-actor-identity.actual-a01.json)与[guard](evidence/episode04-r0185-20261016/identity-guard.actual.json)绑定PID23776、创建FILETIME `134366341994175597`、generation1、episode `native-31254-1b048f683ec8`、实际actor31254。罗贝尔来源链保留，历史1128到运行时31254的直接字段仍未解码，不能泛化角色数值ID。

13:52:31 UTC的[独立容量准入](evidence/episode04-r0185-20261016/CAPACITY.actual-root-a01.json)设scene上限1,811,939,328 bytes、raw上限536,870,912 bytes，复核期限19:16:40.776628 UTC；`old_admission_transferred=false`。14:37:03 UTC的[preflight](evidence/episode04-r0185-20261016/preflight.actual.json)读到scene剩余1,261,624,633 bytes，C卷free30,554,697,728／required29,841,803,986，D卷free53,925,978,112／required21,609,054,208。这些是具体机器和时点的读数，不是后续hold永远可写的保证。

## 12日推进与最低媒体时长分开结算

[film-result](evidence/episode04-r0185-20261016/film-result.actual.json)同时记录 `completed_days=12`、`stopped_reason=planned_days_complete` 与后续错误 `fresh volume budget no longer covers preflight reservation`。12份完成回执及其已绑定的native status证明每次+24、1个daily tick、overshoot0、pause已观测；首日完成14:39:26.669197 UTC，末日完成14:39:49.328236 UTC，最终date53148432。Army18各回执均在2635、sieging、route empty，非交战/撤退；这些不等于实际人数完整查询或扣兵归因。

recorder ready→第一次resume ACK为 **3.272059秒**。配置的12日先完成；随后为达到80秒最低wall时长继续hold时，新容量检查拒绝扩大写入，流程进入正常finish。recorder wall时间 **49.653296秒**，编码内容 **46.466秒**，两种时长均未达80秒。错误只保留其实际范围，不能据后来空闲增加推导当刻检查其实通过；本记录不猜测失败当刻未留明细的卷差值，也不降低旧required门槛。

[后续媒体审计容量](evidence/episode04-r0185-20261016/MEDIA-AUDIT-FRESH-CAPACITY.actual-a01.json)和原便携事实中的 `closure_capacity.current_all_fit=true` 是稍后的独立读回：C余量3,328,455,982 bytes、D余量32,316,919,808 bytes，未降低阈值、未跨卷抵扣、未续期限、未宣称释放预留。它只准入了相应审计工作，**不追认80秒hold已完成**。

## 客户区录像与原片完整性

本场canonical recorder取 `gdigrab-desktop-client-region`：桌面2560×1440，CK3客户区屏幕矩形 **`[640,360,1920,1080]`**，输出1280×720；HWND34408890与前台相同，初始遮挡列表空。命令通过 `-offset_x 640 -offset_y 360 -video_size 1280x720 -i desktop` 获取客户区所在屏幕区域，**不是独立HWND渲染捕获，也没有录入整张桌面**。`capture_guard_error=null`证明采样守卫没有报告错误，不能代替每帧人工遮挡检查。

| 媒体事实 | 实际读回 |
| --- | --- |
| 原片 | `raw-window-a01/raw.mkv`，27,208,789 bytes；SHA **`b15dac9e149903f116af4b16a917aba679633088f5d3be6fb477b995f49ff7b9`** |
| 视频 | H.264、1280×720、30fps，1394帧，无音轨 |
| 时间轴 | 容器46.466秒；首PTS0、末PTS46.433秒、末帧结束46.466秒；缺失/倒退时间戳均0 |
| 正常封装 | `NORMAL_TREE_EMPTY`、recorder exit0、job active0；完整AV解码exit0、诊断空，`premature_end_reported=false` |
| 最低时长 | requested80秒；wall49.653296秒及编码46.466秒，均false，不是80秒或120秒成片素材 |

来源为[canonical结果](evidence/episode04-r0185-20261016/raw.result.json)、[媒体audit](evidence/episode04-r0185-20261016/media.audit.actual.json)、[逐帧PTS原输出](evidence/episode04-r0185-20261016/media.frames.stdout)和[完整解码命令](evidence/episode04-r0185-20261016/media.full-av-decode.command.json)。全片decode无诊断与单PNG抽取的image2文件名提示分别保留，不泛称每个辅助命令stderr都为空。

14:53:10 UTC的[Root三帧原尺寸审阅](evidence/episode04-r0185-20261016/root-three-frame-review.actual-a01.json)按各自原图直接读取：

| 抽帧请求PTS | 可见日期 | Army18面板人数 | 同帧显示 |
| --- | --- | --- | --- |
| 0秒 | 1067-02-21 | 1184 | paused、1%图标、300/300 |
| 23.2165秒 | 1067-03-01 | 1173 | paused、1%图标、300/300 |
| 46.433秒 | 1067-03-05 | 1173 | paused、1%图标、300/300 |

三帧没有观察到外来窗口或周边桌面；显示人数净变−11。此观察不证明所有中间帧、精确扣兵时点、physical DATA映射、损耗writer或补给状态因果。审计保留原来的 `direct_visual_review_performed_by_this_worker=false`，Root后续审阅单独附据；它不是全片1×或连续clean签核。

## 正常闭场与下游决策

14:44:19 UTC的[正常保存](evidence/episode04-r0185-20261016/NORMAL-SAVE.actual.json)固定date53148432、checkpoint73,864,691 bytes、SHA `500ed157a401f22e8ee5433a84b6fb24850f357a964e4474c7b8af4ce67335ff`；[原保存响应](evidence/episode04-r0185-20261016/close-save-once.response.json)及[独立后snapshot](evidence/episode04-r0185-20261016/close-after-snapshot.response.json)可核对。[bootstrap](evidence/episode04-r0185-20261016/bootstrap-result.json)14:45:29 UTC正常process_exit0，cleanup proven、终态游戏进程清单空，SDK/keeper/recorder闭场。[屏幕释放](evidence/episode04-r0185-20261016/SCREEN-RELEASE.actual.json)14:45:58 UTC实际exit0，seq5784、done、resources[]；其中 `capacity_reservation_returned=false`，容量台账返还仍须Root另行记录，不能由屏幕释放代替。

可复用的方法是分别结算**推进合同、最低录制时长、文件完整性、画面可见事实、业务因果及签核**：12日成功不抹去hold失败；hold失败不抹去已有正常可解码原片；显示人数变化也不自动升级为物理扣兵机制正例。下一步视频可以审查这条精确raw的连续候选范围，智能体开发则继续消费同实例writer与物理前后读数。当前不重跑已完成12日以制造媒体成功，不借样本帧或既有R03来源补发资格。

外置根 `C:/ck3-e04-resume-20261015-a01/live12004-r185-window-capture-a01/` 仅定位来源机器。原portable facts为26,093 bytes、SHA `650fec110e4aeb89256e0c2c0fd0a7b0dbd4c011849313caef904e55bb0afaa7`；Root审阅SHA `62513c134701dd4ef2027f92f3a5cb2b05b4625ea50c988c62f92fc764bd7ef0`。本包不复制大原件、不续期配额或保护；原件可读性与时效仍按[统一存储策略](../storage-retention-policy.md)复核。
