# 用户游玩期间与自动玩家恢复交接（2026-10-05）

用户要自行游玩CK3数小时。自动运行R46/PID104164已正常STOP，managed47337在北京时间15:22:48观测CLOSED0。直到用户明确说可以再次使用CK3，保持纯后台研究；不得自行启动/attach/注入/查询/输入/操作窗口、同步运行环境或修改用户profile。后台采用冻结artifact/源码缓存与轻量文件消费者，不运行会抢占游戏资源的完整并行构建。

最后授权运行基线：v73/source Z:/g78 HEAD d22e9a1cd3fb1062f6c66282f044daafa016718a，env20ba8b4f1c4e99c6575a0029adf17ea4cae5e492a5a516fc7fc3b234768a7cbf。累计5035/36524正常保存日、resume1882、Oct5+377。六日存档h9048/raw53265168/99036288B/SHA9354912f261fca203aeda8e0cedaef6c5b579c210444556faefc590233db783d；末零日查询后h9052同date/size/SHAe0a7fb224723c62296a60ce6683c7b7f2e7614a6d6536e6a3ab8cbf2a5840cec。存档属于隔离的g2-robert-mainline-12003-v73-20261005 profile，本段不把用户游玩计为自动任务进度。

冻结状态：470已Robert占领/围城结束，war117440524 score38；主301989997在470余route[3717,3711]，器械268435481在3717余route[3711]，均moving target3711；守184549452保持3711围城。主2407、器械8／mangonel7/10、守2883、敌2846；3711 C24279868/T55m、44.145%、K0、D96432、breach0且CanStartfalse。器械未抵达，未授K强化或3711占领。敌369098771战斗main day16@4893未完成，仅只读观测。

用户再次授权后，再读取fresh actor29829/episode native-29829-2bc2d599f7f9、war117、三自军位置/route/Combat、当前公共revision。按冻结检查点恢复时，主第一段getter约.86868日，器械当前段约6.11111日；这些不是用户游玩后的实时状态，也不是全程ETA。先确认实际到场，再用既有occupation查询验证3711 K/M/D/B/G/占领状态；所有命令使用当时fresh公共revision，不能复用旧public2。战争、宗教研究继续开放，此次只是用户占用实机期间的授权暂停。

证据：Z:/ck3_mod_rewrite_process_assets/g2-resume-20261005/ROOT-CK3-USER-RESERVED-RELEASE.json；[捕获与调动](../ck3-native-ai/episode03-assault-capture470-stage3711-1.20.0.3.md)、[攻城实际完成日](../ck3-native-ai/siege-assault470-capture-live-loop-12003-2026-10-05.md)。失败attempt与原sealedcut保持，不重复测试/CI/实机验证。
