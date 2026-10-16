# Episode 04 R183：窗口化录制、截断原片与三次自然日回执

`machine_id: desktop-3fevhd2-1c74096080`；场次 `desktop-3fevhd2-1c74096080--vanilla--R0183`。本文归纳 2026-10-16 已落盘事实，供视频制作与智能体开发共同使用。可移植原始回执在 [evidence/episode04-r0183-20261016](evidence/episode04-r0183-20261016/README.md)；该包不含原片、截图、存档或游戏源码。其他机器可以复用结论与合同，不能据此认定其安装、桌面、权限、容量或录制也已通过。

本场确认了**窗口化 CK3 的客户区能通过屏幕区域采集得到游戏画面**，但未完成计划录像。保留原片只有 **239 帧，实际可用帧末端 7.966 秒**，属于截止中止留下的 partial。没有新的业务正样本、连续 clean span、人工完整观看或成片签核；研究口径保持 **6/14（42.9%）**，业务情景 **4/11（36.4%）**，合格动态镜头 **0/11**。

## 运行身份与来源

06:33:20 UTC 的 [生产构建资格](evidence/episode04-r0183-20261016/production-build-qualification.actual-a01.json)绑定 source/native build `20c7319b6964c80fa419540cf4e30852feff4810`。游戏为 CK3 `1.20.0.4`／Steam build `25734779`，实际 EXE `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`，101,040,248 bytes，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。实际 a26 DLL SHA-256 为 `d5f6217ba0a5d785e1e9e4d57472d7bf652b337d2aab189fc111d1cc7b547735`；injector 为 `ca8927a2d6690390c1c885427aa2d149af48556419784ce1b323968043741f0e`，host 为 `f884a1f229faae1e7369b3285d753be8de1f565219b637c595c3cbfda24d3cff`。资格回执中的 `game_started=false` 是其开场前时点，不表示后续没有实机。

当场最终使用的 [Steam 离线审阅](evidence/episode04-r0183-20261016/steam-offline-reviewed.actual-a03.json)为 06:45:16 UTC，直接审阅同一原图内的新 nonce 与 Steam 离线文字；桌面 shell 时钟仍停滞，回执没有声称桌面全面恢复。此处不使用早期 a01 离线审阅替代最终 a03。

06:54:27 UTC 的 [运行身份](evidence/episode04-r0183-20261016/runtime-actor-identity.actual-a01.json)及 [守卫 PASS](evidence/episode04-r0183-20261016/runtime-actor-guard-check.actual-a01.json)绑定 PID `7640`、进程创建 FILETIME `134366067983295206`、connection generation `1`、episode `native-31254-f71419cd501a`、实际角色 full ID `31254`、起始 date raw `53147928`。这是 R182 普通 checkpoint 的接续，不是新的 1066 开局或 ABC T0。新场普通存档为 73,445,818 bytes、SHA-256 `c7d9de734ab0fdd613046cac99f6d6b8f4b338a08ecd85f9bac209993b1d2fe1`；头部实际字面值与来源链支持罗贝尔意图，但没有解码出历史 ID `1128` 到运行时 `31254` 的直接字段。该数值不能成为跨场通用角色映射。

## 窗口化采集的实际方法

| 尝试 | 本场实际结果 | 能支持的结论 |
| --- | --- | --- |
| 07:25:46 UTC，`window-pilot-a01`，`gdigrab hwnd=32639418` | 1280×720 原始 PNG 全黑，尚未开始 raw 录像 | 此 HWND 采集路径在本场失败；不能据 ACK 或图像尺寸宣布窗口采集通过 |
| 07:34:19 UTC，`window-pilot-a02` | 以已核验 CK3 客户区屏幕坐标采集，原图可见暂停地图和 Army18 面板；07:37:42 UTC Root 审阅通过此单帧 | 客户区区域采集能得到本场游戏图像；该单帧没有 Steam、Windows 边框或周边桌面 |
| 07:44:49 UTC，`raw-r183-a01` | 使用相同客户区区域开始外置受管 FFmpeg 录像；后因容量期限中止 | 有实际录制及可解码 partial，未完成 90 秒计划 |

CK3 HWND 为 `32639418`，窗口矩形 `[632,329,1928,1088]`；客户区在桌面上的矩形为 **`[640,360,1920,1080]`**，尺寸 **1280×720**；当时桌面 **2560×1440**。实际命令来自 [raw.intent.json](evidence/episode04-r0183-20261016/raw.intent.json)：`gdigrab` 使用 `-offset_x 640 -offset_y 360 -video_size 1280x720 -i desktop`。输出覆盖游戏客户区，没有录入整张桌面，也不是独立读取 HWND 渲染像素；其他窗口若覆盖该区域，仍可能被录入。单帧无遮挡不能证明全片无障碍、无冻结。

