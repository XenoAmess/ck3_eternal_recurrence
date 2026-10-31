# 第一期董卓实拍与来源记录

`machine_id: 4-8e1c2f1861`。取材与闭场发生于2026-10-31 UTC；本次文档合入于2026-11-01北京时间。只归档已经发生的游戏、原生接口、保存和退出结果，没有重开游戏，也没有注册或修改生产事件策略。其他机器需重新取得自己的安装、Steam、存储、进程与屏幕资格。

本记录连接[第一期导演稿](../../episode-01-dong-zhuo.md)与[董卓玩法及事件知识](../dong-zhuo.md)。三份小型JSON分别保存[机器与闭场事实](machine-receipt.json)、[来源SHA索引](source-index.json)和[市丘保存战果](battle-result.json)。原片、大保存、世界全文与全部中间回执继续留在本机外置目录，没有复制进Git。

## 这次实际拍到了什么

| 项目 | 已确认结果 |
| --- | --- |
| 玩家与时间 | 190.1.1董卓5048新档，至190.5.1仍存活；date_raw 45464400→45467280，差2880小时，即120游戏日 |
| 剧情 | 190.2.1焚雒迁都，190.4.2讨董War31成立；迁都单选，不编造“不焚城”分支 |
| 战斗 | 190.4.24至190.5.1在省762市丘交锋，保存明确win5048；只确认这一场战斗胜利 |
| 战争与后续 | 闭场native229/public230、paused=true；War31仍在，董卓为主防守方；未央邀请未触发 |
| 保存 | 1次Native checkpoint成功；SDK物化的同SHA episode seed副本不算第2次游戏保存 |
| 操作区分 | 原版UI RaiseAll操作1次；事件选择、普通交互拒绝、时间推进及主力106的preview／move使用既有原生通道；查询与控制记录不混算世界动作 |

执行安装是CK3 1.20.0.4，EXE SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。隔离profile按主包3780919688、服装3797664499、议和3820784621、纯选人addon的顺序加载。原推荐卡未能直接选董卓，本地addon只新增190.1.1董卓推荐入口，复用`dong_zhuo_2`，没有改人物、历史持有、兵力、事件或规则。服装声明1.20.1.2与实际安装的差异保留；本次渲染与取材事实不等于全模组兼容验收。

Game2于2026-10-31T10:03:13.189274Z启动：PID字符串`12136`，birth FILETIME字符串`134379145931892740`。profile为`C:/workspace/hanjin-spring-autumn-20261031/shooting-02/launcher/state/profile`，pipe为`\\.\pipe\hanjin_dongzhuo_20261031_02`。启动使用当时新鲜的Steam离线回执；旧启动证据不授予将来新启动资格。

## 动员与原生接口边界

战前的`raise-troops-default`拒绝发生在服务提交DLL之前：`service.py`先要求当前step在`action_steps`内，`native_driver.py`仅在snapshot的active_wars非空时展开raise。本局早期snapshot为active_wars=[]，所以DLL声明raise、只读query合法也不等于公开动作可执行。这一条件没有读取Robert身份、ordinary-war readiness或succession_lifecycle。

190.4.2已有War31后出现另一种拒绝：第五次query为native132/public133、date_raw45466584，默认省867、unraised30923，status=available、legality_ready=true、failure=none，但native_default_raise_legal=false。查询与正式raise共用同一个actual4单省命令构造及最终validator，原生储备人数不能替代地点合法性。

现有命令从capital出发调`selector(character, capital, 0, -1)`，构造唯一entry`{province,-1}`；actual4 constructor将mode写为1、selected_index为-1。最终validator`298C2A0`调用单省`24A4890→24A4520`，已读有限正文包含占领、敌对军队、敌方领土分类及受限holder／家宅／首都关系。原生拒绝key为`RP_CANNOT_RAISE_OCCUPIED`、`RP_CANNOT_RAISE_HOSTILE`、`RP_CANNOT_RAISE_ENEMY_TERRITORY`。没有当前进程内存的分支读回，不能断言867实际命中哪一项，也没有证据据此修改Celestial预算。相关源码与有限反汇编的Hash已入[source-index.json](source-index.json)，反汇编正文仍外置。

主包`gui/window_military.gui:165–179`的原版控件`tutorial_highlight_raise_troops_button`使用`PlayerCanRaiseAnyRallyPoint`、`PlayerRaiseAllRegiments`及`GetPlayerRaiseAllTooltip`，与单省默认点合同不同。root实际使用一次该原版UI入口，随后独立snapshot读回可控军队；它另记为UI fallback，**没有记成typed default raise成功**。已有MCP没有显式province参数或typed多点RaiseAll，不通过改JSON绕过单省validator，不为本片换DLL或重启Game。

