# R183 精简可移植证据

`machine_id: desktop-3fevhd2-1c74096080`；run `desktop-3fevhd2-1c74096080--vanilla--R0183`，2026-10-16 UTC。本包供其他机器上的研究、开发、决策和视频消费者直接读取。运行源与 native build 为 `20c7319b6964c80fa419540cf4e30852feff4810`。事实说明见 [R183 专题](../../episode04-r183-window-capture-12004.md)，视频使用边界见 [promo 结果页](../../../../promo/ck3_native_war_ai/episode-04-march-logistics/r183-capture-result-2026-10-16.md)。

33 份原始小文件均逐字节复制，原路径、bytes、SHA-256 与复制范围见 [source-index.json](source-index.json)。另有本代理直接审阅两个既有 pilot 原图后生成的 [离线单帧审阅记录](pilot-offline-review.actual.json)；它明确不是原始实机回执，也不是完整视频审阅。

| 入口 | 用途 |
| --- | --- |
| [r183-raw-portable-facts.actual.json](r183-raw-portable-facts.actual.json) | 最小机器可读结果，SHA-256 `8431a2c562903fee5e5e1ce15fdd07468e5098f12488d8bd02bcb622a53aca94` |
| [r183-raw-audit.actual.json](r183-raw-audit.actual.json) | 原片元数据、完整命令、239 帧与末端7.966秒、截断诊断及三天回执；SHA-256 `f1ac860bf7794e90a5d7c29c0c43c0d06c9e55d87a70a6b1960a7f45fbaecb32` |
| [production-build-qualification.actual-a01.json](production-build-qualification.actual-a01.json) | CK3 EXE、a26 生产构建与来源绑定，非业务通过 |
| [runtime-actor-identity.actual-a01.json](runtime-actor-identity.actual-a01.json) / [guard](runtime-actor-guard-check.actual-a01.json) | 本次 PID7640／generation1／episode／actor31254 的身份链 |
| [window-pilot-a01.pilot.actual.json](window-pilot-a01.pilot.actual.json) / [a02](window-pilot-a02.pilot.actual.json) | HWND 试图全黑；改为客户区屏幕区域采集后取得可见游戏单帧 |
| [raw.intent.json](raw.intent.json) / [process-ready](raw.process-ready.json) / [handoff](r183-window-film-handoff.actual.json) / [failure](raw.failure.json) | 外置录制的真实命令、开始、0.3726659秒衔接、容量截止 abort |
| [r183-film-d03-poll-008.json](r183-film-d03-poll-008.json) | 最后一天的选择性原始 native snapshot；三天完成小回执也均入库 |
| [bootstrap-result.json](bootstrap-result.json) / [session-result.json](session-result.json) / [screen state](screen-task-after-release.actual.json) | 游戏 timeout 与树清空；屏幕任务最终 seq5733、waiting、resources[] |

`raw.mkv`、所有 PNG、存档、游戏源码、全量请求/响应、构建产物未复制到仓库。原片现有审计身份为 2,883,584 bytes、SHA-256 `d232680842948124ea57f8138fc2d1a8cb4261a3db8bc2ec5062a3194e3c1e73`；其原路径保存在索引与审计中。哈希不代替原件可读性，也不表示已上传到其他机器。

读取时须保留以下边界：

- `gdigrab -i desktop` 只取已核验客户区 `[640,360,1920,1080]` 的1280×720区域，没有录整张2560×1440桌面；区域可能受其他窗口遮挡，不是独立 HWND 像素捕获。
- 容器90秒为计划值；实际可用239帧，末端7.966秒，`File ended prematurely`。全解码 exit0 不能提升为完整录像。
- 三个自然日回执不表示三天都在留存 raw 里；Army18仍位于2635围城，不是新的行军或抵达正样本。
- bootstrap 的 `NOT_STARTED` 只描述其自有 recorder，不能抹掉外置 recorder 的开始与失败；cleanup成功不等于正常退出。
- `business_positive=false`、`clean_span_certified=false`、`human_full_review=false`、`human_signoff=false`；研究6/14、业务4/11、合格动态0/11不变。

这些是来源机器在所记录时间的事实。新机器的 Steam、CK3安装、权限、依赖、容量和实时采集必须重新核验。小型仓库记录按统一策略180天复核归纳；外置大原件按其实际用途与期限处置，本包不续期旧容量配额、不创建永久保护。
