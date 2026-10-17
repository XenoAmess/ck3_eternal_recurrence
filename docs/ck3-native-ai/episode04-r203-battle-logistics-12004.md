# R203：地图战斗短片、精确一日后验与正常闭场

`machine_id: desktop-3fevhd2-1c74096080`；实际run `desktop-3fevhd2-1c74096080--vanilla--R0203`，source/native source `19024b4d79d818a88709c9932ca4eb364d81ef33`、a35生产资格16,198B/SHA `a80af8f9df7ca2a2ba56e474cb4092654e8f0782908b63f8278672534e6e2f67`。PID31536/create134367365952775484/gen1/episode `native-31254-b17c8eb618e2`、actor31254；本包整合观察 `2026-10-17T19:52:31.483142+00:00`。后继源码不追认旧进程部署。

## 直接可用的诊断与下一步

loading phaseb025的played_character=null/armies[]发生在map_ready=false；其main-thread mailbox installed/ready、owner TID与current TID37876一致，failure0。另一coat-of-arms probe的installed=false/failure1不能冒充mailbox坏了；last_read_ms=0是读取耗时毫秒，不代表从未读取。后续phaseb042真实map_ready、public3/native2/date53148864、paused且未进日，已结束本次加载疑问。恢复应读取实际ready字段，无需重装hook或重放启动。

R203 ArmyWindow独立可见subject没有通过；CombatWindow查询真正SDK错误为“current native UI supports army query and select only”。Python `ingame_ui_contract.validate_ui_build_scope`和native `ingame_ui_navigation_v1.cpp`的modern army分支都尚未迁移CombatWindow；1.19的combat RVA不可移用，没有发unsupported Open。当前可用拍法是原生battle上下文绑定地图client；若后续要独立CombatWindow，施工入口是exact .4窗口handler/type/subject只读迁移，而非反复猜旧按钮。

## 原actor RED与实际一日必须并列

Root直接审阅map a05的战斗标记/军队上下文、无hover后，只执行一次canonical Start/Finish。actor随后因检查顶层accepted抛出 `one-day composite action not accepted`，exit1与原stderr保留，**不改标GREEN**。真正返回是 `native-composite`、`progress_status=postcondition`，没有顶层accepted；内部primitive ACK不等于composite后验。

实际native exact clock在53148864→53148888触发date_deadline、completed_daily_ticks1、overshoot0、pause_observed=true、abnormal=false；独立cleanup-before snapshot再次paused/date53148888。原日步不重投。已迁入[可复用纯合同](../../ck3_autonomous_player/src/xar_autoplayer/bridge/exact_one_day_postcondition.py)的 `exact_day_postcondition(step,before,after)`，要求composite字段、停止clock和独立前后帧相符。3079B原代码在小ZIP精确保留，产品仅LF规范化、AST一致；不改NativeDriver、现有actor或a35 native树。R204冻结19024不含新module，不能因入库强迫旧actor从该路径导入。

## 媒体与采样结果的实际范围

raw为5,478,203B/SHA `1f2fd4197af588d7a3971638fcdc84755e441920ce505e384862d77b7deb2c19`，**9.333秒/280帧/1280×720**；gdigrab客户区矩形 `[640,360,1920,1080]`，不是直接HWND采集。Finish NORMAL_TREE_EMPTY、partial=false、guarderror=null；全解码与PTS完整性通过。四个已审样本0/3.1/6.2/9.3秒显示地图战斗与底栏；两端有暂停字样，内部两个样本无可见tooltip。候选[0.5,9)仍待完整视觉连续性审阅，不授clean/1×/人审或正式cue。只保留[一张客户区原裁剪](evidence/episode04-r203-battle-logistics-12004/map-a05-client.png)，没有复制raw或桌面。首提帧命令因obsolete -vsync失败是工具参数历史，不是内容坏片。

oneOwnedRecorder/keeper门意味着同worker不能第二次Start；本场没有重试，下一take用R204新scene/worker。采样由手工inline arm/collect，collector默认0day，没有冒充pre_resume_hook。实际companion已独立禁用payment/natural并clear，capture_enabled=false、busy=false、active0、cleanup_complete；normal-close里的NOT_CONFIGURED仅表示未配置pre_resume_hook，两份事实不冲突。consumer完整collect的resource4记录为0，**不是零军事付款**；paid/payer/cadence与资源业务名仍null/unknown。a02可选oneday合同修复只有source资格，不能倒授本场a01默认0day现场。

## 正常恢复来源与交接

最终正常Save74,286,185B/SHA `653980a0f00e03ea989f2e4102a9a37a38d15d1f20914f4223fb9830058359c9`、date53148888。bootstrap19:33:22Z正常process_exit/CK3 exit0，SDK/recorder/keeper收尾；SCREEN-RELEASE helper exit0、CAS6321 done/resources[]。这正常闭场不覆盖actor RED，也不授战斗胜负、抵达2629或R06 ADD。

[原件索引和源码接点](evidence/episode04-r203-battle-logistics-12004/source-index.json)、[便携核验说明](evidence/episode04-r203-battle-logistics-12004/README.md)供video与agent复用。研究9/14、业务6/11、合格动态0/11、ABC0/3及正式cue数均不变。R204由Root独立实机，本包不执行游戏/SDK/构建或等待成片。跨机重新核安装、Steam、SYSTEM、PID与容量。
