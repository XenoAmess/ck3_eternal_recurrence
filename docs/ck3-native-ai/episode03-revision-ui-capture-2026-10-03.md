# 第三期返修：威廉书签与新原版 UI 录制来源

整理日期：2026-10-03（Asia/Shanghai）。本页保存 **R0157 / R0158 新界面素材的来源、选择证据、连续片段与清理结果**。实际研究案例仍是 [R0156 刘易斯围攻](episode03-william-lewes-live-2026-10-03.md)；新画面不替代其数值前后样本。本页及[机器可读索引](episode03-revision-ui-capture-2026-10-03.json)只整理既有文件，没有重新启动游戏、SDK、Steam、桌面、录制器或任务总线，也没有重跑测试、native构建或媒体audit。

## 版本、准备与执行边界

两次准备均记录原版1.20.0.3 Crozier，EXE101039736 bytes、SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`；简中、fullscreen1920×1080、enabled_mods空，`native_bridge_mode=disabled`，没有自动load/continue参数。存档只在新独立profile里保留精确SHA副本，通过官方界面加载；仓库不复制这些存档或游戏二进制。源码基线记录 `6c87eb77568601499ab98a43f9cbea4c2ee870f6`。

R0157实际命令使用a02 launcher与`live-…R0157-a03`目录，不能把目录a03后缀改写成launcher版本。准备时D:/we3r包含已授权的composer/production视觉修改，whole_worktree_clean=false；392项固定launch依赖独立冻结，屏幕keeper使用另一干净D:/e3rt。R0158准备来自干净D:/e3u的392项冻结依赖。完整prepared、实际run/recorder argv和依赖manifest路径与SHA均在同名JSON；不把模板参数当作实际执行。

准备状态引用的默认 `.3` **离线编译descriptor**共有62项capabilities，没有frontend/bookmark能力。本次选用官方UI，且运行时native bridge关闭；没有SDK、pipe或DLL注入。源码注册某个MCP名称不等于该build可调用。本页没有宣称当次runtime advertisement已验证，也没有虚构MCP失败尝试。`open_kaishek`是原版前端没有mod-script语义的not-applicable。1920纯原版profile有自己的冻结settings，不声称2560/mod/OCR标准validator通过。

R0157启动使用[既有a08离线审阅](D:/ck3-war-episode03-revision-20261003-a01/bookmark-preparation/normalized-offline-review-a08.json)，R0158使用[既有a09离线审阅](D:/ck3-war-episode03-revision-20261003-a01/bookmark-preparation/normalized-offline-review-a09.json)。两者关联原图、真实窗口位移及新像素鲜度收据；本次只核对已有pins，没有产生新的离线观察或改变Steam模式。

## 威廉原生书签与选择证据

漂亮的威廉画面来自[新R0157原图](D:/ck3-war-episode03-revision-20261003-a01/ui-capture/william-bookmark-clean-01/desktop.png)，**2805333 bytes**，SHA **`414cf9d018e08c8f39270b3eedfc6077cd487005855c11600aac1cb1ed4672ae`**。原图1920×1080，已直接审阅：当前是“英格兰的命运”，公元1066年9月15日；右侧选中“私生子”威廉、39岁、诺曼底公爵，显示原生人物肖像、家庭和介绍。

[选择点击回执](D:/ck3-war-episode03-revision-20261003-a01/ui-capture/william-bookmark-selected-01/receipt.json)和[清爽画面回执](D:/ck3-war-episode03-revision-20261003-a01/ui-capture/william-bookmark-clean-01/receipt.json)关联同一真实CK3PID18892及原始1920尺寸；选择后画面也有自己的独立SHA。prepared里的frontend_observed=false、william_selected=false只描述启动前准备状态，不能替代或否定之后的选角画面。process-ready也不单独证明书签已选中。

连续原片中的书签可用PTS **[126.000,141.000)**：原生介绍可读，人物有细微动画；它是角色选择页面，game_progress=false，不宣称日期推进。完整[稀疏画面复核与cutlist](D:/ck3-war-episode03-revision-20261003-a01/new-footage-review/r0157/exact-cutlist-a01.md)保留实际解码帧、PTS、命令和图册。

## 新UI演示与旧事件分开

R0157随后示范暂停合军、渡海、登陆起围和新run占领。其占领样本在1067年2月24日画面中显示2月23日胜利、军队5439，不能配成旧R0156的4月22日6384事件。

R0158从新profile加载已冻结autosave副本，示范普通日进度、总工作、当前事件计时、地图占领及战争面板。复核实际PTS295显示围攻事件计时（8天剩余、12天间隔）；PTS308/320/322显示森林提示。`walls/breach`回执文件名不证明镜头是破口大小或城墙状态提示，不能把命名当作内容验收。已直接审阅[5月2日后态原图](D:/ck3-war-episode03-revision-20261003-a01/ui-capture/r0158-dismiss-event-01/desktop.png)：日期1067年5月2日，通知“围攻获胜5月2日”，军队5493，围攻窗消失、出现占领斜线。这是**另一次5月2日完成**，不是原R0156的4月22日完成。5月1日最后围攻阶段被事件模态遮住，不声称原片提供了清晰连续的城破前后过程。之后战争面板段跨6月2日至6月24日；6月2日原图显示南撒克逊+13.2%与当前上限+150%，仍只作新UI示意，没有同帧native数值query或新的完整公式验证。

两条原片的生产回执都exit0、recorderPID absent：R0157原片1791466340 bytes，SHA `3efaeaecb7396a139fd0b1d143ef4beff2714b80590ed70b4493e7e6f046edac`；R0158原片951107548 bytes，SHA `6bb76e0e776d61ad93ecc5f87845f1a7fc2a351e9063cd7a76eb18d72003e6ac`。实际媒体时长分别为1453.866秒与595.700秒，均为1920×1080、H.264、30fps、无音轨。独立素材复核记录实际ffprobe与showinfo PTS，不把UTC或请求seek直接当媒体时间。

| 来源 / 连续段 | 源PTS秒范围（起含末不含） | source role | game progress |
|---|---|---|---|
| R0157 / r0157-william-bookmark-intro | [126.0, 141.0) | new-ui-demo | False |
| R0157 / r0157-paused-merge-action | [496.0, 503.0) | paused-ui | False |
| R0157 / r0157-calendar-travel-and-arrival | [856.0, 880.0) | new-ui-demo | True |
| R0157 / r0157-new-run-occupation-change | [944.0, 955.0) | new-ui-demo | True |
| R0158 / r0158-siege-window-long | [90.0, 320.0) | new-ui-demo | True |
| R0158 / r0158-occupation-map | [422.0, 474.0) | new-ui-demo | True |
| R0158 / r0158-war-panel | [492.0, 595.0) | new-ui-demo | True |

切段范围与内容限制以[R0157](D:/ck3-war-episode03-revision-20261003-a01/new-footage-review/r0157/exact-cutlist-a01.json)、[R0158](D:/ck3-war-episode03-revision-20261003-a01/new-footage-review/r0158/exact-cutlist-a01.json)精确cutlist为准。这是候选区间的稀疏采样直接看图，不是逐帧人工验收或1×完整观看。编辑应绑定实际源片与连续PTS，不逐句重复片头，也不把新UI演示叠成旧数值事件。

R0158三个主区间分别为230、52、103秒，合计385秒。其中只有230秒属于连续围攻窗口，另外155秒是完成后的地图与战争面板；不能将385秒都说成围攻窗口或把素材容量写成已渲染成片验收。

## 2026-10-03 追加勘误：第一张R0158回执的旧scope文字

[r0158-frontend-01原始回执](D:/ck3-war-episode03-revision-20261003-a01/ui-capture/r0158-frontend-01/receipt.json)的scope仍字面写“New vanilla R0157 UI demonstration”。该文件时间、路径和CK3PID9264与实际R0158运行相符，这是遗留文字标签。后续loaded/daily/war回执已经使用通用“New vanilla UI demonstration”。原始错误回执字节保留，本页追加勘误，不覆盖历史。

## 停止、恢复显示与屏幕租约释放

R0157与R0158均按root_stop_requested停止，error=null；cleanup_proven/tree_gone=true、Job最终0进程、最后CK3 inventory空、watchdog消失、keeper线程退出。回执中的CK3 termination exit_code=1原样记录，不冒称自然退出0。

[最终清理](D:/ck3-war-episode03-revision-20261003-a01/capture-cleanup-a01/result.json)确认CK3/recorder进程清单为空，且屏幕仍只有本次 `ck3-e3-revision-ui-r0158-20261003` 一个持有者；显示由1920×1080恢复为**1024×768**，pyautogui与新截图尺寸一致，registry_persisted=false。keeper最后序号3875，随后[CAS释放命令](D:/ck3-war-episode03-revision-20261003-a01/capture-screen-release-a01/command.json)exit0，[实际回读](D:/ck3-war-episode03-revision-20261003-a01/capture-screen-release-a01/stdout.json)为**3876**、state=done、resources空。

原R0156录像、原九制作输入、存档及数值证据继续保全；本次未写入这些历史来源。新的raw、截图、argv、stdio、prepared、旧候选与失败attempt也永久保留。文档不宣称新增numeric proof、G2/Robert验收、人工1×签核或metadata/OneDrive远端验证。最终成片及交付由根代理另记真实结果。