保存前driver历史100行、98行ok，里面含只读查询、界面控制和时钟请求，不是100次世界动作。精确命令分组在[machine-receipt.json](machine-receipt.json)：40条life-advance记录、14条第一显示项选择、4条待回复交互拒绝、1条主力106移动、1条preview、1条checkpoint等；失败和后态依原件保留，不将每行都计为成功。generic driver仍输出legacy rogue_one_life／xar_on声明，该默认字段不能证明本局加载了XAR pact。

## 市丘胜利来自保存结果

主力106与Combat16777217／Result16777216的身份由本局原生读回绑定。typed终态query返回`typed query result is inconsistent`，后继transition返回combat_not_found；它们保留为真实失败，敌军从列表消失也不能单独充当胜负判据。

本局唯一checkpoint为`launcher/state/profile/save games/xar_checkpoint.ck3`，40,181,838B，SHA256 `46ead77a194e755e247fc0ad3777df59f0bc487765463bf67dc6c677a957c1b6`。本机现成rakaly两次只读完整解码均exit0、无stderr未知token、有限提取未截断，保存size／mtime未变。没有生成或入库全世界melt正文。

保存的`combats.combat_results.16777216`明确记录：

- location762；董卓方main_participant5048、commander7554（乐进），inital_soldiers20030、surviving_soldiers20027。
- 对方main_participant及commander7125，inital_soldiers1410；本记录不猜其中文姓名。
- winning_side0、start_date190.4.24、end_date190.5.1、win5048、leader5048、wipedyes。

完整116行结果块与保存Hash、原始melt行号2038377–2038492保存在[battle-result.json](battle-result.json)。这支持“董卓方赢得本场市丘战斗”的离线结论；不回写原生查询失败，也不将War31记为结束。整数兵力差3与保存participants casualties4两个字段并列保留，不拼成统一伤亡数字。原辅助回执字段melted_utf8_characters实际按Java UTF-16 code units计数，不作为UTF-8文件字节数或资格依据。

## 正常退出与屏幕释放

原生normal-exit-context拒绝原因为缺少fixed actual managed-source inventory：本次由独立Java launcher启动，不能事后伪造managed-factory来源。停止本局MCP后，root通过WM_CLOSE进入原版退出对话框，取消退出自动存档，再退出桌面；没有强杀Game，也没有为补拍开第二个战局。独立launcher记录Game12136于`2026-10-31T16:53:54.7767446Z`正常exit0。

`display-restored.json`于`2026-10-31T17:05:23.024317Z`读回从1920×1080@60恢复到1024×768@60，change_result0。keeper随后报告thread_exited=true、last_sequence14882；其report中screen_released=false保留，不能把keeper停止直接当成租约已释放。

后继总线原始event14883于`2026-10-31T17:14:17.096922Z`以expected／prior14882释放本人过期claim，resources=[]；retirement.kind=`expired-own-claim-released`、business_status=`unresolved_red`、state=waiting。**资源已释放，退场状态不是验收GREEN。** [机器JSON](machine-receipt.json)保留选定原事件、原行SHA、keeper报告、显示恢复及exit0原件摘要；不复制整个总线或全部心跳。

闭场Steam回执`shooting-02/steam-offline-close.json`在`2026-10-31T17:23:30.835075Z`以native_current_user_byte确认offline_mode=true，Steam PID13760／birth FILETIME字符串134378949641026140前后一致。该新鲜闭场事实单独归档，不回填旧launch资格，也不授未来启动资格。

## 审片交付入口

稳定本机交付JSON：`C:/workspace/hanjin-spring-autumn-20261031/episode01-dongzhuo-delivery.json`。视频、字幕与封面分别为同目录的`episode01-dongzhuo-review.mp4`、`episode01-dongzhuo-review.srt`、`episode01-dongzhuo-cover.jpg`，时长约7分50秒。旁白为Edge TTS 7.3.1、`zh-CN-YunjianNeural`、rate -12%、pitch -8Hz。

旧初剪供给段5000部队／屠城tooltip和2万旁白错配，已在v3重选镜头。root实际核对`edit-02/qc-frame-245.png`的20,030／4,680／300及乐进实拍一致、无屠城tooltip，446秒甲胄近景亦匹配。新run002随后独立完成plan/build、17帧自动审计、33帧pending review、全片解码和封存后manifest校验，均退出0；人工签核仍为null，不将关键帧检查称为人工1倍速全片批准。旧v2视频及edit-01审核保留，新视频470.221秒、27,844,779B，SHA256为`80082a16a0925c17706b9ff62ceab48e57c4fef30216139b07df71c42227a00e`，元数据固定在[交付快照](delivery-snapshot.json)。可复用玩法知识已经合入[董卓专题](../dong-zhuo.md)，剪辑检查与原生取材／保存成功分别记录。
