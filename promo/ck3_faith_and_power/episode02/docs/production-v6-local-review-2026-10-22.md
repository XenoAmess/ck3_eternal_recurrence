# 信仰引擎二期 V6 本地审阅版制作记录

machine_id: 4-8e1c2f1861。制作终态实际时间：2026-10-22T06:18:36.152059+00:00；Root有限画面审阅完成时间：2026-10-22T06:22:24.314803+00:00；原生宗教实际观察时间：2026-10-22T03:57:31.598338Z。

当前状态：黄色完整审阅版已于07:46:17.841701Z完成，Root于07:49:24.658285Z完成五张最终编码帧配色抽查，本机本地交付。此前蓝色稿及其技术检查保留历史身份，不将其追认为系列视觉合格。蓝色原进程PID14212于05:51:31.248Z启动，06:18:36.152Z原等待0；黄色原进程PID13544于07:18:33.757277Z启动，07:46:17.841701Z原等待0，耗时1664.084秒，两次均无自动重试。

本期主题是「朝圣在奖励什么？」：分别计算支出、活动评价、虔诚奖励和人物成长，再用固定条件的算例解释它们的关联。实际视频44102帧、24:30.067；33段旁白、196组双语字幕。仅N02、N15为实拍后新配，31段原声保留。作者时钟与实际视频帧数相符；101秒额外静读时间已计入总长。

主片保留28页主表，另补8条当前事件／初始化路径。169条来源条目按118条主片处理、51条历史／角色生成／调试资料处理；不能宣称169条逐项全部进入主片。

## 本次实拍

完整场次ID：4-8e1c2f1861--faith-engine--R0032。实际人物31254、日期53144328、天主教信仰13，由同场原生宗教观测绑定。CK3版本1.20.0.4，EXE SHA-256：98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518。

| 镜头 | 本次实际观察 | 适用边界 |
| --- | --- | --- |
| 朝圣类型 | 虔诚朝圣、世俗朝圣两张卡 | 识别本次界面，不外推全部宗教 |
| 朝圣意图 | 深思熟虑、行善、热忱三项 | 本次人物菜单显示；不能普遍称固定四选一，也未逐项授予CanPick资格 |
| 旅队主管 | 0.10金币／月 | 未任命；月薪不等于出发俸禄L |
| 当前配置报价 | 基础60.0＋距离10.0＝70金币 | 未出发／付款，不是F0的176公式模型实测，也未证明所有旅行分项已经包含 |

四段原片都是VFR，实际帧数187／219／205／205。每段选择真实2—7秒供交付重采样；150帧是5秒×30fps的作者目标，不能冒称原片已包含150帧。四段完整解码均返回0，12张实际PTS抽帧已作有限画面检查。它们不是完整朝圣实况，也不证明完成了新旅程。

原生正常退出已确认OS0，原公共run等待返回0；keeper停止后Root按CAS13272释放现场。独立任务于05:53:39Z恢复原1024×768@60、32bit、rotation0，CAS13274释放，未影响离屏编码。

## 研究与来源

- [旅行费边界补记](research-v6-travel-fee-boundaries.md)及[结构化来源](knowledge/pilgrimage-v6-travel-fee-boundaries-12004.json)区分主管GUI接收者、出发俸禄、补给显示门及两个规划器的报价容器。主管getter至脚本root／aptitude scopes、补给producer、旅行与活动最终合计／付款链仍未闭合，不能用70或176拟合完整实付。
- 已提交的导演稿与配置：0264e27d06f01042ae25a4da00b78413ae019746。两段声音先冻结于b916d652888464ba5aa848646fa9a9286c142176；三份配置／导演稿字节与提交版本相同。旧图表的a425作者输入保留独立快照。
- 工作根：C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01。原生宗教来源位于filming/live/4-8e1c2f1861--faith-engine--R0032/case-output/ordinary-pilgrimage-0002-receipt.json；四镜头来源、实际PTS及画面审阅在full-grant/native-media-a01/SOURCE-INDEX.actual.json和DELIVERY.actual.json。
- 自动验证、解码和有限抽帧不代替人工完整观看，未制造人工签核。原片、派生物和交付按通用存储策略分别限期保留。

## 蓝色历史稿的本地文件与验片

本机器按本地交付例外提供实际文件，不配置或重试OneDrive。

- [完整审阅版MP4](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/full-grant/sample/build-a01/native-run/derived/direct/episode02-review.mp4)：70,123,159字节；SHA-256：08410cc82cbd5b339e8f12c8e02c222d4f1780e473f760b9fbff4b9299d424b8。
- [双语SRT](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/full-grant/sample/build-a01/native-run/derived/direct/text/episode02.bilingual.srt)、[中文SRT](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/full-grant/sample/build-a01/native-run/derived/direct/text/episode02.zh.srt)、[英文SRT](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/full-grant/sample/build-a01/native-run/derived/direct/text/episode02.en.srt)、[配套讲稿](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/full-grant/sample/build-a01/native-run/derived/direct/text/episode02-script.md)。

实际媒体为H.264、2560×1440、30fps；AAC、48kHz、双声道。视频和音频流时长1470.066667秒，容器1470.088021秒，视频起点0.021354秒；不将容器长度误作多出一帧。全部44102个视频PTS连续，完整AV严格解码返回0，原五个音乐窗口检查通过；现成音量统计平均−22.7dB、峰值−3.6dB。没有另跑同结论检查。

