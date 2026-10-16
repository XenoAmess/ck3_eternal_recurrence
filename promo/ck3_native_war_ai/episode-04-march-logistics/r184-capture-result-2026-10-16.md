# R184 拍摄结果：正常封装22.766秒客户区录像

`machine_id: desktop-3fevhd2-1c74096080`；run `desktop-3fevhd2-1c74096080--vanilla--R0184`，2026-10-16 UTC；runtime/native源 `163530f1bbcabe5a97854625b3fab7568006ee65`。CK3 `1.20.0.4`／build25734779，本场独立载入R182普通checkpoint。完整来源、身份与可供智能体复用的方法见 [R184研究专题](../../../docs/ck3-native-ai/episode04-r184-window-capture-12004.md)和[精简证据索引](../../../docs/ck3-native-ai/evidence/episode04-r0184-20261016/source-index.json)。

本次得到**正常封装22.766秒／683帧**的原片，完整音视频解码exit0且无诊断，完成正常保存与游戏exit0退出。它解决了上次截断文件的采集问题，仍没有连续clean认证、人工完整观看或成片签核；合格动态仍 **0/11**，研究 **6/14（42.9%）**、业务 **4/11（36.4%）** 不变。计划90秒因辅助器误判提前finish，不能将此结果写成已拍满90秒。

## 画面与媒体身份

| 项目 | 本场实际结果 |
| --- | --- |
| 输入 | canonical recorder；FFmpeg `gdigrab -i desktop`仅取已核验客户区区域 |
| 区域 | 桌面2560×1440；客户区屏幕矩形`[640,360,1920,1080]`，输出1280×720 |
| 捕获语义 | 没有录整张桌面，也不是独立HWND渲染像素；guard采样未报错误，仍需逐段审片排除遮挡/冻结 |
| 原片 | `raw-window-a01/raw.mkv`，11,904,058 bytes；H.264／yuv420p／30fps，无音轨 |
| 时码 | 683帧，首PTS0、末PTS22.733秒、末帧结束22.766秒；无缺失时间戳或倒退 |
| 结束 | `NORMAL_TREE_EMPTY`，recorder exit0、active0，`capture_guard_error=null`，未报告premature end |
| 期限 | spawn时90秒计划＋180秒收尾要求270秒，实际约3608.54秒可用；本次未因容量期限截断 |

原片SHA-256 **`6d1704561753f74adc689fe1c2a3be391b1e15063e3b7c83d06476d3ea605f19`**，来源机器路径 `C:/ck3-e04-resume-20261015-a01/live12004-r184-window-capture-a01/raw-window-a01/raw.mkv`。实际 [recorder结果](../../../docs/ck3-native-ai/evidence/episode04-r0184-20261016/raw.result.json)与[媒体审计](../../../docs/ck3-native-ai/evidence/episode04-r0184-20261016/media.audit.actual.json)已入库；没有把raw、PNG或存档复制进仓库。

离线直接审阅三张既有原尺寸帧：0秒见1067-02-12，请求11.3665秒见1067-02-15，请求22.733秒见1067-02-21；均只有CK3地图、军队及军事面板，未见Windows边框、Steam或周边桌面。[Root原尺寸复核](../../../docs/ck3-native-ai/evidence/episode04-r0184-20261016/root-three-frame-review.actual-a01.json)已纠正早期多图预览中的中/尾日期误读。其[独立单帧审阅](../../../docs/ck3-native-ai/evidence/episode04-r0184-20261016/three-still-offline-review.actual.json)不等于完整连续播放检查，不证明每个中间日都入片，也没有批准clip。原audit的旧 `visually_reviewed=false` 字段保持原样，后续审阅分开留据。

## 推进、提前结束与正常闭场

八份完成回执证明date raw **53147928→53148120**，各日1 tick、overshoot0；Army18仍在2635围城、route empty。第九次Resume后，第一轮询同日paused却有native/public revision变化，辅助器误分类为early pause并转入正常finish。离线实际trace已确认这是轮询分类问题；具体促发native新发布的字段未查明。候选修正通过离线回归，尚无新实机资格，不重投旧动作、不追认第九份exact-day成功。

后续正常保存日期为 **53148144**、checkpoint73,664,718 bytes、SHA `fe0ef524ec71a77f830faf1cce1d46167790799796f006eb5335a3637836f2b8`。它与片中日期样本、八份辅助器完成回执分别记录，不能互相倒填。13:03:25 UTC游戏正常process_exit0，进程树清空；13:07:47 UTC屏幕任务seq5763、done、resources[]。屏幕释放回执未同时授容量预留返还，Root另做存储闭场。

## 剪辑范围

当前原片可进入下一轮连续画面审查，不能直接计为合格机制镜头。需要逐段确认实际内容、日期变化、无遮挡与无冻结，再将获准区间绑定raw SHA及帧范围；片中不直接可见的native数值只能作有来源标签的叠层。正常媒体文件和军事面板可见，不证明实际扣兵、补员、补给增长或付款结果。

新包只带选择性小原件与一份完整闭场snapshot，其他快照和时钟原件保留精确外置pin；它不是完整可移植closure replay。研究与视频共享同一事实入口，其他机器复用方法后仍须自行取得本机实时资格。所有原件与过程资产继续按[统一存储策略](../../../docs/storage-retention-policy.md)复核，本页不续期容量或保护。
