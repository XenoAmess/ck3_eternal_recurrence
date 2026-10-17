# R204：连续32日、自然回调与一次战斗地图短片

`machine_id: desktop-3fevhd2-1c74096080`，run `desktop-3fevhd2-1c74096080--vanilla--R0204`；本包整合观察 `2026-10-17T20:30:55.523808+00:00`。实际runtime/native source `19024b4d79d818a88709c9932ca4eb364d81ef33`、a35资格16,198B/SHA `a80af8f9df7ca2a2ba56e474cb4092654e8f0782908b63f8278672534e6e2f67`。PID29068/create134367407686810142/gen1/episode `native-31254-6a76736d65fa`，actor31254；后继master不追认旧进程部署。

## 实际推进与恢复方法

本场从[R203正常checkpoint](episode04-r203-battle-logistics-12004.md)独立加载，原生战斗控制绑定Army18在2633、目标2629，路线 `[2627,2626,8753,2629]`；五份片中日步前后仍在战斗。Root直接审阅地图battle上下文、无hover后一次Start/Finish；没有宣称ArmyWindow/CombatWindow可见，也不把路线或目标当抵达。

连续实际日期53148888→53149656，分为**片中5日+原a01已成功1日+新a02的26日=32日**。a01执行完第一日后，下一只读查询的生成suffix `D01-natural` 含大写，不符合该外置队列既有 `r204-[a-z0-9-]{1,75}` 约束，抛出 `bounded existing request ID required`。原RED、已成功1日和unknown[]分别保留；没有重投已推进的日步，没有二次arm。

2527B a02源码只在生成新名字时将suffix转为lowercase，沿用同一a01 arm-token和原有文件排他/未知不重放规则；新attempt从已读日期53149032继续26日。它不是重命名旧请求、改写历史response或放宽任何原生身份门。应在**生成新后缀时**符合调用队列实际grammar；对于已有request ID仍保留原字节并按原请求收集结果。便携verifier只重放这个确定性字符串seam，不导入含C盘路径的运行wrapper、不把它发明成全项目统一ID规范。逐日composite+独立snapshot纯后验沿用[R203合同](../../ck3_autonomous_player/src/xar_autoplayer/bridge/exact_one_day_postcondition.py)，不能查顶层accepted替代真正后验。

## 7条回调明确支持什么

同一owned/no-load窗口共7条留存：6条kind0 Army transition，return RVA `2A9A8C5`、literal amount0/resource−1；1条kind2 `cashpersonal_add`，Character31254、return `28A6D7C`、amount206846，personal balance bits25971864→26178710。后者是个人现金增加，**不是R06兵员ADD**；kind0中的0和−1只是该族的原始字段，不能解释为军事付款为0。

摘要把record内原始日期和首次观察checkpoint日期单列，例如第一条回调日期53148912，而首次checkpoint看到它是在53149008；不能把首次观察时刻改写成事件发生时刻。自然journal64条、phase1/2各32，原始读回无overwrite/failed append；此层支持32日自然入口覆盖，不建立民用月结周期或军事付款触发频率。resource4种类/qualified boundary和raw4 getter均无样本；**无样本不等于0军费**，payer/paid/cadence/资源正式业务名及settlement token仍unknown/null。

后续有价值的施工是沿既有[resource4 wallet-context观察边界](war-payment-resource4-wallet-context-12004.md)等待真实kind1/resource4或actual incoming-writer来源，同时保留当前7行的正面族分类；不要把既有个人现金回调重新命名成军事扣费。完整cash生产consumer已由原owner消费，本次只核便携小摘要和小原件，没有重读最后412,827B cash或重跑旧矩阵。

## 媒体、清理与正常S0

原片15,441,657B/SHA `665fe47cdcd6600cc526460818a9aaeae149857bb5505153510361e8c4000ab2`，**23.266秒/698帧/1280×720**，PTS0→23.233秒、全解码通过。gdigrab客户区 `[640,360,1920,1080]`，不是直接HWND捕获。film primary/cleanup error均null；Start→Finish墙钟27.0436535秒与编码时长分别记录。四个0/7.733/15.5/23.233秒样本中，首尾有暂停，最后有右侧通知；候选 `[0.5,20)`仅供后续完整审阅，未授连续clean、full1×、human signoff或正式cue。只携[开录前原客户区图](evidence/episode04-r204-battle-natural-payments-12004/map-a01-client.png)，不复制原片/桌面图/抽帧组。

手工collect后实际payment disable与独立clear、natural disable与独立off均确认，`actual_cleanup_complete=true`、unknown请求[]。采样precleanup摘要中的enabled=true和close helper里的NOT_CONFIGURED是各自时刻/职责；NOT_CONFIGURED指未配置pre_resume_hook，不能抹去具名手工cleanup。最终正常Save74,845,159B/SHA `101f8fbfdd70b0147b5b49383c4152d99ca22fa42b3e052e6bc01fc4732d7245`、date53149656；CK3/bootstrap正常exit0，SCREEN-RELEASE helper0、CAS6346 done/resources[]。正常闭场不覆盖a01 RED，不授胜利、抵达2629或R06 ADD。

[便携说明](evidence/episode04-r204-battle-natural-payments-12004/README.md)与[exact来源索引](evidence/episode04-r204-battle-natural-payments-12004/source-index.json)可供视频和agent复用。研究9/14、业务6/11、合格动态0/11、ABC0/3、正式cue数保持不变。不同机器须重核安装、运行时、Steam/SYSTEM/容量，不能外推本场身份或通过。