Root直接审阅16张最终编码帧，覆盖五种朝圣态度、麦加初始化、意图菜单、旅行密集表、四段实拍、活动本体有序费用、虔诚阈值与算式、经验封顶及初始／生成人物。所选画面中的公式和脚注完整，关键字段与字幕分区清楚；实拍70金与模型、月薪与出发俸禄分别标注。静读时字幕为空属于安排。此结论仅限抽帧，不代替连续动作检查、整片听审或人工1倍速观看，也不构成人工签核。

原件索引以工作根为相对基准：

- 正式成片与现成技术结果：full-grant/sample/build-a01/completed-review.json；该文件状态仍为ENCODED_REVIEW_PENDING，保留人工审阅待办。
- 原合成进程退出：full-grant/sample/BUILD-ORIGINAL-WAIT.actual.json。
- 原完整解码、probe、PTS：full-grant/sample/build-a01/audit/下full-decode、final-probe、final-pts的command.json、result.json及实际输出；音乐为build-a01/music-presence.json。
- 最终画面抽取与审阅：full-grant/sample/final-visual-review-a01/EXTRACTION.actual.json、VISUAL-REVIEW.actual.json；16张JPEG共3,690,317字节，未增加第二次整片解码。

当前交付是机制分析审阅版。费用剩余三条研究链见上文，保留未知项；本次没有出发、支付或完成新朝圣，也没有新增普通auto业务资格。用户此前对V3教学价值的否定保持原样，不能由技术通过追认为本版教学价值已获用户认可。

## 用户指出配色错误后的黄色修订

用户指出「图的颜色为什么不是我们系列的黄色，而是蓝色？」。直接原因是本次独立图表生成器写死青蓝色板，没有沿用既有full_diagrams.py的系列暖棕／金黄色。Root原16帧检查只检查文字、公式与来源披露，漏掉系列视觉一致性；该有限通过不授配色合格。

本机2026-10-22T07:05:04.208529Z已重生成55张实际使用图表，273处图引用待按新pins进入新片。直接重用原绘图函数，仅换系列色板，所有有效text_runs的文字、字号和bbox与原件一致。三张代表图直接审阅通过，新完整yellow_graphics.py的strict通过；没有改游戏原图或重配声音。色板已同步[品牌记录](../../series-brand.json)及[制作经验](../../docs/production-experience.md)。

黄色输入正常plan于07:13:15Z返回0，gaps为空，仍为33段／44102帧／24:30.067；反向替回原图和原grant后与a10逐字段相等。新工作根是原工作根下yellow-revision-a01，明确新准入至08:00Z，不修改原蓝色attempt。最新Release查询的前三次网络失败保留；07:23:19.191162Z重查实际成功，仍为正式v0.3.0、wheel SHA与隔离安装一致。该正面结果晚于本次build启动，不能倒填启动前确认；没有安装或降级依赖。

## 黄色修正版的当前交付

- [当前MP4](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/yellow-revision-a01/sample/build-a01/native-run/derived/direct/episode02-review.mp4)：70,102,554字节；SHA-256：a73ead885dc93390a644e6ff65fb2607d3f705a452e7a467c210ff10a276f5d4。
- [双语SRT](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/yellow-revision-a01/sample/build-a01/native-run/derived/direct/text/episode02.bilingual.srt)及[讲稿](C:/workspace/ck3-faith-and-power-20261017/episode02/v6-mechanism-production-20261022-a01/yellow-revision-a01/sample/build-a01/native-run/derived/direct/text/episode02-script.md)；同目录有中文、英文SRT。三个SRT和讲稿SHA均与蓝色版相同，旁白、切点、静读和四段实机未变。

实际媒体H.264、2560×1440、30fps、44102帧，AAC、48kHz双声道。音视频流均1470.066667秒，容器1470.088021秒。原完整AV严格解码返回0，全帧PTS和五窗口音乐检查通过，音量平均−22.7dB、峰值−3.6dB；全片技术结果来自新build，未借用蓝色版通过。Root额外直接审阅五张最终编码帧：主题页、事件接受者补图、旅行密集表、有序费用和经验封顶，暖棕与金黄色已正确进入成片，主要文字和脚注未被字幕遮挡；密集表静读时字幕为空。该检查仅限五张画面，完整人工1倍速听看与签核仍为false。

本次新输入661,697字节／SHA99894377e440c7c2dfedd2d12e6039c0c9ca7a1d0b520e0a8db1cbcf41f71182；实际启动源HEAD4df7c93214de3737f07f145aabde745e78fa98d8。品牌与经验后继提交defdce517不改写实际启动源。以黄色工作根为相对基准，原build与审计索引为sample/RENDER-DELIVERY.actual.json，原wait为sample/BUILD-ORIGINAL-WAIT.actual.json，有限画面为sample/final-palette-review-a01/VISUAL-REVIEW.actual.json，55图替换为graphics/REPLACEMENTS.actual.json。

07:50:57.216075Z按通用存储策略完成新工作根闭场清点：972个既有文件，含本次回执余量的4KiB占用上界159,010,816字节，future0，未使用预留释放；目录元数据上界不冒充精确NTFS实占。成片／字幕30天、派生物48小时、记录180天后按用途复核，无自动删除；原片另沿既有30天规则。小清单为FINAL-STORAGE-CLOSURE.actual.json。仅本地交付，无OneDrive上传，也不据此新增游戏业务或用户教学价值签收。
