# R183 拍摄结果：客户区区域可见，原片因截止中止

`machine_id: desktop-3fevhd2-1c74096080`；run `desktop-3fevhd2-1c74096080--vanilla--R0183`，2026-10-16 UTC。实际拍摄源 `20c7319b6964c80fa419540cf4e30852feff4810`，CK3 `1.20.0.4`／build25734779。原片与实机事实权威记录在 [研究专题](../../../docs/ck3-native-ai/episode04-r183-window-capture-12004.md)及[精简原始回执](../../../docs/ck3-native-ai/evidence/episode04-r0183-20261016/README.md)，视频制作与智能体开发共用同一来源。

窗口化下**实际取得了仅含 CK3 客户区的单帧，并启动了该区域的录像**。本次不是完整可交付镜头：保留 raw 只有 **239 帧，实际帧末端7.966秒**，容量期限到达后中止，未认证 clean span、未人工完整观看、未获签核。因此合格动态镜头仍 **0/11**；研究 **6/14（42.9%）**、业务情景 **4/11（36.4%）** 不变。

## 录到了什么范围

最初 `gdigrab hwnd=32639418` 的 `window-pilot-a01` 原图全黑，未启动 raw。修正后的 `window-pilot-a02` 直接取 CK3 客户区在桌面上的区域：桌面2560×1440，客户区矩形 **`[640,360,1920,1080]`**，输出 **1280×720**。Root 07:37:42 UTC 的单帧审阅看到游戏暂停地图与 Army18 面板，没有 Steam、Windows边框或周边桌面。

实际录像采用 FFmpeg `gdigrab -offset_x 640 -offset_y 360 -video_size 1280x720 -i desktop`，记录客户区所在的屏幕区域。它没有录整张桌面，但也不独立读取 HWND 像素；其他窗口覆盖该区域时可能进入录像。pilot与开拍前单帧通过只支持这些静态帧，不能代替全片无遮挡、无冻结检查。来源是入库 [raw.intent.json](../../../docs/ck3-native-ai/evidence/episode04-r0183-20261016/raw.intent.json)及 [pilot 审阅](../../../docs/ck3-native-ai/evidence/episode04-r0183-20261016/window-pilot-a02.pilot-reviewed.actual.json)。

## 时间、原片与原生推进

| 项目 | 实际结果 |
| --- | --- |
| 外置录制开始 | 07:44:49.651173 UTC；recorder ready→resume ACK 0.3726659秒 |
| 原容量复核期限 | 07:45:01.597 UTC，未续期；不足完成计划90秒 |
| 实际中止 | 07:45:02.781143 UTC，`capacity review deadline reached`，`ABORT_TREE_EMPTY` |
| 原片 | `raw-r183-a01/raw.mkv`，2,883,584 bytes，H.264／1280×720／30fps，无音轨 |
| 实际媒体末端 | 239帧，末帧PTS7.933秒，末帧结束7.966秒；容器90秒是计划字段 |
| 完整性 | 全解码exit0但有 `File ended prematurely`，属于截断partial |
| 原生推进 | 三天：53147928→53147952→53147976→53148000，每天overshoot0；最后Army18仍在2635围城 |
| 游戏闭场 | 07:45:38 UTC受管timeout，非正常UI退出；游戏树与录制进程树均已清空 |
| 屏幕释放 | 08:26:18 UTC，task seq5733、waiting、resources[] |

原片 SHA-256：`d232680842948124ea57f8138fc2d1a8cb4261a3db8bc2ec5062a3194e3c1e73`。原始录像位于来源机器 `C:/ck3-e04-resume-20261015-a01/live12004-r183-siege-diagnostic-a01/raw-r183-a01/raw.mkv`，未复制进仓库；可移植摘要 SHA-256 `8431a2c562903fee5e5e1ce15fdd07468e5098f12488d8bd02bcb622a53aca94`。详细离线媒体审计原路径 `C:/ck3-e04-resume-20261015-a01/r183-raw-audit-a01/r183-raw-audit.actual.json`，小型精确副本已入库。

三次原生日期回执的时间分别为07:44:58.209266、07:45:00.391581、07:45:02.739902 UTC，晚于部分已留存画面的范围，**不能据此宣称三个自然日全部录入片中**。本场没有新的行军、抵达、实际扣兵、补给流入或补员正样本。暂停pilot里看见的1184兵不能替代逐日的实际兵力查询。

## 剪辑与后续拍摄约束

此 raw 暂列失败采集证据，未经逐帧检查不得作为机制正证据或连续 clean 动态镜头。不得把容器90秒写入成片素材时长，也不得用R182或后续原生到达状态倒填本场画面。若后续审查从partial选出可用片段，需另行绑定精确raw字节、帧范围和用途；本页没有预先批准任何片段。

后续开拍前须同时完成客户区坐标核验、真实pilot审阅、剩余实机与容量期限检查，确保计划时长和正常收尾余量均可容纳；本条为本次失败导出的操作要求，不声称代码已验收。录像结束还需正常finish及媒体完整性检查、连续画面审阅，之后才可能生成clean候选；业务资格与人工1×/signoff独立记录。

顶层 `bootstrap-result.json` 中 `recorder=NOT_STARTED` 只指bootstrap自有recorder。本次外置受管recorder的intent、ready、handoff、abort和raw同时存在，不能将两种所有权混读成“没有拍摄”或“正常拍完”。所有机器相关结论仅适用于上述machine ID与时点；原片及过程资产按[统一存储策略](../../../docs/storage-retention-policy.md)评估期限，不据本页永久保护。
