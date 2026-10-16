# Episode 04 R184：客户区录像正常封装与自然日轮询误判

`machine_id: desktop-3fevhd2-1c74096080`；run `desktop-3fevhd2-1c74096080--vanilla--R0184`。2026-10-16 本场取得 **22.766 秒／683 帧**的正常封装客户区录像，完整音视频解码 exit0、无诊断，随后正常保存、原版 UI 退出 exit0并释放屏幕。该结果修复了 R183 的截断采集问题，但没有新的业务正例或连续 clean 认证；研究仍 **6/14（42.9%）**，业务 **4/11（36.4%）**，合格动态 **0/11**。

跨机器可复用的摘要与46份精确小原件见 [R184证据索引](evidence/episode04-r0184-20261016/source-index.json)及[便携事实](evidence/episode04-r0184-20261016/portable-facts.actual.json)。包中只带一份完整闭场 snapshot；其余完整快照、原片、截图、存档、Defender大回执及sdk-ready均未复制，已有回执保留精确外置pin。**这是选择性便携记录，不是完整场次离线重放包**；其他机器必须重核安装、离线、权限、容量与实机资格。

## 来源、身份与当场准入

运行及native源均为 `163530f1bbcabe5a97854625b3fab7568006ee65`。12:07:26 UTC 的 [a27生产资格](evidence/episode04-r0184-20261016/A27-PRODUCTION-QUALIFIED.actual-a01.json)绑定实际 CK3 `1.20.0.4`／Steam build25734779，EXE 101,040,248 bytes，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`；本场 DLL 12,982,784 bytes，SHA `372ed8dc1c1881b8bea75415cafd4e696aacb90690f30a15f0a555ca91234d4e`。该回执保留injector/host及实际SYSTEM设置出处，不把权限推至其他机器。源commit中canonical bootstrap、recorder与deadline模块的精确Git字节、SHA及CRC32见索引 `runtime_git_source_pins`，不以以后工作树字节解释旧场。

[allocator](evidence/episode04-r0184-20261016/ALLOCATION.actual-a01.json)于12:07:26 UTC分配R0184；[prepare实际命令](evidence/episode04-r0184-20261016/ROOT-PREPARE-a02.actual.json)指定 `--display-mode windowed --expected-game-version 1.20.0.4`，[prepared](evidence/episode04-r0184-20261016/prepared.json)读回目标版本与空mod纯原版合同。本场独立冷载R182普通checkpoint，73,446,058 bytes、SHA `af291da7e2af3b8b0870dc3aa21291b55452a78e08a241994ba6358411c7c96b`；不是R183终态，也不是新的1066开局或ABC T0。

12:20:37 UTC的[离线审阅](evidence/episode04-r0184-20261016/steam-offline-reviewed.actual-a01.json)直接读到同一原图中新nonce与Steam离线文字；shell时钟仍停滞，不声称桌面已全面恢复。12:28:45 UTC的[运行身份](evidence/episode04-r0184-20261016/runtime-actor-identity.actual-a01.json)与[guard PASS](evidence/episode04-r0184-20261016/identity-guard.actual.json)绑定PID3504、创建FILETIME `134366269232060188`、connection generation1、episode `native-31254-3d3fad411eb2`、实际actor31254、初始date53147928。罗贝尔来源链与正常存档字面值保留；没有解码历史ID1128到运行时31254的直接字段，不能形成跨场数值映射。

11:39:06 UTC的[新容量准入](evidence/episode04-r0184-20261016/CAPACITY.actual-root-a01.json)是独立复核，**没有续用R183的07:45旧额度**；新复核期限17:39:06.531146 UTC，scene上限1,610,612,736 bytes，raw上限536,870,912 bytes。[开拍前检查](evidence/episode04-r0184-20261016/preflight.actual.json)记录本scene剩余1,049,074,811 bytes；当时C卷free29,970,321,408、required29,629,254,164，D卷free48,300,224,512、required21,609,054,208。以上容量仅属于该机器、卷和观察时点。

## 实际采集机制与文件完整性

本场走仓库canonical recorder，source为 **`gdigrab-desktop-client-region`**：2560×1440桌面中，已核验CK3客户区屏幕矩形 **`[640,360,1920,1080]`**，输出 **1280×720**；HWND `101517432`，前台HWND相同，初始遮挡列表空。命令使用 `-offset_x 640 -offset_y 360 -video_size 1280x720 -i desktop`。它采集客户区所在屏幕区域，**不是独立HWND渲染像素，也没有采集整张桌面**。窗口移动、缩放或遮挡仍须守卫观测；`capture_guard_error=null`只能证明本场采样守卫没有报告错误，不能证明每帧都经过人工检查。

[spawn期限检查](evidence/episode04-r0184-20261016/raw.deadline-admission-at-spawn.json)同时绑定5400秒会话总期限（13:50:52 UTC）和新容量期限，要求90秒计划录制加180秒正常闭场余量；当时约3608.54秒可用，admitted=true。[ready](evidence/episode04-r0184-20261016/raw.process-ready.json)报告12:50:41.669433 UTC，首次resume ACK衔接3.2150411秒。后因逐日辅助器误判而提前finish，实际没有录满计划90秒。

| 证据层 | 本场实际结果 |
| --- | --- |
| recorder结束 | 12:51:07.474944 UTC，`NORMAL_TREE_EMPTY`，FFmpeg PID22212、returncode0、job active0、error null |
| 原片身份 | `raw-window-a01/raw.mkv`，11,904,058 bytes；SHA-256 `6d1704561753f74adc689fe1c2a3be391b1e15063e3b7c83d06476d3ea605f19` |
| 媒体 | H.264／yuv420p／1280×720／30fps，683帧，单视频流、无音轨 |
| 实际时长 | 容器22.766秒；首PTS0、末PTS22.733秒、末帧结束22.766秒；时间戳缺失0、逆行0 |
| 完整解码 | 所有实际音视频流解码exit0，stderr空，`premature_end_reported=false`；属于正常提前封装，不是R183式截断partial |
| 质量/业务 | clean、完整人工观看、human signoff及business_positive全部false |

直接来源是 [raw结果](evidence/episode04-r0184-20261016/raw.result.json)及13:00 UTC的[媒体审计](evidence/episode04-r0184-20261016/media.audit.actual.json)。抽取单张PNG的image2文件名提示仍保留在审计中，它不同于全片decode诊断；不能泛称所有抽帧命令stderr也为空。

对既有原尺寸抽帧的[独立离线直接审阅](evidence/episode04-r0184-20261016/three-still-offline-review.actual.json)看到首帧0秒为1067-02-12、中帧请求11.3665秒为1067-02-15、末帧请求22.733秒为1067-02-21；三个单帧均可见CK3地图、军队与军事面板，没有Windows边框、周边桌面或Steam。Root另于13:24:17 UTC逐张按原始尺寸复核，并保存[直接审阅及日期勘误](evidence/episode04-r0184-20261016/root-three-frame-review.actual-a01.json)，纠正早期多图预览将中/尾日期误读为12/15的文字。它们不证明每个中间日期都入片、首次像素变化时点或整段无冻结。原audit中的 `visually_reviewed=false` 保持原字节，其后审阅另记，不能回写历史审计。

## 八份完成回执、d09误判与闭场日期

[film-result](evidence/episode04-r0184-20261016/film-result.actual.json)为 `completed_days=8`，八份逐日完成回执从53147928依次推进至 **53148120**，每份sentinel为1 tick、overshoot0、pause已观测；Army18仍在2635围城、route empty，无本场新的行军或抵达。结果同时保留 `early pause without modal` 错误，不能写成九次辅助器调用全部成功。

[离线原件分析](evidence/episode04-r0184-20261016/early-pause.ACTUAL-EVIDENCE.json)确认d09是假early-stop分类：d08最终12:51:05.839548 UTC为date53148120、paused、native27/public28；d09 Resume12:51:06.361471 UTC仅证明accepted/submitted。首poll仍同日paused，但已native28/public29，旧逻辑的三字段全相等等待条件失败并中止；紧随的cleanup snapshot12:51:06.708965 UTC已同日running、native29/public30。**native与public revision都前进**，不能简化为“只是public revision变了”；具体哪个字段促发native28仍未查明。

[候选回归](evidence/episode04-r0184-20261016/early-pause.REGRESSION.actual.json)复现旧误判，候选逻辑可等待真实running、后续日期或modal并保留有限80-poll、once-Resume和finalizer。它仅为离线实际trace回归，`new_live_validation=false`，不授权重投旧R184动作，也不追认第九份完成回执。

12:57:47 UTC的[正常保存](evidence/episode04-r0184-20261016/NORMAL-SAVE.actual.json)日期已是 **53148144**，checkpoint73,664,718 bytes、SHA `fe0ef524ec71a77f830faf1cce1d46167790799796f006eb5335a3637836f2b8`；[保存响应](evidence/episode04-r0184-20261016/close-save-once.response.json)与唯一入库的[闭场后snapshot](evidence/episode04-r0184-20261016/close-after-snapshot.response.json)分别保留。这是后续真实保存日期，不能覆盖“八份完成回执”的原事实或新增第九次exact-day资格；三张抽帧日期也不能替代逐日native完成合同。

## 正常闭场与复用边界

[bootstrap结果](evidence/episode04-r0184-20261016/bootstrap-result.json)记录13:03:25 UTC `exit_reason=process_exit`、游戏exit0、cleanup_proven、最终游戏进程清单空，SDK/keeper已退出；自有recorder为NORMAL_TREE_EMPTY、guard线程结束且无cleanup错误。本场与R183的外置recorder所有权不同，不能继续套用R183顶层NOT_STARTED解释。[屏幕释放](evidence/episode04-r0184-20261016/SCREEN-RELEASE.actual.json)13:07:47 UTC实际exit0，sequence5763、done、resources[]。该回执明确 `capacity_reservation_returned=false`，屏幕释放不自动证明容量台账已返还；后续存储闭场由Root另行记录。

智能体可复用三项方法：按真实客户区与进程身份采集；把recorder正常封装、完整decode、单帧审阅、连续clean及业务结果分层；Resume后用日期/运行态/modal与有界轮询判断后验，不能只用一次新revision的paused帧结束流程。视频下游必须绑定这条raw的精确SHA和实际帧时码，审完连续范围后才能选clip。当前只闭合采集技术事实，不授围城扣兵、补员、补给或付款正例，不制造人工签核。

来源根 `C:/ck3-e04-resume-20261015-a01/live12004-r184-window-capture-a01/`、分析根 `C:/ck3-e04-resume-20261015-a01/r184-early-pause-analysis-a01/` 均为来源机器定位；原件可读性及期限仍按[统一存储策略](../storage-retention-policy.md)复核。精简包不续期配额、不保护整scene、不宣称已上传到其他机器。