首次全黑图与修正 pilot 原图的离线直接审阅另记在 [pilot-offline-review.actual.json](evidence/episode04-r0183-20261016/pilot-offline-review.actual.json)，没有为此操作实时桌面。Root pilot 回执中的 `window_only=true` 描述所见图像范围，不能被下游解释成独立 HWND 捕获机制。

## 录像、推进与截止中止

[录制进程就绪](evidence/episode04-r0183-20261016/raw.process-ready.json)时间为 **07:44:49.651173 UTC**，FFmpeg PID `26452`。从 recorder ready 到第一次 resume ACK 为 **0.3726659 秒**，见 [handoff](evidence/episode04-r0183-20261016/r183-window-film-handoff.actual.json)。这是启动衔接时延，不是 clean span 或业务结果。

原容量配额复核截止为 **07:45:01.597 UTC**；本场没有续期。07:45:02.781143 UTC 的 [失败回执](evidence/episode04-r0183-20261016/raw.failure.json)记 `capacity review deadline reached`，外置录制进程经 abort 终止，`ABORT_TREE_EMPTY`、return code `1`、job active processes `0`，partial 保留。开拍时距原期限不足完成计划的 90 秒，这是本次未完成的直接时间约束；后续开拍必须同时核对剩余实机、容量期限与收尾余量。

原片 `raw-r183-a01/raw.mkv` 为 **2,883,584 bytes**，SHA-256 **`d232680842948124ea57f8138fc2d1a8cb4261a3db8bc2ec5062a3194e3c1e73`**；H.264、yuv420p、1280×720、30 fps，单视频流，无音轨。离线 [审计](evidence/episode04-r0183-20261016/r183-raw-audit.actual.json)读出 239 帧，首帧 PTS 0，末帧 PTS 7.933 秒，末帧结束 7.966 秒。容器 `duration=90` 只反映计划字段，**不能报告成实际留存 90 秒**。全解码 exit `0` 同时产生 `File ended prematurely`，仅说明现有包可解码，不说明录像完整。

| 原生完成回执时间 UTC | 日期 raw | 该日结果 |
| --- | --- | --- |
| 07:44:58.209266 | 53147928 → 53147952 | 1 个自然日 tick，overshoot 0，暂停已观测 |
| 07:45:00.391581 | 53147952 → 53147976 | 同上 |
| 07:45:02.739902 | 53147976 → 53148000 | 同上；Army18 仍在2635，`sieging`，路线为空 |

三个 [逐日回执](evidence/episode04-r0183-20261016/r183-raw-portable-facts.actual.json)及所引用的原生响应证明游戏推进了三天；最终原生响应 [r183-film-d03-poll-008.json](evidence/episode04-r0183-20261016/r183-film-d03-poll-008.json)已选择性入库。它们不证明第三日或全部三日画面保存在 7.966 秒 partial 内。Army18 没有本场新的行军或抵达事实；这些回执中 `soldiers=null`，不能把 pilot 单帧的1184兵倒填为三天兵力不变，也不能据围城状态宣布实际县损耗、补给流入或补员。

## 闭场与消费边界

[session-result.json](evidence/episode04-r0183-20261016/session-result.json)记本场于 **07:45:38 UTC timeout** 结束，**不是正常 UI 退出**；shutdown 中 CK3 exit code `1`、树清空、`cleanup_proven=true`，终态游戏进程清单为空。08:26:18 UTC 的 [任务总线原始状态](evidence/episode04-r0183-20261016/screen-task-after-release.actual.json)为 sequence `5733`、`waiting`、`resources=[]`。原 task JSON 没有机器字段；本包通过相同任务 ID 的 machine-bound bootstrap 记录及本机稳定 ID 读回说明其所属，未改写原始字节。

[bootstrap-result.json](evidence/episode04-r0183-20261016/bootstrap-result.json)顶层 `recorder.state=NOT_STARTED` 只描述 bootstrap 自有 recorder。本次实际录像由另一个外置受管 recorder 启动，应同时读取 `raw.intent.json`、`raw.process-ready.json`、handoff、failure 和媒体审计；不能由顶层字段推导“本场从未录制”，也不能反向把外置 partial 写成 bootstrap 正常 finish。

智能体与视频下游必须保持四层结果独立：单帧采集可见、原生日期推进、录像完整性、业务机制/人工签核。本场前两层有上述有限事实，录像为截断 partial，后两类资格没有增加。小型可移植摘要 SHA-256 为 `8431a2c562903fee5e5e1ce15fdd07468e5098f12488d8bd02bcb622a53aca94`；全部原始文件的来源路径、大小与 SHA 见 [source-index.json](evidence/episode04-r0183-20261016/source-index.json)。外置根为 `C:/ck3-e04-resume-20261015-a01/live12004-r183-siege-diagnostic-a01/`，离线审计根为 `C:/ck3-e04-resume-20261015-a01/r183-raw-audit-a01/`。这些路径是来源机器的定位信息，不保证其他机器可读；原件时效继续遵守[统一存储策略](../storage-retention-policy.md)，本包不新设或续期保护。
