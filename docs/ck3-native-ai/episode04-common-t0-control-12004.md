# 战争四期：共同T0、自然登船对照与跨机器复用（1.20.0.4）

本方法供战争四期视频和自动游玩智能体共同使用。当前自然登船正例与21日保存T0驻地对照均有实证；[R0174对照及便携复验](episode04-r0174-common-t0-control-12004.md)已通过现有pair checker。原R07七日/避开结算/静止T0后新Move合同仍未闭合。代码或离线测试通过不抵扣实机资格。操作工具见[review02工具](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/README.md)；[精确小投影](evidence/episode04-common-t0-control-12004/common-t0-r0173.receipt-freeze.actual-a01.json)保留原机器、场次和来源字段。大存档、EXE、原片未复制或重哈希。

## 原卡与实际边界

原EXPERIMENT-CARDS R01（38–53行）要求新空profile、普通1066 Robert、正常战争/可控Army/正常seed-S0，并冻结指挥官、补给、兵数、现金及合法ABC目标。实际普通新开起点是R0171，runtime31254来自本次多源身份链；历史人物ID1128和旧runtime29829不能当跨场次映射。R0172/R0173是其正常存档谱系，不是第二次新开，也不能补写完整R01指挥官/ABC目标验收；这两项仍pending。

原R07（103–109行，尤其107）要求同新正常T0、实际陆转海处理组与独立无登船驻地对照，避开实际经济结算机会，窗口不超过7个自然日。R0173在21日首次登船，跨月且T0已在移动。追加21日驻地对照只能关闭**修订的保存T0续行对照**，不能宣称原卡全部完成。原卡完整闭环仍需未来近岸静止T0、合法preview≤7日、避开真实结算机会，两臂分别Move与驻地，所有机会pending。

## 可复用事实和来源

精确版本1.20.0.4/build25734779，EXE SHA98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518。历史R0173源码8dd6d84a60aa246f527a72173117e42a6c107dc2，DLL SHA5d9a4029797a5dc404f084279159f152e306413c7a8e62e2f2453a0334cc0c73。新构建须在显式manifest中绑定新的已批准来源；历史DLL不能冒充未来DLL。

机器desktop-3fevhd2-1c74096080，R0173 PID14544/createFILETIME134365403777766761/gen1/episode native-31254-3072c36153e4。007正常保存产生不可变xar_episode_seed.ck3：68451543B、SHA9ab3b0d05bdc1a0c4ef2d81a9dc27cec3f66e9af2871b5cac11776ddc6ddb784，日期53145048（1066.10.15），正常保存回执SHAa1cacfd64cc9ff5a9227b6cb35aca1ac8874666bd520a5bed0add5975bb9cd2c。R0173实际先load R0172的be327216d366627c46effe1f976f1f479899276a02c88e2511591d6cf732e881（68450356B），保存成9ab3后直接续行；不能说历史处理组load了9ab3。

共同T0：actor31254、Army18、current2624、target1033、route[1036,8653,1034,1033]，1196/1196、supply30000000/Q100000、treasury25166043/Q100000；实际progress31717/Q100000、loaded cutoff50000/Q100000。这些是该保存点实证，不是新场次默认值。新PID必须独立读回。可变checkpoint已被042覆盖到53145576；不能将它代替不可变seed。day20仅summary不是已保存的近岸T0。

历史处理组day21（53145552）Army18进入1036/embarked4，真实一笔personal源链扣费：writer16/gateway17/transition18、payer31254/account0、requested300000/Q100000，wholecallback wallet25448407→25148407。该余额边界是原始callback入口到返回，**不是leaf指令局部store观测或整个日NET**。`qualified_boarding_debits`由Python严格重连原始natural返回、transition、gateway、writer、金额、账户和session；generic writer不能提升为登船费。component3是subbalance偏好，不能解释成军费；maintenance归因仍unclosed。空qualified列表不能证明零费用或免费登船。

## 最短新控制组执行

1. Root在正常prepare/load阶段显式选择不可变9ab3输入。填写新run/PID/create/gen/episode及实际source/DLL；不用事前伪造运行值。只用正常bootstrap/现有逐日runner。
2. 独立T0 snapshot、scoped ordinary Army18和cash；date/actor/位置/route/兵数/补给/余额与冻结点匹配。正常开启natural_phase与payment一次后独立读取admission；数字epoch1在不同window不共享。
3. 原版Halt一次。独立后态必须同2624、空route/target、非embarked、日期不变。若锁定只剩front、拒绝、状态未知或已过日，本控制条件失败，保留原回执，不能冒充驻地对照。ACK不替代后态。
4. 首日单独审阅，再按新attempt推进2..21，每日Arm/Resume各一次、自动exact+24暂停、独立status tick1/overshoot0、fresh cash和ordinary/final。陌生事件按AGENTS采集并选第一显示项；事件后只读补救已执行日，不重Arm/Resume。
5. 同window仅递增sequence连续核对；natural retained≤56、payment≤384、无overwrite/failedappend、Driver128MiB/单包16MiB后验止线，raw另经准入360s/1.5GiB。读取同一成功响应引用后再等待发布完成，不重推动作，不把copy称drain，不clear掉未解释记录。
6. 用portablechecker先baseline再pair。`saved_t0_continuation_control`只声称新控制vs历史保存后续行；`two_new_loaded_arms`需两个新进程从同seed加载、独立readback、21日结果，且处理组实有qualified付款。不同window的counter/sequence不相减、不接续。

## 智能体决策接口

智能体可复用校验器的来源/身份/引用完整性规则和字段语义；不能根据机器名、历史runtime ID、旧route进度或某日NET直接决策扣费。先获取当前独立帧，按实际cutoff/route决定合法后续动作。维护费用需另闭源码调用链与自然实证，现有generic钱包事件仅留原始诊断。此代码只做离线验收，不发MCP、启动游戏或授现场资格。

所有保留输入按[通用存储策略](../storage-retention-policy.md)复核，本轮活跃共同seed、临时展开与操作额度沿实际准入截止2026-10-16T07:45:01.597000+00:00复核（不自动续期；先前10月22日为错误，不构成延长授权）。小型知识/manifest/回执按record期限复核；不因历史或失败就永久保护全部raw。源文件缺失时报告不可读，不制造同名替代证据。

2026-10-15模板勘误：checked-in freeze按Git eol=lf为13320B/SHA1d3593d906b8117934a8bb5cae6a1d3c6c280272c87476867f63e5e816362a5c，template改钉此精确字节；外置CRLF原件13645B/SHA615a...保留为独立历史来源。新增单项unittest核真实文件bytes/SHA和保存T0内容，属于现有验证，不增加现场门禁。
