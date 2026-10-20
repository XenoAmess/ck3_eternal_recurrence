# R0221 选定物理 ADD 与同次 Core 关联的离线恢复（1.20.0.4）

`machine_id: desktop-3fevhd2-1c74096080`。现场 R0221 使用 source `4fc8d0f4cae53735274475bd3e7fc3afbb958f7c`、native tree `fee86631356f556271445157523c62abfd62951e`；新 Python 修复只在隔离集成树执行。精确文件 SHA、观察时间和原件/派生角色见[归档清单](evidence/episode04-r0221-refill-recovery-20261020/MANIFEST.actual.json)。以下结论不外推其他机器、版本或新部署。

## 实际捕获和原现场失败分别保留

原公共单日场实际推进53149056→53149080（1日），worker在自然调用中捕获 Regi2602、physical slot1、ArRg82、CArmy0 的 ADD +1，current68→69；V5 raw包含同一carrier的Core token1、观察到的线程ID37456及generation134369699152906149，配对detach/debug-register restore成立。它不是OS线程数增长，也未重放原指令或追加一天。

原consumer在生成target proof时因 `indent=2` 文件超过64KiB退出2；[原worker结果](evidence/episode04-r0221-refill-recovery-20261020/live/R06-WORKER-RESULT.json)和[原terminal](evidence/episode04-r0221-refill-recovery-20261020/live/R06-REFILL-TERMINAL.json)仍是`STOPPED_ERROR_PRESERVED_NO_REPLAY`、actual_ADD_observed=false、full_R06_qualified=false。finally实际OFF/clear、普通Save、native_restore_verified=true；GUI正常退出后retainedOS0/native0/host原wait0、keeper/allocator0，后态CAS7462 done/resources[]。中间Root回执的keeper pending不回写。[正常闭场原件](evidence/episode04-r0221-refill-recovery-20261020/close/normal-close-result.json)不能替代业务资格。

## 最小修复与一次离线恢复

消费者仅把目标proof输出改成`ensure_ascii=False, separators=(',', ':'), sort_keys=True, allow_nan=False`，保留UTF-8末尾换行和总文件65536字节上限；不删字段、不截断、不放宽任何语义守卫。修复后consumer SHA `cc64032d7ffb1325724871b3a4c124d042d1c643c22125b6db7f825770e9c4b8`；target-proof guard SHA `e226875b69d8b2c753262ca49ecead000f544aeee8fa44c43075c943c3f29721`、instruction guard SHA `265232b78d032165939c660f2f6131d80001eafbfa03d2cd12b34664ffe78bd9`均未变。

12:11:54 UTC 的[一次离线CLI原wait0](evidence/episode04-r0221-refill-recovery-20261020/offline/ORIGINAL-WAIT.actual.json)仅读取同一immutable raw/binding/full-parent proof和原native-wire精确范围18550826字节（SHA `b03ff66bdef770e33231a16e595fdbcc6fcd269eb58104bac62d230043529fd5`），在新路径输出[完整proof](evidence/episode04-r0221-refill-recovery-20261020/offline/R0221-TARGET-CORE-PROOF.offline.json)及[派生item](evidence/episode04-r0221-refill-recovery-20261020/offline/R0221-TARGET-INSTRUCTION.offline.json)。proof紧凑含换行50670字节，原完整对象pretty76077字节；27个ArRg枝、4条选定DATA和1个matching alias均保留。输出proof SHA `46e70788286eff215d37d552bc166db3f2fe1663cd9004f9f57d08dcb0497c6c`，item SHA `c88b81b489beef30b82391e8fbd1050f6bd10cdc19ec915f89513af5cff81bf7`。

新item的`actual_ADD_observed`、`same_core_invocation_join_ready`、`natural_attribution_ready`为true；`same_core_NET_cause_proven`、`whole_core_NET_cause_proven`、`global_physical_closure_qualification_granted`、`full_window_coverage_ready`、`toggle_effect_proven`、`refill_business_qualification_granted`仍false，`owner_admission_authority_verified_here=false`。选定槽位关联不替代全Core NET、全军物理闭包、开关效果或完整R06业务，也不重新授予现场准入。

12:09:35 UTC的[4项真实CLI回归](evidence/episode04-r0221-refill-recovery-20261020/focused/ORIGINAL-WAIT.actual.json)原Popen wait0（32.570秒）：完整大形状无损读回，UTF-8+换行恰65536可写、65537拒绝且无输出；原parent SHA/owner/token/generation/尾枝完整性损坏均拒绝。[独审](evidence/episode04-r0221-refill-recovery-20261020/independent/INDEPENDENT-REVIEW.actual-a01.json)用未改D guard独立从原精确范围重提取，完整对象及item全等，五种实际输入变体均拒绝。测试和离线恢复无新SDK、probe、游戏、原生日步或native构建。consumer位于native_bridge目录，未来Git子树SHA会因Python字节变化；它不证明任何新EXE/DLL已构建或部署合格。

## B、容量与影片界限

被动复用同一自然日pair：CArmy0库存raw10350831→10350831，cap30000000、monthly rate -423728；独立supply journal实际installed=true，目标Army事件两端均0。全局journal序列0→9不等目标Army回调。B [pair原派生结果](evidence/episode04-r0221-refill-recovery-20261020/b-stock/R0221-STOCK-PAIR.actual.json)为NO_CREDIT，B仍0/2；九族regular_core-only采样状态不推出独立journal OFF。

容量原件保留11:42临时文件缺口RED及延迟通知、11:53:34全局RED与同一时间证据不足。[录制终态](evidence/episode04-r0221-refill-recovery-20261020/film/E04-R06-R0221-TAKE01-film-result.actual.json)为11:52:33.788826 UTC，早于后一次RED；这不补证全程无超额或自动暂停。无新视频验收。正式动态仍1/11（既有R12源镜头）、研究10/14、业务7/11、B0/2、ABC0/3，fullR06false。

当前可用于游玩的输入是Army仍在2170、补给相关兵数6689超过当地limit4960、monthly rate raw -423728，且一日库存实际未增；不能据此前推一个未知休整点。后继应以当前来源绑定的route/敌持点/补给输入选择已有具名候选再自然观察，B仍0/2；本包不发Move或初始化库存。R08另需新的ordinary-null maintenance-writer资格Q及公共同client接线，旧a07不充当本轮资格，未实现adapter不并入生产。

后继从此完整target证据及原合同定位剩余未闭边，复用已保留自然日输入，不为重现序列化问题重启游戏或重放日步。大父响应和媒体仅保原位置/pin，按通用存储策略限期复核；归档不是永久保留或删除授权。
